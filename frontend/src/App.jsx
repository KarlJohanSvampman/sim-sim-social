import React, { useEffect, useRef, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, Html, Line } from "@react-three/drei";
import * as THREE from "three";

function TopBar({ page, setPage }) {
  const btn = (id, label) => (
    <button
      onClick={() => setPage(id)}
      style={{
        padding: "8px 12px",
        borderRadius: 8,
        border: "1px solid #4b5563",
        background: page === id ? "#374151" : "#111827",
        color: "#fff",
        cursor: "pointer"
      }}
    >
      {label}
    </button>
  );
  return (
    <div style={{ height: 56, display: "flex", alignItems: "center", gap: 10, padding: "0 12px", borderBottom: "1px solid #374151", background: "#111827", color: "#fff" }}>
      <div style={{ fontWeight: 700, marginRight: 8 }}>Neighborhood Sim</div>
      {btn("map", "Map")}
      {btn("creator", "Character Creator")}
      {btn("debug", "Debug")}
      {btn("settings", "Settings")}
    </div>
  );
}

function Tile({ tile, isSelected, onSelect }) {
  const isWall = tile.type && tile.type.startsWith("wall");
  const h = isWall ? 1.2 : isSelected ? 0.2 : 0.08;
  const y = h / 2;
  const color = isWall ? "#6b7280" : isSelected ? "#f59e0b" : "#7fb069";
  return (
    <group position={[tile.x, 0, tile.y]}>
      <mesh position={[0, y, 0]} onClick={(e) => { e.stopPropagation(); onSelect(tile); }}>
        <boxGeometry args={[0.96, h, 0.96]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {!isWall && (
        <Line
          points={[
            [-0.48, 0.085, -0.48],
            [0.48, 0.085, -0.48],
            [0.48, 0.085, 0.48],
            [-0.48, 0.085, 0.48],
            [-0.48, 0.085, -0.48]
          ]}
          color="#111827"
          lineWidth={1}
        />
      )}
    </group>
  );
}

function Character({ c, showThoughts }) {
  const app = c.appearance_summary || {};
  return (
    <group position={[c.position.x, 0.65, c.position.y]}>
      <mesh>
        <capsuleGeometry args={[0.22, 0.8, 4, 8]} />
        <meshStandardMaterial color="#3b82f6" />
      </mesh>
      <Html position={[0, 1.0, 0]} center>
        <div style={{ background: "#fff", padding: "4px 6px", borderRadius: 6, border: "1px solid #999", fontSize: 12, maxWidth: 240 }}>
          <strong>{c.name}</strong><br />
          {c.speech ? <span>💬 {c.speech}</span> : showThoughts ? <span>💭 {c.thoughts}</span> : <span>…</span>}
          <br /><small>{app.age ?? "?"} · {app.sex || "unknown"} · {app.body_type || "?"}</small>
        </div>
      </Html>
    </group>
  );
}

function GridAxes({ width, height }) {
  return (
    <>
      <Line points={[[0, 0.02, 0], [width, 0.02, 0]]} color="#ef4444" lineWidth={2} />
      <Line points={[[0, 0.02, 0], [0, 0.02, height]]} color="#3b82f6" lineWidth={2} />
    </>
  );
}

function RightToolbar({ zoomIn, zoomOut }) {
  const style = { width: 42, height: 42, borderRadius: 10, border: "1px solid #4b5563", background: "#111827", color: "#fff", fontSize: 22, cursor: "pointer" };
  return (
    <div style={{ position: "absolute", right: 14, top: 76, display: "flex", flexDirection: "column", gap: 8, zIndex: 20 }}>
      <button style={style} onClick={zoomIn} title="Zoom in">+</button>
      <button style={style} onClick={zoomOut} title="Zoom out">−</button>
    </div>
  );
}

function TileInfoOverlay({ tile }) {
  if (!tile) return null;
  return (
    <div style={{ position: "absolute", top: 76, right: 70, width: 280, background: "rgba(17,24,39,0.96)", color: "#fff", border: "1px solid #374151", borderRadius: 10, padding: 12, zIndex: 20 }}>
      <div style={{ fontWeight: 700, marginBottom: 8 }}>Selected Tile</div>
      <div>x: {tile.x}</div>
      <div>y: {tile.y}</div>
      <div>z: {tile.z}</div>
      <div>type: {tile.type || "floor"}</div>
      <div>blocks movement: {String(tile.blocks_movement)}</div>
      <div>blocks sight: {String(tile.blocks_sight)}</div>
    </div>
  );
}

function ControlledOrbit({ controlsRef, centerX, centerZ }) {
  const { camera } = useThree();
  useEffect(() => {
    if (controlsRef.current) {
      controlsRef.current.target.set(centerX, 0, centerZ);
      camera.position.set(centerX + 3, 12, centerZ + 8);
      controlsRef.current.update();
    }
  }, [camera, controlsRef, centerX, centerZ]);
  return (
    <OrbitControls
      ref={controlsRef}
      enableRotate={false}
      enablePan={true}
      enableZoom={true}
      screenSpacePanning={true}
      mouseButtons={{ LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN }}
    />
  );
}

function LoadingPage() {
  return <div style={{ height: "calc(100vh - 56px)", display: "grid", placeItems: "center", background: "#0b1020", color: "#fff" }}>Loading…</div>;
}

function MapPage({ world, showThoughts }) {
  const [selectedTile, setSelectedTile] = useState(null);
  const controlsRef = useRef(null);

  useEffect(() => {
    const onContextMenu = (e) => { e.preventDefault(); setSelectedTile(null); };
    window.addEventListener("contextmenu", onContextMenu);
    return () => window.removeEventListener("contextmenu", onContextMenu);
  }, []);

  if (!world?.grid?.tiles) return <LoadingPage />;

  const width = world.grid.width || 12;
  const height = world.grid.height || 12;
  const centerX = width / 2 - 0.5;
  const centerZ = height / 2 - 0.5;

  const zoomIn = () => {
    if (!controlsRef.current) return;
    controlsRef.current.object.position.y = Math.max(4, controlsRef.current.object.position.y - 2);
    controlsRef.current.object.position.z = Math.max(4, controlsRef.current.object.position.z - 1.5);
    controlsRef.current.update();
  };
  const zoomOut = () => {
    if (!controlsRef.current) return;
    controlsRef.current.object.position.y += 2;
    controlsRef.current.object.position.z += 1.5;
    controlsRef.current.update();
  };

  return (
    <div style={{ position: "relative", height: "calc(100vh - 56px)", background: "#0b1020" }}>
      <RightToolbar zoomIn={zoomIn} zoomOut={zoomOut} />
      <TileInfoOverlay tile={selectedTile} />
      <Canvas camera={{ position: [centerX + 3, 12, centerZ + 8], fov: 50 }} onPointerMissed={(e) => { if (e.type === "click") setSelectedTile(null); }}>
        <color attach="background" args={["#0b1020"]} />
        <ambientLight intensity={0.9} />
        <directionalLight position={[10, 16, 8]} intensity={1.3} castShadow />
        <ControlledOrbit controlsRef={controlsRef} centerX={centerX} centerZ={centerZ} />
        <GridAxes width={width} height={height} />
        {Object.values(world.grid.tiles).map((tile) => (
          <Tile
            key={`${tile.x},${tile.y},${tile.z}`}
            tile={tile}
            isSelected={selectedTile && selectedTile.x === tile.x && selectedTile.y === tile.y && selectedTile.z === tile.z}
            onSelect={setSelectedTile}
          />
        ))}
        {Object.values(world.characters || {}).map((c) => <Character key={c.id} c={c} showThoughts={showThoughts} />)}
      </Canvas>
    </div>
  );
}

function Section({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ padding: 12, background: "#1f2937", borderRadius: 8, marginBottom: 16 }}>
      <button onClick={() => setOpen(!open)} style={{ background: "transparent", border: "none", color: "#fff", fontSize: 18, fontWeight: 700, padding: 0, marginBottom: open ? 12 : 0, cursor: "pointer" }}>
        {open ? "▾" : "▸"} {title}
      </button>
      {open && children}
    </div>
  );
}

function Field({ label, children, help }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{label}</div>
      {children}
      {help && <div style={{ fontSize: 11, opacity: 0.75, marginTop: 4 }}>{help}</div>}
    </div>
  );
}

function TextInput({ value, onChange }) {
  return <input value={value ?? ""} onChange={(e) => onChange(e.target.value)} style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #4b5563", background: "#111827", color: "#fff" }} />;
}
function NumberInput({ value, onChange, min, max, step = 1 }) {
  return <input type="number" value={value ?? 0} min={min} max={max} step={step} onChange={(e) => onChange(Number(e.target.value))} style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #4b5563", background: "#111827", color: "#fff" }} />;
}
function SelectInput({ value, onChange, options }) {
  return (
    <select value={value ?? ""} onChange={(e) => onChange(e.target.value)} style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #4b5563", background: "#111827", color: "#fff" }}>
      {options.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
    </select>
  );
}
function SliderInput({ value, onChange, min = 0, max = 100, step = 1 }) {
  return (
    <div>
      <input type="range" min={min} max={max} step={step} value={value ?? 0} onChange={(e) => onChange(Number(e.target.value))} style={{ width: "100%" }} />
      <div style={{ fontSize: 12, opacity: 0.8 }}>{value}</div>
    </div>
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
    visible_from_model_analysis: { status: "placeholder", note: "Future hook for model-derived visual features." }
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

function deepClone(obj) { return JSON.parse(JSON.stringify(obj)); }
function setAtPath(obj, path, value) {
  const copy = deepClone(obj);
  const parts = path.split(".");
  let cur = copy;
  for (let i = 0; i < parts.length - 1; i++) cur = cur[parts[i]];
  cur[parts[parts.length - 1]] = value;
  return copy;
}
function arrayStringToList(text) { return text.split(",").map((x) => x.trim()).filter(Boolean); }
function listToArrayString(list) { return Array.isArray(list) ? list.join(", ") : ""; }

function AppearanceEditor({ profile, setProfile }) {
  const a = profile.appearance;
  return (
    <>
      <Field label="Name"><TextInput value={profile.name} onChange={(v) => setProfile(setAtPath(profile, "name", v))} /></Field>
      <Field label="Public name"><TextInput value={a.public_name} onChange={(v) => setProfile(setAtPath(profile, "appearance.public_name", v))} /></Field>
      <Field label="Nicknames" help="Comma-separated"><TextInput value={listToArrayString(profile.nicknames)} onChange={(v) => setProfile(setAtPath(profile, "nicknames", arrayStringToList(v)))} /></Field>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Field label="Age"><NumberInput value={a.age} min={0} max={120} onChange={(v) => setProfile(setAtPath(profile, "appearance.age", v))} /></Field>
        <Field label="Sex"><SelectInput value={a.sex} options={["female", "male", "intersex", "unknown"]} onChange={(v) => setProfile(setAtPath(profile, "appearance.sex", v))} /></Field>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Field label="Skin tone"><TextInput value={a.skin_tone} onChange={(v) => setProfile(setAtPath(profile, "appearance.skin_tone", v))} /></Field>
        <Field label="Body type"><SelectInput value={a.body_type} options={["slim", "average", "muscular", "fat", "obese"]} onChange={(v) => setProfile(setAtPath(profile, "appearance.body_type", v))} /></Field>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
        <Field label="Height (cm)"><NumberInput value={a.height_cm} min={80} max={260} onChange={(v) => setProfile(setAtPath(profile, "appearance.height_cm", v))} /></Field>
        <Field label="Hair color"><TextInput value={a.hair_color} onChange={(v) => setProfile(setAtPath(profile, "appearance.hair_color", v))} /></Field>
        <Field label="Eye color"><TextInput value={a.eye_color} onChange={(v) => setProfile(setAtPath(profile, "appearance.eye_color", v))} /></Field>
      </div>
      <Field label="Attractiveness symmetry score"><SliderInput value={a.attractiveness_symmetry} onChange={(v) => setProfile(setAtPath(profile, "appearance.attractiveness_symmetry", v))} /></Field>
      <Field label="Uniqueness score"><SliderInput value={a.uniqueness_score} onChange={(v) => setProfile(setAtPath(profile, "appearance.uniqueness_score", v))} /></Field>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Field label="Profession"><TextInput value={a.profession || ""} onChange={(v) => setProfile(setAtPath(profile, "appearance.profession", v))} /></Field>
        <Field label="Clothing style"><TextInput value={a.clothing_style} onChange={(v) => setProfile(setAtPath(profile, "appearance.clothing_style", v))} /></Field>
      </div>
      <Field label="Titles" help="Comma-separated"><TextInput value={listToArrayString(a.titles)} onChange={(v) => setProfile(setAtPath(profile, "appearance.titles", arrayStringToList(v)))} /></Field>
      <Field label="Visible notes" help="Comma-separated"><TextInput value={listToArrayString(a.visible_notes)} onChange={(v) => setProfile(setAtPath(profile, "appearance.visible_notes", arrayStringToList(v)))} /></Field>
    </>
  );
}

function PersonalityEditor({ profile, setProfile }) {
  const m = profile.mind;
  const t = m.traits;
  const keys = ["openness","conscientiousness","extraversion","agreeableness","neuroticism","honesty_humility","impulsivity","romantic_drive","dominance","empathy","jealousy","risk_tolerance"];
  return (
    <>
      <Field label="Biography summary"><textarea value={m.biography_summary} onChange={(e) => setProfile(setAtPath(profile, "mind.biography_summary", e.target.value))} style={{ width: "100%", minHeight: 80, fontFamily: "inherit", padding: 8, borderRadius: 6, border: "1px solid #4b5563", background: "#111827", color: "#fff" }} /></Field>
      <Field label="Conversation style"><TextInput value={m.conversation_style} onChange={(v) => setProfile(setAtPath(profile, "mind.conversation_style", v))} /></Field>
      <Field label="Values" help="Comma-separated"><TextInput value={listToArrayString(m.values)} onChange={(v) => setProfile(setAtPath(profile, "mind.values", arrayStringToList(v)))} /></Field>
      <Field label="Beliefs" help="Comma-separated"><TextInput value={listToArrayString(m.beliefs)} onChange={(v) => setProfile(setAtPath(profile, "mind.beliefs", arrayStringToList(v)))} /></Field>
      <Field label="Habits" help="Comma-separated"><TextInput value={listToArrayString(m.habits)} onChange={(v) => setProfile(setAtPath(profile, "mind.habits", arrayStringToList(v)))} /></Field>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {keys.map((k) => <Field key={k} label={k.replaceAll("_", " ")}><SliderInput value={t[k]} onChange={(v) => setProfile(setAtPath(profile, `mind.traits.${k}`, v))} /></Field>)}
      </div>
    </>
  );
}

function PreferencesEditor({ profile, setProfile }) {
  const p = profile.female_partner_preference_for_male;
  return (
    <>
      <Field label="Target sex"><SelectInput value={p.target_sex} options={["male", "female", "intersex", "unknown"]} onChange={(v) => setProfile(setAtPath(profile, "female_partner_preference_for_male.target_sex", v))} /></Field>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Field label="Attractiveness min"><SliderInput value={p.attractiveness_min} onChange={(v) => setProfile(setAtPath(profile, "female_partner_preference_for_male.attractiveness_min", v))} /></Field>
        <Field label="Attractiveness ideal"><SliderInput value={p.attractiveness_ideal} onChange={(v) => setProfile(setAtPath(profile, "female_partner_preference_for_male.attractiveness_ideal", v))} /></Field>
        <Field label="Uniqueness min"><SliderInput value={p.uniqueness_min} onChange={(v) => setProfile(setAtPath(profile, "female_partner_preference_for_male.uniqueness_min", v))} /></Field>
        <Field label="Uniqueness ideal"><SliderInput value={p.uniqueness_ideal} onChange={(v) => setProfile(setAtPath(profile, "female_partner_preference_for_male.uniqueness_ideal", v))} /></Field>
        <Field label="Attractiveness weight"><SliderInput min={0} max={1} step={0.01} value={p.attractiveness_weight} onChange={(v) => setProfile(setAtPath(profile, "female_partner_preference_for_male.attractiveness_weight", v))} /></Field>
        <Field label="Uniqueness weight"><SliderInput min={0} max={1} step={0.01} value={p.uniqueness_weight} onChange={(v) => setProfile(setAtPath(profile, "female_partner_preference_for_male.uniqueness_weight", v))} /></Field>
      </div>
      <Field label="Acceptable span"><SliderInput value={p.acceptable_span} onChange={(v) => setProfile(setAtPath(profile, "female_partner_preference_for_male.acceptable_span", v))} /></Field>
    </>
  );
}

function RenderEditor({ profile, setProfile }) {
  const r = profile.render;
  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Field label="Mesh ID"><TextInput value={r.mesh_id} onChange={(v) => setProfile(setAtPath(profile, "render.mesh_id", v))} /></Field>
        <Field label="Material preset"><TextInput value={r.material_preset} onChange={(v) => setProfile(setAtPath(profile, "render.material_preset", v))} /></Field>
        <Field label="Animation controller"><TextInput value={r.animation_controller} onChange={(v) => setProfile(setAtPath(profile, "render.animation_controller", v))} /></Field>
        <Field label="Voice profile"><TextInput value={r.voice_profile} onChange={(v) => setProfile(setAtPath(profile, "render.voice_profile", v))} /></Field>
        <Field label="Locomotion style"><TextInput value={r.locomotion_style} onChange={(v) => setProfile(setAtPath(profile, "render.locomotion_style", v))} /></Field>
        <Field label="Idle set"><TextInput value={r.idle_set} onChange={(v) => setProfile(setAtPath(profile, "render.idle_set", v))} /></Field>
        <Field label="Gesture set"><TextInput value={r.gesture_set} onChange={(v) => setProfile(setAtPath(profile, "render.gesture_set", v))} /></Field>
        <Field label="Scale"><NumberInput value={r.scale} min={0.5} max={2.5} step={0.01} onChange={(v) => setProfile(setAtPath(profile, "render.scale", v))} /></Field>
      </div>
      <Field label="Model analysis note"><textarea value={r.visible_from_model_analysis?.note || ""} onChange={(e) => setProfile(setAtPath(profile, "render.visible_from_model_analysis.note", e.target.value))} style={{ width: "100%", minHeight: 80, fontFamily: "inherit", padding: 8, borderRadius: 6, border: "1px solid #4b5563", background: "#111827", color: "#fff" }} /></Field>
    </>
  );
}

function CharacterCreatorPage({ world }) {
  const [selectedId, setSelectedId] = useState("npc_1");
  const [patchHealth, setPatchHealth] = useState("");
  const [patchRole, setPatchRole] = useState("");
  const [schema, setSchema] = useState(null);
  const [profile, setProfile] = useState(deepClone(DEFAULT_PROFILE));
  const [newCharId, setNewCharId] = useState("npc_3");
  const [profileStatus, setProfileStatus] = useState("");
  const [showRawJson, setShowRawJson] = useState(false);

  useEffect(() => { fetch("http://localhost:8000/operator/schema/character-profile").then((r) => r.json()).then(setSchema); }, []);
  useEffect(() => {
    const current = world?.characters?.[selectedId]?.profile;
    if (current) setProfile(current);
  }, [selectedId, world?.tick]);

  const patchCharacter = async () => {
    const body = { profile };
    if (patchHealth !== "") body.health = Number(patchHealth);
    if (patchRole !== "") body.institution_role = patchRole;
    await fetch(`http://localhost:8000/operator/character/${selectedId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    setPatchHealth("");
    setPatchRole("");
    setProfileStatus("Saved profile changes.");
  };

  const createCharacter = async () => {
    const res = await fetch("http://localhost:8000/operator/character", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ char_id: newCharId, position: { x: 1, y: 1, z: 0 }, profile }) });
    if (res.ok) {
      setSelectedId(newCharId);
      setProfileStatus(`Created ${newCharId}.`);
    } else {
      const err = await res.text();
      setProfileStatus(`Create failed: ${err}`);
    }
  };

  return (
    <div style={{ padding: 16, overflow: "auto", height: "calc(100vh - 56px)", background: "#111", color: "#fff" }}>
      <Section title="Target character / save">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <Field label="Edit existing character"><select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #4b5563", background: "#111827", color: "#fff" }}>{world && Object.keys(world.characters).map((id) => <option key={id} value={id}>{id}</option>)}</select></Field>
          <Field label="New character id"><TextInput value={newCharId} onChange={setNewCharId} /></Field>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <Field label="Set health"><TextInput value={patchHealth} onChange={setPatchHealth} /></Field>
          <Field label="Institution role"><TextInput value={patchRole} onChange={setPatchRole} /></Field>
        </div>
        <button onClick={patchCharacter} style={{ marginRight: 8 }}>Save to selected character</button>
        <button onClick={createCharacter}>Create new character</button>
        <div style={{ marginTop: 8, fontSize: 12, opacity: 0.85 }}>{profileStatus}</div>
      </Section>
      <Section title="Appearance"><AppearanceEditor profile={profile} setProfile={setProfile} /></Section>
      <Section title="Personality"><PersonalityEditor profile={profile} setProfile={setProfile} /></Section>
      <Section title="Preferences"><PreferencesEditor profile={profile} setProfile={setProfile} /></Section>
      <Section title="Render"><RenderEditor profile={profile} setProfile={setProfile} /></Section>
      <Section title="Raw JSON / schema" defaultOpen={false}>
        <label style={{ display: "block", marginBottom: 12 }}><input type="checkbox" checked={showRawJson} onChange={(e) => setShowRawJson(e.target.checked)} /> Show raw JSON</label>
        {showRawJson && <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, background: "#111827", padding: 12, borderRadius: 6, overflow: "auto" }}>{JSON.stringify(profile, null, 2)}</pre>}
        <div style={{ maxHeight: 240, overflow: "auto" }}><pre style={{ whiteSpace: "pre-wrap", fontSize: 12 }}>{schema ? JSON.stringify(schema, null, 2) : "Loading..."}</pre></div>
      </Section>
    </div>
  );
}

function DebugPage({ world }) {
  const [timeline, setTimeline] = useState([]);
  const [cursor, setCursor] = useState(1);
  const [replayWindow, setReplayWindow] = useState([]);
  useEffect(() => { fetch("http://localhost:8000/timeline").then((r) => r.json()).then((d) => setTimeline(d.events || [])); }, [world?.tick]);
  useEffect(() => { fetch(`http://localhost:8000/timeline/replay/window?cursor_tick=${cursor}&radius=15`).then((r) => r.json()).then((d) => setReplayWindow(d.events || [])); }, [cursor]);
  return (
    <div style={{ padding: 16, overflow: "auto", height: "calc(100vh - 56px)", background: "#111", color: "#fff" }}>
      <Section title="Relationships"><pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(world?.relationships || {}, null, 2)}</pre></Section>
      <Section title="Replay scrubber">
        <input type="range" min="1" max={Math.max(1, world?.tick || 1)} value={cursor} onChange={(e) => setCursor(Number(e.target.value))} style={{ width: "100%" }} />
        <div>Cursor tick: {cursor}</div>
        <div style={{ maxHeight: 240, overflow: "auto", marginTop: 8 }}>
          {replayWindow.map((e) => <div key={e.id} style={{ padding: "6px 0", borderBottom: "1px solid #374151" }}><div>tick {e.tick} · {e.kind}</div><div style={{ fontSize: 12, opacity: 0.8 }}>actor: {e.actor_id || "-"} target: {e.target_id || "-"}</div><pre style={{ whiteSpace: "pre-wrap", fontSize: 12 }}>{JSON.stringify(e.payload, null, 2)}</pre></div>)}
        </div>
      </Section>
      <Section title="Latest timeline" defaultOpen={false}>
        <div style={{ maxHeight: 260, overflow: "auto" }}>
          {timeline.map((e) => <div key={e.id} style={{ padding: "6px 0", borderBottom: "1px solid #374151" }}><div>tick {e.tick} · {e.kind}</div><pre style={{ whiteSpace: "pre-wrap", fontSize: 12 }}>{JSON.stringify(e.payload, null, 2)}</pre></div>)}
        </div>
      </Section>
    </div>
  );
}

function SettingsPage({ showThoughts, setShowThoughts }) {
  return (
    <div style={{ padding: 16, overflow: "auto", height: "calc(100vh - 56px)", background: "#111", color: "#fff" }}>
      <Section title="Settings"><label style={{ display: "block", marginBottom: 16 }}><input type="checkbox" checked={showThoughts} onChange={(e) => setShowThoughts(e.target.checked)} /> Show thought overlays</label></Section>
    </div>
  );
}

export default function App() {
  const [world, setWorld] = useState(null);
  const [showThoughts, setShowThoughts] = useState(true);
  const [page, setPage] = useState("map");
  const wsRef = useRef(null);

  useEffect(() => { fetch("http://localhost:8000/world").then((r) => r.json()).then(setWorld).catch(() => {}); }, []);
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");
    wsRef.current = ws;
    ws.onopen = () => ws.send(JSON.stringify({ type: "set_thoughts", enabled: showThoughts }));
    ws.onmessage = (ev) => setWorld(JSON.parse(ev.data));
    return () => ws.close();
  }, []);
  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "set_thoughts", enabled: showThoughts }));
    }
  }, [showThoughts]);

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <TopBar page={page} setPage={setPage} />
      {page === "map" && <MapPage world={world} showThoughts={showThoughts} />}
      {page === "creator" && <CharacterCreatorPage world={world} />}
      {page === "debug" && <DebugPage world={world} />}
      {page === "settings" && <SettingsPage showThoughts={showThoughts} setShowThoughts={setShowThoughts} />}
    </div>
  );
}
