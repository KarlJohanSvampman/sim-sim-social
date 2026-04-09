from services.object_system import has_consumable_for
def decide_goal(c, world):
    n=c["needs"]
    if c.get("is_unconscious"): return {"type":"wait"}
    if n["bladder"]>80: return {"type":"use_toilet","target_object":"toilet_1"}
    if n["thirst"]>60:
        if has_consumable_for(c,"thirst"): return {"type":"consume_drink","target_item_effect":"thirst"}
        return {"type":"drink","target_object":"sink_1"}
    if n["hunger"]>60:
        if has_consumable_for(c,"hunger"): return {"type":"consume_food","target_item_effect":"hunger"}
        return {"type":"eat","target_object":"fridge_1"}
    if n["fatigue"]>70: return {"type":"sleep","target_object":"bed_1"}
    if c["cravings"]["alcohol"]>60: return {"type":"drink","target_object":"fridge_1"}
    if c["cravings"]["tobacco"]>60: return {"type":"eat","target_object":"cabinet_1"}
    return {"type":"socialize","target":{"x":6,"y":6,"z":0}}
