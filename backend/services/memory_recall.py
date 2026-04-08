import os, json
from pathlib import Path
from openai import OpenAI

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "memory_recall_prompt.txt"

def recall_for_question(c, question):
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = {"identity":{"id":c["id"],"name":c["name"]},"compressed_memory":c.get("compressed_memory", [])[-6:],"recent_memory":c.get("memory", [])[-8:],"question":question,"suspicion":c.get("suspicion", {}),"intoxication":c.get("intoxication",0.0),"cravings":c.get("cravings", {}),"withdrawal":c.get("withdrawal", {})}
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        cm = c.get("compressed_memory", [])
        if cm:
            top = cm[-1]
            return {"spoken_out_loud":top.get("summary_belief","I remember it vaguely."),"confidence":float(top.get("confidence_in_memory",0.5)),"volatility":float(top.get("volatility",0.3))}
        return {"spoken_out_loud":"I don't remember much about that.","confidence":0.3,"volatility":0.5}
    client = OpenAI(api_key=api_key)
    try:
        response = client.responses.create(model=model,instructions=prompt,input=json.dumps(payload, ensure_ascii=False),temperature=0.7,max_output_tokens=220)
        return json.loads(response.output_text)
    except Exception:
        return {"spoken_out_loud":"I don't remember much about that.","confidence":0.3,"volatility":0.5}
