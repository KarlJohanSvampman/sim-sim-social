import os
import httpx


def _resolve_env_key(env_name: str) -> str:
    return os.getenv(env_name or "", "")


def _render_auth(template: str, api_key: str) -> str:
    return (template or "Bearer {{api_key}}").replace("{{api_key}}", api_key)


def _walk_path(data, path: str):
    cur = data
    for part in (path or "").split("."):
        if part == "":
            continue
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def _normalize_messages(messages):
    return [{"role": m["role"], "content": m["content"]} for m in messages]


def _interpolate(value, *, model: str, messages):
    if isinstance(value, str):
        if value == "{{model}}":
            return model
        if value == "{{messages}}":
            return _normalize_messages(messages)
        return value
    if isinstance(value, dict):
        return {k: _interpolate(v, model=model, messages=messages) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(v, model=model, messages=messages) for v in value]
    return value


def call_chat_provider(provider_cfg: dict, messages: list[dict]) -> dict:
    provider_kind = provider_cfg.get("provider_kind", "openai_compatible")
    base_url = provider_cfg.get("base_url", "").rstrip("/") + "/"
    model = provider_cfg.get("model", "")
    api_key = _resolve_env_key(provider_cfg.get("api_key_env", ""))
    auth_header_name = provider_cfg.get("auth_header_name", "Authorization")
    auth_template = provider_cfg.get("auth_header_template", "Bearer {{api_key}}")
    headers = {"Content-Type": "application/json"}

    if provider_cfg.get("api_key_env"):
        if not api_key:
            raise RuntimeError(f"Missing API key in env var: {provider_cfg.get('api_key_env', '')}")
        auth_header_value = _render_auth(auth_template, api_key)
        headers[auth_header_name] = auth_header_value

    if "host.docker.internal:11434" in base_url:
        headers["Host"] = "localhost:11434"

    if provider_kind in {"openai_compatible", "generic_http"}:
        path = provider_cfg.get("chat_path", "chat/completions").lstrip("/")
        body = _interpolate(
            provider_cfg.get("request_template", {
                "model": "{{model}}",
                "messages": "{{messages}}",
                "temperature": 0.8,
                "stream": False
            }),
            model=model,
            messages=messages
        )
        url = base_url + path

        debug_result = {
            "url": url,
            "request_headers": headers,
            "request_body": body,
            "status_code": None,
            "response_text": None,
            "response_json": None,
            "text": None,
            "error": None,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, headers=headers, json=body)
                debug_result["status_code"] = resp.status_code
                debug_result["response_text"] = resp.text

                try:
                    data = resp.json()
                    debug_result["response_json"] = data
                except Exception:
                    data = None

                resp.raise_for_status()

            if data is None:
                raise RuntimeError("Provider returned non-JSON success response")

            text = _walk_path(data, provider_cfg.get("response_text_path", "choices.0.message.content"))
            debug_result["text"] = text
            return debug_result
        except Exception as e:
            debug_result["error"] = str(e)
            return debug_result

    raise RuntimeError(f"Unsupported provider_kind: {provider_kind}")
