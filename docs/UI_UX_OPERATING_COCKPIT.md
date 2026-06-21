# Agentic OS UI/UX Operating Cockpit

## Purpose

This implementation turns Agentic OS from disconnected dashboard panels into a connected local-first AI operations cockpit.

The UI follows this operating sequence:

```text
Space -> Agent -> Provider/model -> Workspace -> Memory -> Skills/MCP -> Work Order -> Approval -> Run/action -> Artifact/Audit
```

## Implemented surfaces

### Mission Control

Mission Control is the front door. It now shows:

- operating flow strip
- runtime readiness from backend status probes
- work orders waiting approval or running
- setup blockers with fix actions
- audit evidence timeline
- connected principles explaining why a card exists

### Agent Rooms

Each runtime has a first-class room:

- Codex
- DeepSeek
- Claude Code
- Hermes

Each room has purposeful tabs:

- Setup / Connection
- Chat / Run
- Work Orders
- Workspaces
- Memory
- Skills / MCP
- Audit
- Artifacts

Run and chat surfaces are blocked unless the backend reports a real action path. This prevents fake green states.

### Workspaces

Workspaces are presented as permission boundaries. Each workspace shows path/repo context, allowed agents, allowed commands, memory scopes, linked work orders, and the reminder that registration does not grant execution.

### Memory

Memory is scoped context, not a dump bucket. The UI explains global, agent, workspace, and project scopes and provides a scoped ingestion form.

### Skills / MCP Hub

Skills and MCP entries are shown as operating packages that can be attached to work orders only when their runtime/tool route and validation path are clear.

### Audit

Audit is shown as a human-readable evidence timeline with filters and optional raw detail expansion. Raw JSON is not the primary view.

## Runtime honesty

The UI uses backend data for readiness:

- `systems/status` for runtime readiness
- `kanban/tasks` for structured work orders
- `settings/effective` for agents, workspaces, skills, and capability manifests
- `memory` for scoped context
- `audit` for evidence events

Static configuration is not treated as readiness. Blocked agents show blocker copy and setup actions.

## Rollback

Rollback is safe because this is a frontend/docs pass. Revert the changed frontend pages/components and docs, then rebuild.

## Validation

Required validation commands:

```bash
python3 -m compileall backend
npm --prefix frontend run build
```
