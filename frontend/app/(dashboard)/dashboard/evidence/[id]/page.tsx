"use client";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { PageLoading } from "@/features/loading/LoadingSpinner";
import { useParams, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

type EvidenceDetail = { id: number; title: string; description?: string; evidence_type: string; case?: number };
type ReviewItem = { id: number; decision: string; follow_up_notes?: string; reviewed_by?: { full_name?: string }; reviewed_at?: string };

export default function EvidenceDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const caseId = searchParams.get("case_id");
  const { token } = useAuth();
  const id = Number(params.id);
  const [evidence, setEvidence] = useState<EvidenceDetail | null>(null);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [decision, setDecision] = useState<"accept" | "reject">("accept");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadReviews = useCallback(() => {
    if (!token || !id) return;
    api.get<{ reviews?: ReviewItem[] }>(`/evidence/biological/${id}/reviews/`, token).then((res) => {
      if (res.data) setReviews((res.data as { reviews?: ReviewItem[] }).reviews ?? []);
    });
  }, [token, id]);

  useEffect(() => {
    if (!token || !id) return;
    setLoading(true);
    const cid = caseId ? Number(caseId) : 1;
    api.get<{ evidence?: EvidenceDetail[] }>(`/evidence/cases/?case_id=${cid}`, token).then((res) => {
      if (res.data) {
        const list = (res.data as { evidence?: EvidenceDetail[] }).evidence ?? [];
        const found = list.find((e) => e.id === id) ?? null;
        setEvidence(found ?? { id, title: `مدرک #${id}`, evidence_type: "other" });
      }
    });
    loadReviews();
    setLoading(false);
  }, [token, id, caseId, loadReviews]);

  const handleCoronerSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !id) return;
    setSubmitting(true);
    const res = await api.post(
      `/evidence/biological/${id}/coroner-decision/`,
      { decision, follow_up_notes: notes },
      token
    );
    setSubmitting(false);
    if (res.error) return;
    setNotes("");
    loadReviews();
  };

  if (!token) return null;
  if (loading) return <PageLoading />;

  const isBiological = evidence?.evidence_type === "biological_medical";

  return (
    <div>
      <p style={{ marginBottom: "1rem" }}><Link href="/dashboard/evidence">← بازگشت به مدارک</Link></p>
      <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.75rem" }}>{evidence?.title ?? `مدرک #${id}`}</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>{evidence?.description}</p>

      {isBiological && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3>بررسی پزشکی‌قانونی</h3>
          <form onSubmit={handleCoronerSubmit}>
            <div style={{ display: "grid", gap: "1rem" }}>
              <label>
                تصمیم:
                <select value={decision} onChange={(e) => setDecision(e.target.value as "accept" | "reject")} className="form-control">
                  <option value="accept">تأیید</option>
                  <option value="reject">رد</option>
                </select>
              </label>
              <label>
                یادداشت: <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="form-control" rows={2} />
              </label>
              <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? "..." : "ثبت تصمیم"}</button>
            </div>
          </form>
          {reviews.length > 0 && (
            <div style={{ marginTop: "1.5rem" }}>
              <h4>سابقه بررسی‌ها</h4>
              <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
                {reviews.map((r) => (
                  <li key={r.id} style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}>
                    {r.decision} — {r.follow_up_notes || "—"} ({r.reviewed_by?.full_name ?? "—"})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!isBiological && (
        <p style={{ color: "var(--text-muted)" }}>بررسی پزشکی‌قانونی فقط برای شواهد زیستی/پزشکی است.</p>
      )}
    </div>
  );
}

