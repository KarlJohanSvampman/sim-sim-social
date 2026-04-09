import os, json, random
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel, ValidationError

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "conversation_turn_prompt.txt"

class ConversationTurn(BaseModel):
    speech: str
    end_conversation: bool = False
    emotion_update: dict = {}
    relationship_update: dict = {}

def _fallback_turn(speaker, other, conv, world):
    goal = conv.get("goal", "socialize")
    if goal == "flirt":
        return {"speech":"You look nice today.","end_conversation":False,"emotion_update":{},"relationship_update":{"trust":0.5,"affection":2.0,"fear":0.0}}
    if goal == "interrogate":
        return {"speech":"Where were you earlier?","end_conversation":False,"emotion_update":{},"relationship_update":{"trust":-0.5,"affection":-0.2,"fear":1.0}}
    if goal == "reassure":
        return {"speech":"It's okay, you're safe.","end_conversation":False,"emotion_update":{},"relationship_update":{"trust":1.5,"affection":0.5,"fear":-1.0}}
    if goal == "manipulate":
        return {"speech":"You can trust me on this.","end_conversation":False,"emotion_update":{},"relationship_update":{"trust":0.8,"affection":0.1,"fear":0.2}}
    return {"speech":"Mm-hm.","end_conversation":False,"emotion_update":{},"relationship_update":{"trust":0.2,"affection":0.1,"fear":0.0}}

def generate_conversation_turn(speaker, other, conv, world):
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = {
        "speaker":{"id":speaker["id"],"name":speaker["name"]},
        "other":{"id":other["id"],"name":other["name"]},
        "conversation":conv,
        "speaker_state":{"needs":speaker["needs"],"intoxication":speaker.get("intoxication",0.0),"cravings":speaker.get("cravings", {}),"withdrawal":speaker.get("withdrawal", {})},
        "hazards":world.get("hazards", [])[-5:]
    }
    api_key=os.getenv("OPENAI_API_KEY"); model=os.getenv("OPENAI_MODEL","gpt-4o-mini")
    if not api_key: return _fallback_turn(speaker, other, conv, world)
    client=OpenAI(api_key=api_key)
    tries=[prompt, prompt + "\nReturn ONLY valid JSON matching the schema exactly."]
    for instructions in tries:
        try:
            response=client.responses.create(model=model,instructions=instructions,input=json.dumps(payload, ensure_ascii=False),temperature=0.7,max_output_tokens=180)
            data=json.loads(response.output_text)
            validated=ConversationTurn.model_validate(data)
            return validated.model_dump()
        except (ValidationError, json.JSONDecodeError, Exception):
            continue
    return _fallback_turn(speaker, other, conv, world)
