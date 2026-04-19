import json
import time
import asyncio

from services.provider_client import call_chat_provider_async
from services.llm_queue import enqueue_llm_call, next_queue_id
from services.state import get_world


def _append_log(entry: dict):
    world = get_world()
    world.setdefault("llm_logs", [])
    world["llm_logs"].append(entry)
    world["llm_logs"] = world["llm_logs"][-200:]


def build_decision_prompt(character: dict, world: dict) -> str:
    return "Return JSON action"  # simplified


async def maybe_run_decision_llm(character: dict, world: dict, now_ts: float | None = None, force: bool = False) -> dict | None:
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

    async def job():
        return await call_chat_provider_async(provider_cfg, [
            {"role": "system", "content": "Return JSON only"},
            {"role": "user", "content": prompt},
        ])

    result = await enqueue_llm_call(job, {"type": "decision"})

    _append_log({
        "prompt": prompt,
        "provider_result": result,
    })

    try:
        if result.get("text"):
            return json.loads(result["text"])
    except Exception:
        pass

    return None
