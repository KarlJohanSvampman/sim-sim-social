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

// rest unchanged until renderPage

export default function App() {
  const [page, setPage] = useState("map");

  const renderPage = () => {
    switch (page) {
      case "map":
        return <MapPage />;
      case "tagged":
        return <TaggedProfileEditor />;
      case "objects":
        return <ObjectManager />;
      case "items":
        return <ItemManager />;
      case "actions":
        return <ActionManager />;
      case "activities":
        return <ActivityManager />;
      case "tiletypes":
        return <TileTypeManager />;
      case "debug":
        return <DebugPage />;
      case "llm_inspector":
        return <LLMInspector />;
      case "config":
        return <ConfigPage />;
      default:
        return <MapPage />;
    }
  };

  return (
    <div style={{height:"100vh", display:"flex", flexDirection:"column"}}>
      <TopNav page={page} setPage={setPage} />
      <ErrorBoundary resetKey={page}>
        {renderPage()}
      </ErrorBoundary>
    </div>
  );
}
