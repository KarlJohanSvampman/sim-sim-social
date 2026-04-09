import React, { useEffect, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";

function Tile({ tile }) {
  return (
    <mesh position={[tile.x, 0, tile.y]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[1, 1]} />
      <meshStandardMaterial color="#9fd08a" />
    </mesh>
  );
}

function Character({ c, showThoughts }) {
  return (
    <group position={[c.position.x, 0.5, c.position.y]}>
      <mesh>
        <boxGeometry args={[0.6, 1.2, 0.6]} />
        <meshStandardMaterial color="#3b82f6" />
      </mesh>
      <Html position={[0, 1.2, 0]} center>
        <div style={{background:"#fff",padding:"4px 6px",borderRadius:6,border:"1px solid #999",fontSize:12,maxWidth:260}}>
          <strong>{c.name}</strong><br/>
          {c.speech ? <span>💬 {c.speech}</span> : (showThoughts ? <span>💭 {c.thoughts}</span> : <span>…</span>)}
          <br/><small>{c.institution_role || "no role"}</small>
        </div>
      </Html>
    </group>
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
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");
    wsRef.current = ws;
    ws.onopen = () => ws.send(JSON.stringify({type:"set_thoughts", enabled: showThoughts}));
    ws.onmessage = (ev) => setWorld(JSON.parse(ev.data));
    return () => ws.close();
  }, []);

  useEffect(() => {
    fetch("http://localhost:8000/timeline")
      .then(r => r.json())
      .then(d => setTimeline(d.events || []));
  }, [world?.tick]);

  useEffect(() => {
    fetch(`http://localhost:8000/timeline/replay/window?cursor_tick=${cursor}&radius=15`)
      .then(r => r.json())
      .then(d => setReplayWindow(d.events || []));
  }, [cursor]);

  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({type:"set_thoughts", enabled: showThoughts}));
    }
  }, [showThoughts]);

  const patchCharacter = async () => {
    const body = {};
    if (patchHealth !== "") body.health = Number(patchHealth);
    if (patchRole !== "") body.institution_role = patchRole;
    await fetch(`http://localhost:8000/operator/character/${selectedId}`, {
      method: "PATCH",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(body)
    });
    setPatchHealth("");
    setPatchRole("");
  };

  return (
    <div style={{display:"grid",gridTemplateColumns:"1fr 540px",height:"100%"}}>
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
        <h2>Phase 10</h2>

        <label style={{display:"block", marginBottom:16}}>
          <input type="checkbox" checked={showThoughts} onChange={(e)=>setShowThoughts(e.target.checked)} />
          {" "}Show thought overlays
        </label>

        <div style={{padding:12,background:"#1f2937",borderRadius:8,marginBottom:16}}>
          <h3>Operator controls</h3>
          <select value={selectedId} onChange={(e)=>setSelectedId(e.target.value)}>
            <option value="npc_1">npc_1</option>
            <option value="npc_2">npc_2</option>
          </select>
          <div style={{marginTop:8}}>
            <input value={patchHealth} onChange={(e)=>setPatchHealth(e.target.value)} placeholder="Set health" style={{width:"100%",padding:8,marginBottom:8}} />
            <input value={patchRole} onChange={(e)=>setPatchRole(e.target.value)} placeholder="Assign institution role" style={{width:"100%",padding:8}} />
            <button onClick={patchCharacter} style={{marginTop:8}}>Patch character</button>
          </div>
        </div>

        {world && (
          <>
            <div style={{padding:12,background:"#1f2937",borderRadius:8,marginBottom:16}}>
              <h3>Relationships</h3>
              <pre style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(world.relationships, null, 2)}</pre>
            </div>

            <div style={{padding:12,background:"#1f2937",borderRadius:8,marginBottom:16}}>
              <h3>Institutions</h3>
              <pre style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(world.institutions, null, 2)}</pre>
            </div>

            <div style={{padding:12,background:"#1f2937",borderRadius:8}}>
              <h3>Replay scrubber</h3>
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
            </div>

            <div style={{padding:12,background:"#1f2937",borderRadius:8,marginTop:16}}>
              <h3>Latest timeline</h3>
              <div style={{maxHeight:220,overflow:"auto"}}>
                {timeline.map((e) => (
                  <div key={e.id} style={{padding:"6px 0",borderBottom:"1px solid #374151"}}>
                    <div>tick {e.tick} · {e.kind}</div>
                    <pre style={{whiteSpace:"pre-wrap",fontSize:12}}>{JSON.stringify(e.payload, null, 2)}</pre>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
