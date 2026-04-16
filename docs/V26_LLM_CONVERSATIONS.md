This full-project update adds a real LLM integration path for decisions and conversations.

What changed:
- world config now includes:
  - tick_rate
  - llm_interval_seconds
- real LLM service added:
  - backend/services/llm_service.py
- tagged sim loop now opportunistically calls the LLM on the configured cadence
- LLM logs endpoint added:
  - GET /llm-logs
- frontend config page now lets you set:
  - 30 or 60 second LLM interval
- frontend LLM Logs page shows:
  - prompt
  - response
  - character id
  - mode (live_llm / disabled_fallback / error_fallback)

Important:
- live LLM behavior requires OPENAI_API_KEY in the backend environment
- without that key, the system logs disabled_fallback entries and uses local fallback behavior
