from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict

BodyType = Literal["slim", "average", "muscular", "fat", "obese"]
SexType = Literal["female", "male", "intersex", "unknown"]

class AttractionPreferenceProfile(BaseModel):
    target_sex: Optional[SexType] = "male"
    attractiveness_min: float = Field(default=35.0, ge=0, le=100)
    attractiveness_ideal: float = Field(default=65.0, ge=0, le=100)
    uniqueness_min: float = Field(default=20.0, ge=0, le=100)
    uniqueness_ideal: float = Field(default=45.0, ge=0, le=100)
    attractiveness_weight: float = Field(default=0.6, ge=0, le=1)
    uniqueness_weight: float = Field(default=0.4, ge=0, le=1)
    acceptable_span: float = Field(default=18.0, ge=0, le=100)

class AppearanceProfile(BaseModel):
    public_name: Optional[str] = None
    nicknames: List[str] = Field(default_factory=list)
    age: int = Field(default=30, ge=0, le=120)
    sex: SexType = "unknown"
    skin_tone: str = "medium"
    body_type: BodyType = "average"
    height_cm: int = Field(default=170, ge=80, le=260)
    hair_color: str = "brown"
    eye_color: str = "brown"
    attractiveness_symmetry: float = Field(default=50.0, ge=0, le=100)
    uniqueness_score: float = Field(default=50.0, ge=0, le=100)
    profession: Optional[str] = None
    titles: List[str] = Field(default_factory=list)
    clothing_style: str = "casual"
    visible_notes: List[str] = Field(default_factory=list)

class PersonalityTraits(BaseModel):
    openness: float = Field(default=50.0, ge=0, le=100)
    conscientiousness: float = Field(default=50.0, ge=0, le=100)
    extraversion: float = Field(default=50.0, ge=0, le=100)
    agreeableness: float = Field(default=50.0, ge=0, le=100)
    neuroticism: float = Field(default=50.0, ge=0, le=100)
    honesty_humility: float = Field(default=50.0, ge=0, le=100)
    impulsivity: float = Field(default=50.0, ge=0, le=100)
    romantic_drive: float = Field(default=40.0, ge=0, le=100)
    dominance: float = Field(default=50.0, ge=0, le=100)
    empathy: float = Field(default=50.0, ge=0, le=100)
    jealousy: float = Field(default=35.0, ge=0, le=100)
    risk_tolerance: float = Field(default=40.0, ge=0, le=100)

class MentalIdentityProfile(BaseModel):
    biography_summary: str = ""
    values: List[str] = Field(default_factory=list)
    beliefs: List[str] = Field(default_factory=list)
    habits: List[str] = Field(default_factory=list)
    conversation_style: str = "neutral"
    traits: PersonalityTraits = Field(default_factory=PersonalityTraits)

class RenderProfile(BaseModel):
    mesh_id: str = "human_base_f01"
    material_preset: str = "default_skin"
    animation_controller: str = "biped_v1"
    voice_profile: str = "neutral_01"
    locomotion_style: str = "standard"
    idle_set: str = "idle_relaxed"
    gesture_set: str = "gesture_default"
    scale: float = Field(default=1.0, ge=0.5, le=2.5)
    visible_from_model_analysis: Dict[str, str] = Field(default_factory=lambda: {
        "status": "placeholder",
        "note": "Future hook for features inferred from the 3D model beyond manually entered appearance fields."
    })

class CharacterProfile(BaseModel):
    profile_version: str = "v1"
    name: str
    nicknames: List[str] = Field(default_factory=list)
    appearance: AppearanceProfile = Field(default_factory=AppearanceProfile)
    mind: MentalIdentityProfile = Field(default_factory=MentalIdentityProfile)
    render: RenderProfile = Field(default_factory=RenderProfile)
    female_partner_preference_for_male: Optional[AttractionPreferenceProfile] = Field(default_factory=AttractionPreferenceProfile)
