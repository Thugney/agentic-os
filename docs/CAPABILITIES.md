# Capability Manifest Model

A Capability is a reusable agent workflow package for Agentic OS. The source of truth is `config/capabilities.yaml`.

## YAML shape

```yaml
capabilities:
  - id: codex-build-feature
    name: "Codex: build feature"
    description: "Run an audited Codex build task."
    owning_agent: codex
    allowed_models: [high-accuracy-coding]
    allowed_tools_mcps: [git, terminal]
    allowed_workspaces: [agentic-os]
    memory_scope: workspace
    prompt: "Build with tests, docs, validation, and rollback notes."
    inputs: [task, workspace]
    outputs: [diff_summary, test_result]
    approval_gates: [before_commit, before_push]
    schedule: { supported: false }
    bulk_input: { supported_later: true }
    audit_policy: "Record start, result, artifacts, and approvals."
    cost_token_policy: "Use high-accuracy model only for code-writing/review."
    generated_artifacts: [code_changes, validation_log]
    validation_command: "npm --prefix frontend run build && pytest"
    rollback_notes: "Revert branch or restore previous image."
```

## Enforcement roadmap

| Phase | Enforcement |
| --- | --- |
| MVP | Read YAML through `/api/settings/effective` and render a view-only Canvas from Capability settings. |
| Next | Validate schema before registry updates and show manifest errors in UI. |
| Later | Bind run forms to Capability inputs/outputs and approval gates. |
| Later | Enforce allowed models/tools/workspaces at runtime adapter boundaries. |
| Later | Cost/token trace from runtime telemetry. |

## Safety rules

- Secret values never live in manifest YAML.
- Workspaces are allowlisted by name/path.
- Destructive actions require approval gates.
- External sends and scheduled writes require explicit policy.
- Generated artifacts must be recorded in audit or session metadata.
