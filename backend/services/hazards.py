def tick_hazards(world):
    hazards=[]
    for h in world.get("hazards", []):
        h=dict(h); h["ticks_remaining"]=h.get("ticks_remaining",10)-1
        if h["ticks_remaining"]>0: hazards.append(h)
    world["hazards"]=hazards
def inject_hazard(world, hazard_type, location, intensity=1.0):
    world.setdefault("hazards", []).append({"type":hazard_type,"location":location,"intensity":intensity,"ticks_remaining":12})
def apply_hazard_damage(world, character):
    return
