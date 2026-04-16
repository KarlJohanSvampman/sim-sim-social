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

    reduced_state = {
        "needs": state.get("needs", {}),
        "mood": state.get("mood"),
        "stress": state.get("stress"),
        "focus": state.get("focus"),
        "fatigue": state.get("fatigue"),
        "intoxication": state.get("intoxication"),
        "spoken_text": state.get("spoken_text", ""),
        "current_intention": state.get("current_intention", ""),
        "current_action_name": state.get("current_action_name", ""),
        "action_phase": state.get("action_phase", "idle"),
    }

    return f"""You are the live action planner for one simulated human in a sandbox life sim.

Return STRICT JSON ONLY with this exact shape:
{{
  "thought": "brief internal reasoning",
  "action": {{
    "name": "sleep" | "eat" | "drink" | "use_restroom" | "speak" | "observe" | "wait" | "move" | "cook" | "study" | "work" | "relax" | "check_phone" | "smoke" | "drink_alcohol" | "self_care",
    "intention": "why the sim is doing this in plain language",
    "target_character_id": "optional character id or empty string",
    "target_tile": {{"x": 0, "y": 0}},
    "utterance": "optional spoken line",
    "pre_action_delay": 1,
    "duration_seconds": 5,
    "post_action_delay": 1
  }}
}}

Rules:
- pre_action_delay and post_action_delay must each be an integer from 1 to 15
- duration_seconds must be an integer from 1 to 60
- prefer believable human pacing
- if speaking to someone, set name="speak" and include target_character_id when possible
- be varied; avoid repeating the same exact action forever

Current date/time:
{json.dumps(calendar)}

World config:
{json.dumps(config)}

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
        result = {
            "thought": "No llm_provider configured.",
            "action": {
                "name": "wait",
                "intention": "pause because no provider is configured",
                "target_character_id": "",
                "target_tile": {"x": character.get("position", {}).get("x", 0), "y": character.get("position", {}).get("y", 0)},
                "utterance": "",
                "pre_action_delay": 2,
                "duration_seconds": 4,
                "post_action_delay": 2
            }
        }
        _append_log({"ts": now_ts, "character_id": character.get("profile", {}).get("id"), "prompt": prompt, "response": result, "mode": "no_provider"})
        return result

    try:
        provider_result = call_chat_provider(provider_cfg, [
            {"role": "system", "content": "You produce strict JSON only."},
            {"role": "user", "content": prompt},
        ])
        text = provider_result["text"]
        parsed = json.loads(text)
        _append_log({
            "ts": now_ts,
            "character_id": character.get("profile", {}).get("id"),
            "prompt": prompt,
            "provider": provider_cfg,
            "request_body": provider_result.get("request_body"),
            "url": provider_result.get("url"),
            "response_raw": text,
            "response": parsed,
            "mode": "provider_live"
        })
        return parsed
    except Exception as e:
        result = {
            "thought": f"Provider call failed: {e}",
            "action": {
                "name": "wait",
                "intention": "fallback after provider error",
                "target_character_id": "",
                "target_tile": {"x": character.get("position", {}).get("x", 0), "y": character.get("position", {}).get("y", 0)},
                "utterance": "",
                "pre_action_delay": 2,
                "duration_seconds": 4,
                "post_action_delay": 2
            }
        }
        _append_log({
            "ts": now_ts,
            "character_id": character.get("profile", {}).get("id"),
            "prompt": prompt,
            "provider": provider_cfg,
            "response": result,
            "mode": "provider_error"
        })
        return result
