import json
import time

from services.provider_client import call_chat_provider
from services.state import get_world


def _append_log(entry: dict):
    world = get_world()
    world.setdefault("llm_logs", [])
    world["llm_logs"].append(entry)
    world["llm_logs"] = world["llm_logs"][-200:]


def build_decision_prompt(character: dict, world: dict) -> str:
    profile = character.get("profile", {})
    state = character.get("state", {})
    calendar = world.get("calendar", {})
    config = world.get("config", {})

    memory = character.get("memory", [])[-10:]
    conversation = character.get("conversation_history", [])[-10:]

    reduced_state = {
        "needs": state.get("needs", {}),
        "mood": state.get("mood"),
        "stress": state.get("stress"),
        "focus": state.get("focus"),
        "fatigue": state.get("fatigue"),
        "spoken_text": state.get("spoken_text", ""),
        "current_action_name": state.get("current_action_name", ""),
    }

    return f"""You are the live action planner for one simulated human in a sandbox life sim.

Return STRICT JSON ONLY.

Recent internal memory:
{json.dumps(memory, ensure_ascii=False)}

Recent conversations:
{json.dumps(conversation, ensure_ascii=False)}

Current date/time:
{json.dumps(calendar)}

Character profile:
{json.dumps(profile, ensure_ascii=False)}

Character state:
{json.dumps(reduced_state, ensure_ascii=False)}

Other active characters:
{json.dumps(list((world.get("tagged_characters") or {}).keys()), ensure_ascii=False)}
"""


def maybe_run_decision_llm(character: dict, world: dict, now_ts: float | None = None) -> dict | None:
    now_ts = now_ts or time.time()
    interval = float(world.get("config", {}).get("llm_interval_seconds", 30.0))
    state = character.setdefault("state", {})
    last_ts = float(state.get("last_llm_at", 0) or 0)
    if now_ts - last_ts < interval:
        return None

    prompt = build_decision_prompt(character, world)
    state["last_llm_at"] = now_ts

    provider_cfg = (world.get("config", {}) or {}).get("llm_provider", {})
    if not provider_cfg:
        return None

    try:
        provider_result = call_chat_provider(provider_cfg, [
            {"role": "system", "content": "You produce strict JSON only."},
            {"role": "user", "content": prompt},
        ])
        text = provider_result["text"]
        parsed = json.loads(text)
        _append_log({"prompt": prompt, "response": parsed})
        return parsed
    except Exception as e:
        return None
