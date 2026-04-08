import os, json
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel, ValidationError

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "conversation_turn_prompt.txt"

class ConversationTurn(BaseModel):
    speech: str
    end_conversation: bool = False
    emotion_update: dict = {}

def generate_conversation_turn(speaker, other, conv, world):
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = {
        "speaker": {"id":speaker["id"],"name":speaker["name"]},
        "other": {"id":other["id"],"name":other["name"]},
        "conversation": conv,
        "speaker_state": {
            "needs": speaker["needs"],
            "suspicion": speaker.get("suspicion", {}),
            "memory": speaker.get("memory", [])[-6:],
            "compressed_memory": speaker.get("compressed_memory", [])[-4:],
            "intoxication": speaker.get("intoxication", 0.0),
            "cravings": speaker.get("cravings", {}),
            "withdrawal": speaker.get("withdrawal", {}),
            "health": speaker.get("health", 100.0),
            "smoke_inhalation": speaker.get("smoke_inhalation", 0.0)
        },
        "hazards": world.get("hazards", [])[-5:]
    }
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        return {"speech":"Mm-hm.","end_conversation":False,"emotion_update":{}}
    client = OpenAI(api_key=api_key)
    tries=[prompt, prompt + "\nReturn ONLY valid JSON matching the schema exactly."]
    for instructions in tries:
        try:
            response = client.responses.create(model=model,instructions=instructions,input=json.dumps(payload, ensure_ascii=False),temperature=0.7,max_output_tokens=180)
            data = json.loads(response.output_text)
            validated = ConversationTurn.model_validate(data)
            return validated.model_dump()
        except (ValidationError, json.JSONDecodeError, Exception):
            continue
    return {"speech":"Mm-hm.","end_conversation":False,"emotion_update":{}}
