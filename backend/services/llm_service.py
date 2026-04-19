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
    return """
Return JSON only.
Choose exactly ONE action.

Allowed actions:
wait, move, speak, yell, gesture, leave, smash, observe, relax, study

Schema:
{
  "thought": "...",
  "action": {
    "name": "wait|move|speak|yell|gesture|leave|smash|observe|relax|study",
    "intention": "...",
    "target_character_id": "",
    "target_tile": {"x":0,"y":0},
    "utterance": ""
  }
}
"""


async def maybe_run_decision_llm(character: dict, world: dict, now_ts=None, force=False):
    now_ts = now_ts or time.time()
    state = character.setdefault("state", {})

    async def job():
        return await call_chat_provider_async(world.get("config", {}).get("llm_provider", {}), [
            {"role": "system", "content": "Return JSON only. ONE action."},
            {"role": "user", "content": build_decision_prompt(character, world)},
        ])

    result = await enqueue_llm_call(job)

    _append_log({"provider_result": result})

    try:
        if result.get("text"):
            data = json.loads(result["text"])
            name = data.get("action", {}).get("name", "wait")
            if name not in ["wait","move","speak","yell","gesture","leave","smash","observe","relax","study"]:
                data["action"]["name"] = "wait"
            return data
    except Exception:
        pass

    return None
