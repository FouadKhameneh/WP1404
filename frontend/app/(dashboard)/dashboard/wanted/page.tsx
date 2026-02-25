"use client";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { ErrorDisplay } from "@/features/error/ErrorDisplay";
import { PageLoading } from "@/features/loading/LoadingSpinner";
import { useEffect, useState } from "react";

type WantedItem = { id: number; status?: string; case_reference?: string };

export default function WantedPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<WantedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .get<{ results?: WantedItem[] }>("/wanted/?status=most_wanted", token)
      .then((res) => {
        if (res.error) setError(res.error.message || "Failed to load wanted");
        else if (res.data) {
          const list = (res.data as { results?: WantedItem[] }).results ?? (Array.isArray(res.data) ? res.data : []);
          setItems(list);
        }
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <PageLoading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  return (
    <div>
      <h1>Most wanted</h1>
      <p>Wanted and most-wanted list.</p>
      {items.length === 0 ? (
        <p>No entries.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {items.map((w) => (
            <li key={w.id} style={{ padding: "0.5rem 0", borderBottom: "1px solid #eee" }}>
              #{w.id} — {w.status ?? "—"} {w.case_reference ?? ""}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
