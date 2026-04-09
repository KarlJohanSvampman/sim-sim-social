from services.conversation import maybe_start_conversation
from services.object_system import pickup_from_object, consume_item, has_consumable_for
from services.db import log_event

def execute(world, c, decision):
    c["speech"] = None
    plan = decision.get("plan", [])
    if not plan:
        c["last_action"]={"type":"idle"}
        return
    step=plan[0]; action=step.get("action","idle")
    if action in ("move","evacuate"):
        c["position"]=step["target"]; c["last_action"]={"type":action}
        if step.get("speech"): c["speech"]=step["speech"]
    elif action=="talk":
        c["speech"]=step.get("speech"); c["last_action"]={"type":"talk"}
        maybe_start_conversation(world,c,step.get("target"))
    elif action=="continue_conversation":
        c["speech"]=step.get("speech"); c["last_action"]={"type":"continue_conversation"}
    elif action=="pickup":
        obj=world["objects"].get(step["target"])
        if obj: pickup_from_object(c,obj,step.get("prefer_effect"))
        c["last_action"]={"type":"pickup"}
    elif action=="consume":
        target_effect=step.get("target_effect")
        if target_effect:
            item=has_consumable_for(c,target_effect)
            if item: consume_item(c,item["id"])
        elif step.get("target"):
            consume_item(c,step["target"])
        c["last_action"]={"type":"consume"}
    elif action=="sleep":
        c["needs"]["fatigue"]=max(0,c["needs"]["fatigue"]-35); c["last_action"]={"type":"sleep"}
    elif action=="use_toilet":
        c["needs"]["bladder"]=0; c["last_action"]={"type":"use_toilet"}
    elif action=="warn":
        c["speech"]=step.get("speech","Danger!"); c["last_action"]={"type":"warn"}
    elif action=="rescue":
        c["last_action"]={"type":"rescue"}
    else:
        c["last_action"]={"type":action}
    log_event(world["tick"], "action", c["id"], None, {"action": c["last_action"], "speech": c.get("speech")})
    if c.get("plan"): c["plan"]=c["plan"][1:]
