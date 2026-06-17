# Synology Docker

The MVP+ is built for Synology Docker Manager / Container Manager using host networking.

```yaml
network_mode: "host"
volumes:
  - /volume2/docker/agentic-os:/data
```

## LAN access: use the NAS IP, not 127.0.0.1

Agentic OS binds to `0.0.0.0:3737` in production. From a laptop/phone/desktop on the LAN, open:

```text
http://<SYNOLOGY_LAN_IP>:3737
```

Do **not** use `http://127.0.0.1:3737` from another device. That points to the client device itself. `127.0.0.1` is only valid when curling from the Synology host/container itself.

Set this in `.env` for display/config clarity:

```env
AGENTIC_OS_PUBLIC_URL=http://<SYNOLOGY_LAN_IP>:3737
```

## Setup

```bash
mkdir -p /volume2/docker/agentic-os
git clone https://github.com/Thugney/agentic-os.git
cd agentic-os
git checkout feature/agentic-os-mvp
cp .env.example .env
# edit AGENTIC_OS_ADMIN_TOKEN and AGENTIC_OS_PUBLIC_URL
docker compose up -d --build
```

Because host networking is used, do not use Docker service DNS names for local dependencies. Configure all external services by URL/env var:

- `OPENWEBUI_URL=http://<host-or-service-ip>:18790`
- `HERMES_URL=http://<pi-ip>:9119`

Backup SQLite:

```bash
cp /volume2/docker/agentic-os/agentic-os.db /volume2/docker/agentic-os/backup-agentic-os-$(date +%F-%H%M).db
```
