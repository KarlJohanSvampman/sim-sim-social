from fastapi import APIRouter
from services.state import create_object, move_object

router = APIRouter()

@router.post("/objects")
def create(obj: dict):
    return create_object(obj)

@router.post("/move")
def move(data: dict):
    move_object(data["id"], data["x"], data["y"])
    return {"ok": True}
