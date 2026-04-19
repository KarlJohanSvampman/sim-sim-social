import json
import time

from services.provider_client import call_chat_provider_async
from services.llm_queue import enqueue_llm_call
from services.state import get_world


def _append_log(entry: dict):
    world = get_world()
    world.setdefault("llm_logs", [])
    world["llm_logs"].append(entry)
    world["llm_logs"] = world["llm_logs"][-200:]


def build_decision_prompt(character: dict, world: dict) -> str:
    others = [c["profile"]["id"] for c in world.get("tagged_characters", {}).values() if c["profile"]["id"] != character.get("profile", {}).get("id")]

    return f"""
Return JSON only.
Choose exactly ONE action.

Rules:
- NEVER choose speak or yell with an empty utterance.
- Prefer interacting with other characters instead of yourself.
- If others exist: {others}

Actions:
wait, move, speak, yell, gesture, leave, smash, observe, relax, study

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
"""


async def maybe_run_decision_llm(character: dict, world: dict):
    async def job():
        return await call_chat_provider_async(world.get("config", {}).get("llm_provider", {}), [
            {"role": "system", "content": "Return JSON only. No empty speech."},
            {"role": "user", "content": build_decision_prompt(character, world)},
        ])

    result = await enqueue_llm_call(job)

    _append_log({"provider_result": result})

    try:
        if result.get("text"):
            data = json.loads(result["text"])
            act = data.get("action", {})
            if act.get("name") in ["speak","yell"] and not act.get("utterance"):
                act["name"] = "wait"
            return data
    except Exception:
        pass

    return None
