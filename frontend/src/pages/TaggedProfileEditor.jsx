import React, { useState } from "react";

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
    contacts: [{ character_id: "char_2", hours: 4.5, relationship_tags: [] }],
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
    current_activity: null
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
  const [payload, setPayload] = useState(defaultProfile);
  const [status, setStatus] = useState("");
  const p = payload.profile;
  const s = payload.state;

  const setProfileField = (field, value) => setPayload((prev) => ({ ...prev, profile: { ...prev.profile, [field]: value } }));
  const setStateField = (field, value) => setPayload((prev) => ({ ...prev, state: { ...prev.state, [field]: value } }));

  const save = async () => {
    try {
      const res = await fetch("http://localhost:8000/tagged-profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Save failed");
      setStatus("Saved");
    } catch (e) {
      console.error(e);
      setStatus("Save failed");
    }
  };

  return (
    <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>
      <h2>Tagged Character Profiles</h2>
      <div style={{marginBottom:8, opacity:0.8}}>Status: {status || "Editing"}</div>

      <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:16}}>
        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>Core</h3>
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

        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>Tags</h3>
          <label>Identity Tags<br/><textarea value={tagsToCsv(p.identity_tags)} onChange={(e) => setProfileField("identity_tags", csvToTags(e.target.value))} style={{width:"100%", minHeight:70}} /></label><br/><br/>
          <label>Appearance Tags<br/><textarea value={tagsToCsv(p.appearance_tags)} onChange={(e) => setProfileField("appearance_tags", csvToTags(e.target.value))} style={{width:"100%", minHeight:70}} /></label>
        </div>

        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>Interests and Experience</h3>
          <label>Ranked Interests<br/><textarea value={interestsToCsv(p.interests)} onChange={(e) => setProfileField("interests", csvToInterests(e.target.value))} style={{width:"100%", minHeight:90}} /></label><br/><br/>
          <label>Activities (tag:hours)<br/><textarea value={simpleHoursToCsv(p.activities)} onChange={(e) => setProfileField("activities", csvToHours(e.target.value))} style={{width:"100%", minHeight:90}} /></label><br/><br/>
          <label>Knowledge (tag:hours)<br/><textarea value={simpleHoursToCsv(p.knowledge)} onChange={(e) => setProfileField("knowledge", csvToHours(e.target.value))} style={{width:"100%", minHeight:90}} /></label>
        </div>

        <div style={{background:"#1f2937", padding:12, borderRadius:8}}>
          <h3>Contacts and State</h3>
          <label>Contacts (character_id:hours)<br/><textarea value={contactsToCsv(p.contacts)} onChange={(e) => setProfileField("contacts", csvToContacts(e.target.value))} style={{width:"100%", minHeight:90}} /></label><br/><br/>
          <label>Mood<br/><input value={s.mood} onChange={(e) => setStateField("mood", e.target.value)} style={{width:"100%"}} /></label><br/><br/>
          <label>Focus<br/><input type="number" value={s.focus} onChange={(e) => setStateField("focus", Number(e.target.value))} style={{width:"100%"}} /></label><br/><br/>
          <label>Stress<br/><input type="number" value={s.stress} onChange={(e) => setStateField("stress", Number(e.target.value))} style={{width:"100%"}} /></label><br/><br/>
          <label>Fatigue<br/><input type="number" value={s.fatigue} onChange={(e) => setStateField("fatigue", Number(e.target.value))} style={{width:"100%"}} /></label>
        </div>
      </div>

      <div style={{marginTop:16}}>
        <button onClick={save}>Save Tagged Profile</button>
      </div>

      <div style={{marginTop:16, background:"#1f2937", padding:12, borderRadius:8}}>
        <h3>Payload Preview</h3>
        <pre style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(payload, null, 2)}</pre>
      </div>
    </div>
  );
}
