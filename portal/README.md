# Kant Telemetry & Roadmap Portal (`portal/`)

This directory houses the standalone, isolated telemetry platform and topological roadmap observer for the **Kant** (`.kant`) programming language project.

## Overview
* **Status:** Zero-State Pristine (0.0% Progress, all circles C0..C6 pending, ready for Wave implementations).
* **Identity Icon:** `assets/kant-icon.svg` (transcendental gold gradient, transparent background, zero raster assets).
* **Isolation Guarantee:** The portal is completely decoupled from the compiler codebase in `crates/`. Changes to the telemetry dashboard or UI do not touch compiler internals.

## Running the Portal Locally

### Option 1: Standalone Browser (Zero Servers)
Simply open `portal/index.html` (or root `kant-roadmap-tracker.html`) in any modern web browser:
```powershell
start portal/index.html
```

### Option 2: Live Local Telemetry Server
Run the lightweight Python server:
```powershell
python portal/server.py --port 8080
```
Then navigate to:
[http://127.0.0.1:8080](http://127.0.0.1:8080)

## Data Storage
- Local State: Stored in browser `localStorage` (`KANT_ROADMAP_STATE_V01_ZERO`).
- Persistent Backend (Optional): Synchronized to `.kant-tracker/state.json` and `.kant-tracker/kant_telemetry.db` (git-ignored for clean repo hygiene).
