# Report outline – Police Digital Operations System

This document maps project deliverables to a typical grading rubric.

---

## 1. Backend / API (Tasks 34–41)

| Rubric item | Deliverable | Location |
|-------------|-------------|----------|
| Captain/chief referral workflow | Normal case: captain or chief; critical case: chief only | `backend/apps/cases/services.py`, `cases/tests.py` (CaptainChiefReferralFlowTests) |
| Judiciary module | Referral package, verdict recording, case closure | `backend/apps/judiciary/` (views, models, urls) |
| Wanted lifecycle | Wanted model, signal on suspect, promote to most-wanted, list API | `backend/apps/wanted/` (models, services, management command) |
| Ranking/reward formula | Lj, Di, ranking score, reward amount (20M multiplier) | `backend/apps/rewards/` (RewardComputationSnapshot, services) |
| Reward tip workflow | Tips: pending_police → pending_detective → approved/rejected, claim_id | `backend/apps/rewards/` (RewardTip, tips API, review API) |
| Reward claim verification | POST verify-claim (national_id + reward_claim_id), police-only | `backend/apps/rewards/views.py`, access permission `rewards.claim.verify` |
| Payment module (L2/L3) | Gateway adapter interface, PaymentTransaction, initiate/callback | `backend/apps/payments/` (gateway.py, adapters, views) |
| Reporting/statistics APIs | Homepage, case counts, stage distribution, approvals, wanted rankings, reward outcomes, general | `backend/apps/reports/` (services, views) |

---

## 2. Async processing (Task 42)

| Rubric item | Deliverable | Location |
|-------------|-------------|----------|
| Worker + scheduler | Celery worker + Beat; management commands | `backend/config/celery.py`, `apps/notifications/tasks.py`, management commands in notifications, identity, payments, wanted |
| Notifications | process_notifications command (extensible) | `apps/notifications/management/commands/process_notifications.py` |
| Most-wanted promotion | wanted_promote command (scheduler/Celery) | `apps/wanted/management/commands/wanted_promote.py` |
| Token expiry | expire_tokens command | `apps/identity/management/commands/expire_tokens.py` |
| Payment reconciliation | payment_reconcile command | `apps/payments/management/commands/payment_reconcile.py` |

---

## 3. Backend tests (Task 43)

| Rubric item | Deliverable | Location |
|-------------|-------------|----------|
| ≥10 automated tests | Model invariants, permissions, workflow, formula, API errors, scheduler | `backend/apps/*/tests.py` (cases, investigation, judiciary, wanted, rewards, payments, reports, notifications, evidence, access, identity) |
| Model invariants | Case, participant, complaint, evidence | e.g. `cases/tests.py`, `evidence/tests.py` |
| Permission boundaries | Reports 403 without permission, role-based access | `reports/tests.py`, `access/tests.py`, investigation/cases tests |
| Workflow transitions | Referral, verdict, tip approval, complaint flow | cases, judiciary, rewards tests |
| Formula correctness | Ranking/reward computation | `rewards/tests.py` (RankingRewardFormulaTests) |
| API error handling | 403, validation errors | `reports/tests.py`, identity tests |
| Scheduler/commands | run_scheduled_tasks, expire_tokens, payment_reconcile dry-run | `notifications/tests.py` (ScheduledTasksTests) |

---

## 4. Frontend scaffold (Task 44)

| Rubric item | Deliverable | Location |
|-------------|-------------|----------|
| React or Next.js | Next.js 14 App Router | `frontend/` (package.json, next.config.js, app/) |
| Modular feature folders | features/loading, features/error, app/(auth), app/(dashboard) | `frontend/features/`, `frontend/app/` |
| Role-aware routing / dashboard | Dashboard layout with nav; role from auth | `frontend/app/(dashboard)/dashboard/layout.tsx` |
| Global API client | apiRequest, api.get/post/… with token | `frontend/lib/api.ts` |
| Auth state | AuthContext (login, register, logout, token, user) | `frontend/context/AuthContext.tsx` |
| Loading/error UX | LoadingSpinner, PageLoading, ErrorDisplay, app/loading.tsx, error.tsx | `frontend/features/loading/`, `frontend/features/error/`, `frontend/app/loading.tsx`, `frontend/app/error.tsx` |

---

## 5. Frontend pages and polish (Task 45)

| Rubric item | Deliverable | Location |
|-------------|-------------|----------|
| Home stats | Dashboard home with reports/homepage API | `frontend/app/(dashboard)/dashboard/page.tsx` |
| Login/register | Auth pages | `frontend/app/(auth)/login/page.tsx`, `register/page.tsx` |
| Role-based dashboard | Dashboard layout + nav by route | `frontend/app/(dashboard)/dashboard/layout.tsx` |
| Detective board | Drag/drop, linking, image export (PNG) | `frontend/app/(dashboard)/dashboard/detective/page.tsx` |
| Most wanted | List from /wanted/ API | `frontend/app/(dashboard)/dashboard/wanted/page.tsx` |
| Case/complaint status | Cases list from /cases/ | `frontend/app/(dashboard)/dashboard/cases/page.tsx` |
| General reporting | General report from /reports/general/ | `frontend/app/(dashboard)/dashboard/reports/page.tsx` |
| Evidence registration/review | Evidence links list, placeholder for review | `frontend/app/(dashboard)/dashboard/evidence/page.tsx` |
| ≥5 frontend tests | Home, Login, API client, LoadingSpinner, ErrorDisplay | `frontend/__tests__/*.test.tsx`, `*.test.ts` |
| Docker Compose | Full stack (backend, frontend, postgres, redis, worker, beat) | `infra/docker-compose.yml` |
| Swagger completeness | OpenAPI schema and docs | See below; `backend/config/urls.py` (api/schema/, api/docs/) |
| Final report artifacts | This outline + Swagger review | `docs/report-outline.md`, `docs/swagger-completeness.md` |

---

## 6. Swagger completeness review

- **Schema endpoint**: `GET /api/schema/` (OpenAPI 3.x).
- **Docs UI**: `GET /api/docs/` (Swagger UI), `GET /api/redoc/` (ReDoc).
- **Covered API groups**: identity (auth), access (roles/permissions), cases (complaint, scene, referral), evidence (links, biological review, media), investigation (reasonings, assessments, arrest/interrogation orders), judiciary (referral-package, verdict), wanted (list/filter), rewards (tips, review, verify-claim), payments (initiate, callback), reports (homepage, cases, approvals, wanted-rankings, reward-outcomes, general).
- **Authentication**: Token (Bearer/Token) supported; document in Swagger via `drf_spectacular` settings if needed.

See `docs/swagger-completeness.md` for a concise checklist.

---

## 7. Artifacts summary

| Artifact | Path |
|----------|------|
| Backend apps | `backend/apps/` (identity, access, cases, evidence, investigation, judiciary, wanted, rewards, payments, reports, notifications) |
| Backend tests | `backend/apps/*/tests.py` |
| Frontend | `frontend/` (Next.js, app router, features, context, lib) |
| Frontend tests | `frontend/__tests__/` |
| Docker | `infra/docker-compose.yml`, `infra/.env.example`, Dockerfiles |
| Report outline | `docs/report-outline.md` |
| Swagger review | `docs/swagger-completeness.md` |
