"use client";

import React from "react";

export function ErrorDisplay({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="card"
      style={{
        padding: "1.5rem",
        background: "rgba(220, 38, 38, 0.08)",
        borderColor: "var(--danger)",
        maxWidth: 480,
        margin: "2rem auto",
      }}
    >
      <p style={{ margin: 0, color: "#fca5a5" }}>{message}</p>
      {onRetry && (
        <button type="button" className="btn btn-secondary" onClick={onRetry} style={{ marginTop: "1rem" }}>
          تلاش مجدد
        </button>
      )}
    </div>
  );
}
