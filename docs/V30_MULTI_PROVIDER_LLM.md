This full-project update adds provider-driven chatbot support.

What changed:
- provider client added:
  - backend/services/provider_client.py
- config now supports llm_provider templates
- llm_service now uses HTTP provider templates instead of a hardcoded single-vendor SDK path
- config UI lets you edit:
  - provider_kind
  - base_url
  - chat_path
  - model
  - api_key_env
  - auth_header_name
  - auth_header_template
  - request_template
  - response_text_path

Included example:
- Z.ai docs show:
  - base endpoint: https://api.z.ai/api/paas/v4
  - Bearer auth header
  - chat completions path: /chat/completions
  - OpenAI-compatible usage with model glm-5.1
- the default config is preloaded with a Z.ai-compatible example
