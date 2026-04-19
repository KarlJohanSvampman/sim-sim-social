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

    return f"""You are the live action planner for one simulated human in a sandbox life simulation.

This sim should feel a bit more overdramatic, childish, impulsive, and emotionally reactive than an average adult, while still being believable enough to create drama.

Return STRICT JSON ONLY in this exact shape:
{{
  "thought": "brief internal reasoning",
  "action": {{
    "name": "wait" | "move" | "speak" | "yell" | "gesture" | "leave" | "smash" | "observe" | "relax" | "study",
    "intention": "plain-language why",
    "target_character_id": "optional id or empty string",
    "target_tile": {{"x": 0, "y": 0}},
    "utterance": "optional line of dialogue",
    "pre_action_delay": 1,
    "duration_seconds": 4,
    "post_action_delay": 1,
    "action_mood": "calm" | "playful" | "dramatic" | "annoyed" | "angry" | "furious" | "sad" | "smug"
  }}
}}

Behavior rules:
- If awaiting_reply_from_id is set, prefer replying to that character unless there is a very strong reason not to.
- Continue ongoing conversations when conversation_turns_remaining > 0.
- Use conversation_topic and recent conversation history to avoid repeating the same line.
- emotional_temperature 0-30 = calm, 30-60 = reactive, 60-80 = heated, 80-100 = explosive.
- At higher escalation, prefer gesture, yell, leave, or smash over neutral actions.
- leave is a good breaking point for conflict.
- smash is only appropriate when emotional_temperature is very high or aggression_bias is high.
- If speaking or yelling, include an utterance.
- Prefer allies and friends in neutral or positive scenes.
- Prefer rivals and grudge targets in hostile scenes.
- Reputation matters: sims with high scandal or danger should be treated as volatile or risky.
- Be socially dramatic and expressive, but still return exactly one next action.

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

World reputation:
{json.dumps(world_reputation, ensure_ascii=False)}

World alliances:
{json.dumps(world_alliances, ensure_ascii=False)}

World rivalries:
{json.dumps(world_rivalries, ensure_ascii=False)}

Recent drama arcs:
{json.dumps(world_drama_arcs, ensure_ascii=False)}

Available actions:
{json.dumps(action_definitions, ensure_ascii=False)}

Other active characters:
{json.dumps(nearby_characters, ensure_ascii=False)}
"""


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

    try:
        provider_result = call_chat_provider(provider_cfg, [
            {"role": "system", "content": "You produce strict JSON only."},
            {"role": "user", "content": prompt},
        ])
        text = provider_result["text"]
        parsed = json.loads(text)
        _append_log({"prompt": prompt, "response": parsed})
        return parsed
    except Exception:
        return None
