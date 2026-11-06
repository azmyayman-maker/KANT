"""
Kant Compiler Toolchain - Smoke & Integration Tests for Portal HTTP Server
Validates static file routing, REST APIs, zero-state preservation, and CORS headers.
"""

import json
import shutil
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from portal.backend.config import Config
from portal.backend.server import create_server


class TestPortalServer(unittest.TestCase):
    """Smoke test suite for the threaded HTTP and SSE server."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="kant_server_test_")
        cls.config = Config(
            host="127.0.0.1",
            port=0,  # Auto-assign free port
            tracker_dir=Path(cls.temp_dir) / ".kant-tracker",
        )
        cls.server, cls.db, cls.broker = create_server(config=cls.config)

        # Retrieve the dynamically assigned port
        cls.assigned_port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.assigned_port}"

        # Start server thread
        cls.server_thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True,
            name="TestServerThread",
        )
        cls.server_thread.start()
        time.sleep(0.1)  # Brief warm-up

    @classmethod
    def tearDownClass(cls):
        cls.broker.shutdown()
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def _fetch(self, path: str, method: str = "GET", body: bytes = None, headers: dict = None):
        url = urllib.parse.urljoin(self.base_url, path)
        req = urllib.request.Request(url, data=body, method=method)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        return urllib.request.urlopen(req, timeout=5.0)

    def test_root_index_html(self):
        """GET / should serve portal/frontend/index.html with UTF-8 encoding."""
        res = self._fetch("/")
        self.assertEqual(res.status, 200)
        self.assertIn("text/html", res.headers.get("Content-Type", ""))
        content = res.read().decode("utf-8")
        self.assertIn("KANT OBSERVATORY", content)
        self.assertIn('src="js/app.js"', content)

    def test_static_assets_delivery(self):
        """Static CSS, JS, and SVG assets must be served with exact MIME types."""
        asset_checks = [
            ("/css/variables.css", "text/css"),
            ("/css/layout.css", "text/css"),
            ("/css/components.css", "text/css"),
            ("/js/app.js", "application/javascript"),
            ("/js/store.js", "application/javascript"),
            ("/js/sse_client.js", "application/javascript"),
            ("/js/graph.js", "application/javascript"),
            ("/js/ui_renderer.js", "application/javascript"),
            ("/js/audit_logger.js", "application/javascript"),
            ("/assets/kant-icon.svg", "image/svg+xml"),
        ]

        for path, expected_mime in asset_checks:
            with self.subTest(path=path):
                res = self._fetch(path)
                self.assertEqual(res.status, 200)
                content_type = res.headers.get("Content-Type", "")
                self.assertIn(expected_mime, content_type)
                content = res.read()
                self.assertGreater(len(content), 0)

    def test_api_health(self):
        """GET /api/health should return ok and zero_state mode."""
        res = self._fetch("/api/health")
        self.assertEqual(res.status, 200)
        self.assertIn("application/json", res.headers.get("Content-Type", ""))
        data = json.loads(res.read().decode("utf-8"))
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("mode"), "zero_state")
        self.assertEqual(data.get("version"), "0.1.0")

    def test_api_state_zero_state_preservation(self):
        """GET /api/state MUST strictly uphold the 0.0% zero-state invariant."""
        res = self._fetch("/api/state")
        self.assertEqual(res.status, 200)
        state = json.loads(res.read().decode("utf-8"))

        self.assertEqual(state.get("version"), "0.1.0")
        stats = state.get("global_stats", {})
        self.assertEqual(stats.get("total_tasks"), 75, "Total verification tasks must equal 75")
        self.assertEqual(stats.get("completed_tasks"), 0, "Completed tasks must equal 0")
        self.assertEqual(stats.get("blocked_tasks"), 0, "Blocked tasks must equal 0")
        self.assertEqual(stats.get("progress_percent"), 0.0, "Progress percentage must equal 0.0%")

        circles = state.get("circles", [])
        self.assertEqual(len(circles), 7, "Macro-Circles C0 through C6 must exist")
        circle_ids = [c["id"] for c in circles]
        self.assertEqual(circle_ids, ["C0", "C1", "C2", "C3", "C4", "C5", "C6"])

        # Count individual tasks
        counted_tasks = 0
        for circle in circles:
            for heading in circle.get("main_headings", []):
                for sub in heading.get("sub_headings", []):
                    counted_tasks += len(sub.get("tasks", []))
        self.assertEqual(counted_tasks, 75, "Sum of all tasks in schema must exactly equal 75")

    def test_api_state_post_mutation(self):
        """POST /api/state should persist state changes and return 200 ok."""
        # Fetch current state first
        res = self._fetch("/api/state")
        current_state = json.loads(res.read().decode("utf-8"))

        # Mutate notes on a task
        current_state["notes"] = "Test mutation verification."
        payload = json.dumps(current_state).encode("utf-8")

        res_post = self._fetch(
            "/api/state",
            method="POST",
            body=payload,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(res_post.status, 200)
        res_data = json.loads(res_post.read().decode("utf-8"))
        self.assertEqual(res_data.get("status"), "ok")

        # Verify persisted state
        res_after = self._fetch("/api/state")
        updated_state = json.loads(res_after.read().decode("utf-8"))
        self.assertEqual(updated_state.get("notes"), "Test mutation verification.")

    def test_api_telemetry_get(self):
        """GET /api/telemetry should return JSON array of audit events."""
        res = self._fetch("/api/telemetry?limit=50")
        self.assertEqual(res.status, 200)
        events = json.loads(res.read().decode("utf-8"))
        self.assertIsInstance(events, list)

    def test_cors_preflight(self):
        """OPTIONS /api/state should return HTTP 204 with CORS headers."""
        res = self._fetch("/api/state", method="OPTIONS")
        self.assertEqual(res.status, 204)
        self.assertEqual(res.headers.get("Access-Control-Allow-Origin"), "*")
        self.assertIn("GET", res.headers.get("Access-Control-Allow-Methods", ""))

    def test_not_found_handling(self):
        """Unknown endpoints must return 404 Not Found."""
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._fetch("/api/nonexistent_route_404")
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
