from models.tagged_character import CharacterV2, CharacterProfileV2, CharacterStateV2, NeedState, Tag, InterestTag, ContactEntry
from services.tagged_profile_store import TAGGED_CHARACTERS

def seed_default_tagged_characters():
    if TAGGED_CHARACTERS:
        return

    char1 = CharacterV2(
        profile=CharacterProfileV2(
            id="tag_ada",
            name="Ada",
            age=30,
            sex="female",
            intelligence_spectrum=-35,
            identity_tags=[Tag(category="temperament", tag="curious"), Tag(category="social_style", tag="reserved")],
            appearance_tags=[Tag(category="style", tag="casual"), Tag(category="build", tag="average")],
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
            current_activity=None,
            roam_tiles_remaining=0,
            last_idle_roll=[],
        ),
        position={"x": 3, "y": 3, "z": 0},
        inventory_item_ids=[],
        equipped_item_ids=[],
        memory=[],
    )

    char2 = CharacterV2(
        profile=CharacterProfileV2(
            id="tag_bryn",
            name="Bryn",
            age=34,
            sex="male",
            intelligence_spectrum=40,
            identity_tags=[Tag(category="social_style", tag="warm"), Tag(category="temperament", tag="observant")],
            appearance_tags=[Tag(category="style", tag="neat"), Tag(category="build", tag="average")],
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
            current_activity=None,
            roam_tiles_remaining=0,
            last_idle_roll=[],
        ),
        position={"x": 8, "y": 8, "z": 0},
        inventory_item_ids=[],
        equipped_item_ids=[],
        memory=[],
    )

    TAGGED_CHARACTERS[char1.profile.id] = char1
    TAGGED_CHARACTERS[char2.profile.id] = char2
