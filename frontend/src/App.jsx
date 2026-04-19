import React, { useEffect, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html, Line } from "@react-three/drei";
import TopNav from "./components/TopNav";
import RightToolbar from "./components/RightToolbar";
import ObjectManager from "./pages/ObjectManager";
import ItemManager from "./pages/ItemManager";
import ActionManager from "./pages/ActionManager";
import ActivityManager from "./pages/ActivityManager";
import TileTypeManager from "./pages/TileTypeManager";
import DebugPage from "./pages/DebugPage";
import TaggedProfileEditor from "./pages/TaggedProfileEditor";
import LLMInspector from "./pages/LLMInspector";
import ConfigPage from "./pages/ConfigPage";

function Character({ c, onSelect }) {
  const facing = c.state?.facing || { x: 0, y: 1 };
  const angle = Math.atan2(facing.x, facing.y);

  return (
    <group rotation={[0, angle, 0]} position={[c.position.x, 0.65, c.position.y]}>
      <mesh>
        <capsuleGeometry args={[0.22, 0.8, 4, 8]} />
        <meshStandardMaterial color="#2563eb" />
      </mesh>
      <mesh position={[0, 0.2, 0.3]}>
        <coneGeometry args={[0.08, 0.2, 6]} />
        <meshStandardMaterial color="#f59e0b" />
      </mesh>
      <Html position={[0, 1.0, 0]} center>
        <div style={{ background: "#fff", padding: "4px 6px", borderRadius: 6, border: "1px solid #999", fontSize: 12 }}>
          <strong>{c.name}</strong><br />
          {c.spoken_text && <div>🗨️ {c.spoken_text}</div>}
        </div>
      </Html>
    </group>
  );
}

export default Character
