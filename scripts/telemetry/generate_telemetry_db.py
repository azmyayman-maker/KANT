#!/usr/bin/env python3
"""
scripts/telemetry/generate_telemetry_db.py: SQLite Schema Initializer & Migration Tool for Kant.

Creates and validates the high-assurance telemetry database at .kant-tracker/kant_telemetry.db:
- Tables: metadata, circles, headings, subheadings, tasks, iterations, gate_runs, telemetry_events
- Indexes: circle lookups, timestamps, action types, task associations
- Idempotent execution: safe to run multiple times without data corruption.
"""

import sys
import os
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_TRACKER_DIR = WORKSPACE_ROOT / ".kant-tracker"
DEFAULT_DB_FILE = DEFAULT_TRACKER_DIR / "kant_telemetry.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS circles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    short_title TEXT,
    wave TEXT,
    gate_status TEXT NOT NULL DEFAULT 'LOCKED',
    iteration INTEGER NOT NULL DEFAULT 1,
    dependencies TEXT DEFAULT '[]',
    gate_checklist TEXT DEFAULT '{}',
    ordering INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS headings (
    id TEXT PRIMARY KEY,
    circle_id TEXT NOT NULL REFERENCES circles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    crate_lane TEXT,
    assigned_agent TEXT,
    ordering INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS subheadings (
    id TEXT PRIMARY KEY,
    heading_id TEXT NOT NULL REFERENCES headings(id) ON DELETE CASCADE,
    circle_id TEXT NOT NULL REFERENCES circles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    ordering INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    subheading_id TEXT NOT NULL REFERENCES subheadings(id) ON DELETE CASCADE,
    heading_id TEXT NOT NULL REFERENCES headings(id) ON DELETE CASCADE,
    circle_id TEXT NOT NULL REFERENCES circles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'TODO',
    iteration_completed INTEGER DEFAULT 0,
    verification_cmd TEXT,
    notes TEXT DEFAULT '',
    ordering INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS iterations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    circle_id TEXT NOT NULL REFERENCES circles(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    status TEXT NOT NULL,
    summary TEXT
);

CREATE TABLE IF NOT EXISTS gate_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    circle_id TEXT NOT NULL REFERENCES circles(id) ON DELETE CASCADE,
    iteration INTEGER NOT NULL,
    gate_step TEXT NOT NULL,
    status TEXT NOT NULL,
    command TEXT,
    output TEXT,
    run_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS telemetry_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action_type TEXT NOT NULL,
    task_id TEXT,
    circle_id TEXT,
    git_commit TEXT,
    status_diff TEXT,
    details TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_circle ON tasks(circle_id);
CREATE INDEX IF NOT EXISTS idx_tasks_subheading ON tasks(subheading_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_action ON telemetry_events(action_type);
CREATE INDEX IF NOT EXISTS idx_telemetry_task ON telemetry_events(task_id);
CREATE INDEX IF NOT EXISTS idx_gate_runs_circle ON gate_runs(circle_id);
"""


def init_database(db_path: Path, reset: bool = False) -> bool:
    """Initialize SQLite telemetry database schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if reset and db_path.exists():
        print(f"[*] Resetting database at {db_path}...")
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.executescript(SCHEMA_SQL)

        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            "INSERT OR IGNORE INTO metadata (key, value) VALUES ('schema_version', '1.0.0')"
        )
        cur.execute(
            "INSERT OR IGNORE INTO metadata (key, value) VALUES ('created_at', ?)", (now,)
        )
        cur.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_migrated_at', ?)", (now,)
        )
        conn.commit()
        print(f"[✓] Initialized SQLite telemetry database schema at: {db_path}")
        return True
    except Exception as e:
        print(f"[!] Failed to initialize database: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def verify_database(db_path: Path) -> bool:
    """Verify schema integrity of telemetry database."""
    if not db_path.exists():
        print(f"[!] Database file does not exist: {db_path}", file=sys.stderr)
        return False

    required_tables = {
        "metadata", "circles", "headings", "subheadings",
        "tasks", "iterations", "gate_runs", "telemetry_events"
    }

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        missing = required_tables - tables
        if missing:
            print(f"[x] Database missing tables: {missing}", file=sys.stderr)
            return False

        cur.execute("SELECT value FROM metadata WHERE key='schema_version'")
        row = cur.fetchone()
        version = row[0] if row else "unknown"
        print(f"[✓] Telemetry database verified. Schema version: {version}")
        return True
    except Exception as e:
        print(f"[!] Verification failed: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Kant Telemetry Database Initializer")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_FILE, help="Path to sqlite db")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate database")
    parser.add_argument("--verify", action="store_true", help="Verify schema without modifying")
    args = parser.parse_args()

    if args.verify:
        return 0 if verify_database(args.db_path) else 1

    success = init_database(args.db_path, reset=args.reset)
    if success:
        return 0 if verify_database(args.db_path) else 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
