import React, { useEffect, useState } from "react";

export default function ConfigPage() {
  const [config, setConfig] = useState(null);
  const [status, setStatus] = useState("Loading...");
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    fetch("http://localhost:8000/config")
      .then(r => r.json())
      .then(data => {
        setConfig(data || {});
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

  const testConnection = () => {
    setTestResult({ loading: true });
    fetch("http://localhost:8000/config/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config)
    })
      .then(r => r.json())
      .then(data => setTestResult({ ...data, loading: false }))
      .catch(err => setTestResult({ error: String(err), loading: false }));
  };

  if (!config) return <div style={{padding:16,color:"#fff",background:"#111"}}>{status}</div>;

  const provider = config.llm_provider || {};

  return (
    <div style={{padding:16,color:"#fff",background:"#111",minHeight:"100vh"}}>
      <h2>Config</h2>
      <div>Status: {status}</div>

      <div>
        <label>Tick Rate</label>
        <input
          type="number"
          value={config.tick_rate || 1}
          onChange={e => setConfig({...config, tick_rate: parseFloat(e.target.value)})}
        />
      </div>

      <div>
        <label>LLM Interval</label>
        <input
          type="number"
          value={config.llm_interval_seconds || 30}
          onChange={e => setConfig({...config, llm_interval_seconds: parseFloat(e.target.value)})}
        />
      </div>

      <h3>LLM Provider</h3>

      <div>
        <label>Base URL</label>
        <input
          style={{width:"100%"}}
          value={provider.base_url || ""}
          onChange={e => setConfig({...config, llm_provider: {...provider, base_url: e.target.value}})}
        />
      </div>

      <div>
        <label>Model</label>
        <input
          value={provider.model || ""}
          onChange={e => setConfig({...config, llm_provider: {...provider, model: e.target.value}})}
        />
      </div>

      <div>
        <label>Chat Path</label>
        <input
          value={provider.chat_path || "chat/completions"}
          onChange={e => setConfig({...config, llm_provider: {...provider, chat_path: e.target.value}})}
        />
      </div>

      <button onClick={save} style={{marginTop:12}}>Save</button>
      <button onClick={testConnection} style={{marginTop:12, marginLeft:8}}>Test Connection</button>

      {testResult && (
        <div style={{marginTop:16, background:"#1f2937", padding:12, borderRadius:8}}>
          {testResult.loading ? "Testing..." : (
            <pre style={{whiteSpace:"pre-wrap", color:"#e5e7eb"}}>
              {JSON.stringify(testResult, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
