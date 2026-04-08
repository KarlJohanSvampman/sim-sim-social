from services.pathfinding import astar
def dispatch_services(world):
    fire_targets=[h["location"] for h in world.get("hazards", []) if h["type"]=="fire"]
    unconscious=[c for c in world["characters"].values() if c.get("is_unconscious")]
    for svc in world["emergency_services"]["firefighters"]:
        if fire_targets:
            target=fire_targets[0]
            svc["status"]="responding"
            path=astar(world,(svc["position"]["x"],svc["position"]["y"],svc["position"]["z"]),(target["x"],target["y"],target["z"]))
            if len(path)>1:
                step=path[1]
                svc["position"]={"x":step[0],"y":step[1],"z":step[2]}
            else:
                removed=False
                remaining=[]
                for h in world["hazards"]:
                    if not removed and h["type"]=="fire":
                        removed=True
                        continue
                    remaining.append(h)
                world["hazards"]=remaining
                svc["status"]="extinguishing"
        else:
            svc["status"]="idle"
    for svc in world["emergency_services"]["paramedics"]:
        if unconscious:
            target_char=unconscious[0]
            svc["status"]="responding"
            path=astar(world,(svc["position"]["x"],svc["position"]["y"],svc["position"]["z"]),(target_char["position"]["x"],target_char["position"]["y"],target_char["position"]["z"]))
            if len(path)>1:
                step=path[1]
                svc["position"]={"x":step[0],"y":step[1],"z":step[2]}
            else:
                target_char["is_unconscious"]=False
                target_char["health"]=max(20,target_char["health"])
                target_char["smoke_inhalation"]=max(0,target_char["smoke_inhalation"]-30)
                svc["status"]="treating"
        else:
            svc["status"]="idle"
