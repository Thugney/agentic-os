# Core operating studio diagram

```mermaid
flowchart LR
  User[Robel] --> UI[Agentic OS UI]
  UI --> Agents[Custom Agents]
  Agents --> Providers[Runtime Providers]
  Agents --> Workspaces[Workspace Grants]
  Agents --> Memory[Scoped Memory]
  Agents --> Skills[Skills / MCP Channels]
  UI --> Kanban[Structured Kanban Tasks]
  Kanban --> Agents
  Kanban --> Approvals[Approval Gates]
  Agents --> Runs[Chat / Run / Runtime Action]
  Runs --> Audit[Audit Log]
  Runs --> Artifacts[Artifacts / Threads]
  Providers --> DeepSeek[DeepSeek API]
  Providers --> Hermes[Hermes Gateway API]
  Providers --> Codex[Codex Subscription CLI Adapter]
  Providers --> Claude[Claude Code Subscription CLI Adapter]
```

## Explanation

Agentic OS is the control plane. Agents are configured identities that attach a provider/model strategy, workspace access, memory scopes, skills/MCP channels, and approval policy. Kanban tasks are structured work orders that assign work to agents and link to workspaces, schedules, approval gates, artifacts, and audit events.

Hermes dashboard access is intentionally separate from Hermes gateway/API access. The dashboard is human UI; the gateway/API is the action path Agentic OS needs.
