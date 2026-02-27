"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type LandingStats = {
  closed_cases?: number;
  staff_count?: number;
  active_cases?: number;
};

export default function HomePage() {
  const [stats, setStats] = useState<LandingStats | null>(null);
  useEffect(() => {
    api.get<LandingStats>("/reports/landing-stats/").then((res) => {
      if (res.data) setStats(res.data);
    });
  }, []);

  return (
    <main className="hero-bg" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", padding: "2rem" }}>
      <div style={{ textAlign: "center", maxWidth: 640 }}>
        <div style={{ marginBottom: "0.5rem", fontSize: "0.9rem", color: "var(--text-muted)", letterSpacing: "0.15em", textTransform: "uppercase" }}>
          سامانه یکپارچه
        </div>
        <h1 style={{ fontSize: "clamp(1.75rem, 4vw, 2.5rem)", fontWeight: 700, margin: "0 0 0.5rem 0", color: "var(--text)", letterSpacing: "-0.02em" }}>
          Police Digital Operations
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "1.1rem", marginBottom: "1.5rem", lineHeight: 1.6 }}>
          ورود و ثبت‌نام برای دسترسی به داشبورد عملیات، پرونده‌ها و گزارش‌ها.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem", marginBottom: "2rem", maxWidth: 400, margin: "0 auto 2rem" }}>
          <div className="stat-card" style={{ padding: "1rem" }}>
            <div className="stat-value" style={{ fontSize: "1.5rem" }}>{stats?.closed_cases ?? "—"}</div>
            <div className="stat-label" style={{ fontSize: "0.85rem" }}>پرونده‌های حل‌شده</div>
          </div>
          <div className="stat-card" style={{ padding: "1rem" }}>
            <div className="stat-value" style={{ fontSize: "1.5rem" }}>{stats?.staff_count ?? "—"}</div>
            <div className="stat-label" style={{ fontSize: "0.85rem" }}>کارمندان</div>
          </div>
          <div className="stat-card" style={{ padding: "1rem" }}>
            <div className="stat-value" style={{ fontSize: "1.5rem" }}>{stats?.active_cases ?? "—"}</div>
            <div className="stat-label" style={{ fontSize: "0.85rem" }}>پرونده‌های فعال</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", justifyContent: "center" }}>
          <Link href="/login" className="btn btn-primary" style={{ minWidth: 140 }}>
            ورود
          </Link>
          <Link href="/register" className="btn btn-secondary" style={{ minWidth: 140 }}>
            ثبت‌نام
          </Link>
          <Link href="/dashboard" className="btn btn-secondary" style={{ minWidth: 140 }}>
            داشبورد
          </Link>
        </div>
      </div>
      <footer style={{ marginTop: "3rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
        © Police Digital Operations System
      </footer>
    </main>
  );
}
