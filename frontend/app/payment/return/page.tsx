"use client";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";

type Transaction = {
  id?: number;
  status?: string;
  amount_rials?: number;
  gateway_name?: string;
  case?: number;
};

export default function PaymentReturnPage() {
  const searchParams = useSearchParams();
  const transactionId = searchParams.get("transaction_id");
  const statusParam = searchParams.get("status");
  const { token } = useAuth();
  const [tx, setTx] = useState<Transaction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!transactionId) {
      setError("شناسه تراکنش یافت نشد.");
      setLoading(false);
      return;
    }
    if (!token) {
      setError("برای مشاهده نتیجه پرداخت، وارد شوید.");
      setLoading(false);
      return;
    }
    api
      .get<Transaction>(`/payments/transactions/${transactionId}/`, token)
      .then((res) => {
        if (res.error) setError(res.error.message || "خطا در بارگذاری وضعیت.");
        else if (res.data) setTx(res.data as Transaction);
      })
      .finally(() => setLoading(false));
  }, [transactionId, token]);

  if (loading) {
    return (
      <div className="card" style={{ maxWidth: 400, margin: "3rem auto", padding: "2rem", textAlign: "center" }}>
        <div style={{ width: 40, height: 40, border: "3px solid var(--border)", borderTopColor: "var(--accent)", borderRadius: "50%", animation: "spin 0.8s linear infinite", margin: "0 auto 1rem" }} />
        <p style={{ color: "var(--text-muted)" }}>در حال بررسی وضعیت پرداخت...</p>
      </div>
    );
  }

  const isSuccess = tx?.status === "success" || statusParam === "success";

  return (
    <main style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem" }}>
      <div className="card" style={{ maxWidth: 420, width: "100%", padding: "2rem", textAlign: "center" }}>
        <h1 style={{ margin: "0 0 1rem 0", fontSize: "1.5rem", color: "var(--text)" }}>
          بازگشت از درگاه پرداخت
        </h1>
        {error ? (
          <p style={{ color: "var(--error)", marginBottom: "1.5rem" }}>{error}</p>
        ) : isSuccess ? (
          <>
            <p style={{ color: "var(--success)", fontSize: "1.1rem", marginBottom: "1rem" }}>
              ✓ پرداخت با موفقیت انجام شد.
            </p>
            {tx?.amount_rials && <p style={{ color: "var(--text-muted)" }}>مبلغ: {tx.amount_rials.toLocaleString("fa-IR")} ریال</p>}
          </>
        ) : (
          <>
            <p style={{ color: "var(--error)", fontSize: "1.1rem", marginBottom: "1rem" }}>
              ✗ پرداخت انجام نشد یا با خطا مواجه شد.
            </p>
            {tx?.status && <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>وضعیت: {tx.status}</p>}
          </>
        )}
        <div style={{ marginTop: "2rem" }}>
          <Link href="/dashboard" className="btn btn-primary">
            بازگشت به داشبورد
          </Link>
        </div>
      </div>
    </main>
  );
}
