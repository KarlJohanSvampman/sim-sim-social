from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from routes.world import router as world_router
from routes.objects import router as object_router
from routes.editor import router as editor_router
from services.ws import manager
from services.state import get_world_snapshot
from services.live_sim import live_sim_loop

app = FastAPI()
app.include_router(world_router)
app.include_router(object_router)
app.include_router(editor_router)

@app.on_event("startup")
async def startup():
    asyncio.create_task(live_sim_loop())

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
