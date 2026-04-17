from __future__ import annotations
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

class Tag(BaseModel):
    category: str = Field(min_length=1)
    tag: str = Field(min_length=1)

class InterestTag(BaseModel):
    category: Literal["Knowledge", "Activity"]
    tag: str = Field(min_length=1)
    rank: int | None = Field(default=None, ge=1)
    weight: float | None = Field(default=None, ge=0.0, le=1.0)

class ActivityHistoryEntry(BaseModel):
    tag: str = Field(min_length=1)
    total_hours: float = Field(ge=0.0)

class KnowledgeEntry(BaseModel):
    tag: str = Field(min_length=1)
    total_hours: float = Field(ge=0.0)

class ContactEntry(BaseModel):
    character_id: str = Field(min_length=1)
    hours: float = Field(ge=0.0)
    last_contact_tick: int | None = Field(default=None, ge=0)
    relationship_tags: list[Tag] = Field(default_factory=list)

class AssociatedPerson(BaseModel):
    character_id: str = Field(min_length=1)
    appearance_tags: list[Tag] = Field(default_factory=list)
    identity_tags: list[Tag] = Field(default_factory=list)

class ExperienceValence(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class ExperienceEntry(BaseModel):
    tag: str = Field(min_length=1)
    valence: ExperienceValence
    tick: int = Field(ge=0)
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    associated_people: list[AssociatedPerson] = Field(default_factory=list)
    notes: str = ""

class ExpectationEntry(BaseModel):
    source_tags: list[Tag] = Field(min_length=1)
    weight: float = Field(ge=0.0, le=1.0)
    derived_from_count: int = Field(ge=1)

class ExpectationCollection(BaseModel):
    positive: list[ExpectationEntry] = Field(default_factory=list)
    negative: list[ExpectationEntry] = Field(default_factory=list)

class NeedState(BaseModel):
    hunger: float = Field(default=0.0, ge=0.0, le=100.0)
    thirst: float = Field(default=0.0, ge=0.0, le=100.0)
    bladder: float = Field(default=0.0, ge=0.0, le=100.0)
    sleep: float = Field(default=0.0, ge=0.0, le=100.0)

class ActivityType(str, Enum):
    STUDY = "study"
    PRACTICE = "practice"
    SOCIAL = "social"
    RECREATIVE = "recreative"

class CurrentActivity(BaseModel):
    activity_type: ActivityType
    tag: str = Field(min_length=1)
    hours_total: float = Field(ge=0.1)
    hours_completed: float = Field(default=0.0, ge=0.0)
    tick_size_hours: float = Field(default=0.1)
    requirements: list[str] = Field(default_factory=list)
    contacts: list[str] = Field(default_factory=list)
    started_at_tick: int = Field(default=0, ge=0)

    @field_validator("tick_size_hours")
    @classmethod
    def validate_tick_size(cls, v: float) -> float:
        if abs(v - 0.1) > 1e-9:
            raise ValueError("tick_size_hours must be 0.1")
        return v

class RelationshipMeter(BaseModel):
    love: float = Field(default=0.0, ge=-100.0, le=100.0)
    hate: float = Field(default=0.0, ge=0.0, le=100.0)
    trust: float = Field(default=0.0, ge=-100.0, le=100.0)
    fear: float = Field(default=0.0, ge=0.0, le=100.0)

class GrudgeMemory(BaseModel):
    target_character_id: str = Field(min_length=1)
    reason: str = ""
    intensity: float = Field(default=10.0, ge=0.0, le=100.0)
    created_tick: int = Field(default=0, ge=0)
    decay_rate: float = Field(default=0.25, ge=0.0, le=5.0)

class CharacterProfileV2(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    age: int | None = Field(default=None, ge=0, le=120)
    sex: str | None = None
    intelligence_spectrum: int = Field(default=0, ge=-100, le=100)
    identity_tags: list[Tag] = Field(default_factory=list)
    appearance_tags: list[Tag] = Field(default_factory=list)
    interests: list[InterestTag] = Field(default_factory=list)
    activities: list[ActivityHistoryEntry] = Field(default_factory=list)
    knowledge: list[KnowledgeEntry] = Field(default_factory=list)
    contacts: list[ContactEntry] = Field(default_factory=list)
    experiences: list[ExperienceEntry] = Field(default_factory=list)
    expectations: ExpectationCollection = Field(default_factory=ExpectationCollection)

class CharacterStateV2(BaseModel):
    needs: NeedState = Field(default_factory=NeedState)
    mood: str = "neutral"
    action_mood: str = "neutral"
    stress: float = Field(default=0.0, ge=0.0, le=100.0)
    focus: float = Field(default=50.0, ge=0.0, le=100.0)
    fatigue: float = Field(default=0.0, ge=0.0, le=100.0)
    intoxication: float = Field(default=0.0, ge=0.0, le=100.0)
    emotional_temperature: float = Field(default=20.0, ge=0.0, le=100.0)
    escalation_level: int = Field(default=0, ge=0, le=5)
    volatility: float = Field(default=0.5, ge=0.0, le=1.0)
    aggression_bias: float = Field(default=0.2, ge=0.0, le=1.0)
    drama_bias: float = Field(default=0.6, ge=0.0, le=1.0)
    authority_sensitivity: float = Field(default=0.3, ge=0.0, le=1.0)
    insecurity: float = Field(default=0.4, ge=0.0, le=1.0)
    current_activity: CurrentActivity | None = None
    roam_tiles_remaining: int = Field(default=0, ge=0)
    last_idle_roll: list[int] = Field(default_factory=list)
    roam_target: dict[str, int | str | float] | None = None
    roam_path: list[dict[str, int]] = Field(default_factory=list)
    dwell_ticks_remaining: int = Field(default=0, ge=0)
    move_cooldown_ticks: int = Field(default=0, ge=0)
    spoken_text: str = ""
    speech_expires_tick: int = Field(default=0, ge=0)
    current_intention: str = ""
    current_action_name: str = ""
    action_delay_ticks_remaining: int = Field(default=0, ge=0)
    action_phase: str = "idle"
    pending_action: dict | None = None
    conversation_partner_id: str = ""
    awaiting_reply_from_id: str = ""
    conversation_turns_remaining: int = Field(default=0, ge=0)
    last_conversation_tick: int = Field(default=0, ge=0)
    conversation_topic: str = ""
    affinity: dict[str, float] = Field(default_factory=dict)
    relationship_meters: dict[str, RelationshipMeter] = Field(default_factory=dict)
    grudges: list[GrudgeMemory] = Field(default_factory=list)
    avoid_character_ids: list[str] = Field(default_factory=list)
    feared_character_ids: list[str] = Field(default_factory=list)

class CharacterV2(BaseModel):
    profile: CharacterProfileV2
    state: CharacterStateV2
    position: dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    inventory_item_ids: list[str] = Field(default_factory=list)
    equipped_item_ids: list[str] = Field(default_factory=list)
    memory: list[dict[str, Any]] = Field(default_factory=list)
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
