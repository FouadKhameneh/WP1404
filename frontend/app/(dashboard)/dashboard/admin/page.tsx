"use client";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { ErrorDisplay } from "@/features/error/ErrorDisplay";
import { PageLoading } from "@/features/loading/LoadingSpinner";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

type RoleItem = { id: number; name: string; key?: string; description?: string };
type UserItem = {
  id: number;
  username: string;
  full_name?: string;
  email?: string;
  phone?: string;
  national_id?: string;
  is_staff?: boolean;
};
type UserRolesResp = { user: UserItem; roles: { id: number; role: RoleItem }[] };

type CaseListItem = {
  id: number;
  case_number: string;
  title?: string;
  level?: string;
  status?: string;
  priority?: string;
  source_type?: string;
};

export default function AdminPage() {
  const { token, user } = useAuth();
  const router = useRouter();
  const [roles, setRoles] = useState<RoleItem[]>([]);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [userRoles, setUserRoles] = useState<UserRolesResp | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [newUser, setNewUser] = useState({
    username: "",
    full_name: "",
    email: "",
    phone: "",
    national_id: "",
    password: "",
    password_confirm: "",
  });
  const [creatingUser, setCreatingUser] = useState(false);
  const [userFormError, setUserFormError] = useState<string | null>(null);

  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [casesLoading, setCasesLoading] = useState(true);
  const [casesError, setCasesError] = useState<string | null>(null);
  const [creatingCase, setCreatingCase] = useState(false);
  const [caseFormError, setCaseFormError] = useState<string | null>(null);
  const [caseForm, setCaseForm] = useState({
    title: "",
    level: "1",
    priority: "medium",
    scene_occurred_at: "",
    witness_full_name: "",
    witness_phone: "",
    witness_national_id: "",
    witness_notes: "",
  });

  const isAdmin = user?.is_staff === true;

  const loadUserRoles = useCallback(() => {
    if (!token || !selectedUserId) return;
    api.get<UserRolesResp>(`/access/users/${selectedUserId}/roles/`, token).then((res) => {
      if (res.data) setUserRoles(res.data as UserRolesResp);
    });
  }, [token, selectedUserId]);

  const loadCases = useCallback(() => {
    if (!token) return;
    setCasesLoading(true);
    setCasesError(null);
    api.get<{ results?: CaseListItem[] }>("/cases/cases/", token).then((res) => {
      if (res.error) {
        setCasesError(res.error.message || "خطا در بارگذاری پرونده‌ها");
      } else if (res.data) {
        const list =
          (res.data as { results?: CaseListItem[] }).results ??
          (Array.isArray(res.data) ? (res.data as CaseListItem[]) : []);
        setCases(list);
      }
    }).finally(() => setCasesLoading(false));
  }, [token]);

  useEffect(() => {
    if (!token) return;
    if (!isAdmin) {
      router.push("/dashboard");
      return;
    }
    api.get<{ results?: RoleItem[] }>("/access/roles/", token).then((res) => {
      if (res.error) setError(res.error.message || "خطا در بارگذاری نقش‌ها");
      else if (res.data) setRoles((res.data as { results?: RoleItem[] }).results ?? []);
    });
    api.get<{ results?: UserItem[] }>("/access/users/", token).then((res) => {
      if (res.error) setError(res.error.message || "خطا در بارگذاری کاربران");
      else if (res.data) setUsers((res.data as { results?: UserItem[] }).results ?? []);
    });
    loadCases();
    setLoading(false);
  }, [token, isAdmin, router, loadCases]);

  useEffect(() => {
    loadUserRoles();
  }, [selectedUserId, loadUserRoles]);

  const handleAssignRole = async (roleId: number) => {
    if (!token || !selectedUserId) return;
    const res = await api.post(`/access/users/${selectedUserId}/roles/`, { role_id: roleId }, token);
    if (!res.error) loadUserRoles();
  };

  const handleRemoveRole = async (roleId: number) => {
    if (!token || !selectedUserId) return;
    const res = await api.delete(`/access/users/${selectedUserId}/roles/${roleId}/`, token);
    if (!res.error) loadUserRoles();
  };

  const handleCreateUser = async (e: any) => {
    e.preventDefault();
    setUserFormError(null);
    setCreatingUser(true);
    const payload = {
      username: newUser.username.trim(),
      full_name: newUser.full_name.trim(),
      email: newUser.email.trim(),
      phone: newUser.phone.trim(),
      national_id: newUser.national_id.trim(),
      password: newUser.password,
      password_confirm: newUser.password_confirm,
    } as any;

    const res = await api.post<{ user: UserItem }>("/identity/auth/register/", payload);
    if (res.error || !res.data) {
      const details = res.error?.details as Record<string, string[] | string> | undefined;
      let msg = res.error?.message || "ساخت کاربر ناموفق بود.";
      if (details && typeof details === "object") {
        const parts = Object.entries(details).map(([k, v]) => {
          const text = Array.isArray(v) ? v[0] : v;
          return `${k}: ${text}`;
        });
        if (parts.length) msg = parts.join(" — ");
      }
      setUserFormError(msg);
    } else {
      const createdUser = (res.data as any).user as UserItem;
      setUsers((prev) => [createdUser, ...prev]);
      setNewUser({
        username: "",
        full_name: "",
        email: "",
        phone: "",
        national_id: "",
        password: "",
        password_confirm: "",
      });
      setUserFormError(null);
    }
    setCreatingUser(false);
  };

  const handleCreateCase = async (e: any) => {
    e.preventDefault();
    if (!token) return;
    setCaseFormError(null);
    setCreatingCase(true);
    const dt = caseForm.scene_occurred_at.trim();
    const sceneOccurredAt = dt ? new Date(dt).toISOString() : "";
    const payload = {
      title: caseForm.title.trim(),
      summary: "",
      level: caseForm.level,
      priority: caseForm.priority,
      scene_occurred_at: sceneOccurredAt,
      witnesses: [
        {
          full_name: caseForm.witness_full_name.trim(),
          phone: caseForm.witness_phone.trim(),
          national_id: caseForm.witness_national_id.trim(),
          notes: caseForm.witness_notes.trim(),
        },
      ],
    };
    const res = await api.post("/cases/scene-cases/", payload, token);
    if (res.error) {
      const details = res.error.details as Record<string, string[] | string> | undefined;
      let msg = res.error.message || "ایجاد پرونده ناموفق بود.";
      if (details && typeof details === "object") {
        const parts = Object.entries(details).map(([k, v]) => {
          const text = Array.isArray(v) ? v[0] : v;
          return `${k}: ${text}`;
        });
        if (parts.length) msg = parts.join(" — ");
      }
      setCaseFormError(msg);
    } else {
      setCaseForm({
        title: "",
        level: "1",
        priority: "medium",
        scene_occurred_at: "",
        witness_full_name: "",
        witness_phone: "",
        witness_national_id: "",
        witness_notes: "",
      });
      loadCases();
    }
    setCreatingCase(false);
  };

  const handleCloseCase = async (caseId: number) => {
    if (!token) return;
    setCasesError(null);
    const res = await api.post(
      `/cases/cases/${caseId}/transition-status/`,
      { new_status: "closed" },
      token
    );
    if (!res.error) {
      loadCases();
    } else {
      const details = res.error.details as Record<string, string[] | string> | undefined;
      let msg = res.error.message || "بستن پرونده ناموفق بود.";
      if (details && typeof details === "object") {
        const parts = Object.entries(details).map(([k, v]) => {
          const text = Array.isArray(v) ? v[0] : v;
          return `${k}: ${text}`;
        });
        if (parts.length) msg = parts.join(" — ");
      }
      setCasesError(msg);
    }
  };

  if (!token) return null;
  if (!isAdmin) return null;
  if (loading) return <PageLoading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  const currentRoleIds = new Set((userRoles?.roles ?? []).map((r) => r.role?.id).filter(Boolean));

  return (
    <div>
      <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.75rem" }}>پنل ادمین</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
        مدیریت کاربران، نقش‌ها و پرونده‌ها
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", marginBottom: "2rem" }}>
        <div className="card">
          <h3>کاربران</h3>
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {users.map((u) => (
              <li
                key={u.id}
                onClick={() => setSelectedUserId(u.id)}
                style={{
                  padding: "0.5rem",
                  cursor: "pointer",
                  background: selectedUserId === u.id ? "var(--bg-hover)" : "transparent",
                  borderRadius: 4,
                }}
              >
                {u.username} — {u.full_name || u.email || ""}
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h3>نقش‌های کاربر</h3>
          {!selectedUserId ? (
            <p style={{ color: "var(--text-muted)" }}>یک کاربر انتخاب کنید.</p>
          ) : (
            <>
              <p style={{ marginBottom: "1rem" }}>کاربر: {users.find((u) => u.id === selectedUserId)?.username}</p>
              <div style={{ marginBottom: "1rem" }}>
                <strong>نقش‌های فعلی:</strong>
                <ul style={{ listStyle: "none", margin: "0.5rem 0 0", padding: 0 }}>
                  {(userRoles?.roles ?? []).map((ur) => (
                    <li
                      key={ur.id}
                      style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}
                    >
                      <span>{ur.role?.name ?? ur.role?.key}</span>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ padding: "0.2rem 0.5rem", fontSize: "0.8rem" }}
                        onClick={() => handleRemoveRole(ur.role?.id ?? 0)}
                      >
                        حذف
                      </button>
                    </li>
                  ))}
                  {(userRoles?.roles ?? []).length === 0 && (
                    <li style={{ color: "var(--text-muted)" }}>—</li>
                  )}
                </ul>
              </div>
              <div>
                <strong>افزودن نقش:</strong>
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.5rem" }}>
                  {roles
                    .filter((r) => !currentRoleIds.has(r.id))
                    .map((r) => (
                      <button
                        key={r.id}
                        type="button"
                        className="btn btn-primary"
                        style={{ padding: "0.3rem 0.6rem", fontSize: "0.85rem" }}
                        onClick={() => handleAssignRole(r.id)}
                      >
                        + {r.name}
                      </button>
                    ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1.2fr",
          gap: "2rem",
          marginBottom: "2rem",
        }}
      >
        <div className="card">
          <h3>ساخت کاربر جدید</h3>
          <p style={{ color: "var(--text-muted)", marginBottom: "0.75rem" }}>
            برای ساخت یوزر سیستم (شاکی، کارآگاه، ادمین و ...) فیلدهای زیر را پر کنید.
          </p>
          {userFormError && (
            <p style={{ color: "var(--danger)", marginBottom: "0.75rem", fontSize: "0.9rem" }}>
              {userFormError}
            </p>
          )}
          <form
            onSubmit={handleCreateUser}
            style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}
          >
            <input
              type="text"
              placeholder="نام کاربری"
              value={newUser.username}
              onChange={(e) => setNewUser((p) => ({ ...p, username: e.target.value }))}
              required
            />
            <input
              type="text"
              placeholder="نام و نام خانوادگی"
              value={newUser.full_name}
              onChange={(e) => setNewUser((p) => ({ ...p, full_name: e.target.value }))}
              required
            />
            <input
              type="email"
              placeholder="ایمیل"
              value={newUser.email}
              onChange={(e) => setNewUser((p) => ({ ...p, email: e.target.value }))}
              required
            />
            <input
              type="tel"
              placeholder="تلفن"
              value={newUser.phone}
              onChange={(e) => setNewUser((p) => ({ ...p, phone: e.target.value }))}
              required
            />
            <input
              type="text"
              placeholder="کد ملی"
              value={newUser.national_id}
              onChange={(e) => setNewUser((p) => ({ ...p, national_id: e.target.value }))}
              required
            />
            <input
              type="password"
              placeholder="رمز عبور"
              value={newUser.password}
              onChange={(e) => setNewUser((p) => ({ ...p, password: e.target.value }))}
              required
            />
            <input
              type="password"
              placeholder="تکرار رمز عبور"
              value={newUser.password_confirm}
              onChange={(e) =>
                setNewUser((p) => ({ ...p, password_confirm: e.target.value }))
              }
              required
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={creatingUser}
              style={{ marginTop: "0.5rem" }}
            >
              {creatingUser ? "در حال ساخت..." : "ساخت کاربر"}
            </button>
          </form>
        </div>

        <div className="card">
          <h3>ایجاد و مدیریت پرونده‌ها</h3>
          <p style={{ color: "var(--text-muted)", marginBottom: "0.75rem" }}>
            ایجاد پرونده صحنه جرم (Scene Case) و بستن منطقی پرونده‌ها.
          </p>
          {caseFormError && (
            <p style={{ color: "var(--danger)", marginBottom: "0.75rem", fontSize: "0.9rem" }}>
              {caseFormError}
            </p>
          )}
          <form
            onSubmit={handleCreateCase}
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
              gap: "0.5rem 0.75rem",
              marginBottom: "1rem",
            }}
          >
            <input
              type="text"
              placeholder="عنوان پرونده"
              value={caseForm.title}
              onChange={(e) => setCaseForm((p) => ({ ...p, title: e.target.value }))}
              required
            />
            <select
              value={caseForm.level}
              onChange={(e) => setCaseForm((p) => ({ ...p, level: e.target.value }))}
            >
              <option value="1">سطح ۱</option>
              <option value="2">سطح ۲</option>
              <option value="3">سطح ۳</option>
              <option value="critical">بحرانی</option>
            </select>
            <select
              value={caseForm.priority}
              onChange={(e) => setCaseForm((p) => ({ ...p, priority: e.target.value }))}
            >
              <option value="low">کم</option>
              <option value="medium">متوسط</option>
              <option value="high">زیاد</option>
              <option value="urgent">فوری</option>
            </select>
            <input
              type="datetime-local"
              value={caseForm.scene_occurred_at}
              onChange={(e) =>
                setCaseForm((p) => ({ ...p, scene_occurred_at: e.target.value }))
              }
              required
            />
            <input
              type="text"
              placeholder="نام شاهد"
              value={caseForm.witness_full_name}
              onChange={(e) =>
                setCaseForm((p) => ({ ...p, witness_full_name: e.target.value }))
              }
              required
            />
            <input
              type="tel"
              placeholder="تلفن شاهد"
              value={caseForm.witness_phone}
              onChange={(e) =>
                setCaseForm((p) => ({ ...p, witness_phone: e.target.value }))
              }
              required
            />
            <input
              type="text"
              placeholder="کد ملی شاهد"
              value={caseForm.witness_national_id}
              onChange={(e) =>
                setCaseForm((p) => ({ ...p, witness_national_id: e.target.value }))
              }
              required
            />
            <input
              type="text"
              placeholder="توضیح کوتاه شاهد (اختیاری)"
              value={caseForm.witness_notes}
              onChange={(e) =>
                setCaseForm((p) => ({ ...p, witness_notes: e.target.value }))
              }
            />
            <div style={{ gridColumn: "1 / -1", textAlign: "left" }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={creatingCase}
              >
                {creatingCase ? "در حال ایجاد پرونده..." : "ایجاد پرونده صحنه جرم"}
              </button>
            </div>
          </form>

          <h4 style={{ marginBottom: "0.5rem" }}>پرونده‌های اخیر</h4>
          {casesLoading ? (
            <p style={{ color: "var(--text-muted)" }}>در حال بارگذاری لیست پرونده‌ها...</p>
          ) : casesError ? (
            <p style={{ color: "var(--danger)" }}>{casesError}</p>
          ) : cases.length === 0 ? (
            <p style={{ color: "var(--text-muted)" }}>پرونده‌ای یافت نشد.</p>
          ) : (
            <div style={{ maxHeight: 260, overflow: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: "right", padding: "0.4rem" }}>کد پرونده</th>
                    <th style={{ textAlign: "right", padding: "0.4rem" }}>عنوان</th>
                    <th style={{ textAlign: "right", padding: "0.4rem" }}>سطح</th>
                    <th style={{ textAlign: "right", padding: "0.4rem" }}>وضعیت</th>
                    <th style={{ textAlign: "right", padding: "0.4rem" }}>اقدامات</th>
                  </tr>
                </thead>
                <tbody>
                  {cases.map((c) => {
                    const isClosed =
                      c.status === "closed" || c.status === "final_invalid";
                    const canCloseFromHere = c.status === "in_trial";
                    return (
                      <tr key={c.id}>
                        <td style={{ padding: "0.35rem", whiteSpace: "nowrap" }}>
                          {c.case_number}
                        </td>
                        <td style={{ padding: "0.35rem" }}>
                          {c.title || "—"}
                        </td>
                        <td style={{ padding: "0.35rem" }}>{c.level || "—"}</td>
                        <td style={{ padding: "0.35rem" }}>{c.status || "—"}</td>
                        <td style={{ padding: "0.35rem" }}>
                          <button
                            type="button"
                            className="btn btn-secondary"
                            style={{ padding: "0.2rem 0.5rem", fontSize: "0.8rem" }}
                            disabled={isClosed || !canCloseFromHere}
                            onClick={() => handleCloseCase(c.id)}
                          >
                            بستن پرونده
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <p>
        <Link href="/dashboard">بازگشت به داشبورد</Link>
      </p>
    </div>
  );
}
