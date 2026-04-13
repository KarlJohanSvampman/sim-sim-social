This patch adds:
- backend/models/tagged_character.py
- backend/services/activity_engine.py
- backend/services/tagged_profile_store.py
- backend/routes/tagged_profiles.py
- backend/prompts/decision_prompt_v2.txt
- frontend/src/pages/TaggedProfileEditor.jsx
- frontend/src/types/taggedCharacter.ts

Main migration goals:
- store CharacterProfileV2
- store CharacterStateV2
- store current_activity
- add intelligence spectrum slider
- replace trait-heavy profile editing with tag-based editing
- update LLM decision contract
