# Agentic OS UI Design

## Product direction

The frontend is now designed as a local AI operations studio rather than a raw admin dashboard. The interface centers on four agent rooms:

- **Codex** — green terminal/build accent for safe, audited code work.
- **DeepSeek** — cyan/blue reasoning/chat accent for low-cost threaded chat.
- **Claude** — amber premium reasoning accent with intentional disabled/setup state.
- **Hermes** — violet operating-layer accent for orchestration, gateway, MCP, skills, Kanban, memory, and activity.

## Design system

Design tokens live in `frontend/src/styles/tokens.css` and define:

- background, surface, elevated surface, border, primary/muted text
- agent accents: Codex, DeepSeek, Claude, Hermes
- danger, warning, success
- radius scale, shadows, spacing scale

The app stylesheet `frontend/src/styles/app.css` uses those tokens for glass panels, cinematic gradients, responsive layouts, terminal panels, chat bubbles, Kanban lanes, cards, tabs, drawer, and command palette.

## Information architecture

### Workspace group

- Mission Control
- Workspaces
- Kanban
- Memory
- Skills Hub
- Activity
- Settings

### Agent rooms

- Codex
- DeepSeek
- Claude
- Hermes

Each sidebar item routes to a real page. Buttons either call existing APIs, navigate to a working workflow, or show an explicit not-configured state.

## Page behavior

- Mission Control is the front door: status strip, metrics, room cards, activity, failures, quick actions.
- Agent rooms group capabilities behind tabs instead of scattering one-off admin pages.
- Codex commit/push controls are visually isolated as controlled/dangerous actions and still require explicit backend confirmation.
- DeepSeek uses a chat layout with thread list, message bubbles, composer, loading, and error display.
- Claude shows a setup checklist and useful disabled-state pages instead of a broken placeholder.
- Workspaces, Kanban, Memory, Skills, Activity, and Settings render cards/timelines/forms as primary UI. Raw JSON is only available in collapsible advanced sections where useful.

## Responsive design

- Desktop: persistent left sidebar and wide content grid.
- Tablet: drawer sidebar and single-column room layouts where needed.
- Mobile: top menu, bottom quick nav, horizontally scrollable Kanban lanes, sticky chat composer, and wrapped pre blocks so logs/config do not break layout.
