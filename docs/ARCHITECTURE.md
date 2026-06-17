# Architecture

Agentic OS MVP is intentionally one container: FastAPI serves `/api` and the built Vite frontend. SQLite stores local state in `/data/agentic-os.db`. YAML files under `config/` define agents, providers, workspaces, and skills.

## Runtime modules

- `core`: settings, logging, token middleware, redaction.
- `db`: SQLite connection and idempotent migrations.
- `services`: config, audit, chat, Codex, workspace logic.
- `adapters`: provider-specific clients such as OpenAI-compatible chat.
- `api`: route definitions.

No Redis, Postgres, Kubernetes, Supabase, or microservices are required for MVP.
