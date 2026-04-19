from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from routes.world import router as world_router
from routes.objects import router as object_router
from routes.editor import router as editor_router
from routes.tagged_profiles import router as tagged_profiles_router
from services.ws import manager
from services.state import get_world, get_world_snapshot
from services.live_sim import live_sim_loop
from services.tagged_sim_loop import tagged_sim_loop
from services.llm_queue import ensure_llm_worker_started, enqueue_llm_call
from services.provider_client import call_chat_provider_async

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(world_router)
app.include_router(object_router)
app.include_router(editor_router)
app.include_router(tagged_profiles_router)


def _default_config() -> dict:
    return {
        "tick_rate": 1.0,
        "llm_interval_seconds": 30.0,
        "llm_provider": {
            "provider_kind": "openai_compatible",
            "base_url": "http://ollamaserver:11434/v1/",
            "chat_path": "chat/completions",
            "model": "llama3.1",
            "api_key_env": "",
            "auth_header_name": "Authorization",
            "auth_header_template": "Bearer {{api_key}}",
            "response_text_path": "choices.0.message.content",
        },
    }


def _merged_config() -> dict:
    world = get_world()
    existing = world.get("config", {}) or {}
    defaults = _default_config()
    merged = {**defaults, **existing}
    merged["llm_provider"] = {**defaults["llm_provider"], **(existing.get("llm_provider", {}) or {})}
    world["config"] = merged
    return merged


@app.on_event("startup")
async def startup():
    _merged_config()
    await ensure_llm_worker_started()
    asyncio.create_task(live_sim_loop())
    asyncio.create_task(tagged_sim_loop())


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    cid = await manager.connect(ws)
    try:
        await ws.send_json(get_world_snapshot())
        while True:
            await ws.receive_text()
            await manager.broadcast(get_world_snapshot())
    except WebSocketDisconnect:
        manager.disconnect(cid)


@app.get("/config")
def get_config():
    return _merged_config()


@app.post("/config")
def set_config(cfg: dict = Body(...)):
    world = get_world()
    existing = _merged_config()
    incoming_provider = cfg.get("llm_provider")
    existing_provider = existing.get("llm_provider", {}) or {}

    merged = {**existing, **cfg}
    if incoming_provider is not None:
        merged["llm_provider"] = {**existing_provider, **incoming_provider}

    world["config"] = merged
    return world["config"]


@app.post("/config/test")
async def test_config(cfg: dict = Body(...)):
    effective = _default_config()
    effective.update(cfg or {})
    effective["llm_provider"] = {**_default_config()["llm_provider"], **((cfg or {}).get("llm_provider", {}) or {})}
    provider_cfg = effective.get("llm_provider", {})

    async def job():
        return await call_chat_provider_async(provider_cfg, [
            {"role": "system", "content": "You are a connectivity test. Reply briefly."},
            {"role": "user", "content": "Reply with the single word: connected"},
        ])

    return await enqueue_llm_call(job, {"type": "config_test"})


@app.get("/llm-logs")
def get_llm_logs():
    return get_world().get("llm_logs", [])


@app.delete("/llm-logs")
def clear_llm_logs():
    world = get_world()
    world["llm_logs"] = []
    return {"ok": True, "count": 0}
