# Courman

Courman is a course management system for administering courses, course staff,
student rosters, grading components, grading assignments, and score sheets. The
project is organized as a Django API backend and a Next.js frontend.

## Overview

Courman provides a staff-oriented administration panel and a session-authenticated
API for course operations. The backend exposes a Django Ninja API under `/api/`,
while the frontend proxies browser API requests through Next.js so session
cookies remain first-party during local development.

Primary capabilities include:

- User registration, login, logout, and current-user session lookup.
- Staff-managed users, roles, and role actions.
- User profile management with optional avatar upload.
- Course creation and staff assignment for professors, head TAs, and TAs.
- Course roster management for enrolled students.
- Grading components, grading task assignment, grading sheets, sub-grades, score
  entry, comments, and bulk score updates.

## Repository Structure

```text
.
|-- courmanbackend/      # Django 6 and Django Ninja API
|-- courmanfrontend/     # Next.js 16 frontend
|-- docker-compose.yml   # Root compose file including backend and frontend stacks
|-- README.md
`-- LICENSE
```

## Technology Stack

Backend:

- Python 3.14
- Django 6
- Django Ninja
- PostgreSQL
- Redis
- MinIO or S3-compatible object storage
- WhiteNoise for static files
- uv for Python dependency management

Frontend:

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- pnpm
- shadcn-style UI components

## Quick Start with Docker

The recommended development setup is Docker Compose. It starts the backend,
frontend, PostgreSQL, Redis, and MinIO services.

```bash
docker compose up --build
```

After the services are ready:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/`
- Django admin: `http://localhost:8000/admin/`
- MinIO console: `http://localhost:9001`

The backend container runs database migrations, seeds default course roles, seeds
an administrator account, and collects static files at startup.

Default administrator credentials for the Docker setup are:

```text
Username: admin
Password: Admin@123
Email: admin@example.com
```

These values can be overridden with `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and
`ADMIN_EMAIL`.

## Local Development

Docker is preferred because the full application depends on PostgreSQL, Redis,
and S3-compatible storage. The backend can also run locally with SQLite,
in-memory cache, and local media storage when the related service environment
variables are omitted.

### Backend

```bash
cd courmanbackend
uv sync
uv run python manage.py migrate
uv run python manage.py seed_roles
uv run python manage.py seed_admin
uv run python manage.py runserver 127.0.0.1:8000
```

The backend reads local environment variables from `courmanbackend/.env` when
the file exists.

Common backend environment variables:

```text
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
POSTGRES_DB=courman
POSTGRES_USER=courman
POSTGRES_PASSWORD=courman
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
REDIS_URL=redis://127.0.0.1:6379/0
AWS_S3_ENDPOINT_URL=http://127.0.0.1:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=courman
AWS_S3_USE_SSL=false
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@123
ADMIN_EMAIL=admin@example.com
```

When `POSTGRES_HOST` is not set, Django uses SQLite. When `REDIS_URL` is not
set, Django uses the local-memory cache. When `AWS_S3_ENDPOINT_URL` is not set,
uploaded media is stored on local disk.

### Frontend

```bash
cd courmanfrontend
pnpm install
cp .env.example .env.local
pnpm dev
```

The frontend development server runs at `http://localhost:3000`.

Important frontend environment variables:

```text
NEXT_PUBLIC_API_URL=/api
BACKEND_URL=http://127.0.0.1:8000
```

`NEXT_PUBLIC_API_URL` is the browser-facing API base path. `BACKEND_URL` is used
server-side by Next.js rewrites to proxy `/api/*` requests to Django.

## API

The backend API is registered at `/api/`. Major route groups are:

- `/api/iam/auth/` for registration, login, logout, and current-user lookup.
- `/api/iam/users/` for staff-managed user administration and user lookup.
- `/api/iam/roles/` for role management.
- `/api/iam/actions/` for role-action management.
- `/api/profiles/` for profile self-service and staff profile lookup.
- `/api/courses/` for courses, course staff, and student rosters.
- `/api/grading/` for grading components, tasks, sheets, sub-grades, and scores.

Django Ninja also exposes generated API documentation from the API root when the
development server is running.

## Testing and Quality Checks

Run backend tests from the backend directory:

```bash
cd courmanbackend
uv run python manage.py test
```

Run frontend linting from the frontend directory:

```bash
cd courmanfrontend
pnpm lint
```

Build the frontend from the frontend directory:

```bash
cd courmanfrontend
pnpm build
```

## License

See `LICENSE` for licensing information.
