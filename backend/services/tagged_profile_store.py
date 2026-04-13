from models.tagged_character import CharacterV2

TAGGED_CHARACTERS: dict[str, CharacterV2] = {}

def upsert_tagged_character(payload: dict):
    character = CharacterV2.model_validate(payload)
    TAGGED_CHARACTERS[character.profile.id] = character
    return character.model_dump()

def get_tagged_character(char_id: str):
    c = TAGGED_CHARACTERS.get(char_id)
    return c.model_dump() if c else None

def list_tagged_characters():
    return [c.model_dump() for c in TAGGED_CHARACTERS.values()]
