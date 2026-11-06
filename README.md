<div align="center">

<img src="assets/kant-icon.svg" width="160" height="160" alt="Kant Programming Language Logo" />

# KANT

**Kant: An Epistemologically Grounded Systems Programming Language with Constructive Type Theory, Exact Algebraic Effects, and Zero-GC Perceus Memory Management**

[![Spec Version](https://img.shields.io/badge/spec-v0.1.0--alpha-blue.svg?style=flat-square)](docs/spec/)
[![License](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-emerald.svg?style=flat-square)](LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.80%2B-orange.svg?style=flat-square)](kant-toolchain.toml)
[![Workspace](https://img.shields.io/badge/workspace-17%20crates-purple.svg?style=flat-square)](crates/)
[![Git Remote](https://img.shields.io/badge/origin-azmyayman--maker%2FKANT-cyan.svg?style=flat-square)](https://github.com/azmyayman-maker/KANT.git)

*Epistemological architecture and Moussa Wehbe's dual-representation Arabic lexicon formalized as constructive type theory, deterministic SSA intermediate representation, and capabilities-secured systems programming.*

</div>

---

## 1. Systems Architecture & Design Principles

**Kant** (`.kant`) is a statically typed, deterministic systems programming language designed for verifiable human and autonomous software agent collaboration. Rather than relying on unchecked ambient authority or nondeterministic runtime tracing, Kant maps constructive epistemology into formal programming language theory (PLT) and compiler engineering:

* **Formal Verifiability & Invariant Soundness:** Every program unit satisfies strict categorical typing, termination obligations via well-founded metrics (`decreases`), and pre-/post-condition contracts verified through a 3-tier pipeline combining syntactic interval evaluation, automated SMT solving (Z3), and static capability analysis.
* **Deterministic Spatial Normalization:** Source files are transformed into canonical abstract syntax trees with De Bruijn variable indexing (`@T.0`, `@T.1`), invariant alphabetical sorting of structural fields, and cryptographic SHA-256 definition identity hashes (`DefHash`). Surface cosmetic permutations do not perturb semantic hashes.
* **Zero-GC Perceus Memory Reclamation:** Memory is governed deterministically without a garbage collector or manual pointer arithmetic. The compiler inserts reference-counting updates and drop operations at syntactically verified last-use points, recycling matching memory cells in place via drop-guided reuse (`Alloc@r`).
* **Affine Capability Security (Noumena Sandbox):** Ambient I/O, network sockets, file system access, and external hardware are quarantined outside the typed memory boundary. Execution operates under default `trust none`, requiring unforgeable linear capability tokens passed explicitly down the call graph.

---

## 2. Language Semantics & Type System

Kant's type system is grounded in Martin-Löf Constructive Type Theory, organizing all valid computational types across the twelve categorical judgment forms partitioned into four fundamental triads:

### 2.1. The 12 Categorical Judgment Forms

| Triad | Category | Language Type / Constructor | Formal Type-Theoretic Semantics |
| :--- | :--- | :--- | :--- |
| **Quantity** | Unity | `Unit`, `Bool`, `Int64`, `Float64`, `String` | Indivisible atomic base types (0-tuples, booleans, machine integers, IEEE-754 floats). |
| | Plurality | `Slice<T>`, `[T; N]` | Linearly indexed finite sequences and contiguous homogeneous buffer slices. |
| | Totality | `enum` / Algebraic Sum Types, Refinements | Closed, exhaustive sum types $\sum_{i} T_i$ and predicate-bounded integers. |
| **Quality** | Reality | Inhabited Types (`T`) | Types with constructive inhabitants certified by sound proof witnesses. |
| | Negation | Bottom / Never (`!`) | Empty type $\bot$; denotes non-terminating branches or divergence. |
| | Limitation | `Secret<T>`, Attenuated Capabilities | Information-flow security wrappers enforcing constant-time execution and zeroization. |
| **Relation** | Substance | `afhoum` (Value Structs) | Persistent product types $\prod_{i} T_i$ with structural value equality. |
| | Causality | Arrow Types `fn(A) -> B ! E` | Explicitly effect-annotated morphisms with deterministic state transitions. |
| | Community | `!Stream<T>` | Synchronous, typed channel morphisms with bidirectional conservation laws. |
| **Modality** | Possibility | `Option<T>`, `Result<T, E>` | Monadic error envelopes representing partial computable functions. |
| | Actuality | `cap &Cap` | Linear, non-forgeable hardware capability tokens active in current runtime frames. |
| | Necessity | `const`, Compile-Time Theorems | Statically verified invariants, SMT tautologies, and compile-time evaluated constants. |

### 2.2. Exact Algebraic Effect Matching (The Sigil Law)

The compiler enforces strict effect equivalence across all call sites:

$$\forall f, \quad E_{\text{decl}}(f) = E_{\text{inf}}(f)$$

Ambient, undeclared, or implicit side effects trigger fatal compilation errors (`KANT-E301`). Unused declared effects trigger dead-annotation errors (`KANT-E302`). Dynamic or indirect function invocations are quarantined exclusively inside `dyn { target_1, ..., target_n }` blocks with closed, statically verified target bounds.

---

## 3. Dual-Surface AST Projection

Kant provides an algebraic dual-representation ontology, decoupling compiler consumption from human and multilingual projection:

```
Canonical ASCII Source (.kant)      Projection Sidecar (.kantd)        Deterministic Lockfile
[Dense ASCII / De Bruijn AST]  <-->  [Moussa Wehbe Arabic Lexicon] <--> [module.kant.lock]
```

* **Canonical Compiler Ingestion (`.kant`):** Dense ASCII syntax standardized for token efficiency in LLM context windows, deterministic parsing, and fast type-checking passes.
* **Dual-Surface Projection Sidecar (`.kantd`):** Deterministic AST sidecar mapping byte spans to Moussa Wehbe's formal Arabic philosophical and mathematical terminology (*المُجاوِز، الأفهوم، الشَّيْم، النومان، الأمثول*) without altering canonical `DefHash` digests.
* **Deterministic Lockfile Engine (`module.kant.lock`):** Mechanical reconciliation engine enforcing rules R1 through R6 for definition renaming, dependency tracking, and AST tamper detection.
* **Magic Header Invariant:** Every compilation unit mandates `#![kant(v0.1)]` as its initial token, guaranteeing namespace isolation across package ecosystems.

---

## 4. Compiler Toolchain & Workspace Architecture

The `kantc` toolchain is architected as 17 modular Rust crates under `crates/`, enforcing strict layer decoupling:

```
crates/
├── kant-core/          # Core primitives, ByteSpan, SymbolId, SHA-256 DefHash
├── kant-lexer/         # Lexical analyzer for the 48 closed tokens
├── kant-parser/        # Flattened LL(1) and Pratt precedence parser
├── kant-canonical/     # Spatial AST canonicalizer, De Bruijn alpha-renaming, .kantd sidecar
├── kant-types/         # Martin-Löf 12-categories type inference and checker
├── kant-effects/       # Exact effect lattice matcher and dyn quarantine analyzer
├── kant-ir/            # 30-opcode Static Single Assignment (SSA) KANT-IR lowering
├── kant-perceus/       # Perceus deterministic reference counting & drop-guided reuse (Alloc@r)
├── kant-paralogism/    # Affine capability ownership checker & Secret<T> taint analysis
├── kant-antinomy/      # 3-tier contract verifier (syntactic, Z3 SMT, fallback assertions)
├── kant-noumena/       # Capability security runtime & sandboxed executor
├── kant-spec/          # Contract specification view extractor and call graph builder
├── kant-eval/          # Deterministic SSA reference tree-walk interpreter & Merkle evidence
├── kant-codegen/       # Cranelift JIT compiler and native static AOT binary generator
├── kant-diag/          # Structured machine diagnostics & RFC 6902 JSON patch generator
├── kant-cli/           # Unified compiler driver binary (kantc)
└── kant-mcp/           # Model Context Protocol (MCP) server & Language Server Protocol (LSP)
```

---

## 5. Telemetry & Verification Framework

The toolchain integrates runtime deterministic replay and multi-tier verification telemetry:

* **Merkle Evidence Bundles (`module.kant.evidence.jsonl`):** Execution traces, capability invocations, and I/O transitions are recorded in cryptographic hash-chained Merkle logs, providing bit-level reproducibility (`kantc replay`).
* **Differential Verification:** All compiler optimizations are differentially verified by executing the 30-op SSA reference interpreter (`kant-eval`) against Cranelift native machine codegen (`kant-codegen`), asserting byte-level execution equivalence.
* **Roadmap Observatory (`kant-roadmap-tracker.html`):** An isolated single-file local visualization dashboard tracks verification milestones across the 17 workspace crates without external network dependencies or workspace pollution.

---

## 6. Getting Started & Verification Commands

### Toolchain Prerequisites
* **Rust Toolchain:** 1.80.0+ (`kant-toolchain.toml`)
* **Python:** 3.10+ (for workspace validation tooling and telemetry engine)
* **Git:** 2.40+

### Workspace Verification
All contributions must satisfy the workspace verification suite without warnings:

```powershell
# 1. Verify workspace compilation across all 17 crates
cargo check --workspace

# 2. Execute unit and conformance test suites
cargo test --workspace

# 3. Verify standard code formatting compliance
cargo fmt --check
```

### Launching the Local Roadmap Observatory
```powershell
# Standalone local browser session (isolated from Git repository)
start kant-roadmap-tracker.html
```

---

## 7. Repository Provenance & License

* **Canonical Remote:** `https://github.com/azmyayman-maker/KANT.git`
* **Default Branch:** `main`
* **Official Vector Icon:** `assets/kant-icon.svg`
* **Licensing:** Dual-licensed under the [Apache License, Version 2.0](LICENSE) or the [MIT License](LICENSE).
