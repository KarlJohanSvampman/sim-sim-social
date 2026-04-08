import os, json
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel, ValidationError, Field
from typing import Any, Optional, Literal, List
from services.pathfinding import astar
from services.object_system import has_consumable_for

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "decision_prompt.txt"

class PlanStep(BaseModel):
    action: Literal["move","talk","wait","investigate","continue_conversation","pickup","consume","sleep","use_toilet","evacuate","warn","rescue"]
    target: Any = None
    speech: Optional[str] = None
    prefer_effect: Optional[str] = None
    target_effect: Optional[str] = None

class Decision(BaseModel):
    plan: List[PlanStep] = Field(default_factory=list)
    thoughts: str
    emotion_update: dict = Field(default_factory=dict)

def _load_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")

def _make_multistep_need_plan(c, world, goal):
    if c.get("is_unconscious"):
        return [{"action":"wait"}]
    if goal["type"] == "consume_food":
        item = has_consumable_for(c, "hunger")
        if item:
            return [{"action":"consume","target":item["id"]}]
    if goal["type"] == "consume_drink":
        item = has_consumable_for(c, "thirst")
        if item:
            return [{"action":"consume","target":item["id"]}]
    if "target_object" not in goal:
        return None
    obj = world["objects"][goal["target_object"]]
    pos = c["position"]
    target = (obj["position"]["x"], obj["position"]["y"], obj["position"]["z"])
    path = astar(world, (pos["x"],pos["y"],pos["z"]), target)
    pre = []
    if len(path) > 1:
        step = path[1]
        pre.append({"action":"move","target":{"x":step[0],"y":step[1],"z":step[2]}})
    if goal["type"] == "eat":
        return pre + [{"action":"pickup","target":goal["target_object"],"prefer_effect":"hunger"},{"action":"consume","target_effect":"hunger"}]
    if goal["type"] == "drink":
        return pre + [{"action":"pickup","target":goal["target_object"],"prefer_effect":"thirst"},{"action":"consume","target_effect":"thirst"}]
    if goal["type"] == "sleep":
        return pre + [{"action":"sleep","target":goal["target_object"]}]
    if goal["type"] == "use_toilet":
        return pre + [{"action":"use_toilet","target":goal["target_object"]}]
    return None

def _fallback_decide(c, world, context):
    if c.get("is_unconscious"):
        return {"plan":[{"action":"wait"}],"thoughts":"Unconscious.","emotion_update":{}}
    if context.get("hazards"):
        return {"plan":[{"action":"warn","speech":"Fire!"},{"action":"evacuate","target":{"x":1,"y":1,"z":0}}],"thoughts":"Danger nearby. Get out.","emotion_update":{"stress":0.3}}
    if c.get("conversation_id"):
        return {"plan":[{"action":"continue_conversation","speech":"Okay."}],"thoughts":"Stay in the conversation for now.","emotion_update":{}}
    goal=context["goal"]
    plan=_make_multistep_need_plan(c, world, goal)
    if plan:
        impair=[]
        if c.get("intoxication",0)>30: impair.append("dizzy")
        if c.get("withdrawal",{}).get("tobacco",0)>10: impair.append("restless")
        thoughts=f"Handling need: {goal['type']}."
        if impair: thoughts += " Feeling " + ", ".join(impair) + "."
        return {"plan":plan,"thoughts":thoughts,"emotion_update":{}}
    pos=c["position"]
    target=goal["target"]
    path=astar(world,(pos["x"],pos["y"],pos["z"]),(target["x"],target["y"],target["z"]))
    if len(path)>1:
        step=path[1]
        return {"plan":[{"action":"move","target":{"x":step[0],"y":step[1],"z":step[2]}}],"thoughts":f"Moving toward {goal['type']}.","emotion_update":{}}
    return {"plan":[{"action":goal["type"],"target":target}],"thoughts":f"At target for {goal['type']}.","emotion_update":{}}

def _validate_or_raise(data):
    d = Decision.model_validate(data)
    return d.model_dump()

def decide_action(c, world, context):
    api_key=os.getenv("OPENAI_API_KEY")
    model=os.getenv("OPENAI_MODEL","gpt-4o-mini")
    prompt=_load_prompt()
    if not api_key:
        return _fallback_decide(c, world, context)
    client=OpenAI(api_key=api_key)
    inp=json.dumps(context, ensure_ascii=False)
    attempts=[
        {"instructions":prompt,"input":inp},
        {"instructions":prompt+"\nYour previous output was invalid. Return ONLY valid JSON matching the schema exactly.","input":inp},
    ]
    for attempt in attempts:
        try:
            response=client.responses.create(model=model,instructions=attempt["instructions"],input=attempt["input"],temperature=0.6,max_output_tokens=500)
            parsed=json.loads(response.output_text)
            return _validate_or_raise(parsed)
        except (ValidationError, ValueError, json.JSONDecodeError, Exception):
            continue
    return _fallback_decide(c, world, context)
