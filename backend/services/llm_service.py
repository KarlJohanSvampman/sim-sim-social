import json
from services.provider_client import call_chat_provider_async
from services.llm_queue import enqueue_llm_call
from services.state import get_world

ALLOWED_ACTIONS = [
    "wait", "move", "speak", "yell", "gesture", "leave",
    "smash", "observe", "relax", "study", "evaluate_subjective"
]

ALLOWED_SPEECH_ACTS = [
    "question", "statement", "request", "insult", "threat", "greeting", "farewell"
]


def _append_log(entry: dict):
    world = get_world()
    world.setdefault("llm_logs", [])
    world["llm_logs"].append(entry)
    world["llm_logs"] = world["llm_logs"][-200:]


def build_decision_prompt(character: dict, world: dict) -> str:
    state = character.get("state", {})
    profile = character.get("profile", {})

    awaiting = state.get("awaiting_reply_from_id", "")
    waiting_on = state.get("waiting_on_character_id", "")
    partner = state.get("conversation_partner_id", "")
    topic = state.get("conversation_topic", "")

    recent_history = character.get("conversation_history", [])[-6:]
    views = character.get("subjective_views", [])[-5:]
    grudges = state.get("grudges", [])[-5:]
    motivators = state.get("weekly_motivators", {})

    anti_greeting = ""
    recent_texts = [str(x.get("text", "")).lower() for x in recent_history]
    if any(("hello" in t) or t.startswith("hi") for t in recent_texts):
        anti_greeting = "Do not greet again unless the conversation has clearly restarted."

    reply_rule = ""
    if awaiting:
        reply_rule = f"""
You are being spoken to by {awaiting}.
Reply directly using speak or yell.
Use a YES-AND style: extend the idea, stay open-ended, and often end with a question.
Set target_character_id to {awaiting}.
"""
    elif waiting_on:
        reply_rule = f"""
You are waiting for {waiting_on}.
Prefer wait and show \"...\" unless there is a strong reason to leave or observe.
"""

    return f"""
Return JSON only.

Choose ONE action.
Never return empty speech.

{anti_greeting}
{reply_rule}

Behavior:
- Overdramatic, impulsive, emotional
- Use "yes, and" conversational style
- Avoid dead-end answers
- End with a question often
- Prefer continuing the current topic if one exists

You may:
- Refer to past impressions (views)
- Form opinions about others
- Use evaluate_subjective to build impressions

Schema:
{{
  "thought": "...",
  "speech_act": "question|statement|request|insult|threat|greeting|farewell",
  "conversation_score": 0,
  "topic": "",
  "view_keywords": [],
  "action": {{
    "name": "{'|'.join(ALLOWED_ACTIONS)}",
    "target_character_id": "",
    "target_tile": {{"x":0,"y":0}},
    "utterance": "",
    "subject_type": "",
    "subject_ref": ""
  }}
}}

Self:
{json.dumps({
    "name": profile.get("name"),
    "mood": state.get("mood"),
    "partner": partner,
    "topic": topic,
    "motivators": motivators
}, ensure_ascii=False)}

Views:
{json.dumps(views, ensure_ascii=False)}

Grudges:
{json.dumps(grudges, ensure_ascii=False)}

Recent conversation:
{json.dumps(recent_history, ensure_ascii=False)}
""".strip()


def _normalize(data: dict):
    act = data.get("action", {}) or {}
    name = act.get("name", "wait")

    if name not in ALLOWED_ACTIONS:
        act["name"] = "wait"
        act["target_character_id"] = ""
        act["utterance"] = ""

    if act.get("name") in ["speak", "yell"] and not str(act.get("utterance") or "").strip():
        act["name"] = "wait"
        act["target_character_id"] = ""
        act["utterance"] = ""

    speech_act = str(data.get("speech_act", "statement")).strip()
    if speech_act not in ALLOWED_SPEECH_ACTS:
        speech_act = "statement"
    data["speech_act"] = speech_act

    try:
        score = float(data.get("conversation_score", 50))
    except Exception:
        score = 50.0
    data["conversation_score"] = max(0.0, min(100.0, score))

    data["topic"] = str(data.get("topic", "")).strip()

    kws = data.get("view_keywords") or []
    if not isinstance(kws, list):
        kws = []
    data["view_keywords"] = [str(x).strip() for x in kws[:8] if str(x).strip()]

    if act.get("name") == "evaluate_subjective":
        act["subject_type"] = str(act.get("subject_type") or "character").strip()
        act["subject_ref"] = str(act.get("subject_ref") or act.get("target_character_id") or "").strip()

    data["action"] = act
    return data


async def maybe_run_decision_llm(character, world):
    prompt = build_decision_prompt(character, world)

    async def job():
        return await call_chat_provider_async(
            world.get("config", {}).get("llm_provider", {}),
            [
                {"role": "system", "content": "Return valid JSON only. No commentary. Include speech_act, conversation_score, topic, and view_keywords."},
                {"role": "user", "content": prompt},
            ]
        )

    result = await enqueue_llm_call(job)
    _append_log({"prompt": prompt, "provider_result": result})

    try:
        if result.get("text"):
            return _normalize(json.loads(result["text"]))
    except Exception:
        pass

    return None
