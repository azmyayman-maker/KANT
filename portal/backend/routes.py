"""
Kant Compiler Toolchain - HTTP Request Dispatchers and Route Handlers
Implements REST endpoints and SSE upgrade without external dependencies.
"""

import json
import mimetypes
import os
import urllib.parse
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .config import Config
from .database import TelemetryDatabase
from .sse import SSEBroker


MIME_MAP = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".ico": "image/x-icon",
    ".txt": "text/plain; charset=utf-8",
}


def get_mime_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    return MIME_MAP.get(suffix, mimetypes.guess_type(str(file_path))[0] or "application/octet-stream")


def handle_options(handler: Any, config: Config) -> None:
    """Handle CORS pre-flight OPTIONS request."""
    handler.send_response(HTTPStatus.NO_CONTENT)
    if config.enable_cors:
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Content-Length", "0")
    handler.end_headers()


def serve_file(handler: Any, file_path: Path, config: Config) -> None:
    """Serve a static file with appropriate headers and caching control."""
    if not file_path.is_file():
        handler.send_error(HTTPStatus.NOT_FOUND, f"File not found: {file_path.name}")
        return

    content_type = get_mime_type(file_path)
    try:
        content = file_path.read_bytes()
    except Exception as e:
        handler.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Error reading file: {e}")
        return

    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(content)))
    if config.enable_cors:
        handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Cache-Control", "no-cache, must-revalidate")
    handler.end_headers()
    handler.wfile.write(content)


def handle_static_get(handler: Any, path: str, config: Config) -> bool:
    """Route static frontend assets and icons. Returns True if handled."""
    parsed_path = urllib.parse.urlparse(path).path.lstrip("/")

    if parsed_path in ("", "index.html"):
        serve_file(handler, config.frontend_dir / "index.html", config)
        return True

    # Check under frontend directory (css/, js/, etc.)
    frontend_candidate = (config.frontend_dir / parsed_path).resolve()
    if frontend_candidate.is_relative_to(config.frontend_dir) and frontend_candidate.is_file():
        serve_file(handler, frontend_candidate, config)
        return True

    # Check under assets directory (assets/kant-icon.svg)
    if parsed_path.startswith("assets/"):
        asset_rel = parsed_path[len("assets/"):]
        asset_candidate = (config.assets_dir / asset_rel).resolve()
        if asset_candidate.is_relative_to(config.assets_dir) and asset_candidate.is_file():
            serve_file(handler, asset_candidate, config)
            return True

    return False


def get_current_state_data(config: Config, db: TelemetryDatabase) -> Dict[str, Any]:
    """Retrieve current state dict, initializing from default zero-state if needed."""
    if config.state_file.exists():
        try:
            with open(config.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Fall back to default state file
    if config.default_state_file.exists():
        try:
            with open(config.default_state_file, "r", encoding="utf-8") as f:
                default_data = json.load(f)
                # Seed into tracker directory
                config.ensure_directories()
                with open(config.state_file, "w", encoding="utf-8") as out_f:
                    json.dump(default_data, out_f, indent=2, ensure_ascii=False)
                db.record_state_snapshot(default_data)
                return default_data
        except Exception:
            pass

    # Minimal zero-state fallback
    minimal = {
        "version": "0.1.0",
        "current_circle_focus": "C0",
        "global_stats": {
            "total_tasks": 75,
            "completed_tasks": 0,
            "blocked_tasks": 0,
            "progress_percent": 0.0,
        },
        "circles": [],
    }
    return minimal


def handle_api_state_get(handler: Any, config: Config, db: TelemetryDatabase) -> None:
    """Handle GET /api/state."""
    state_data = get_current_state_data(config, db)
    payload = json.dumps(state_data, ensure_ascii=False).encode("utf-8")

    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    if config.enable_cors:
        handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(payload)


def handle_api_state_post(
    handler: Any,
    config: Config,
    db: TelemetryDatabase,
    broker: SSEBroker,
) -> None:
    """Handle POST /api/state to mutate roadmap progress."""
    content_length = int(handler.headers.get("Content-Length", 0))
    if content_length <= 0:
        handler.send_error(HTTPStatus.BAD_REQUEST, "Missing or empty request body")
        return

    body = handler.rfile.read(content_length)
    try:
        data = json.loads(body.decode("utf-8"))
    except Exception as e:
        handler.send_error(HTTPStatus.BAD_REQUEST, f"Malformed JSON: {e}")
        return

    config.ensure_directories()
    try:
        with open(config.state_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        handler.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to persist state: {e}")
        return

    # Record snapshot & audit event in database
    db.record_state_snapshot(data)
    stats = data.get("global_stats", {})
    pct = stats.get("progress_percent", 0.0)
    db.record_event(
        level="INFO",
        agent="PORTAL",
        commit_hash="HEAD",
        message=f"Roadmap state updated: {stats.get('completed_tasks', 0)}/{stats.get('total_tasks', 75)} tasks ({pct}%)",
    )

    # Broadcast via SSE
    broker.broadcast("state_update", data)

    response_body = b'{"status":"ok"}'
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(response_body)))
    if config.enable_cors:
        handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(response_body)


def handle_api_health(handler: Any, config: Config, broker: SSEBroker) -> None:
    """Handle GET /api/health."""
    payload = json.dumps({
        "status": "ok",
        "mode": "zero_state",
        "version": "0.1.0",
        "active_sse_clients": broker.client_count(),
    }).encode("utf-8")

    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    if config.enable_cors:
        handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(payload)


def handle_api_telemetry(handler: Any, config: Config, db: TelemetryDatabase, query_string: str) -> None:
    """Handle GET /api/telemetry."""
    params = urllib.parse.parse_qs(query_string)
    limit = int(params.get("limit", [100])[0])

    events = db.get_audit_events(limit=limit)
    payload = json.dumps(events, ensure_ascii=False).encode("utf-8")

    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    if config.enable_cors:
        handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(payload)


def handle_api_commits(handler: Any, config: Config, db: TelemetryDatabase) -> None:
    """Handle GET /api/commits."""
    commits = db.get_recent_commits(limit=50)
    payload = json.dumps(commits, ensure_ascii=False).encode("utf-8")

    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    if config.enable_cors:
        handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(payload)


def handle_sse_stream(handler: Any, config: Config, broker: SSEBroker) -> None:
    """Upgrade connection to SSE stream and push live events."""
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "text/event-stream; charset=utf-8")
    handler.send_header("Cache-Control", "no-cache, no-transform")
    handler.send_header("Connection", "keep-alive")
    handler.send_header("X-Accel-Buffering", "no")
    if config.enable_cors:
        handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()

    client_queue = broker.register_client()
    try:
        while True:
            msg = client_queue.get()
            if msg is None:  # Shutdown sentinel
                break
            handler.wfile.write(msg.encode("utf-8"))
            handler.wfile.flush()
    except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
        pass
    finally:
        broker.unregister_client(client_queue)
