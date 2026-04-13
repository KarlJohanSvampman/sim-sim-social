from __future__ import annotations
import math
from typing import Iterable
from models.tagged_character import ActivityHistoryEntry, ActivityType, CharacterV2, CurrentActivity, KnowledgeEntry

ACTIVITY_TICK_HOURS = 0.1

def _find_or_create_activity_entry(character: CharacterV2, tag: str) -> ActivityHistoryEntry:
    for entry in character.profile.activities:
        if entry.tag == tag:
            return entry
    entry = ActivityHistoryEntry(tag=tag, total_hours=0.0)
    character.profile.activities.append(entry)
    return entry

def _find_or_create_knowledge_entry(character: CharacterV2, tag: str) -> KnowledgeEntry:
    for entry in character.profile.knowledge:
        if entry.tag == tag:
            return entry
    entry = KnowledgeEntry(tag=tag, total_hours=0.0)
    character.profile.knowledge.append(entry)
    return entry

def _find_contacts(character: CharacterV2, contact_ids: Iterable[str]):
    wanted = set(contact_ids)
    return [c for c in character.profile.contacts if c.character_id in wanted]

def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def study_efficiency_multiplier(character: CharacterV2) -> float:
    iq_bias = max(0.0, -character.profile.intelligence_spectrum) / 100.0
    focus_factor = _lerp(0.6, 1.2, character.state.focus / 100.0)
    fatigue_factor = _lerp(1.0, 0.6, character.state.fatigue / 100.0)
    stress_factor = _lerp(1.0, 0.75, character.state.stress / 100.0)
    intox_factor = _lerp(1.0, 0.5, character.state.intoxication / 100.0)
    return (1.0 + 0.15 * iq_bias) * focus_factor * fatigue_factor * stress_factor * intox_factor

def social_efficiency_multiplier(character: CharacterV2) -> float:
    eq_bias = max(0.0, character.profile.intelligence_spectrum) / 100.0
    focus_factor = _lerp(0.8, 1.1, character.state.focus / 100.0)
    fatigue_factor = _lerp(1.0, 0.7, character.state.fatigue / 100.0)
    stress_factor = _lerp(1.0, 0.85, character.state.stress / 100.0)
    intox_factor = _lerp(1.0, 0.7, character.state.intoxication / 100.0)
    return (1.0 + 0.15 * eq_bias) * focus_factor * fatigue_factor * stress_factor * intox_factor

def practical_proficiency(character: CharacterV2, tag: str) -> float:
    practice_hours = next((x.total_hours for x in character.profile.activities if x.tag == tag), 0.0)
    knowledge_hours = next((x.total_hours for x in character.profile.knowledge if x.tag == tag), 0.0)
    practice_score = math.sqrt(practice_hours)
    knowledge_score = math.sqrt(knowledge_hours)
    base = 0.7 * practice_score + 0.3 * knowledge_score
    focus_modifier = _lerp(0.6, 1.2, character.state.focus / 100.0)
    fatigue_modifier = _lerp(1.0, 0.6, character.state.fatigue / 100.0)
    stress_modifier = _lerp(1.0, 0.75, character.state.stress / 100.0)
    intox_modifier = _lerp(1.0, 0.5, character.state.intoxication / 100.0)
    return base * focus_modifier * fatigue_modifier * stress_modifier * intox_modifier

def can_start_activity(character: CharacterV2, activity_type: ActivityType, tag: str, hours: float, available_requirements: set[str], contacts: list[str] | None = None) -> tuple[bool, str]:
    if hours < 0.1:
        return False, "hours must be at least 0.1"
    if activity_type == ActivityType.SOCIAL:
        if "smartphone" not in available_requirements and "computer" not in available_requirements:
            return False, "social activity requires smartphone or computer"
        if not contacts:
            return False, "social activity requires at least one contact"
    return True, "ok"

def start_activity(character: CharacterV2, tick: int, activity_type: ActivityType, tag: str, hours: float, requirements: list[str] | None = None, contacts: list[str] | None = None) -> None:
    character.state.current_activity = CurrentActivity(activity_type=activity_type, tag=tag, hours_total=hours, hours_completed=0.0, tick_size_hours=0.1, requirements=requirements or [], contacts=contacts or [], started_at_tick=tick)

def interrupt_activity(character: CharacterV2, reason: str) -> None:
    if character.state.current_activity is not None:
        character.memory.append({"type": "activity_interrupted", "reason": reason, "activity": character.state.current_activity.model_dump()})
    character.state.current_activity = None

def finish_activity(character: CharacterV2) -> None:
    if character.state.current_activity is None:
        return
    character.memory.append({"type": "activity_finished", "activity": character.state.current_activity.model_dump()})
    character.state.current_activity = None

def apply_general_activity_costs(character: CharacterV2, activity_type: ActivityType, dt: float) -> None:
    if activity_type == ActivityType.STUDY:
        character.state.fatigue = min(100.0, character.state.fatigue + 0.6 * dt * 10)
        character.state.needs.hunger = min(100.0, character.state.needs.hunger + 0.2 * dt * 10)
        character.state.needs.thirst = min(100.0, character.state.needs.thirst + 0.25 * dt * 10)
    elif activity_type == ActivityType.PRACTICE:
        character.state.fatigue = min(100.0, character.state.fatigue + 0.9 * dt * 10)
        character.state.needs.hunger = min(100.0, character.state.needs.hunger + 0.35 * dt * 10)
        character.state.needs.thirst = min(100.0, character.state.needs.thirst + 0.35 * dt * 10)
    elif activity_type == ActivityType.SOCIAL:
        character.state.fatigue = min(100.0, character.state.fatigue + 0.4 * dt * 10)
        character.state.stress = max(0.0, character.state.stress - 0.2 * dt * 10)
    character.state.needs.bladder = min(100.0, character.state.needs.bladder + 0.2 * dt * 10)

def apply_recreative_effects(character: CharacterV2, tag: str, dt: float) -> None:
    if tag == "sleep":
        character.state.fatigue = max(0.0, character.state.fatigue - 2.5 * dt * 10)
        character.state.needs.sleep = max(0.0, character.state.needs.sleep - 2.5 * dt * 10)
        character.state.stress = max(0.0, character.state.stress - 0.5 * dt * 10)
    elif tag == "eat":
        character.state.needs.hunger = max(0.0, character.state.needs.hunger - 2.0 * dt * 10)
    elif tag == "hygiene":
        character.state.stress = max(0.0, character.state.stress - 0.8 * dt * 10)
        character.state.needs.bladder = max(0.0, character.state.needs.bladder - 3.0 * dt * 10)

def distribute_social_hours(character: CharacterV2, contact_ids: list[str], dt: float) -> None:
    if not contact_ids:
        return
    contacts = _find_contacts(character, contact_ids)
    if not contacts:
        return
    share = dt / len(contacts)
    for contact in contacts:
        contact.hours += share

def tick_current_activity(character: CharacterV2, current_tick: int) -> None:
    activity = character.state.current_activity
    if activity is None:
        return
    dt = ACTIVITY_TICK_HOURS
    activity.hours_completed = round(activity.hours_completed + dt, 4)
    if activity.activity_type == ActivityType.STUDY:
        gain = dt * study_efficiency_multiplier(character)
        entry = _find_or_create_knowledge_entry(character, activity.tag)
        entry.total_hours = round(entry.total_hours + gain, 4)
    elif activity.activity_type == ActivityType.PRACTICE:
        entry = _find_or_create_activity_entry(character, activity.tag)
        entry.total_hours = round(entry.total_hours + dt, 4)
    elif activity.activity_type == ActivityType.SOCIAL:
        social_dt = dt * social_efficiency_multiplier(character)
        distribute_social_hours(character, activity.contacts, social_dt)
    elif activity.activity_type == ActivityType.RECREATIVE:
        apply_recreative_effects(character, activity.tag, dt)
    apply_general_activity_costs(character, activity.activity_type, dt)
    if activity.hours_completed >= activity.hours_total:
        finish_activity(character)
