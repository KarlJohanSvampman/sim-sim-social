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


async def call_chat_provider_async(provider_cfg: dict, messages: list[dict]) -> dict:
    provider_kind = provider_cfg.get("provider_kind", "openai_compatible")
    base_url = provider_cfg.get("base_url", "").rstrip("/") + "/"
    model = provider_cfg.get("model", "")

    headers = {"Content-Type": "application/json"}

    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.8,
        "stream": False,
    }

    url = base_url + "chat/completions"

    debug = {
        "url": url,
        "request_body": body,
        "status_code": None,
        "text": None,
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            debug["status_code"] = resp.status_code
            data = resp.json()
            text = _walk_path(data, "choices.0.message.content")
            debug["text"] = text
            return debug
    except Exception as e:
        debug["error"] = str(e)
        return debug
