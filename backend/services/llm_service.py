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

ALLOWED_EMOTIONS = [
    "calm", "playful", "warm", "awkward", "annoyed", "angry",
    "furious", "fearful", "sad", "smug", "curious", "suspicious"
]


def _append_log(entry: dict):
    world = get_world()
    world.setdefault("llm_logs", [])
    world["llm_logs"].append(entry)
    world["llm_logs"] = world["llm_logs"][-200:]


def _memory_score(item: dict, *, partner: str, topic: str, current_tick: int) -> float:
    score = float(item.get("importance", 0.5) or 0.5) * 10.0
    target = str(item.get("target", "") or "")
    about = str(item.get("about", "") or "")
    text = str(item.get("text", "") or "")
    mem_topic = str(item.get("topic", "") or "")
    source = str(item.get("source", "direct") or "direct")
    speech_act = str(item.get("speech_act", "") or "")
    tick = int(item.get("tick", current_tick) or current_tick)
    age = max(0, current_tick - tick)

    if partner and (target == partner or about == partner):
        score += 8.0
    if topic and (mem_topic == topic or topic.lower() in text.lower()):
        score += 6.0
    if speech_act in ["insult", "threat"]:
        score += 4.0
    if source == "direct":
        score += 1.5
    else:
        score += 0.5

    score -= age * 0.02
    return score


def _smart_memories(character: dict, world: dict, limit: int = 6) -> list[dict]:
    memory = character.get("memory", []) or []
    state = character.get("state", {})
    partner = str(state.get("conversation_partner_id", "") or state.get("awaiting_reply_from_id", "") or "")
    topic = str(state.get("conversation_topic", "") or "")
    current_tick = int(world.get("tick", 0))

    scored = []
    for item in memory:
        if not isinstance(item, dict):
            continue
        score = _memory_score(item, partner=partner, topic=topic, current_tick=current_tick)
        scored.append((score, {
            "kind": item.get("kind", ""),
            "target": item.get("target", ""),
            "about": item.get("about", ""),
            "text": item.get("text", ""),
            "topic": item.get("topic", ""),
            "speech_act": item.get("speech_act", ""),
            "source": item.get("source", "direct"),
            "importance": item.get("importance", 0.5),
            "tick": item.get("tick", 0),
        }))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


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
    recalled_memories = _smart_memories(character, world)

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
- Prefer the MOST RELEVANT memories, not merely the most recent ones

You may:
- Refer to past impressions (views)
- Refer to direct memories or gossip memories if relevant
- Form opinions about others
- Use evaluate_subjective to build impressions

Schema:
{{
  "thought": "...",
  "emotion": "{'|'.join(ALLOWED_EMOTIONS)}",
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
    "action_mood": state.get("action_mood"),
    "partner": partner,
    "topic": topic,
    "motivators": motivators,
    "emotional_temperature": state.get("emotional_temperature"),
    "aggression_bias": state.get("aggression_bias"),
    "drama_bias": state.get("drama_bias"),
    "insecurity": state.get("insecurity")
}, ensure_ascii=False)}

Views:
{json.dumps(views, ensure_ascii=False)}

Grudges:
{json.dumps(grudges, ensure_ascii=False)}

Recent conversation:
{json.dumps(recent_history, ensure_ascii=False)}

Smart recalled memories and gossip:
{json.dumps(recalled_memories, ensure_ascii=False)}
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

    emotion = str(data.get("emotion", "calm")).strip()
    if emotion not in ALLOWED_EMOTIONS:
        emotion = "calm"
    data["emotion"] = emotion

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
                {"role": "system", "content": "Return valid JSON only. No commentary. Include emotion, speech_act, conversation_score, topic, and view_keywords."},
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
