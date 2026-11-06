#!/usr/bin/env python3
"""
scripts/git/install_hooks.py: Git Hooks Installer for Kant (kantc) Workspace.

Installs and configures executable Git hooks:
- commit-msg: Enforces Conventional Commits 1.0.0 via scripts/git/validate_commit.py.
- pre-commit: Executes code formatting and zero-warning sanity checks before commit.
- post-commit: Logs commit metadata into telemetry DB if active.
"""

import sys
import os
import stat
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

COMMIT_MSG_HOOK = """#!/bin/sh
# Kant Git Hook: commit-msg
# Validates Conventional Commits format
python3 scripts/git/validate_commit.py "$1" || python scripts/git/validate_commit.py "$1"
"""

PRE_COMMIT_HOOK = """#!/bin/sh
# Kant Git Hook: pre-commit
# Checks multi-language formatting and workspace hygiene
python3 scripts/ci/check_format.py || python scripts/ci/check_format.py
"""

POST_COMMIT_HOOK = """#!/bin/sh
# Kant Git Hook: post-commit
# Updates telemetry database with commit metadata (best-effort)
python3 scripts/telemetry/kant_tracker_sync.py --record-commit >/dev/null 2>&1 || true
"""


def get_hooks_dir() -> Path:
    """Resolve Git hooks directory using git rev-parse or fallback."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--git-path", "hooks"],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(res.stdout.strip())
    except Exception:
        return Path(".git") / "hooks"


def install_hook(hooks_dir: Path, hook_name: str, script_content: str) -> bool:
    """Write hook script and mark executable."""
    hook_path = hooks_dir / hook_name
    try:
        hook_path.write_text(script_content, encoding="utf-8")
        # Set executable permissions on POSIX
        if os.name != "nt":
            mode = hook_path.stat().st_mode
            hook_path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"[✓] Installed hook: {hook_path}")
        return True
    except Exception as e:
        print(f"[!] Failed to install {hook_name}: {e}", file=sys.stderr)
        return False


def main() -> int:
    hooks_dir = get_hooks_dir()
    if not hooks_dir.parent.exists():
        print(f"[!] Git repository directory not found at {hooks_dir.parent}", file=sys.stderr)
        return 1

    hooks_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] Target hooks directory: {hooks_dir.resolve()}")

    s1 = install_hook(hooks_dir, "commit-msg", COMMIT_MSG_HOOK)
    s2 = install_hook(hooks_dir, "pre-commit", PRE_COMMIT_HOOK)
    s3 = install_hook(hooks_dir, "post-commit", POST_COMMIT_HOOK)

    if s1 and s2 and s3:
        print("[✓] All Git hooks successfully installed and active.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
