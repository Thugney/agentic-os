# Work Order Runtime Path

Draw.io file: [`work-order-runtime.drawio`](work-order-runtime.drawio)

## Mermaid

```mermaid
flowchart LR
  Operator[Robel / local operator] --> UI[Work Orders UI]
  UI -->|GET runtime adapters| RuntimeAPI[FastAPI runtime adapter routes]
  UI -->|POST work order| WorkAPI[FastAPI work-order routes]
  RuntimeAPI --> Registry[Runtime adapter registry]
  Registry --> CodexProbe[codex CLI probe]
  Registry --> DeepSeekProbe[OpenAI-compatible endpoint probe]
  Registry --> HermesProbe[Hermes endpoint probe]
  Registry --> ClaudeProbe[claude CLI probe]
  WorkAPI --> Tasks[(kanban_tasks as work_orders)]
  WorkAPI --> Audit[(audit_log)]
  WorkAPI --> Approve[approval gate]
  Approve -->|approved + ready| Run[run_work_order]
  Approve -->|not approved / not ready| Block[blocked with reason]
  Run --> Codex[Codex background session]
  Run --> DeepSeek[DeepSeek chat thread]
  Run --> Block
  Codex --> Sessions[(codex_sessions)]
  DeepSeek --> Chats[(chat_threads/messages)]
  Sessions --> Artifacts[logs / session refs]
  Chats --> Artifacts
```

## What is real in this implementation

- The Work Orders page creates records through the backend, not local-only state.
- Runtime readiness is probed by the backend adapter registry and shown in the UI.
- Create, approve, run, blocked-run, and update actions write audit records.
- Codex work orders start a real background Codex session when the `codex` CLI and workspace are available.
- DeepSeek work orders call the existing chat service and link the resulting thread.
- Hermes, Claude, and MCP registry entries are shown honestly as blocked/not implemented unless their executable or endpoint is available.

## Safety properties

- Work orders do not auto-run when created.
- Run requires `approval_state=approved`.
- Codex run still goes through workspace allowlisting and the existing Codex danger-pattern checks.
- If a runtime is not ready, the backend blocks the run and writes an audit event with the reason.
- The UI disables run buttons until both approval and runtime readiness are true.

## Main failure modes

| Failure | Expected behavior |
| --- | --- |
| Missing Codex CLI | Runtime adapter reports blocked; run returns HTTP 400 and audit event. |
| Missing DeepSeek/OpenWebUI endpoint | Adapter reports blocked with endpoint/config reason. |
| Work order not approved | Run is blocked and audit event records approval requirement. |
| Unsupported adapter path | Run is blocked rather than pretending execution happened. |
| Workspace mismatch | Codex path blocks through workspace allowlist validation. |
