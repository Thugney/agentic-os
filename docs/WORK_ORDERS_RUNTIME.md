# Work Orders Runtime Implementation

This document describes the first real Mission-Control-style Agentic OS implementation slice.

## Purpose

A work order is the backend-backed unit of agent work. It connects what was previously fragmented across Kanban, agent rooms, runtime status, workspace policy, memory scope, validation commands, artifacts, and audit logging.

## Backend contract

| Route name | Behavior |
| --- | --- |
| runtime adapters list | Returns live runtime adapter readiness for Codex, DeepSeek, Hermes, Claude, and MCP registry. |
| runtime adapter detail | Returns one adapter status or 404. |
| work orders list | Lists work orders from SQLite. Kept under Kanban route family for UI compatibility. |
| work order detail | Returns one work order plus runtime status. |
| work order create | Creates a structured work order and writes an audit event. |
| work order update | Updates allowed work-order fields and writes an audit event. |
| work order approve | Moves the work order to `approval_state=approved` and `status=Ready`. |
| work order run | Runs only when approved and runtime-ready; otherwise blocks honestly and audits the reason. |

## Data model

The `kanban_tasks` table now carries work-order metadata:

- `priority`
- `assigned_agent` / `agent`
- `capability_id`
- `workspace`
- `memory_scope`
- `schedule` / `schedule_intent`
- `approval_gate` / `approval_state`
- `validation_command`
- `run_session_id`
- `artifact_refs`
- `chat_thread`

Migration `003_work_order_runtime_path` upgrades existing installations idempotently.

## Runtime adapter behavior

| Adapter | Readiness source | Run behavior |
| --- | --- | --- |
| Codex | `codex` CLI on `PATH` plus configured workspace | Starts real background Codex session through existing `codex_service`. |
| DeepSeek | OpenAI-compatible provider config and endpoint reachability | Sends work-order prompt through existing chat service and links thread. |
| Hermes | Configured endpoint reachability | Status only in this slice; run blocks until adapter execution exists. |
| Claude | `claude` CLI on `PATH` | Status only in this slice; run blocks until adapter execution exists. |
| MCP registry | Configured registry items | Status only in this slice. |

## UI behavior

The Work Orders page now:

- fetches agents, workspaces, capabilities, and runtime adapter readiness from the backend;
- creates real backend work orders instead of title-only local tasks;
- shows runtime readiness on cards;
- disables `Run` until a work order is approved and the runtime is ready;
- calls real approve/run endpoints;
- shows blocked runtime reasons rather than pretending success.

## Validation performed

- `python3 -m compileall backend`
- FastAPI in-process smoke test in development mode:
  - health endpoint returns 200;
  - runtime adapters endpoint returns five adapter records;
  - work-order create returns 200;
  - approve returns 200 and `Ready`;
  - run returns HTTP 400 when Codex CLI is unavailable;
  - audit contains create, approve, and blocked-run events.
- `npm --prefix frontend install`
- `npm --prefix frontend run build`

## Known limitations

- Codex execution is real only when the runtime image or host has the `codex` CLI installed and the selected workspace is allowed.
- DeepSeek execution depends on configured OpenAI-compatible endpoint reachability.
- Hermes and Claude adapters expose honest readiness/status but do not execute work orders in this slice.
- The endpoint path still uses the Kanban task route family for compatibility; the internal semantics are now work orders.
