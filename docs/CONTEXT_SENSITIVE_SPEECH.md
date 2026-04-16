This patch makes sim speech context-sensitive.

Speech now depends on:
- current mood bucket
- current room tag
- nearby tagged people
- current activity tag

Examples:
- in kitchen: food / utility flavored lines
- in bedroom: tired / quiet lines
- in living_room or yard: social / relaxed lines
- during conversation or phone_call: more direct social lines
- when nearby people are present: names can be used in speech

Files added/updated:
- backend/services/speech_engine.py
- backend/services/tagged_sim_loop.py
- frontend/src/App.jsx
