# Security Model

MVP is local-admin single-user. It is not multi-user RBAC.

- Production requires `AGENTIC_OS_ADMIN_TOKEN`.
- Write/action endpoints and log/audit reads require the token.
- Secrets are provided through env vars only.
- Secret-looking fields are redacted before audit metadata is stored.
- Codex runs only in registered workspaces.
- Dangerous task patterns and `--yolo` are refused.
- Audit log captures timestamp, actor, action, target agent, workspace, command type, status, error, git branch, and git commit when available.
