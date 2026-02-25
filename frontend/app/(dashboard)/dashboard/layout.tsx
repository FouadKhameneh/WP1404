"use client";

import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, token, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !token) router.push("/login");
  }, [loading, token, router]);

  if (loading) return <div style={{ padding: "2rem" }}>Loading...</div>;
  if (!token) return null;

  const roles = (user?.roles ?? []).join(", ") || "—";

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          padding: "1rem 2rem",
          borderBottom: "1px solid #e5e7eb",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <nav style={{ display: "flex", gap: "1rem" }}>
          <Link href="/dashboard">Dashboard</Link>
          <Link href="/dashboard/cases">Cases</Link>
          <Link href="/dashboard/reports">Reports</Link>
          <Link href="/dashboard/wanted">Most Wanted</Link>
        </nav>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <span title={roles}>{user?.username ?? "User"}</span>
          <button type="button" onClick={() => logout().then(() => router.push("/"))} style={{ background: "none", border: "none", cursor: "pointer", color: "#2563eb", padding: 0 }}>Logout</button>
        </div>
      </header>
      <main style={{ flex: 1, padding: "2rem" }}>{children}</main>
    </div>
  );
}
