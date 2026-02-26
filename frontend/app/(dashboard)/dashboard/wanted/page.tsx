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
        if (res.error) setError(res.error.message || "بارگذاری لیست ناموفق بود.");
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
      <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.75rem", color: "var(--text)" }}>تحت تعقیب / بسیار تحت تعقیب</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>لیست افراد تحت تعقیب و بسیار تحت تعقیب</p>
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {items.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>موردی یافت نشد.</div>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {items.map((w) => (
              <li key={w.id} className="list-item">
                <span style={{ fontWeight: 500 }}>#{w.id}</span>
                <span style={{ fontSize: "0.9rem", color: "var(--accent)" }}>{w.status ?? "—"}</span>
                <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>{w.case_reference ?? ""}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
