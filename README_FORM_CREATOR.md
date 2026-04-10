This version replaces the raw JSON-first editor with a proper form-based character creator UI.

Sections:
- Appearance
- Personality
- Preferences
- Render

It still preserves:
- raw JSON inspection
- schema inspection
- creating characters
- editing existing characters

The split is easier to understand:
- body / visible appearance
- mind / personality and biography
- preferences / attraction logic
- render / mesh, animation, voice, and future model-analysis hooks
