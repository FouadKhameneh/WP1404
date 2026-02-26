"use client";

import { ErrorDisplay } from "@/features/error/ErrorDisplay";
import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <div style={{ padding: "2rem", minHeight: "60vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <ErrorDisplay message={error.message || "خطایی رخ داد."} onRetry={reset} />
    </div>
  );
}
