import React, { useEffect, useState } from "react";

export default function ActivityManager() {
  const [items, setItems] = useState([]);
  const [draft, setDraft] = useState(`{
  "id": "av_new",
  "name": "new_activity",
  "type": "practice",
  "description": "Describe what this activity does.",
  "min_hours": 0.1
}`);
  const [status, setStatus] = useState("Loading...");

  const load = async () => {
    try {
      const r = await fetch("http://localhost:8000/editor/activities");
      if (!r.ok) throw new Error("Load failed");
      setItems(await r.json());
      setStatus("Loaded");
    } catch (e) {
      console.error(e);
      setStatus("Load failed");
    }
  };

  useEffect(() => { load(); }, []);

  const save = async () => {
    try {
      const r = await fetch("http://localhost:8000/editor/activities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: draft
      });
      if (!r.ok) throw new Error("Save failed");
      await load();
      setStatus("Saved");
    } catch (e) {
      console.error(e);
      setStatus("Save failed");
    }
  };

  const remove = async (id) => {
    try {
      const r = await fetch(`http://localhost:8000/editor/activities/${id}`, { method: "DELETE" });
      if (!r.ok) throw new Error("Delete failed");
      await load();
      setStatus("Deleted");
    } catch (e) {
      console.error(e);
      setStatus("Delete failed");
    }
  };

  return (
    <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Activities</h2>
      <div style={{marginBottom:8, opacity:0.8}}>Status: {status}</div>
      <div style={{display:"grid", gridTemplateColumns:"320px 1fr", gap:16}}>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          {items.map((i) => (
            <div key={i.id} style={{padding:"8px 0", borderBottom:"1px solid #374151"}}>
              <strong>{i.name}</strong>
              <div style={{fontSize:12, opacity:0.75}}>{i.id} · {i.type}</div>
              <div style={{marginTop:8}}>
                <button onClick={() => setDraft(JSON.stringify(i, null, 2))} style={{marginRight:8}}>Edit</button>
                <button onClick={() => remove(i.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>Create / Edit Activity</h3>
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} style={{width:"100%", minHeight:420, fontFamily:"monospace"}} />
          <div style={{marginTop:8}}><button onClick={save}>Save</button></div>
        </div>
      </div>
    </div>
  );
}
