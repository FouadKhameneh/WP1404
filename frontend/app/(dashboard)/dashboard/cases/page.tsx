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
      .get<{ results?: CaseItem[] }>("/cases/", token)
      .then((res) => {
        if (res.error) setError(res.error.message || "Failed to load cases");
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
      <h1>Case status</h1>
      <p>List of cases (complaint and scene-based).</p>
      {cases.length === 0 ? (
        <p>No cases found.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {cases.map((c) => (
            <li key={c.id} style={{ padding: "0.5rem 0", borderBottom: "1px solid #eee" }}>
              {c.case_number ?? c.title ?? `Case #${c.id}`} — {c.status ?? "—"}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
