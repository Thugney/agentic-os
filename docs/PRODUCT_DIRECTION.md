# Agentic OS Product Direction

Agentic OS is Robel's private local control plane: **one process, every door**.

It is a local-first AI operations cockpit and visual operating studio for controlling and unifying Hermes, Codex, DeepSeek/OpenWebUI, Claude Code, future OpenFang-style runtime adapters, future SmythOS/SRE-style studio adapters if Robel chooses them, workspaces, memory, MCPs, skills, Kanban, sessions, audit, architecture diagrams, approval gates, and deployment/runtime targets.

## Inspiration boundary

SmythOS and OpenFang are used only as architecture and product inspiration. Do not copy their code, UI, branding, wording, assets, layouts, product-specific names, or visual identity.

## Product feel

Agentic OS should feel like a local AI operations studio, agent command center, visual workflow cockpit, secure build control plane, and engineering workspace for a vibe coder. It must not feel like a plain admin dashboard, JSON viewer, toy chatbot, copied SaaS template, or old internal IT portal.

## Layers

### 1. Control Plane

Mission Control, Agent Rooms, Spaces/Workspaces, Kanban, Memory, Skills Hub, MCP Registry, Activity/Audit, Settings, Approval Gates, Cost/Token Trace, and Visual Workflow Canvas.

### 2. Agent Runtimes

Hermes is Robel's orchestrator/operator. Codex is the coding/build runtime. DeepSeek/OpenWebUI is the low-cost local or OpenAI-compatible research/chat lane. Claude Code is the premium reasoning/code-review lane when configured. OpenFang-style and SmythOS/SRE-style adapters remain future options.

### 3. Capability Packages

A **Capability** is a reusable agent workflow package with manifest YAML, name, description, owning agent, allowed models, allowed tools/MCPs, allowed workspaces, memory scope, prompt/system instruction, inputs, outputs, approval gates, schedule support, bulk input support later, audit policy, cost/token policy, generated artifacts, validation command, and rollback notes.

### 4. Visual Workflow Canvas

MVP Canvas is view-only and generated from `config/capabilities.yaml` surfaced through effective settings. It shows Capability, Agent, Model, Prompt, Tool/MCP, API, Workspace, Memory, Approval, Audit, Artifact, Schedule, and Deployment Target nodes. Drag/drop editing is explicitly later work and must not be faked.

### 5. Spaces

A **Space** groups agents, capabilities, workspaces, and memory scope around an operating context. Spaces define which agents can act, which Capabilities are allowed, which workspaces are in scope, and which approvals apply before mutation or delivery.
