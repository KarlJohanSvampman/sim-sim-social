from services.object_registry import list_objects, upsert_object, delete_object
from services.item_registry import list_items, upsert_item, delete_item
from services.tile_type_registry import list_tile_types, upsert_tile_type, delete_tile_type
from services.state import get_world

def list_tiles():
    return list(get_world()["grid"]["tiles"].values())

def patch_tile(tile_key, updates):
    world = get_world()
    tile = world["grid"]["tiles"].get(tile_key)
    if not tile:
        return None
    tile.update(updates)
    return tile

def api_list_objects():
    return list_objects()

def api_upsert_object(payload):
    return upsert_object(payload)

def api_delete_object(obj_id):
    delete_object(obj_id)
    return {"deleted": obj_id}

def api_list_items():
    return list_items()

def api_upsert_item(payload):
    return upsert_item(payload)

def api_delete_item(item_id):
    delete_item(item_id)
    return {"deleted": item_id}

def api_list_tile_types():
    return list_tile_types()

def api_upsert_tile_type(payload):
    return upsert_tile_type(payload)

def api_delete_tile_type(tile_type_id):
    delete_tile_type(tile_type_id)
    return {"deleted": tile_type_id}
