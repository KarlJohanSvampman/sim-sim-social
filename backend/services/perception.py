from math import sqrt
def perceive(character, world):
    out=[]; me=character["position"]
    for oid, other in world["characters"].items():
        if oid==character["id"]: continue
        d=sqrt((me["x"]-other["position"]["x"])**2+(me["y"]-other["position"]["y"])**2)
        if d<=character["sight_radius"]:
            out.append({"type":"visual","source_id":oid,"position":other["position"],"certainty":max(0.1,1.0-d/character["sight_radius"]),"data":{"entity_type":"character","appearance":other["name"],"action":other.get("last_action",{}).get("type","idle")}})
        if other.get("speech") and d<=character["hearing_radius"]:
            out.append({"type":"auditory","source_id":oid,"position":other["position"],"certainty":max(0.1,1.0-d/character["hearing_radius"]),"data":{"entity_type":"character","appearance":other["name"],"action":"speech","sound":other["speech"]}})
    return out
