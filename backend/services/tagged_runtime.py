import random

from models.tagged_character import CharacterV2, CharacterProfileV2, CharacterStateV2, NeedState, Tag, InterestTag, ContactEntry
from services.tagged_profile_store import TAGGED_CHARACTERS

POSITIVE_TRAIT_BANK = [
    "Adventurous", "Ambitious", "Artistic", "Assertive", "Authentic", "Attentive", "Autonomous", "Blunt", "Brave", "Calm",
    "Carefree", "Cautious", "Charismatic", "Compassionate", "Confident", "Considerate", "Creative", "Critical_thinking",
    "Determined", "Diplomatic", "Empathetic", "Enthusiastic", "Fair_minded", "Flexible", "Forgiving", "Generous", "Genuine",
    "Grateful", "Honest", "Humble", "Independent", "Insightful", "Intelligent", "Introspective", "Kind", "Loyal", "Modest",
    "Motivated", "Optimistic", "Organized", "Patient", "Perceptive", "Persistent", "Philosophical", "Playful", "Positive",
    "Pragmatic", "Proactive"
]

NEGATIVE_TRAIT_BANK = [
    "Absent_minded", "Aggressive", "Apathetic", "Argumentative", "Arrogant", "Ashamed", "Bitter", "Bossy", "Callous",
    "Conceited", "Confrontational", "Cowardly", "Critical", "Cruel", "Defiant", "Deceptive", "Demanding", "Despairing",
    "Detached", "Disapproving", "Dishonest", "Distant", "Dominating", "Dour", "Envious", "Escapist", "Excitable", "Flippant",
    "Forgetful", "Frustrated", "Gossipy", "Grim", "Hateful", "Hopeless", "Hypocritical", "Imperious", "Inconsiderate",
    "Indecisive", "Insensitive", "Intrusive", "Irritable", "Manipulative", "Melancholy", "Moody", "Narcissistic", "Negative",
    "Opportunistic", "Overbearing", "Pessimistic"
]

APPEARANCE_BANK = {
    "age": ["youthful", "mature", "elderly"],
    "body_type": ["athletic", "slender", "curvy", "muscular"],
    "hair_color": ["blonde", "brunette", "redhead", "grey"],
    "eyes": ["bright", "dull", "expressive", "lifeless"],
    "nose": ["small", "large", "proportional", "crooked"],
    "mouth": ["full", "thin"],
    "lips": ["thick", "thin"],
    "face_shape": ["angular", "curved"],
    "skin_tone": ["fair", "dark", "radiant", "pale"],
    "height": ["short", "tall", "average"],
    "posture": ["straight", "slouched", "confident", "hesitant"],
    "style": ["casual", "neat", "plain", "flashy"],
}


def _sample_traits(seed_key: str, positive_count: int = 3, negative_count: int = 2) -> list[Tag]:
    rng = random.Random(seed_key)
    positives = rng.sample(POSITIVE_TRAIT_BANK, k=min(positive_count, len(POSITIVE_TRAIT_BANK)))
    negatives = rng.sample(NEGATIVE_TRAIT_BANK, k=min(negative_count, len(NEGATIVE_TRAIT_BANK)))
    tags = [Tag(category="personality_positive", tag=t.lower()) for t in positives]
    tags.extend(Tag(category="personality_negative", tag=t.lower()) for t in negatives)
    return tags


def _sample_appearance(seed_key: str) -> list[Tag]:
    rng = random.Random(f"appearance::{seed_key}")
    tags = []
    for category, values in APPEARANCE_BANK.items():
        tags.append(Tag(category=category, tag=rng.choice(values)))
    return tags


def _biases_from_traits(traits: list[Tag]) -> dict:
    positive = {t.tag for t in traits if t.category == "personality_positive"}
    negative = {t.tag for t in traits if t.category == "personality_negative"}

    out = {
        "volatility": 0.5,
        "aggression_bias": 0.2,
        "drama_bias": 0.5,
        "authority_sensitivity": 0.3,
        "insecurity": 0.4,
        "social_patience": 45.0,
    }

    if "playful" in positive or "charismatic" in positive:
        out["drama_bias"] += 0.12
    if "loyal" in positive or "kind" in positive or "patient" in positive:
        out["social_patience"] += 10.0
    if "creative" in positive or "philosophical" in positive:
        out["insecurity"] -= 0.05

    if "aggressive" in negative or "confrontational" in negative or "argumentative" in negative:
        out["aggression_bias"] += 0.25
        out["volatility"] += 0.18
    if "irritable" in negative or "moody" in negative or "excitable" in negative:
        out["volatility"] += 0.15
        out["drama_bias"] += 0.08
    if "manipulative" in negative or "arrogant" in negative:
        out["insecurity"] += 0.12
    if "bossy" in negative or "imperious" in negative:
        out["authority_sensitivity"] += 0.15
    if "gossipy" in negative:
        out["drama_bias"] += 0.12

    out["volatility"] = max(0.0, min(1.0, out["volatility"]))
    out["aggression_bias"] = max(0.0, min(1.0, out["aggression_bias"]))
    out["drama_bias"] = max(0.0, min(1.0, out["drama_bias"]))
    out["authority_sensitivity"] = max(0.0, min(1.0, out["authority_sensitivity"]))
    out["insecurity"] = max(0.0, min(1.0, out["insecurity"]))
    out["social_patience"] = max(10.0, min(90.0, out["social_patience"]))
    return out


def seed_default_tagged_characters():
    if TAGGED_CHARACTERS:
        return

    ada_traits = _sample_traits("tag_ada")
    bryn_traits = _sample_traits("tag_bryn")
    ada_appearance = _sample_appearance("tag_ada")
    bryn_appearance = _sample_appearance("tag_bryn")
    ada_bias = _biases_from_traits(ada_traits)
    bryn_bias = _biases_from_traits(bryn_traits)

    char1 = CharacterV2(
        profile=CharacterProfileV2(
            id="tag_ada",
            name="Ada",
            age=30,
            sex="female",
            intelligence_spectrum=-35,
            identity_tags=[
                Tag(category="temperament", tag="curious"),
                Tag(category="social_style", tag="reserved"),
                Tag(category="conflict_style", tag="dramatic"),
                *ada_traits,
            ],
            appearance_tags=ada_appearance,
            interests=[InterestTag(category="Knowledge", tag="psychology", rank=1), InterestTag(category="Activity", tag="cooking", rank=2)],
            activities=[],
            knowledge=[],
            contacts=[ContactEntry(character_id="tag_bryn", hours=4.0, relationship_tags=[])],
            experiences=[],
            expectations={"positive": [], "negative": []},
        ),
        state=CharacterStateV2(
            needs=NeedState(hunger=15, thirst=10, bladder=8, sleep=20),
            mood="neutral",
            stress=18,
            focus=62,
            fatigue=20,
            intoxication=0,
            emotional_temperature=28,
            volatility=ada_bias["volatility"],
            aggression_bias=ada_bias["aggression_bias"],
            drama_bias=ada_bias["drama_bias"],
            authority_sensitivity=ada_bias["authority_sensitivity"],
            insecurity=ada_bias["insecurity"],
            social_patience=ada_bias["social_patience"],
            affinity={"tag_bryn": 12.0},
            current_activity=None,
            roam_tiles_remaining=0,
            last_idle_roll=[],
            roam_target=None,
            roam_path=[],
            dwell_ticks_remaining=0,
            move_cooldown_ticks=0,
            spoken_text="",
            speech_expires_tick=0,
            current_intention="",
            current_action_name="",
            action_delay_ticks_remaining=0,
            action_phase="idle",
            pending_action=None,
            household_id="house_1"
        ),
        position={"x": 3, "y": 3, "z": 0},
        inventory_item_ids=[],
        equipped_item_ids=[],
        memory=[],
        conversation_history=[],
        subjective_views=[],
    )

    char2 = CharacterV2(
        profile=CharacterProfileV2(
            id="tag_bryn",
            name="Bryn",
            age=34,
            sex="male",
            intelligence_spectrum=40,
            identity_tags=[
                Tag(category="social_style", tag="warm"),
                Tag(category="temperament", tag="observant"),
                Tag(category="conflict_style", tag="passive_aggressive"),
                *bryn_traits,
            ],
            appearance_tags=bryn_appearance,
            interests=[InterestTag(category="Activity", tag="conversation", rank=1), InterestTag(category="Knowledge", tag="history", rank=2)],
            activities=[],
            knowledge=[],
            contacts=[ContactEntry(character_id="tag_ada", hours=6.0, relationship_tags=[])],
            experiences=[],
            expectations={"positive": [], "negative": []},
        ),
        state=CharacterStateV2(
            needs=NeedState(hunger=10, thirst=12, bladder=10, sleep=16),
            mood="neutral",
            stress=22,
            focus=58,
            fatigue=15,
            intoxication=0,
            emotional_temperature=20,
            volatility=bryn_bias["volatility"],
            aggression_bias=bryn_bias["aggression_bias"],
            drama_bias=bryn_bias["drama_bias"],
            authority_sensitivity=bryn_bias["authority_sensitivity"],
            insecurity=bryn_bias["insecurity"],
            social_patience=bryn_bias["social_patience"],
            affinity={"tag_ada": 18.0},
            current_activity=None,
            roam_tiles_remaining=0,
            last_idle_roll=[],
            roam_target=None,
            roam_path=[],
            dwell_ticks_remaining=0,
            move_cooldown_ticks=0,
            spoken_text="",
            speech_expires_tick=0,
            current_intention="",
            current_action_name="",
            action_delay_ticks_remaining=0,
            action_phase="idle",
            pending_action=None,
            household_id="house_2"
        ),
        position={"x": 14, "y": 3, "z": 0},
        inventory_item_ids=[],
        equipped_item_ids=[],
        memory=[],
        conversation_history=[],
        subjective_views=[],
    )

    TAGGED_CHARACTERS[char1.profile.id] = char1
    TAGGED_CHARACTERS[char2.profile.id] = char2
