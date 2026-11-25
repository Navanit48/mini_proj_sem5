# AidFlow AI

AidFlow AI helps people discover Indian government welfare schemes, check their eligibility, and organize application tasks. The MVP combines a React frontend, FastAPI backend, and Supabase for authentication, PostgreSQL data, and document storage.

## Features

- Supabase registration, login, session persistence, logout, and protected routes.
- User dashboard with profile completion, latest eligibility results, uploaded document count, checklist progress, and deterministic insights.
- Scheme discovery with search, category filters, eligibility and benefit summaries, deadlines, and official links.
- Rule-based eligibility checks with saved history and deterministic recommendations.
- Scheme checklists with saved progress.
- PDF/JPEG upload, document listing, and deletion through Supabase Storage.
- Personal analytics based on saved eligibility, document, and checklist data.
- Deterministic assistant with scheme explanations, saved conversation history, and profile-aware answers.

## Architecture and folder structure

```text
backend/
  app/
    routers/       FastAPI endpoints
    schemas/       Request and response models
    services/      Eligibility, checklist, OCR, and assistant logic
    utils/         Supabase, storage, and provider clients
    dependencies.py Authentication and shared dependencies
  tests/           Python unittest coverage
frontend/
  src/
    components/    Shared UI and feature components
    context/       Authentication context
    lib/           API and Supabase clients
    pages/         Application screens
    router/        Public and protected routes
  public/          Static files
supabase/
  migrations/      SQL schema, policies, seed data, and feature changes
```

The frontend calls FastAPI under `/api/v1`. The backend verifies Supabase Auth tokens, then uses the Supabase service client for database and Storage operations. Keep ownership filters in backend queries because that client has elevated access.

## Tech stack

- React 19, Vite, Tailwind CSS, React Router, Axios, Framer Motion, Recharts, and Lucide.
- Python, FastAPI, Pydantic, and the Supabase Python client.
- Supabase Auth, PostgreSQL, Row Level Security, and Storage.
- Optional Groq integration is used by existing checklist/OCR services; the assistant itself is deterministic and uses no external model.

## Local setup

Requirements: Node.js/npm, Python 3.10+, and a Supabase project.

Apply `supabase/migrations/001` through `006` in order in the Supabase SQL Editor for a fresh database. If earlier migrations are already applied, run only migrations that have not yet been applied; `006_assistant_conversations.sql` creates assistant history tables and ownership policies.

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<publishable-or-anon-key>
```

Create `backend/.env`:

```env
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<publishable-or-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
GROQ_API_KEY=<optional>
GROQ_MODEL=llama-3.3-70b-versatile
PADDLE_USE_GPU=false
PADDLE_LANG=en
MAX_UPLOAD_SIZE_MB=10
ALLOWED_FILE_TYPES=image/jpeg,application/pdf
N8N_WEBHOOK_SECRET=<optional-webhook-secret>
```

The Groq, PaddleOCR, upload, and webhook values are optional overrides. Never expose the service-role key in frontend configuration or commit local environment files.

Run the API:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In another terminal, run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API documentation is at `http://127.0.0.1:8000/api/docs`. Run frontend build with `cd frontend && npm run build`; run backend tests with `cd backend && python -m unittest discover -s tests -v`.

## Screenshots

Add review screenshots under `docs/screenshots/`:

- Dashboard: `docs/screenshots/dashboard.png`
- Schemes: `docs/screenshots/schemes.png`
- Eligibility: `docs/screenshots/eligibility.png`
- Assistant: `docs/screenshots/assistant.png`

## Known limitations and future work

- Eligibility rules cover only a subset of seeded schemes; check scheme records and rule coverage before relying on an outcome.
- Assistant responses are deterministic and limited to information stored in AidFlow. They are guidance, not official decisions.
- OCR processing exists in the backend but is not part of the current document screen flow.
- Automated API coverage is limited, and no frontend end-to-end suite is configured.
- Older bootstrap migrations contain overlapping idempotent table definitions. Preserve applied migration history and use the ordered SQL files for new installations.
- Future work: expand validated scheme rules, add full document verification workflow, add browser-level tests, and optionally provide a model-backed assistant behind the existing provider interface.
