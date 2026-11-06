# Contributing to Kant (`kantc`)

Thank you for your interest in contributing to **Kant** (`.kant`), an epistemologically rigorous,
AI-native programming language inspired by Immanuel Kant's *Critique of Pure Reason* (informed by
Moussa Wehbe's foundational Arabic philosophical translation) and modern high-assurance systems
compiler engineering.

This document outlines the contribution lifecycle, governance requirements, quality invariants,
and verification harnesses mandated for all contributors (human and autonomous agents alike).

---

## 1. Architectural Philosophy & Epistemic Verification

Kant adheres to high-assurance systems engineering guidelines inspired by DO-178C Level A and
ISO/IEC/IEEE 12207 lifecycle protocols. The central pillar of Kant engineering is:

### The Iron Law of Verification
> **No contributor, engineer, or autonomous sub-agent may declare a task complete, and no pull
> request or worktree may be merged, without executing the mandatory Five-Step Verification Harness
> and attaching raw terminal outputs.**

Empirical studies demonstrate that conversational assumptions or informal statements lead to
omitted verifications. In Kant, verification is strictly evidential: an assertion without
reproducible terminal or machine-checkable evidence is treated as non-existent.

### The Four Core Architectural Invariants
1. **Deterministic Content-Addressing ($I_1$):** Every definition identity (`DefHash`) is a 32-byte
   SHA-256 digest of its canonicalized AST, invariant to local variable renames or whitespace alterations.
2. **Exact Effect Matching ($I_2$):** A function $f$ is well-typed if and only if $E_{\text{decl}}(f) = E_{\text{inf}}(f)$.
   Undeclared effects or unused declared effects trigger compiler diagnostics with deterministic RFC 6902 quick-fixes.
3. **Garbage-Free Memory Management ($I_3$):** All cyclic-free programs manage memory deterministically
   via Perceus reference counting and drop-guided in-place reuse without any tracing garbage collector.
4. **Noumena Zero-Escape Boundary ($I_4$):** By default, code executes under `trust none`. The external
   world (filesystem, network, OS syscalls, unvetted models) is inaccessible without an explicit, linear,
   unforgeable capability token.

---

## 2. Workspace Organization & 17 Crate Allocation

The Kant compiler repository is organized as a unified Cargo workspace containing 17 specialized crates.
To prevent write collisions and maintain architectural modularity, each development lane has a strict
**Write-Allowlist**:

| Sub-Agent / Lane | Epistemic / Architectural Domain | Assigned Crate Lane | Upstream Dependencies (Read-Only) | Wave |
| :--- | :--- | :--- | :--- | :--- |
| **SA-01** | Epistemic & Workspace Bootstrapper | `crates/kant-core/` | Spec Docs, Root Manifest | Wave 1 |
| **SA-02** | Transcendental Aesthetic Lexer | `crates/kant-lexer/` | `kant-core` | Wave 1 |
| **SA-03** | Flattened Pratt & LL(1) Parser | `crates/kant-parser/` | `kant-core`, `kant-lexer` | Wave 1 |
| **SA-04** | Spatial Canonicalizer & Lockfile | `crates/kant-canonical/` | `kant-core`, `kant-parser` | Wave 1 |
| **SA-05** | 12-Categories Type System | `crates/kant-types/` | `kant-core`, `kant-canonical` | Wave 2 |
| **SA-06** | Exact Effect & Quarantine Analyzer | `crates/kant-effects/` | `kant-core`, `kant-canonical`, `kant-types` | Wave 2 |
| **SA-07** | Al-Shaym SSA IR Lowering Engine | `crates/kant-ir/` | `kant-types`, `kant-effects` | Wave 2 |
| **SA-08** | Perceus Memory & Reuse Pass | `crates/kant-perceus/` | `kant-ir` | Wave 2 |
| **SA-09** | Paralogism Linear & Taint Guard | `crates/kant-paralogism/`| `kant-ir`, `kant-types` | Wave 3 |
| **SA-10** | Antinomy 3-Tier Contract Verifier| `crates/kant-antinomy/`  | `kant-ir`, `kant-types` | Wave 3 |
| **SA-11** | Noumena Capability Runtime | `crates/kant-noumena/`   | `kant-effects`, `kant-ir` | Wave 3 |
| **SA-12** | Amthoul Spec & Graph Extractor | `crates/kant-spec/`      | `kant-types`, `kant-effects` | Wave 3 |
| **SA-13** | KANT-IR Evaluator & Merkle Trace | `crates/kant-eval/`      | `kant-ir`, `kant-noumena`, `kant-perceus` | Wave 4 |
| **SA-14** | Cranelift JIT/AOT Native Codegen | `crates/kant-codegen/`   | `kant-ir`, `kant-eval` | Wave 4 |
| **SA-15** | Structured Diagnostics & Auto-Fix| `crates/kant-diag/`      | `kant-canonical` .. `kant-antinomy` | Wave 4 |
| **SA-16** | Unified CLI Driver (`kantc`) | `crates/kant-cli/`       | All Workspace Crates | Wave 4 |
| **SA-16** | Model Context Protocol Server | `crates/kant-mcp/`       | All Workspace Crates | Wave 4 |

Modifying files outside your assigned crate lane is strictly prohibited and results in immediate automated CI rejection.

---

## 3. Git Workflow & Branching Conventions

All development must occur on topic branches branched from `main`. Direct pushes to `main` are
restricted by repository branch protection policies.

### Branch Naming Standard
Branches must follow the structured pattern:
`<type>/<short-description>`

Allowed `<type>` prefixes:
- `feat/`: New language feature, compiler pass, or runtime capability.
- `fix/`: Bug fix or defect correction.
- `docs/`: Formal specifications, architectural reports, or reference documentation.
- `ci/`: Continuous integration, build matrix, or tooling automation.
- `refactor/`: Code reorganization without functional or behavioral changes.

Examples:
- `feat/transcendental-aesthetic-lexer`
- `fix/perceus-reference-cycle-leak`
- `ci/multi-platform-verification-matrix`

---

## 4. Conventional Commit Format & Enforcement Rules

Every commit in the Kant project MUST strictly conform to the **Conventional Commits 1.0.0** specification.
Commits are validated locally via Git hooks and in CI workflows.

### Structure
```
<type>(<scope>): <subject>

[optional body explaining context and rationale]

[optional footer(s)]
```

### Constraints
1. **Allowed Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
2. **Scope:** Mandatory or recommended identifier indicating the affected subsystem (e.g., `lexer`, `parser`, `ir`, `effects`, `workflows`).
3. **Subject Line Length:** Subject must be under 100 characters, written in imperative lowercase (no trailing period).
4. **Periodic Commits:** Work must be committed progressively as logical increments are completed; monolithic mega-commits are rejected.

---

## 5. Five-Step Verification Harness

Before opening a pull request or submitting work, execute the workspace verification harness:

```bash
# Step 1: Automated Formatting Check
cargo fmt --all -- --check

# Step 2: Zero-Warning Linter Audit
cargo clippy --workspace --all-targets --all-features -- -D warnings

# Step 3: Workspace Test Suite
cargo test --workspace --all-targets --all-features -- --nocapture

# Step 4: Python Infrastructure & Format Lint
python scripts/ci/check_format.py

# Step 5: Multi-Step Workspace Verification Suite
python scripts/ci/verify_workspace.py
```

All 5 steps must exit with return code `0`.

---

## 6. Pull Request Lifecycle & Mandatory Review

1. **Self-Verification Evidence:** Every Pull Request description must include the terminal output from the Five-Step Verification Harness.
2. **Automated CI Matrix:** All jobs in `.github/workflows/ci.yml`, `.github/workflows/security.yml`, and `.github/workflows/portal.yml` must succeed.
3. **SMT & Fuzzing Invariant Verification:**
   - Any modifications affecting the type system or contract engine require formal Z3 SMT contract consistency checks.
   - Any modifications to the lexer or parser must successfully execute continuous fuzzing vectors without panics or crashes.
4. **Architectural Review:** PRs modifying core specifications in `docs/spec/` or workspace-wide configs require approval from the Systems DevOps Architect or Project Lead.
