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

    memory = character.get("memory", [])[-10:]
    conversation = character.get("conversation_history", [])[-12:]
    nearby_characters = list((world.get("tagged_characters") or {}).keys())
    action_definitions = list((world.get("action_definitions") or {}).values())
    world_reputation = world.get("reputation", {})
    world_alliances = world.get("alliances", [])
    world_rivalries = world.get("rivalries", [])
    world_drama_arcs = world.get("drama_arcs", [])[-8:]

    reduced_state = {
        "needs": state.get("needs", {}),
        "mood": state.get("mood"),
        "action_mood": state.get("action_mood", "neutral"),
        "stress": state.get("stress"),
        "focus": state.get("focus"),
        "fatigue": state.get("fatigue"),
        "spoken_text": state.get("spoken_text", ""),
        "current_action_name": state.get("current_action_name", ""),
        "emotional_temperature": state.get("emotional_temperature", 20.0),
        "escalation_level": state.get("escalation_level", 0),
        "volatility": state.get("volatility", 0.5),
        "aggression_bias": state.get("aggression_bias", 0.2),
        "drama_bias": state.get("drama_bias", 0.6),
        "authority_sensitivity": state.get("authority_sensitivity", 0.3),
        "insecurity": state.get("insecurity", 0.4),
        "conversation_partner_id": state.get("conversation_partner_id", ""),
        "awaiting_reply_from_id": state.get("awaiting_reply_from_id", ""),
        "conversation_turns_remaining": state.get("conversation_turns_remaining", 0),
        "conversation_topic": state.get("conversation_topic", ""),
        "affinity": state.get("affinity", {}),
        "relationship_meters": state.get("relationship_meters", {}),
        "grudges": state.get("grudges", []),
        "avoid_character_ids": state.get("avoid_character_ids", []),
        "feared_character_ids": state.get("feared_character_ids", []),
    }

    return f"PROMPT REDACTED FOR BREVITY"  # unchanged


def maybe_run_decision_llm(character: dict, world: dict, now_ts: float | None = None, force: bool = False) -> dict | None:
    now_ts = now_ts or time.time()
    interval = float(world.get("config", {}).get("llm_interval_seconds", 30.0))
    state = character.setdefault("state", {})
    last_ts = float(state.get("last_llm_at", 0) or 0)
    if not force and now_ts - last_ts < interval:
        return None

    prompt = build_decision_prompt(character, world)
    state["last_llm_at"] = now_ts

    provider_cfg = (world.get("config", {}) or {}).get("llm_provider", {})
    if not provider_cfg:
        return None

    provider_result = call_chat_provider(provider_cfg, [
        {"role": "system", "content": "You produce strict JSON only."},
        {"role": "user", "content": prompt},
    ])

    _append_log({
        "prompt": prompt,
        "provider_result": provider_result,
    })

    try:
        if provider_result.get("text"):
            return json.loads(provider_result["text"])
    except Exception:
        pass

    return None
