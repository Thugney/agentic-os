# Validation Notes

Validation run in Hermes container on 2026-06-17.

## Passed

```bash
python -m compileall backend
```

Result: passed.

```bash
AGENTIC_OS_ENVIRONMENT=development AGENTIC_OS_DATA_DIR=/tmp/agentic-os-pytest python -m pytest -q
```

Result: `1 passed, 2 warnings`.

```bash
npm install
npm run build
```

Result: Vite production build completed successfully.

```bash
AGENTIC_OS_ADMIN_TOKEN=*** AGENTIC_OS_DATA_DIR=/tmp/agentic-os-test AGENTIC_OS_ENVIRONMENT=production uvicorn backend.app.main:app --host 127.0.0.1 --port 3737
curl http://127.0.0.1:3737/api/health
```

Result:

```json
{
  "status": "healthy",
  "app": "Agentic OS",
  "data_dir": "/tmp/agentic-os-test",
  "sqlite_path": "/tmp/agentic-os-test/agentic-os.db"
}
```

SQLite DB was created at `/tmp/agentic-os-test/agentic-os.db`.

## Not run in this Hermes container

```bash
docker build -t agentic-os:local .
docker run --rm --network host -e AGENTIC_OS_ADMIN_TOKEN=*** -e AGENTIC_OS_DATA_DIR=/data -v /tmp/agentic-os-test:/data agentic-os:local
```

Blocked because Docker CLI is not installed in this Hermes execution environment (`docker: command not found`). The repo includes `Dockerfile` and `docker-compose.yml` with `network_mode: "host"` for Synology validation.
