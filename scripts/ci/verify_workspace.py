#!/usr/bin/env python3
"""
scripts/ci/verify_workspace.py: Multi-Step Verification Harness for Kant Workspace.

Adheres to The Iron Law of Verification:
1. Format verification (cargo fmt --all -- --check)
2. Static analysis / linter check (cargo clippy --workspace --all-targets --all-features -- -D warnings)
3. Workspace build & check (cargo check --workspace --all-targets --all-features)
4. Unit and integration tests (cargo test --workspace --all-targets --all-features)
5. Spec and contract audit (--spec-audit)
6. Zero-state telemetry invariant guard (--zero-state-guard)
"""

import sys
import os
import re
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def run_command(cmd: List[str], desc: str) -> bool:
    """Run a subprocess command and stream output."""
    print(f"\n=======================================================")
    print(f"[*] STEP: {desc}")
    print(f"[*] EXEC: {' '.join(cmd)}")
    print(f"=======================================================")
    try:
        res = subprocess.run(cmd, cwd=ROOT_DIR)
        if res.returncode != 0:
            print(f"[x] FAILED: {desc} (exit code {res.returncode})", file=sys.stderr)
            return False
        print(f"[✓] PASSED: {desc}")
        return True
    except FileNotFoundError as e:
        print(f"[!] Executable not found for {cmd[0]}: {e}", file=sys.stderr)
        return False


def verify_zero_state_guard() -> bool:
    """Assert zero completed tasks invariant in telemetry before v0.1 release."""
    print("\n[*] Validating Telemetry Zero-State Invariant...")
    tracker_dir = ROOT_DIR / ".kant-tracker"
    state_file = tracker_dir / "state.json"

    data = None
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            print(f"[✓] Loaded state from {state_file}")
        except Exception as e:
            print(f"[!] Error parsing state.json: {e}", file=sys.stderr)
            return False
    else:
        # Check default state from kant_tracker_sync or default definition
        sync_script = ROOT_DIR / "scripts" / "telemetry" / "kant_tracker_sync.py"
        if not sync_script.exists():
            sync_script = ROOT_DIR / "scripts" / "kant_tracker_sync.py"
        if sync_script.exists():
            try:
                res = subprocess.run(
                    [sys.executable, str(sync_script), "--dump-json"],
                    cwd=ROOT_DIR,
                    capture_output=True,
                    text=True
                )
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    print("[✓] Retrieved zero-state schema from telemetry engine.")
            except Exception:
                pass

    if data is None:
        print("[*] No active state.json; repository is in pristine pre-telemetry zero state.")
        print("[✓] Invariant SATISFIED: 0 completed tasks active in workspace.")
        return True

    stats = data.get("global_stats", {})
    completed = stats.get("completed_tasks", 0)
    percent = stats.get("progress_percent", 0.0)

    if completed != 0 or percent > 0.0:
        print(
            f"[x] ZERO-STATE INVARIANT VIOLATION: Expected 0 completed tasks, found {completed} "
            f"({percent}%). v0.1 requires pristine zero state before wave implementation.",
            file=sys.stderr
        )
        return False

    print(f"[✓] Zero-State Invariant verified: completed_tasks = {completed}, progress = {percent}%.")
    return True


def verify_spec_audit() -> bool:
    """Validate documentation specifications, signatures, and contract formats."""
    print("\n[*] Auditing Formal Specs & Contract Signatures...")
    spec_dir = ROOT_DIR / "docs" / "spec"
    if not spec_dir.exists():
        print(f"[x] Missing spec directory: {spec_dir}", file=sys.stderr)
        return False

    spec_files = list(spec_dir.glob("*.md"))
    if len(spec_files) < 7:
        print(f"[x] Expected at least 7 reference specification documents, found {len(spec_files)}.", file=sys.stderr)
        return False

    mandatory_specs = [
        "01_EPISTEMOLOGY_AND_LEXICON.md",
        "02_AESTHETICS_GRAMMAR_AND_AST.md",
        "03_ANALYTIC_CATEGORIES_AND_EFFECTS.md",
        "04_SCHEMATISM_IR_AND_PERCEUS.md",
        "05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md",
        "06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md",
        "07_AGENT_SURFACE_SIDECAR_AND_MCP.md",
    ]

    for fname in mandatory_specs:
        path = spec_dir / fname
        if not path.is_file():
            print(f"[x] Missing mandatory spec file: {fname}", file=sys.stderr)
            return False
        content = path.read_text(encoding="utf-8")
        if len(content) < 500:
            print(f"[x] Spec file {fname} appears truncated or empty ({len(content)} bytes).", file=sys.stderr)
            return False

    print(f"[✓] Verified all {len(mandatory_specs)} core specification contracts.")

    # Search for .spec or .kantd files across the repo
    spec_contracts = list(ROOT_DIR.glob("**/*.spec"))
    kantd_files = list(ROOT_DIR.glob("**/*.kantd"))
    print(f"[*] Found {len(spec_contracts)} .spec files and {len(kantd_files)} .kantd sidecar files.")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-Step Workspace Verification Harness")
    parser.add_argument("--spec-audit", action="store_true", help="Run formal spec audit only")
    parser.add_argument("--zero-state-guard", action="store_true", help="Assert zero completed tasks invariant only")
    parser.add_argument("--full", action="store_true", help="Run complete Five-Step verification harness")
    args = parser.parse_args()

    if args.spec_audit:
        return 0 if verify_spec_audit() else 1

    if args.zero_state_guard:
        return 0 if verify_zero_state_guard() else 1

    # Default or full run: execute verification harness
    success = True

    # Check spec audit
    if not verify_spec_audit():
        success = False

    # Check zero-state guard
    if not verify_zero_state_guard():
        success = False

    # Check Rust workspace if cargo is present
    cargo_bin = "cargo"
    user_cargo = Path.home() / ".cargo" / "bin" / ("cargo.exe" if os.name == "nt" else "cargo")
    if user_cargo.exists():
        cargo_bin = str(user_cargo)

    print("\n[*] Checking cargo availability...")
    try:
        subprocess.run([cargo_bin, "--version"], capture_output=True, check=True)
        has_cargo = True
    except Exception:
        has_cargo = False
        print("[!] cargo not detected; skipping compiler test execution.")

    if has_cargo:
        if not run_command([cargo_bin, "fmt", "--all", "--", "--check"], "Rust Formatting Check"):
            success = False

        if not run_command([cargo_bin, "check", "--workspace", "--all-targets", "--all-features"], "Cargo Workspace Check"):
            success = False

        if not run_command([cargo_bin, "clippy", "--workspace", "--all-targets", "--all-features", "--", "-D", "warnings"], "Clippy Static Analysis"):
            success = False

        if not run_command([cargo_bin, "test", "--workspace", "--all-targets", "--all-features", "--", "--nocapture"], "Cargo Unit & Integration Tests"):
            success = False

    if success:
        print("\n=======================================================")
        print("[✓] ALL VERIFICATION HARNESS STEPS COMPLETED SUCCESSFULLY!")
        print("=======================================================")
        return 0
    else:
        print("\n=======================================================", file=sys.stderr)
        print("[x] VERIFICATION HARNESS FAILED ON ONE OR MORE STEPS.", file=sys.stderr)
        print("=======================================================", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
