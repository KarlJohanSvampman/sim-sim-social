from fastapi import APIRouter, HTTPException
from services.state import get_world

router = APIRouter(prefix="/editor", tags=["editor"])

@router.get("/objects")
def list_objects():
    return list(get_world().get("objects", {}).values())

@router.post("/objects")
def upsert_object(obj: dict):
    world = get_world()
    world.setdefault("objects", {})
    world["objects"][obj["id"]] = obj
    return obj

@router.delete("/objects/{obj_id}")
def delete_object(obj_id: str):
    world = get_world()
    if obj_id not in world.get("objects", {}):
        raise HTTPException(status_code=404, detail="Object not found")
    del world["objects"][obj_id]
    return {"deleted": obj_id}

@router.get("/items")
def list_items():
    return list(get_world().get("items", {}).values())

@router.post("/items")
def upsert_item(item: dict):
    world = get_world()
    world.setdefault("items", {})
    world["items"][item["id"]] = item
    return item

@router.delete("/items/{item_id}")
def delete_item(item_id: str):
    world = get_world()
    if item_id not in world.get("items", {}):
        raise HTTPException(status_code=404, detail="Item not found")
    del world["items"][item_id]
    return {"deleted": item_id}

@router.get("/tile-types")
def list_tile_types():
    world = get_world()
    world.setdefault("tile_types", {})
    return list(world["tile_types"].values())

@router.post("/tile-types")
def upsert_tile_type(tile_type: dict):
    world = get_world()
    world.setdefault("tile_types", {})
    world["tile_types"][tile_type["id"]] = tile_type
    return tile_type

@router.delete("/tile-types/{tile_type_id}")
def delete_tile_type(tile_type_id: str):
    world = get_world()
    if tile_type_id not in world.get("tile_types", {}):
        raise HTTPException(status_code=404, detail="Tile type not found")
    del world["tile_types"][tile_type_id]
    return {"deleted": tile_type_id}

@router.get("/actions")
def list_actions():
    return list(get_world().get("action_definitions", {}).values())

@router.post("/actions")
def upsert_action(action: dict):
    if "id" not in action or "name" not in action:
        raise HTTPException(status_code=400, detail="Action requires at least id and name")
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
    if "id" not in activity or "name" not in activity:
        raise HTTPException(status_code=400, detail="Activity requires at least id and name")
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
