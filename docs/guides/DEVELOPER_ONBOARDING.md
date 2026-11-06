# Developer & Contributor Onboarding Guide

## 1. System Requirements & Toolchain Prerequisites

Before developing or compiling the Kant compiler toolchain (`kantc`), verify that your host environment meets the following baseline toolchain requirements:

| Tool / Runtime | Minimum Version | Recommended Purpose |
| :--- | :--- | :--- |
| **Rust / Cargo** | `1.80.0` or higher | Core compiler compilation, edition 2021 |
| **Python** | `3.10` or higher | Workspace verification and testbench tooling |
| **Git** | `2.40.0` or higher | Multi-agent branch management and conventional commit tracking |
| **Z3 Theorem Prover** (Optional) | `4.12.0` or higher | Tier 1 Antinomy contract verification (`kant-antinomy`) |

---

## 2. Environment Configuration

Configure the following environment variables in your active shell profile (`~/.bashrc`, `~/.zshrc`, or PowerShell `$PROFILE`):

```bash
# Enable full backtraces for compiler crash reporting
export RUST_BACKTRACE=1

# Optional: Set custom Cargo home if operating in isolated agent worktrees
export CARGO_HOME="${HOME}/.cargo"

# Optional: Z3 binary path for contract solving
export Z3_SYS_Z3_HEADER="/usr/include/z3.h"
```

For Windows PowerShell:
```powershell
$env:RUST_BACKTRACE = "1"
```

---

## 3. Cloning & Workspace Initialization

```bash
# Clone the repository
git clone https://github.com/azmyayman-maker/KANT.git
cd KANT

# Verify repository status
git status
```

---

## 4. Workspace Architecture & Building

The Kant toolchain is structured as a modular Cargo workspace containing 17 specialized crates:

```
crates/
├── kant-core/          # Epistemic foundation, span tokens, shared primitives
├── kant-lexer/         # Closed 48-token transcendental aesthetic lexer
├── kant-parser/        # Flattened Pratt and LL(1) syntax parser
├── kant-canonical/     # Spatial normalization, De Bruijn indices, DefHash
├── kant-types/         # 12-Categories constructive type checker
├── kant-effects/       # Exact algebraic effect inference & quarantine analyzer
├── kant-ir/            # Al-Shaym SSA IR lowering engine (30 instructions)
├── kant-perceus/       # Perceus deterministic reference counting & reuse pass
├── kant-paralogism/    # Linear capability ownership & secret taint guard
├── kant-antinomy/      # 3-Tier contract & termination verifier (Z3 SMT)
├── kant-noumena/       # Noumena capability sandbox & runtime governor
├── kant-spec/          # Specification extractor & dependency graph generator
├── kant-eval/          # Reference SSA interpreter & Merkle evidence trace
├── kant-codegen/       # Cranelift native JIT & static AOT backend
├── kant-diag/          # Structured JSON diagnostics & RFC 6902 auto-fixes
├── kant-cli/           # Main driver binary (kantc)
└── kant-mcp/           # Model Context Protocol (MCP) server daemon
```

### 4.1. Building the Entire Workspace
To compile all crates and binaries:
```bash
cargo build --workspace
```

For optimized release builds:
```bash
cargo build --workspace --release
```

### 4.2. Building an Individual Crate
```bash
cargo build -p kant-parser
cargo build -p kant-types
```

---

## 5. Running the Test Suite

Kant enforces rigorous test suites across all crates:

```bash
# Run unit and integration tests across all 17 crates
cargo test --workspace

# Run tests for a specific crate with full stdout output
cargo test -p kant-effects -- --nocapture

# Run conformance test suite
cargo test -p kant-codegen conformance -- --exact
```

---

## 6. Code Style, Formatting & Linting

Kant maintains a zero-warning policy across all crates. Code that produces compiler warnings or clippy lints will fail CI gates.

```bash
# 1. Format check
cargo fmt --all -- --check

# 2. Automatically apply formatting
cargo fmt --all

# 3. Strict Clippy check with zero warnings allowed
cargo clippy --workspace --all-targets -- -D warnings
```

---

## 7. Launching the Local Roadmap Observatory

Kant includes an interactive, single-file engineering & verification observatory: `kant-roadmap-tracker.html`. It provides real-time visual monitoring of compilation passes, agent worktree progress, commit metrics, and pipeline flowcharts without external network dependencies, server runtimes, or workspace pollution.

To launch the local observatory:
```bash
# Open in default browser (isolated local-only file)
start kant-roadmap-tracker.html    # Windows
xdg-open kant-roadmap-tracker.html # Linux
open kant-roadmap-tracker.html     # macOS
```

The observatory provides live visual dashboards, interactive pipeline DAG flowcharts, and full verification tracking.

---

## 8. Development Workflow Checklist

Before opening a pull request or submitting work:
1. Run `cargo fmt --all -- --check`.
2. Run `cargo clippy --workspace --all-targets -- -D warnings`.
3. Run `cargo test --workspace`.
4. Ensure all commit messages adhere to Conventional Commits 1.0.0 (e.g. `docs(guides): ...`, `refactor(core): ...`).
5. Ensure `git status` shows a clean working tree with zero untracked artifacts.
