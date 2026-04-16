from __future__ import annotations
from services.state import get_world

ACTIVITY_REQUIREMENTS = {
    ("recreative", "sleep"): {"objects": {"bed"}, "tile_types": set(), "room_tags": {"bedroom"}},
    ("recreative", "eat"): {"objects": {"food"}, "tile_types": set(), "room_tags": {"kitchen", "dining"}},
    ("recreative", "hygiene"): {"objects": {"restroom"}, "tile_types": set(), "room_tags": {"bathroom"}},
    ("recreative", "watch_tv"): {"objects": {"tv"}, "tile_types": set(), "room_tags": {"living_room"}},
    ("recreative", "listen_radio"): {"objects": {"radio"}, "tile_types": set(), "room_tags": set()},
    ("recreative", "read_for_fun"): {"objects": {"book"}, "tile_types": set(), "room_tags": set()},
    ("recreative", "exercise"): {"objects": set(), "tile_types": {"yard", "gym_floor"}, "room_tags": {"yard", "gym"}},
    ("recreative", "stress_relief"): {"objects": set(), "tile_types": set(), "room_tags": {"living_room", "yard", "bedroom"}},
    ("social", "phone_call"): {"objects": {"smartphone", "computer"}, "tile_types": set(), "room_tags": set()},
    ("social", "social_media"): {"objects": {"smartphone", "computer"}, "tile_types": set(), "room_tags": set()},
    ("study", "general_study"): {"objects": {"book", "computer"}, "tile_types": set(), "room_tags": {"study", "office"}},
    ("practice", "cooking"): {"objects": {"stove", "food"}, "tile_types": set(), "room_tags": {"kitchen"}},
    ("practice", "conversation"): {"objects": set(), "tile_types": set(), "room_tags": {"living_room", "yard", "kitchen"}},
    ("practice", "work"): {"objects": {"computer", "car"}, "tile_types": set(), "room_tags": {"office", "garage"}},
}

def normalize_object_name(name: str) -> str:
    return str(name).strip().lower().replace(" ", "_")

def tile_key(x: int, y: int, z: int = 0) -> str:
    world = get_world()
    if f"{x},{y},{z}" in world["grid"]["tiles"]:
        return f"{x},{y},{z}"
    return f"{x},{y}"

def current_tile(character) -> dict | None:
    world = get_world()
    pos = character.position if hasattr(character, "position") else character.get("position", {})
    return world["grid"]["tiles"].get(tile_key(pos["x"], pos["y"], pos.get("z", 0)))

def tile_room_tags(tile: dict) -> set[str]:
    tags = set()
    if tile.get("room_tag"):
        tags.add(tile["room_tag"])
    if tile.get("zone_type"):
        tags.add(tile["zone_type"])
    tile_type = tile.get("tile_type") or tile.get("type")
    if tile_type:
        tags.add(tile_type)
    return tags

def nearby_objects(character, radius: int = 2) -> set[str]:
    world = get_world()
    pos = character.position if hasattr(character, "position") else character.get("position", {})
    found = set()
    for t in world["grid"]["tiles"].values():
        if abs(t["x"] - pos["x"]) <= radius and abs(t["y"] - pos["y"]) <= radius:
            obj = t.get("object")
            if obj:
                found.add(normalize_object_name(obj.get("name", obj.get("id", ""))))
                found.add(normalize_object_name(obj.get("category", "")))
                found.add(normalize_object_name(obj.get("id", "")))
            for item in t.get("items", []):
                found.add(normalize_object_name(item.get("name", item.get("id", ""))))
                found.add(normalize_object_name(item.get("type", "")))
                found.add(normalize_object_name(item.get("id", "")))
    return {x for x in found if x}

def requirements_for_activity(activity_type: str, tag: str) -> dict:
    default = {"objects": set(), "tile_types": set(), "room_tags": set()}
    return ACTIVITY_REQUIREMENTS.get((activity_type, tag), ACTIVITY_REQUIREMENTS.get((activity_type, "general_study"), default))

def is_activity_available(character, activity_type: str, tag: str) -> tuple[bool, set[str]]:
    tile = current_tile(character)
    req = requirements_for_activity(activity_type, tag)
    nearby = nearby_objects(character, radius=2)
    room_tags = tile_room_tags(tile or {})
    objects_ok = (not req["objects"]) or bool(req["objects"] & nearby)
    tile_ok = (not req["tile_types"]) or ((tile.get("tile_type") if tile else None) in req["tile_types"])
    room_ok = (not req["room_tags"]) or bool(req["room_tags"] & room_tags)
    available = set(nearby) | room_tags
    return objects_ok and tile_ok and room_ok, available
