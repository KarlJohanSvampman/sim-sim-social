import React, { useEffect, useState } from "react";

export default function ConfigPage() {
  const [config, setConfig] = useState(null);
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    fetch("http://localhost:8000/world")
      .then(r => r.json())
      .then(data => {
        setConfig(data.config || {});
        setStatus("Loaded");
      })
      .catch(() => setStatus("Load failed"));
  }, []);

  const save = () => {
    fetch("http://localhost:8000/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config)
    }).then(() => setStatus("Saved"));
  };

  if (!config) return <div style={{padding:16,color:"#fff",background:"#111"}}>{status}</div>;

  return (
    <div style={{padding:16,color:"#fff",background:"#111",minHeight:"100%"}}>
      <h2>Config</h2>
      <div>Status: {status}</div>

      <div style={{marginTop:12}}>
        <label>Tick Rate (seconds)</label>
        <input
          type="number"
          value={config.tick_rate || 1}
          onChange={e => setConfig({...config, tick_rate: parseFloat(e.target.value)})}
        />
      </div>

      <div>
        <label>LLM Interval (seconds)</label>
        <input
          type="number"
          value={config.llm_interval_seconds || 30}
          onChange={e => setConfig({...config, llm_interval_seconds: parseFloat(e.target.value)})}
        />
      </div>

      <div>
        <label>Provider Base URL</label>
        <input
          style={{width:"100%"}}
          value={config.provider_base_url || ""}
          onChange={e => setConfig({...config, provider_base_url: e.target.value})}
        />
      </div>

      <div>
        <label>Model</label>
        <input
          value={config.model || ""}
          onChange={e => setConfig({...config, model: e.target.value})}
        />
      </div>

      <button onClick={save} style={{marginTop:12}}>Save</button>
    </div>
  );
}
