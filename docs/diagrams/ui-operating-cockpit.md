# UI operating cockpit diagram

```mermaid
flowchart LR
  User[Robel in browser] --> Mission[Mission Control]
  Mission --> Flow[Operating flow strip]
  Mission --> Runtime[Runtime health and blockers]
  Mission --> Work[Work Order Studio]
  Mission --> Audit[Audit timeline]

  Runtime --> Codex[Codex Room]
  Runtime --> DeepSeek[DeepSeek Room]
  Runtime --> Claude[Claude Code Room]
  Runtime --> Hermes[Hermes Room]

  Codex --> Setup[Setup and connection]
  DeepSeek --> Setup
  Claude --> Setup
  Hermes --> Setup

  Setup --> Probe[Backend readiness probe]
  Probe --> Ready{Action path ready?}
  Ready -->|yes| Run[Chat or run enabled]
  Ready -->|no| Blocked[Blocked state with fix action]

  Work --> Workspace[Workspace boundary]
  Work --> Memory[Scoped memory]
  Work --> Skills[Skills and MCP package]
  Work --> Approval[Approval gate]
  Approval --> Run
  Run --> Artifact[Artifact]
  Run --> Audit
```

## Explanation

Mission Control is the front door. Agent rooms are the control surfaces. Workspaces, memory, skills/MCP, approvals, runs, artifacts, and audit are connected through structured work orders. The UI must never imply a runtime is ready until the backend probe confirms a real action path.
