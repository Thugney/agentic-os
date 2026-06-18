# Runtime Connections

Agentic OS is a control plane. Runtime rows in YAML are not secrets and are not proof that an agent is connected. Each runtime needs a real adapter and a real action path.

## DeepSeek API

DeepSeek should be configured as a cloud API provider by default.

### What goes in `.env`

Put the real DeepSeek key in `.env` only:

```bash
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=
```

On your NAS/Synology deployment, fill `DEEPSEEK_API_KEY` locally with the real value. Never commit the real key. Never paste it into `config/providers.yaml`.

### What goes in `config/providers.yaml`

YAML stores non-secret metadata and the name of the env var:

```yaml
provider: deepseek
connection_mode: cloud_api
endpoint: https://api.deepseek.com
api_key_env: DEEPSEEK_API_KEY
model_selection: live_dropdown
```

Do **not** hardcode one required DeepSeek model for Robel's workflow. Agentic OS probes:

```text
GET https://api.deepseek.com/v1/models
```

using `DEEPSEEK_API_KEY`, then shows available models in the DeepSeek Room dropdown. Robel chooses the model before chatting.

## Codex subscription

Robel wants to use his Codex subscription, not an API key. That means Agentic OS needs a subscription/CLI adapter, not an API-key provider.

Current intended config:

```yaml
provider: codex
connection_mode: subscription_cli
cli_binary: codex
auth_mode: interactive_subscription
```

Operational meaning:

1. The Codex CLI must exist where Agentic OS can run it.
2. The CLI must already be logged in with Robel's subscription.
3. If Agentic OS runs in Docker, that means either:
   - install Codex CLI inside the image/container and persist its auth config safely, or
   - run a sidecar/host adapter that Agentic OS can call.

Agentic OS must not ask for a Codex API key if Robel wants subscription mode.

## Claude Code subscription

Robel wants Claude Code through subscription login, not API key.

Current intended config:

```yaml
provider: claude
connection_mode: subscription_cli
cli_binary: claude
auth_mode: interactive_subscription
```

Operational meaning:

1. Claude Code CLI must exist where the adapter runs.
2. Claude Code must already be authenticated with Robel's subscription.
3. Agentic OS needs a Claude Code adapter to create sessions, stream output, capture artifacts, and audit actions.

This is not the same as setting `ANTHROPIC_API_KEY`. API-key mode is a different adapter and should not be forced on Robel.

## Hermes

Hermes should be connected through a callable API/gateway endpoint or a deliberately installed/mounted CLI bridge.

A browser dashboard URL is not enough. Agentic OS needs endpoints it can call for actions such as chat, jobs, tools, skills, memory, and sessions.

## Security rules

- Secrets live in `.env`, not YAML.
- YAML can store only env var names such as `DEEPSEEK_API_KEY`.
- Runtime setup forms must not store raw keys.
- Provider tests may call health/model-list endpoints, but must not log secrets.
- Codex/Claude subscription adapters must not copy browser tokens or private auth files into public repo files.
