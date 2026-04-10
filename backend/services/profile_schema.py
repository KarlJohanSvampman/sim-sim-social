from models.character_profile import CharacterProfile

def get_character_profile_schema():
    return CharacterProfile.model_json_schema()
