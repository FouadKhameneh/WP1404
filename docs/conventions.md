# Team Engineering Conventions

## 1. Branching Strategy

- Main branches:
  - `main`: stable, release-ready branch.
  - `develop`: integration branch for completed features.
- Working branches are short-lived and must be created from `develop`.
- Allowed branch prefixes:
  - `feature/<scope>-<short-description>`
  - `fix/<scope>-<short-description>`
  - `hotfix/<scope>-<short-description>`
  - `chore/<scope>-<short-description>`
  - `docs/<scope>-<short-description>`
  - `test/<scope>-<short-description>`
- Direct pushes to `main` are not allowed.
- Direct pushes to `develop` are discouraged; use pull requests.
- Merge policy:
  - Feature/fix/chore/docs/test branches merge into `develop` via PR.
  - `develop` merges into `main` only for checkpoint/release stabilization.

## 2. Commit Message Format

Use Conventional Commits format:

`<type>(<scope>): <short imperative summary>`

Examples:
- `feat(cases): add complaint validation transition`
- `fix(auth): enforce unique national id check`
- `docs(report): add architecture decision record`

Allowed `type` values:
- `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`

Rules:
- Subject line max 72 characters.
- Use imperative mood.
- One logical change per commit.
- Reference task ID in body/footer when available.
- Avoid vague messages like `update` or `changes`.

## 3. Pull Request Template

Every PR must include the following sections:

- `Title`: concise and descriptive.
- `Summary`: what changed and why.
- `Scope`: backend, frontend, infra, docs.
- `Checklist`:
  - requirements reviewed
  - tests added/updated
  - local tests passed
  - API docs updated (if endpoint change)
  - migration added (if schema change)
  - no secrets committed
- `Breaking Changes`: yes/no; describe impact if yes.
- `Screenshots/Artifacts`: required for UI changes.
- `Test Evidence`: command list and results.
- `Linked Tasks`: issue IDs or tracker links.

Review rules:
- Minimum 1 approval required before merge.
- Author must not self-merge unless urgent and approved by team.
- All review comments must be resolved before merge.

## 4. Naming Rules

General:
- Use English for all code, API, and documentation identifiers.
- Use clear domain terms aligned with project language.

Backend naming:
- Python modules and files: `snake_case`.
- Classes: `PascalCase`.
- Functions, variables, serializer fields: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Django apps: singular or bounded-context names in `snake_case`.

Frontend naming:
- React component files: `PascalCase`.
- Hooks: `useCamelCase`.
- Utility files: `camelCase` or `kebab-case`, keep consistent within folder.
- Route segments in NextJS: `kebab-case`.

Database naming:
- Tables: `snake_case`.
- Columns: `snake_case`.
- Primary key: `id`.
- Foreign keys: `<referenced_entity>_id`.

Branch/task naming:
- Keep names short, readable, and scope-first.
- Replace spaces with hyphens.

## 5. API Versioning Rules

- All public API routes must be prefixed with version:
  - `/api/v1/...`
- `v1` is the active stable contract.
- Backward-incompatible changes require a new major version (`v2`).
- Backward-compatible additions stay in current major version.
- Deprecation policy:
  - Mark deprecated endpoints/fields in docs.
  - Provide migration notes.
  - Keep deprecated behavior available for at least one checkpoint cycle before removal.
- Response contract rules:
  - Keep field names stable within a major version.
  - Additive fields must be optional by default.
  - Error response format must be consistent across endpoints.

## 6. Team Process Notes

- Each team member must contribute regularly across commits and reviews.
- Commit ownership should reflect actual work; avoid bulk commits by one member.
- Use small PRs to improve review quality and reduce merge conflicts.
