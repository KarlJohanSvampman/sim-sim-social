from fastapi import APIRouter
from services.state import get_world_snapshot

router = APIRouter()

@router.get("/world")
def world():
    return get_world_snapshot()
