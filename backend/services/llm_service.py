import json

from services.provider_client import call_chat_provider_async
from services.llm_queue import enqueue_llm_call
from services.state import get_world

ALLOWED_ACTIONS = ["wait", "move", "speak", "yell", "gesture", "leave", "smash", "observe", "relax", "study"]


def _append_log(entry: dict):
    world = get_world()
    world.setdefault("llm_logs", [])
    world["llm_logs"].append(entry)
    world["llm_logs"] = world["llm_logs"][-200:]


def build_decision_prompt(character: dict, world: dict) -> str:
    me = character.get("profile", {}).get("id")
    others = []
    for c in (world.get("tagged_characters", {}) or {}).values():
        pid = c.get("profile", {}).get("id")
        if pid and pid != me:
            others.append({
                "id": pid,
                "name": c.get("profile", {}).get("name", pid),
                "position": c.get("position", {}),
                "mood": c.get("state", {}).get("mood", "neutral"),
            })

    compact = {
        "self_id": me,
        "name": character.get("profile", {}).get("name"),
        "position": character.get("position", {}),
        "mood": character.get("state", {}).get("mood"),
        "current_action_name": character.get("state", {}).get("current_action_name", ""),
        "conversation_partner_id": character.get("state", {}).get("conversation_partner_id", ""),
        "awaiting_reply_from_id": character.get("state", {}).get("awaiting_reply_from_id", ""),
    }

    return f"""
Return JSON only.
Choose exactly ONE action.
Never choose speak or yell with an empty utterance.
If you choose speak, yell, or gesture and another person is available, set target_character_id to one of the listed others, not yourself.
If currently in conversation, prefer replying to the conversation partner.

Allowed actions: {", ".join(ALLOWED_ACTIONS)}

Schema:
{{
  "thought": "...",
  "action": {{
    "name": "wait|move|speak|yell|gesture|leave|smash|observe|relax|study",
    "target_character_id": "",
    "target_tile": {{"x":0,"y":0}},
    "utterance": ""
  }}
}}

Self:
{json.dumps(compact, ensure_ascii=False)}

Others:
{json.dumps(others[:5], ensure_ascii=False)}
""".strip()


async def maybe_run_decision_llm(character: dict, world: dict):
    async def job():
        return await call_chat_provider_async(world.get("config", {}).get("llm_provider", {}), [
            {"role": "system", "content": "Return valid JSON only. Choose one action. No empty speech."},
            {"role": "user", "content": build_decision_prompt(character, world)},
        ])

    result = await enqueue_llm_call(job)
    _append_log({"prompt": build_decision_prompt(character, world), "provider_result": result})

    try:
        if result.get("text"):
            data = json.loads(result["text"])
            act = data.get("action", {})
            name = act.get("name", "wait")
            if name not in ALLOWED_ACTIONS:
                act["name"] = "wait"
            if act.get("name") in ["speak", "yell"] and not (act.get("utterance") or "").strip():
                act["name"] = "wait"
                act["utterance"] = ""
            return data
    except Exception:
        pass

    return None
