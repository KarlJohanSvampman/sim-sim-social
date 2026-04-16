import React, { useEffect, useState } from "react";

const ollamaPreset = {
  provider_kind: "openai_compatible",
  label: "Ollama (localhost)",
  base_url: "http://localhost:11434/v1/",
  chat_path: "chat/completions",
  model: "llama3.1",
  api_key_env: "",
  auth_header_name: "Authorization",
  auth_header_template: "",
  request_template: {
    model: "{{model}}",
    messages: "{{messages}}",
    temperature: 0.8,
    stream: false
  },
  response_text_path: "choices.0.message.content"
};

const zaiPreset = {
  provider_kind: "openai_compatible",
  label: "Z.ai (example)",
  base_url: "https://api.z.ai/api/paas/v4/",
  chat_path: "chat/completions",
  model: "glm-5.1",
  api_key_env: "CHAT_PROVIDER_API_KEY",
  auth_header_name: "Authorization",
  auth_header_template: "Bearer {{api_key}}",
  request_template: {
    model: "{{model}}",
    messages: "{{messages}}",
    temperature: 0.8,
    stream: false
  },
  response_text_path: "choices.0.message.content"
};

export default function Config() {
  const [cfg, setCfg] = useState({
    tick_rate: 1.0,
    llm_interval_seconds: 30.0,
    enable_activity_logic: false,
    enable_roaming_logic: false,
    ai_action_mode: "actions_only",
    llm_provider: ollamaPreset
  });
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    fetch("http://localhost:8000/config")
      .then(r => r.json())
      .then((data) => {
        setCfg({
          tick_rate: data.tick_rate ?? 1.0,
          llm_interval_seconds: data.llm_interval_seconds ?? 30.0,
          enable_activity_logic: data.enable_activity_logic ?? false,
          enable_roaming_logic: data.enable_roaming_logic ?? false,
          ai_action_mode: data.ai_action_mode ?? "actions_only",
          llm_provider: data.llm_provider ?? ollamaPreset
        });
        setStatus("Loaded");
      })
      .catch(() => setStatus("Load failed"));
  }, []);

  const save = async () => {
    const r = await fetch("http://localhost:8000/config", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(cfg)
    });
    setStatus(r.ok ? "Saved" : "Save failed");
  };

  const p = cfg.llm_provider || ollamaPreset;

  return (
    <div style={{padding:20, color:"white", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Config</h2>
      <div style={{marginBottom:8, opacity:0.8}}>Status: {status}</div>

      <div style={{maxWidth:860, display:"grid", gap:16, background:"#1f2937", padding:16, borderRadius:8}}>
        <label>
          Tick Rate (seconds)
          <input type="number" step="0.1" value={cfg.tick_rate}
            onChange={e => setCfg({...cfg, tick_rate: parseFloat(e.target.value)})}
            style={{display:"block", width:"100%"}} />
        </label>

        <label>
          LLM Decision / Conversation Interval (seconds)
          <select value={String(cfg.llm_interval_seconds)}
            onChange={e => setCfg({...cfg, llm_interval_seconds: parseFloat(e.target.value)})}
            style={{display:"block", width:"100%"}}>
            <option value="30">30</option>
            <option value="60">60</option>
          </select>
        </label>

        <label><input type="checkbox" checked={cfg.enable_activity_logic}
          onChange={e => setCfg({...cfg, enable_activity_logic: e.target.checked})}/> Enable activity logic</label>

        <label><input type="checkbox" checked={cfg.enable_roaming_logic}
          onChange={e => setCfg({...cfg, enable_roaming_logic: e.target.checked})}/> Enable roaming logic</label>

        <label>
          AI Action Mode
          <select value={cfg.ai_action_mode}
            onChange={e => setCfg({...cfg, ai_action_mode: e.target.value})}
            style={{display:"block", width:"100%"}}>
            <option value="actions_only">actions_only</option>
          </select>
        </label>

        <hr style={{width:"100%", borderColor:"#374151"}} />

        <h3 style={{margin:0}}>Chat Provider</h3>

        <div style={{display:"flex", gap:8, flexWrap:"wrap"}}>
          <button onClick={() => setCfg({...cfg, llm_provider: ollamaPreset})}>Use Ollama preset</button>
          <button onClick={() => setCfg({...cfg, llm_provider: zaiPreset})}>Use Z.ai preset</button>
        </div>

        <div style={{fontSize:12, opacity:0.8}}>
          Ollama local mode requires no API key for localhost. For hosted providers, put the actual key in the environment variable named below.
        </div>

        <label>
          Provider Kind
          <select value={p.provider_kind}
            onChange={e => setCfg({...cfg, llm_provider: {...p, provider_kind: e.target.value}})}
            style={{display:"block", width:"100%"}}>
            <option value="openai_compatible">openai_compatible</option>
            <option value="generic_http">generic_http</option>
          </select>
        </label>

        <label>Label
          <input value={p.label || ""} onChange={e => setCfg({...cfg, llm_provider: {...p, label: e.target.value}})} style={{display:"block", width:"100%"}} />
        </label>

        <label>Base URL
          <input value={p.base_url || ""} onChange={e => setCfg({...cfg, llm_provider: {...p, base_url: e.target.value}})} style={{display:"block", width:"100%"}} />
        </label>

        <label>Chat Path
          <input value={p.chat_path || ""} onChange={e => setCfg({...cfg, llm_provider: {...p, chat_path: e.target.value}})} style={{display:"block", width:"100%"}} />
        </label>

        <label>Model
          <input value={p.model || ""} onChange={e => setCfg({...cfg, llm_provider: {...p, model: e.target.value}})} style={{display:"block", width:"100%"}} />
        </label>

        <label>API Key Env Var
          <input value={p.api_key_env || ""} onChange={e => setCfg({...cfg, llm_provider: {...p, api_key_env: e.target.value}})} style={{display:"block", width:"100%"}} />
        </label>

        <label>Auth Header Name
          <input value={p.auth_header_name || ""} onChange={e => setCfg({...cfg, llm_provider: {...p, auth_header_name: e.target.value}})} style={{display:"block", width:"100%"}} />
        </label>

        <label>Auth Header Template
          <input value={p.auth_header_template || ""} onChange={e => setCfg({...cfg, llm_provider: {...p, auth_header_template: e.target.value}})} style={{display:"block", width:"100%"}} />
        </label>

        <label>Response Text Path
          <input value={p.response_text_path || ""} onChange={e => setCfg({...cfg, llm_provider: {...p, response_text_path: e.target.value}})} style={{display:"block", width:"100%"}} />
        </label>

        <label>Request Template (JSON)
          <textarea
            value={JSON.stringify(p.request_template || {}, null, 2)}
            onChange={e => {
              try {
                setCfg({...cfg, llm_provider: {...p, request_template: JSON.parse(e.target.value)}});
              } catch {}
            }}
            style={{display:"block", width:"100%", minHeight:180, fontFamily:"monospace"}}
          />
        </label>

        <button onClick={save}>Save Config</button>
      </div>
    </div>
  );
}
