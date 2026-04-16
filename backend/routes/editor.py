from fastapi import APIRouter, HTTPException
from services.editor_api import (
    api_list_objects, api_upsert_object, api_delete_object,
    api_list_items, api_upsert_item, api_delete_item,
    api_list_tile_types, api_upsert_tile_type, api_delete_tile_type,
    list_tiles, patch_tile
)

router = APIRouter(prefix="/editor")

@router.get("/objects")
def list_objects():
    return api_list_objects()

@router.post("/objects")
def upsert_object(payload: dict):
    return api_upsert_object(payload)

@router.delete("/objects/{obj_id}")
def delete_object(obj_id: str):
    return api_delete_object(obj_id)

@router.get("/items")
def list_items():
    return api_list_items()

@router.post("/items")
def upsert_item(payload: dict):
    return api_upsert_item(payload)

@router.delete("/items/{item_id}")
def delete_item(item_id: str):
    return api_delete_item(item_id)

@router.get("/tile-types")
def list_tile_types():
    return api_list_tile_types()

@router.post("/tile-types")
def upsert_tile_type(payload: dict):
    return api_upsert_tile_type(payload)

@router.delete("/tile-types/{tile_type_id}")
def delete_tile_type(tile_type_id: str):
    return api_delete_tile_type(tile_type_id)

@router.get("/tiles")
def tiles():
    return list_tiles()

@router.patch("/tiles/{tile_key}")
def update_tile(tile_key: str, updates: dict):
    tile = patch_tile(tile_key, updates)
    if not tile:
        raise HTTPException(status_code=404, detail="Tile not found")
    return tile


@router.get("/actions")
def list_actions():
    return list(get_world().get("action_definitions", {}).values())

@router.post("/actions")
def upsert_action(action: dict):
    world = get_world()
    world.setdefault("action_definitions", {})
    world["action_definitions"][action["id"]] = action
    return action

@router.delete("/actions/{action_id}")
def delete_action(action_id: str):
    world = get_world()
    if action_id not in world.get("action_definitions", {}):
        raise HTTPException(status_code=404, detail="Action not found")
    del world["action_definitions"][action_id]
    return {"deleted": action_id}

@router.get("/activities")
def list_activities():
    return list(get_world().get("activity_definitions", {}).values())

@router.post("/activities")
def upsert_activity(activity: dict):
    world = get_world()
    world.setdefault("activity_definitions", {})
    world["activity_definitions"][activity["id"]] = activity
    return activity

@router.delete("/activities/{activity_id}")
def delete_activity(activity_id: str):
    world = get_world()
    if activity_id not in world.get("activity_definitions", {}):
        raise HTTPException(status_code=404, detail="Activity not found")
    del world["activity_definitions"][activity_id]
    return {"deleted": activity_id}
