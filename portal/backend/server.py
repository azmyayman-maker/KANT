"""
Kant Compiler Toolchain - Threaded HTTP & SSE Server Implementation
Zero external dependencies beyond Python 3 standard library.
"""

import argparse
import sys
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Optional, Tuple

from .config import Config, get_config, set_config
from .database import TelemetryDatabase
from .routes import (
    handle_api_commits,
    handle_api_health,
    handle_api_state_get,
    handle_api_state_post,
    handle_api_telemetry,
    handle_options,
    handle_sse_stream,
    handle_static_get,
)
from .sse import SSEBroker


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTP server that processes each client connection in a separate thread."""
    daemon_threads = True
    allow_reuse_address = True


class PortalHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for the Kant Observatory Telemetry Portal."""

    server_version = "KantObservatory/0.1.0"

    def __init__(self, *args, **kwargs):
        # We handle directory routing explicitly via routes.py
        super().__init__(*args, **kwargs)

    @property
    def config(self) -> Config:
        return self.server.config  # type: ignore

    @property
    def db(self) -> TelemetryDatabase:
        return self.server.db  # type: ignore

    @property
    def broker(self) -> SSEBroker:
        return self.server.broker  # type: ignore

    def do_OPTIONS(self) -> None:
        handle_options(self, self.config)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/state":
            handle_api_state_get(self, self.config, self.db)
            return

        if path == "/api/events":
            handle_sse_stream(self, self.config, self.broker)
            return

        if path == "/api/health":
            handle_api_health(self, self.config, self.broker)
            return

        if path == "/api/telemetry":
            handle_api_telemetry(self, self.config, self.db, parsed.query)
            return

        if path == "/api/commits":
            handle_api_commits(self, self.config, self.db)
            return

        # Attempt static file resolution
        if handle_static_get(self, self.path, self.config):
            return

        self.send_error(404, f"Path not found: {path}")

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/state":
            handle_api_state_post(self, self.config, self.db, self.broker)
            return

        self.send_error(404, f"POST endpoint not found: {path}")

    def log_message(self, format: str, *args) -> None:
        """Suppress standard HTTP access logging in production to keep stdout pristine."""
        pass


def create_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    config: Optional[Config] = None,
) -> Tuple[ThreadedHTTPServer, TelemetryDatabase, SSEBroker]:
    """Factory creating the threaded HTTP server with database adapter and SSE broker."""
    cfg = config or get_config()
    if host:
        cfg.host = host
    if port:
        cfg.port = port
    set_config(cfg)

    cfg.ensure_directories()
    db = TelemetryDatabase(cfg.db_file)
    broker = SSEBroker(ping_interval_seconds=cfg.ping_interval_seconds)

    server = ThreadedHTTPServer((cfg.host, cfg.port), PortalHTTPRequestHandler)
    server.config = cfg  # type: ignore
    server.db = db  # type: ignore
    server.broker = broker  # type: ignore

    return server, db, broker


def run_server(host: Optional[str] = None, port: Optional[int] = None) -> None:
    """Convenience runner that creates and serves the portal indefinitely."""
    server, db, broker = create_server(host, port)
    cfg = server.config  # type: ignore

    # Record initial boot audit event
    db.record_event(
        level="AUDIT",
        agent="PORTAL",
        commit_hash="HEAD",
        message="Observatory Telemetry Portal started in strict 0.0% zero-state mode.",
    )

    print("================================================================")
    print(f"  Kant Observatory Portal: http://{cfg.host}:{cfg.port}/")
    print(f"  Architecture: Modular Python Backend + ES6 Frontend")
    print(f"  Status: Strict Zero-State (75 tasks, 0 completed, 0.0%)")
    print(f"  SSE Broker: Enabled at /api/events")
    print(f"  SQLite Telemetry: {cfg.db_file}")
    print("================================================================")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Kant Observatory Portal...")
    finally:
        broker.shutdown()
        server.server_close()
        print("Portal stopped successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kant Observatory Modular Telemetry Portal")
    parser.add_argument("--host", type=str, default=None, help="Host to listen on (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None, help="Port to listen on (default: 8080)")
    args = parser.parse_args()
    run_server(args.host, args.port)
