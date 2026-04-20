from copy import deepcopy

WORLD = {
    "tick": 0,
    "grid": {
        "width": 20,
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
    "zones": {},
    "doors": [],
    "households": {},
    "config": {
        "tick_rate": 1.0,
        "llm_interval_seconds": 30.0,
        "llm_provider": {
            "provider_kind": "openai_compatible",
            "label": "Ollama (localhost)",
            "base_url": "http://host.docker.internal:11434/v1/",
            "chat_path": "chat/completions",
            "model": "llama3.1",
            "api_key_env": "",
            "auth_header_name": "Authorization",
            "auth_header_template": "",
            "request_template": {
                "model": "{{model}}",
                "messages": "{{messages}}",
                "temperature": 0.8,
                "stream": False
            },
            "response_text_path": "choices.0.message.content"
        },
        "enable_activity_logic": False,
        "enable_roaming_logic": False,
        "ai_action_mode": "actions_only"
    },
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
    return {
        "x": x,
        "y": y,
        "z": 0,
        "tile_type": "void",
        "elevation": "FLAT",
        "room_tag": None,
        "zone_type": None,
        "household_id": None,
        "object": None,
        "items": [],
        "blocks_movement": True,
        "blocks_sight": True
    }


def carve_floor(x1, y1, x2, y2, *, zone_type=None, room_tag=None, household_id=None, tile_type="floor"):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            tile = WORLD["grid"]["tiles"][f"{x},{y}"]
            tile["tile_type"] = tile_type
            tile["zone_type"] = zone_type
            tile["room_tag"] = room_tag
            tile["household_id"] = household_id
            tile["blocks_movement"] = False
            tile["blocks_sight"] = False


def set_wall(x, y, *, zone_type=None, household_id=None):
    tile = WORLD["grid"]["tiles"][f"{x},{y}"]
    tile["tile_type"] = "wall"
    tile["zone_type"] = zone_type
    tile["household_id"] = household_id
    tile["blocks_movement"] = True
    tile["blocks_sight"] = True


def set_door(x, y, *, connects, household_id=None):
    tile = WORLD["grid"]["tiles"][f"{x},{y}"]
    tile["tile_type"] = "door"
    tile["zone_type"] = "door"
    tile["room_tag"] = "entry"
    tile["household_id"] = household_id
    tile["blocks_movement"] = False
    tile["blocks_sight"] = False
    WORLD["doors"].append({"x": x, "y": y, "connects": connects, "household_id": household_id})


def init():
    if WORLD["grid"]["tiles"]:
        return

    width = WORLD["grid"]["width"]
    height = WORLD["grid"]["height"]

    for y in range(height):
        for x in range(width):
            WORLD["grid"]["tiles"][f"{x},{y}"] = make_tile(x, y)

    # Base outer boundary
    for x in range(width):
        set_wall(x, 0)
        set_wall(x, height - 1)
    for y in range(height):
        set_wall(0, y)
        set_wall(width - 1, y)

    # Street zone in the middle
    carve_floor(8, 1, 11, 10, zone_type="street", room_tag="street", household_id=None, tile_type="street")

    # Households metadata
    WORLD["households"] = {
        "house_1": {
            "id": "house_1",
            "name": "Household 1",
            "zone_id": "house_1",
            "members": ["tag_ada"],
            "balance": 1200.0,
            "weekly_upkeep": 350.0,
            "car": {"id": "car_house_1", "name": "Household Car 1", "cost_per_roundtrip": 12.0}
        },
        "house_2": {
            "id": "house_2",
            "name": "Household 2",
            "zone_id": "house_2",
            "members": ["tag_bryn"],
            "balance": 1200.0,
            "weekly_upkeep": 350.0,
            "car": {"id": "car_house_2", "name": "Household Car 2", "cost_per_roundtrip": 12.0}
        }
    }

    WORLD["zones"] = {
        "house_1": {"id": "house_1", "name": "House 1", "type": "household"},
        "street": {"id": "street", "name": "Neighborhood Street", "type": "street"},
        "house_2": {"id": "house_2", "name": "House 2", "type": "household"},
    }

    # Left house shell: x 1..7, y 1..10
    for x in range(1, 8):
        set_wall(x, 1, zone_type="house_1", household_id="house_1")
        set_wall(x, 10, zone_type="house_1", household_id="house_1")
    for y in range(1, 11):
        set_wall(1, y, zone_type="house_1", household_id="house_1")
        set_wall(7, y, zone_type="house_1", household_id="house_1")

    carve_floor(2, 2, 4, 4, zone_type="house_1", room_tag="bedroom", household_id="house_1")
    carve_floor(2, 5, 4, 7, zone_type="house_1", room_tag="bathroom", household_id="house_1")
    carve_floor(5, 2, 6, 4, zone_type="house_1", room_tag="kitchen", household_id="house_1")
    carve_floor(5, 5, 6, 9, zone_type="house_1", room_tag="living_room", household_id="house_1")
    carve_floor(2, 8, 4, 9, zone_type="house_1", room_tag="hall", household_id="house_1")

    # Door from house 1 to street
    set_door(7, 6, connects=["house_1", "street"], household_id="house_1")

    # Right house shell: x 12..18, y 1..10
    for x in range(12, 19):
        set_wall(x, 1, zone_type="house_2", household_id="house_2")
        set_wall(x, 10, zone_type="house_2", household_id="house_2")
    for y in range(1, 11):
        set_wall(12, y, zone_type="house_2", household_id="house_2")
        set_wall(18, y, zone_type="house_2", household_id="house_2")

    carve_floor(13, 2, 15, 4, zone_type="house_2", room_tag="bedroom", household_id="house_2")
    carve_floor(13, 5, 15, 7, zone_type="house_2", room_tag="bathroom", household_id="house_2")
    carve_floor(16, 2, 17, 4, zone_type="house_2", room_tag="kitchen", household_id="house_2")
    carve_floor(16, 5, 17, 9, zone_type="house_2", room_tag="living_room", household_id="house_2")
    carve_floor(13, 8, 15, 9, zone_type="house_2", room_tag="hall", household_id="house_2")

    # Door from street to house 2
    set_door(12, 6, connects=["street", "house_2"], household_id="house_2")

    WORLD["objects"].update({
        "obj_bed_1": {"id": "obj_bed_1", "name": "Bed", "category": "bed", "household_id": "house_1"},
        "obj_stove_1": {"id": "obj_stove_1", "name": "Stove", "category": "stove", "household_id": "house_1"},
        "obj_tv_1": {"id": "obj_tv_1", "name": "TV", "category": "tv", "household_id": "house_1"},
        "obj_restroom_1": {"id": "obj_restroom_1", "name": "Restroom", "category": "restroom", "household_id": "house_1"},
        "obj_bed_2": {"id": "obj_bed_2", "name": "Bed", "category": "bed", "household_id": "house_2"},
        "obj_stove_2": {"id": "obj_stove_2", "name": "Stove", "category": "stove", "household_id": "house_2"},
        "obj_tv_2": {"id": "obj_tv_2", "name": "TV", "category": "tv", "household_id": "house_2"},
        "obj_restroom_2": {"id": "obj_restroom_2", "name": "Restroom", "category": "restroom", "household_id": "house_2"},
        "obj_car_1": {"id": "obj_car_1", "name": "Car", "category": "car", "household_id": "house_1"},
        "obj_car_2": {"id": "obj_car_2", "name": "Car", "category": "car", "household_id": "house_2"},
    })

    WORLD["grid"]["tiles"]["3,3"]["object"] = WORLD["objects"]["obj_bed_1"]
    WORLD["grid"]["tiles"]["5,3"]["object"] = WORLD["objects"]["obj_stove_1"]
    WORLD["grid"]["tiles"]["6,7"]["object"] = WORLD["objects"]["obj_tv_1"]
    WORLD["grid"]["tiles"]["3,6"]["object"] = WORLD["objects"]["obj_restroom_1"]
    WORLD["grid"]["tiles"]["13,3"]["object"] = WORLD["objects"]["obj_bed_2"]
    WORLD["grid"]["tiles"]["16,3"]["object"] = WORLD["objects"]["obj_stove_2"]
    WORLD["grid"]["tiles"]["17,7"]["object"] = WORLD["objects"]["obj_tv_2"]
    WORLD["grid"]["tiles"]["14,6"]["object"] = WORLD["objects"]["obj_restroom_2"]
    WORLD["grid"]["tiles"]["8,9"]["object"] = WORLD["objects"]["obj_car_1"]
    WORLD["grid"]["tiles"]["11,9"]["object"] = WORLD["objects"]["obj_car_2"]
    WORLD["grid"]["tiles"]["4,3"]["items"] = [{"id": "item_phone", "name": "Smartphone", "type": "smartphone"}]

    WORLD["action_definitions"].update({
        "act_wait": {
            "id": "act_wait",
            "name": "wait",
            "category": "idle",
            "description": "Pause briefly without changing position.",
            "supports_target_character": False,
            "supports_target_tile": False,
            "supports_utterance": False,
            "supports_action_mood": True,
            "default_pre_action_delay": 2,
            "default_duration_seconds": 4,
            "default_post_action_delay": 2,
            "min_duration_seconds": 1,
            "max_duration_seconds": 60,
            "allowed_intentions": ["pause", "think", "wait"],
            "notes": ""
        },
        "act_move": {
            "id": "act_move",
            "name": "move",
            "category": "movement",
            "description": "Move toward a target tile.",
            "supports_target_character": False,
            "supports_target_tile": True,
            "supports_utterance": False,
            "supports_action_mood": True,
            "default_pre_action_delay": 1,
            "default_duration_seconds": 3,
            "default_post_action_delay": 1,
            "min_duration_seconds": 1,
            "max_duration_seconds": 30,
            "allowed_intentions": ["go somewhere", "approach", "relocate"],
            "notes": ""
        },
        "act_speak": {
            "id": "act_speak",
            "name": "speak",
            "category": "social",
            "description": "Speak to another character or aloud.",
            "supports_target_character": True,
            "supports_target_tile": False,
            "supports_utterance": True,
            "supports_action_mood": True,
            "default_pre_action_delay": 2,
            "default_duration_seconds": 6,
            "default_post_action_delay": 2,
            "min_duration_seconds": 1,
            "max_duration_seconds": 45,
            "allowed_intentions": ["talk", "ask", "comment", "greet"],
            "notes": ""
        },
        "act_yell": {
            "id": "act_yell",
            "name": "yell",
            "category": "social",
            "description": "Raise voice in an emotional or confrontational way.",
            "supports_target_character": True,
            "supports_target_tile": False,
            "supports_utterance": True,
            "supports_action_mood": True,
            "default_pre_action_delay": 1,
            "default_duration_seconds": 4,
            "default_post_action_delay": 2,
            "min_duration_seconds": 1,
            "max_duration_seconds": 20,
            "allowed_intentions": ["argue", "complain", "accuse", "vent"],
            "notes": ""
        },
        "act_gesture": {
            "id": "act_gesture",
            "name": "gesture",
            "category": "social",
            "description": "Use body language to react or emphasize.",
            "supports_target_character": True,
            "supports_target_tile": False,
            "supports_utterance": False,
            "supports_action_mood": True,
            "default_pre_action_delay": 1,
            "default_duration_seconds": 3,
            "default_post_action_delay": 1,
            "min_duration_seconds": 1,
            "max_duration_seconds": 15,
            "allowed_intentions": ["react", "emphasize", "dismiss", "threaten"],
            "notes": ""
        },
        "act_leave": {
            "id": "act_leave",
            "name": "leave",
            "category": "movement",
            "description": "Exit the situation or room.",
            "supports_target_character": False,
            "supports_target_tile": True,
            "supports_utterance": False,
            "supports_action_mood": True,
            "default_pre_action_delay": 1,
            "default_duration_seconds": 5,
            "default_post_action_delay": 1,
            "min_duration_seconds": 1,
            "max_duration_seconds": 30,
            "allowed_intentions": ["exit", "avoid", "escape", "storm off"],
            "notes": ""
        },
        "act_smash": {
            "id": "act_smash",
            "name": "smash",
            "category": "destructive",
            "description": "Break or strike a nearby object in anger.",
            "supports_target_character": False,
            "supports_target_tile": True,
            "supports_utterance": False,
            "supports_action_mood": True,
            "default_pre_action_delay": 1,
            "default_duration_seconds": 3,
            "default_post_action_delay": 2,
            "min_duration_seconds": 1,
            "max_duration_seconds": 15,
            "allowed_intentions": ["destroy", "vent anger", "lash out"],
            "notes": ""
        },
        "act_observe": {
            "id": "act_observe",
            "name": "observe",
            "category": "perception",
            "description": "Look around and pay attention to surroundings.",
            "supports_target_character": False,
            "supports_target_tile": True,
            "supports_utterance": False,
            "supports_action_mood": True,
            "default_pre_action_delay": 1,
            "default_duration_seconds": 5,
            "default_post_action_delay": 1,
            "min_duration_seconds": 1,
            "max_duration_seconds": 30,
            "allowed_intentions": ["inspect", "watch", "notice"],
            "notes": ""
        },
        "act_relax": {
            "id": "act_relax",
            "name": "relax",
            "category": "self_regulation",
            "description": "Rest, calm down, or decompress.",
            "supports_target_character": False,
            "supports_target_tile": False,
            "supports_utterance": False,
            "supports_action_mood": True,
            "default_pre_action_delay": 2,
            "default_duration_seconds": 10,
            "default_post_action_delay": 2,
            "min_duration_seconds": 1,
            "max_duration_seconds": 60,
            "allowed_intentions": ["decompress", "rest", "reset"],
            "notes": ""
        },
        "act_study": {
            "id": "act_study",
            "name": "study",
            "category": "cognitive",
            "description": "Spend time learning or thinking deeply.",
            "supports_target_character": False,
            "supports_target_tile": False,
            "supports_utterance": False,
            "supports_action_mood": True,
            "default_pre_action_delay": 2,
            "default_duration_seconds": 15,
            "default_post_action_delay": 2,
            "min_duration_seconds": 1,
            "max_duration_seconds": 60,
            "allowed_intentions": ["learn", "analyze", "focus"],
            "notes": ""
        }
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
