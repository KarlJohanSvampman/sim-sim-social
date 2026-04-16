This archive patches a CharacterStateV2 / tagged_sim_loop mismatch.

Fixed error:
AttributeError: 'CharacterStateV2' object has no attribute 'speech_expires_tick'

Fix applied:
- added missing fields to backend/models/tagged_character.py:
  - roam_tiles_remaining
  - last_idle_roll
  - roam_target
  - roam_path
  - dwell_ticks_remaining
  - move_cooldown_ticks
  - spoken_text
  - speech_expires_tick
- aligned backend/services/tagged_runtime.py defaults

Base archive used:
- v17_context_sensitive_speech.zip

Rebuild:
docker compose down
docker compose build --no-cache backend
docker compose up
