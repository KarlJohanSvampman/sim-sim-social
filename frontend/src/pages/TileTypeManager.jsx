import React, { useEffect, useState } from "react";

export default function TileTypeManager() {
  const [items, setItems] = useState([]);
  const [draft, setDraft] = useState(`{
  "id": "tile_new",
  "name": "New Tile Type",
  "texture": "textures/new_tile.png",
  "blocks_movement": false,
  "blocks_sight": false,
  "default_interactions": ["inspect"]
}`);
  const [status, setStatus] = useState("Loading...");

  const load = () =>
    fetch("http://localhost:8000/editor/tile-types")
      .then((r) => {
        if (!r.ok) throw new Error(`GET /editor/tile-types failed: ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setItems(data);
        setStatus("Loaded");
      })
      .catch((err) => {
        console.error(err);
        setItems([]);
        setStatus("Load failed");
      });

  useEffect(load, []);

  const save = async () => {
    try {
      const res = await fetch("http://localhost:8000/editor/tile-types", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: draft
      });
      if (!res.ok) throw new Error("Save failed");
      load();
    } catch (e) {
      console.error(e);
      setStatus("Save failed");
    }
  };

  const remove = async (id) => {
    try {
      const res = await fetch(`http://localhost:8000/editor/tile-types/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Delete failed");
      load();
    } catch (e) {
      console.error(e);
      setStatus("Delete failed");
    }
  };

  return (
    <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Tile Types</h2>
      <div style={{marginBottom:8, opacity:0.8}}>Status: {status}</div>
      <div style={{display:"grid", gridTemplateColumns:"320px 1fr", gap:16}}>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          {items.map((i) => (
            <div key={i.id} style={{padding:"8px 0", borderBottom:"1px solid #374151"}}>
              <strong>{i.name}</strong>
              <div style={{fontSize:12, opacity:0.8}}>{i.id}</div>
              <button onClick={() => setDraft(JSON.stringify(i, null, 2))} style={{marginRight:8}}>Edit</button>
              <button onClick={() => remove(i.id)}>Delete</button>
            </div>
          ))}
        </div>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>Create / Edit</h3>
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} style={{width:"100%", minHeight:420, fontFamily:"monospace"}} />
          <div style={{marginTop:8}}>
            <button onClick={save}>Save</button>
          </div>
        </div>
      </div>
    </div>
  );
}
