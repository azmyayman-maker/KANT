# DECISIONS_AND_DEFERRED_ROADMAP.md: Architectural Decision Records (ADRs) & Engineering Roadmap

This document serves as the official registry of Architectural Decision Records (ADRs) and the engineering triage roadmap for the Kant compiler project (`kantc`). It formalizes the resolution of all 32 technical architectural design decisions, categorizing them into 8 P0-blocking core invariants enforced in `v0.1` and 24 pragmatically deferred P1/P2 milestones.

---

## 1. Architectural Decision Records (The 32 ADRs)

```
                             32 ARCHITECTURAL DECISIONS
                      ┌────────────────────────────────┐
                      │   8 P0-BLOCKING (MVP CORE)     │
                      │  Enforced immediately in v0.1  │
                      └────────────────┬───────────────┘
                                       │
                      ┌────────────────┴───────────────┐
                      │   24 P1/P2-DEFERRED (ROADMAP)  │
                      │  Isolated & defaulted in v0.1  │
                      └────────────────────────────────┘
```

### Table of Architectural Decisions & Implementation Boundaries

| ID | Engineering Domain & Specification Question | Priority | Technical Resolution & Compiler Trait Boundary | Target Milestone |
| :--- | :--- | :--- | :--- | :--- |
| **Q01** | Keyword Lexicon: ASCII Latin vs. Localized Arabic | **P0-BLOCKING** | Pure ASCII keywords (`afhoum`, `shaym`) in `.kant` for token economy and fast LLM parsing; Arabic representation localized to `.kantd` sidecar. | `v0.1` (Implemented) |
| **Q02** | Global Ecosystem Namespace Disambiguation | **P0-BLOCKING** | Enforce binary name `kantc`, crate namespace prefix `kant-*`, and mandatory source header `#![kant(v0.1)]`. | `v0.1` (Implemented) |
| **Q03** | Expression Syntax: Infix vs. Polish Prefix | **P0-BLOCKING** | Flattened infix notation with explicit operator precedence for standard tooling compatibility and low block depth. | `v0.1` (Implemented) |
| **Q04** | AST Variable Binding: De Bruijn vs. Named Slots | **P0-BLOCKING** | Surface AST preserves identifiers; Canonical AST converts bindings to De Bruijn indices (`@T.k`) for invariant SHA-256 identity. | `v0.1` (Implemented) |
| **Q05** | Source Storage: Plain Text vs. Canonical JSON AST | **P0-BLOCKING** | Text-first UTF-8 source (`.kant`) tracked with deterministic lockfile (`module.kant.lock`). Machine export via `kantc ast --json`. | `v0.1` (Implemented) |
| **Q06** | Intent Clause Enforcement Level | **P1-DEFERRABLE** | Mandatory for public (`pub`) and effectful functions; optional warning on private local helper functions. | `v0.1` |
| **Q07** | Architectural `decision` Blocks in AST | **P2-DEFERRABLE** | Parsed into structured AST metadata nodes in v0.1; semantic querying engine deferred to v0.2. | `v0.1` |
| **Q08** | Closed Vocabulary Constraint | **P1-DEFERRABLE** | Strict invariant table of 48 closed tokens in v0.1; user-defined procedural macros deferred post-v1.0. | `v0.1` |
| **Q09** | Exact Algebraic Effect Matching Enforcement | **P0-BLOCKING** | Enforce exact set equality ($E_{\text{decl}} = E_{\text{inf}}$) across all functions; auto-fix via RFC 6902 JSON patch. | `v0.1` (Implemented) |
| **Q10** | Core Primitive Effect Lattice Definition | **P1-DEFERRABLE** | Core v0.1 lattice: `Pure`, `Console`, `Fs.Read/Write`, `Net.Http`, `Ai.Infer`, `Diverge`. | `v0.1` |
| **Q11** | Representation of Quantity Triad | **P1-DEFERRABLE** | Scalar primitives (Unity), contiguous slices (Plurality), exhaustive sum ADTs (Totality). Dependent types deferred. | `v0.1` |
| **Q12** | Dynamic Call Call-Graph Isolation | **P1-DEFERRABLE** | Bounded dispatch restricted to `dyn { t_1..t_n }` and closed dispatch tables. Unbounded function pointers prohibited. | `v0.1` |
| **Q13** | Iteration: Functional Combinators vs. Loops | **P1-DEFERRABLE** | Iteration bounded to pure combinators (`map/fold`) and recursion with mandatory `decreases` well-founded metrics. | `v0.1` |
| **Q14** | Row Polymorphism for Algebraic Effects | **P2-DEFERRABLE** | Explicit effect sums and `effects of(f)` inheritance in v0.1; general row polymorphism deferred to v0.5. | `v0.5` |
| **Q15** | Stream Channels Representation (`Community`) | **P2-DEFERRABLE** | Typed `!Stream<T>` types in standard library; single-threaded FIFO in v0.1; multi-threaded channels in v0.5. | `v0.5` |
| **Q16** | Typed Hole Expressions (`?hole`) | **P1-DEFERRABLE** | Supported in parser and type checker with unification variable $\tau_{\text{hole}}$ to facilitate incremental code synthesis. | `v0.1` |
| **Q17** | Multi-Tier Contract Verifier Architecture | **P0-BLOCKING** | 3-tier pipeline: Syntactic simplifier + Z3 SMT solver (10s budget) for Tier 1/2; compiled runtime assertions for Tier 3. | `v0.1` (Implemented) |
| **Q18** | Cyclic Data Structures in Perceus Memory | **P1-DEFERRABLE** | Direct pointer cycles prohibited at type level (Lean 4 model); arbitrary graph topologies require `ArenaIdx<T>`. | `v0.1` |
| **Q19** | Reference Count Atomicity in Perceus | **P2-DEFERRABLE** | High-performance single-threaded RC in v0.1; atomic reference counting (`Arc`) deferred to v0.5 concurrent runtime. | `v0.5` |
| **Q20** | Secret Taint Tracking & Memory Zeroization | **P2-DEFERRABLE** | `Secret<T>` wrapper enforcing constant-time execution, prohibition of secret-dependent branches, and zeroize-on-drop. | `v0.1` |
| **Q21** | Affine Ownership for Capability Tokens | **P1-DEFERRABLE** | Affine move-only semantics enforced strictly on capability handles; ordinary data managed automatically by Perceus. | `v0.1` |
| **Q22** | Formal Proof Export to Interactive Theorem Provers | **P2-DEFERRABLE** | Deferred to v0.2; contract AST structured with a clean `ProofExporter` trait boundary targeting Lean 4 and Dafny. | `v0.2` |
| **Q23** | Interactive Human-in-the-Loop Approval Gates | **P1-DEFERRABLE** | Built-in `approval_gate(policy)` suspending delimited continuations in evaluator and runtime daemon. | `v0.1` |
| **Q24** | Deterministic Execution Enforcement | **P1-DEFERRABLE** | Deterministic execution default; non-deterministic operations require explicit `ClockCap` or `EntropyCap` handles. | `v0.1` |
| **Q25** | Target Code Generation Backends | **P0-BLOCKING** | Reference SSA Interpreter (`kant-eval`) + Cranelift JIT/AOT (`kant-codegen`) for x86-64/ARM64. WASM deferred to v0.2. | `v0.1` (Implemented) |
| **Q26** | Compiler Diagnostic Machine Format | **P1-DEFERRABLE** | Structured JSON schema with unique error codes, `FixSafety: SAFE/REVIEW`, and RFC 6902 JSON patch vectors. | `v0.1` |
| **Q27** | Background Daemon & Model Context Protocol | **P1-DEFERRABLE** | `kantc serv` and `kant-mcp` exposing 10 canonical tools implemented in v0.1. | `v0.1` |
| **Q28** | Token Context Budgeting Tool | **P1-DEFERRABLE** | `kantc context --budget <kb>` included in v0.1 to export token-bounded semantic dependency slices. | `v0.1` |
| **Q29** | Content-Addressed Test Execution Caching | **P1-DEFERRABLE** | Content-addressed dependency cones; `kantc test` invalidates and reruns strictly affected definition subgraphs. | `v0.1` |
| **Q30** | Constrained Decoding Grammar Export | **P2-DEFERRABLE** | `kantc grammar --export-xgrammar` included in v0.1; live speculative socket streaming deferred to v0.2. | `v0.2` |
| **Q31** | Compiler-Injected Telemetry Infrastructure | **P2-DEFERRABLE** | Cryptographic hash-chained Merkle evidence bundles in v0.1; OpenTelemetry distributed spans deferred to v0.5. | `v0.5` |
| **Q32** | Graphical UI Execution Observatory | **P2-DEFERRABLE** | CLI, MCP, and LSP tools prioritized in v0.1; standalone GPUI desktop monitor deferred to v0.5. | `v0.5` |

---

## 2. Compiler Engineering Milestone Roadmap

### Phase I: Core Compiler MVP (`v0.1`) — *Current Baseline*
* Formal specifications verified and synchronized across `docs/spec/`.
* Flattened LL(1) and Pratt precedence parser with De Bruijn canonicalization.
* SHA-256 content-addressed definition hashing (`DefHash`) and `module.kant.lock` reconciliation.
* 12-Categories constructive type checker and exact algebraic effect verifier ($E_{\text{decl}} = E_{\text{inf}}$).
* 30-opcode SSA KANT-IR lowering pass with Perceus drop-guided in-place reuse (`Alloc@r`).
* Dual execution: Reference SSA interpreter (`kant-eval`) and native Cranelift JIT/AOT backend (`kant-codegen`).
* Structured RFC 6902 auto-fix JSON diagnostics and 10 canonical MCP tools (`kant-mcp`).

### Phase II: Verified Toolchain (`v0.2`)
* Persistent background Z3 SMT solver session integrated into language server (LSP).
* Formal proof export pipeline targeting Lean 4 and Dafny via `ProofExporter` trait.
* WebAssembly backend targeting WASI Preview 2.
* Live speculative type-directed sampling integration via IPC socket.

### Phase III: Concurrent Systems Runtime (`v0.5`)
* Atomic reference counting (`Atomic RC`) in Perceus with thread-safe borrowed references.
* Multi-threaded typed stream channels (`!Stream<T>`) with barrier synchronization.
* Automated OpenTelemetry distributed tracing span injection.
* GPUI high-performance desktop execution monitor.

### Phase IV: Self-Hosting Compiler (`v1.0`)
* `kantc` toolchain self-hosted and authored natively in `.kant`.
* Bit-identical self-compilation verification gate ($0\text{-byte diff}$ between boostrap iterations).
* Optional LLVM backend for extreme machine-code optimization.
