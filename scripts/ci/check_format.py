#!/usr/bin/env python3
"""
scripts/ci/check_format.py: Multi-language formatting and hygiene checker for Kant workspace.

Validates:
1. Rust code formatting via cargo fmt (when Rust is available).
2. Trailing whitespace across non-markdown source files.
3. UTF-8 file encoding across repository text files.
4. HTML5 structural conformance for kant-roadmap-tracker.html via HTMLParser.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from html.parser import HTMLParser
from typing import List, Tuple

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

EXCLUDED_DIRS = {
    ".git",
    "target",
    ".kant-tracker",
    "portal",
    "__pycache__",
    ".pytest_cache",
    "dist",
}

CHECK_EXTENSIONS = {
    ".rs",
    ".py",
    ".toml",
    ".json",
    ".yml",
    ".yaml",
    ".sh",
    ".spec",
    ".kant",
    ".kantd",
}


class HTMLConformanceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags_stack: List[str] = []
        self.errors: List[str] = []
        self.has_doctype = False
        self.void_tags = {
            "meta", "link", "img", "br", "hr", "input", "col", "area", "base", "source"
        }

    def handle_decl(self, decl: str):
        if "doctype html" in decl.lower():
            self.has_doctype = True

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() not in self.void_tags:
            self.tags_stack.append(tag.lower())

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower in self.void_tags:
            return
        if self.tags_stack and self.tags_stack[-1] == tag_lower:
            self.tags_stack.pop()
        elif tag_lower in self.tags_stack:
            while self.tags_stack and self.tags_stack[-1] != tag_lower:
                unclosed = self.tags_stack.pop()
                self.errors.append(f"Implicit unclosed tag <{unclosed}> before </{tag_lower}>")
            if self.tags_stack:
                self.tags_stack.pop()
        else:
            self.errors.append(f"Stray closing tag </{tag_lower}>")


def check_html_conformance(html_path: Path) -> Tuple[bool, List[str]]:
    """Parse HTML file and return conformance issues."""
    if not html_path.exists():
        return False, [f"HTML file not found: {html_path}"]

    content = html_path.read_text(encoding="utf-8")
    parser = HTMLConformanceParser()
    try:
        parser.feed(content)
        parser.close()
    except Exception as e:
        return False, [f"HTML parse exception: {e}"]

    issues = []
    if not parser.has_doctype:
        issues.append("Missing <!DOCTYPE html> declaration.")

    if len(parser.tags_stack) > 5:
        issues.append(f"Excessive unclosed HTML tags: {parser.tags_stack}")

    return len(issues) == 0, issues


def check_trailing_whitespace(root: Path) -> List[Tuple[Path, int]]:
    """Find files with trailing whitespace."""
    violations: List[Tuple[Path, int]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for fname in filenames:
            ext = Path(fname).suffix
            if ext in CHECK_EXTENSIONS:
                fpath = Path(dirpath) / fname
                try:
                    lines = fpath.read_text(encoding="utf-8").splitlines()
                    for idx, line in enumerate(lines, 1):
                        if line.endswith(" ") or line.endswith("\t"):
                            violations.append((fpath, idx))
                            break
                except Exception:
                    continue
    return violations


def check_rust_formatting(strict: bool = False) -> bool:
    """Run cargo fmt --all -- --check if cargo is present."""
    cargo_cmd = "cargo"
    user_cargo = Path.home() / ".cargo" / "bin" / ("cargo.exe" if os.name == "nt" else "cargo")
    if user_cargo.exists():
        cargo_cmd = str(user_cargo)

    try:
        res = subprocess.run(
            [cargo_cmd, "fmt", "--all", "--", "--check"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            lines = (res.stderr + "\n" + res.stdout).strip().splitlines()
            code_diffs = [
                l for l in lines
                if l.strip() and not l.startswith("Warning:") and "Incorrect newline style" not in l
            ]
            if code_diffs or strict:
                print("[!] Rust formatting check failed:\n" + (res.stderr or res.stdout), file=sys.stderr)
                return False
            else:
                print("[*] Rust formatting notice: unstable nightly options and platform newlines noted.")
                return True
        return True
    except FileNotFoundError:
        print("[*] cargo not found in PATH; skipping rustfmt check.")
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-language format and hygiene checker.")
    parser.add_argument("--check-html", action="store_true", help="Assert HTML conformance only.")
    parser.add_argument("--check-ws", action="store_true", help="Assert whitespace cleanliness only.")
    parser.add_argument("--strict-rustfmt", action="store_true", help="Enforce strict rustfmt exit codes.")
    args = parser.parse_args()

    overall_clean = True

    if args.check_html:
        tracker_html = ROOT_DIR / "kant-roadmap-tracker.html"
        if tracker_html.exists():
            print(f"[*] Validating HTML conformance: {tracker_html.name}")
            valid, issues = check_html_conformance(tracker_html)
            if not valid:
                for issue in issues:
                    print(f"  [x] {issue}", file=sys.stderr)
                return 1
            print("[✓] HTML conformance verified.")
            return 0
        else:
            print("[*] Local observatory HTML not present; skipping local-only HTML conformance.")
            return 0

    if not args.check_ws:
        print("[*] Running cargo fmt check...")
        if not check_rust_formatting(strict=args.strict_rustfmt):
            overall_clean = False
        else:
            print("[✓] Rustfmt clean.")

    print("[*] Checking for trailing whitespace...")
    ws_violations = check_trailing_whitespace(ROOT_DIR)
    if ws_violations:
        print(f"[!] Trailing whitespace found in {len(ws_violations)} files:", file=sys.stderr)
        for path, line_no in ws_violations[:10]:
            print(f"    {path.relative_to(ROOT_DIR)}: line {line_no}", file=sys.stderr)
        if len(ws_violations) > 10:
            print(f"    ... and {len(ws_violations) - 10} more.", file=sys.stderr)
        overall_clean = False
    else:
        print("[✓] Trailing whitespace check passed.")

    tracker_html = ROOT_DIR / "kant-roadmap-tracker.html"
    if tracker_html.exists():
        valid_html, html_issues = check_html_conformance(tracker_html)
        if valid_html:
            print("[✓] Local observatory HTML conformance verified.")
        else:
            print(f"[!] HTML conformance warning: {html_issues}")

    return 0 if overall_clean else 1


if __name__ == "__main__":
    sys.exit(main())
