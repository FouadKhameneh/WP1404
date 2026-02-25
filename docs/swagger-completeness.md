# Swagger / OpenAPI completeness review

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/schema/` | OpenAPI 3 schema (JSON/YAML) |
| `GET /api/docs/` | Swagger UI |
| `GET /api/redoc/` | ReDoc UI |

## API coverage (v1)

All v1 APIs are mounted under `/api/v1/` and are included in the schema via `drf_spectacular.openapi.AutoSchema` (DEFAULT_SCHEMA_CLASS in settings).

| Prefix | App | Main resources |
|--------|-----|----------------|
| `/api/v1/identity/` | identity | auth/register, auth/login, auth/logout, me |
| `/api/v1/access/` | access | roles, permissions, user-role assignments, current-authorization |
| `/api/v1/cases/` | cases | complaints, scene cases, referral, timeline |
| `/api/v1/evidence/` | evidence | links, biological reviews, coroner decision, media (stream, signed URL) |
| `/api/v1/investigation/` | investigation | reasonings, assessments, arrest/interrogation orders |
| `/api/v1/judiciary/` | judiciary | referral-package, verdict |
| `/api/v1/wanted/` | wanted | list/filter (status=wanted|most_wanted) |
| `/api/v1/rewards/` | rewards | tips, review, verify-claim |
| `/api/v1/payments/` | payments | initiate, callback |
| `/api/v1/reports/` | reports | homepage, cases, approvals, wanted-rankings, reward-outcomes, general |
| `/api/v1/notifications/` | notifications | (if any public endpoints) |

## Checklist

- [x] Schema generated from DRF views
- [x] All v1 apps included via URL includes
- [x] Authentication: Token (DRF TokenAuthentication) in use; can be described in schema
- [x] Pagination: PageNumberPagination used where applicable
- [ ] Optional: Add `SPECTACULAR_SETTINGS` for tags, security schemes, examples (already has TITLE, DESCRIPTION, VERSION in base settings)

## How to verify

1. Run backend: `python manage.py runserver`
2. Open `http://localhost:8000/api/docs/` and confirm all v1 paths appear.
3. Open `http://localhost:8000/api/schema/` and confirm response is valid OpenAPI JSON.
