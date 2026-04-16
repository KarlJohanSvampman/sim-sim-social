import React, { useEffect, useMemo, useState } from "react";

const defaultAction = {
  id: "act_new",
  name: "new_action",
  category: "interaction",
  description: "Describe what this action does.",
  supports_target_character: false,
  supports_target_tile: false,
  supports_utterance: false,
  default_pre_action_delay: 2,
  default_duration_seconds: 5,
  default_post_action_delay: 2,
  min_duration_seconds: 1,
  max_duration_seconds: 60,
  allowed_intentions: [],
  notes: ""
};

function csvToArray(value) {
  return value.split(",").map((x) => x.trim()).filter(Boolean);
}

export default function ActionManager() {
  const [items, setItems] = useState([]);
  const [draft, setDraft] = useState(defaultAction);
  const [status, setStatus] = useState("Loading...");
  const [selectedId, setSelectedId] = useState(null);

  const load = async () => {
    try {
      const r = await fetch("http://localhost:8000/editor/actions");
      if (!r.ok) throw new Error(`Load failed: ${r.status}`);
      const data = await r.json();
      setItems(Array.isArray(data) ? data : []);
      setStatus("Loaded");
    } catch (e) {
      console.error(e);
      setStatus("Load failed");
    }
  };

  useEffect(() => { load(); }, []);

  const save = async () => {
    try {
      const payload = {
        ...draft,
        default_pre_action_delay: Number(draft.default_pre_action_delay) || 1,
        default_duration_seconds: Number(draft.default_duration_seconds) || 1,
        default_post_action_delay: Number(draft.default_post_action_delay) || 1,
        min_duration_seconds: Number(draft.min_duration_seconds) || 1,
        max_duration_seconds: Number(draft.max_duration_seconds) || 60,
      };
      const r = await fetch("http://localhost:8000/editor/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!r.ok) throw new Error(`Save failed: ${r.status}`);
      await load();
      setSelectedId(payload.id);
      setStatus("Saved");
    } catch (e) {
      console.error(e);
      setStatus("Save failed");
    }
  };

  const remove = async (id) => {
    try {
      const r = await fetch(`http://localhost:8000/editor/actions/${id}`, { method: "DELETE" });
      if (!r.ok) throw new Error(`Delete failed: ${r.status}`);
      await load();
      if (selectedId === id) {
        setSelectedId(null);
        setDraft(defaultAction);
      }
      setStatus("Deleted");
    } catch (e) {
      console.error(e);
      setStatus("Delete failed");
    }
  };

  const selectItem = (item) => {
    setSelectedId(item.id);
    setDraft({
      ...defaultAction,
      ...item,
      allowed_intentions: Array.isArray(item.allowed_intentions) ? item.allowed_intentions : []
    });
  };

  const createNew = () => {
    setSelectedId(null);
    setDraft({ ...defaultAction });
    setStatus("Creating new action");
  };

  return (
    <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Actions</h2>
      <div style={{marginBottom:8, opacity:0.8}}>Status: {status}</div>

      <div style={{display:"grid", gridTemplateColumns:"320px 1fr", gap:16}}>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <div style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
            <h3 style={{margin:0}}>Existing Actions</h3>
            <button onClick={createNew}>New</button>
          </div>

          <div style={{marginTop:12}}>
            {items.length === 0 ? <div style={{opacity:0.7}}>No actions found.</div> : null}
            {items.map((i) => (
              <div key={i.id} style={{padding:"10px 0", borderBottom:"1px solid #374151"}}>
                <div><strong>{i.name}</strong></div>
                <div style={{fontSize:12, opacity:0.75}}>{i.id} · {i.category}</div>
                <div style={{fontSize:12, opacity:0.75}}>
                  duration {i.min_duration_seconds ?? "?"}-{i.max_duration_seconds ?? "?"}s
                </div>
                <div style={{marginTop:8}}>
                  <button onClick={() => selectItem(i)} style={{marginRight:8}}>Edit</button>
                  <button onClick={() => remove(i.id)}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>{selectedId ? `Edit Action: ${selectedId}` : "Create Action"}</h3>

          <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:16}}>
            <label>
              Action ID
              <input value={draft.id} onChange={(e) => setDraft({...draft, id: e.target.value})} style={{display:"block", width:"100%"}} />
            </label>

            <label>
              Name
              <input value={draft.name} onChange={(e) => setDraft({...draft, name: e.target.value})} style={{display:"block", width:"100%"}} />
            </label>

            <label>
              Category
              <input value={draft.category} onChange={(e) => setDraft({...draft, category: e.target.value})} style={{display:"block", width:"100%"}} />
            </label>

            <label>
              Description
              <input value={draft.description} onChange={(e) => setDraft({...draft, description: e.target.value})} style={{display:"block", width:"100%"}} />
            </label>

            <label>
              Default Pre-Action Delay
              <input type="number" value={draft.default_pre_action_delay} onChange={(e) => setDraft({...draft, default_pre_action_delay: e.target.value})} style={{display:"block", width:"100%"}} />
            </label>

            <label>
              Default Duration Seconds
              <input type="number" value={draft.default_duration_seconds} onChange={(e) => setDraft({...draft, default_duration_seconds: e.target.value})} style={{display:"block", width:"100%"}} />
            </label>

            <label>
              Default Post-Action Delay
              <input type="number" value={draft.default_post_action_delay} onChange={(e) => setDraft({...draft, default_post_action_delay: e.target.value})} style={{display:"block", width:"100%"}} />
            </label>

            <label>
              Min Duration Seconds
              <input type="number" value={draft.min_duration_seconds} onChange={(e) => setDraft({...draft, min_duration_seconds: e.target.value})} style={{display:"block", width:"100%"}} />
            </label>

            <label>
              Max Duration Seconds
              <input type="number" value={draft.max_duration_seconds} onChange={(e) => setDraft({...draft, max_duration_seconds: e.target.value})} style={{display:"block", width:"100%"}} />
            </label>

            <label>
              Allowed Intentions (comma-separated)
              <input
                value={(draft.allowed_intentions || []).join(", ")}
                onChange={(e) => setDraft({...draft, allowed_intentions: csvToArray(e.target.value)})}
                style={{display:"block", width:"100%"}}
              />
            </label>

            <label style={{display:"flex", alignItems:"center", gap:8}}>
              <input
                type="checkbox"
                checked={!!draft.supports_target_character}
                onChange={(e) => setDraft({...draft, supports_target_character: e.target.checked})}
              />
              Supports Target Character
            </label>

            <label style={{display:"flex", alignItems:"center", gap:8}}>
              <input
                type="checkbox"
                checked={!!draft.supports_target_tile}
                onChange={(e) => setDraft({...draft, supports_target_tile: e.target.checked})}
              />
              Supports Target Tile
            </label>

            <label style={{display:"flex", alignItems:"center", gap:8}}>
              <input
                type="checkbox"
                checked={!!draft.supports_utterance}
                onChange={(e) => setDraft({...draft, supports_utterance: e.target.checked})}
              />
              Supports Utterance
            </label>
          </div>

          <label style={{display:"block", marginTop:16}}>
            Notes
            <textarea
              value={draft.notes || ""}
              onChange={(e) => setDraft({...draft, notes: e.target.value})}
              style={{display:"block", width:"100%", minHeight:120}}
            />
          </label>

          <div style={{marginTop:16}}>
            <button onClick={save}>Save Action</button>
          </div>

          <div style={{marginTop:16}}>
            <strong>Preview JSON</strong>
            <pre style={{whiteSpace:"pre-wrap", fontSize:12, background:"#111827", padding:8, borderRadius:8, maxHeight:220, overflow:"auto"}}>
{JSON.stringify(draft, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
