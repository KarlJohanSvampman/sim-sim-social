
import React, { useEffect, useState } from "react";

export default function Config() {
  const [cfg, setCfg] = useState({ tick_rate: 1.0, llm_interval_seconds: 30.0 });
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    fetch("http://localhost:8000/config")
      .then(r => r.json())
      .then((data) => {
        setCfg({
          tick_rate: data.tick_rate ?? 1.0,
          llm_interval_seconds: data.llm_interval_seconds ?? 30.0
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

  return (
    <div style={{padding:20, color:"white", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Config</h2>
      <div style={{marginBottom:8, opacity:0.8}}>Status: {status}</div>

      <div style={{maxWidth:480, display:"grid", gap:16, background:"#1f2937", padding:16, borderRadius:8}}>
        <label>
          Tick Rate (seconds)
          <input
            type="number"
            step="0.1"
            value={cfg.tick_rate}
            onChange={e => setCfg({...cfg, tick_rate: parseFloat(e.target.value)})}
            style={{display:"block", width:"100%"}}
          />
        </label>

        <label>
          LLM Decision / Conversation Interval (seconds)
          <select
            value={String(cfg.llm_interval_seconds)}
            onChange={e => setCfg({...cfg, llm_interval_seconds: parseFloat(e.target.value)})}
            style={{display:"block", width:"100%"}}
          >
            <option value="30">30</option>
            <option value="60">60</option>
          </select>
        </label>

        <div style={{fontSize:12, opacity:0.8}}>
          This controls how often a character may call the chatbot for a fresh decision or conversational turn.
        </div>

        <button onClick={save}>Save Config</button>
      </div>
    </div>
  );
}
