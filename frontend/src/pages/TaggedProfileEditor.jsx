import React, { useEffect, useMemo, useState } from "react";

const defaultProfile = {
  profile: {
    id: "char_new",
    name: "New Character",
    age: 30,
    sex: "unknown",
    intelligence_spectrum: 0,
    identity_tags: [{ category: "temperament", tag: "curious" }],
    appearance_tags: [{ category: "style", tag: "casual" }],
    interests: [
      { category: "Knowledge", tag: "psychology", rank: 1 },
      { category: "Activity", tag: "cooking", rank: 2 }
    ],
    activities: [{ tag: "cooking", total_hours: 12.5 }],
    knowledge: [{ tag: "nutrition", total_hours: 8.0 }],
    contacts: [{ character_id: "tag_2", hours: 4.5, relationship_tags: [] }],
    experiences: [],
    expectations: { positive: [], negative: [] }
  },
  state: {
    needs: { hunger: 10, thirst: 10, bladder: 10, sleep: 10 },
    mood: "neutral",
    stress: 10,
    focus: 55,
    fatigue: 10,
    intoxication: 0,
    current_activity: null,
    roam_tiles_remaining: 0,
    last_idle_roll: [],
    roam_target: null,
    roam_path: [],
    dwell_ticks_remaining: 0,
    move_cooldown_ticks: 0,
    spoken_text: "",
    speech_expires_tick: 0
  },
  position: { x: 1, y: 1, z: 0 },
  inventory_item_ids: [],
  equipped_item_ids: [],
  memory: []
};

function parseArrayField(value) {
  return value.split(",").map((x) => x.trim()).filter(Boolean);
}
function tagsToCsv(tags) {
  return (tags || []).map((t) => `${t.category}:${t.tag}`).join(", ");
}
function csvToTags(csv) {
  return parseArrayField(csv).map((entry) => {
    const [category, ...rest] = entry.split(":");
    return { category: (category || "other").trim(), tag: rest.join(":").trim() || "untagged" };
  });
}
function simpleHoursToCsv(arr) {
  return (arr || []).map((x) => `${x.tag}:${x.total_hours}`).join(", ");
}
function csvToHours(csv) {
  return parseArrayField(csv).map((entry) => {
    const [tag, hours] = entry.split(":");
    return { tag: (tag || "").trim(), total_hours: Number(hours || 0) || 0 };
  });
}
function interestsToCsv(arr) {
  return (arr || []).map((x) => `${x.category}:${x.tag}:${x.rank ?? ""}`).join(", ");
}
function csvToInterests(csv) {
  return parseArrayField(csv).map((entry, idx) => {
    const [category, tag, rank] = entry.split(":");
    return { category: (category || "Activity").trim(), tag: (tag || "").trim(), rank: Number(rank || idx + 1) || idx + 1 };
  });
}
function contactsToCsv(arr) {
  return (arr || []).map((x) => `${x.character_id}:${x.hours}`).join(", ");
}
function csvToContacts(csv) {
  return parseArrayField(csv).map((entry) => {
    const [character_id, hours] = entry.split(":");
    return { character_id: (character_id || "").trim(), hours: Number(hours || 0) || 0, relationship_tags: [] };
  });
}

export default function TaggedProfileEditor() {
  const [profiles, setProfiles] = useState([]);
  const [payload, setPayload] = useState(defaultProfile);
  const [selectedId, setSelectedId] = useState(null);
  const [world, setWorld] = useState(null);
  const [status, setStatus] = useState("Loading...");

  const loadProfiles = async () => {
    try {
      const res = await fetch("http://localhost:8000/tagged-profiles");
      if (!res.ok) throw new Error("Profile list failed");
      const data = await res.json();
      setProfiles(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
      setStatus("Profile list failed");
    }
  };

  const loadWorld = async () => {
    try {
      const res = await fetch("http://localhost:8000/world");
      if (!res.ok) throw new Error("World load failed");
      const data = await res.json();
      setWorld(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    const load = async () => {
      setStatus("Loading...");
      await Promise.all([loadProfiles(), loadWorld()]);
      setStatus("Loaded");
    };
    load();
  }, []);

  const p = payload.profile;
  const s = payload.state;

  const selectedRuntime = useMemo(() => {
    if (!selectedId || !world?.tagged_characters) return null;
    return world.tagged_characters[selectedId] || null;
  }, [selectedId, world]);

  const setProfileField = (field, value) => setPayload((prev) => ({ ...prev, profile: { ...prev.profile, [field]: value } }));
  const setStateField = (field, value) => setPayload((prev) => ({ ...prev, state: { ...prev.state, [field]: value } }));

  const selectProfile = async (id) => {
    setSelectedId(id);
    try {
      const res = await fetch(`http://localhost:8000/tagged-profiles/${id}`);
      if (!res.ok) throw new Error("Load profile failed");
      const data = await res.json();
      setPayload(data);
      setStatus(`Editing ${data.profile.name}`);
    } catch (e) {
      console.error(e);
      setStatus("Load profile failed");
    }
  };

  const save = async () => {
    try {
      const res = await fetch("http://localhost:8000/tagged-profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(`Save failed: ${res.status}`);
      await loadProfiles();
      await loadWorld();
      setSelectedId(payload.profile.id);
      setStatus("Saved");
    } catch (e) {
      console.error(e);
      setStatus("Save failed");
    }
  };

  const removeProfile = async (id) => {
    try {
      const res = await fetch(`http://localhost:8000/tagged-profiles/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Delete failed");
      await loadProfiles();
      await loadWorld();
      if (selectedId === id) {
        setSelectedId(null);
        setPayload(defaultProfile);
      }
      setStatus("Deleted");
    } catch (e) {
      console.error(e);
      setStatus("Delete failed");
    }
  };

  const createNew = () => {
    setSelectedId(null);
    setPayload(JSON.parse(JSON.stringify(defaultProfile)));
    setStatus("Creating new profile");
  };

  const memoryEntries = selectedRuntime?.memory || payload.memory || [];
  const latestDecision = [...memoryEntries].reverse().find((m) => m?.decision);
  const latestPromptPayload = latestDecision?.prompt_payload || null;

  return (
    <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Profiles</h2>
      <div style={{marginBottom:8, opacity:0.8}}>
        Status: {status}
      </div>
      <div style={{marginBottom:12, opacity:0.85}}>
        Current behavior engine: <strong>not a live chatbot yet</strong>. Actions and speech are currently produced by a deterministic simulation engine with prompt-style payload inspection.
      </div>

      <div style={{display:"grid", gridTemplateColumns:"280px 1fr 420px", gap:16}}>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <div style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
            <h3 style={{margin:0}}>All Characters</h3>
            <button onClick={createNew}>New</button>
          </div>
          <div style={{marginTop:12}}>
            {profiles.length === 0 ? <div style={{opacity:0.7}}>No saved profiles yet.</div> : null}
            {profiles.map((item) => (
              <div key={item.profile.id} style={{padding:"10px 0", borderBottom:"1px solid #374151"}}>
                <div><strong>{item.profile.name}</strong></div>
                <div style={{fontSize:12, opacity:0.75}}>ID: {item.profile.id}</div>
                <div style={{fontSize:12, opacity:0.75}}>IQ↔EQ: {item.profile.intelligence_spectrum}</div>
                <div style={{marginTop:8}}>
                  <button onClick={() => selectProfile(item.profile.id)} style={{marginRight:8}}>Edit</button>
                  <button onClick={() => removeProfile(item.profile.id)}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>Selected Profile</h3>
          <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:16}}>
            <div>
              <label>Name<br/><input value={p.name} onChange={(e) => setProfileField("name", e.target.value)} style={{width:"100%"}} /></label><br/><br/>
              <label>Profile ID<br/><input value={p.id} onChange={(e) => setProfileField("id", e.target.value)} style={{width:"100%"}} /></label><br/><br/>
              <label>Age<br/><input type="number" value={p.age ?? 0} onChange={(e) => setProfileField("age", Number(e.target.value))} style={{width:"100%"}} /></label><br/><br/>
              <label>Sex<br/><input value={p.sex ?? ""} onChange={(e) => setProfileField("sex", e.target.value)} style={{width:"100%"}} /></label><br/><br/>
              <label>
                Intelligence Spectrum: {p.intelligence_spectrum}
                <input type="range" min="-100" max="100" value={p.intelligence_spectrum} onChange={(e) => setProfileField("intelligence_spectrum", Number(e.target.value))} style={{width:"100%"}} />
              </label>
              <div style={{fontSize:12, opacity:0.8}}>High IQ ←→ High EQ</div>
            </div>

            <div>
              <label>Identity Tags<br/><textarea value={tagsToCsv(p.identity_tags)} onChange={(e) => setProfileField("identity_tags", csvToTags(e.target.value))} style={{width:"100%", minHeight:80}} /></label><br/><br/>
              <label>Appearance Tags<br/><textarea value={tagsToCsv(p.appearance_tags)} onChange={(e) => setProfileField("appearance_tags", csvToTags(e.target.value))} style={{width:"100%", minHeight:80}} /></label>
            </div>

            <div>
              <label>Ranked Interests<br/><textarea value={interestsToCsv(p.interests)} onChange={(e) => setProfileField("interests", csvToInterests(e.target.value))} style={{width:"100%", minHeight:90}} /></label><br/><br/>
              <label>Activities (tag:hours)<br/><textarea value={simpleHoursToCsv(p.activities)} onChange={(e) => setProfileField("activities", csvToHours(e.target.value))} style={{width:"100%", minHeight:90}} /></label>
            </div>

            <div>
              <label>Knowledge (tag:hours)<br/><textarea value={simpleHoursToCsv(p.knowledge)} onChange={(e) => setProfileField("knowledge", csvToHours(e.target.value))} style={{width:"100%", minHeight:90}} /></label><br/><br/>
              <label>Contacts (character_id:hours)<br/><textarea value={contactsToCsv(p.contacts)} onChange={(e) => setProfileField("contacts", csvToContacts(e.target.value))} style={{width:"100%", minHeight:90}} /></label>
            </div>

            <div>
              <label>Mood<br/><input value={s.mood} onChange={(e) => setStateField("mood", e.target.value)} style={{width:"100%"}} /></label><br/><br/>
              <label>Focus<br/><input type="number" value={s.focus} onChange={(e) => setStateField("focus", Number(e.target.value))} style={{width:"100%"}} /></label><br/><br/>
              <label>Stress<br/><input type="number" value={s.stress} onChange={(e) => setStateField("stress", Number(e.target.value))} style={{width:"100%"}} /></label>
            </div>

            <div>
              <label>Fatigue<br/><input type="number" value={s.fatigue} onChange={(e) => setStateField("fatigue", Number(e.target.value))} style={{width:"100%"}} /></label><br/><br/>
              <label>Spoken Text<br/><input value={s.spoken_text || ""} onChange={(e) => setStateField("spoken_text", e.target.value)} style={{width:"100%"}} /></label>
            </div>
          </div>

          <div style={{marginTop:16}}>
            <button onClick={save}>Save Profile</button>
          </div>
        </div>

        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>AI / Decision Inspector</h3>
          <div style={{fontSize:12, opacity:0.8, marginBottom:8}}>
            This currently shows the simulation prompt contract payload plus the deterministic decision output, not a live LLM response.
          </div>

          <div style={{marginBottom:12}}>
            <strong>Runtime selection:</strong> {selectedRuntime?.profile?.name || payload.profile.name || "None"}
          </div>

          <div style={{marginBottom:12}}>
            <strong>Current state</strong>
            <pre style={{whiteSpace:"pre-wrap", fontSize:12, maxHeight:160, overflow:"auto", background:"#111827", padding:8, borderRadius:8}}>
{JSON.stringify(selectedRuntime?.state || payload.state, null, 2)}
            </pre>
          </div>

          <div style={{marginBottom:12}}>
            <strong>Latest prompt payload</strong>
            <pre style={{whiteSpace:"pre-wrap", fontSize:12, maxHeight:220, overflow:"auto", background:"#111827", padding:8, borderRadius:8}}>
{latestPromptPayload ? JSON.stringify(latestPromptPayload, null, 2) : "No prompt payload recorded yet."}
            </pre>
          </div>

          <div style={{marginBottom:12}}>
            <strong>Latest decision output</strong>
            <pre style={{whiteSpace:"pre-wrap", fontSize:12, maxHeight:180, overflow:"auto", background:"#111827", padding:8, borderRadius:8}}>
{latestDecision?.decision ? JSON.stringify(latestDecision.decision, null, 2) : "No decision recorded yet."}
            </pre>
          </div>

          <div>
            <strong>Recent memory log</strong>
            <pre style={{whiteSpace:"pre-wrap", fontSize:12, maxHeight:240, overflow:"auto", background:"#111827", padding:8, borderRadius:8}}>
{memoryEntries.length ? JSON.stringify(memoryEntries.slice(-6), null, 2) : "No memory entries yet."}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
