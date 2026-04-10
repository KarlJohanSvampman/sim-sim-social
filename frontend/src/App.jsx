import React, { useEffect, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";

function Tile({ tile }) {
  return (
    <mesh position={[tile.x,0,tile.y]} rotation={[-Math.PI/2,0,0]}>
      <planeGeometry args={[1,1]} />
      <meshStandardMaterial color="#9fd08a" />
    </mesh>
  );
}

function Character({ c, showThoughts }) {
  const app = c.appearance_summary || {};
  return (
    <group position={[c.position.x,0.5,c.position.y]}>
      <mesh>
        <boxGeometry args={[0.6,1.2,0.6]} />
        <meshStandardMaterial color="#3b82f6" />
      </mesh>
      <Html position={[0,1.2,0]} center>
        <div style={{background:"#fff",padding:"4px 6px",borderRadius:6,border:"1px solid #999",fontSize:12,maxWidth:280}}>
          <strong>{c.name}</strong><br/>
          {c.speech ? <span>💬 {c.speech}</span> : (showThoughts ? <span>💭 {c.thoughts}</span> : <span>…</span>)}
          <br/><small>{app.age ?? "?"} · {app.sex || "unknown"} · {app.body_type || "?"}</small>
          <br/><small>{c.render_ref?.mesh_id || "no mesh"} / {c.render_ref?.animation_controller || "no anim"}</small>
        </div>
      </Html>
    </group>
  );
}

const DEFAULT_PROFILE = {
  profile_version: "v1",
  name: "New Character",
  nicknames: [],
  appearance: {
    public_name: "New Character",
    nicknames: [],
    age: 28,
    sex: "female",
    skin_tone: "medium",
    body_type: "average",
    height_cm: 170,
    hair_color: "brown",
    eye_color: "brown",
    attractiveness_symmetry: 50,
    uniqueness_score: 50,
    profession: "",
    titles: [],
    clothing_style: "casual",
    visible_notes: []
  },
  mind: {
    biography_summary: "",
    values: [],
    beliefs: [],
    habits: [],
    conversation_style: "neutral",
    traits: {
      openness: 50,
      conscientiousness: 50,
      extraversion: 50,
      agreeableness: 50,
      neuroticism: 50,
      honesty_humility: 50,
      impulsivity: 50,
      romantic_drive: 40,
      dominance: 50,
      empathy: 50,
      jealousy: 35,
      risk_tolerance: 40
    }
  },
  render: {
    mesh_id: "human_base_f01",
    material_preset: "default_skin",
    animation_controller: "biped_v1",
    voice_profile: "neutral_01",
    locomotion_style: "standard",
    idle_set: "idle_relaxed",
    gesture_set: "gesture_default",
    scale: 1.0,
    visible_from_model_analysis: {
      status: "placeholder",
      note: "Future hook for model-derived visual features."
    }
  },
  female_partner_preference_for_male: {
    target_sex: "male",
    attractiveness_min: 35,
    attractiveness_ideal: 65,
    uniqueness_min: 20,
    uniqueness_ideal: 45,
    attractiveness_weight: 0.6,
    uniqueness_weight: 0.4,
    acceptable_span: 18
  }
};

function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function setAtPath(obj, path, value) {
  const copy = deepClone(obj);
  const parts = path.split(".");
  let cur = copy;
  for (let i = 0; i < parts.length - 1; i++) cur = cur[parts[i]];
  cur[parts[parts.length - 1]] = value;
  return copy;
}

function arrayStringToList(text) {
  return text.split(",").map(x => x.trim()).filter(Boolean);
}

function listToArrayString(list) {
  return Array.isArray(list) ? list.join(", ") : "";
}

function Field({ label, children, help }) {
  return (
    <div style={{marginBottom:12}}>
      <div style={{fontSize:13,fontWeight:600,marginBottom:4}}>{label}</div>
      {children}
      {help && <div style={{fontSize:11,opacity:0.7,marginTop:4}}>{help}</div>}
    </div>
  );
}

function TextInput({ value, onChange }) {
  return <input value={value ?? ""} onChange={(e)=>onChange(e.target.value)} style={{width:"100%",padding:8,borderRadius:6,border:"1px solid #4b5563",background:"#111827",color:"#fff"}} />;
}

function NumberInput({ value, onChange, min, max, step=1 }) {
  return <input type="number" value={value ?? 0} min={min} max={max} step={step} onChange={(e)=>onChange(Number(e.target.value))} style={{width:"100%",padding:8,borderRadius:6,border:"1px solid #4b5563",background:"#111827",color:"#fff"}} />;
}

function SelectInput({ value, onChange, options }) {
  return (
    <select value={value ?? ""} onChange={(e)=>onChange(e.target.value)} style={{width:"100%",padding:8,borderRadius:6,border:"1px solid #4b5563",background:"#111827",color:"#fff"}}>
      {options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
    </select>
  );
}

function SliderInput({ value, onChange, min=0, max=100, step=1 }) {
  return (
    <div>
      <input type="range" min={min} max={max} step={step} value={value ?? 0} onChange={(e)=>onChange(Number(e.target.value))} style={{width:"100%"}} />
      <div style={{fontSize:12,opacity:0.8}}>{value}</div>
    </div>
  );
}

function Section({ title, children, defaultOpen=true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{padding:12,background:"#1f2937",borderRadius:8,marginBottom:16}}>
      <button onClick={()=>setOpen(!open)} style={{background:"transparent",border:"none",color:"#fff",fontSize:18,fontWeight:700,padding:0,marginBottom:open?12:0,cursor:"pointer"}}>
        {open ? "▾" : "▸"} {title}
      </button>
      {open && children}
    </div>
  );
}

function AppearanceEditor({ profile, setProfile }) {
  const a = profile.appearance;
  return (
    <>
      <Field label="Name"><TextInput value={profile.name} onChange={(v)=>setProfile(setAtPath(profile,"name",v))} /></Field>
      <Field label="Public name"><TextInput value={a.public_name} onChange={(v)=>setProfile(setAtPath(profile,"appearance.public_name",v))} /></Field>
      <Field label="Nicknames" help="Comma-separated"><TextInput value={listToArrayString(profile.nicknames)} onChange={(v)=>setProfile(setAtPath(profile,"nicknames",arrayStringToList(v)))} /></Field>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
        <Field label="Age"><NumberInput value={a.age} min={0} max={120} onChange={(v)=>setProfile(setAtPath(profile,"appearance.age",v))} /></Field>
        <Field label="Sex"><SelectInput value={a.sex} options={["female","male","intersex","unknown"]} onChange={(v)=>setProfile(setAtPath(profile,"appearance.sex",v))} /></Field>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
        <Field label="Skin tone"><TextInput value={a.skin_tone} onChange={(v)=>setProfile(setAtPath(profile,"appearance.skin_tone",v))} /></Field>
        <Field label="Body type"><SelectInput value={a.body_type} options={["slim","average","muscular","fat","obese"]} onChange={(v)=>setProfile(setAtPath(profile,"appearance.body_type",v))} /></Field>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:12}}>
        <Field label="Height (cm)"><NumberInput value={a.height_cm} min={80} max={260} onChange={(v)=>setProfile(setAtPath(profile,"appearance.height_cm",v))} /></Field>
        <Field label="Hair color"><TextInput value={a.hair_color} onChange={(v)=>setProfile(setAtPath(profile,"appearance.hair_color",v))} /></Field>
        <Field label="Eye color"><TextInput value={a.eye_color} onChange={(v)=>setProfile(setAtPath(profile,"appearance.eye_color",v))} /></Field>
      </div>
      <Field label="Attractiveness symmetry score"><SliderInput value={a.attractiveness_symmetry} onChange={(v)=>setProfile(setAtPath(profile,"appearance.attractiveness_symmetry",v))} /></Field>
      <Field label="Uniqueness score"><SliderInput value={a.uniqueness_score} onChange={(v)=>setProfile(setAtPath(profile,"appearance.uniqueness_score",v))} /></Field>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
        <Field label="Profession"><TextInput value={a.profession || ""} onChange={(v)=>setProfile(setAtPath(profile,"appearance.profession",v))} /></Field>
        <Field label="Clothing style"><TextInput value={a.clothing_style} onChange={(v)=>setProfile(setAtPath(profile,"appearance.clothing_style",v))} /></Field>
      </div>
      <Field label="Titles" help="Comma-separated"><TextInput value={listToArrayString(a.titles)} onChange={(v)=>setProfile(setAtPath(profile,"appearance.titles",arrayStringToList(v)))} /></Field>
      <Field label="Visible notes" help="Comma-separated"><TextInput value={listToArrayString(a.visible_notes)} onChange={(v)=>setProfile(setAtPath(profile,"appearance.visible_notes",arrayStringToList(v)))} /></Field>
    </>
  );
}

function PersonalityEditor({ profile, setProfile }) {
  const m = profile.mind;
  const t = m.traits;
  const traitKeys = ["openness","conscientiousness","extraversion","agreeableness","neuroticism","honesty_humility","impulsivity","romantic_drive","dominance","empathy","jealousy","risk_tolerance"];
  return (
    <>
      <Field label="Biography summary">
        <textarea value={m.biography_summary} onChange={(e)=>setProfile(setAtPath(profile,"mind.biography_summary",e.target.value))} style={{width:"100%",minHeight:80,fontFamily:"inherit",padding:8,borderRadius:6,border:"1px solid #4b5563",background:"#111827",color:"#fff"}} />
      </Field>
      <Field label="Conversation style"><TextInput value={m.conversation_style} onChange={(v)=>setProfile(setAtPath(profile,"mind.conversation_style",v))} /></Field>
      <Field label="Values" help="Comma-separated"><TextInput value={listToArrayString(m.values)} onChange={(v)=>setProfile(setAtPath(profile,"mind.values",arrayStringToList(v)))} /></Field>
      <Field label="Beliefs" help="Comma-separated"><TextInput value={listToArrayString(m.beliefs)} onChange={(v)=>setProfile(setAtPath(profile,"mind.beliefs",arrayStringToList(v)))} /></Field>
      <Field label="Habits" help="Comma-separated"><TextInput value={listToArrayString(m.habits)} onChange={(v)=>setProfile(setAtPath(profile,"mind.habits",arrayStringToList(v)))} /></Field>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
        {traitKeys.map((k)=>(
          <Field key={k} label={k.replaceAll("_"," ")}>
            <SliderInput value={t[k]} onChange={(v)=>setProfile(setAtPath(profile,`mind.traits.${k}`,v))} />
          </Field>
        ))}
      </div>
    </>
  );
}

function PreferencesEditor({ profile, setProfile }) {
  const p = profile.female_partner_preference_for_male;
  return (
    <>
      <Field label="Target sex"><SelectInput value={p.target_sex} options={["male","female","intersex","unknown"]} onChange={(v)=>setProfile(setAtPath(profile,"female_partner_preference_for_male.target_sex",v))} /></Field>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
        <Field label="Attractiveness min"><SliderInput value={p.attractiveness_min} onChange={(v)=>setProfile(setAtPath(profile,"female_partner_preference_for_male.attractiveness_min",v))} /></Field>
        <Field label="Attractiveness ideal"><SliderInput value={p.attractiveness_ideal} onChange={(v)=>setProfile(setAtPath(profile,"female_partner_preference_for_male.attractiveness_ideal",v))} /></Field>
        <Field label="Uniqueness min"><SliderInput value={p.uniqueness_min} onChange={(v)=>setProfile(setAtPath(profile,"female_partner_preference_for_male.uniqueness_min",v))} /></Field>
        <Field label="Uniqueness ideal"><SliderInput value={p.uniqueness_ideal} onChange={(v)=>setProfile(setAtPath(profile,"female_partner_preference_for_male.uniqueness_ideal",v))} /></Field>
        <Field label="Attractiveness weight"><SliderInput min={0} max={1} step={0.01} value={p.attractiveness_weight} onChange={(v)=>setProfile(setAtPath(profile,"female_partner_preference_for_male.attractiveness_weight",v))} /></Field>
        <Field label="Uniqueness weight"><SliderInput min={0} max={1} step={0.01} value={p.uniqueness_weight} onChange={(v)=>setProfile(setAtPath(profile,"female_partner_preference_for_male.uniqueness_weight",v))} /></Field>
      </div>
      <Field label="Acceptable span"><SliderInput value={p.acceptable_span} onChange={(v)=>setProfile(setAtPath(profile,"female_partner_preference_for_male.acceptable_span",v))} /></Field>
    </>
  );
}

function RenderEditor({ profile, setProfile }) {
  const r = profile.render;
  return (
    <>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
        <Field label="Mesh ID"><TextInput value={r.mesh_id} onChange={(v)=>setProfile(setAtPath(profile,"render.mesh_id",v))} /></Field>
        <Field label="Material preset"><TextInput value={r.material_preset} onChange={(v)=>setProfile(setAtPath(profile,"render.material_preset",v))} /></Field>
        <Field label="Animation controller"><TextInput value={r.animation_controller} onChange={(v)=>setProfile(setAtPath(profile,"render.animation_controller",v))} /></Field>
        <Field label="Voice profile"><TextInput value={r.voice_profile} onChange={(v)=>setProfile(setAtPath(profile,"render.voice_profile",v))} /></Field>
        <Field label="Locomotion style"><TextInput value={r.locomotion_style} onChange={(v)=>setProfile(setAtPath(profile,"render.locomotion_style",v))} /></Field>
        <Field label="Idle set"><TextInput value={r.idle_set} onChange={(v)=>setProfile(setAtPath(profile,"render.idle_set",v))} /></Field>
        <Field label="Gesture set"><TextInput value={r.gesture_set} onChange={(v)=>setProfile(setAtPath(profile,"render.gesture_set",v))} /></Field>
        <Field label="Scale"><NumberInput value={r.scale} min={0.5} max={2.5} step={0.01} onChange={(v)=>setProfile(setAtPath(profile,"render.scale",v))} /></Field>
      </div>
      <Field label="Model analysis note">
        <textarea value={r.visible_from_model_analysis?.note || ""} onChange={(e)=>setProfile(setAtPath(profile,"render.visible_from_model_analysis.note",e.target.value))} style={{width:"100%",minHeight:80,fontFamily:"inherit",padding:8,borderRadius:6,border:"1px solid #4b5563",background:"#111827",color:"#fff"}} />
      </Field>
    </>
  );
}

function SummaryCard({ profile }) {
  const a = profile.appearance;
  const t = profile.mind.traits;
  return (
    <div style={{padding:12,background:"#1f2937",borderRadius:8,marginBottom:16}}>
      <h3 style={{marginTop:0}}>Profile summary</h3>
      <div><strong>{profile.name}</strong></div>
      <div>{a.age} · {a.sex} · {a.skin_tone} · {a.body_type}</div>
      <div>{a.profession || "no profession"} · {a.clothing_style}</div>
      <div>Symmetry {a.attractiveness_symmetry} / Uniqueness {a.uniqueness_score}</div>
      <div style={{marginTop:8,fontSize:13}}>Personality: O {t.openness}, C {t.conscientiousness}, E {t.extraversion}, A {t.agreeableness}, N {t.neuroticism}</div>
      <div style={{fontSize:13}}>Render: {profile.render.mesh_id} / {profile.render.animation_controller}</div>
    </div>
  );
}

export default function App() {
  const [world, setWorld] = useState(null);
  const [showThoughts, setShowThoughts] = useState(true);
  const [timeline, setTimeline] = useState([]);
  const [cursor, setCursor] = useState(1);
  const [replayWindow, setReplayWindow] = useState([]);
  const [selectedId, setSelectedId] = useState("npc_1");
  const [patchHealth, setPatchHealth] = useState("");
  const [patchRole, setPatchRole] = useState("");
  const [schema, setSchema] = useState(null);
  const [profile, setProfile] = useState(deepClone(DEFAULT_PROFILE));
  const [newCharId, setNewCharId] = useState("npc_3");
  const [profileStatus, setProfileStatus] = useState("");
  const [showRawJson, setShowRawJson] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");
    wsRef.current = ws;
    ws.onopen = () => ws.send(JSON.stringify({type:"set_thoughts", enabled: showThoughts}));
    ws.onmessage = (ev) => setWorld(JSON.parse(ev.data));
    return () => ws.close();
  }, []);

  useEffect(() => {
    fetch("http://localhost:8000/timeline").then(r => r.json()).then(d => setTimeline(d.events || []));
  }, [world?.tick]);

  useEffect(() => {
    fetch(`http://localhost:8000/timeline/replay/window?cursor_tick=${cursor}&radius=15`)
      .then(r => r.json()).then(d => setReplayWindow(d.events || []));
  }, [cursor]);

  useEffect(() => {
    fetch("http://localhost:8000/operator/schema/character-profile").then(r => r.json()).then(setSchema);
  }, []);

  useEffect(() => {
    const current = world?.characters?.[selectedId]?.profile;
    if (current) setProfile(current);
  }, [selectedId, world?.tick]);

  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({type:"set_thoughts", enabled: showThoughts}));
    }
  }, [showThoughts]);

  const patchCharacter = async () => {
    const body = { profile };
    if (patchHealth !== "") body.health = Number(patchHealth);
    if (patchRole !== "") body.institution_role = patchRole;
    await fetch(`http://localhost:8000/operator/character/${selectedId}`, {
      method: "PATCH",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(body)
    });
    setPatchHealth("");
    setPatchRole("");
    setProfileStatus("Saved profile changes.");
  };

  const createCharacter = async () => {
    const res = await fetch("http://localhost:8000/operator/character", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ char_id: newCharId, position: {x:1,y:1,z:0}, profile })
    });
    if (res.ok) {
      setSelectedId(newCharId);
      setProfileStatus(`Created ${newCharId}.`);
    } else {
      const err = await res.text();
      setProfileStatus(`Create failed: ${err}`);
    }
  };

  return (
    <div style={{display:"grid",gridTemplateColumns:"1fr 720px",height:"100%"}}>
      <div>
        <Canvas camera={{position:[6,10,16], fov:50}}>
          <ambientLight intensity={0.8} />
          <directionalLight position={[10,10,5]} intensity={1} />
          <OrbitControls />
          {world && Object.values(world.grid.tiles).map((tile) => <Tile key={`${tile.x},${tile.y},${tile.z}`} tile={tile} />)}
          {world && Object.values(world.characters).map((c) => <Character key={c.id} c={c} showThoughts={showThoughts} />)}
        </Canvas>
      </div>
      <div style={{padding:16,overflow:"auto",background:"#111",color:"#fff"}}>
        <h2>Form-based character creator</h2>
        <label style={{display:"block", marginBottom:16}}>
          <input type="checkbox" checked={showThoughts} onChange={(e)=>setShowThoughts(e.target.checked)} /> Show thought overlays
        </label>

        <Section title="Target character / save">
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
            <Field label="Edit existing character">
              <select value={selectedId} onChange={(e)=>setSelectedId(e.target.value)} style={{width:"100%",padding:8,borderRadius:6,border:"1px solid #4b5563",background:"#111827",color:"#fff"}}>
                {world && Object.keys(world.characters).map((id) => <option key={id} value={id}>{id}</option>)}
              </select>
            </Field>
            <Field label="New character id">
              <TextInput value={newCharId} onChange={setNewCharId} />
            </Field>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
            <Field label="Set health"><TextInput value={patchHealth} onChange={setPatchHealth} /></Field>
            <Field label="Institution role"><TextInput value={patchRole} onChange={setPatchRole} /></Field>
          </div>
          <button onClick={patchCharacter} style={{marginRight:8}}>Save to selected character</button>
          <button onClick={createCharacter}>Create new character</button>
          <div style={{marginTop:8,fontSize:12,opacity:0.85}}>{profileStatus}</div>
        </Section>

        <SummaryCard profile={profile} />
        <Section title="Appearance"><AppearanceEditor profile={profile} setProfile={setProfile} /></Section>
        <Section title="Personality"><PersonalityEditor profile={profile} setProfile={setProfile} /></Section>
        <Section title="Preferences"><PreferencesEditor profile={profile} setProfile={setProfile} /></Section>
        <Section title="Render"><RenderEditor profile={profile} setProfile={setProfile} /></Section>

        <Section title="Raw JSON / schema" defaultOpen={false}>
          <label style={{display:"block", marginBottom:12}}>
            <input type="checkbox" checked={showRawJson} onChange={(e)=>setShowRawJson(e.target.checked)} /> Show raw JSON
          </label>
          {showRawJson && <pre style={{whiteSpace:"pre-wrap",fontSize:12,background:"#111827",padding:12,borderRadius:6,overflow:"auto"}}>{JSON.stringify(profile, null, 2)}</pre>}
          <h4>Schema</h4>
          <div style={{maxHeight:240,overflow:"auto"}}>
            <pre style={{whiteSpace:"pre-wrap",fontSize:12}}>{schema ? JSON.stringify(schema, null, 2) : "Loading..."}</pre>
          </div>
        </Section>

        {world && (
          <>
            <Section title="Relationships" defaultOpen={false}>
              <pre style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(world.relationships, null, 2)}</pre>
            </Section>

            <Section title="Replay scrubber" defaultOpen={false}>
              <input type="range" min="1" max={Math.max(1, world.tick)} value={cursor} onChange={(e)=>setCursor(Number(e.target.value))} style={{width:"100%"}} />
              <div>Cursor tick: {cursor}</div>
              <div style={{maxHeight:220,overflow:"auto",marginTop:8}}>
                {replayWindow.map((e) => (
                  <div key={e.id} style={{padding:"6px 0",borderBottom:"1px solid #374151"}}>
                    <div>tick {e.tick} · {e.kind}</div>
                    <div style={{fontSize:12,opacity:0.8}}>actor: {e.actor_id || "-"} target: {e.target_id || "-"}</div>
                    <pre style={{whiteSpace:"pre-wrap",fontSize:12}}>{JSON.stringify(e.payload, null, 2)}</pre>
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Latest timeline" defaultOpen={false}>
              <div style={{maxHeight:220,overflow:"auto"}}>
                {timeline.map((e) => (
                  <div key={e.id} style={{padding:"6px 0",borderBottom:"1px solid #374151"}}>
                    <div>tick {e.tick} · {e.kind}</div>
                    <pre style={{whiteSpace:"pre-wrap",fontSize:12}}>{JSON.stringify(e.payload, null, 2)}</pre>
                  </div>
                ))}
              </div>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
