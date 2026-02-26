"use client";

import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function LoginPage() {
  const { login, error, setError } = useAuth();
  const router = useRouter();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const ok = await login(identifier, password);
    setSubmitting(false);
    if (ok) router.push("/dashboard");
  }

  return (
    <main className="hero-bg" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", padding: "2rem" }}>
      <div className="card" style={{ width: "100%", maxWidth: 400 }}>
        <h1 style={{ margin: "0 0 0.25rem 0", fontSize: "1.75rem", color: "var(--text)" }}>ورود</h1>
        <p style={{ margin: "0 0 1.5rem 0", fontSize: "0.9rem", color: "var(--text-muted)" }}>
          نام کاربری، ایمیل، تلفن یا کد ملی
        </p>
        {error && (
          <div role="alert" style={{ padding: "0.75rem", background: "rgba(220, 38, 38, 0.15)", border: "1px solid var(--danger)", borderRadius: "var(--radius)", marginBottom: "1rem", color: "#fca5a5" }}>
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.1rem" }}>
          <label className="label">
            شناسه
            <input
              type="text"
              className="input"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="username / email / phone / national ID"
              required
            />
          </label>
          <label className="label">
            رمز عبور
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={submitting} style={{ marginTop: "0.5rem" }}>
            {submitting ? "در حال ورود..." : "ورود"}
          </button>
        </form>
        <p style={{ marginTop: "1.5rem", fontSize: "0.9rem", color: "var(--text-muted)" }}>
          <Link href="/register">ثبت‌نام</Link>
          <span style={{ margin: "0 0.5rem" }}>|</span>
          <Link href="/">خانه</Link>
        </p>
      </div>
    </main>
  );
}
