"use client";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { ErrorDisplay } from "@/features/error/ErrorDisplay";
import { PageLoading } from "@/features/loading/LoadingSpinner";
import { useEffect, useState } from "react";
import Link from "next/link";

type HomeStats = {
  total_cases?: number;
  active_cases?: number;
  [key: string]: unknown;
};

export default function DashboardPage() {
  const { token } = useAuth();
  const [stats, setStats] = useState<HomeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .get<HomeStats>("/reports/homepage/", token)
      .then((res) => {
        if (res.error) setError(res.error.message || "Failed to load stats");
        else if (res.data) setStats(res.data);
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <PageLoading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  return (
    <div>
      <h1>Dashboard</h1>
      <section style={{ marginTop: "1.5rem" }}>
        <h2>Homepage stats</h2>
        <ul style={{ listStyle: "none", padding: 0 }}>
          <li>Total cases: {stats?.total_cases ?? "—"}</li>
          <li>Active cases: {stats?.active_cases ?? "—"}</li>
        </ul>
      </section>
      <nav style={{ marginTop: "1.5rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/dashboard/cases">Case status</Link>
        <Link href="/dashboard/reports">General reporting</Link>
        <Link href="/dashboard/wanted">Most wanted</Link>
      </nav>
    </div>
  );
}
