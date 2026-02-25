"use client";

import { useAuth } from "@/context/AuthContext";
import { useState, useCallback } from "react";
import Link from "next/link";

type BoardItem = { id: string; title: string; x: number; y: number };

export default function DetectiveBoardPage() {
  const { token, user } = useAuth();
  const [items, setItems] = useState<BoardItem[]>([
    { id: "1", title: "Case A", x: 20, y: 20 },
    { id: "2", title: "Evidence 1", x: 120, y: 80 },
    { id: "3", title: "Suspect X", x: 220, y: 20 },
  ]);
  const [dragging, setDragging] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [linked, setLinked] = useState<[string, string][]>([]);
  const [exporting, setExporting] = useState(false);

  const handleDragStart = useCallback((e: React.DragEvent, id: string) => {
    setDragging(id);
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    setDragOffset({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    e.dataTransfer.setData("text/plain", id);
    e.dataTransfer.effectAllowed = "move";
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent, targetId: string) => {
      e.preventDefault();
      const sourceId = e.dataTransfer.getData("text/plain");
      if (sourceId && sourceId !== targetId) {
        const pair: [string, string] = [sourceId, targetId].sort() as [string, string];
        setLinked((prev) =>
          prev.some(([a, b]) => a === pair[0] && b === pair[1])
            ? prev
            : [...prev, pair]
        );
      }
      setDragging(null);
    },
    []
  );

  const handleDragEnd = useCallback(() => {
    setDragging(null);
  }, []);

  const handleBoardMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!dragging) return;
      const board = e.currentTarget.getBoundingClientRect();
      setItems((prev) =>
        prev.map((it) =>
          it.id === dragging
            ? {
                ...it,
                x: Math.max(0, e.clientX - board.left - dragOffset.x),
                y: Math.max(0, e.clientY - board.top - dragOffset.y),
              }
            : it
        )
      );
    },
    [dragging, dragOffset]
  );

  const handleBoardMouseUp = useCallback(() => {
    setDragging(null);
  }, []);

  const exportAsImage = useCallback(() => {
    setExporting(true);
    const board = document.getElementById("detective-board");
    if (!board) {
      setExporting(false);
      return;
    }
    import("html-to-image").then(({ toPng }) => {
      toPng(board, { backgroundColor: "#fff" })
        .then((dataUrl) => {
          const a = document.createElement("a");
          a.href = dataUrl;
          a.download = "detective-board.png";
          a.click();
        })
        .catch(() => {})
        .finally(() => setExporting(false));
    }).catch(() => setExporting(false));
  }, []);

  if (!token) return null;

  return (
    <div>
      <h1>Detective board</h1>
      <p>Drag items to reposition; drop one on another to link. Export as image (requires html-to-image).</p>
      <nav style={{ marginBottom: "1rem" }}>
        <Link href="/dashboard">Dashboard</Link>
      </nav>
      <div style={{ marginBottom: "1rem" }}>
        <button
          type="button"
          onClick={exportAsImage}
          disabled={exporting}
          style={{ padding: "0.5rem 1rem" }}
        >
          {exporting ? "Exporting..." : "Export as PNG"}
        </button>
      </div>
      <div
        id="detective-board"
        style={{
          position: "relative",
          width: 600,
          height: 400,
          border: "2px solid #ccc",
          background: "#fafafa",
          marginBottom: "1rem",
        }}
        onMouseMove={handleBoardMouseMove}
        onMouseLeave={handleBoardMouseUp}
        onMouseUp={handleBoardMouseUp}
      >
        {items.map((it) => (
          <div
            key={it.id}
            draggable
            onDragStart={(e) => handleDragStart(e, it.id)}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, it.id)}
            onDragEnd={handleDragEnd}
            style={{
              position: "absolute",
              left: it.x,
              top: it.y,
              padding: "8px 12px",
              background: dragging === it.id ? "#dbeafe" : "#e5e7eb",
              border: "1px solid #9ca3af",
              borderRadius: 6,
              cursor: "grab",
              userSelect: "none",
            }}
          >
            {it.title}
          </div>
        ))}
        {linked.map(([a, b], i) => {
          const itemA = items.find((it) => it.id === a);
          const itemB = items.find((it) => it.id === b);
          if (!itemA || !itemB) return null;
          return (
            <svg
              key={`${a}-${b}-${i}`}
              style={{ position: "absolute", inset: 0, pointerEvents: "none", overflow: "visible" }}
            >
              <line
                x1={itemA.x + 50}
                y1={itemA.y + 20}
                x2={itemB.x + 50}
                y2={itemB.y + 20}
                stroke="#6b7280"
                strokeWidth={2}
              />
            </svg>
          );
        })}
      </div>
      <p>Linked pairs: {linked.length}</p>
    </div>
  );
}
