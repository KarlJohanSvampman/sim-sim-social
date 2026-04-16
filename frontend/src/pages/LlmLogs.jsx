import React, { useEffect, useState } from "react";

export default function LlmLogs() {
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState("Loading...");

  const load = async () => {
    try {
      const r = await fetch("http://localhost:8000/llm-logs");
      const data = await r.json();
      setLogs(Array.isArray(data) ? data.slice().reverse() : []);
      setStatus("Loaded");
    } catch {
      setStatus("Load failed");
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>LLM Logs</h2>
      <div style={{marginBottom:8, opacity:0.8}}>Status: {status}</div>
      <div style={{display:"grid", gap:12}}>
        {logs.map((log, idx) => (
          <div key={idx} style={{background:"#1f2937", padding:12, borderRadius:8}}>
            <div><strong>Character:</strong> {log.character_id || "-"}</div>
            <div><strong>Mode:</strong> {log.mode || "-"}</div>
            <div style={{marginTop:8}}><strong>Prompt</strong></div>
            <pre style={{whiteSpace:"pre-wrap", fontSize:12, background:"#111827", padding:8, borderRadius:8, maxHeight:220, overflow:"auto"}}>{log.prompt || "-"}</pre>
            <div style={{marginTop:8}}><strong>Response</strong></div>
            <pre style={{whiteSpace:"pre-wrap", fontSize:12, background:"#111827", padding:8, borderRadius:8, maxHeight:220, overflow:"auto"}}>{JSON.stringify(log.response ?? log.response_raw ?? "-", null, 2)}</pre>
          </div>
        ))}
        {!logs.length ? <div style={{opacity:0.8}}>No LLM logs yet.</div> : null}
      </div>
    </div>
  );
}
