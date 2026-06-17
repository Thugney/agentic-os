# Configuration

Configuration is split between environment variables and YAML registry files. Secrets stay in `.env` and are never written to SQLite.

Files:

- `config/providers.yaml`
- `config/agents.yaml`
- `config/workspaces.yaml`
- `config/skills.yaml`

Environment defaults:

- `AGENTIC_OS_APP_PORT=3737`
- `AGENTIC_OS_DATA_DIR=/data`
- `OPENWEBUI_URL=http://127.0.0.1:18790`
- `HERMES_URL=http://127.0.0.1:9119`
