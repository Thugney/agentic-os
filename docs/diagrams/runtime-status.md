# Runtime Status and Chat Wiring

```mermaid
flowchart LR
  UI[Agent Rooms and Mission Control] --> Status[GET /api/systems/status]
  Status --> Runtime[backend runtime_service]
  Runtime --> OpenWebUI[OpenWebUI /v1/models]
  Runtime --> CodexCLI[codex --version]
  Runtime --> HermesCLI[hermes --version]
  Runtime --> HermesHealth[HERMES_URL /health]
  UI --> DeepSeekChat[POST /api/chat]
  DeepSeekChat --> OpenAIAdapter[OpenAI-compatible adapter]
  OpenAIAdapter --> OpenWebUIChat[OpenWebUI /v1/chat/completions]
  UI --> HermesChat[POST /api/hermes/chat]
  HermesChat --> HermesCommand[hermes chat -q]
  UI --> CodexRun[POST /api/codex/run]
  CodexRun --> CodexService[async Codex service]
  CodexService --> Workspace[allowlisted workspace]
  CodexService --> Logs[/data/logs/codex]
  CodexService --> Audit[(audit_log)]
```

Agentic OS no longer treats YAML `enabled: true` as proof that a runtime works. `/api/systems/status` actively probes configured runtime boundaries and returns `ready`, `status`, and `detail` fields. The UI disables chat/run controls when the runtime is not reachable and shows the blocker.
