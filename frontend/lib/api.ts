/**
 * Global API client for Police Digital Operations backend.
 * Base URL from NEXT_PUBLIC_API_BASE_URL (e.g. http://localhost:8000/api/v1).
 */

const getBaseUrl = () =>
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/$/, "") || "/api/v1"
    : process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export type ApiError = {
  code?: string;
  message?: string;
  details?: Record<string, unknown>;
};

export async function apiRequest<T = unknown>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<{ data?: T; error?: ApiError; status: number }> {
  const { token, ...fetchOptions } = options;
  const base = getBaseUrl();
  const url = path.startsWith("http") ? path : `${base}${path.startsWith("/") ? path : `/${path}`}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(typeof (fetchOptions.headers as Record<string, string>) === "object"
      ? (fetchOptions.headers as Record<string, string>)
      : {}),
  };
  if (token) (headers as Record<string, string>)["Authorization"] = `Token ${token}`;
  const res = await fetch(url, { ...fetchOptions, headers });
  let body: { data?: T; error?: ApiError } = {};
  const ct = res.headers.get("content-type");
  if (ct?.includes("application/json")) {
    try {
      body = await res.json();
    } catch {
      body = { error: { message: "Invalid JSON response" } };
    }
  }
  if (!res.ok) {
    return {
      status: res.status,
      error: body.error || { code: "HTTP_ERROR", message: res.statusText },
    };
  }
  return { status: res.status, data: (body.data ?? body) as T };
}

export const api = {
  get: <T>(path: string, token?: string) =>
    apiRequest<T>(path, { method: "GET", token }),
  post: <T>(path: string, body: unknown, token?: string) =>
    apiRequest<T>(path, { method: "POST", body: JSON.stringify(body), token }),
  put: <T>(path: string, body: unknown, token?: string) =>
    apiRequest<T>(path, { method: "PUT", body: JSON.stringify(body), token }),
  patch: <T>(path: string, body: unknown, token?: string) =>
    apiRequest<T>(path, { method: "PATCH", body: JSON.stringify(body), token }),
  delete: <T>(path: string, token?: string) =>
    apiRequest<T>(path, { method: "DELETE", token }),
};
