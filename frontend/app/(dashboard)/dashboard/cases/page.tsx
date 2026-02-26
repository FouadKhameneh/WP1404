"use client";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { ErrorDisplay } from "@/features/error/ErrorDisplay";
import { PageLoading } from "@/features/loading/LoadingSpinner";
import { useEffect, useState } from "react";

type CaseItem = { id: number; title?: string; case_number?: string; status?: string };

export default function CasesPage() {
  const { token } = useAuth();
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .get<{ results?: CaseItem[] }>("/cases/cases/", token)
      .then((res) => {
        if (res.error) setError(res.error.message || "بارگذاری پرونده‌ها ناموفق بود.");
        else if (res.data) {
          const list = (res.data as { results?: CaseItem[] }).results ?? (Array.isArray(res.data) ? res.data : []);
          setCases(list);
        }
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <PageLoading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  return (
    <div>
      <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.75rem", color: "var(--text)" }}>وضعیت پرونده‌ها</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>لیست پرونده‌های شکایت و صحنه جرم</p>
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {cases.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>پرونده‌ای یافت نشد.</div>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {cases.map((c) => (
              <li key={c.id} className="list-item">
                <span style={{ fontWeight: 500 }}>{c.case_number ?? c.title ?? `پرونده #${c.id}`}</span>
                <span style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>{c.status ?? "—"}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
