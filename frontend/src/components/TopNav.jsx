import React from "react";

export default function TopNav({ page, setPage }) {
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
      {btn("tagged", "Profiles")}
      {btn("objects", "Objects")}
      {btn("items", "Items")}
      {btn("tiletypes", "Tile Types")}
      {btn("debug", "Debug")}
    </div>
  );
}
