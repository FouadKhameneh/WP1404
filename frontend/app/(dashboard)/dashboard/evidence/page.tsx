"use client";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { ErrorDisplay } from "@/features/error/ErrorDisplay";
import { PageLoading } from "@/features/loading/LoadingSpinner";
import { useEffect, useState } from "react";
import Link from "next/link";

type EvidenceLinkItem = { id: number; source_type?: string; target_type?: string };

export default function EvidencePage() {
  const { token } = useAuth();
  const [links, setLinks] = useState<EvidenceLinkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .get<{ results?: EvidenceLinkItem[] }>("/evidence/links/", token)
      .then((res) => {
        if (res.error) setError(res.error.message || "Failed to load evidence links");
        else if (res.data) {
          const list = (res.data as { results?: EvidenceLinkItem[] }).results ?? (Array.isArray(res.data) ? res.data : []);
          setLinks(list);
        }
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (!token) return null;

  if (loading) return <PageLoading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  return (
    <div>
      <h1>Evidence registration & review</h1>
      <p>Evidence links and biological/medical evidence review (coroner decision).</p>
      <nav style={{ marginBottom: "1rem" }}>
        <Link href="/dashboard">Dashboard</Link>
      </nav>
      <h2>Evidence links</h2>
      {links.length === 0 ? (
        <p>No evidence links. Use the API to create links between evidence items.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {links.map((l) => (
            <li key={l.id} style={{ padding: "0.5rem 0", borderBottom: "1px solid #eee" }}>
              Link #{l.id} — {l.source_type ?? "—"} → {l.target_type ?? "—"}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
