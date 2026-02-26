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
        if (res.error) setError(res.error.message || "بارگذاری گزارش ناموفق بود.");
        else if (res.data) setReport(res.data as GeneralReport);
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <PageLoading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  return (
    <div>
      <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.75rem", color: "var(--text)" }}>گزارش کلی</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
        آمار تجمیعی: داشبورد، تعداد پرونده، تأییدها، تحت تعقیب، جوایز
      </p>
      <div className="card" style={{ overflow: "auto" }}>
        <pre style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-muted)", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          {JSON.stringify(report, null, 2)}
        </pre>
      </div>
    </div>
  );
}
