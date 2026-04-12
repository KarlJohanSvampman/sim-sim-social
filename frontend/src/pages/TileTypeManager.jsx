import React, { useEffect, useState } from "react";

const template = {
  id: "tile_new",
  name: "New Tile Type",
  texture: "textures/new_tile.png",
  blocks_movement: false,
  blocks_sight: false,
  default_interactions: ["inspect"]
};

export default function TileTypeManager() {
  const [tileTypes, setTileTypes] = useState([]);
  const [draft, setDraft] = useState(JSON.stringify(template, null, 2));

  const load = () => fetch("http://localhost:8000/editor/tile-types").then(r => r.json()).then(setTileTypes);
  useEffect(load, []);

  const save = async () => {
    await fetch("http://localhost:8000/editor/tile-types", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: draft
    });
    load();
  };

  const remove = async (id) => {
    await fetch(`http://localhost:8000/editor/tile-types/${id}`, { method: "DELETE" });
    load();
  };

  return (
    <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Tile Types</h2>
      <div style={{display:"grid", gridTemplateColumns:"320px 1fr", gap:16}}>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          {tileTypes.map(t => (
            <div key={t.id} style={{padding:"8px 0", borderBottom:"1px solid #374151"}}>
              <strong>{t.name}</strong>
              <div style={{fontSize:12, opacity:0.8}}>{t.id}</div>
              <button onClick={() => setDraft(JSON.stringify(t, null, 2))} style={{marginRight:8}}>Edit</button>
              <button onClick={() => remove(t.id)}>Delete</button>
            </div>
          ))}
        </div>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>Create / Edit Tile Type</h3>
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} style={{width:"100%", minHeight:420, fontFamily:"monospace"}} />
          <div style={{marginTop:8}}>
            <button onClick={save}>Save Tile Type</button>
          </div>
        </div>
      </div>
    </div>
  );
}
