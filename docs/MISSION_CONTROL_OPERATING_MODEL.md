# Mission-Control-inspired operating model for Agentic OS

## Decision

Agentic OS should lean toward the **operating model** of `builderz-labs/mission-control`, not copy its code, branding, or exact UI.

The core problem to solve is Robel's fragmentation:

```text
Hermes + Codex + DeepSeek/OpenWebUI + Claude Code + workspaces + memory + skills + tasks + schedules + audit
```

Today these exist as separate tools and rooms. The product move is to make Agentic OS the **single local control plane** where every agent action starts as a scoped work order, runs through a runtime adapter, and leaves an auditable artifact.

## What Mission Control proves

Mission Control is useful because it is not just a pretty dashboard. Its strongest patterns are:

| Pattern | Why it matters for Agentic OS |
| --- | --- |
| Agent fleet overview | Operators see which agents exist, their status, and what they are doing. |
| Task dispatch center | Work starts from tasks, not random chat tabs. |
| Real-time activity | Running work, failures, logs, and state changes are visible without hunting. |
| Quality gates | Completion requires review/sign-off instead of blind autonomous action. |
| Skills hub | Reusable procedures become controlled packages. |
| Memory visibility | Agent context is inspectable, not hidden. |
| Security/trust panels | Operators see risk, secrets, permissions, and audit posture. |
| Local-first SQLite deployment | Simple, self-hosted, and recoverable. |

Agentic OS already has the right local-first stack: FastAPI, React/Vite, SQLite, YAML manifests, Docker, and room-based runtime surfaces. The missing piece is **operating sequence coherence**.

## What not to copy

Do not clone Mission Control's exact UI, language, screenshots, names, or layout. Agentic OS should keep its own identity:

- **One process, every door**
- Robel's local AI operations cockpit
- Runtime adapter control plane
- Workspace-safe automation studio

Do not chase all 32 Mission Control panels. That would recreate fragmentation inside Agentic OS.

## Product north star

Every serious action should follow this path:

```text
Intent -> Work order -> Agent/runtime -> Workspace -> Memory/skills/tools -> Approval gate -> Run -> Logs/artifacts -> Audit -> Review/next action
```

The UI should make this path obvious from the first screen.

## Recommended IA: one cockpit, not many disconnected tabs

### 1. Mission Control front door

Mission Control should show:

- agent/runtime health: Hermes, Codex, DeepSeek/OpenWebUI, Claude Code
- active runs and queued work
- failed actions requiring attention
- pending approvals
- recent artifacts
- cost/token summary when available
- quick actions: create work order, start chat, run Codex, schedule Hermes job

### 2. Work Orders as the center of gravity

Kanban should become the central dispatch system. A task is not a title-only card. It should include:

- title and description
- selected agent/runtime
- workspace boundary
- memory scope
- skill/capability package
- approval policy
- validation command
- schedule intent if recurring
- linked chat/session/log/artifact
- audit state

Creating a task must not secretly execute it. Execution should require a visible **Run** or **Approve** action.

### 3. Agent rooms as runtime detail pages

Keep rooms, but make them subordinate to work orders:

- **Hermes Room:** orchestration, cron, profiles, tools, Telegram/gateway actions, Kanban bridge.
- **Codex Room:** code/build/review execution with workspace allowlist, logs, diff, tests, commit/push approvals.
- **DeepSeek Room:** low-cost reasoning/chat/research with model selector and safe context limits.
- **Claude Room:** premium/subscription CLI lane, disabled until real adapter path is verified.

### 4. Capabilities as packages

`config/capabilities.yaml` should become the manifest layer for reusable workflows:

- allowed agent/runtime
- allowed model/provider
- allowed workspace
- allowed tools/MCPs
- memory scope
- prompt policy
- inputs/outputs
- approval gates
- audit policy
- validation command
- rollback notes

This is stronger than hardcoding random buttons across pages.

### 5. Canvas should visualize reality only

Canvas should remain view-only until execution editing is real. It should show:

```text
Capability -> Agent -> Model -> Workspace -> Memory -> Tools/MCP -> Approval -> Artifact -> Audit
```

Do not add fake drag/drop workflow editing before manifest editing, validation, and approvals are implemented.

## First implementation slice

Build this before adding more panels:

### Slice 1: Work Order Runtime Path

Goal: turn Agentic OS from a dashboard into a control plane.

Deliverables:

1. Extend `kanban_tasks` / work-order model with:
   - `agent`
   - `capability_id`
   - `workspace`
   - `memory_scope`
   - `approval_state`
   - `validation_command`
   - `artifact_refs`
   - `run_session_id`
2. Add a `Create Work Order` form that uses dropdowns from live config:
   - agents from `/api/agents`
   - workspaces from `/api/workspaces`
   - capabilities from `/api/capabilities`
   - memory scopes from supported values
3. Add a work-order detail drawer/page:
   - intent
   - runtime readiness
   - workspace boundary
   - approval gates
   - linked logs/artifacts/audit events
4. Add explicit run adapters:
   - Codex: can run when workspace + capability are valid
   - DeepSeek: chat/research task path
   - Hermes: schedule/orchestration remains marked not integrated unless callable route exists
   - Claude: setup blocker until subscription CLI adapter exists
5. Add audit event for every state transition:
   - created
   - approved
   - started
   - completed/failed
   - artifact linked

Success criteria:

- A user can create one work order from Mission Control.
- It appears in Kanban.
- It can be opened and inspected.
- If runtime is ready, it can launch a real Codex/DeepSeek action.
- If runtime is not ready, UI shows the exact setup blocker.
- Audit records prove what happened.

## Second implementation slice

### Runtime Connection Studio

Make each runtime connection-first:

- Save connection settings without secrets in repo.
- Test adapter boundary.
- Show implemented vs future capabilities.
- Disable action buttons when action path is not real.

Priority order:

1. DeepSeek cloud/OpenAI-compatible model list and chat path.
2. Codex subscription CLI execution path.
3. Hermes callable API bridge for chat/action/cron/Kanban capabilities.
4. Claude Code subscription CLI adapter.

## Third implementation slice

### Operator-quality dashboards

Only after work orders and runtime adapters are real, add Mission-Control-like panels:

- cost/token tracing
- security/trust posture
- secret detection results
- recurring jobs
- webhooks/integrations
- eval/quality gates

These should summarize real events, not become passive decoration.

## Architecture guardrails

- Keep MVP local-first: FastAPI + React + SQLite.
- Use adapters for every runtime; do not make UI call tools directly.
- Never store provider secrets in YAML or committed files.
- Keep action buttons disabled unless the backend action path exists.
- Record audit for every meaningful operation.
- Require explicit approval before commit, push, destructive commands, or external delivery.
- Use raw JSON only as advanced diagnostics.

## Best move now

Do **not** rebuild Agentic OS as a Mission Control clone.

Do **recenter Agentic OS around work orders and runtime adapters**:

```text
Mission Control front door
  -> create work order
  -> choose capability + runtime + workspace + memory
  -> approve/run
  -> logs/artifacts/audit
  -> review/next action
```

This directly solves fragmentation while preserving Robel's local-first, action-oriented operating style.
