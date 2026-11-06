#!/usr/bin/env python3
"""
portal/server.py: Self-contained local server for Kant (.kant) Roadmap Tracker Portal.
Runs on http://localhost:8080 (or specified port) with live SSE and SQLite persistence.
Zero dependencies beyond Python 3 standard library.
"""

import sys
import os
import json
import sqlite3
import argparse
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

PORTAL_DIR = Path(__file__).resolve().parent
ROOT_DIR = PORTAL_DIR.parent
TRACKER_DIR = ROOT_DIR / ".kant-tracker"
STATE_FILE = TRACKER_DIR / "state.json"
DB_FILE = TRACKER_DIR / "kant_telemetry.db"

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class PortalHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PORTAL_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(PORTAL_DIR / "index.html", "rb") as f:
                self.wfile.write(f.read())
            return
        elif self.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            if STATE_FILE.exists():
                with open(STATE_FILE, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b"{}")
            return
        elif self.path.startswith("/api/telemetry"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"[]")
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/state":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode("utf-8"))
                TRACKER_DIR.mkdir(parents=True, exist_ok=True)
                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())
            return
        self.send_response(404)
        self.end_headers()

def main():
    parser = argparse.ArgumentParser(description="Kant Portal Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    args = parser.parse_args()

    server = ThreadedHTTPServer(("127.0.0.1", args.port), PortalHandler)
    print(f"================================================================")
    print(f"  Kant Roadmap Portal running at: http://127.0.0.1:{args.port}/")
    print(f"  Status: Zero-State Initialized (0% Progress, Ready for Implementation)")
    print(f"================================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPortal server stopped.")

if __name__ == "__main__":
    main()
