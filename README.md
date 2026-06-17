# Agentic OS

Agentic OS is Robel's local-first AI operations control plane: **one process, every door**. It unifies local agent status, chat history, Codex sessions, workspaces, Kanban, memory, skills, settings, goal mode scaffolding, MCP registry, and audit logs in a single FastAPI + React container.

## MVP+ stack

- Backend: Python FastAPI under `backend/`
- Frontend: React + Vite + TypeScript under `frontend/`
- DB: SQLite at `/data/agentic-os.db`
- Static frontend served by FastAPI in production
- API prefix: `/api`
- Health: `/api/health`
- Default port: `3737`
- Production bind host: `0.0.0.0`

## Critical Synology LAN access

Inside the container, `127.0.0.1` only means the container/host loopback. For browser access from another LAN device, use the NAS LAN IP:

```text
http://<SYNOLOGY_LAN_IP>:3737
```

The Docker image starts Uvicorn with `--host 0.0.0.0`, and `docker-compose.yml` uses:

```yaml
network_mode: "host"
```

So Synology host networking exposes Agentic OS directly on the NAS IP and port 3737. Local service URLs such as OpenWebUI/Hermes remain configurable by env var.

## Synology Docker Manager quick start

```bash
git clone https://github.com/Thugney/agentic-os.git
cd agentic-os
git checkout feature/agentic-os-mvp
cp .env.example .env
# edit AGENTIC_OS_ADMIN_TOKEN and AGENTIC_OS_PUBLIC_URL=http://<SYNOLOGY_LAN_IP>:3737
docker compose up -d --build
```

Persistent data path:

```text
/volume2/docker/agentic-os:/data
```

## Required production setting

`AGENTIC_OS_ADMIN_TOKEN` is required in production. The UI stores it only in browser localStorage and sends it as `x-admin-token` for protected actions.

## Implemented control-plane areas

- Mission Control with active process and failed-action telemetry
- Agent registry from YAML
- Chat threads/messages persisted in SQLite
- OpenAI-compatible chat adapter for DeepSeek/OpenWebUI
- Codex sessions with live log polling, cancel, git diff/test result/artifacts, confirm-only commit/push endpoints
- Workspace registry and command allowlist enforcement
- Local Kanban
- Local Memory
- Skills Hub
- Audit timeline and JSONL export
- Settings effective config view and safe registry update endpoint
- Goal Mode scaffold
- MCP registry scaffold
- Claude Code disabled placeholder

## Validation

```bash
python -m compileall backend
pytest
npm --prefix frontend install
npm --prefix frontend run build
docker build -t agentic-os:local .
docker run --rm --network host -e AGENTIC_OS_ADMIN_TOKEN=*** -e AGENTIC_OS_DATA_DIR=/data -v /tmp/agentic-os-test:/data agentic-os:local
curl http://127.0.0.1:3737/api/health
```

For LAN validation from another machine:

```bash
curl http://<SYNOLOGY_LAN_IP>:3737/api/health
```

See `docs/VALIDATION.md` for the validation performed during this build.
