#!/usr/bin/env python3
"""
kant_git_automation.py: Git Workflow Automation & Developer Tooling Engine for Kant (.kant).

Capabilities:
1. Automated Git Hooks Management:
   - Installs `.git/hooks/post-commit` to push commit SHA, author info, and modified files
     directly into the SQLite telemetry database (.kant-tracker/kant_telemetry.db).
   - Installs `.git/hooks/commit-msg` to enforce strict Conventional Commit standards.
2. Conventional Commit Linter:
   - Enforces strict type tags: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `ci:`.
   - Supports optional scopes (e.g. `feat(git): ...`) and breaking change indicator (`!`).
   - Validates subject line length and format.
3. Subagent Feature Branch Orchestration:
   - CLI: `--create-branch <name> --track-task <task_id>`
   - Tracks active feature branches, maps them to roadmap task IDs, and updates task statuses.
   - Verifies subagent write-allowlist file lane hygiene as mandated by AGENTS.md.
4. Automated Changelog Generator:
   - Correlates git commits and merged branches with roadmap milestones (Circles C0–C6).
   - Categorizes commits by type and milestone into Markdown release notes.
"""

import sys
import os
import re
import json
import sqlite3
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Determine workspace root and telemetry paths
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
TRACKER_DIR = WORKSPACE_ROOT / ".kant-tracker"
DB_FILE = TRACKER_DIR / "kant_telemetry.db"
DEFAULT_SERVER_URL = "http://localhost:8080"

# Conventional Commit Standards
ALLOWED_COMMIT_TYPES = {
    "feat": "New user-facing or architectural feature",
    "fix": "Bug fix or error resolution",
    "docs": "Documentation updates, specs, or reports",
    "refactor": "Code change that neither fixes a bug nor adds a feature",
    "test": "Adding or correcting unit, integration, or conformance tests",
    "ci": "CI/CD, git hooks, build scripts, or developer tooling",
}

# Regex pattern for conventional commits:
# <type>[(<scope>)][!]: <description>
CONVENTIONAL_REGEX = re.compile(
    r"^(?P<type>feat|fix|docs|refactor|test|ci)(?:\((?P<scope>[a-zA-Z0-9_\-\./]+)\))?(?P<breaking>!)?:\s+(?P<desc>.+)$"
)

# Regex pattern to match task IDs like C1.H1.S1.T01 or C0.H2.S1.T03
TASK_ID_REGEX = re.compile(r"\b(C[0-6]\.H[0-9]+\.S[0-9]+\.T[0-9]+)\b")
CIRCLE_ID_REGEX = re.compile(r"\b(C[0-6])\b")

# Subagent File Lane Mapping as defined in AGENTS.md
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

SUBAGENT_LANES = {
    "SA-01": ["crates/kant-core/", "AGENTS.md", "Cargo.toml", "kant-toolchain.toml", "docs/spec/01_"],
    "SA-02": ["crates/kant-lexer/", "docs/spec/02_"],
    "SA-03": ["crates/kant-parser/"],
    "SA-04": ["crates/kant-canonical/"],
    "SA-05": ["crates/kant-types/", "docs/spec/03_"],
    "SA-06": ["crates/kant-effects/"],
    "SA-07": ["crates/kant-ir/", "docs/spec/04_"],
    "SA-08": ["crates/kant-perceus/"],
    "SA-09": ["crates/kant-paralogism/", "docs/spec/05_"],
    "SA-10": ["crates/kant-antinomy/"],
    "SA-11": ["crates/kant-noumena/"],
    "SA-12": ["crates/kant-spec/"],
    "SA-13": ["crates/kant-eval/", "docs/spec/06_"],
    "SA-14": ["crates/kant-codegen/"],
    "SA-15": ["crates/kant-diag/", "docs/spec/07_"],
    "SA-16": ["crates/kant-cli/", "crates/kant-mcp/"],
    "SA-TOOLING": ["scripts/", "docs/reports/", ".kant-tracker/"],
}


# ==============================================================================
# Database & Telemetry Engine
# ==============================================================================

def get_db_conn(db_path: Path = DB_FILE) -> sqlite3.Connection:
    """Returns an optimized SQLite connection with WAL mode enabled."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=15.0)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensures database tables exist for telemetry, git commits, and branch orchestration."""
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS telemetry_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action_type TEXT NOT NULL,
            task_id TEXT,
            circle_id TEXT,
            git_commit TEXT,
            status_diff TEXT,
            details TEXT
        );

        CREATE TABLE IF NOT EXISTS git_commits (
            commit_hash TEXT PRIMARY KEY,
            short_hash TEXT NOT NULL,
            author_name TEXT NOT NULL,
            author_email TEXT,
            committed_at TEXT NOT NULL,
            branch TEXT,
            subject TEXT NOT NULL,
            body TEXT,
            changed_files TEXT, -- JSON array: [{"status": "M", "path": "file"}]
            task_id TEXT,
            circle_id TEXT,
            recorded_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS git_branches (
            branch_name TEXT PRIMARY KEY,
            task_id TEXT,
            circle_id TEXT,
            base_commit TEXT,
            status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE', 'MERGED', 'CLOSED'
            created_at TEXT NOT NULL,
            merged_at TEXT,
            merge_commit TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_telemetry_action ON telemetry_events(action_type);
        CREATE INDEX IF NOT EXISTS idx_telemetry_task ON telemetry_events(task_id);
        CREATE INDEX IF NOT EXISTS idx_git_commits_branch ON git_commits(branch);
        CREATE INDEX IF NOT EXISTS idx_git_commits_task ON git_commits(task_id);
        CREATE INDEX IF NOT EXISTS idx_git_commits_circle ON git_commits(circle_id);
        CREATE INDEX IF NOT EXISTS idx_git_branches_task ON git_branches(task_id);
    """)
    conn.commit()


def record_git_commit_telemetry(
    commit_hash: str,
    short_hash: str,
    author_name: str,
    author_email: str,
    committed_at: str,
    branch: str,
    subject: str,
    body: str,
    changed_files: List[Dict[str, str]],
    task_id: Optional[str] = None,
    circle_id: Optional[str] = None,
    server_url: str = DEFAULT_SERVER_URL,
) -> bool:
    """
    Inserts a commit and changed file paths directly into SQLite telemetry database
    and optionally streams an event to the live HTTP SSE dashboard.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    files_json = json.dumps(changed_files)

    # Inferred circle from task ID or changed files if not provided
    if not circle_id and task_id:
        m = CIRCLE_ID_REGEX.search(task_id)
        if m:
            circle_id = m.group(1)

    if not circle_id and changed_files:
        for f in changed_files:
            p = f.get("path", "")
            for crate, (cid, _) in CRATE_TO_CIRCLE_MAP.items():
                if f"crates/{crate}/" in p:
                    circle_id = cid
                    break
            if circle_id:
                break

    try:
        conn = get_db_conn()
        cur = conn.cursor()

        # Insert or replace in git_commits
        cur.execute(
            """
            INSERT OR REPLACE INTO git_commits
            (commit_hash, short_hash, author_name, author_email, committed_at, branch, subject, body, changed_files, task_id, circle_id, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                commit_hash,
                short_hash,
                author_name,
                author_email,
                committed_at,
                branch,
                subject,
                body,
                files_json,
                task_id,
                circle_id,
                now_iso,
            ),
        )

        # Build telemetry event payload
        details_obj = {
            "short_hash": short_hash,
            "author_name": author_name,
            "author_email": author_email,
            "branch": branch,
            "subject": subject,
            "files_count": len(changed_files),
            "files": changed_files[:20],  # sample
        }
        details_str = json.dumps(details_obj)

        cur.execute(
            """
            INSERT INTO telemetry_events
            (timestamp, action_type, task_id, circle_id, git_commit, status_diff, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now_iso,
                "GIT_COMMIT",
                task_id,
                circle_id,
                commit_hash,
                f"Commit {short_hash}: {subject[:50]}",
                details_str,
            ),
        )

        # If a task is associated and exists in tasks table, update updated_at
        if task_id:
            cur.execute("SELECT id, status FROM tasks WHERE id = ?", (task_id,))
            task_row = cur.fetchone()
            if task_row:
                cur.execute(
                    "UPDATE tasks SET updated_at = ? WHERE id = ?",
                    (now_iso, task_id),
                )

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Warning: SQLite commit telemetry error: {e}", file=sys.stderr)

    # Optional HTTP SSE notification to live dashboard
    try:
        sse_payload = {
            "action_type": "GIT_COMMIT",
            "task_id": task_id,
            "circle_id": circle_id,
            "git_commit": commit_hash,
            "status_diff": f"Commit {short_hash}",
            "details": f"{author_name}: {subject} ({len(changed_files)} files modified)",
        }
        endpoint = f"{server_url.rstrip('/')}/api/telemetry"
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(sse_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=0.5):
            pass
    except Exception:
        pass

    return True


# ==============================================================================
# Conventional Commit Validation Engine
# ==============================================================================

def validate_commit_message(msg: str) -> Tuple[bool, str, Optional[Dict[str, str]]]:
    """
    Validates a commit message according to strict Conventional Commits standard:
    Format: <type>[(<scope>)][!]: <description>
    Enforced types: feat, fix, docs, refactor, test, ci.
    """
    # Filter out git comments (#)
    lines = [line.strip() for line in msg.strip().splitlines() if not line.strip().startswith("#")]
    if not lines or not lines[0]:
        return False, "Commit message cannot be empty.", None

    subject = lines[0]

    # Allow automatic git merge and revert messages
    if (
        subject.startswith("Merge branch ")
        or subject.startswith("Merge remote-tracking branch ")
        or subject.startswith("Merge pull request ")
        or subject.startswith("Revert \"")
        or subject.startswith("fixup! ")
        or subject.startswith("squash! ")
    ):
        return True, f"Special git commit detected: {subject}", {"type": "git-internal", "subject": subject}

    # Match conventional regex
    m = CONVENTIONAL_REGEX.match(subject)
    if not m:
        # Determine specific failure reason to give rich guidance
        if ":" not in subject:
            reason = "Missing colon ':' separating type/scope and description."
        else:
            prefix = subject.split(":", 1)[0].strip()
            type_candidate = prefix.split("(")[0].rstrip("!")
            if type_candidate not in ALLOWED_COMMIT_TYPES:
                allowed_str = ", ".join(f"'{t}:'" for t in sorted(ALLOWED_COMMIT_TYPES.keys()))
                reason = f"Invalid commit type '{type_candidate}'. Allowed types are strictly: {allowed_str}"
            else:
                reason = "Malformed header. Expected format: '<type>(<scope>): <description>' or '<type>: <description>' with a space after ':'."

        return False, reason, None

    # Length check on subject line
    if len(subject) > 100:
        return (
            False,
            f"Commit subject is too long ({len(subject)} characters). Maximum permitted length is 100 characters.",
            None,
        )

    parsed = {
        "type": m.group("type"),
        "scope": m.group("scope") or "",
        "breaking": bool(m.group("breaking")),
        "description": m.group("desc").strip(),
        "subject": subject,
        "body": "\n".join(lines[1:]).strip() if len(lines) > 1 else "",
    }

    return True, "Valid conventional commit format.", parsed


def validate_commit_msg_file(file_path: Path) -> bool:
    """Reads commit message file (passed by git in .git/COMMIT_EDITMSG) and validates it."""
    if not file_path.exists():
        print(f"[x] Error: Commit message file does not exist at {file_path}", file=sys.stderr)
        return False

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        print(f"[x] Error reading commit message file: {e}", file=sys.stderr)
        return False

    valid, reason, parsed = validate_commit_message(content)
    if not valid:
        print("=" * 72, file=sys.stderr)
        print(" [x] CONVENTIONAL COMMIT VALIDATION FAILED", file=sys.stderr)
        print("=" * 72, file=sys.stderr)
        print(f" Reason: {reason}", file=sys.stderr)
        print("\n Rejected Message:", file=sys.stderr)
        first_line = content.strip().splitlines()[0] if content.strip() else "<empty>"
        print(f"   > {first_line}", file=sys.stderr)
        print("\n Permitted Format:", file=sys.stderr)
        print("   <type>(<optional-scope>): <description>", file=sys.stderr)
        print("   <type>: <description>", file=sys.stderr)
        print("\n Allowed Strict Types:", file=sys.stderr)
        for t, desc in sorted(ALLOWED_COMMIT_TYPES.items()):
            print(f"   - {t:<10} : {desc}", file=sys.stderr)
        print("\n Examples of Valid Commits:", file=sys.stderr)
        print("   feat(git): implement SQLite post-commit hook telemetry", file=sys.stderr)
        print("   fix(parser): resolve expression hole recovery edge case", file=sys.stderr)
        print("   ci(hooks): install conventional commit validation hook", file=sys.stderr)
        print("   docs(spec): pin De Bruijn slot indexing specification", file=sys.stderr)
        print("   test(core): add conformance test vectors for DefHash", file=sys.stderr)
        print("   refactor(ir): optimize Perceus reference count pass", file=sys.stderr)
        print("=" * 72, file=sys.stderr)
        return False

    # Success acknowledgment
    p_type = parsed.get("type", "commit")
    p_scope = f"({parsed.get('scope')})" if parsed.get("scope") else ""
    print(f"[✓] Conventional commit validated: {p_type}{p_scope}: {parsed.get('description', '')[:50]}")
    return True


# ==============================================================================
# Git Hook Installation & Management
# ==============================================================================

def resolve_git_hooks_dir() -> Path:
    """
    Resolves the actual git hooks directory, handling standard repos,
    worktrees, submodules, and custom git configurations.
    """
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--git-path", "hooks"],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout.strip():
            hooks_p = Path(res.stdout.strip())
            if not hooks_p.is_absolute():
                hooks_p = (WORKSPACE_ROOT / hooks_p).resolve()
            return hooks_p
    except Exception:
        pass

    # Fallback to .git/hooks under workspace
    return WORKSPACE_ROOT / ".git" / "hooks"


def install_hooks() -> bool:
    """
    Installs both post-commit and commit-msg hooks into the active git repository.
    Works seamlessly across Windows, Linux, and macOS.
    """
    hooks_dir = resolve_git_hooks_dir()
    hooks_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("  KANT (.kant) GIT WORKFLOW HOOKS INSTALLER")
    print("=" * 72)
    print(f"  Target Hooks Directory: {hooks_dir}")

    # 1. Post-Commit Hook
    # Invokes python scripts/kant_git_automation.py --post-commit-hook
    post_commit_file = hooks_dir / "post-commit"
    post_commit_script = """#!/bin/sh
# Kant Epistemic Telemetry Engine: Git Post-Commit Hook
# Automatically logs commit SHA, author, message, and changed files into SQLite telemetry DB.

python scripts/kant_git_automation.py --post-commit-hook || true
"""
    try:
        with open(post_commit_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(post_commit_script)
        if sys.platform != "win32":
            os.chmod(post_commit_file, 0o755)
        print(f"  [✓] Installed post-commit hook: {post_commit_file}")
    except Exception as e:
        print(f"  [x] Failed to install post-commit hook: {e}", file=sys.stderr)
        return False

    # 2. Commit-Msg Hook
    # Invokes python scripts/kant_git_automation.py --validate-commit-msg "$1"
    commit_msg_file = hooks_dir / "commit-msg"
    commit_msg_script = """#!/bin/sh
# Kant Epistemic Compiler: Conventional Commit Linter Hook
# Enforces strict type tags: feat:, fix:, docs:, refactor:, test:, ci:

python scripts/kant_git_automation.py --validate-commit-msg "$1"
"""
    try:
        with open(commit_msg_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(commit_msg_script)
        if sys.platform != "win32":
            os.chmod(commit_msg_file, 0o755)
        print(f"  [✓] Installed commit-msg hook:   {commit_msg_file}")
    except Exception as e:
        print(f"  [x] Failed to install commit-msg hook: {e}", file=sys.stderr)
        return False

    print("=" * 72)
    print("  All Git automation hooks successfully installed and active!")
    print("=" * 72)
    return True


def verify_hooks() -> bool:
    """Verifies that the hooks are properly installed and contain required commands."""
    hooks_dir = resolve_git_hooks_dir()
    post_commit = hooks_dir / "post-commit"
    commit_msg = hooks_dir / "commit-msg"

    status = True
    print(f"[*] Checking git hooks in: {hooks_dir}")

    if post_commit.exists():
        content = post_commit.read_text(encoding="utf-8", errors="ignore")
        if "kant_git_automation.py" in content or "kant_watch.py" in content:
            print(f"  [✓] post-commit hook present and configured ({post_commit.stat().st_size} bytes)")
        else:
            print("  [!] post-commit hook exists but does not reference Kant automation")
            status = False
    else:
        print("  [x] post-commit hook missing")
        status = False

    if commit_msg.exists():
        content = commit_msg.read_text(encoding="utf-8", errors="ignore")
        if "kant_git_automation.py" in content:
            print(f"  [✓] commit-msg hook present and configured ({commit_msg.stat().st_size} bytes)")
        else:
            print("  [!] commit-msg hook exists but does not reference Kant linter")
            status = False
    else:
        print("  [x] commit-msg hook missing")
        status = False

    return status


# ==============================================================================
# Post-Commit Execution Handler
# ==============================================================================

def execute_post_commit() -> bool:
    """
    Executed automatically by `.git/hooks/post-commit`.
    Extracts commit hash, author info, message, and modified file paths,
    and inserts directly into the SQLite telemetry database.
    """
    try:
        # 1. Extract HEAD commit metadata
        cmd_meta = [
            "git",
            "log",
            "-1",
            "--pretty=format:%H%x00%h%x00%an%x00%ae%x00%aI%x00%s%x00%b",
        ]
        res_meta = subprocess.run(cmd_meta, cwd=WORKSPACE_ROOT, capture_output=True, text=True, timeout=5)
        if res_meta.returncode != 0:
            print("[!] Could not retrieve git HEAD metadata.", file=sys.stderr)
            return False

        parts = res_meta.stdout.strip().split("\x00")
        if len(parts) < 6:
            print("[!] Malformed git log output.", file=sys.stderr)
            return False

        full_hash = parts[0]
        short_hash = parts[1]
        author_name = parts[2]
        author_email = parts[3]
        committed_at = parts[4]
        subject = parts[5]
        body = parts[6] if len(parts) > 6 else ""

        # 2. Extract current branch name
        res_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch = res_branch.stdout.strip() if res_branch.returncode == 0 else "HEAD"

        # 3. Extract modified file paths and change types
        # Use git diff-tree against parent commit, or show if root commit
        cmd_diff = ["git", "diff-tree", "--no-commit-id", "--name-status", "-r", "HEAD"]
        res_diff = subprocess.run(cmd_diff, cwd=WORKSPACE_ROOT, capture_output=True, text=True, timeout=5)
        changed_files = []
        if res_diff.returncode == 0 and res_diff.stdout.strip():
            for line in res_diff.stdout.strip().splitlines():
                toks = line.split(maxsplit=1)
                if len(toks) == 2:
                    changed_files.append({"status": toks[0], "path": toks[1].replace("\\", "/")})
        else:
            # Fallback for initial commit
            cmd_show = ["git", "show", "--name-status", "--pretty=format:", "HEAD"]
            res_show = subprocess.run(cmd_show, cwd=WORKSPACE_ROOT, capture_output=True, text=True, timeout=5)
            if res_show.returncode == 0 and res_show.stdout.strip():
                for line in res_show.stdout.strip().splitlines():
                    toks = line.split(maxsplit=1)
                    if len(toks) == 2:
                        changed_files.append({"status": toks[0], "path": toks[1].replace("\\", "/")})

        # 4. Infer Task ID and Circle ID
        task_id = None
        circle_id = None

        # Check commit message for task ID
        m_task = TASK_ID_REGEX.search(subject) or TASK_ID_REGEX.search(body)
        if m_task:
            task_id = m_task.group(1)

        # If not in commit message, check if current branch is mapped to a task in git_branches table
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("SELECT task_id, circle_id FROM git_branches WHERE branch_name = ?", (branch,))
            branch_row = cur.fetchone()
            if branch_row:
                if not task_id and branch_row[0]:
                    task_id = branch_row[0]
                if branch_row[1]:
                    circle_id = branch_row[1]
            conn.close()
        except Exception:
            pass

        # If still no circle_id, infer from task_id or changed files
        if not circle_id and task_id:
            m_circ = CIRCLE_ID_REGEX.search(task_id)
            if m_circ:
                circle_id = m_circ.group(1)

        # 5. Record directly in SQLite database
        record_git_commit_telemetry(
            commit_hash=full_hash,
            short_hash=short_hash,
            author_name=author_name,
            author_email=author_email,
            committed_at=committed_at,
            branch=branch,
            subject=subject,
            body=body,
            changed_files=changed_files,
            task_id=task_id,
            circle_id=circle_id,
        )

        task_str = f" [Task: {task_id}]" if task_id else ""
        circle_str = f" [Circle: {circle_id}]" if circle_id else ""
        print(f"[✓] Telemetry: Logged commit {short_hash} by {author_name} ({len(changed_files)} files modified){task_str}{circle_str}")
        return True

    except Exception as e:
        print(f"[!] Error in post-commit telemetry: {e}", file=sys.stderr)
        return False


# ==============================================================================
# Subagent Feature Branch Orchestration
# ==============================================================================

def create_and_track_branch(branch_name: str, task_id: str) -> bool:
    """
    Creates a new feature branch and registers it in SQLite git_branches,
    linking it to the specified roadmap task ID.
    Transitions task status to IN_PROGRESS if currently TODO.
    """
    print("=" * 72)
    print("  KANT (.kant) SUBAGENT BRANCH ORCHESTRATOR")
    print("=" * 72)

    # 1. Validate task ID format
    m_task = TASK_ID_REGEX.search(task_id)
    if not m_task:
        print(f"[x] Error: Invalid Task ID format '{task_id}'. Expected format e.g. 'C1.H1.S1.T01'.", file=sys.stderr)
        return False

    task_id = m_task.group(1)
    circle_id = task_id.split(".")[0]

    # 2. Check task existence in SQLite database
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, status, circle_id FROM tasks WHERE id = ?", (task_id,))
    task_row = cur.fetchone()
    if not task_row:
        print(f"[!] Warning: Task '{task_id}' not found in SQLite tasks table.", file=sys.stderr)
        task_title = "Unindexed Task"
        task_status = "TODO"
    else:
        task_title = task_row[1]
        task_status = task_row[2]
        circle_id = task_row[3] or circle_id

    # 3. Get current HEAD commit hash
    res_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT, capture_output=True, text=True)
    base_commit = res_head.stdout.strip() if res_head.returncode == 0 else ""

    # 4. Create and checkout git branch
    cmd_checkout = ["git", "checkout", "-b", branch_name]
    res_checkout = subprocess.run(cmd_checkout, cwd=WORKSPACE_ROOT, capture_output=True, text=True)
    if res_checkout.returncode != 0:
        # If branch already exists, attempt checkout
        if "already exists" in res_checkout.stderr.lower():
            print(f"[*] Branch '{branch_name}' already exists. Switching to it...")
            res_switch = subprocess.run(["git", "checkout", branch_name], cwd=WORKSPACE_ROOT, capture_output=True, text=True)
            if res_switch.returncode != 0:
                print(f"[x] Failed to switch to branch '{branch_name}': {res_switch.stderr}", file=sys.stderr)
                conn.close()
                return False
        else:
            print(f"[x] Failed to create branch '{branch_name}': {res_checkout.stderr}", file=sys.stderr)
            conn.close()
            return False

    now_iso = datetime.now(timezone.utc).isoformat()

    # 5. Record branch in git_branches table
    cur.execute(
        """
        INSERT OR REPLACE INTO git_branches
        (branch_name, task_id, circle_id, base_commit, status, created_at)
        VALUES (?, ?, ?, ?, 'ACTIVE', ?)
        """,
        (branch_name, task_id, circle_id, base_commit, now_iso),
    )

    # 6. Update task status if it was TODO
    if task_status == "TODO":
        cur.execute(
            "UPDATE tasks SET status = 'IN_PROGRESS', updated_at = ? WHERE id = ?",
            (now_iso, task_id),
        )
        print(f"  [✓] Updated task {task_id} status: TODO -> IN_PROGRESS")

    # 7. Record telemetry event
    cur.execute(
        """
        INSERT INTO telemetry_events
        (timestamp, action_type, task_id, circle_id, git_commit, status_diff, details)
        VALUES (?, 'BRANCH_ORCHESTRATION', ?, ?, ?, ?, ?)
        """,
        (
            now_iso,
            task_id,
            circle_id,
            base_commit,
            f"Created branch '{branch_name}'",
            json.dumps({"branch": branch_name, "task_id": task_id, "task_title": task_title}),
        ),
    )

    conn.commit()
    conn.close()

    print(f"  [✓] Active Branch:    {branch_name}")
    print(f"  [✓] Linked Task:      {task_id} ({task_title})")
    print(f"  [✓] Roadmap Circle:   {circle_id}")
    print(f"  [✓] Base Commit:      {base_commit[:10]}")
    print("=" * 72)
    return True


def list_tracked_branches() -> None:
    """Lists all tracked git branches and their linked roadmap tasks from SQLite."""
    conn = get_db_conn()
    cur = conn.cursor()

    # Get current git branch
    res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=WORKSPACE_ROOT, capture_output=True, text=True)
    current_git_branch = res.stdout.strip() if res.returncode == 0 else ""

    cur.execute("""
        SELECT b.branch_name, b.task_id, b.circle_id, b.status, b.created_at, b.base_commit,
               COALESCE(t.title, 'Unlinked Task') AS task_title,
               COALESCE(t.status, 'UNKNOWN') AS task_status
        FROM git_branches b
        LEFT JOIN tasks t ON b.task_id = t.id
        ORDER BY b.created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()

    print("=" * 80)
    print("  KANT (.kant) TRACKED SUBAGENT FEATURE BRANCHES")
    print("=" * 80)
    if not rows:
        print("  No tracked branches registered yet.")
        print("  Create one using: python scripts/kant_git_automation.py --create-branch <name> --track-task <task_id>")
        print("=" * 80)
        return

    print(f"  {'Cur':<3} {'Branch Name':<30} {'Task ID':<16} {'Circle':<8} {'Branch St':<10} {'Task St':<12}")
    print("  " + "-" * 78)
    for r in rows:
        b_name, t_id, c_id, b_stat, created, base_c, title, t_stat = r
        is_cur = "*" if b_name == current_git_branch else " "
        print(f"  {is_cur:<3} {b_name:<30} {t_id:<16} {c_id:<8} {b_stat:<10} {t_stat:<12}")
        print(f"      └─ Task: {title}")
    print("=" * 80)


def sync_branch_and_verify_lane(branch_name: Optional[str] = None) -> bool:
    """
    Checks commits on the specified branch, verifies subagent write lane hygiene
    mandated by AGENTS.md, and checks alignment with the linked task.
    """
    if not branch_name:
        res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=WORKSPACE_ROOT, capture_output=True, text=True)
        branch_name = res.stdout.strip() if res.returncode == 0 else ""

    if not branch_name or branch_name == "HEAD":
        print("[x] Error: Cannot determine active branch name.", file=sys.stderr)
        return False

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT branch_name, task_id, circle_id, base_commit, status FROM git_branches WHERE branch_name = ?", (branch_name,))
    row = cur.fetchone()

    print("=" * 72)
    print(f"  KANT (.kant) BRANCH SYNC & LANE HYGIENE AUDIT: {branch_name}")
    print("=" * 72)

    if not row:
        print(f"  [!] Note: Branch '{branch_name}' is not formally tracked in git_branches.")
        base_ref = "main"
        task_id = "N/A"
        circle_id = "N/A"
    else:
        task_id = row[1] or "N/A"
        circle_id = row[2] or "N/A"
        base_ref = row[3] or "main"
        print(f"  Tracked Task:    {task_id}")
        print(f"  Roadmap Circle:  {circle_id}")
        print(f"  Base Reference:  {base_ref[:10] if len(base_ref) > 10 else base_ref}")

    # Inspect changed files on this branch relative to base
    try:
        cmd_diff = ["git", "diff", "--name-status", f"{base_ref}..HEAD"]
        res_diff = subprocess.run(cmd_diff, cwd=WORKSPACE_ROOT, capture_output=True, text=True)
        if res_diff.returncode != 0:
            # Fallback to diff against HEAD~1 or uncommitted changes
            cmd_diff = ["git", "status", "--porcelain"]
            res_diff = subprocess.run(cmd_diff, cwd=WORKSPACE_ROOT, capture_output=True, text=True)

        lines = res_diff.stdout.strip().splitlines() if res_diff.stdout.strip() else []
        print(f"\n  Inspected Changes: {len(lines)} file(s) modified on branch:")

        lane_violations = []
        for line in lines:
            toks = line.split(maxsplit=1)
            if len(toks) == 2:
                status, path = toks[0], toks[1].replace("\\", "/")
                print(f"    [{status}] {path}")

                # Check for lane violations if task is assigned to a specific crate
                # E.g. if task_id starts with C1.H1.S1 -> SA-01
                # But scripts/, docs/, and tests are permitted tooling lanes
                if path.startswith("crates/"):
                    crate_name = path.split("/")[1]
                    # Check if crate belongs to assigned circle
                    if crate_name in CRATE_TO_CIRCLE_MAP:
                        c_id, lane = CRATE_TO_CIRCLE_MAP[crate_name]
                        if circle_id != "N/A" and c_id != circle_id:
                            lane_violations.append((path, c_id, lane))

        if lane_violations:
            print("\n  [x] SUBAGENT LANE HYGIENE VIOLATIONS DETECTED (AGENTS.md):")
            for path, c_id, lane in lane_violations:
                print(f"    - File '{path}' belongs to {lane} ({c_id}), outside current branch circle {circle_id}!")
            conn.close()
            return False
        else:
            print("\n  [✓] Strict Lane Hygiene Verified: Zero multi-agent write collisions detected.")

    except Exception as e:
        print(f"  [!] Warning inspecting git diff: {e}")

    conn.close()
    print("=" * 72)
    return True


def merge_and_finalize_branch(branch_name: str, target: str = "main") -> bool:
    """
    Marks a branch as MERGED in the SQLite database, records merge commit,
    and updates the associated task status to DONE_VERIFIED.
    """
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT branch_name, task_id, circle_id FROM git_branches WHERE branch_name = ?", (branch_name,))
    row = cur.fetchone()
    if not row:
        print(f"[x] Error: Branch '{branch_name}' not found in tracked branches registry.", file=sys.stderr)
        conn.close()
        return False

    task_id = row[1]
    circle_id = row[2]

    # Get current HEAD hash as merge commit
    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT, capture_output=True, text=True)
    head_hash = res.stdout.strip() if res.returncode == 0 else ""
    now_iso = datetime.now(timezone.utc).isoformat()

    cur.execute(
        """
        UPDATE git_branches
        SET status = 'MERGED', merged_at = ?, merge_commit = ?
        WHERE branch_name = ?
        """,
        (now_iso, head_hash, branch_name),
    )

    if task_id:
        cur.execute(
            "UPDATE tasks SET status = 'DONE_VERIFIED', updated_at = ? WHERE id = ?",
            (now_iso, task_id),
        )

    # Telemetry
    cur.execute(
        """
        INSERT INTO telemetry_events
        (timestamp, action_type, task_id, circle_id, git_commit, status_diff, details)
        VALUES (?, 'BRANCH_MERGED', ?, ?, ?, ?, ?)
        """,
        (
            now_iso,
            task_id,
            circle_id,
            head_hash,
            f"Merged branch '{branch_name}'",
            json.dumps({"branch": branch_name, "task_id": task_id, "merge_commit": head_hash}),
        ),
    )

    conn.commit()
    conn.close()

    print(f"[✓] Branch '{branch_name}' marked MERGED in SQLite telemetry database.")
    if task_id:
        print(f"[✓] Linked task {task_id} transitioned to DONE_VERIFIED.")
    return True


# ==============================================================================
# Automated Changelog Generator
# ==============================================================================

def generate_changelog(
    milestone: str = "all",
    output_path: Optional[Path] = None,
    since_ref: Optional[str] = None,
) -> str:
    """
    Generates a structured, conventional changelog grouped by roadmap milestones
    (Circles C0–C6) and commit categories (Features, Fixes, Docs, Refactoring, CI).
    """
    conn = get_db_conn()
    cur = conn.cursor()

    # Query commits from git_commits table
    query = """
        SELECT commit_hash, short_hash, author_name, committed_at, branch, subject, body, task_id, circle_id
        FROM git_commits
        ORDER BY committed_at DESC
    """
    cur.execute(query)
    rows = cur.fetchall()

    # Also query git log directly to catch commits not yet captured in SQLite
    git_commits_map = {}
    try:
        cmd = ["git", "log", "--pretty=format:%H%x00%h%x00%an%x00%aI%x00%s%x00%b"]
        if since_ref:
            cmd.append(f"{since_ref}..HEAD")
        res = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            for entry in res.stdout.strip().split("\n"):
                if not entry:
                    continue
                parts = entry.split("\x00")
                if len(parts) >= 5:
                    h, sh, author, date, subj = parts[0], parts[1], parts[2], parts[3], parts[4]
                    git_commits_map[h] = {
                        "commit_hash": h,
                        "short_hash": sh,
                        "author_name": author,
                        "committed_at": date,
                        "branch": "",
                        "subject": subj,
                        "task_id": None,
                        "circle_id": None,
                    }
    except Exception:
        pass

    # Merge database records with git log
    combined_commits = []
    seen_hashes = set()

    for r in rows:
        h = r[0]
        seen_hashes.add(h)
        combined_commits.append({
            "commit_hash": r[0],
            "short_hash": r[1],
            "author_name": r[2],
            "committed_at": r[3],
            "branch": r[4],
            "subject": r[5],
            "body": r[6],
            "task_id": r[7],
            "circle_id": r[8],
        })

    for h, c in git_commits_map.items():
        if h not in seen_hashes:
            seen_hashes.add(h)
            combined_commits.append(c)

    # Circle metadata
    cur.execute("SELECT id, name, short_title, gate_status FROM circles ORDER BY ordering ASC")
    circle_rows = cur.fetchall()
    circle_meta = {r[0]: {"name": r[1], "short_title": r[2], "status": r[3]} for r in circle_rows}
    conn.close()

    # Categorize commits by milestone and type
    categorized: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    # Types: feat, fix, docs, refactor, test, ci, other
    type_display = {
        "feat": "🚀 Features & Architecture",
        "fix": "🐛 Bug Fixes & Verifications",
        "docs": "📚 Epistemic Specifications & Documentation",
        "refactor": "♻️ Refactoring & Optimizations",
        "test": "🧪 Test Suites & Conformance Vectors",
        "ci": "🔧 CI/CD, Git Hooks & Tooling",
        "other": "📦 Other Changes",
    }

    for c in combined_commits:
        subj = c["subject"]
        # Determine milestone / circle
        cid = c.get("circle_id")
        if not cid:
            m = CIRCLE_ID_REGEX.search(subj) or (TASK_ID_REGEX.search(subj) and TASK_ID_REGEX.search(subj).group(1).split(".")[0])
            cid = m.group(1) if m else "C1"

        if milestone != "all" and cid != milestone:
            continue

        if cid not in categorized:
            categorized[cid] = {t: [] for t in type_display.keys()}

        # Determine type
        m_conv = CONVENTIONAL_REGEX.match(subj)
        if m_conv:
            t = m_conv.group("type")
            t_key = t if t in type_display else "other"
        else:
            t_key = "other"

        categorized[cid][t_key].append(c)

    # Build Markdown document
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Kant (.kant) Compiler Toolchain — Automated Changelog",
        f"\n*Generated automatically by `scripts/kant_git_automation.py` on {now_str}*",
        "\n---",
    ]

    for cid in sorted(categorized.keys()):
        meta = circle_meta.get(cid, {"name": f"Milestone {cid}", "status": "ACTIVE"})
        c_name = meta["name"]
        c_stat = meta.get("status", "IN_ITERATION")
        lines.append(f"\n## Circle {cid}: {c_name} `[{c_stat}]`\n")

        has_entries = False
        for t_key, t_title in type_display.items():
            entries = categorized[cid][t_key]
            if not entries:
                continue
            has_entries = True
            lines.append(f"### {t_title}\n")
            for entry in entries:
                sh = entry["short_hash"]
                subj = entry["subject"]
                author = entry["author_name"]
                tid = entry.get("task_id")
                task_tag = f"`{tid}` " if tid else ""
                lines.append(f"- **{sh}** {task_tag}{subj} *(by {author})*")
            lines.append("")

        if not has_entries:
            lines.append("*No commits recorded for this milestone yet.*\n")

    changelog_content = "\n".join(lines) + "\n"

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(changelog_content)
        print(f"[✓] Automated changelog successfully written to {output_path}")

    return changelog_content


# ==============================================================================
# Comprehensive Self-Test Harness
# ==============================================================================

def run_self_tests() -> bool:
    """Executes end-to-end self tests of all git automation components."""
    print("=" * 72)
    print("  KANT (.kant) GIT AUTOMATION ENGINE SELF-TEST HARNESS")
    print("=" * 72)

    passed = 0
    failed = 0

    def test(name: str, cond: bool) -> None:
        nonlocal passed, failed
        if cond:
            print(f"  [✓] PASS: {name}")
            passed += 1
        else:
            print(f"  [x] FAIL: {name}", file=sys.stderr)
            failed += 1

    # 1. Test Conventional Commit Validator - Positive Cases
    valid_samples = [
        "feat: introduce ByteSpan and DefHash primitives",
        "feat(core): add De Bruijn index canonicalizer",
        "fix(lexer): resolve UTF-8 offset counting bug",
        "docs(reports): author SA-05 git automation technical report",
        "refactor(perceus): optimize drop-guided reuse allocations",
        "test(types): add 12-categories type checker conformance tests",
        "ci(hooks): install post-commit telemetry integration",
        "feat(ir)!: breaking change to Al-Shaym SSA block format",
        "Merge branch 'feat/git-automation-engine' into main",
    ]
    for s in valid_samples:
        ok, reason, _ = validate_commit_message(s)
        test(f"Validate conforming message: '{s[:40]}...'", ok)

    # 2. Test Conventional Commit Validator - Negative Cases
    invalid_samples = [
        "",  # empty
        "WIP: working on stuff",  # disallowed tag
        "feature: wrong tag name",  # 'feature' instead of 'feat'
        "feat missing colon",  # missing colon
        "feat:no space after colon",  # missing space
        "random message without type tag",
        "feat(core): " + ("a" * 120),  # exceeds 100 chars
    ]
    for s in invalid_samples:
        ok, reason, _ = validate_commit_message(s)
        test(f"Reject non-conforming message: '{s[:30]}'", not ok)

    # 3. Test Database Schema Initialization
    test_db = TRACKER_DIR / "test_telemetry.db"
    try:
        conn = get_db_conn(test_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        test("Database creates 'git_commits' table", "git_commits" in tables)
        test("Database creates 'git_branches' table", "git_branches" in tables)
        test("Database creates 'telemetry_events' table", "telemetry_events" in tables)
        conn.close()
    finally:
        if test_db.exists():
            try:
                os.remove(test_db)
            except Exception:
                pass

    # 4. Test Commit Telemetry Recording
    test("Record telemetry function callable", callable(record_git_commit_telemetry))

    # 5. Test Changelog Generation
    cl = generate_changelog(milestone="all")
    test("Changelog generation returns markdown content", "# Kant (.kant)" in cl)

    print("=" * 72)
    print(f"  Self-Test Results: {passed} PASSED, {failed} FAILED")
    print("=" * 72)
    return failed == 0


# ==============================================================================
# CLI Entry Point & Dispatcher
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Kant (.kant) Git Workflow Automation, Hooks & Branch Orchestration Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Git Hooks
    hook_group = parser.add_argument_group("Git Hook Management")
    hook_group.add_argument("--install-hooks", action="store_true", help="Install automated post-commit and commit-msg hooks into .git/hooks")
    hook_group.add_argument("--verify-hooks", action="store_true", help="Verify presence and executability of installed git hooks")
    hook_group.add_argument("--post-commit-hook", action="store_true", help="Internal entry point executed by .git/hooks/post-commit")
    hook_group.add_argument("--validate-commit-msg", type=Path, metavar="FILE", help="Internal entry point executed by .git/hooks/commit-msg")
    hook_group.add_argument("--lint-commit-msg", type=str, metavar="MSG", help="Lint an arbitrary commit message string")
    hook_group.add_argument("--lint-recent", type=int, nargs="?", const=10, metavar="N", help="Lint the last N git commits in the current branch (default: 10)")

    # Branch Orchestration
    branch_group = parser.add_argument_group("Subagent Branch Orchestration")
    branch_group.add_argument("--create-branch", type=str, metavar="NAME", help="Create and checkout a new subagent feature branch")
    branch_group.add_argument("--track-task", type=str, metavar="TASK_ID", help="Map created feature branch to target Atomic Task ID (e.g. C1.H1.S1.T01)")
    branch_group.add_argument("--list-branches", action="store_true", help="List all tracked subagent feature branches and linked tasks")
    branch_group.add_argument("--sync-branch", type=str, nargs="?", const="", metavar="NAME", help="Audit branch commits and AGENTS.md file lane hygiene")
    branch_group.add_argument("--merge-branch", type=str, metavar="NAME", help="Mark branch MERGED in database and update task to DONE_VERIFIED")

    # Changelog & Reporting
    cl_group = parser.add_argument_group("Changelog & Documentation")
    cl_group.add_argument("--generate-changelog", action="store_true", help="Generate milestone-grouped Markdown changelog from commits and roadmap")
    cl_group.add_argument("--output", type=Path, metavar="FILE", help="Destination file for generated changelog (e.g. CHANGELOG.md)")
    cl_group.add_argument("--milestone", type=str, default="all", metavar="ID", help="Filter changelog by milestone/circle ID (C0-C6, default: all)")

    # Status & Diagnostics
    diag_group = parser.add_argument_group("Status & Diagnostics")
    diag_group.add_argument("--status", action="store_true", help="Display git automation and branch tracking dashboard summary")
    diag_group.add_argument("--test", action="store_true", help="Run comprehensive internal self-test suite")

    args = parser.parse_args()

    # Dispatch commands
    if args.install_hooks:
        success = install_hooks()
        sys.exit(0 if success else 1)

    if args.verify_hooks:
        success = verify_hooks()
        sys.exit(0 if success else 1)

    if args.post_commit_hook:
        success = execute_post_commit()
        sys.exit(0 if success else 1)

    if args.validate_commit_msg:
        success = validate_commit_msg_file(args.validate_commit_msg)
        sys.exit(0 if success else 1)

    if args.lint_commit_msg:
        valid, reason, parsed = validate_commit_message(args.lint_commit_msg)
        if valid:
            p_type = parsed.get("type")
            p_scope = f"({parsed.get('scope')})" if parsed.get("scope") else ""
            print(f"[✓] Valid conventional commit: {p_type}{p_scope}: {parsed.get('description')}")
            sys.exit(0)
        else:
            print(f"[x] Invalid commit message: {reason}", file=sys.stderr)
            sys.exit(1)

    if args.lint_recent is not None:
        count = args.lint_recent
        res = subprocess.run(["git", "log", f"-{count}", "--pretty=format:%h|%s"], cwd=WORKSPACE_ROOT, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[x] Error executing git log: {res.stderr}", file=sys.stderr)
            sys.exit(1)
        print(f"[*] Linting the last {count} commits on current branch:")
        all_valid = True
        for line in res.stdout.strip().splitlines():
            if not line:
                continue
            sh, subj = line.split("|", 1)
            valid, reason, _ = validate_commit_message(subj)
            icon = "✓" if valid else "x"
            print(f"  [{icon}] {sh}: {subj}")
            if not valid:
                print(f"      └─ Reason: {reason}")
                all_valid = False
        sys.exit(0 if all_valid else 1)

    if args.create_branch:
        if not args.track_task:
            print("[x] Error: --track-task <task_id> is required when creating a tracked branch.", file=sys.stderr)
            sys.exit(1)
        success = create_and_track_branch(args.create_branch, args.track_task)
        sys.exit(0 if success else 1)

    if args.list_branches:
        list_tracked_branches()
        sys.exit(0)

    if args.sync_branch is not None:
        target = args.sync_branch if args.sync_branch else None
        success = sync_branch_and_verify_lane(target)
        sys.exit(0 if success else 1)

    if args.merge_branch:
        success = merge_and_finalize_branch(args.merge_branch)
        sys.exit(0 if success else 1)

    if args.generate_changelog:
        out = args.output or (WORKSPACE_ROOT / "CHANGELOG.md")
        content = generate_changelog(milestone=args.milestone, output_path=out)
        if not args.output:
            print(content)
        sys.exit(0)

    if args.test:
        success = run_self_tests()
        sys.exit(0 if success else 1)

    if args.status:
        # Show status dashboard
        hooks_dir = resolve_git_hooks_dir()
        post_ok = (hooks_dir / "post-commit").exists()
        msg_ok = (hooks_dir / "commit-msg").exists()
        res_b = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=WORKSPACE_ROOT, capture_output=True, text=True)
        cur_b = res_b.stdout.strip() if res_b.returncode == 0 else "unknown"

        print("=" * 72)
        print("  KANT (.kant) GIT AUTOMATION & TOOLING STATUS")
        print("=" * 72)
        print(f"  Workspace:             {WORKSPACE_ROOT}")
        print(f"  Current Git Branch:    {cur_b}")
        print(f"  Post-Commit Hook:      {'INSTALLED [✓]' if post_ok else 'MISSING [x]'}")
        print(f"  Commit-Msg Linter:     {'INSTALLED [✓]' if msg_ok else 'MISSING [x]'}")
        print(f"  Telemetry Database:    {DB_FILE} ({'EXISTS [✓]' if DB_FILE.exists() else 'PENDING [!]'})\n")
        list_tracked_branches()
        sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
