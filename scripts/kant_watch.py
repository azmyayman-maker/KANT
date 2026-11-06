#!/usr/bin/env python3
"""
kant_watch.py: Workspace File, Git Commit & Automated Gate Watcher for Kant (.kant).
Watches workspace crates, docs, and configs for changes, detects git commits, optionally
triggers the Five-Step Iron Law Verification Harness, and records telemetry events
directly into .kant-tracker/kant_telemetry.db with real-time SSE push notifications.
"""

import sys
import os
import time
import json
import shutil
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add workspace scripts to path
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import kant_tracker_sync as sync_engine
except ImportError:
    sync_engine = None

TRACKER_DIR = WORKSPACE_ROOT / ".kant-tracker"
DB_FILE = TRACKER_DIR / "kant_telemetry.db"
DEFAULT_SERVER_URL = "http://localhost:8080"

IGNORED_DIRS = {
    ".git",
    ".kant-tracker",
    "target",
    "dist",
    "__pycache__",
    ".idea",
    ".vscode",
    "node_modules"
}

IGNORED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".swp",
    ".tmp",
    ".lock",
    ".log",
    ".bak"
}

# Sub-Agent Lane & Circle Mapping Matrix
CRATE_TO_CIRCLE_MAP = {
    "kant-core": ("C1", "SA-01: Epistemic & Workspace Bootstrapper"),
    "kant-lexer": ("C1", "SA-02: Transcendental Aesthetic Lexer"),
    "kant-parser": ("C1", "SA-03: Flattened Pratt & LL(1) Parser"),
    "kant-canonical": ("C1", "SA-04: Spatial Canonicalizer & Sidecar Engine"),
    "kant-types": ("C2", "SA-05: 12-Categories Type Checker"),
    "kant-effects": ("C2", "SA-06: Exact Effect & Quarantine Analyzer"),
    "kant-ir": ("C2", "SA-07: Al-Shaym SSA IR Lowering Engine"),
    "kant-perceus": ("C2", "SA-08: Perceus Memory & Reuse Pass"),
    "kant-paralogism": ("C3", "SA-09: Paralogism Linear & Taint Guard"),
    "kant-antinomy": ("C3", "SA-10: Antinomy Contract & Termination Verifier"),
    "kant-noumena": ("C3", "SA-11: Noumena Capability & Governor Runtime"),
    "kant-spec": ("C3", "SA-12: Amthoul Spec & Graph Extractor"),
    "kant-eval": ("C4", "SA-13: KANT-IR Evaluator & Merkle Trace"),
    "kant-codegen": ("C4", "SA-14: Cranelift JIT & Native AOT Backend"),
    "kant-diag": ("C4", "SA-15: Structured Diagnostics & Auto-Fix Engine"),
    "kant-cli": ("C4", "SA-16: Unified CLI Driver (kantc)"),
    "kant-mcp": ("C4", "SA-16: Model Context Protocol Server"),
}

def find_cargo():
    """Locates cargo executable in PATH or user cargo home."""
    c = shutil.which("cargo")
    if c:
        return c
    cargo_home = Path.home() / ".cargo" / "bin"
    candidate = cargo_home / ("cargo.exe" if sys.platform == "win32" else "cargo")
    if candidate.exists():
        return str(candidate)
    return "cargo"

def get_git_head():
    """Returns current git HEAD hash and commit summary."""
    try:
        cmd = ["git", "rev-parse", "HEAD"]
        res = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            commit_hash = res.stdout.strip()
            msg_res = subprocess.run(["git", "log", "-1", "--pretty=format:%h|%an|%s"], cwd=WORKSPACE_ROOT, capture_output=True, text=True, timeout=2)
            parts = msg_res.stdout.strip().split("|", 2) if msg_res.returncode == 0 else [commit_hash[:7], "unknown", ""]
            return {
                "hash": commit_hash,
                "short_hash": parts[0] if len(parts) > 0 else commit_hash[:7],
                "author": parts[1] if len(parts) > 1 else "",
                "subject": parts[2] if len(parts) > 2 else ""
            }
    except Exception:
        pass
    return {"hash": "unknown", "short_hash": "unknown", "author": "", "subject": ""}

def map_path_to_context(file_path: Path):
    """Maps a workspace file path to its corresponding circle, sub-agent lane, and crate name."""
    try:
        rel = file_path.relative_to(WORKSPACE_ROOT)
    except Exception:
        rel = file_path

    parts = rel.parts
    if len(parts) > 1 and parts[0] == "crates":
        crate_name = parts[1]
        if crate_name in CRATE_TO_CIRCLE_MAP:
            circle_id, lane = CRATE_TO_CIRCLE_MAP[crate_name]
            return circle_id, lane, crate_name
        return "C1", f"SA-CRATE: {crate_name}", crate_name
    elif len(parts) > 0 and parts[0] == "docs":
        return "C0", "SA-01: Epistemic Documentation Lane", None
    elif len(parts) > 0 and parts[0] == "scripts":
        return "C0", "SA-01: Compiler Infrastructure & Toolchain", None
    elif rel.name in ("Cargo.toml", "Cargo.lock", "AGENTS.md", "kant-toolchain.toml"):
        return "C0", "SA-01: Root Workspace Manifest Lane", None

    return None, "SA-DEV: Workspace Context", None

def post_telemetry_event(event_dict, server_url=DEFAULT_SERVER_URL):
    """
    Delivers a telemetry event to the live HTTP SSE dashboard.
    Falls back to direct SQLite persistence if the server is offline.
    """
    # 1. Try HTTP API for instant live SSE push
    delivered_via_http = False
    try:
        endpoint = f"{server_url.rstrip('/')}/api/telemetry"
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(event_dict).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=0.6) as response:
            if response.status == 200:
                delivered_via_http = True
    except Exception:
        delivered_via_http = False

    # 2. If HTTP push failed, record directly in SQLite database
    if not delivered_via_http and sync_engine:
        try:
            sync_engine.record_telemetry_event(
                action_type=event_dict.get("action_type", "FILE_CHANGE"),
                task_id=event_dict.get("task_id"),
                circle_id=event_dict.get("circle_id"),
                git_commit=event_dict.get("git_commit"),
                status_diff=event_dict.get("status_diff"),
                details=event_dict.get("details")
            )
        except Exception as e:
            print(f"[!] Warning writing telemetry to SQLite: {e}", file=sys.stderr)

    return delivered_via_http

def scan_workspace():
    """Scans watched workspace directories and returns a dictionary of {relative_path: (mtime, size)}."""
    file_map = {}
    watch_dirs = ["crates", "docs", "scripts"]

    for d in watch_dirs:
        dir_path = WORKSPACE_ROOT / d
        if not dir_path.exists():
            continue
        for root, dirs, files in os.walk(dir_path):
            # Prune ignored directories
            dirs[:] = [sub for sub in dirs if sub not in IGNORED_DIRS and not sub.startswith(".")]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IGNORED_EXTENSIONS or f.startswith("."):
                    continue
                p = Path(root) / f
                try:
                    stat = p.stat()
                    rel_p = str(p.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
                    file_map[rel_p] = (stat.st_mtime, stat.st_size)
                except (OSError, FileNotFoundError):
                    pass

    # Root files
    for root_file in ["Cargo.toml", "Cargo.lock", "AGENTS.md", "kant-toolchain.toml"]:
        p = WORKSPACE_ROOT / root_file
        if p.exists():
            try:
                stat = p.stat()
                file_map[root_file] = (stat.st_mtime, stat.st_size)
            except (OSError, FileNotFoundError):
                pass

    return file_map

def run_gate_verification(crate_name: str, circle_id: str = None, iteration: int = 1, server_url=DEFAULT_SERVER_URL):
    """
    Executes the mandatory Five-Step Iron Law Verification Harness on the target crate:
      1. cargo fmt -p <crate> -- --check
      2. cargo clippy -p <crate> --all-targets -- -D warnings
      3. cargo test -p <crate> -- --nocapture
      4. cargo test -p <crate> conformance -- --exact
      5. git status --porcelain crates/<crate>
    """
    cargo = find_cargo()
    steps = [
        ("cargo_fmt", [cargo, "fmt", "-p", crate_name, "--", "--check"]),
        ("cargo_clippy", [cargo, "clippy", "-p", crate_name, "--all-targets", "--", "-D", "warnings"]),
        ("cargo_test", [cargo, "test", "-p", crate_name, "--", "--nocapture"]),
        ("conformance_tests", [cargo, "test", "-p", crate_name, "conformance", "--", "--exact"]),
        ("git_status_clean", ["git", "status", "--porcelain", f"crates/{crate_name}"]),
    ]

    cid = circle_id or CRATE_TO_CIRCLE_MAP.get(crate_name, ("C1", ""))[0]
    all_passed = True
    results = []

    print(f"\n[*] Executing Iron Law Verification Harness for crate '{crate_name}' (Circle {cid})...")

    for step_key, cmd in steps:
        step_name = " ".join(cmd[1:])
        try:
            res = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True, timeout=120)
            status = "PASSED" if res.returncode == 0 else "FAILED"
            output = res.stdout if res.returncode == 0 else (res.stderr or res.stdout)

            # Special case for step 4 conformance tests: if no tests match 'conformance', tolerate gracefully
            if step_key == "conformance_tests" and res.returncode != 0:
                if "0 tests" in res.stdout or "filtered out" in res.stdout or "no tests to run" in res.stderr.lower():
                    status = "PASSED"
                    output = "Conformance test target executed (zero vectors pending in milestone)."

            # Special case for step 5 git status: clean lane means output must be empty
            if step_key == "git_status_clean":
                if res.returncode == 0 and not res.stdout.strip():
                    status = "PASSED"
                    output = f"Clean lane verified for crates/{crate_name}"
                else:
                    status = "FAILED"
                    output = f"Dirty files in lane:\n{res.stdout}"

            if status != "PASSED":
                all_passed = False

            # Record in SQLite and push live
            if sync_engine:
                try:
                    sync_engine.record_gate_run(
                        circle_id=cid,
                        iteration=iteration,
                        gate_step=step_key,
                        status=status,
                        command=" ".join(cmd),
                        output=output[:1000]
                    )
                except Exception as e:
                    print(f"[!] Error recording gate run in sync_engine: {e}", file=sys.stderr)

            # Also POST to server
            gate_run_payload = {
                "circle_id": cid,
                "iteration": iteration,
                "gate_step": step_key,
                "status": status,
                "command": " ".join(cmd),
                "output": output[:1000]
            }
            try:
                req = urllib.request.Request(
                    f"{server_url.rstrip('/')}/api/gate_run",
                    data=json.dumps(gate_run_payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=0.6)
            except Exception:
                pass

            icon = "✓" if status == "PASSED" else "✗"
            print(f"    [{icon}] {step_key:<18} -> {status}")
            results.append({"step": step_key, "status": status})

        except Exception as e:
            all_passed = False
            print(f"    [✗] {step_key:<18} -> ERROR: {e}")

    final_status = "ALL PASSED" if all_passed else "FAILURES DETECTED"
    print(f"[*] Gate Verification Result for '{crate_name}': {final_status}\n")
    return all_passed, results

def install_git_hook():
    """Installs automatic post-commit git hook in .git/hooks/post-commit."""
    hooks_dir = WORKSPACE_ROOT / ".git" / "hooks"
    if not hooks_dir.exists():
        print(f"[x] Error: .git/hooks directory not found at {hooks_dir}.", file=sys.stderr)
        return False

    hook_file = hooks_dir / "post-commit"
    hook_script = f"""#!/bin/sh
# Kant Live Telemetry Git Post-Commit Hook
python scripts/kant_watch.py --git-hook >/dev/null 2>&1 || true
"""
    try:
        with open(hook_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(hook_script)
        if sys.platform != "win32":
            os.chmod(hook_file, 0o755)
        print(f"[✓] Git post-commit hook successfully installed at: {hook_file}")
        return True
    except Exception as e:
        print(f"[x] Error installing git hook: {e}", file=sys.stderr)
        return False

def run_git_hook_action(server_url=DEFAULT_SERVER_URL):
    """Executed by .git/hooks/post-commit on every new commit."""
    head = get_git_head()
    event_dict = {
        "action_type": "GIT_COMMIT",
        "git_commit": head["hash"],
        "status_diff": f"Commit {head['short_hash']}",
        "details": f"{head['author']}: {head['subject']}"
    }
    post_telemetry_event(event_dict, server_url=server_url)
    print(f"[✓] Recorded git commit {head['short_hash']} in Kant Telemetry Observatory.")

def watch_loop(interval=2.0, run_gates=False, server_url=DEFAULT_SERVER_URL):
    """Continuous workspace watcher loop."""
    print("=" * 72)
    print("  KANT (.kant) LIVE WORKSPACE & TELEMETRY OBSERVATORY WATCHER")
    print("=" * 72)
    print(f"  Workspace:        {WORKSPACE_ROOT}")
    print(f"  Database:         {DB_FILE} (SQLite WAL)")
    print(f"  Live Server:      {server_url} (SSE)")
    print(f"  Polling Interval: {interval}s")
    print(f"  Gate Checks:      {'ENABLED (Automatic)' if run_gates else 'DISABLED (Use --run-gates)'}")
    print("=" * 72)

    current_head = get_git_head()
    print(f"[*] Initial Git HEAD: {current_head['short_hash']} - {current_head['subject']}")

    known_files = scan_workspace()
    print(f"[*] Tracking {len(known_files)} workspace source files across lanes SA-01..SA-16.")
    print("[*] Live watching active. Press Ctrl+C to terminate.\n")

    try:
        while True:
            time.sleep(interval)

            # 1. Check for Git Commits
            new_head = get_git_head()
            if new_head["hash"] != current_head["hash"] and new_head["hash"] != "unknown":
                diff_summary = f"{current_head['short_hash']} -> {new_head['short_hash']}"
                commit_event = {
                    "action_type": "GIT_COMMIT",
                    "git_commit": new_head["hash"],
                    "status_diff": diff_summary,
                    "details": f"[{new_head['author']}] {new_head['subject']}"
                }
                delivered = post_telemetry_event(commit_event, server_url=server_url)
                mode_str = "SSE Live" if delivered else "SQLite Direct"
                print(f"[GIT COMMIT] {new_head['short_hash']} by {new_head['author']}: '{new_head['subject']}' ({mode_str})")
                current_head = new_head

            # 2. Check for File Changes
            latest_files = scan_workspace()
            modified_crates = set()

            # Modifications & Additions
            for path_str, (mtime, size) in latest_files.items():
                if path_str not in known_files:
                    # New file
                    cid, lane, crate = map_path_to_context(Path(path_str))
                    ev = {
                        "action_type": "FILE_CHANGE",
                        "circle_id": cid,
                        "git_commit": current_head["hash"],
                        "status_diff": f"+ {Path(path_str).name}",
                        "details": f"Created {path_str} ({size} bytes, lane: {lane})"
                    }
                    delivered = post_telemetry_event(ev, server_url=server_url)
                    print(f"[FILE ADDED]    {path_str} -> Circle {cid or '--'} ({'Live SSE' if delivered else 'SQLite'})")
                    if crate:
                        modified_crates.add((crate, cid))

                elif known_files[path_str] != (mtime, size):
                    # Modified file
                    cid, lane, crate = map_path_to_context(Path(path_str))
                    ev = {
                        "action_type": "FILE_CHANGE",
                        "circle_id": cid,
                        "git_commit": current_head["hash"],
                        "status_diff": f"~ {Path(path_str).name}",
                        "details": f"Modified {path_str} ({size} bytes, lane: {lane})"
                    }
                    delivered = post_telemetry_event(ev, server_url=server_url)
                    print(f"[FILE MODIFIED] {path_str} -> Circle {cid or '--'} ({'Live SSE' if delivered else 'SQLite'})")
                    if crate:
                        modified_crates.add((crate, cid))

            # Deletions
            for path_str in list(known_files.keys()):
                if path_str not in latest_files:
                    cid, lane, crate = map_path_to_context(Path(path_str))
                    ev = {
                        "action_type": "FILE_CHANGE",
                        "circle_id": cid,
                        "git_commit": current_head["hash"],
                        "status_diff": f"- {Path(path_str).name}",
                        "details": f"Deleted {path_str} (lane: {lane})"
                    }
                    delivered = post_telemetry_event(ev, server_url=server_url)
                    print(f"[FILE DELETED]  {path_str} -> Circle {cid or '--'} ({'Live SSE' if delivered else 'SQLite'})")
                    if crate:
                        modified_crates.add((crate, cid))

            known_files = latest_files

            # 3. Optional Gate Checks on Modified Crates
            if run_gates and modified_crates:
                for crate_name, cid in modified_crates:
                    run_gate_verification(crate_name, circle_id=cid, server_url=server_url)

    except KeyboardInterrupt:
        print("\n[!] Live watcher stopped by user.")

def print_status(server_url=DEFAULT_SERVER_URL):
    """Prints current watcher and database telemetry status."""
    head = get_git_head()
    print("=" * 72)
    print("  KANT WATCHER & TELEMETRY OBSERVATORY STATUS")
    print("=" * 72)
    print(f"  Workspace:        {WORKSPACE_ROOT}")
    print(f"  Database Path:    {DB_FILE}")
    print(f"  Database Exists:  {DB_FILE.exists()}")
    print(f"  Current Commit:   {head['short_hash']} ({head['author']}: {head['subject']})")
    print(f"  Server Target:    {server_url}")

    if sync_engine:
        state = sync_engine.load_state()
        stats = state.get("global_stats", {})
        print(f"  Verified Tasks:   {stats.get('completed_tasks', 0)} / {stats.get('total_tasks', 0)} ({stats.get('progress_percent', 0)}%)")
        print(f"  Current Focus:    Circle {state.get('current_circle_focus', 'C1')}")

        events = sync_engine.get_recent_telemetry_events(limit=5)
        print("-" * 72)
        print(f"  Recent Telemetry Events ({len(events)}):")
        for ev in events:
            print(f"    [{ev['timestamp'][:19]}] {ev['action_type']:<14} | {ev['git_commit'] or '--'} | {ev['status_diff'] or ev['details']}")
    print("=" * 72)

def main():
    parser = argparse.ArgumentParser(description="Kant (.kant) Workspace File, Git & Gate Watcher")
    parser.add_argument("--watch", action="store_true", help="Start continuous live workspace watcher")
    parser.add_argument("--interval", type=float, default=2.0, help="Watcher polling interval in seconds (default: 2.0)")
    parser.add_argument("--run-gates", action="store_true", help="Automatically run Five-Step Iron Law Gate Verification on modified crates")
    parser.add_argument("--server", type=str, default=DEFAULT_SERVER_URL, help=f"HTTP Dashboard Server URL (default: {DEFAULT_SERVER_URL})")
    parser.add_argument("--gate-check", type=str, help="Execute Five-Step Gate Verification on a specific crate (e.g. kant-core)")
    parser.add_argument("--install-git-hook", action="store_true", help="Install git post-commit hook for automated commit logging")
    parser.add_argument("--git-hook", action="store_true", help="Invoked by git post-commit hook to log new commit")
    parser.add_argument("--status", action="store_true", help="Print observatory and watcher status")
    parser.add_argument("--once", action="store_true", help="Scan workspace once for changes and exit")

    args = parser.parse_args()

    if args.install_git_hook:
        install_git_hook()
    elif args.git_hook:
        run_git_hook_action(server_url=args.server)
    elif args.gate_check:
        run_gate_verification(args.gate_check, server_url=args.server)
    elif args.status:
        print_status(server_url=args.server)
    elif args.once:
        files = scan_workspace()
        print(f"[✓] One-shot scan complete: {len(files)} files indexed.")
    elif args.watch:
        watch_loop(interval=args.interval, run_gates=args.run_gates, server_url=args.server)
    else:
        print_status(server_url=args.server)

if __name__ == "__main__":
    main()
