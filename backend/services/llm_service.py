import json
import time

from services.provider_client import call_chat_provider
from services.state import get_world


def _append_log(entry: dict):
    world = get_world()
    world.setdefault("llm_logs", [])
    world["llm_logs"].append(entry)
    world["llm_logs"] = world["llm_logs"][-200:]


def _summarize_relationships(character, world):
    state = character.get("state", {})
    affinity = state.get("affinity", {})
    rep = world.get("reputation", {})

    summaries = []
    for cid, val in list(affinity.items())[:5]:
        summaries.append({
            "id": cid,
            "affinity": val,
            "rep": rep.get(cid, {})
        })
    return summaries


def build_decision_prompt(character: dict, world: dict) -> str:
    profile = character.get("profile", {})
    state = character.get("state", {})

    compact = {
        "name": profile.get("name"),
        "traits": profile.get("identity_tags", [])[:3],
        "needs": state.get("needs", {}),
        "mood": state.get("mood"),
        "emotion": state.get("emotional_temperature"),
        "partner": state.get("conversation_partner_id"),
        "awaiting": state.get("awaiting_reply_from_id"),
        "topic": state.get("conversation_topic"),
    }

    memory = character.get("memory", [])[-5:]
    convo = character.get("conversation_history", [])[-6:]
    relationships = _summarize_relationships(character, world)

    allowed_actions = [
        "wait", "move", "speak", "yell", "gesture", "leave", "smash", "observe", "relax", "study"
    ]
    allowed_actions_text = " | ".join(f'"{a}"' for a in allowed_actions)

    prompt = f"""
Return JSON only.

Schema:
{{
  "thought": "...",
  "action": {{
    "name": {allowed_actions_text},
    "intention": "...",
    "target_character_id": "",
    "target_tile": {{"x":0,"y":0}},
    "utterance": "",
    "pre_action_delay": 1,
    "duration_seconds": 4,
    "post_action_delay": 1,
    "action_mood": "calm" | "playful" | "dramatic" | "annoyed" | "angry" | "furious" | "sad" | "smug"
  }}
}}

Behavior:
- Overdramatic, impulsive, emotional.
- If awaiting reply, respond.
- High emotion -> escalate.
- smash only if very emotional.
- Choose exactly one action name, never a list and never multiple actions combined.

Character:
{json.dumps(compact)}

Relationships:
{json.dumps(relationships)}

Memory:
{json.dumps(memory)}

Conversation:
{json.dumps(convo)}
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
        {"role": "system", "content": "Return valid JSON only. Choose one action only."},
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
