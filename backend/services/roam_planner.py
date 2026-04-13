from __future__ import annotations
import random
from services.state import get_world

SOCIAL_ROOM_TAGS = {"living_room", "yard", "kitchen"}
QUIET_ROOM_TAGS = {"bedroom", "study", "office"}

def _manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def _candidate_tiles(character, max_radius: int = 10):
    world = get_world()
    pos = character.position
    out = []
    for tile in world["grid"]["tiles"].values():
        if tile.get("blocks_movement"):
            continue
        dist = _manhattan((pos["x"], pos["y"]), (tile["x"], tile["y"]))
        if 1 <= dist <= max_radius:
            out.append((tile, dist))
    return out

def _interest_bias(character, tile):
    bias = 0.0
    room_tag = tile.get("room_tag")
    interests = {(i.category, i.tag): (i.rank or 99) for i in character.profile.interests}
    if room_tag == "kitchen" and ("Activity", "cooking") in interests:
        bias += 5.0
    if room_tag in {"study", "office"} and any(i.category == "Knowledge" for i in character.profile.interests):
        bias += 4.0
    if room_tag in SOCIAL_ROOM_TAGS and character.profile.intelligence_spectrum > 20:
        bias += 3.0
    if room_tag in QUIET_ROOM_TAGS and character.profile.intelligence_spectrum < -20:
        bias += 3.0
    return bias

def _need_bias(character, tile):
    bias = 0.0
    needs = character.state.needs
    room_tag = tile.get("room_tag")
    obj = tile.get("object") or {}
    obj_name = str(obj.get("name", "")).lower()
    obj_cat = str(obj.get("category", "")).lower()

    if needs.sleep >= 60 and (room_tag == "bedroom" or obj_name == "bed" or obj_cat == "bed"):
        bias += 10.0
    if needs.hunger >= 60 and (room_tag == "kitchen" or obj_name in {"food", "stove"} or obj_cat in {"food", "stove"}):
        bias += 8.0
    if needs.thirst >= 60 and room_tag in {"kitchen", "living_room"}:
        bias += 4.0
    if needs.bladder >= 60 and (room_tag == "bathroom" or obj_name == "restroom" or obj_cat == "restroom"):
        bias += 10.0
    if character.state.stress >= 50 and room_tag in {"living_room", "yard", "bedroom"}:
        bias += 4.0
    return bias

def _social_bias(character, tile):
    room_tag = tile.get("room_tag")
    if character.profile.intelligence_spectrum > 25 and room_tag in SOCIAL_ROOM_TAGS:
        return 2.5
    return 0.0

def choose_roam_destination(character, roam_budget: int):
    candidates = _candidate_tiles(character, max_radius=max(4, min(12, roam_budget + 4)))
    if not candidates:
        return None

    scored = []
    for tile, dist in candidates:
        score = 0.0
        score += _interest_bias(character, tile)
        score += _need_bias(character, tile)
        score += _social_bias(character, tile)
        score += max(0, 3 - abs(dist - roam_budget) * 0.5)
        score += random.random() * 1.5
        scored.append((score, tile, dist))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_tile, best_dist = scored[0]
    return {
        "x": best_tile["x"],
        "y": best_tile["y"],
        "z": best_tile.get("z", 0),
        "room_tag": best_tile.get("room_tag"),
        "tile_type": best_tile.get("tile_type"),
        "estimated_distance": best_dist,
        "score": round(best_score, 2)
    }
