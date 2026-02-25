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
        border: "3px solid #e5e7eb",
        borderTopColor: "#3b82f6",
        borderRadius: "50%",
        animation: "spin 0.8s linear infinite",
      }}
    />
  );
}

export function PageLoading() {
  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <LoadingSpinner />
      <p style={{ marginTop: "1rem" }}>Loading...</p>
    </div>
  );
}
