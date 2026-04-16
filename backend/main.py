from fastapi import FastAPI
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from routes.world import router as world_router
from routes.objects import router as object_router
from routes.editor import router as editor_router
from routes.tagged_profiles import router as tagged_profiles_router
from services.ws import manager
from services.state import get_world_snapshot
from services.live_sim import live_sim_loop
from services.tagged_sim_loop import tagged_sim_loop

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

@app.on_event("startup")
async def startup():
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

from fastapi import Body

@app.get("/config")
def get_config():
    from services.state import get_world
    return get_world().get("config", {})

@app.post("/config")
def set_config(cfg: dict = Body(...)):
    from services.state import get_world
    world = get_world()
    world["config"] = cfg
    return cfg


@app.get("/llm-logs")
def get_llm_logs():
    from services.state import get_world
    return get_world().get("llm_logs", [])
