# Repository Guidelines

## Project Structure & Module Organization

AidFlow AI is a React/Vite frontend with a FastAPI backend and Supabase data layer. Frontend pages, shared components, auth context, routing, and API clients live under `frontend/src/`; static assets are in `frontend/public/` and `frontend/src/assets/`. Backend routes are in `backend/app/routers/`, with schemas, services, utilities, configuration, and dependencies in sibling modules. Supabase bootstrap SQL is under `supabase/migrations/`; Alembic migrations are in `backend/alembic/versions/`. Keep changes in the appropriate layer and update SQL and backend schema together when changing persisted data.

## Build, Test, and Development Commands

- `cd frontend && npm install && npm run dev` starts the Vite development server, usually at `http://localhost:5173`.
- `cd frontend && npm run build` creates the production frontend in `frontend/dist/`; `npm run preview` serves that build locally.
- `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` prepares the API environment.
- `cd backend && uvicorn app.main:app --reload` runs the API at `http://localhost:8000`.
- `docker compose up --build` starts the configured services when the required environment variables are set.

## Coding Style & Naming Conventions

Follow existing patterns: four-space indentation and `snake_case` for Python modules, functions, and variables; React components and page files use `PascalCase`, while JavaScript variables and functions use `camelCase`. Keep API request and response shapes aligned with `backend/app/schemas/` and frontend consumers. No formatter or linter is configured in the repository, so keep diffs focused and consistent with adjacent code.

## Testing Guidelines

No project test suite or test command is currently configured. For frontend changes, run `npm run build`. For backend changes, start the API and exercise affected endpoints through the local API docs at `/docs`; add automated tests only when introducing a test setup consistent with the project.

## Commit & Pull Request Guidelines

Recent commits use short, imperative descriptions, with some Conventional Commit prefixes such as `feat:`. Keep commits focused and use a concise subject (for example, `fix: stabilize profile lookup`). Pull requests should explain the behavior changed, list verification steps, link related issues when available, and include screenshots for visible UI changes.

## Security & Configuration

Use local environment files for Supabase, database, and API credentials; never commit secrets. Configure frontend and backend environment values according to their existing `.env` usage and `docker-compose.yml`. Treat Supabase migrations as deployable changes: review SQL and apply it to the intended project before relying on the updated schema.
