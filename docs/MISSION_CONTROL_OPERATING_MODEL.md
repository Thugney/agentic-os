# Mission-Control-inspired operating model for Agentic OS

## Decision

Agentic OS should lean toward the **operating model** of `builderz-labs/mission-control`, not copy its code, branding, exact UI, or framework choices.

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
| Task dispatch center | Work starts from tasks/work orders, not random chat tabs. |
| Real-time activity | Running work, failures, logs, and state changes are visible without hunting. |
| Quality gates | Completion requires review/sign-off instead of blind autonomous action. |
| Skills hub | Reusable procedures become controlled packages. |
| Memory visibility | Agent context is inspectable, not hidden. |
| Security/trust panels | Operators see risk, secrets, permissions, and audit posture. |
| Local-first SQLite deployment | Simple, self-hosted, and recoverable. |

Agentic OS already has the right local-first stack: FastAPI, React/Vite, SQLite, YAML manifests, Docker, and room-based runtime surfaces. The missing piece is **operating sequence coherence**.

## What not to copy

Do not clone Mission Control's exact UI, language, screenshots, names, branding, or layout. Agentic OS should keep its own identity:

- **One process, every door**
- Robel's local AI operations cockpit
- Runtime adapter control plane
- Workspace-safe automation studio

Do not chase all Mission Control panels. That would recreate fragmentation inside Agentic OS.

Also do not copy:

- Next.js-specific middleware or project structure.
- OpenClaw/gateway-specific adapter assumptions.
- Framework-specific adapter lists before a generic adapter contract exists.
- Huge monolithic frontend store files.
- Dashboard panels that summarize things Agentic OS cannot actually operate yet.

## Product north star

Every serious action should follow this path:

```text
Intent -> Work order -> Agent/runtime -> Workspace -> Memory/skills/tools -> Approval gate -> Run -> Logs/artifacts -> Audit -> Review/next action
```

The UI should make this path obvious from the first screen.

## P0 architecture priorities

### 1. Unified runtime adapter protocol

Rooms must not become separate mini-apps. Codex, DeepSeek, Hermes, Claude Code, and future agents should implement one backend adapter protocol.

Minimum adapter lifecycle:

```text
register -> heartbeat -> describe capabilities -> accept assignment -> stream/report progress -> complete/fail -> disconnect
```

Each adapter should expose:

- runtime id
- display name
- type: `local_cli`, `cloud_api`, `custom_endpoint`, `remote_api`, `remote_ssh`, `disabled`
- readiness probe
- supported actions
- required configuration
- scoped capabilities
- last heartbeat
- last error
- rate/capacity limits

This lets the UI show honest readiness instead of treating static YAML as proof of connection.

### 2. Auth/security gate as ASGI middleware

Security should not be scattered across route handlers. Add a central FastAPI/ASGI gate for:

- admin token validation
- constant-time token comparison
- host allowlist
- CORS/Origin/CSRF protection for mutating routes
- security headers
- per-agent API-key detection
- rate-limit headers
- audit correlation id

This is a direct improvement over per-route checks.

### 3. Agent-scoped API keys

Do not rely on one global admin key forever. Add scoped keys for adapters/agents.

Initial scopes should stay small:

| Scope | Meaning |
| --- | --- |
| `read` | read status/config allowed to that agent |
| `write` | create/update allowed assigned resources |
| `agent:self` | heartbeat/report only for that agent identity |
| `admin` | full operator/admin actions |

Each key should support:

- prefix identifying Agentic OS key type
- scope list
- optional agent binding
- expiry
- last used timestamp
- per-key rate limit
- revocation

### 4. Single frontend store composed from slices

The frontend should have one coherent application state model, not isolated state per room.

Use one composed store with slices such as:

- agents/runtimes
- work orders/Kanban
- sessions/logs
- memory
- skills/capabilities
- audit/activity
- settings
- UI preferences

Persist only safe UI preferences locally. Never persist secrets in frontend store beyond the existing explicit browser token pattern.

## Recommended information architecture

### 1. Mission Control front door

Mission Control should show:

- agent/runtime health: Hermes, Codex, DeepSeek/OpenWebUI, Claude Code
- active runs and queued work
- failed actions requiring attention
- pending approvals
- recent artifacts
- security/trust posture
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

Recommended workflow columns:

```text
Inbox -> Assigned -> In progress -> Review -> Done -> Failed
```

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

### Slice 1: Work Order Runtime Path

Goal: turn Agentic OS from a dashboard into a control plane.

Deliverables:

1. Extend work-order/Kanban data model with:
   - `agent`
   - `capability_id`
   - `workspace`
   - `memory_scope`
   - `approval_state`
   - `priority`
   - `due_at`
   - `validation_command`
   - `artifact_refs`
   - `run_session_id`
2. Add a `Create Work Order` form that uses dropdowns from live config:
   - agents/runtimes from adapter registry
   - workspaces from workspace service
   - capabilities from capability manifests
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
   - assigned
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

### Queue dispatch and quality gates

After work orders exist, add orchestration behavior:

- queue-based dispatch
- atomic task claiming
- priority + due date + created date ordering
- per-agent capacity control
- stale task recovery when an adapter goes offline
- review/quality gate before marking sensitive work done

Do not auto-run risky tasks by default. Auto-dispatch can be added per capability after approval policy is explicit.

## Third implementation slice

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

## Fourth implementation slice

### Event stream and live cockpit

Use SSE first. WebSockets can wait.

Broadcast events such as:

- `agent.status_changed`
- `work_order.created`
- `work_order.updated`
- `work_order.started`
- `work_order.completed`
- `work_order.failed`
- `artifact.created`
- `approval.requested`
- `security.event`

The frontend should pause expensive polling when the tab is inactive and resume on visibility change.

## Fifth implementation slice

### Security and trust panels

After audit events are real, build panels that summarize real state:

- posture score
- per-agent trust score
- failed auth attempts
- blocked dangerous actions
- secret redaction/security scan events
- tool/action frequency
- error rate by adapter
- drift from normal behavior

The panel must not be decorative. It should link directly to audit events and remediation actions.

## Later differentiators

### Skills Hub with scanner

Before installing or enabling a skill, scan for:

- prompt injection patterns
- credential-looking content
- dangerous shell commands
- data exfiltration patterns
- obfuscated content

Support Hermes skills and plain skill directories before external registries.

### Memory knowledge graph

Visualize memory, sessions, files, workspaces, and artifacts as relationships after the underlying memory permissions are clear.

### Evaluation framework

Add layers gradually:

1. output evals for generated artifacts
2. trace evals for loops/retries/convergence
3. tool/component reliability metrics
4. drift detection over rolling baseline

Trigger evals on task completion or failed review gates.

### CI and release quality

Add minimum CI before treating the repo as serious/public:

- backend compile/test
- frontend build/lint
- API contract check
- security scan for secrets
- screenshot smoke test for key pages
- Docker build

## Architecture guardrails

- Keep MVP local-first: FastAPI + React + SQLite.
- Use adapters for every runtime; do not make UI call tools directly.
- Never store provider secrets in YAML or committed files.
- Keep action buttons disabled unless the backend action path exists.
- Record audit for every meaningful operation.
- Require explicit approval before commit, push, destructive commands, or external delivery.
- Use raw JSON only as advanced diagnostics.
- Build tools and automations, not passive dashboards.

## Best move now

Do **not** rebuild Agentic OS as a Mission Control clone.

Do **recenter Agentic OS around work orders, runtime adapters, scoped security, and audit**:

```text
Mission Control front door
  -> create work order
  -> choose capability + runtime + workspace + memory
  -> approve/run
  -> logs/artifacts/audit
  -> review/next action
```

This directly solves fragmentation while preserving Robel's local-first, action-oriented operating style.
