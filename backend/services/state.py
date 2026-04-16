from copy import deepcopy

WORLD = {
    "tick": 0,
    "grid": {
        "width": 12,
        "height": 12,
        "tiles": {}
    },
    "characters": {},
    "relationships": {},
    "conversations": {},
    "institutions": {},
    "news": [],
    "objects": {},
    "items": {},
    "tagged_characters": {},
    "config": {"tick_rate": 1.0, "llm_interval_seconds": 30.0, "enable_activity_logic": False, "enable_roaming_logic": False, "ai_action_mode": "actions_only"},
    "calendar": {
        "year": 2026,
        "month": 4,
        "day": 16,
        "minute_of_day": 480
    },
    "action_definitions": {},
    "activity_definitions": {},
    "llm_logs": []
}

def make_tile(x, y):
    is_border = x == 0 or y == 0 or x == WORLD["grid"]["width"] - 1 or y == WORLD["grid"]["height"] - 1
    return {
        "x": x,
        "y": y,
        "z": 0,
        "tile_type": "wall" if is_border else "floor",
        "elevation": "FLAT",
        "room_tag": None,
        "zone_type": None,
        "object": None,
        "items": [],
        "blocks_movement": is_border,
        "blocks_sight": is_border
    }

def init():
    if WORLD["grid"]["tiles"]:
        return

    width = WORLD["grid"]["width"]
    height = WORLD["grid"]["height"]

    for y in range(height):
        for x in range(width):
            WORLD["grid"]["tiles"][f"{x},{y}"] = make_tile(x, y)

    # Room tags
    for tile in WORLD["grid"]["tiles"].values():
        if 2 <= tile["x"] <= 4 and 2 <= tile["y"] <= 4:
            tile["room_tag"] = "bedroom"
        elif 5 <= tile["x"] <= 7 and 2 <= tile["y"] <= 4:
            tile["room_tag"] = "kitchen"
        elif 8 <= tile["x"] <= 10 and 2 <= tile["y"] <= 4:
            tile["room_tag"] = "living_room"
        elif 2 <= tile["x"] <= 4 and 5 <= tile["y"] <= 7:
            tile["room_tag"] = "bathroom"
        elif 5 <= tile["x"] <= 10 and 5 <= tile["y"] <= 10:
            tile["room_tag"] = "yard"

    # Seed world objects used by activity requirement checks
    WORLD["objects"]["obj_bed"] = {"id": "obj_bed", "name": "Bed", "category": "bed"}
    WORLD["objects"]["obj_stove"] = {"id": "obj_stove", "name": "Stove", "category": "stove"}
    WORLD["objects"]["obj_food"] = {"id": "obj_food", "name": "Food", "category": "food"}
    WORLD["objects"]["obj_tv"] = {"id": "obj_tv", "name": "TV", "category": "tv"}
    WORLD["objects"]["obj_restroom"] = {"id": "obj_restroom", "name": "Restroom", "category": "restroom"}
    WORLD["objects"]["obj_computer"] = {"id": "obj_computer", "name": "Computer", "category": "computer"}
    WORLD["objects"]["obj_book"] = {"id": "obj_book", "name": "Book", "category": "book"}

    WORLD["grid"]["tiles"]["3,3"]["object"] = WORLD["objects"]["obj_bed"]
    WORLD["grid"]["tiles"]["6,3"]["object"] = WORLD["objects"]["obj_stove"]
    WORLD["grid"]["tiles"]["7,3"]["object"] = WORLD["objects"]["obj_food"]
    WORLD["grid"]["tiles"]["9,3"]["object"] = WORLD["objects"]["obj_tv"]
    WORLD["grid"]["tiles"]["3,6"]["object"] = WORLD["objects"]["obj_restroom"]
    WORLD["grid"]["tiles"]["6,6"]["object"] = WORLD["objects"]["obj_computer"]
    WORLD["grid"]["tiles"]["9,6"]["object"] = WORLD["objects"]["obj_book"]
    WORLD["grid"]["tiles"]["4,3"]["items"] = [
        {"id": "item_phone", "name": "Smartphone", "type": "smartphone"}
    ]

    WORLD["action_definitions"].update({
        "act_move": {"id": "act_move", "name": "move_to_tile", "category": "movement", "description": "Move toward a target tile."},
        "act_talk": {"id": "act_talk", "name": "speak", "category": "social", "description": "Speak or converse with another character."},
        "act_use": {"id": "act_use", "name": "use_object", "category": "interaction", "description": "Use an object on the current tile or nearby."}
    })
    WORLD["activity_definitions"].update({
        "av_sleep": {"id": "av_sleep", "name": "sleep", "type": "recreative", "description": "Sleep and recover fatigue.", "min_hours": 0.5},
        "av_eat": {"id": "av_eat", "name": "eat", "type": "recreative", "description": "Consume food to reduce hunger.", "min_hours": 0.1},
        "av_conversation": {"id": "av_conversation", "name": "conversation", "type": "social", "description": "Spend time talking with another sim.", "min_hours": 0.1},
        "av_study": {"id": "av_study", "name": "general_study", "type": "study", "description": "Study a knowledge topic.", "min_hours": 0.2}
    })

def create_object(obj):
    WORLD.setdefault("objects", {})
    WORLD["objects"][obj["id"]] = obj
    return obj

def move_object(obj_id, x, y, z=0):
    for tile in WORLD["grid"]["tiles"].values():
        existing = tile.get("object")
        if existing and existing.get("id") == obj_id:
            tile["object"] = None

    if obj_id in WORLD.get("objects", {}):
        key_2d = f"{x},{y}"
        if key_2d in WORLD["grid"]["tiles"]:
            WORLD["grid"]["tiles"][key_2d]["object"] = WORLD["objects"][obj_id]

    return WORLD.get("objects", {}).get(obj_id)

def get_world():
    return WORLD

def get_world_snapshot():
    return deepcopy(WORLD)

init()
