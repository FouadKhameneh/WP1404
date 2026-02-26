import Link from "next/link";

export default function HomePage() {
  return (
    <main className="hero-bg" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", padding: "2rem" }}>
      <div style={{ textAlign: "center", maxWidth: 560 }}>
        <div style={{ marginBottom: "0.5rem", fontSize: "0.9rem", color: "var(--text-muted)", letterSpacing: "0.15em", textTransform: "uppercase" }}>
          سامانه یکپارچه
        </div>
        <h1 style={{ fontSize: "clamp(1.75rem, 4vw, 2.5rem)", fontWeight: 700, margin: "0 0 0.5rem 0", color: "var(--text)", letterSpacing: "-0.02em" }}>
          Police Digital Operations
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "1.1rem", marginBottom: "2rem", lineHeight: 1.6 }}>
          ورود و ثبت‌نام برای دسترسی به داشبورد عملیات، پرونده‌ها و گزارش‌ها.
        </p>
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
