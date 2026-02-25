"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";

export type User = {
  id: number;
  username: string;
  email?: string;
  full_name?: string;
  roles?: string[];
  permissions?: string[];
};

type AuthState = {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (identifier: string, password: string) => Promise<boolean>;
  register: (data: {
    username: string;
    email?: string;
    phone?: string;
    national_id?: string;
    full_name?: string;
    password: string;
    password_confirm: string;
  }) => Promise<boolean>;
  logout: () => Promise<void>;
  setError: (err: string | null) => void;
};

const AuthContext = createContext<AuthState | null>(null);

const TOKEN_KEY = "police_ops_token";
const USER_KEY = "police_ops_user";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStored = useCallback(() => {
    if (typeof window === "undefined") return;
    const t = localStorage.getItem(TOKEN_KEY);
    const u = localStorage.getItem(USER_KEY);
    if (t && u) {
      try {
        setToken(t);
        setUser(JSON.parse(u) as User);
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
      }
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadStored();
  }, [loadStored]);

  const login = useCallback(async (identifier: string, password: string) => {
    setError(null);
    const res = await api.post<{ access_token: string; user: User }>(
      "/identity/auth/login/",
      { identifier, password }
    );
    if (res.error || !res.data) {
      setError(res.error?.message || "Login failed");
      return false;
    }
    const t = (res.data as { access_token?: string }).access_token ?? (res.data as { token?: string }).token;
    const u = (res.data as { user?: User }).user;
    if (!t || !u) {
      setError("Invalid response from server");
      return false;
    }
    if (typeof window !== "undefined") {
      localStorage.setItem(TOKEN_KEY, t);
      localStorage.setItem(USER_KEY, JSON.stringify(u));
    }
    setToken(t);
    setUser(u);
    return true;
  }, []);

  const register = useCallback(
    async (data: {
      username: string;
      email?: string;
      phone?: string;
      national_id?: string;
      full_name?: string;
      password: string;
      password_confirm: string;
    }) => {
      setError(null);
      const res = await api.post<{ access_token: string; user: User }>(
        "/identity/auth/register/",
        data
      );
      if (res.error || !res.data) {
        setError(res.error?.message || (res.error?.details as { identifier?: string[] })?.["identifier"]?.[0] || "Registration failed");
        return false;
      }
      const t = (res.data as { access_token?: string }).access_token ?? (res.data as { token?: string }).token;
      const u = (res.data as { user?: User }).user;
      if (!t || !u) {
        setError("Invalid response from server");
        return false;
      }
      if (typeof window !== "undefined") {
        localStorage.setItem(TOKEN_KEY, t);
        localStorage.setItem(USER_KEY, JSON.stringify(u));
      }
      setToken(t);
      setUser(u);
      return true;
    },
    []
  );

  const logout = useCallback(async () => {
    if (token) {
      try {
        await api.post("/identity/auth/logout/", {}, token);
      } catch {
        /* ignore */
      }
    }
    setToken(null);
    setUser(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  }, [token]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        error,
        login,
        register,
        logout,
        setError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
