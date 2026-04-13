from __future__ import annotations
from pathlib import Path
from typing import Any
from models.tagged_character import ActivityType, CharacterV2
from services.activity_engine import can_start_activity
from services.activity_requirements import is_activity_available

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "decision_prompt_v2.txt"
TRIGGER_DOUBLES = {(1,1), (4,4), (6,6)}

def load_prompt_contract() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "decision prompt missing"

def _sorted_interests(character: CharacterV2) -> list[dict[str, Any]]:
    interests = character.profile.interests[:]
    interests.sort(key=lambda x: (x.rank if x.rank is not None else 9999, -(x.weight or 0)))
    return [i.model_dump() for i in interests]

def _top_interest(character: CharacterV2, category: str | None = None) -> str | None:
    interests = _sorted_interests(character)
    if category:
        interests = [i for i in interests if i["category"] == category]
    return interests[0]["tag"] if interests else None

def build_prompt_payload(character: CharacterV2, available_requirements: set[str], current_tick: int) -> dict[str, Any]:
    return {
        "tick": current_tick,
        "contract": load_prompt_contract(),
        "character_profile": character.profile.model_dump(),
        "character_state": character.state.model_dump(),
        "available_requirements": sorted(available_requirements),
    }

def choose_activity_action(character: CharacterV2, available_requirements: set[str], current_tick: int) -> dict[str, Any]:
    state = character.state
    needs = state.needs
    candidate_actions = []

    if needs.sleep >= 80:
        candidate_actions.append({"type": "engage_activity", "activity_type": "recreative", "tag": "sleep", "hours": 0.8})
    if needs.hunger >= 75:
        candidate_actions.append({"type": "engage_activity", "activity_type": "recreative", "tag": "eat", "hours": 0.3})
    if needs.thirst >= 75 or state.stress >= 70:
        candidate_actions.append({"type": "engage_activity", "activity_type": "recreative", "tag": "stress_relief", "hours": 0.3})

    eq_skew = character.profile.intelligence_spectrum > 25
    iq_skew = character.profile.intelligence_spectrum < -25

    if eq_skew and character.profile.contacts:
        top_contact = max(character.profile.contacts, key=lambda c: c.hours)
        candidate_actions.append({"type": "engage_activity", "activity_type": "social", "tag": "phone_call", "hours": 0.4, "contacts": [top_contact.character_id]})

    if iq_skew:
        candidate_actions.append({"type": "engage_activity", "activity_type": "study", "tag": _top_interest(character, "Knowledge") or "general_study", "hours": 0.6})
    else:
        candidate_actions.append({"type": "engage_activity", "activity_type": "practice", "tag": _top_interest(character, "Activity") or "general_practice", "hours": 0.6})

    for action in candidate_actions:
        available, discovered = is_activity_available(character, action["activity_type"], action["tag"])
        if not available:
            continue
        ok, reason = validate_decision_action(character, {"action": action}, available_requirements | discovered)
        if ok:
            return {"thought": f"Starting {action['activity_type']}:{action['tag']} because conditions are satisfied.", "action": action}

    return {"thought": "No suitable activity is available right here, so roaming is better.", "action": {"type": "wander"}}

def choose_action_v2(character: CharacterV2, available_requirements: set[str], current_tick: int) -> dict[str, Any]:
    state = character.state
    needs = state.needs

    if state.current_activity is not None:
        if needs.thirst >= 95 or needs.bladder >= 95:
            return {"thought": "An urgent need overrides the current activity.", "action": {"type": "interrupt_activity", "reason": "urgent_need"}}
        return {"thought": "Continuing the current activity.", "action": {"type": "continue_activity"}}

    dice = getattr(character.state, "last_idle_roll", None)
    if dice and tuple(dice) in TRIGGER_DOUBLES:
        return choose_activity_action(character, available_requirements, current_tick)

    return {"thought": "No activity trigger was rolled, so keep roaming until the next stop.", "action": {"type": "wander"}}

def validate_decision_action(character: CharacterV2, decision: dict[str, Any], available_requirements: set[str]) -> tuple[bool, str]:
    action = decision.get("action", {})
    action_type = action.get("type")
    if action_type in {"continue_activity", "interrupt_activity", "wander"}:
        return True, "ok"
    if action_type != "engage_activity":
        return False, f"unsupported action type: {action_type}"
    try:
        activity_type = ActivityType(action["activity_type"])
    except Exception:
        return False, "invalid activity_type"
    return can_start_activity(character, activity_type, str(action.get("tag", "")), float(action.get("hours", 0)), available_requirements, action.get("contacts"))
