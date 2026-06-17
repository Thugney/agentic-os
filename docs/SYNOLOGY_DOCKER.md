# Synology Docker

The MVP is built for Synology Docker Manager / Container Manager using host networking.

```yaml
network_mode: "host"
volumes:
  - /volume2/docker/agentic-os:/data
```

Create the data directory on the NAS, copy `.env.example` to `.env`, set a long `AGENTIC_OS_ADMIN_TOKEN`, then run `docker compose up -d --build`.

Because host networking is used, do not use Docker service DNS names for local dependencies. Configure all external services by URL/env var.

Backup SQLite:

```bash
cp /volume2/docker/agentic-os/agentic-os.db /volume2/docker/agentic-os/backup-agentic-os-$(date +%F-%H%M).db
```
