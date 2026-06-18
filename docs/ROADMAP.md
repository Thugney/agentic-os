# Roadmap

## Now: local cockpit foundation

- [x] Mission Control, Agent Rooms, Workspaces, Kanban, Memory, Skills Hub, Activity, Settings.
- [x] Codex sessions with explicit commit/push approval gates.
- [x] MCP registry scaffold.
- [x] Capability manifest registry in `config/capabilities.yaml`.
- [x] Spaces registry in `config/spaces.yaml`.
- [x] Capability and Spaces data exposed through `/api/settings/effective`.
- [x] Canvas page with view-only graph generated from Capability YAML.
- [x] Architecture docs and diagrams for capability canvas direction.

## Next: manifest discipline

- [ ] Add JSON Schema or Pydantic validation for Capability manifests.
- [ ] Surface manifest validation errors in Settings and Canvas.
- [ ] Add Capability detail page with inputs, outputs, approvals, audit policy, validation command, rollback notes.
- [ ] Add cost/token trace fields to session and audit events where runtimes expose usage.
- [ ] Connect Capability selection to Codex/Hermes/DeepSeek run forms without bypassing approvals.

## Later: real visual operating studio

- [ ] Persist manual Canvas node positions.
- [ ] Add safe manifest editor with schema validation and diff preview.
- [ ] Add drag/drop editing only when it can write valid Capability YAML and pass validation.
- [ ] Simulate workflow runs before execution.
- [ ] Enforce allowed models/tools/workspaces in runtime adapters.
- [ ] Add bulk input runs for approved Capabilities.
- [ ] Add OpenFang-style runtime adapter if Robel chooses a runtime package lane.
- [ ] Add SmythOS/SRE-style adapter only if Robel chooses to integrate an external studio/runtime.
