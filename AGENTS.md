# AGENTS.md: Compiler Architecture & Multi-Agent Engineering Constitution for Kant (.kant)

This document establishes the binding architectural specification, workspace coordination rules, and verification contracts governing all human engineers and autonomous sub-agents contributing to the Kant compiler toolchain (`kantc`).

Kant formalizes constructive epistemology into compiler systems engineering: Martin-Löf constructive type theory, exact algebraic effect lattices, affine capability sandboxing, and zero-GC Perceus memory management with drop-guided reuse. Moussa Wehbe's Arabic philosophical lexicon is incorporated as a deterministic, bijective dual-surface AST projection ontology.

---

## 1. Project Identity & Namespace Isolation

To prevent namespace collisions across compiler ecosystems, software package registries, and formal verification frameworks, all tools and artifacts must strictly adhere to the following identity boundaries:

* **Language Identifier:** Kant (stylized as **Kant**)
* **Source File Extension:** `.kant` (UTF-8 encoded canonical source file)
* **Projection & Sidecar Extension:** `.kantd` (holds non-semantic display names, localized Arabic terms, and line formatting)
* **Deterministic Lockfile:** `module.kant.lock` (pins canonical definition hashes and dependency roots)
* **Contract Specification View:** `.spec` (contract signatures, pre/post-conditions, and effect sets)
* **Compiler Binary:** `kantc`
* **Cargo Workspace Prefix:** `kant-*` (e.g., `kant-core`, `kant-lexer`, `kant-parser`)
* **Magic Header Invariant:** `#![kant(v0.1)]` (mandatory top-level attribute disambiguating compilation units)

### Explicit Namespace Disambiguation
* **TU Berlin KASH/KANT:** A legacy Computer Algebra System specialized in algebraic number theory. No overlap in syntax, runtime, or domain.
* **Aprover/kant:** A 66-commit Langium-based security protocol DSL on GitHub using `.kant`. Kant is disambiguated by compiler binary `kantc`, crate prefix `kant-*`, and header `#![kant(v0.1)]`.
* **PyPI `kant`:** Python event-sourcing/CQRS library (v2.1.0).
* **crates.io `kant`:** 156-line micro-telemetry crate (v0.0.3).
* **npm `@kant/node-boxcars`, `kant-ui`:** Unrelated front-end utilities.

---

## 2. Progressive Disclosure Specification Index

To optimize agent context efficiency and prevent prompt degradation, agents must not ingest the entire repository simultaneously. Reference the specific architectural specification covering your assigned domain:

| Specification Document | Theoretical Domain & Compiler Stage | Primary Coverage |
| :--- | :--- | :--- |
| [`01_EPISTEMOLOGY_AND_LEXICON.md`](docs/spec/01_EPISTEMOLOGY_AND_LEXICON.md) | Constructive Epistemology & Dual-Surface Lexicon | Martin-Löf constructive type foundations, Moussa Wehbe bijective mapping table. |
| [`02_AESTHETICS_GRAMMAR_AND_AST.md`](docs/spec/02_AESTHETICS_GRAMMAR_AND_AST.md) | Spatial Normalization, EBNF Grammar & Canonical AST | Flattened EBNF grammar, De Bruijn indices, canonical AST serialization, SHA-256 DefHash. |
| [`03_ANALYTIC_CATEGORIES_AND_EFFECTS.md`](docs/spec/03_ANALYTIC_CATEGORIES_AND_EFFECTS.md) | 12-Categorical Type System & Effect Quarantine | Martin-Löf type judgments, exact effect matching ($E_{\text{decl}} = E_{\text{inf}}$), `dyn` call quarantine. |
| [`04_SCHEMATISM_IR_AND_PERCEUS.md`](docs/spec/04_SCHEMATISM_IR_AND_PERCEUS.md) | 30-Op SSA KANT-IR & Perceus Memory Engine | SSA IR instruction set, Perceus reference counting, drop-guided in-place reuse (`Alloc@r`). |
| [`05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md`](docs/spec/05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md) | 3-Tier Contract Verification & Capability Sandbox | 3-tier SMT verification pipeline (Z3), affine capability tokens (`trust none`), secret taint guard. |
| [`06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md`](docs/spec/06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md) | Reference Evaluator, Cranelift Backend & Evidence | SSA interpreter, Cranelift JIT/AOT code generator, differential testing, Merkle evidence chains. |
| [`07_AGENT_SURFACE_SIDECAR_AND_MCP.md`](docs/spec/07_AGENT_SURFACE_SIDECAR_AND_MCP.md) | Structured Diagnostics, Lockfile & MCP Tooling | RFC 6902 auto-fix JSON patches, lockfile reconciliation rules R1–R6, 10 canonical MCP tools. |
| [`DECISIONS_AND_DEFERRED_ROADMAP.md`](docs/DECISIONS_AND_DEFERRED_ROADMAP.md) | Architectural Decision Records (ADRs) & Roadmap | Formal resolutions Q01–Q32 and milestone progression from v0.1 MVP to v1.0 self-hosting. |

---

## 3. Sub-Agent File Lanes (SA-01 to SA-16)

The `kantc` toolchain is partitioned into 17 isolated Cargo crates across 16 sub-agent execution lanes. Modifying files outside your assigned write lane is strictly prohibited and constitutes an immediate verification failure.

```
crates/
├── kant-core/          [SA-01: Core Primitives & Invariant Bootstrap]
├── kant-lexer/         [SA-02: 48-Token Lexical Analyzer]
├── kant-parser/        [SA-03: Flattened Pratt & LL(1) Parser]
├── kant-canonical/     [SA-04: Spatial Canonicalizer & Lockfile Engine]
├── kant-types/         [SA-05: 12-Categories Constructive Type Checker]
├── kant-effects/       [SA-06: Exact Effect Matcher & Quarantine Analyzer]
├── kant-ir/            [SA-07: 30-Op SSA KANT-IR Lowering Engine]
├── kant-perceus/       [SA-08: Perceus RC Pass & Drop-Guided Reuse]
├── kant-paralogism/    [SA-09: Affine Ownership & Secret Taint Guard]
├── kant-antinomy/      [SA-10: 3-Tier Contract & Termination Verifier]
├── kant-noumena/       [SA-11: Noumena Capability Runtime Sandbox]
├── kant-spec/          [SA-12: Contract Specification & Graph Extractor]
├── kant-eval/          [SA-13: Reference SSA Evaluator & Merkle Trace Engine]
├── kant-codegen/       [SA-14: Cranelift JIT & Native AOT Backend]
├── kant-diag/          [SA-15: Structured Diagnostics & RFC 6902 Engine]
├── kant-cli/           [SA-16: Unified CLI Driver (kantc)]
└── kant-mcp/           [SA-16: Model Context Protocol Server]
```

### Sub-Agent Allocation & Dependency Matrix

| Agent ID | Architectural & Subsystem Role | Assigned Crate Lane | Upstream Dependencies (Read-Only) | Wave |
| :--- | :--- | :--- | :--- | :--- |
| **SA-01** | Core Primitives & Invariant Bootstrap | `crates/kant-core/` | Formal Specifications, Root Manifests | Wave 1 |
| **SA-02** | 48-Token Lexical Analyzer | `crates/kant-lexer/` | `kant-core` | Wave 1 |
| **SA-03** | Flattened Pratt & LL(1) Parser | `crates/kant-parser/` | `kant-core`, `kant-lexer` | Wave 1 |
| **SA-04** | Spatial Canonicalizer & Lockfile Engine | `crates/kant-canonical/` | `kant-core`, `kant-parser` | Wave 1 |
| **SA-05** | 12-Categories Constructive Type Checker | `crates/kant-types/` | `kant-core`, `kant-canonical` | Wave 2 |
| **SA-06** | Exact Effect Matcher & Quarantine Analyzer | `crates/kant-effects/` | `kant-core`, `kant-canonical`, `kant-types` | Wave 2 |
| **SA-07** | 30-Op SSA KANT-IR Lowering Engine | `crates/kant-ir/` | `kant-types`, `kant-effects` | Wave 2 |
| **SA-08** | Perceus RC Pass & Drop-Guided Reuse | `crates/kant-perceus/` | `kant-ir` | Wave 2 |
| **SA-09** | Affine Ownership & Secret Taint Guard | `crates/kant-paralogism/`| `kant-ir`, `kant-types` | Wave 3 |
| **SA-10** | 3-Tier Contract & Termination Verifier | `crates/kant-antinomy/`  | `kant-ir`, `kant-types` | Wave 3 |
| **SA-11** | Noumena Capability Runtime Sandbox | `crates/kant-noumena/`   | `kant-effects`, `kant-ir` | Wave 3 |
| **SA-12** | Contract Specification & Graph Extractor | `crates/kant-spec/`      | `kant-types`, `kant-effects` | Wave 3 |
| **SA-13** | Reference SSA Evaluator & Merkle Trace Engine | `crates/kant-eval/`      | `kant-ir`, `kant-noumena`, `kant-perceus` | Wave 4 |
| **SA-14** | Cranelift JIT & Native AOT Backend | `crates/kant-codegen/`   | `kant-ir`, `kant-eval` | Wave 4 |
| **SA-15** | Structured Diagnostics & RFC 6902 Engine | `crates/kant-diag/`      | `kant-canonical` .. `kant-antinomy` | Wave 4 |
| **SA-16** | Unified CLI Driver & MCP/LSP Daemon | `crates/kant-cli/`, `crates/kant-mcp/` | All Crates | Wave 4 |

---

## 4. The Iron Law of Verification

Under empirical software engineering findings (SIGIL study, arXiv:2607.27309), conversational prose leads autonomous agents to skip verification in over 44% of tasks. Therefore, **THE IRON LAW OF VERIFICATION** is binding on all agents without exception:

> **No sub-agent may declare a task complete, and no pull request or worktree may be merged into `main`, without executing the mandatory Five-Step Verification Harness and providing raw terminal execution logs proving zero errors and zero warnings.**

### Mandatory Five-Step Verification Harness
```bash
# 1. Format check across assigned crate
cargo fmt -p <crate-name> -- --check

# 2. Strict static analysis (zero warnings tolerated)
cargo clippy -p <crate-name> --all-targets -- -D warnings

# 3. Unit and integration test suite execution
cargo test -p <crate-name> -- --nocapture

# 4. Mandatory conformance test suite execution
cargo test -p <crate-name> conformance -- --exact

# 5. Git status check ensuring zero untracked artifacts or modified foreign lanes
git status --porcelain <crate-path>
```

---

## 5. Architectural Invariants

Every module and compiler pass in Kant must formally satisfy four foundational invariants:

### 5.1. Invariant $I_1$: Deterministic Content-Addressing
Every definition identity (`DefHash`) is a 32-byte cryptographic digest computed over the canonical serialized abstract syntax tree:

$$\text{DefHash} = \text{SHA-256}(\text{Serialize}(\text{CanonicalAST}(D)))$$

The canonical AST normalizes local variable names to De Bruijn indices (`@T.k`), sorts record fields and effect sets alphabetically, and eliminates cosmetic whitespace and comments. Identifier renaming or formatting permutations produce identical `DefHash` values.

### 5.2. Invariant $I_2$: Exact Effect Matching
A function $f$ is well-typed under the effect system if and only if its declared effect set matches its inferred atomic effect set with set equality:

$$f \text{ is soundly typed} \iff E_{\text{decl}}(f) = E_{\text{inf}}(f)$$

Undeclared effect escapes ($E_{\text{inf}} \setminus E_{\text{decl}} \neq \emptyset$) trigger error `KANT-E301`. Unused declared effects ($E_{\text{decl}} \setminus E_{\text{inf}} \neq \emptyset$) trigger error `KANT-E302`. Both emit machine-executable RFC 6902 JSON quick-fix patches.

### 5.3. Invariant $I_3$: Zero-GC Perceus Memory Reclamation
For all cyclic-free program graphs, memory reclamation is executed deterministically without a tracing garbage collector or manual pointer deallocation. Reference count increments and drops are placed at syntactically verified last-use points:

$$\forall v, \quad \text{drop}(v) \text{ is inserted at } \text{LastUse}(v)$$

When a value with reference count $R(v) = 1$ is dropped and a value of matching size is allocated within the same execution frame, the memory buffer is recycled in place via the drop-guided reuse operator $\text{Alloc}@r$. Reclamation is $\mathcal{O}(1)$ deterministic.

### 5.4. Invariant $I_4$: Noumena Affine Capability Boundary
Execution operates under strict default isolation (`trust none`). External environmental resources (file systems, network sockets, OS system calls, clock timers, external LLM calls) are classified as the external environment (*Noumena*). They cannot be accessed via ambient authority, global state, or indirect call pointers.

Access requires an explicit, unforgeable, linear capability token ($\text{CapToken}$) threaded through the call graph and governed by an enclosing `handle ... with governor` runtime sandbox.
