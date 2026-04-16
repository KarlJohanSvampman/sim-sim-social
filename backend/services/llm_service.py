import json
import os
import time
from typing import Any, Dict

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
    state = character.get("state", {})
    profile = character.get("profile", {})
    calendar = world.get("calendar", {})
    return f"""You are the decision engine for one simulated person in a life sim.

Return strict JSON only with this shape:
{{
  "thought": "brief internal reasoning",
  "action": {{
    "type": "wander" | "engage_activity" | "continue_activity" | "speak_to",
    "activity_type": "study" | "practice" | "social" | "recreative",
    "tag": "activity_or_topic",
    "hours": 0.1,
    "target_character_id": "optional"
  }},
  "speech": ["optional lines to say next, max 2"]
}}

Current in-world date/time:
{json.dumps(calendar)}

Character profile:
{json.dumps(profile, ensure_ascii=False)}

Character state:
{json.dumps(state, ensure_ascii=False)}

Use current needs, mood, current activity, nearby context, and social opportunities.
Be concise. If no urgent reason exists, prefer either wander or speak_to over constantly starting activities.
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
            "action": {"type": "wander"},
            "speech": []
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
            temperature=0.7,
            messages=[
                {"role": "system", "content": "You produce strict JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        text = resp.choices[0].message.content.strip()
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
            "action": {"type": "wander"},
            "speech": []
        }
        _append_log({
            "ts": now_ts,
            "character_id": character.get("profile", {}).get("id"),
            "prompt": prompt,
            "response": result,
            "mode": "error_fallback"
        })
        return result
