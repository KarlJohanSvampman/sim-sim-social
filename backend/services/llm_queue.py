import asyncio
from typing import Awaitable, Callable, Any


LLM_QUEUE: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
_LLM_WORKER_STARTED = False
_LLM_SEQ = 0


def next_queue_id() -> int:
    global _LLM_SEQ
    _LLM_SEQ += 1
    return _LLM_SEQ


async def enqueue_llm_call(fn: Callable[[], Awaitable[dict]], meta: dict | None = None) -> dict:
    loop = asyncio.get_running_loop()
    future: asyncio.Future = loop.create_future()
    item = {
        "fn": fn,
        "future": future,
        "meta": meta or {},
    }
    await LLM_QUEUE.put(item)
    return await future


async def llm_worker() -> None:
    while True:
        item = await LLM_QUEUE.get()
        future = item["future"]
        fn = item["fn"]
        try:
            result = await fn()
            if not future.done():
                future.set_result(result)
        except Exception as e:
            if not future.done():
                future.set_result({"error": str(e)})
        finally:
            LLM_QUEUE.task_done()


async def ensure_llm_worker_started() -> None:
    global _LLM_WORKER_STARTED
    if _LLM_WORKER_STARTED:
        return
    asyncio.create_task(llm_worker())
    _LLM_WORKER_STARTED = True
