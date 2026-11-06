"""
Kant Compiler Toolchain - Unit Tests for TelemetryDatabase
Validates schema integrity, zero-state persistence, query methods, and thread-safety.
"""

import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from portal.backend.database import TelemetryDatabase


class TestTelemetryDatabase(unittest.TestCase):
    """Test suite for SQLite TelemetryDatabase adapter."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="kant_test_db_")
        self.db_path = Path(self.temp_dir) / "test_telemetry.db"
        self.db = TelemetryDatabase(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_schema_initialization(self):
        """Verify tables and indexes are created properly upon initialization."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row["name"] for row in cursor.fetchall()}
            self.assertIn("telemetry_events", tables)
            self.assertIn("state_snapshots", tables)

            # Check columns in telemetry_events
            cursor.execute("PRAGMA table_info(telemetry_events);")
            cols = {row["name"] for row in cursor.fetchall()}
            for expected_col in ("id", "timestamp", "level", "agent", "commit_hash", "message"):
                self.assertIn(expected_col, cols)

    def test_record_and_get_audit_events(self):
        """Verify recording audit events and retrieving them in reverse chronological order."""
        event_id = self.db.record_event(
            level="AUDIT",
            agent="SA-01",
            commit_hash="3fe7aea",
            message="Test verification law pinned.",
            details={"step": 1, "rule": "iron_law"},
        )
        self.assertGreater(event_id, 0)

        # Record a second event
        self.db.record_event(
            level="INFO",
            agent="SA-02",
            commit_hash="4ab8f12",
            message="EBNF grammar formalization complete.",
        )

        events = self.db.get_audit_events(limit=10)
        self.assertEqual(len(events), 2)
        # Most recent event first
        self.assertEqual(events[0]["agent"], "SA-02")
        self.assertEqual(events[0]["level"], "INFO")
        self.assertEqual(events[1]["agent"], "SA-01")
        self.assertEqual(events[1]["details"], {"step": 1, "rule": "iron_law"})

    def test_record_and_get_state_snapshot(self):
        """Verify state snapshot persistence and zero-state retrieval."""
        zero_state = {
            "version": "0.1.0",
            "last_updated": "2026-11-06T18:00:00Z",
            "current_circle_focus": "C0",
            "global_stats": {
                "total_tasks": 75,
                "completed_tasks": 0,
                "blocked_tasks": 0,
                "progress_percent": 0.0,
            },
            "circles": [{"id": "C0", "name": "Epistemology"}],
        }

        snap_id = self.db.record_state_snapshot(zero_state)
        self.assertGreater(snap_id, 0)

        retrieved = self.db.get_latest_state()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["version"], "0.1.0")
        stats = retrieved["global_stats"]
        self.assertEqual(stats["total_tasks"], 75)
        self.assertEqual(stats["completed_tasks"], 0)
        self.assertEqual(stats["blocked_tasks"], 0)
        self.assertEqual(stats["progress_percent"], 0.0)

    def test_get_recent_commits(self):
        """Verify distinct commit history extraction."""
        self.db.record_event("INFO", "SA-01", "commit-aaa", "First commit")
        self.db.record_event("INFO", "SA-02", "commit-bbb", "Second commit")
        self.db.record_event("INFO", "SA-01", "commit-aaa", "First commit repeated")

        commits = self.db.get_recent_commits(limit=10)
        self.assertEqual(len(commits), 2)
        commit_hashes = {c["commit_hash"] for c in commits}
        self.assertEqual(commit_hashes, {"commit-aaa", "commit-bbb"})

    def test_thread_safety_concurrency(self):
        """Stress-test concurrent insertions across multiple worker threads."""
        threads = []
        errors = []
        worker_count = 10
        events_per_worker = 20

        def worker(thread_idx: int):
            try:
                for i in range(events_per_worker):
                    self.db.record_event(
                        level="INFO",
                        agent=f"WORKER-{thread_idx}",
                        commit_hash=f"hash-{thread_idx}-{i}",
                        message=f"Concurrent message {i} from thread {thread_idx}",
                    )
            except Exception as e:
                errors.append(e)

        for i in range(worker_count):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10.0)

        self.assertEqual(len(errors), 0, f"Thread errors occurred: {errors}")

        events = self.db.get_audit_events(limit=worker_count * events_per_worker + 10)
        self.assertEqual(len(events), worker_count * events_per_worker)


if __name__ == "__main__":
    unittest.main()
