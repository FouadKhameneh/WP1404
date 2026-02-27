"use client";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { ErrorDisplay } from "@/features/error/ErrorDisplay";
import { PageLoading } from "@/features/loading/LoadingSpinner";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

type RoleItem = { id: number; name: string; key?: string; description?: string };
type UserItem = { id: number; username: string; full_name?: string; email?: string };
type UserRolesResp = { user: UserItem; roles: { id: number; role: RoleItem }[] };

export default function AdminPage() {
  const { token, user } = useAuth();
  const router = useRouter();
  const [roles, setRoles] = useState<RoleItem[]>([]);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [userRoles, setUserRoles] = useState<UserRolesResp | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAdmin = user?.is_staff === true;

  const loadUserRoles = useCallback(() => {
    if (!token || !selectedUserId) return;
    api.get<UserRolesResp>(`/access/users/${selectedUserId}/roles/`, token).then((res) => {
      if (res.data) setUserRoles(res.data as UserRolesResp);
    });
  }, [token, selectedUserId]);

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
    setLoading(false);
  }, [token, isAdmin, router]);

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

  if (!token) return null;
  if (!isAdmin) return null;
  if (loading) return <PageLoading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  const currentRoleIds = new Set((userRoles?.roles ?? []).map((r) => r.role?.id).filter(Boolean));

  return (
    <div>
      <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.75rem" }}>پنل ادمین</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
        مدیریت نقش‌ها و دسترسی کاربران
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
                    <li key={ur.id} style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
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
                  {(userRoles?.roles ?? []).length === 0 && <li style={{ color: "var(--text-muted)" }}>—</li>}
                </ul>
              </div>
              <div>
                <strong>افزودن نقش:</strong>
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.5rem" }}>
                  {roles.filter((r) => !currentRoleIds.has(r.id)).map((r) => (
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

      <p><Link href="/dashboard">بازگشت به داشبورد</Link></p>
    </div>
  );
}
