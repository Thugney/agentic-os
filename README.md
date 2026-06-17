# Agentic OS

Agentic OS is Robel's local-first AI operations control plane: **one process, every door**. It unifies local agent status, chat history, Codex sessions, workspaces, Kanban, memory, skills, settings, and audit logs in a single FastAPI + React container.

## MVP stack

- Backend: Python FastAPI under `backend/`
- Frontend: React + Vite + TypeScript under `frontend/`
- DB: SQLite at `/data/agentic-os.db`
- Static frontend served by FastAPI in production
- API prefix: `/api`
- Health: `/api/health`
- Default port: `3737`

## Synology Docker Manager quick start

```bash
git clone https://github.com/Thugney/agentic-os.git
cd agentic-os
cp .env.example .env
# edit AGENTIC_OS_ADMIN_TOKEN and local service URLs
docker compose up -d --build
```

The compose file uses host networking and persists data to:

```text
/volume2/docker/agentic-os:/data
```

Open `http://127.0.0.1:3737` or the Synology host IP on port 3737.

## Required production setting

`AGENTIC_OS_ADMIN_TOKEN` is required in production. The UI stores it only in browser localStorage and sends it as `x-admin-token` for protected actions.

## Validation

```bash
python -m compileall backend
pytest
npm --prefix frontend install
npm --prefix frontend run build
docker build -t agentic-os:local .
docker run --rm --network host -e AGENTIC_OS_ADMIN_TOKEN=test-token -e AGENTIC_OS_DATA_DIR=/data -v /tmp/agentic-os-test:/data agentic-os:local
curl http://127.0.0.1:3737/api/health
```

See `docs/VALIDATION.md` for the validation performed during this MVP build.

## Notes

Codex runs as a subprocess in a registered workspace only. No `--yolo` is used. Commit and push require explicit future confirmation flows; MVP records sessions/logs/diffs and does not auto-commit by default.
