from services.state import get_world
from services.hazards import inject_hazard as inject_hazard_into_world
def inject_news(content):
    get_world().setdefault("news", []).append({"content":content})
def inject_hazard(hazard_type, location, intensity=1.0):
    inject_hazard_into_world(get_world(), hazard_type, location, intensity)
def get_character(char_id):
    return get_world()["characters"].get(char_id)
def patch_character(char_id, updates):
    world=get_world()
    c=world["characters"].get(char_id)
    if not c:
        return None
    for k,v in updates.items():
        if isinstance(v, dict) and isinstance(c.get(k), dict):
            c[k].update(v)
        else:
            c[k]=v
    return c
