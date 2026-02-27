"use client";

import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, token, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !token) router.push("/login");
  }, [loading, token, router]);

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="card" style={{ padding: "2rem" }}>
          <div style={{ width: 40, height: 40, border: "3px solid var(--border)", borderTopColor: "var(--accent)", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
          <p style={{ marginTop: "1rem", color: "var(--text-muted)" }}>در حال بارگذاری...</p>
        </div>
      </div>
    );
  }
  if (!token) return null;

  const roles = (user?.roles ?? []).join(", ") || "—";
  const isAdmin = user?.is_staff === true || user?.roles?.some((r: string) => String(r).toLowerCase().includes("admin"));
  const navItems = [
    { href: "/dashboard", label: "داشبورد" },
    { href: "/dashboard/cases", label: "پرونده‌ها" },
    { href: "/dashboard/detective", label: "بورد کارآگاه" },
    { href: "/dashboard/evidence", label: "مدارک" },
    { href: "/dashboard/reports", label: "گزارش‌ها" },
    { href: "/dashboard/wanted", label: "تحت تعقیب" },
    ...(isAdmin ? [{ href: "/dashboard/admin", label: "پنل ادمین" }] : []),
  ];

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          padding: "0.75rem 1.5rem",
          borderBottom: "1px solid var(--border)",
          background: "var(--bg-card)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
          <Link href="/dashboard" style={{ fontWeight: 700, color: "var(--text)", fontSize: "1.15rem" }}>
            PDOS
          </Link>
          <nav style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap" }}>
            {navItems.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={`nav-link ${pathname === href ? "active" : ""}`}
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <span title={roles} style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>
            {user?.username ?? "User"}
          </span>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => logout().then(() => router.push("/"))}
            style={{ padding: "0.4rem 0.9rem", fontSize: "0.9rem" }}
          >
            خروج
          </button>
        </div>
      </header>
      <main style={{ flex: 1, padding: "1.5rem 2rem", maxWidth: 1200, margin: "0 auto", width: "100%" }}>
        {children}
      </main>
    </div>
  );
}
