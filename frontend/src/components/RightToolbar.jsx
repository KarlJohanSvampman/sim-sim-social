import React from "react";

export default function RightToolbar({ zoomIn, zoomOut, rotateLeft, rotateRight }) {
  const style = {
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
    <div style={{ position: "absolute", right: 14, top: 14, display: "flex", flexDirection: "column", gap: 8, zIndex: 20 }}>
      <button style={style} onClick={zoomIn} title="Zoom in">+</button>
      <button style={style} onClick={zoomOut} title="Zoom out">−</button>
      <button style={style} onClick={rotateLeft} title="Rotate left">↶</button>
      <button style={style} onClick={rotateRight} title="Rotate right">↷</button>
    </div>
  );
}
