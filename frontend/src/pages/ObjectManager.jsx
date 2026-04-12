import React, { useEffect, useState } from "react";

const template = {
  id: "obj_new",
  name: "New Object",
  model: "models/new.glb",
  texture: "textures/new.png",
  icon: "icons/new.png",
  category: "furniture",
  description: "",
  weight: 1,
  portable: true,
  interactions: ["inspect"],
  is_container: false,
  capacity: 0,
  items: []
};

export default function ObjectManager() {
  const [objects, setObjects] = useState([]);
  const [draft, setDraft] = useState(JSON.stringify(template, null, 2));

  const load = () => fetch("http://localhost:8000/editor/objects").then(r => r.json()).then(setObjects);
  useEffect(load, []);

  const save = async () => {
    await fetch("http://localhost:8000/editor/objects", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: draft
    });
    load();
  };

  const remove = async (id) => {
    await fetch(`http://localhost:8000/editor/objects/${id}`, { method: "DELETE" });
    load();
  };

  return (
    <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Objects</h2>
      <div style={{display:"grid", gridTemplateColumns:"320px 1fr", gap:16}}>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          {objects.map(o => (
            <div key={o.id} style={{padding:"8px 0", borderBottom:"1px solid #374151"}}>
              <strong>{o.name}</strong>
              <div style={{fontSize:12, opacity:0.8}}>{o.category}</div>
              <button onClick={() => setDraft(JSON.stringify(o, null, 2))} style={{marginRight:8}}>Edit</button>
              <button onClick={() => remove(o.id)}>Delete</button>
            </div>
          ))}
        </div>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>Create / Edit Object</h3>
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} style={{width:"100%", minHeight:420, fontFamily:"monospace"}} />
          <div style={{marginTop:8}}>
            <button onClick={save}>Save Object</button>
          </div>
        </div>
      </div>
    </div>
  );
}
