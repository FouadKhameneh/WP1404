"use client";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { ErrorDisplay } from "@/features/error/ErrorDisplay";
import { PageLoading } from "@/features/loading/LoadingSpinner";
import { useEffect, useState } from "react";

type ReportData = {
  homepage?: { total_cases?: number; active_cases?: number; closed_cases?: number; staff_count?: number; by_status?: Record<string, number> };
  case_counts?: { total?: number; by_status?: Record<string, number> };
  stage_distribution?: { status: string; count: number }[];
  approvals?: { reasoning_approved?: number; reasoning_rejected?: number; reasoning_pending?: number };
  wanted_rankings?: { wanted_count?: number; most_wanted_count?: number; top_ranked?: { national_id?: string; full_name?: string; ranking_score?: number }[] };
  reward_outcomes?: { tips_approved?: number; tips_rejected?: number; tips_pending?: number };
};

export default function ReportsPage() {
  const { token } = useAuth();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api.get<ReportData>("/reports/general/", token).then((res) => {
      if (res.error) setError(res.error.message || "بارگذاری گزارش ناموفق بود.");
      else if (res.data) setReport(res.data as ReportData);
    }).finally(() => setLoading(false));
  }, [token]);

  if (loading) return <PageLoading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  const h = report?.homepage;
  const a = report?.approvals;
  const w = report?.wanted_rankings;
  const r = report?.reward_outcomes;

  return (
    <div>
      <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.75rem", color: "var(--text)" }}>گزارش کلی</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>آمار تجمیعی و جداول</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <div className="stat-card"><div className="stat-value">{h?.total_cases ?? "—"}</div><div className="stat-label">کل پرونده‌ها</div></div>
        <div className="stat-card"><div className="stat-value">{h?.active_cases ?? "—"}</div><div className="stat-label">پرونده‌های فعال</div></div>
        <div className="stat-card"><div className="stat-value">{h?.closed_cases ?? "—"}</div><div className="stat-label">بسته‌شده</div></div>
        <div className="stat-card"><div className="stat-value">{h?.staff_count ?? "—"}</div><div className="stat-label">پرسنل</div></div>
        <div className="stat-card"><div className="stat-value">{a?.reasoning_pending ?? "—"}</div><div className="stat-label">در انتظار تأیید</div></div>
        <div className="stat-card"><div className="stat-value">{w?.most_wanted_count ?? "—"}</div><div className="stat-label">تحت تعقیب شدید</div></div>
        <div className="stat-card"><div className="stat-value">{r?.tips_pending ?? "—"}</div><div className="stat-label">نکات پاداش در انتظار</div></div>
      </div>

      {report?.stage_distribution && report.stage_distribution.length > 0 && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3>توزیع وضعیت پرونده‌ها</h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead><tr><th style={{ textAlign: "right", padding: "0.5rem" }}>وضعیت</th><th style={{ padding: "0.5rem" }}>تعداد</th></tr></thead>
            <tbody>
              {report.stage_distribution.map((s, i) => (
                <tr key={i}><td style={{ padding: "0.5rem" }}>{s.status}</td><td style={{ padding: "0.5rem" }}>{s.count}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {report?.wanted_rankings?.top_ranked && report.wanted_rankings.top_ranked.length > 0 && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3>رتبه‌بندی تحت تعقیب‌ها</h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead><tr><th style={{ textAlign: "right", padding: "0.5rem" }}>کد ملی</th><th style={{ padding: "0.5rem" }}>نام</th><th style={{ padding: "0.5rem" }}>امتیاز</th></tr></thead>
            <tbody>
              {report.wanted_rankings.top_ranked.map((row, i) => (
                <tr key={i}><td style={{ padding: "0.5rem" }}>{row.national_id}</td><td style={{ padding: "0.5rem" }}>{row.full_name}</td><td style={{ padding: "0.5rem" }}>{row.ranking_score}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="card" style={{ overflow: "auto" }}>
        <h3>خروجی خام JSON</h3>
        <pre style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-muted)", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          {JSON.stringify(report, null, 2)}
        </pre>
      </div>
    </div>
  );
}
