from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
import asyncio
from services.tick import simulation_loop
from services.ws import manager
from services.state import get_world_snapshot
from services.operator import inject_news, inject_hazard, get_character, patch_character
from services.memory_recall import recall_for_question

app = FastAPI(title="Phase 8")

class NewsPayload(BaseModel):
    content: str

class HazardPayload(BaseModel):
    hazard_type: str
    location: dict
    intensity: float = 1.0

class CharacterPatch(BaseModel):
    health: float | None = None
    intoxication: float | None = None
    is_unconscious: bool | None = None
    thoughts: str | None = None
    needs: dict | None = None

class AskPayload(BaseModel):
    question: str

@app.on_event("startup")
async def startup():
    asyncio.create_task(simulation_loop())

@app.get("/")
def root():
    return {"status": "running", "world": get_world_snapshot()}

@app.get("/world")
def world():
    return get_world_snapshot()

@app.post("/operator/news")
def post_news(payload: NewsPayload):
    inject_news(payload.content)
    return {"ok": True}

@app.post("/operator/hazard")
def post_hazard(payload: HazardPayload):
    inject_hazard(payload.hazard_type, payload.location, payload.intensity)
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

@app.post("/operator/ask/{char_id}")
def ask_character_endpoint(char_id: str, payload: AskPayload):
    c = get_character(char_id)
    if not c:
        raise HTTPException(status_code=404, detail="Character not found")
    return recall_for_question(c, payload.question)

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
