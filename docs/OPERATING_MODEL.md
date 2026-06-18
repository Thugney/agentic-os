# Agentic OS Operating Model

Agentic OS is Robel's local-first AI operations cockpit. It is not just a chat UI or passive dashboard. The core sequence is:

```text
Agent -> Provider/model -> Workspace -> Memory -> Skills/MCP -> Kanban task -> Run/action -> Audit/artifact
```

## What each surface does

### Agents

An agent is a controlled runtime identity. It defines:

- provider/model strategy
- role and system instruction
- workspace access
- memory scopes
- allowed tools/MCP channels
- approval policy
- audit identity

Example: an SEO agent can use DeepSeek, global/workspace/agent memory, selected workspace docs, skills, and Kanban tasks. It should not publish externally without approval.

### Workspaces

A workspace is the repo/path boundary Agentic OS may hand to agents.

- DeepSeek can use workspace content when it is imported/indexed into memory/context.
- Codex can act on workspace files only when the path is mounted into the Agentic OS runtime or a remote Codex adapter is implemented.
- Hermes can reach workspace files only through a callable Hermes gateway/API or CLI bridge that supports that action.

Workspace registration is not permission to mutate files. File writes/runs still require approval gates.

### Kanban

Agentic OS Kanban is currently a local SQLite work queue. It is **not yet synchronized with Hermes Kanban**.

A task is more than a title. It should carry:

- description
- assigned agent
- workspace
- priority
- schedule intent
- approval gate
- artifact/thread/session links
- audit events

Creating a task creates a work order. It does not automatically run until an executable adapter and approval path are wired.

### Memory

Memory stores local context. Scopes mean:

| Scope | Meaning |
|---|---|
| `global` | available to all agents when permitted |
| `agent` | attached to one agent identity |
| `workspace` | follows a repo/path |
| `project` | larger operating zone |

The UI supports pasting text and uploading local text/markdown/doc-like files by reading them in the browser and saving the extracted text as memory. Agents only use memory whose scopes/grants match the task.

### Skills Hub

A skill is a reusable operating package: prompt procedure, tool requirement, command template, validation habit, or workflow recipe. Skills are meant to be attached to agents/tasks so the agent knows how work should be done.

### Canvas

Canvas is a view-only map of how agents, providers, capabilities, memory, workspaces, approvals, artifacts, and audit connect. It is not a fake drag/drop workflow builder.

## Hermes integration

Robel's dashboard command:

```bash
hermes dashboard --host 0.0.0.0 --port 9119 --no-open --insecure
```

exposes the human dashboard only. Agentic OS needs a callable Hermes API/gateway endpoint.

Robel's current gateway/API endpoint is:

```text
http://192.168.1.118:8642
```

Set it in `.env`:

```bash
HERMES_URL=http://192.168.1.118:8642
```

Agentic OS still needs a Hermes adapter contract for Kanban/profile/session/cron/tool actions. Until that is implemented, it must not claim that Hermes capabilities are fully exposed.

## Codex and Claude Code

Robel wants subscription auth, not API keys.

Correct direction:

- Codex: subscription CLI adapter where `codex` is installed and already logged in.
- Claude Code: subscription CLI adapter where `claude` is installed and already logged in.

Inside Docker this requires one of:

1. install/authenticate the CLI inside the Agentic OS container,
2. mount a host CLI/session safely,
3. build a sidecar/remote worker adapter,
4. build an SSH/remote API adapter.

Do not fake these as connected from config alone.
