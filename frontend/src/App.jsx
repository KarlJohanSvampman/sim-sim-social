import React, { useEffect, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";

function Tile({ tile }) {
  let color = "#9fd08a";
  if (tile.type.startsWith("wall")) color = "#666";
  return <mesh position={[tile.x,0,tile.y]} rotation={[-Math.PI/2,0,0]}><planeGeometry args={[1,1]} /><meshStandardMaterial color={color} /></mesh>;
}
function Character({ c, showThoughts }) {
  const bodyColor = c.is_unconscious ? "#111827" : "#3b82f6";
  return (
    <group position={[c.position.x,0.5,c.position.y]}>
      <mesh><boxGeometry args={[0.6,1.2,0.6]} /><meshStandardMaterial color={bodyColor} /></mesh>
      <Html position={[0,1.2,0]} center>
        <div style={{background:"#fff",padding:"4px 6px",borderRadius:6,border:"1px solid #999",fontSize:12,maxWidth:280}}>
          <strong>{c.name}</strong><br/>
          {c.speech ? <span>💬 {c.speech}</span> : (showThoughts ? <span>💭 {c.thoughts}</span> : <span>…</span>)}
          <br/><small>HP: {c.health} Smoke: {c.smoke_inhalation} Unconscious: {String(c.is_unconscious)}</small>
        </div>
      </Html>
    </group>
  );
}

export default function App() {
  const [world, setWorld] = useState(null);
  const [showThoughts, setShowThoughts] = useState(true);
  const [selectedId, setSelectedId] = useState("npc_1");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [patchHealth, setPatchHealth] = useState("");
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");
    wsRef.current = ws;
    ws.onopen = () => ws.send(JSON.stringify({type:"set_thoughts", enabled: showThoughts}));
    ws.onmessage = (ev) => setWorld(JSON.parse(ev.data));
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({type:"set_thoughts", enabled: showThoughts}));
    }
  }, [showThoughts]);

  const askCharacter = async () => {
    const res = await fetch(`http://localhost:8000/operator/ask/${selectedId}`, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({question})
    });
    setAnswer(await res.json());
  };

  const patchCharacter = async () => {
    const body = {};
    if (patchHealth !== "") body.health = Number(patchHealth);
    await fetch(`http://localhost:8000/operator/character/${selectedId}`, {
      method:"PATCH",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify(body)
    });
    setPatchHealth("");
  };

  return (
    <div style={{display:"grid",gridTemplateColumns:"1fr 460px",height:"100%"}}>
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
        <h2>Phase 8</h2>
        <label style={{display:"block", marginBottom:16}}>
          <input type="checkbox" checked={showThoughts} onChange={(e)=>setShowThoughts(e.target.checked)} /> Show thought overlays
        </label>

        <div style={{padding:12, background:"#1f2937", borderRadius:8}}>
          <h3>Operator controls</h3>
          <select value={selectedId} onChange={(e)=>setSelectedId(e.target.value)}>
            <option value="npc_1">npc_1</option>
            <option value="npc_2">npc_2</option>
          </select>

          <div style={{marginTop:12}}>
            <input value={question} onChange={(e)=>setQuestion(e.target.value)} placeholder="Ask about the past..." style={{width:"100%", padding:8}} />
            <button onClick={askCharacter} style={{marginTop:8}}>Ask character</button>
            {answer && <pre style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(answer, null, 2)}</pre>}
          </div>

          <div style={{marginTop:12}}>
            <input value={patchHealth} onChange={(e)=>setPatchHealth(e.target.value)} placeholder="Set health" style={{width:"100%", padding:8}} />
            <button onClick={patchCharacter} style={{marginTop:8}}>Patch character</button>
          </div>
        </div>

        {!world && <p>Connecting…</p>}
        {world && Object.values(world.characters).map((c) => (
          <div key={c.id} style={{marginTop:16,padding:12,background:"#1f2937",borderRadius:8}}>
            <div><strong>{c.name}</strong> ({c.id})</div>
            <div>Goal: {c.goal?.type}</div>
            <div>Planned steps: {(c.plan || []).map((p,i)=><span key={i}>{p.action}{i < c.plan.length-1 ? " → " : ""}</span>)}</div>
            <div>Speech: {c.speech || "-"}</div>
            <div>Conversation: {c.conversation_id || "-"}</div>
            <div>Needs: {JSON.stringify(c.needs)}</div>
            <div>Inventory: {JSON.stringify(c.inventory)}</div>
            <div>Intoxication: {c.intoxication}</div>
            <div>Addiction: {JSON.stringify(c.addiction)}</div>
            <div>Cravings: {JSON.stringify(c.cravings)}</div>
            <div>Withdrawal: {JSON.stringify(c.withdrawal)}</div>
            <div>Health: {c.health}</div>
            <div>Unconscious: {String(c.is_unconscious)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
