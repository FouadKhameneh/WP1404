import React from "react";

export function LoadingSpinner({ className = "" }: { className?: string }) {
  return (
    <div
      className={className}
      role="status"
      aria-label="Loading"
      style={{
        width: 32,
        height: 32,
        border: "3px solid var(--border)",
        borderTopColor: "var(--accent)",
        borderRadius: "50%",
        animation: "spin 0.8s linear infinite",
      }}
    />
  );
}

export function PageLoading() {
  return (
    <div className="card" style={{ padding: "2rem", textAlign: "center", maxWidth: 320, margin: "2rem auto" }}>
      <LoadingSpinner />
      <p style={{ marginTop: "1rem", color: "var(--text-muted)" }}>در حال بارگذاری...</p>
    </div>
  );
}
