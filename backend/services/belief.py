from time import time
def update_beliefs(c, focused):
    beliefs=c.setdefault("beliefs",[])
    for p in focused:
        beliefs.append({"entity_id":p["source_id"],"last_seen_position":p["position"],"confidence":p["certainty"],"last_update":time(),"kind":p["type"]})
    c["beliefs"]=beliefs[-30:]
