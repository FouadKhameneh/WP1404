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
        if (res.error) setError(res.error.message || "بارگذاری لینک‌های مدارک ناموفق بود.");
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
      <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.75rem", color: "var(--text)" }}>ثبت و بررسی مدارک</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
        لینک مدارک و بررسی پزشکی‌قانونی (تصمیم کورونر)
      </p>
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {links.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
            لینک مدرکی وجود ندارد. از API برای ایجاد لینک بین آیتم‌ها استفاده کنید.
          </div>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {links.map((l) => (
              <li key={l.id} className="list-item">
                <span>لینک #{l.id}</span>
                <span style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>
                  {l.source_type ?? "—"} → {l.target_type ?? "—"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <p style={{ marginTop: "1rem" }}>
        <Link href="/dashboard">بازگشت به داشبورد</Link>
      </p>
    </div>
  );
}
