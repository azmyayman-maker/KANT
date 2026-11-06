"""
Kant Compiler Toolchain - Thread-Safe SQLite Telemetry Database Adapter
Stores audit events, state snapshots, and verification commits with bidirectional
compatibility across git hooks and modular REST APIs.
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional


class TelemetryDatabase:
    """Thread-safe SQLite database adapter for Kant toolchain telemetry."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path).resolve()
        self.lock = threading.Lock()
        self._ensure_parent_dir()
        self.init_db()

    def _ensure_parent_dir(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Thread-safe context manager for obtaining a SQLite connection."""
        with self.lock:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False,
            )
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def init_db(self) -> None:
        """Create telemetry tables, indexes, and schema migrations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Enable WAL mode for high concurrency
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")

            # Telemetry events stream table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action_type TEXT,
                    task_id TEXT,
                    circle_id TEXT,
                    git_commit TEXT,
                    status_diff TEXT,
                    details TEXT,
                    level TEXT,
                    agent TEXT,
                    commit_hash TEXT,
                    message TEXT
                );
            """)

            # Check for existing table schema migrations (e.g. if table created by git hook)
            cursor.execute("PRAGMA table_info(telemetry_events);")
            existing_cols = {row[1] for row in cursor.fetchall()}
            for col in ("level", "agent", "commit_hash", "message"):
                if col not in existing_cols:
                    cursor.execute(f"ALTER TABLE telemetry_events ADD COLUMN {col} TEXT;")

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp
                ON telemetry_events(timestamp DESC);
            """)

            # State snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS state_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    version TEXT NOT NULL,
                    total_tasks INTEGER NOT NULL,
                    completed_tasks INTEGER NOT NULL,
                    blocked_tasks INTEGER NOT NULL,
                    progress_percent REAL NOT NULL,
                    state_json TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
                ON state_snapshots(timestamp DESC);
            """)

    def record_event(
        self,
        level: str,
        agent: str,
        commit_hash: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        """Insert a telemetry audit event into the database."""
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        details_str = json.dumps(details, ensure_ascii=False) if details else None
        lvl = level.upper()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO telemetry_events (
                    timestamp, action_type, git_commit, status_diff, details,
                    level, agent, commit_hash, message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ts, lvl, commit_hash, message, details_str, lvl, agent, commit_hash, message),
            )
            return cursor.lastrowid or 0

    def get_audit_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve the most recent audit events."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, action_type, git_commit, status_diff, details,
                       level, agent, commit_hash, message
                FROM telemetry_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            events = []
            for row in rows:
                details = None
                if row["details"]:
                    try:
                        details = json.loads(row["details"])
                    except Exception:
                        details = row["details"]

                lvl = row["level"] or row["action_type"] or "INFO"
                ag = row["agent"] or (details.get("author_name") if isinstance(details, dict) else None) or "SYSTEM"
                ch = row["commit_hash"] or row["git_commit"] or (details.get("short_hash") if isinstance(details, dict) else "") or ""
                msg = row["message"] or row["status_diff"] or (details.get("subject") if isinstance(details, dict) else "") or ""

                events.append({
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "level": lvl,
                    "agent": ag,
                    "commit_hash": ch,
                    "message": msg,
                    "details": details,
                })
            return events

    def record_state_snapshot(self, state_dict: Dict[str, Any]) -> int:
        """Persist a full roadmap state snapshot."""
        ts = state_dict.get("last_updated") or datetime.now(timezone.utc).isoformat()
        version = state_dict.get("version", "0.1.0")
        stats = state_dict.get("global_stats", {})
        total = stats.get("total_tasks", 75)
        completed = stats.get("completed_tasks", 0)
        blocked = stats.get("blocked_tasks", 0)
        progress = stats.get("progress_percent", 0.0)
        state_json = json.dumps(state_dict, ensure_ascii=False)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO state_snapshots (
                    timestamp, version, total_tasks, completed_tasks, blocked_tasks, progress_percent, state_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (ts, version, total, completed, blocked, progress, state_json),
            )
            return cursor.lastrowid or 0

    def get_latest_state(self) -> Optional[Dict[str, Any]]:
        """Retrieve the most recently recorded state snapshot."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT state_json
                FROM state_snapshots
                ORDER BY id DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if row and row["state_json"]:
                try:
                    return json.loads(row["state_json"])
                except Exception:
                    pass
            return None

    def get_recent_commits(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Extract recent commits recorded by git hooks or telemetry events."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if git_commits table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='git_commits';")
            if cursor.fetchone():
                cursor.execute(
                    """
                    SELECT commit_hash, short_hash, author_name, branch, subject, committed_at
                    FROM git_commits
                    ORDER BY committed_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                return [
                    {
                        "commit_hash": r["commit_hash"],
                        "short_hash": r["short_hash"],
                        "author_name": r["author_name"],
                        "branch": r["branch"],
                        "subject": r["subject"],
                        "timestamp": r["committed_at"],
                    }
                    for r in cursor.fetchall()
                ]

            # Fallback to telemetry_events
            cursor.execute(
                """
                SELECT DISTINCT commit_hash, agent, MAX(timestamp) as last_seen
                FROM telemetry_events
                WHERE commit_hash IS NOT NULL AND commit_hash != ''
                GROUP BY commit_hash
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [
                {
                    "commit_hash": r["commit_hash"],
                    "short_hash": r["commit_hash"][:7],
                    "author_name": r["agent"],
                    "branch": "main",
                    "subject": "Commit event",
                    "timestamp": r["last_seen"],
                }
                for r in cursor.fetchall()
            ]
