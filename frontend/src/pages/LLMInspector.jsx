import React, { useEffect, useState } from "react";

export default function LLMInspector() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const load = () => {
      fetch("http://localhost:8000/world")
        .then(r => r.json())
        .then(data => setLogs(data.llm_logs || []))
        .catch(() => {});
    };
    load();
    const i = setInterval(load, 2000);
    return () => clearInterval(i);
  }, []);

  return (
    <div style={{ padding: 16, color: "#fff", background: "#111", minHeight: "100%" }}>
      <h2>LLM Inspector</h2>
      {logs.slice().reverse().map((log, i) => (
        <details key={i} style={{ marginBottom: 12, border: "1px solid #333", padding: 8 }}>
          <summary>
            {log.provider_result?.status_code || "?"} — {log.provider_result?.url}
          </summary>
          <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(log, null, 2)}</pre>
        </details>
      ))}
    </div>
  );
}
