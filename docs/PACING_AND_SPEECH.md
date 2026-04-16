This patch improves pacing and visible expressiveness.

Changes:
- slower roaming:
  - sims no longer move every tick
  - they pause between moves
  - they sometimes stop for 1-4 ticks at destinations
- more frequent activity attempts:
  - any doubles now trigger an activity attempt
  - high needs can also trigger an activity attempt even without doubles
- speech bubbles:
  - conversation and phone_call can produce visible spoken_text
  - frontend renders spoken_text as a speech bubble over the sim

New state fields:
- dwell_ticks_remaining
- move_cooldown_ticks
- spoken_text
- speech_expires_tick
