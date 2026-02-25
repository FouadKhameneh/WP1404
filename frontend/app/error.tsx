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
    <div style={{ padding: "2rem" }}>
      <ErrorDisplay message={error.message || "Something went wrong"} onRetry={reset} />
    </div>
  );
}
