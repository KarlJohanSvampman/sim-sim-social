import React, { useEffect, useState } from "react";

export default function LLMInspector() {
  const [logs, setLogs] = useState([]);

  const load = () => {
    fetch("http://localhost:8000/llm-logs")
      .then(r => r.json())
      .then(setLogs)
      .catch(() => {});
  };

  useEffect(() => {
    load();
    const i = setInterval(load, 2000);
    return () => clearInterval(i);
  }, []);

  const clear = () => {
    fetch("http://localhost:8000/llm-logs", { method: "DELETE" })
      .then(load);
  };

  return (
    <div style={{ padding: 16, color: "#fff", background: "#111", minHeight: "100vh" }}>
      <h2>LLM Inspector</h2>
      <button onClick={clear} style={{marginBottom:12}}>Clear Logs</button>

      {logs.slice().reverse().map((log, i) => (
        <details key={i} style={{ marginBottom: 12, border: "1px solid #333", padding: 8, background: "#1f2937" }}>
          <summary style={{color:"#fff"}}>
            {log.provider_result?.status_code || "?"} — {log.provider_result?.url}
          </summary>
          <pre style={{ whiteSpace: "pre-wrap", color: "#e5e7eb" }}>{JSON.stringify(log, null, 2)}</pre>
        </details>
      ))}
    </div>
  );
}
