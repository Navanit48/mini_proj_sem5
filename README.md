# AidFlow AI

AidFlow AI is a GovTech MVP for helping people in India discover government welfare schemes and organize the steps needed to apply. It combines a React web app, a FastAPI service, and Supabase authentication and data storage.

## Features completed

- **Authentication:** Supabase registration, login, logout, persistent sessions, and protected pages.
- **Dashboard:** Profile completion, latest eligibility count, uploaded document count, and checklist progress from backend data.
- **Government schemes:** Search and category filters over Supabase-backed scheme records, with benefits, eligibility summaries, deadlines, and application links.
- **Eligibility checker:** Profile-prefilled eligibility checks against configured `scheme_rules`, match percentages, result statuses, and saved check history. Rule definitions currently cover 9 of the 12 seeded schemes.
- **Checklists:** Create a checklist for a selected scheme, load saved tasks, mark tasks complete, and track progress.
- **Analytics:** Charts based on the signed-in user’s eligibility history, document statuses, and checklist progress.

The Documents screen and API scaffolding are present; the end-to-end document workflow is still future work.

## Tech stack

- **Frontend:** React 19, Vite, Tailwind CSS, React Router, Axios, Framer Motion, Recharts, Lucide icons.
- **Backend:** Python, FastAPI, Pydantic, Supabase Python client.
- **Data and identity:** Supabase Auth, PostgreSQL, and Storage.
- **Optional checklist generation:** Groq API, with a built-in checklist fallback when it is unavailable.

## Repository structure

```text
backend/
  app/
    routers/       API endpoints
    schemas/       Request and response models
    services/      Eligibility and checklist logic
    utils/         Supabase, storage, and API helpers
  alembic/         Backend database migration history
  requirements.txt Python dependencies
frontend/
  src/
    components/    Shared layout and dashboard components
    context/       Authentication state
    lib/           API and Supabase clients
    pages/         Application screens
    router/        Protected application routes
  public/          Static assets
supabase/
  migrations/      SQL bootstrap and feature migrations
```

## Local setup

### Prerequisites

- Node.js and npm
- Python 3.10 or newer
- A Supabase project

### Configure Supabase

Apply the SQL files in `supabase/migrations/` in numeric order (`001` through `004`) using the Supabase SQL Editor. These create the application tables, seed schemes and eligibility rules, and set up saved eligibility history.

Create local environment files; do not commit credentials.

`frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<publishable-or-anon-key>
```

`backend/.env`:

```env
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<publishable-or-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
GROQ_API_KEY=<optional>
```

Keep the service-role key on the backend only.

### Install and run

In one terminal, start the API:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In another terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend at `http://localhost:5173`. The FastAPI interactive docs are at `http://127.0.0.1:8000/api/docs`. To create a production frontend bundle, run `npm run build` from `frontend/`.

## Screenshots

Add screenshots to `docs/screenshots/` and replace these placeholders when available.

<!-- Screenshot placeholder: docs/screenshots/dashboard.png -->
![Dashboard screenshot placeholder](docs/screenshots/dashboard.png)

<!-- Screenshot placeholder: docs/screenshots/schemes.png -->
![Government schemes screenshot placeholder](docs/screenshots/schemes.png)

<!-- Screenshot placeholder: docs/screenshots/eligibility.png -->
![Eligibility results screenshot placeholder](docs/screenshots/eligibility.png)

## Future work

- Complete the document upload, listing, and deletion workflow with Supabase Storage.
- Add eligibility rule coverage for the remaining seeded schemes.
- Add automated frontend and backend tests.
- Prepare deployment configuration and production environment guidance.
