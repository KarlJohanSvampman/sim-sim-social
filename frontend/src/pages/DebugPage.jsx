import React, { useEffect, useState } from "react";

export default function DebugPage() {
  const [world, setWorld] = useState(null);

  useEffect(() => {
    fetch("http://localhost:8000/world").then(r => r.json()).then(setWorld);
  }, []);

  return (
    <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Debug</h2>
      <pre style={{whiteSpace:"pre-wrap"}}>{world ? JSON.stringify(world, null, 2) : "Loading..."}</pre>
    </div>
  );
}
