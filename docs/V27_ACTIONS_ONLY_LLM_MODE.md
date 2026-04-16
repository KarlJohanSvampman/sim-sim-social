Recommendation implemented:
- for this experiment, actions-only is the best choice
- actions now include:
  - name
  - intention
  - target_character_id
  - target_tile
  - utterance
  - pre_action_delay
  - duration_seconds
  - post_action_delay

What changed:
- activity logic disabled by config default
- roaming logic disabled by config default
- pure LLM action mode now drives behavior
- if no fresh LLM turn is allowed yet, sims wait between LLM turns
- delays are honored by the sim loop
- actions can now replace activities for both short and longer behaviors via duration_seconds

Config defaults:
- tick_rate: 1.0
- llm_interval_seconds: 30.0
- enable_activity_logic: false
- enable_roaming_logic: false
- ai_action_mode: actions_only

Recommendation:
- keep actions-only for now
- once you observe behavior, we can optionally reintroduce activities later as a higher-level abstraction
