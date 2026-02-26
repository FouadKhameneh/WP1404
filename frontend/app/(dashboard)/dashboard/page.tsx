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
  closed_cases?: number;
  staff_count?: number;
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
        if (res.error) setError(res.error.message || "بارگذاری آمار ناموفق بود.");
        else if (res.data) setStats(res.data);
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <PageLoading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  return (
    <div>
      <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.75rem", color: "var(--text)" }}>داشبورد</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>خلاصه آمار و دسترسی سریع</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <div className="stat-card">
          <div className="stat-value">{stats?.total_cases ?? "—"}</div>
          <div className="stat-label">کل پرونده‌ها</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.active_cases ?? "—"}</div>
          <div className="stat-label">پرونده‌های فعال</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.closed_cases ?? "—"}</div>
          <div className="stat-label">بسته‌شده</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.staff_count ?? "—"}</div>
          <div className="stat-label">پرسنل فعال</div>
        </div>
      </div>
      <section className="card">
        <h2 className="card-title">دسترسی سریع</h2>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <Link href="/dashboard/cases" className="btn btn-secondary">وضعیت پرونده‌ها</Link>
          <Link href="/dashboard/reports" className="btn btn-secondary">گزارش کلی</Link>
          <Link href="/dashboard/wanted" className="btn btn-secondary">تحت تعقیب</Link>
          <Link href="/dashboard/detective" className="btn btn-secondary">بورد کارآگاه</Link>
          <Link href="/dashboard/evidence" className="btn btn-secondary">مدارک</Link>
        </div>
      </section>
    </div>
  );
}
