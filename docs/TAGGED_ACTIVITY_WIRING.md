This patch wires the tagged profile system into the live simulation loop.

Added:
- backend/services/decision_engine_v2.py
- backend/services/tagged_runtime.py
- backend/services/tagged_sim_loop.py

Now used end to end:
- current_activity
- engage_activity
- tick_current_activity()
- decision_prompt_v2.txt contract

Behavior:
- tagged characters are seeded at startup
- if idle, they choose a new engage_activity-compatible action
- if already busy, they continue ticking current_activity
- their serialized state is mirrored into world.tagged_characters
- websocket broadcasts include tagged characters
