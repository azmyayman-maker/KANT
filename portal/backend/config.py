"""
Kant Compiler Toolchain - Backend Configuration
Resolves paths dynamically relative to workspace root and provides runtime settings.
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Runtime configuration for the Kant Observatory Telemetry Portal."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        tracker_dir: Optional[Path] = None,
    ):
        # Resolve paths relative to this config file
        self.backend_dir = Path(__file__).resolve().parent
        self.portal_dir = self.backend_dir.parent
        self.project_root = self.portal_dir.parent

        self.frontend_dir = self.portal_dir / "frontend"
        self.assets_dir = self.portal_dir / "assets"
        self.default_state_file = self.backend_dir / "default_state.json"

        # Host and Port configuration
        self.host = host or os.environ.get("KANT_PORTAL_HOST", "127.0.0.1")
        env_port = os.environ.get("KANT_PORTAL_PORT")
        self.port = port or (int(env_port) if env_port else 8080)

        # Telemetry directory and database paths
        if tracker_dir:
            self.tracker_dir = Path(tracker_dir).resolve()
        else:
            env_tracker = os.environ.get("KANT_TRACKER_DIR")
            self.tracker_dir = Path(env_tracker).resolve() if env_tracker else (self.project_root / ".kant-tracker")

        self.state_file = self.tracker_dir / "state.json"
        self.db_file = self.tracker_dir / "kant_telemetry.db"

        # Server Settings
        self.server_name = "KantObservatory/0.1.0"
        self.enable_cors = True
        self.cors_allowed_origins = ["*"]
        self.ping_interval_seconds = 15

    def ensure_directories(self) -> None:
        """Create tracker and runtime directories if they do not exist."""
        self.tracker_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "backend_dir": str(self.backend_dir),
            "frontend_dir": str(self.frontend_dir),
            "assets_dir": str(self.assets_dir),
            "tracker_dir": str(self.tracker_dir),
            "state_file": str(self.state_file),
            "db_file": str(self.db_file),
            "default_state_file": str(self.default_state_file),
        }


_global_config: Optional[Config] = None


def get_config() -> Config:
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def set_config(config: Config) -> None:
    global _global_config
    _global_config = config
