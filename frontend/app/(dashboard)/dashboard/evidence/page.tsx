"use client";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { ErrorDisplay } from "@/features/error/ErrorDisplay";
import { PageLoading } from "@/features/loading/LoadingSpinner";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

type CaseItem = { id: number; case_number?: string; title?: string };
type EvidenceItem = {
  id: number;
  title: string;
  description?: string;
  evidence_type: string;
  evidence_type_display?: string;
  registered_at: string;
  registrar_display?: string;
};

const EVIDENCE_TYPES = [
  { value: "witness_testimony", label: "استشهاد شاهد" },
  { value: "biological_medical", label: "زیستی/پزشکی" },
  { value: "vehicle", label: "خودرو" },
  { value: "identification", label: "مدرک شناسایی" },
  { value: "other", label: "سایر" },
];

export default function EvidencePage() {
  const { token, user } = useAuth();
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [links, setLinks] = useState<{ id: number; source_node?: { title: string }; target_node?: { title: string } }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formType, setFormType] = useState("other");
  const [formTitle, setFormTitle] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formPlate, setFormPlate] = useState("");
  const [formSerial, setFormSerial] = useState("");
  const [formModel, setFormModel] = useState("");
  const [formColor, setFormColor] = useState("");
  const [formAttributes, setFormAttributes] = useState("{}");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const loadCases = useCallback(() => {
    if (!token) return;
    api.get<{ results?: CaseItem[] }>("/cases/cases/", token).then((res) => {
      if (res.data) {
        const list = (res.data as { results?: CaseItem[] }).results ?? [];
        setCases(list);
        if (list.length > 0 && !selectedCaseId) setSelectedCaseId(list[0].id);
      }
    });
  }, [token, selectedCaseId]);

  const loadEvidence = useCallback(() => {
    if (!token || !selectedCaseId) return;
    api.get<{ evidence?: EvidenceItem[] }>(`/evidence/cases/?case_id=${selectedCaseId}`, token).then((res) => {
      if (res.data) setEvidence((res.data as { evidence?: EvidenceItem[] }).evidence ?? []);
    });
  }, [token, selectedCaseId]);

  const loadLinks = useCallback(() => {
    if (!token) return;
    api.get<{ links?: unknown[] }>(`/evidence/links/?case_id=${selectedCaseId || ""}`, token).then((res) => {
      if (res.data) setLinks((res.data as { links?: typeof links }).links ?? []);
    });
  }, [token, selectedCaseId]);

  useEffect(() => {
    if (!token) return;
    loadCases();
  }, [token, loadCases]);

  useEffect(() => {
    if (!token) return;
    loadEvidence();
    loadLinks();
  }, [token, selectedCaseId, loadEvidence, loadLinks]);

  useEffect(() => {
    setLoading(false);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedCaseId) return;
    setSubmitting(true);
    setSubmitError(null);
    const payload: Record<string, unknown> = {
      case_id: selectedCaseId,
      evidence_type: formType,
      title: formTitle,
      description: formDesc,
      registered_at: new Date().toISOString(),
    };
    if (formType === "vehicle") {
      payload.model = formModel;
      payload.color = formColor;
      payload.plate = formPlate || undefined;
      payload.serial_number = formSerial || undefined;
    }
    if (formType === "identification") {
      try {
        payload.attributes = JSON.parse(formAttributes || "{}");
      } catch {
        setSubmitError("attributes باید JSON معتبر باشد");
        setSubmitting(false);
        return;
      }
    }
    const res = await api.post<{ evidence?: EvidenceItem }>("/evidence/cases/create/", payload, token);
    setSubmitting(false);
    if (res.error) setSubmitError(res.error.message || "ثبت ناموفق بود.");
    else {
      setShowForm(false);
      setFormTitle("");
      setFormDesc("");
      loadEvidence();
    }
  };

  if (!token) return null;
  if (loading) return <PageLoading />;
  if (error) return <ErrorDisplay message={error} onRetry={() => window.location.reload()} />;

  return (
    <div>
      <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.75rem", color: "var(--text)" }}>ثبت و بررسی مدارک</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
        انتخاب پرونده، مشاهده شواهد، ثبت مدرک جدید، لینک‌ها و بررسی پزشکی‌قانونی
      </p>

      <div style={{ marginBottom: "1rem", display: "flex", gap: "1rem", alignItems: "center", flexWrap: "wrap" }}>
        <label>
          <span style={{ marginLeft: "0.5rem" }}>پرونده:</span>
          <select
            value={selectedCaseId ?? ""}
            onChange={(e) => setSelectedCaseId(Number(e.target.value) || null)}
            className="form-control"
            style={{ marginRight: "0.5rem", minWidth: 200 }}
          >
            <option value="">— انتخاب —</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.case_number} - {c.title}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "انصراف" : "+ ثبت مدرک جدید"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card" style={{ marginBottom: "1.5rem" }}>
          <h3>ثبت مدرک جدید</h3>
          {submitError && <p style={{ color: "var(--error)", marginBottom: "0.5rem" }}>{submitError}</p>}
          <div style={{ display: "grid", gap: "1rem" }}>
            <label>
              نوع مدرک:
              <select value={formType} onChange={(e) => setFormType(e.target.value)} className="form-control">
                {EVIDENCE_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </label>
            <label>
              عنوان: <input type="text" value={formTitle} onChange={(e) => setFormTitle(e.target.value)} className="form-control" required />
            </label>
            <label>
              توضیحات: <textarea value={formDesc} onChange={(e) => setFormDesc(e.target.value)} className="form-control" rows={2} />
            </label>
            {formType === "vehicle" && (
              <>
                <label>مدل: <input type="text" value={formModel} onChange={(e) => setFormModel(e.target.value)} className="form-control" /></label>
                <label>رنگ: <input type="text" value={formColor} onChange={(e) => setFormColor(e.target.value)} className="form-control" /></label>
                <label>پلاک (یا خالی برای شماره سریال): <input type="text" value={formPlate} onChange={(e) => setFormPlate(e.target.value)} className="form-control" /></label>
                <label>شماره سریال (اگر پلاک ندارید): <input type="text" value={formSerial} onChange={(e) => setFormSerial(e.target.value)} className="form-control" /></label>
              </>
            )}
            {formType === "identification" && (
              <label>attributes (JSON): <textarea value={formAttributes} onChange={(e) => setFormAttributes(e.target.value)} className="form-control" rows={2} placeholder='{"full_name":"","national_id":""}' /></label>
            )}
            <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? "در حال ثبت..." : "ثبت"}</button>
          </div>
        </form>
      )}

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <h3 style={{ padding: "1rem 1rem 0" }}>شواهد پرونده</h3>
        {evidence.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>مدرکی یافت نشد. یک پرونده انتخاب کنید یا مدرک جدید ثبت کنید.</div>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {evidence.map((e) => (
              <li key={e.id} className="list-item" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
                <div>
                  <span style={{ fontWeight: 500 }}>{e.title}</span>
                  <span style={{ marginRight: "0.5rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    ({e.evidence_type_display ?? e.evidence_type})
                  </span>
                  {e.registrar_display && <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}> — {e.registrar_display}</span>}
                </div>
                <Link href={`/dashboard/evidence/${e.id}?case_id=${selectedCaseId}`} style={{ fontSize: "0.9rem" }}>مشاهده / تأیید پزشکی</Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="card" style={{ marginTop: "1rem", padding: 0, overflow: "hidden" }}>
        <h3 style={{ padding: "1rem 1rem 0" }}>لینک‌های مدارک</h3>
        {links.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>لینکی وجود ندارد.</div>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {links.map((l) => (
              <li key={l.id} className="list-item">
                {l.source_node?.title ?? "—"} → {l.target_node?.title ?? "—"}
              </li>
            ))}
          </ul>
        )}
      </div>

      <p style={{ marginTop: "1rem" }}><Link href="/dashboard">بازگشت به داشبورد</Link></p>
    </div>
  );
}
