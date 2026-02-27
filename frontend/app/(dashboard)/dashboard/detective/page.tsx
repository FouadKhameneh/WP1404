"use client";

import { useAuth } from "@/context/AuthContext";
import { useState, useCallback, useRef } from "react";

type BoardItem = { id: string; title: string; x: number; y: number };
type LinkPair = [string, string];

const CARD_WIDTH = 150;
const CARD_HEIGHT = 56;

export default function DetectiveBoardPage() {
  const { token } = useAuth();

  const [items, setItems] = useState<BoardItem[]>([
    { id: "1", title: "پرونده اصلی", x: 40, y: 40 },
    { id: "2", title: "شکایت اولیه", x: 260, y: 60 },
    { id: "3", title: "مظنون X", x: 140, y: 180 },
  ]);
  const [links, setLinks] = useState<LinkPair[]>([]);

  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const boardRef = useRef<HTMLDivElement | null>(null);

  const [linkMode, setLinkMode] = useState(false);
  const [linkSourceId, setLinkSourceId] = useState<string | null>(null);

  const [newTitle, setNewTitle] = useState("");
  const [exporting, setExporting] = useState(false);

  const handleItemMouseDown = useCallback(
    (e: React.MouseEvent<HTMLDivElement>, id: string) => {
      if (linkMode) return;
      e.preventDefault();
      const boardRect = boardRef.current?.getBoundingClientRect();
      const itemRect = (e.currentTarget as HTMLElement).getBoundingClientRect();
      if (!boardRect) return;
      setDraggingId(id);
      setDragOffset({
        x: e.clientX - itemRect.left,
        y: e.clientY - itemRect.top,
      });
    },
    [linkMode]
  );

  const handleBoardMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!draggingId) return;
      const boardRect = boardRef.current?.getBoundingClientRect();
      if (!boardRect) return;

      const rawX = e.clientX - boardRect.left - dragOffset.x;
      const rawY = e.clientY - boardRect.top - dragOffset.y;

      const x = Math.max(0, Math.min(boardRect.width - CARD_WIDTH, rawX));
      const y = Math.max(0, Math.min(boardRect.height - CARD_HEIGHT, rawY));

      setItems((prev) =>
        prev.map((it) => (it.id === draggingId ? { ...it, x, y } : it))
      );
    },
    [draggingId, dragOffset]
  );

  const stopDragging = useCallback(() => {
    setDraggingId(null);
  }, []);

  const toggleLinkMode = useCallback(() => {
    setLinkMode((prev) => !prev);
    setLinkSourceId(null);
  }, []);

  const handleItemClick = useCallback(
    (id: string) => {
      if (!linkMode) return;
      if (!linkSourceId) {
        setLinkSourceId(id);
        return;
      }
      if (linkSourceId === id) {
        setLinkSourceId(null);
        return;
      }
      const pair: LinkPair = [linkSourceId, id].sort() as LinkPair;
      setLinks((prev) =>
        prev.some(([a, b]) => a === pair[0] && b === pair[1]) ? prev : [...prev, pair]
      );
      setLinkSourceId(null);
    },
    [linkMode, linkSourceId]
  );

  const handleAddItem = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const title = newTitle.trim();
      if (!title) return;
      setItems((prev) => [
        ...prev,
        {
          id: String(Date.now()),
          title,
          x: 40 + ((prev.length * 60) % 360),
          y: 40 + ((prev.length * 80) % 240),
        },
      ]);
      setNewTitle("");
    },
    [newTitle]
  );

  const clearLinks = useCallback(() => setLinks([]), []);

  const exportAsImage = useCallback(() => {
    setExporting(true);
    const board = document.getElementById("detective-board");
    if (!board) {
      setExporting(false);
      return;
    }
    import("html-to-image")
      .then(({ toPng }) => {
        toPng(board, { backgroundColor: "#fff" })
          .then((dataUrl) => {
            const a = document.createElement("a");
            a.href = dataUrl;
            a.download = "detective-board.png";
            a.click();
          })
          .catch(() => {})
          .finally(() => setExporting(false));
      })
      .catch(() => setExporting(false));
  }, []);

  if (!token) return null;

  return (
    <div>
      <h1
        style={{
          margin: "0 0 0.5rem 0",
          fontSize: "1.75rem",
          color: "var(--text)",
        }}
      >
        بورد کارآگاه
      </h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>
        آیتم‌ها را با ماوس بکشید و رها کنید، آیتم جدید اضافه کنید و در حالت اتصال، بین آن‌ها لینک تصویری بسازید.
      </p>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.5rem",
          marginBottom: "1rem",
        }}
      >
        <button
          type="button"
          className="btn btn-primary"
          onClick={exportAsImage}
          disabled={exporting}
        >
          {exporting ? "در حال خروجی..." : "خروجی PNG"}
        </button>
        <button
          type="button"
          className={linkMode ? "btn btn-secondary" : "btn btn-outline-secondary"}
          onClick={toggleLinkMode}
        >
          {linkMode ? "خروج از حالت اتصال" : "حالت اتصال آیتم‌ها"}
        </button>
        <button
          type="button"
          className="btn btn-outline-secondary"
          onClick={clearLinks}
          disabled={!links.length}
        >
          پاک کردن همه اتصال‌ها
        </button>
      </div>

      <form
        onSubmit={handleAddItem}
        style={{
          display: "flex",
          gap: "0.5rem",
          marginBottom: "1rem",
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <input
          type="text"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="عنوان آیتم جدید (مثلاً مظنون جدید، شاهد، مدرک)"
          style={{
            flex: "1 1 200px",
            minWidth: 0,
            padding: "0.4rem 0.6rem",
            borderRadius: "var(--radius)",
            border: "1px solid var(--border)",
            background: "var(--bg-card)",
            color: "var(--text)",
          }}
        />
        <button type="submit" className="btn btn-outline-primary">
          افزودن آیتم
        </button>
      </form>

      <div
        id="detective-board"
        ref={boardRef}
        style={{
          position: "relative",
          width: "100%",
          maxWidth: 700,
          height: 420,
          border: "2px solid var(--border)",
          backgroundImage:
            "radial-gradient(circle at 1px 1px, rgba(148, 163, 184, 0.3) 1px, transparent 0)",
          backgroundSize: "20px 20px",
          backgroundColor: "var(--bg-card)",
          marginBottom: "1rem",
          borderRadius: "var(--radius)",
          overflow: "hidden",
        }}
        onMouseMove={handleBoardMouseMove}
        onMouseUp={stopDragging}
        onMouseLeave={stopDragging}
      >
        {links.map(([a, b], i) => {
          const itemA = items.find((it) => it.id === a);
          const itemB = items.find((it) => it.id === b);
          if (!itemA || !itemB) return null;
          const x1 = itemA.x + CARD_WIDTH / 2;
          const y1 = itemA.y + CARD_HEIGHT / 2;
          const x2 = itemB.x + CARD_WIDTH / 2;
          const y2 = itemB.y + CARD_HEIGHT / 2;
          return (
            <svg
              key={`${a}-${b}-${i}`}
              style={{
                position: "absolute",
                inset: 0,
                pointerEvents: "none",
                overflow: "visible",
              }}
            >
              <defs>
                <marker
                  id={`arrow-${i}`}
                  markerWidth="8"
                  markerHeight="8"
                  refX="4"
                  refY="4"
                  orient="auto-start-reverse"
                >
                  <path d="M0,0 L8,4 L0,8 z" fill="#6b7280" />
                </marker>
              </defs>
              <line
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#6b7280"
                strokeWidth={2}
                markerEnd={`url(#arrow-${i})`}
              />
            </svg>
          );
        })}

        {items.map((it) => {
          const isDragging = draggingId === it.id;
          const isSource = linkMode && linkSourceId === it.id;
          return (
            <div
              key={it.id}
              onMouseDown={(e) => handleItemMouseDown(e, it.id)}
              onClick={() => handleItemClick(it.id)}
              style={{
                position: "absolute",
                left: it.x,
                top: it.y,
                width: CARD_WIDTH,
                minHeight: CARD_HEIGHT,
                padding: "8px 12px",
                background: "var(--bg-elevated)",
                color: "var(--text)",
                borderRadius: "var(--radius)",
                boxShadow: isSource
                  ? "0 0 0 2px var(--accent)"
                  : "0 0 0 1px var(--border)",
                cursor: linkMode
                  ? "pointer"
                  : isDragging
                  ? "grabbing"
                  : "grab",
                userSelect: "none",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                textAlign: "center",
                fontSize: "0.9rem",
                fontWeight: 500,
                backdropFilter: "blur(2px)",
              }}
            >
              {it.title}
            </div>
          );
        })}
      </div>

      <p style={{ color: "var(--text-muted)" }}>
        تعداد آیتم‌ها: {items.length} — تعداد اتصال‌ها: {links.length}
      </p>
      <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
        نکته: برای جابجایی، فقط ماوس را روی کارت پایین نگه دارید و بکشید. برای اتصال،
        دکمه حالت اتصال را فعال کنید و دو کارت را به ترتیب کلیک کنید.
      </p>
    </div>
  );
}
