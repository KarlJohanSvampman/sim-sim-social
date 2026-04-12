TILE_TYPES = {
    "floor_wood": {
        "id": "floor_wood",
        "name": "Wood Floor",
        "texture": "textures/floor_wood.png",
        "blocks_movement": False,
        "blocks_sight": False,
        "default_interactions": ["walk", "inspect"]
    },
    "wall_brick": {
        "id": "wall_brick",
        "name": "Brick Wall",
        "texture": "textures/wall_brick.png",
        "blocks_movement": True,
        "blocks_sight": True,
        "default_interactions": ["inspect"]
    },
    "door_closed": {
        "id": "door_closed",
        "name": "Closed Door",
        "texture": "textures/door_closed.png",
        "blocks_movement": True,
        "blocks_sight": True,
        "default_interactions": ["open", "inspect"]
    },
    "door_open": {
        "id": "door_open",
        "name": "Open Door",
        "texture": "textures/door_open.png",
        "blocks_movement": False,
        "blocks_sight": False,
        "default_interactions": ["close", "inspect"]
    },
    "window": {
        "id": "window",
        "name": "Window",
        "texture": "textures/window.png",
        "blocks_movement": True,
        "blocks_sight": False,
        "default_interactions": ["open", "close", "inspect"]
    }
}

def list_tile_types():
    return list(TILE_TYPES.values())

def upsert_tile_type(payload):
    TILE_TYPES[payload["id"]] = payload
    return payload

def delete_tile_type(tile_type_id):
    TILE_TYPES.pop(tile_type_id, None)
