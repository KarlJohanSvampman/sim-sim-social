from copy import deepcopy

WORLD = {
    "tick": 0,
    "grid": {"width": 12, "height": 12, "tiles": {}},
    "characters": {},
    "objects": {},
    "hazards": [],
    "emergency_services": {"firefighters": [], "paramedics": []},
    "news": [],
    "conversations": {}
}

def init_world():
    if WORLD["grid"]["tiles"]:
        return
    for y in range(WORLD["grid"]["height"]):
        for x in range(WORLD["grid"]["width"]):
            WORLD["grid"]["tiles"][f"{x},{y},0"] = {"x":x,"y":y,"z":0,"type":"floor","blocks_movement":False,"blocks_sight":False}
    WORLD["objects"] = {
        "bed_1": {"id":"bed_1","type":"bed","name":"Bed","position":{"x":2,"y":2,"z":0},"inventory":[]},
        "toilet_1": {"id":"toilet_1","type":"toilet","name":"Toilet","position":{"x":2,"y":9,"z":0},"inventory":[]},
        "sink_1": {"id":"sink_1","type":"sink","name":"Sink","position":{"x":3,"y":8,"z":0},"inventory":[{"id":"water_1","type":"consumable","name":"Water","effects":{"thirst":-25},"size":"small"}]},
        "fridge_1": {"id":"fridge_1","type":"fridge","name":"Fridge","position":{"x":8,"y":2,"z":0},"inventory":[{"id":"apple_1","type":"consumable","name":"Apple","effects":{"hunger":-20},"size":"small"},{"id":"beer_1","type":"consumable","name":"Beer","effects":{"thirst":-8,"intoxication":15,"alcohol_use":8},"size":"small"}]},
        "cabinet_1": {"id":"cabinet_1","type":"cabinet","name":"Cabinet","position":{"x":9,"y":2,"z":0},"inventory":[{"id":"cigarette_1","type":"consumable","name":"Cigarette","effects":{"intoxication":2,"tobacco_use":6},"size":"small"}]}
    }
    base = {
        "sight_radius":6,"hearing_radius":5,"goal":None,"plan":[],"memory":[],"beliefs":[],"compressed_memory":[],"suspicion":{},
        "deception":0.1,"thoughts":"...","speech":None,"last_action":{"type":"idle"},"conversation_id":None,
        "inventory":[],"intoxication":0.0,"health":100.0,"smoke_inhalation":0.0,"is_unconscious":False,
        "carry_capacity_small":4,"hands":{"left":None,"right":None},
        "addiction":{"alcohol":0.0,"tobacco":0.0},"cravings":{"alcohol":0.0,"tobacco":0.0},"withdrawal":{"alcohol":0.0,"tobacco":0.0}
    }
    WORLD["characters"] = {
        "npc_1": dict(base, **{"id":"npc_1","name":"Ada","position":{"x":2,"y":2,"z":0},"needs":{"hunger":10,"thirst":15,"fatigue":5,"bladder":10},"deception":0.25}),
        "npc_2": dict(base, **{"id":"npc_2","name":"Bryn","position":{"x":9,"y":9,"z":0},"needs":{"hunger":20,"thirst":10,"fatigue":8,"bladder":12}})
    }
    WORLD["emergency_services"]["firefighters"] = [{"id":"fire_1","position":{"x":1,"y":1,"z":0},"status":"idle"}]
    WORLD["emergency_services"]["paramedics"] = [{"id":"medic_1","position":{"x":1,"y":3,"z":0},"status":"idle"}]

def get_world():
    return WORLD

def get_world_snapshot():
    return deepcopy(WORLD)
