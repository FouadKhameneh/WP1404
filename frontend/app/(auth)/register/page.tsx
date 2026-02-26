"use client";

import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function RegisterPage() {
  const { register, error, setError } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    username: "",
    email: "",
    phone: "",
    national_id: "",
    full_name: "",
    password: "",
    password_confirm: "",
  });
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (form.password !== form.password_confirm) {
      setError("رمز عبور و تکرار آن یکسان نیستند.");
      return;
    }
    if (form.password.length < 8) {
      setError("رمز عبور باید حداقل ۸ کاراکتر باشد.");
      return;
    }
    if (!form.username.trim()) {
      setError("نام کاربری الزامی است.");
      return;
    }
    if (!form.email?.trim()) {
      setError("ایمیل الزامی است.");
      return;
    }
    if (!form.phone?.trim()) {
      setError("شماره تلفن الزامی است.");
      return;
    }
    if (!form.national_id?.trim()) {
      setError("کد ملی الزامی است.");
      return;
    }
    if (!form.full_name?.trim()) {
      setError("نام کامل الزامی است.");
      return;
    }
    setSubmitting(true);
    const ok = await register({
      username: form.username.trim(),
      email: form.email.trim(),
      phone: form.phone.trim(),
      national_id: form.national_id.trim(),
      full_name: form.full_name.trim(),
      password: form.password,
      password_confirm: form.password_confirm,
    });
    setSubmitting(false);
    if (ok) router.push("/dashboard");
  }

  return (
    <main className="hero-bg" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", padding: "2rem" }}>
      <div className="card" style={{ width: "100%", maxWidth: 420 }}>
        <h1 style={{ margin: "0 0 0.25rem 0", fontSize: "1.75rem", color: "var(--text)" }}>ثبت‌نام</h1>
        <p style={{ margin: "0 0 1.5rem 0", fontSize: "0.9rem", color: "var(--text-muted)" }}>
          همه فیلدها الزامی هستند. ایمیل و تلفن و کد ملی یکتا باشند.
        </p>
        {error && (
          <div role="alert" style={{ padding: "0.75rem", background: "rgba(220, 38, 38, 0.15)", border: "1px solid var(--danger)", borderRadius: "var(--radius)", marginBottom: "1rem", color: "#fca5a5", fontSize: "0.9rem" }}>
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <label className="label">نام کاربری *</label>
          <input
            type="text"
            className="input"
            value={form.username}
            onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
            placeholder="یکتا، بدون فاصله"
            required
          />
          <label className="label">ایمیل *</label>
          <input
            type="email"
            className="input"
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            placeholder="example@domain.com"
            required
          />
          <label className="label">شماره تلفن *</label>
          <input
            type="text"
            className="input"
            value={form.phone}
            onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
            placeholder="مثال: 09121234567"
            required
          />
          <label className="label">کد ملی *</label>
          <input
            type="text"
            className="input"
            value={form.national_id}
            onChange={(e) => setForm((f) => ({ ...f, national_id: e.target.value }))}
            placeholder="۱۰ رقم"
            required
          />
          <label className="label">نام کامل *</label>
          <input
            type="text"
            className="input"
            value={form.full_name}
            onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
            placeholder="نام و نام خانوادگی"
            required
          />
          <label className="label">رمز عبور * (حداقل ۸ کاراکتر)</label>
          <input
            type="password"
            className="input"
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            minLength={8}
            required
          />
          <label className="label">تکرار رمز عبور *</label>
          <input
            type="password"
            className="input"
            value={form.password_confirm}
            onChange={(e) => setForm((f) => ({ ...f, password_confirm: e.target.value }))}
            minLength={8}
            required
          />
          <button type="submit" className="btn btn-primary" disabled={submitting} style={{ marginTop: "0.5rem" }}>
            {submitting ? "در حال ایجاد..." : "ثبت‌نام"}
          </button>
        </form>
        <p style={{ marginTop: "1.5rem", fontSize: "0.9rem", color: "var(--text-muted)" }}>
          <Link href="/login">ورود</Link>
          <span style={{ margin: "0 0.5rem" }}>|</span>
          <Link href="/">خانه</Link>
        </p>
      </div>
    </main>
  );
}
