import React, { useEffect, useRef, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";

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
    <div
      style={{
        height: 56,
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "0 12px",
        borderBottom: "1px solid #374151",
        background: "#111827",
        color: "#fff"
      }}
    >
      <div style={{ fontWeight: 700, marginRight: 8 }}>Neighborhood Sim</div>
      {btn("map", "Map")}
      {btn("creator", "Character Creator")}
      {btn("debug", "Debug")}
      {btn("settings", "Settings")}
    </div>
  );
}

function Tile({ tile, isSelected, onSelect }) {
  const color =
    tile.type && tile.type.startsWith("wall")
      ? "#666"
      : isSelected
        ? "#f59e0b"
        : "#9fd08a";

  return (
    <mesh
      position={[tile.x, 0, tile.y]}
      rotation={[-Math.PI / 2, 0, 0]}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(tile);
      }}
    >
      <planeGeometry args={[1, 1]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}

function Character({ c, showThoughts }) {
  const app = c.appearance_summary || {};
  return (
    <group position={[c.position.x, 0.5, c.position.y]}>
      <mesh>
        <boxGeometry args={[0.6, 1.2, 0.6]} />
        <meshStandardMaterial color="#3b82f6" />
      </mesh>
      <Html position={[0, 1.2, 0]} center>
        <div
          style={{
            background: "#fff",
            padding: "4px 6px",
            borderRadius: 6,
            border: "1px solid #999",
            fontSize: 12,
            maxWidth: 240
          }}
        >
          <strong>{c.name}</strong>
          <br />
          {c.speech ? <span>💬 {c.speech}</span> : showThoughts ? <span>💭 {c.thoughts}</span> : <span>…</span>}
          <br />
          <small>{app.age ?? "?"} · {app.sex || "unknown"} · {app.body_type || "?"}</small>
        </div>
      </Html>
    </group>
  );
}

function RightToolbar({ zoomIn, zoomOut }) {
  const buttonStyle = {
    width: 42,
    height: 42,
    borderRadius: 10,
    border: "1px solid #4b5563",
    background: "#111827",
    color: "#fff",
    fontSize: 22,
    cursor: "pointer"
  };

  return (
    <div
      style={{
        position: "absolute",
        right: 14,
        top: 76,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        zIndex: 20
      }}
    >
      <button style={buttonStyle} onClick={zoomIn} title="Zoom in">+</button>
      <button style={buttonStyle} onClick={zoomOut} title="Zoom out">−</button>
    </div>
  );
}

function TileInfoOverlay({ tile }) {
  if (!tile) return null;
  return (
    <div
      style={{
        position: "absolute",
        top: 76,
        right: 70,
        width: 260,
        background: "rgba(17,24,39,0.96)",
        color: "#fff",
        border: "1px solid #374151",
        borderRadius: 10,
        padding: 12,
        zIndex: 20
      }}
    >
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

function ControlledOrbit({ controlsRef }) {
  const { camera } = useThree();

  useEffect(() => {
    if (controlsRef.current) {
      controlsRef.current.target.set(6, 0, 6);
      camera.position.set(6, 12, 16);
      controlsRef.current.update();
    }
  }, [camera, controlsRef]);

  return (
    <OrbitControls
      ref={controlsRef}
      enableRotate={false}
      enablePan={true}
      enableZoom={true}
      mouseButtons={{
        LEFT: -1,
        MIDDLE: 1,
        RIGHT: 2
      }}
    />
  );
}

function MapPage({ world, showThoughts }) {
  const [selectedTile, setSelectedTile] = useState(null);
  const controlsRef = useRef(null);

  useEffect(() => {
    const onContextMenu = (e) => {
      e.preventDefault();
      setSelectedTile(null);
    };
    window.addEventListener("contextmenu", onContextMenu);
    return () => window.removeEventListener("contextmenu", onContextMenu);
  }, []);

  const zoomIn = () => {
    if (!controlsRef.current) return;
    controlsRef.current.object.position.y = Math.max(4, controlsRef.current.object.position.y - 2);
    controlsRef.current.object.position.z = Math.max(4, controlsRef.current.object.position.z - 2);
    controlsRef.current.update();
  };

  const zoomOut = () => {
    if (!controlsRef.current) return;
    controlsRef.current.object.position.y += 2;
    controlsRef.current.object.position.z += 2;
    controlsRef.current.update();
  };

  return (
    <div style={{ position: "relative", height: "calc(100vh - 56px)", background: "#0b1020" }}>
      <RightToolbar zoomIn={zoomIn} zoomOut={zoomOut} />
      <TileInfoOverlay tile={selectedTile} />
      <Canvas
        camera={{ position: [6, 12, 16], fov: 50 }}
        onPointerMissed={(e) => {
          if (e.type === "click") setSelectedTile(null);
        }}
      >
        <ambientLight intensity={0.8} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <ControlledOrbit controlsRef={controlsRef} />
        {world && Object.values(world.grid.tiles).map((tile) => (
          <Tile
            key={`${tile.x},${tile.y},${tile.z}`}
            tile={tile}
            isSelected={selectedTile && selectedTile.x === tile.x && selectedTile.y === tile.y && selectedTile.z === tile.z}
            onSelect={setSelectedTile}
          />
        ))}
        {world && Object.values(world.characters).map((c) => (
          <Character key={c.id} c={c} showThoughts={showThoughts} />
        ))}
      </Canvas>
    </div>
  );
}

function Section({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ padding: 12, background: "#1f2937", borderRadius: 8, marginBottom: 16 }}>
      <button
        onClick={() => setOpen(!open)}
        style={{ background: "transparent", border: "none", color: "#fff", fontSize: 18, fontWeight: 700, padding: 0, marginBottom: open ? 12 : 0, cursor: "pointer" }}
      >
        {open ? "▾" : "▸"} {title}
      </button>
      {open && children}
    </div>
  );
}

function CreatorPage() {
  return (
    <div style={{ padding: 16, overflow: "auto", height: "calc(100vh - 56px)", background: "#111", color: "#fff" }}>
      <Section title="Character Creator">
        <div>The existing character creator remains available in the repo. This page is the navigation entry point from the new map-first frontend.</div>
        <div style={{ marginTop: 8, fontSize: 13, opacity: 0.8 }}>
          You can continue extending this page into the full form-based creator.
        </div>
      </Section>
    </div>
  );
}

function DebugPage({ world }) {
  const [timeline, setTimeline] = useState([]);
  const [cursor, setCursor] = useState(1);
  const [replayWindow, setReplayWindow] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/timeline")
      .then((r) => r.json())
      .then((d) => setTimeline(d.events || []));
  }, [world?.tick]);

  useEffect(() => {
    fetch(`http://localhost:8000/timeline/replay/window?cursor_tick=${cursor}&radius=15`)
      .then((r) => r.json())
      .then((d) => setReplayWindow(d.events || []));
  }, [cursor]);

  return (
    <div style={{ padding: 16, overflow: "auto", height: "calc(100vh - 56px)", background: "#111", color: "#fff" }}>
      <Section title="Replay scrubber">
        <input type="range" min="1" max={Math.max(1, world?.tick || 1)} value={cursor} onChange={(e) => setCursor(Number(e.target.value))} style={{ width: "100%" }} />
        <div>Cursor tick: {cursor}</div>
        <div style={{ maxHeight: 240, overflow: "auto", marginTop: 8 }}>
          {replayWindow.map((e) => (
            <div key={e.id} style={{ padding: "6px 0", borderBottom: "1px solid #374151" }}>
              <div>tick {e.tick} · {e.kind}</div>
              <div style={{ fontSize: 12, opacity: 0.8 }}>actor: {e.actor_id || "-"} target: {e.target_id || "-"}</div>
              <pre style={{ whiteSpace: "pre-wrap", fontSize: 12 }}>{JSON.stringify(e.payload, null, 2)}</pre>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Latest timeline" defaultOpen={false}>
        <div style={{ maxHeight: 260, overflow: "auto" }}>
          {timeline.map((e) => (
            <div key={e.id} style={{ padding: "6px 0", borderBottom: "1px solid #374151" }}>
              <div>tick {e.tick} · {e.kind}</div>
              <pre style={{ whiteSpace: "pre-wrap", fontSize: 12 }}>{JSON.stringify(e.payload, null, 2)}</pre>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

function SettingsPage({ showThoughts, setShowThoughts }) {
  return (
    <div style={{ padding: 16, overflow: "auto", height: "calc(100vh - 56px)", background: "#111", color: "#fff" }}>
      <Section title="Settings">
        <label style={{ display: "block", marginBottom: 16 }}>
          <input type="checkbox" checked={showThoughts} onChange={(e) => setShowThoughts(e.target.checked)} />
          {" "}Show thought overlays
        </label>
      </Section>
    </div>
  );
}

export default function App() {
  const [world, setWorld] = useState(null);
  const [showThoughts, setShowThoughts] = useState(true);
  const [page, setPage] = useState("map");
  const wsRef = useRef(null);

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
      {page === "creator" && <CreatorPage />}
      {page === "debug" && <DebugPage world={world} />}
      {page === "settings" && <SettingsPage showThoughts={showThoughts} setShowThoughts={setShowThoughts} />}
    </div>
  );
}
