# Validation Notes

Validation run in Hermes container on 2026-06-17 for the expanded Agentic OS MVP+ branch.

## Passed

```bash
python -m compileall backend
```

Result: passed.

```bash
AGENTIC_OS_ENVIRONMENT=development AGENTIC_OS_DATA_DIR=/tmp/agentic-os-pytest-full2 python -m pytest -q
```

Result: `3 passed, 2 warnings`.

```bash
cd frontend
npm install
npm run build
```

Result: Vite production build completed successfully.

```bash
PYTHONPATH=/root/work/agentic-os-full \
AGENTIC_OS_DATA_DIR=/tmp/agentic-os-test-full \
AGENTIC_OS_ENVIRONMENT=development \
AGENTIC_OS_PUBLIC_URL=http://0.0.0.0:3737 \
uvicorn backend.app.main:app --host 0.0.0.0 --port 3737
```

Health probe result:

```json
{
  "status": "healthy",
  "app": "Agentic OS",
  "bind_host": "0.0.0.0",
  "public_url": "http://0.0.0.0:3737",
  "data_dir": "/tmp/agentic-os-test-full",
  "sqlite_path": "/tmp/agentic-os-test-full/agentic-os.db"
}
```

SQLite DB was created at `/tmp/agentic-os-test-full/agentic-os.db`.

## Synology/LAN note

The app binds to `0.0.0.0:3737`. In Synology host networking, browser access should use:

```text
http://<SYNOLOGY_LAN_IP>:3737
```

Do not use `127.0.0.1` from another LAN device; that points to the client device.

## Not run in this Hermes container

```bash
docker build -t agentic-os:local .
docker run --rm --network host -e AGENTIC_OS_ADMIN_TOKEN=*** -e AGENTIC_OS_DATA_DIR=/data -v /tmp/agentic-os-test:/data agentic-os:local
```

Blocked because Docker CLI is not installed in this Hermes execution environment (`docker: command not found`). The repo includes `Dockerfile` and `docker-compose.yml` with `network_mode: "host"` for Synology validation.
