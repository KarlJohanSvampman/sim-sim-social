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
    position = character.get("position", {})

    reduced_state = {
        "needs": state.get("needs", {}),
        "mood": state.get("mood"),
        "action_mood": state.get("action_mood", "neutral"),
        "stress": state.get("stress"),
        "focus": state.get("focus"),
        "fatigue": state.get("fatigue"),
        "spoken_text": state.get("spoken_text", ""),
        "current_action_name": state.get("current_action_name", ""),
        "current_intention": state.get("current_intention", ""),
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

    prompt = f"""
You are the decision engine for one simulated human in a sandbox social simulation.

The sim should feel slightly overdramatic, childish, impulsive, and emotionally reactive compared to an average adult, while still remaining coherent.

Return STRICT JSON ONLY. Do not include markdown. Do not explain. Do not refuse. Produce exactly one action.

Required JSON shape:
{{
  "thought": "brief internal reasoning",
  "action": {{
    "name": "wait" | "move" | "speak" | "yell" | "gesture" | "leave" | "smash" | "observe" | "relax" | "study",
    "intention": "plain-language reason",
    "target_character_id": "optional character id or empty string",
    "target_tile": {{"x": 0, "y": 0}},
    "utterance": "optional spoken line or empty string",
    "pre_action_delay": 1,
    "duration_seconds": 4,
    "post_action_delay": 1,
    "action_mood": "calm" | "playful" | "dramatic" | "annoyed" | "angry" | "furious" | "sad" | "smug"
  }}
}}

Rules:
- If awaiting_reply_from_id is set, prefer replying to that character.
- Continue ongoing conversations when conversation_turns_remaining > 0.
- Use conversation_topic and recent conversation history to avoid repetition.
- emotional_temperature 0-30 = calm, 30-60 = reactive, 60-80 = heated, 80-100 = explosive.
- Higher escalation should bias toward gesture, yell, leave, or smash.
- leave is a valid conflict breaking point.
- smash is only appropriate when emotional_temperature is very high or aggression_bias is high.
- If choosing speak or yell, include an utterance.
- Prefer allies and friends in positive or neutral scenes.
- Prefer rivals or grudge targets in hostile scenes.
- Respect avoid_character_ids and feared_character_ids when deciding who to approach.
- Output valid JSON only.

Current date/time:
{json.dumps(calendar, ensure_ascii=False)}

Character profile:
{json.dumps(profile, ensure_ascii=False)}

Character position:
{json.dumps(position, ensure_ascii=False)}

Character state:
{json.dumps(reduced_state, ensure_ascii=False)}

Recent internal memory:
{json.dumps(memory, ensure_ascii=False)}

Recent conversations:
{json.dumps(conversation, ensure_ascii=False)}

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
""".strip()

    return prompt


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
        {"role": "system", "content": "Return only valid JSON matching the requested action schema. Never add commentary or links."},
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
