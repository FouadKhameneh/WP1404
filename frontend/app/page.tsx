import Link from "next/link";

export default function HomePage() {
  return (
    <main style={{ padding: "2rem", maxWidth: 800, margin: "0 auto" }}>
      <h1>Police Digital Operations</h1>
      <p>Welcome. Sign in or register to access the dashboard.</p>
      <nav style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
        <Link href="/login" style={{ color: "#2563eb" }}>Login</Link>
        <Link href="/register" style={{ color: "#2563eb" }}>Register</Link>
        <Link href="/dashboard" style={{ color: "#2563eb" }}>Dashboard</Link>
      </nav>
    </main>
  );
}
