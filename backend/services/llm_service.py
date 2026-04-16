import json
import os
import time

from services.state import get_world

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def llm_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) and OpenAI is not None


def _client():
    if not llm_enabled():
        return None
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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

IMPORTANT EXPERIMENT SETTINGS:
- activity logic is disabled
- roaming logic is disabled
- decide behavior using only needs, tags, current mood/state, and broad human judgment
- you must return a SINGLE action request in strict JSON
- the action can be short or long because actions can carry duration_seconds

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
- if no urgent need exists, "wait", "observe", "speak", or "relax" are acceptable
- do NOT use activities
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

    if not llm_enabled():
        result = {
            "thought": "LLM disabled because OPENAI_API_KEY is missing or SDK unavailable.",
            "action": {
                "name": "wait",
                "intention": "pause because live LLM is disabled",
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
            "response": result,
            "mode": "disabled_fallback"
        })
        return result

    client = _client()
    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            temperature=0.8,
            messages=[
                {"role": "system", "content": "You produce strict JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(text)
        _append_log({
            "ts": now_ts,
            "character_id": character.get("profile", {}).get("id"),
            "prompt": prompt,
            "response_raw": text,
            "response": parsed,
            "mode": "live_llm"
        })
        return parsed
    except Exception as e:
        result = {
            "thought": f"LLM call failed: {e}",
            "action": {
                "name": "wait",
                "intention": "fallback after llm error",
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
            "response": result,
            "mode": "error_fallback"
        })
        return result
