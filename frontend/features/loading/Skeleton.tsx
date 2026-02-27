import React from "react";

export function Skeleton({
  width,
  height = 16,
  className = "",
  style = {},
}: {
  width?: string | number;
  height?: number;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={className}
      style={{
        width: width ?? "100%",
        height,
        background: "linear-gradient(90deg, var(--border) 25%, rgba(255,255,255,0.08) 50%, var(--border) 75%)",
        backgroundSize: "200% 100%",
        animation: "skeleton-shimmer 1.2s ease-in-out infinite",
        borderRadius: 4,
        ...style,
      }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="card" style={{ padding: "1rem" }}>
      <Skeleton width="60%" height={20} style={{ marginBottom: "0.75rem" }} />
      <Skeleton width="100%" height={14} style={{ marginBottom: "0.5rem" }} />
      <Skeleton width="80%" height={14} />
    </div>
  );
}

export function SkeletonList({ count = 5 }: { count?: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <Skeleton width={40} height={40} style={{ borderRadius: "50%", flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <Skeleton width="70%" height={14} style={{ marginBottom: "0.25rem" }} />
            <Skeleton width="40%" height={12} />
          </div>
        </div>
      ))}
    </div>
  );
}
