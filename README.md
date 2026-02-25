# Police Digital Operations System

This repository is a monorepo for the course project that digitizes police operations from complaint intake through investigation, judiciary referral, and trial outcomes.

## Stack Constraints

- Backend must be implemented with Django REST Framework (DRF).
- Frontend must be implemented with React or NextJS.
- Using other backend/frontend frameworks is out of project scope.

## Repository Structure

- `backend/` - DRF backend service
- `frontend/` - React or NextJS frontend application
- `infra/` - Docker and infrastructure-related configuration
- `docs/` - architecture, requirement, and reporting documents
- `scripts/` - development and automation scripts

## Run locally

1. **Backend** (Django, default SQLite if no `DB_NAME`):
   ```bash
   cd backend
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver 0.0.0.0:8000
   ```
   - API: http://localhost:8000/api/v1/
   - Swagger: http://localhost:8000/api/docs/
   - Admin: http://localhost:8000/admin/ (create superuser first: `python manage.py createsuperuser`)

2. **Frontend** (Next.js):
   ```bash
   cd frontend
   npm install
   $env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000/api/v1"   # PowerShell
   npm run dev
   ```
   - App: http://localhost:3000

3. **Full stack with Docker** (from repo root):
   ```bash
   cd infra
   cp .env.example .env
   docker compose up -d
   ```
   Backend: port 8000, Frontend: port 3000, Postgres, Redis. Optional worker/beat: `docker compose --profile worker up -d`.
