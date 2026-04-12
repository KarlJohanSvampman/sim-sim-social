OBJECTS = {
    "obj_crate_1": {
        "id": "obj_crate_1",
        "name": "Crate",
        "model": "models/crate.glb",
        "texture": "textures/crate.png",
        "icon": "icons/crate.png",
        "category": "storage",
        "description": "A wooden storage crate.",
        "weight": 12.0,
        "portable": True,
        "interactions": ["carry", "place", "inspect"],
        "is_container": True,
        "capacity": 6,
        "items": []
    },
    "obj_bench_1": {
        "id": "obj_bench_1",
        "name": "Bench",
        "model": "models/bench.glb",
        "texture": "textures/bench.png",
        "icon": "icons/bench.png",
        "category": "furniture",
        "description": "A public bench.",
        "weight": 40.0,
        "portable": False,
        "interactions": ["sit", "inspect"],
        "is_container": False,
        "capacity": 0,
        "items": []
    }
}

def list_objects():
    return list(OBJECTS.values())

def get_object(obj_id):
    return OBJECTS.get(obj_id)

def upsert_object(payload):
    OBJECTS[payload["id"]] = payload
    return payload

def delete_object(obj_id):
    OBJECTS.pop(obj_id, None)
