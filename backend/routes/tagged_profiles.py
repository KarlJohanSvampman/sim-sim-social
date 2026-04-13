from fastapi import APIRouter, HTTPException
from services.tagged_profile_store import upsert_tagged_character, get_tagged_character, list_tagged_characters

router = APIRouter(prefix="/tagged-profiles")

@router.get("")
def list_profiles():
    return list_tagged_characters()

@router.get("/{char_id}")
def get_profile(char_id: str):
    p = get_tagged_character(char_id)
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    return p

@router.post("")
def upsert_profile(payload: dict):
    return upsert_tagged_character(payload)
