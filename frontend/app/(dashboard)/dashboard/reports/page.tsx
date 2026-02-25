"use client";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { ErrorDisplay } from "@/features/error/ErrorDisplay";
import { PageLoading } from "@/features/loading/LoadingSpinner";
import { useEffect, useState } from "react";

type GeneralReport = Record<string, unknown>;

export default function ReportsPage() {
  const { token } = useAuth();
  const [report, setReport] = useState<GeneralReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .get<GeneralReport>("/reports/general/", token)
      .then((res) => {
        if (res.error) setError(res.error.message || "Failed to load report");
        else if (res.data) setReport(res.data as GeneralReport);
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <PageLoading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  return (
    <div>
      <h1>General reporting</h1>
      <p>Aggregated statistics: homepage, case counts, approvals, wanted rankings, reward outcomes.</p>
      <pre style={{ background: "#f5f5f5", padding: "1rem", overflow: "auto" }}>
        {JSON.stringify(report, null, 2)}
      </pre>
    </div>
  );
}
