#!/usr/bin/env python3
"""
portal/server.py: Root convenience entrypoint for the Kant Observatory Telemetry Portal.
Seamlessly delegates to the decoupled, thread-safe modular backend package: portal.backend.server.
"""

import argparse
import sys
from pathlib import Path

# Ensure portal package is resolvable
PORTAL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PORTAL_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from portal.backend.server import run_server


def main():
    parser = argparse.ArgumentParser(
        description="Kant Observatory Modular Telemetry Portal (v0.1.0)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind HTTP server to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on",
    )
    args = parser.parse_args()

    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
