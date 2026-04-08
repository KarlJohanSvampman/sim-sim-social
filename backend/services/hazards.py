from math import sqrt
def tick_hazards(world):
    hazards=[]
    for h in world.get("hazards", []):
        h=dict(h)
        h["ticks_remaining"]=h.get("ticks_remaining",10)-1
        if h["ticks_remaining"]<=0:
            continue
        hazards.append(h)
        if h["type"]=="fire":
            hazards.append({"type":"smoke","location":h["location"],"intensity":max(0.2,h.get("intensity",1.0)*0.7),"ticks_remaining":max(1,h["ticks_remaining"]-1)})
    world["hazards"]=hazards
def inject_hazard(world, hazard_type, location, intensity=1.0):
    world.setdefault("hazards", []).append({"type":hazard_type,"location":location,"intensity":intensity,"ticks_remaining":12})
def apply_hazard_damage(world, character):
    if character.get("is_unconscious"):
        return
    px,py=character["position"]["x"],character["position"]["y"]
    for h in world.get("hazards", []):
        hx,hy=h["location"]["x"],h["location"]["y"]
        d=sqrt((px-hx)**2+(py-hy)**2)
        if d<=1.2:
            if h["type"]=="fire":
                character["health"]=max(0,character["health"]-6*h.get("intensity",1.0))
            elif h["type"]=="smoke":
                character["smoke_inhalation"]=min(100,character["smoke_inhalation"]+5*h.get("intensity",1.0))
                character["health"]=max(0,character["health"]-1.5*h.get("intensity",1.0))
    if character["health"]<=0 or character["smoke_inhalation"]>=80 or character["intoxication"]>=95:
        character["is_unconscious"]=True
