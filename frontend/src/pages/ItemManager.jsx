import React, { useEffect, useState } from "react";

const template = {
  id: "item_new",
  name: "New Item",
  type: "generic",
  icon: "icons/new_item.png",
  description: "",
  weight: 0.1,
  effects: {}
};

export default function ItemManager() {
  const [items, setItems] = useState([]);
  const [draft, setDraft] = useState(JSON.stringify(template, null, 2));

  const load = () => fetch("http://localhost:8000/editor/items").then(r => r.json()).then(setItems);
  useEffect(load, []);

  const save = async () => {
    await fetch("http://localhost:8000/editor/items", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: draft
    });
    load();
  };

  const remove = async (id) => {
    await fetch(`http://localhost:8000/editor/items/${id}`, { method: "DELETE" });
    load();
  };

  return (
    <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Items</h2>
      <div style={{display:"grid", gridTemplateColumns:"320px 1fr", gap:16}}>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          {items.map(i => (
            <div key={i.id} style={{padding:"8px 0", borderBottom:"1px solid #374151"}}>
              <strong>{i.name}</strong>
              <div style={{fontSize:12, opacity:0.8}}>{i.type}</div>
              <button onClick={() => setDraft(JSON.stringify(i, null, 2))} style={{marginRight:8}}>Edit</button>
              <button onClick={() => remove(i.id)}>Delete</button>
            </div>
          ))}
        </div>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>Create / Edit Item</h3>
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} style={{width:"100%", minHeight:420, fontFamily:"monospace"}} />
          <div style={{marginTop:8}}>
            <button onClick={save}>Save Item</button>
          </div>
        </div>
      </div>
    </div>
  );
}
