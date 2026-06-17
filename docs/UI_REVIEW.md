# UI Review

This branch refactors Agentic OS into a product-grade local AI command center. Use this checklist to capture review screenshots after running the app locally.

## Run locally

```bash
npm --prefix frontend install
npm --prefix frontend run build
AGENTIC_OS_ENVIRONMENT=development AGENTIC_OS_DATA_DIR=/tmp/agentic-os-ui-review uvicorn backend.app.main:app --host 0.0.0.0 --port 3737
```

Open:

```text
http://127.0.0.1:3737
```

For production/container review, set `AGENTIC_OS_ADMIN_TOKEN` and enter it in the top bar token field before protected actions.

## Required screenshots

### 1. Desktop Mission Control

- Viewport: 1440×1000 or similar.
- Capture the full sidebar, hero, agent status strip, metrics, agent room cards, activity/failure panels, and quick actions.
- Expected: cinematic dark command-center feel, no raw JSON as primary UI.

### 2. Codex Room

- Open **Codex** from the agent room sidebar group.
- Capture the **Run** tab and **Sessions** tab if sessions exist.
- Expected: first-class run form, safety contract, readable session list/log panel, controlled commit/push area under Diff/Test.

### 3. DeepSeek Chat

- Open **DeepSeek**.
- Capture the **Chat** tab.
- Expected: thread list, model/agent selector, message bubble area, sticky composer, loading/error space.

### 4. Mobile layout

- Viewport: 390×844 or similar.
- Capture Mission Control and one room.
- Expected: hidden desktop sidebar, mobile menu/drawer, bottom quick nav, readable cards, no overflowing JSON/pre blocks.

## Browser smoke checks

- Open every sidebar item and agent room.
- Confirm no page is a raw JSON dump as the primary experience.
- Confirm placeholder buttons use alerts or setup guidance rather than silently doing nothing.
- Confirm Kanban scrolls horizontally on mobile.
- Confirm DeepSeek composer remains usable on mobile.
- Confirm Settings hides secret values and shows raw config only in the advanced collapsible section.
