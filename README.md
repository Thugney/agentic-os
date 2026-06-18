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

## Runtime configuration docs

See `docs/RUNTIME_CONNECTIONS.md` for DeepSeek API setup, live model dropdown behavior, Codex subscription CLI expectations, Claude Code subscription expectations, and Hermes API/gateway requirements.

## Required production setting

`AGENTIC_OS_ADMIN_TOKEN` is required in production. The UI stores it only in browser localStorage and sends it as `x-admin-token` for protected actions.
