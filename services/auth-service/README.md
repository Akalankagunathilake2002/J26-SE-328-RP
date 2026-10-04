# Auth Service

User accounts for the Academic-to-Industry Skill Bridge: registration, login and the current
user. Passwords are hashed with Argon2; logins return a signed JWT access token.

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Service status (`/auth/health` through the gateway) |
| `POST /auth/register` | Create an account (`full_name`, `email`, `password`) |
| `POST /auth/login` | Exchange `email` + `password` for an access token |
| `GET /auth/me` | The current user (`Authorization: Bearer <token>`) |

## Configuration

| Environment variable | Default |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://skillbridge:skillbridge@localhost:5432/auth_db` |
| `JWT_SECRET` | none — required, at least 32 characters |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |

Tables are created on startup. Add migrations (e.g. Alembic) before changing the schema.

## Run with Docker (recommended)

From the repository root:

```bash
docker compose -f infrastructure/docker-compose.yml up --build
```

The service is reached through the API gateway at http://localhost:8080/auth/… (API docs at
http://localhost:8080/auth/docs). Inside Docker it listens on port 8006; that port is not published.
PostgreSQL is reachable from your machine on port 5433 (`skillbridge` / `skillbridge`, database `auth_db`).

## Tests

The tests use a temporary SQLite database, so PostgreSQL does not need to be running.

```bash
cd services/auth-service
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```
