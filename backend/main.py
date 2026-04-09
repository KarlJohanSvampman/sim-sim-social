from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel
import asyncio
from services.tick import simulation_loop
from services.ws import manager
from services.state import get_world_snapshot
from services.operator import inject_news, get_character, patch_character
from services.db import init_db, list_timeline_events, replay_events, replay_window

app = FastAPI(title="Phase 10")

class NewsPayload(BaseModel):
    content: str

class CharacterPatch(BaseModel):
    health: float | None = None
    needs: dict | None = None
    thoughts: str | None = None
    institution_role: str | None = None

@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(simulation_loop())

@app.get("/")
def root():
    return {"status": "running", "world": get_world_snapshot()}

@app.get("/world")
def world():
    return get_world_snapshot()

@app.get("/timeline")
def timeline(limit: int = Query(default=200, ge=1, le=5000)):
    return {"events": list_timeline_events(limit)}

@app.get("/timeline/replay")
def replay(start_tick: int = 1, end_tick: int = 100):
    return {"events": replay_events(start_tick, end_tick)}

@app.get("/timeline/replay/window")
def replay_scrub(cursor_tick: int = 1, radius: int = 15):
    return {"events": replay_window(cursor_tick, radius)}

@app.post("/operator/news")
def post_news(payload: NewsPayload):
    inject_news(payload.content)
    return {"ok": True}

@app.get("/operator/character/{char_id}")
def get_character_endpoint(char_id: str):
    c = get_character(char_id)
    if not c:
        raise HTTPException(status_code=404, detail="Character not found")
    return c

@app.patch("/operator/character/{char_id}")
def patch_character_endpoint(char_id: str, payload: CharacterPatch):
    c = patch_character(char_id, payload.model_dump(exclude_none=True))
    if not c:
        raise HTTPException(status_code=404, detail="Character not found")
    return c

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    client_id = await manager.connect(ws)
    try:
        await manager.send_personal(client_id, get_world_snapshot())
        while True:
            msg = await ws.receive_json()
            if msg.get("type") == "set_thoughts":
                manager.set_thoughts_enabled(client_id, bool(msg.get("enabled", True)))
    except WebSocketDisconnect:
        manager.disconnect(client_id)
