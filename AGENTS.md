# AGENTS.md: Root Architecture & Multi-Agent Constitution for Kant (.kant)

Welcome to **Kant** (`.kant`), an epistemologically rigorous, AI-native programming language inspired by Immanuel Kant's *Critique of Pure Reason* (specifically through the foundational Arabic translation and philosophical conceptualization by Lebanese philosopher Moussa Wehbe) integrated with modern compiler engineering, algebraic effect systems, capability security, and zero-allocation memory management.

This document serves as the master constitution and root coordination contract for all agents (human and synthetic) collaborating on the Kant compiler toolchain (`kantc`).

---

## 1. Project Identity & Namespace Isolation

To prevent naming collisions across the global software ecosystem, the following boundaries are strictly enforced:

* **Language Name:** Kant (stylized as **Kant**)
* **Source Extension:** `.kant` (UTF-8 encoded source file)
* **Projection & Sidecar Extension:** `.kantd` (holds non-semantic display names, localized Arabic terms, and line formatting)
* **Deterministic Lockfile:** `module.kant.lock` (pins canonical definition hashes and dependency roots)
* **Contract Specification View:** `.spec` (human-reviewable contract and effect signature)
* **Compiler Binary:** `kantc`
* **Cargo Workspace Prefix:** `kant-*` (e.g., `kant-core`, `kant-lexer`, `kant-parser`)
* **Magic Header:** `#![kant(v0.1)]` (mandatory top-level attribute to disambiguate from other DSLs)

### Explicit Disambiguation
* **TU Berlin KASH/KANT:** A legacy Computer Algebra System specialized in algebraic number theory. No overlap in syntax, runtime, or domain.
* **Aprover/kant:** A 66-commit Langium-based security protocol DSL on GitHub using `.kant`. Kant is disambiguated by compiler binary `kantc`, crate prefix `kant-*`, and header `#![kant(v0.1)]`.
* **PyPI `kant`:** Python event-sourcing/CQRS library (v2.1.0).
* **crates.io `kant`:** 156-line micro-telemetry crate (v0.0.3).
* **npm `@kant/node-boxcars`, `kant-ui`:** Unrelated front-end utilities.

---

## 2. Progressive Disclosure Index

To prevent context pollution and unnecessary token consumption, agents MUST NOT ingest the entire repository. Instead, consult the specialized formal specifications below:

| Specification Document | Epistemological Stage & Engineering Domain | Primary Coverage |
| :--- | :--- | :--- |
| [`01_EPISTEMOLOGY_AND_LEXICON.md`](docs/spec/01_EPISTEMOLOGY_AND_LEXICON.md) | Epistemology & Moussa Wehbe Lexicon | Philosophical dictionary, Martin-Löf type theory mapping, dual representation. |
| [`02_AESTHETICS_GRAMMAR_AND_AST.md`](docs/spec/02_AESTHETICS_GRAMMAR_AND_AST.md) | Transcendental Aesthetic | Flattened EBNF grammar, De Bruijn indices, canonical AST, SHA-256 identity. |
| [`03_ANALYTIC_CATEGORIES_AND_EFFECTS.md`](docs/spec/03_ANALYTIC_CATEGORIES_AND_EFFECTS.md) | Transcendental Analytic | 12 Categories type system, exact effect matching ($E_{\text{decl}} = E_{\text{inf}}$), `dyn` quarantine. |
| [`04_SCHEMATISM_IR_AND_PERCEUS.md`](docs/spec/04_SCHEMATISM_IR_AND_PERCEUS.md) | The Schematism (*Al-Shaym*) | 30-op SSA KANT-IR, Perceus garbage-free reference counting, drop-guided reuse. |
| [`05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md`](docs/spec/05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md) | Transcendental Dialectic | 3-tier contract verifier (Z3 SMT), Paralogism taint guard, Noumena capabilities (`trust none`). |
| [`06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md`](docs/spec/06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md) | Doctrine of Method | Cranelift JIT/AOT code generator, deterministic KANT-IR VM, Merkle evidence bundle. |
| [`07_AGENT_SURFACE_SIDECAR_AND_MCP.md`](docs/spec/07_AGENT_SURFACE_SIDECAR_AND_MCP.md) | Agent Surface & Tooling | JSON diagnostics with RFC 6902 patches, lockfile reconciliation R1–R6, MCP/LSP server. |
| [`DECISIONS_AND_DEFERRED_ROADMAP.md`](docs/DECISIONS_AND_DEFERRED_ROADMAP.md) | Architectural Decisions & Roadmap | P1/P2 deferred decision records (ADRs) and v0.1 to v1.0 milestone boundaries. |

---

## 3. Sub-Agent File Lanes (SA-01 to SA-16)

The project is structured as a modular Cargo workspace. To eliminate multi-agent write collisions, each sub-agent is assigned an **Exclusive Write-Allowlist Lane**. Modifying files outside your assigned crate lane is strictly prohibited and results in immediate rejection.

```
crates/
├── kant-core/          [SA-01: Epistemic & Workspace Bootstrapper]
├── kant-lexer/         [SA-02: Transcendental Aesthetic Lexer]
├── kant-parser/        [SA-03: Flattened Pratt & LL(1) Parser]
├── kant-canonical/     [SA-04: Spatial Canonicalizer & Sidecar Engine]
├── kant-types/         [SA-05: 12-Categories Type Checker]
├── kant-effects/       [SA-06: Exact Effect & Quarantine Analyzer]
├── kant-ir/            [SA-07: Al-Shaym SSA IR Lowering Engine]
├── kant-perceus/       [SA-08: Perceus Memory & Reuse Pass]
├── kant-paralogism/    [SA-09: Paralogism Ownership & Taint Guard]
├── kant-antinomy/      [SA-10: Antinomy Contract & Termination Verifier]
├── kant-noumena/       [SA-11: Noumena Capability & Governor Runtime]
├── kant-spec/          [SA-12: Amthoul Spec & Graph Extractor]
├── kant-eval/          [SA-13: Reference KANT-IR Evaluator & Merkle Evidence]
├── kant-codegen/       [SA-14: Cranelift JIT & Native AOT Backend]
├── kant-diag/          [SA-15: Structured Diagnostics & Auto-Fix Engine]
├── kant-cli/           [SA-16: Unified CLI Driver (kantc)]
└── kant-mcp/           [SA-16: Model Context Protocol Server]
```

### Sub-Agent Allocation & Wave Matrix

| Agent ID | Epistemic / Architectural Role | Assigned Crate Lane | Upstream Dependencies (Read-Only) | Wave |
| :--- | :--- | :--- | :--- | :--- |
| **SA-01** | Bootstrapper & Core Primitives | `crates/kant-core/` | Spec Docs, Root Manifest | Wave 1 |
| **SA-02** | Transcendental Aesthetic Lexer | `crates/kant-lexer/` | `kant-core` | Wave 1 |
| **SA-03** | Flattened Pratt & LL(1) Parser | `crates/kant-parser/` | `kant-core`, `kant-lexer` | Wave 1 |
| **SA-04** | Spatial Canonicalizer & Lock Engine | `crates/kant-canonical/` | `kant-core`, `kant-parser` | Wave 1 |
| **SA-05** | 12-Categories Type System | `crates/kant-types/` | `kant-core`, `kant-canonical` | Wave 2 |
| **SA-06** | Exact Effect & Quarantine Analyzer | `crates/kant-effects/` | `kant-core`, `kant-canonical`, `kant-types` | Wave 2 |
| **SA-07** | Al-Shaym SSA IR Lowering Engine | `crates/kant-ir/` | `kant-types`, `kant-effects` | Wave 2 |
| **SA-08** | Perceus Memory & In-Place Reuse | `crates/kant-perceus/` | `kant-ir` | Wave 2 |
| **SA-09** | Paralogism Linear & Taint Guard | `crates/kant-paralogism/`| `kant-ir`, `kant-types` | Wave 3 |
| **SA-10** | Antinomy 3-Tier Contract Verifier| `crates/kant-antinomy/`  | `kant-ir`, `kant-types` | Wave 3 |
| **SA-11** | Noumena Capability Runtime | `crates/kant-noumena/`   | `kant-effects`, `kant-ir` | Wave 3 |
| **SA-12** | Amthoul Spec & Graph Extractor | `crates/kant-spec/`      | `kant-types`, `kant-effects` | Wave 3 |
| **SA-13** | KANT-IR Evaluator & Merkle Trace | `crates/kant-eval/`      | `kant-ir`, `kant-noumena`, `kant-perceus` | Wave 4 |
| **SA-14** | Cranelift JIT/AOT Native Codegen | `crates/kant-codegen/`   | `kant-ir`, `kant-eval` | Wave 4 |
| **SA-15** | Structured Diagnostics & Auto-Fix| `crates/kant-diag/`      | `kant-canonical` .. `kant-antinomy` | Wave 4 |
| **SA-16** | Unified CLI, MCP Server & LSP | `crates/kant-cli/`, `crates/kant-mcp/` | All Crates | Wave 4 |

---

## 4. The Iron Law of Verification

Under empirical software engineering findings (SIGIL study, arXiv:2607.27309), conversational prose leads agents to skip verification in over 44% of tasks. Therefore, **THE IRON LAW OF VERIFICATION** is binding on all agents:

> **No sub-agent may declare a task complete, and no PR or worktree may be merged, without executing the mandatory Five-Step Verification Harness and attaching raw terminal outputs.**

### Five-Step Verification Harness
```bash
# 1. Format check
cargo fmt -p <crate-name> -- --check

# 2. Strict linter check (zero warnings tolerated)
cargo clippy -p <crate-name> --all-targets -- -D warnings

# 3. Unit and integration test suite
cargo test -p <crate-name> -- --nocapture

# 4. Mandatory conformance test vectors
cargo test -p <crate-name> conformance -- --exact

# 5. Git status check (ensuring clean lane with zero untracked artifacts)
git status --porcelain <crate-path>
```

---

## 5. Architectural Invariants

Every module in Kant must satisfy four core epistemic and engineering invariants:

1. **Deterministic Content-Addressing ($I_1$):** Every definition identity (`DefHash`) is a 32-byte SHA-256 digest of its canonicalized AST, invariant to local variable renames or whitespace changes.
2. **Exact Effect Matching ($I_2$):** A function $f$ is well-typed if and only if $E_{\text{decl}}(f) = E_{\text{inf}}(f)$. Undeclared effects or unused declared effects trigger compiler errors with deterministic RFC 6902 quick-fixes.
3. **Garbage-Free Memory Management ($I_3$):** All cyclic-free programs manage memory deterministically via Perceus reference counting and drop-guided reuse without any tracing garbage collector.
4. **Noumena Zero-Escape Boundary ($I_4$):** By default, code executes under `trust none`. The external world (files, network, OS, unvetted LLMs) is inaccessible without an explicit, linear, unforgeable capability token.
