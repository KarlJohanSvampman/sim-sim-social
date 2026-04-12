import React, { useEffect, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html, Line } from "@react-three/drei";
import TopNav from "./components/TopNav";
import RightToolbar from "./components/RightToolbar";
import ObjectManager from "./pages/ObjectManager";
import ItemManager from "./pages/ItemManager";
import TileTypeManager from "./pages/TileTypeManager";
import DebugPage from "./pages/DebugPage";

function Tile({ tile, selected, onSelect }) {
  const color = tile.tile_type === "wall" ? "#4b5563" : selected ? "#f59e0b" : "#9ca3af";
  const h = tile.tile_type === "wall" ? 1.2 : 0.08;
  return (
    <group position={[tile.x, 0, tile.y]}>
      <mesh position={[0, h / 2, 0]} onClick={(e) => { e.stopPropagation(); onSelect(tile); }}>
        <boxGeometry args={[0.96, h, 0.96]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {tile.object && (
        <mesh position={[0, 0.35, 0]}>
          <boxGeometry args={[0.4, 0.4, 0.4]} />
          <meshStandardMaterial color="#f59e0b" />
        </mesh>
      )}
    </group>
  );
}

function Character({ c }) {
  const app = c.appearance_summary || {};
  return (
    <group position={[c.position.x, 0.65, c.position.y]}>
      <mesh>
        <capsuleGeometry args={[0.22, 0.8, 4, 8]} />
        <meshStandardMaterial color="#2563eb" />
      </mesh>
      <Html position={[0, 1.0, 0]} center>
        <div style={{ background: "#fff", padding: "4px 6px", borderRadius: 6, border: "1px solid #999", fontSize: 12, maxWidth: 220 }}>
          <strong>{c.name}</strong><br />
          <span>💭 {c.thoughts}</span><br />
          <small>{app.age ?? "?"} · {app.sex || "unknown"} · {app.body_type || "?"}</small>
        </div>
      </Html>
    </group>
  );
}

function GridAxes({ size }) {
  return (
    <>
      <Line points={[[0, 0.02, 0], [size, 0.02, 0]]} color="#ef4444" lineWidth={2} />
      <Line points={[[0, 0.02, 0], [0, 0.02, size]]} color="#3b82f6" lineWidth={2} />
    </>
  );
}

function TileOverlay({ tile }) {
  if (!tile) return null;
  return (
    <div style={{ position: "absolute", top: 14, right: 70, width: 280, background: "rgba(17,24,39,0.96)", color: "#fff", border: "1px solid #374151", borderRadius: 10, padding: 12, zIndex: 20 }}>
      <div style={{ fontWeight: 700, marginBottom: 8 }}>Selected Tile</div>
      <div>x: {tile.x}</div>
      <div>y: {tile.y}</div>
      <div>type: {tile.tile_type}</div>
      <div>elevation: {tile.elevation}</div>
      <div>object: {tile.object?.name || "none"}</div>
      <div>items: {tile.items?.length || 0}</div>
    </div>
  );
}

function MapPage() {
  const [world, setWorld] = useState(null);
  const [selectedTile, setSelectedTile] = useState(null);
  const controlsRef = useRef(null);

  useEffect(() => {
    fetch("http://localhost:8000/world").then(r => r.json()).then(setWorld).catch(() => {});
    const ws = new WebSocket("ws://localhost:8000/ws");
    ws.onmessage = (ev) => setWorld(JSON.parse(ev.data));
    return () => ws.close();
  }, []);

  useEffect(() => {
    const onContext = (e) => {
      e.preventDefault();
      setSelectedTile(null);
    };
    window.addEventListener("contextmenu", onContext);
    return () => window.removeEventListener("contextmenu", onContext);
  }, []);

  const zoomIn = () => {
    if (!controlsRef.current) return;
    controlsRef.current.object.position.y = Math.max(6, controlsRef.current.object.position.y - 2);
    controlsRef.current.object.position.z = Math.max(6, controlsRef.current.object.position.z - 2);
    controlsRef.current.update();
  };
  const zoomOut = () => {
    if (!controlsRef.current) return;
    controlsRef.current.object.position.y += 2;
    controlsRef.current.object.position.z += 2;
    controlsRef.current.update();
  };
  const rotateAround = (dir) => {
    if (!controlsRef.current) return;
    const camera = controlsRef.current.object;
    const target = controlsRef.current.target;
    const dx = camera.position.x - target.x;
    const dz = camera.position.z - target.z;
    const angle = dir * (Math.PI / 12);
    const nx = dx * Math.cos(angle) - dz * Math.sin(angle);
    const nz = dx * Math.sin(angle) + dz * Math.cos(angle);
    camera.position.x = target.x + nx;
    camera.position.z = target.z + nz;
    controlsRef.current.update();
  };

  if (!world) return <div style={{padding:20, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>Loading map…</div>;

  return (
    <div style={{ height: "calc(100vh - 56px)", display: "grid", gridTemplateColumns: "1fr 320px" }}>
      <div style={{ position: "relative" }}>
        <RightToolbar zoomIn={zoomIn} zoomOut={zoomOut} rotateLeft={() => rotateAround(-1)} rotateRight={() => rotateAround(1)} />
        <TileOverlay tile={selectedTile} />
        <Canvas camera={{ position: [18, 24, 18], fov: 50 }} onPointerMissed={(e) => { if (e.type === "click") setSelectedTile(null); }}>
          <color attach="background" args={["#0f172a"]} />
          <ambientLight intensity={0.9} />
          <directionalLight position={[10, 16, 8]} intensity={1.2} />
          <OrbitControls ref={controlsRef} enableRotate={false} enablePan={true} enableZoom={true} />
          <GridAxes size={32} />
          {Object.values(world.grid.tiles).map((t) => <Tile key={t.x + "-" + t.y} tile={t} selected={selectedTile && selectedTile.x === t.x && selectedTile.y === t.y} onSelect={setSelectedTile} />)}
          {Object.values(world.characters || {}).map((c) => <Character key={c.id} c={c} />)}
        </Canvas>
      </div>
      <div style={{ background: "#111827", color: "#fff", padding: 16, overflow: "auto" }}>
        <h2>Live Simulation</h2>
        <div>Tick: {world.tick || 0}</div>
        <h3>Characters</h3>
        {Object.values(world.characters || {}).map((c) => (
          <div key={c.id} style={{ padding: "10px 0", borderBottom: "1px solid #374151" }}>
            <div><strong>{c.name}</strong></div>
            <div>Pos: {c.position.x}, {c.position.y}</div>
            <div>Thoughts: {c.thoughts}</div>
            <div>Last action: {c.last_action?.type}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState("map");
  return (
    <div style={{height:"100vh", display:"flex", flexDirection:"column"}}>
      <TopNav page={page} setPage={setPage} />
      {page === "map" && <MapPage />}
      {page === "creator" && <div style={{padding:16, color:"#fff", background:"#111", minHeight:"calc(100vh - 56px)"}}>Use the existing character creator from the base repo or continue extending it here.</div>}
      {page === "objects" && <ObjectManager />}
      {page === "items" && <ItemManager />}
      {page === "tiletypes" && <TileTypeManager />}
      {page === "debug" && <DebugPage />}
    </div>
  );
}
