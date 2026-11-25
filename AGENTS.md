# Repository Guidelines

## Project Structure

AidFlow AI is a React/Vite frontend, a FastAPI backend, and a Supabase data layer. Frontend screens are in `frontend/src/pages/`; shared UI is in `components/`, auth state in `context/`, API clients in `lib/`, and routing in `router/`. Backend endpoints, schemas, services, and utilities live under `backend/app/`. Supabase SQL history is in `supabase/migrations/`.

Keep changes within the layer that owns the behavior. When changing persisted data, keep SQL, backend models, and frontend consumers aligned. Supabase migrations are the active schema source.

## Development and Verification

- `cd frontend && npm install && npm run dev` starts the Vite app.
- `cd frontend && npm run build` checks and bundles the production frontend.
- `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` prepares the API environment.
- `cd backend && uvicorn app.main:app --reload` starts FastAPI.
- `cd backend && python -m unittest discover -s tests -v` runs backend unit tests.
- `docker compose up --build` starts the containerized app when environment values are configured.

There is no configured frontend lint or formatting command. Keep imports and formatting consistent with adjacent code.

## Style and Naming

Use four spaces and `snake_case` for Python files, functions, and variables. Use `PascalCase` for React components/pages and `camelCase` for frontend variables and functions. Keep reusable UI in `components/`; keep database or provider logic out of page components.

## Data, Security, and Configuration

Store local settings in ignored `.env` files. Frontend variables use the `VITE_` prefix and may contain only public values. Keep Supabase service-role credentials on the backend. Backend code using the service client must scope user records to the authenticated user. Enable RLS and add ownership policies for new user-owned tables.

Review migrations before applying them. Do not rewrite already-applied migrations; add a numbered migration for schema changes.

## Pull Requests

Use a concise imperative or Conventional Commit subject, such as `fix: scope assistant history by user`. Describe behavior changes, list verification steps, and include screenshots for visible UI changes. Do not commit credentials, generated builds, caches, or local environment files.
