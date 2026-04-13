import React, { useEffect, useState } from "react";

export default function DebugPage() {
  const [world, setWorld] = useState(null);
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    fetch("http://localhost:8000/world")
      .then((r) => {
        if (!r.ok) throw new Error(`GET /world failed: ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setWorld(data);
        setStatus("Loaded");
      })
      .catch((err) => {
        console.error(err);
        setStatus("Load failed");
      });
  }, []);

  return (
    <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Debug</h2>
      <div style={{marginBottom:8, opacity:0.8}}>Status: {status}</div>
      <pre style={{whiteSpace:"pre-wrap"}}>{world ? JSON.stringify(world, null, 2) : "No world data."}</pre>
    </div>
  );
}
