# Kant Observatory Telemetry Portal (`portal/`)

The **Kant Observatory** is the decoupled, production-grade telemetry dashboard and topological roadmap observer for the **Kant** (`.kant`) programming language compiler toolchain.

---

## 1. Architectural Philosophy & Invariants

1. **Strict 0.0% Zero-State Invariant [S0]:**
   The portal tracks the exact 75 formal verification tasks across Macro-Circles **C0** through **C6**. In accordance with the project constitution, progress begins at exactly **0.0%** (0 tasks completed, 0 blocked, health 100%). Synthetic progress inflation or mock test runs are prohibited.
2. **100% Offline Self-Containment [O1]:**
   The portal operates without any external CDN links (`cdnjs`, `fonts.googleapis.com`, `jsdelivr`). Typography relies on pure system font stacks, and branding is rendered via self-hosted vector assets (`assets/kant-icon.svg`).
3. **Decoupled Separation of Concerns:**
   The frontend is written in vanilla modern ES6 modules with decoupled CSS design token stylesheets. The backend is an asynchronous, thread-safe Python package relying strictly on the Python 3 standard library (`http.server`, `sqlite3`, `queue`, `threading`).
4. **Compiler Isolation [Z0]:**
   The portal is physically and logically decoupled from the compiler crate source tree in `crates/*/src/`.

---

## 2. Directory Structure

```
portal/
├── README.md                      # Comprehensive operations and API guide
├── server.py                      # Root convenience runner (delegates to backend package)
├── .gitignore                     # Ignores runtime databases, logs, and __pycache__
├── assets/
│   └── kant-icon.svg              # Canonical vector brand asset (gold silhouette, transparent)
├── frontend/                      # Decoupled static frontend
│   ├── index.html                 # Clean semantic HTML5 markup (zero inline CSS/JS)
│   ├── css/
│   │   ├── variables.css          # Design tokens: palette, typography, spacing, shadows
│   │   ├── layout.css             # Page shell, header, metrics toolbar, grid system
│   │   └── components.css         # Stage cards, task items, progress rings, modal dialogues
│   └── js/
│       ├── app.js                 # Bootstrap coordinator & lifecycle manager
│       ├── store.js               # Centralized reactive state store (tasks, metrics, gates)
│       ├── sse_client.js          # Robust SSE client with exponential backoff & reconnection
│       ├── graph.js               # Canvas/SVG topological pipeline dependency graph
│       ├── ui_renderer.js         # DOM rendering engine for stages, cards, and filters
│       └── audit_logger.js        # Telemetry events stream and audit history inspector
├── backend/                       # Python backend package
│   ├── __init__.py                # Package declaration & version
│   ├── config.py                  # Port, host, paths, and CORS configuration
│   ├── database.py                # Thread-safe SQLite telemetry adapter
│   ├── default_state.json         # Canonical 75-task zero-state roadmap baseline
│   ├── routes.py                  # HTTP request dispatchers and REST endpoints
│   ├── server.py                  # HTTP & SSE server implementation
│   └── sse.py                     # Server-Sent Events broker and client multiplexer
└── tests/                         # Automated test suite
    ├── __init__.py
    ├── test_database.py           # Unit tests for database queries and schema integrity
    └── test_server.py             # Smoke tests for HTTP endpoints and static file delivery
```

---

## 3. Quickstart & Operations

### 3.1. Starting the Observatory Server
Run the portal using the root convenience runner:
```bash
python portal/server.py --port 8080
```
Or directly run the backend package:
```bash
python -m portal.backend.server --host 127.0.0.1 --port 8080
```
Open your browser to:
[http://127.0.0.1:8080](http://127.0.0.1:8080)

### 3.2. Running Automated Tests
Execute the unit and regression test suite:
```bash
python -m unittest discover -s portal/tests -v
```

---

## 4. REST & SSE API Reference

| Endpoint | Method | Content-Type | Description |
|---|---|---|---|
| `/` | `GET` | `text/html` | Serves `portal/frontend/index.html` |
| `/css/*`, `/js/*`, `/assets/*` | `GET` | `text/css`, `application/javascript`, `image/svg+xml` | Static frontend modules and vector assets |
| `/api/state` | `GET` | `application/json` | Returns full roadmap state snapshot (0.0% zero-state baseline) |
| `/api/state` | `POST` | `application/json` | Updates roadmap task state, persists to SQLite, and broadcasts via SSE |
| `/api/events` | `GET` | `text/event-stream` | Upgrades connection to live Server-Sent Events (SSE) telemetry stream |
| `/api/health` | `GET` | `application/json` | Health status: `{"status": "ok", "mode": "zero_state", "version": "0.1.0"}` |
| `/api/telemetry` | `GET` | `application/json` | Returns recent audit events from SQLite telemetry database (`?limit=N`) |
| `/api/commits` | `GET` | `application/json` | Returns recent distinct git commit records |
| `/*` | `OPTIONS` | `none` | CORS pre-flight handler returning HTTP 204 with permissive headers |

---

## 5. Frontend Modular Subsystems

* **`store.js` (`RoadmapStore`):** Reactive state manager holding all 75 tasks across circles C0 through C6. Subscribes listeners to state mutations and provides automatic recalculation of completion percentages.
* **`sse_client.js` (`SSEClient`):** Manages persistent `EventSource` connection to `/api/events` with automatic exponential backoff reconnection (1s, 2s, 4s, 8s, up to 30s) and jitter.
* **`graph.js` (`TopologicalPipelineGraph`):** Interactive SVG renderer visualizing the Macro-Circle compilation pipeline ($C_0 \rightarrow C_1 \rightarrow C_2 \rightarrow C_3 \rightarrow C_4 \rightarrow C_5 \rightarrow C_6$) with pan, zoom, and node selection.
* **`ui_renderer.js` (`UIRenderer`):** Modular DOM engine rendering stage cards, epistemological gate checklists, filter toolbars (all/incomplete/done, sub-agent lane filters SA-01 to SA-16), and search controls.
* **`audit_logger.js` (`TelemetryAuditLogger`):** Appends real-time telemetry events with timestamps, severity levels (`INFO`, `WARN`, `ERROR`, `AUDIT`), commit hashes, and export capabilities.
* **`app.js` (`KantPortalApp`):** Central coordinator initializing all components, binding user actions, and orchestrating state synchronization.

---

## 6. Persistence & Telemetry Database

The backend automatically manages an embedded, thread-safe SQLite database at `.kant-tracker/kant_telemetry.db` (git-ignored):
* **`telemetry_events`:** Logs every state mutation, verification law step, and commit action.
* **`state_snapshots`:** Maintains historical snapshots of the roadmap state.
* **`git_commits`:** Tracks commits recorded by git automation hooks.
