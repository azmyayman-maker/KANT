# DECISIONS_AND_DEFERRED_ROADMAP.md: Architectural Decisions & Pragmatic Roadmap

This document serves as the official registry of Architectural Decision Records (ADRs) and the **Pragmatic Deferral Engine** for the Kant compiler project. It records the resolution of all 32 clarification points from the architectural mandate, distinguishing between the 8 critical P0 invariants and the 24 pragmatically deferred P1/P2 features.

---

## 1. Architectural Invariant Triage (The 32 Decisions)

```
                            32 CLARIFICATION POINTS
                     ┌────────────────────────────────┐
                     │   8 P0-BLOCKING (MVP CORE)     │
                     │  Enforced immediately in v0.1  │
                     └────────────────┬───────────────┘
                                      │
                     ┌────────────────┴───────────────┐
                     │   24 P1/P2-DEFERRED (ROADMAP)  │
                     │  Defaulted & isolated in v0.1  │
                     └────────────────────────────────┘
```

### Table of the 32 Decisions & MVP Defaults

| ID | Domain & Question Summary | Priority | MVP Default Resolution & Trait Boundary | Target Milestone |
| :--- | :--- | :--- | :--- | :--- |
| **Q01** | Keyword Lexicon: Arabic vs Latin vs Dual | **P0-BLOCKING** | Standard Latin ASCII keywords (`afhoum`, `shaym`) in `.kant` for tokenizers; Arabic fidelity in `.kantd`. | `v0.1` (Implemented) |
| **Q02** | Namespace collision disambiguation | **P0-BLOCKING** | Binary `kantc`, crate prefix `kant-*`, magic header `#![kant(v0.1)]`. | `v0.1` (Implemented) |
| **Q03** | Syntax notation: Infix vs Prefix | **P0-BLOCKING** | Flattened Infix notation with explicit precedence for standard LLM familiarity. | `v0.1` (Implemented) |
| **Q04** | Variable naming: De Bruijn vs Names | **P0-BLOCKING** | Human names in source; automatic De Bruijn conversion in Canonical AST for SHA-256. | `v0.1` (Implemented) |
| **Q05** | Storage format: Text vs JSON AST | **P0-BLOCKING** | Text-first (`.kant`) with sidecar lockfile (`module.kant.lock`). `kantc ast --json` available. | `v0.1` (Implemented) |
| **Q06** | Intent clauses mandatory vs optional | **P1-DEFERRABLE** | Mandatory for `pub` and effectful functions; optional warning for local helpers. | `v0.1` |
| **Q07** | Architectural `decision` blocks in grammar | **P2-DEFERRABLE** | Parsed as structured metadata; full semantic querying deferred to v0.2. | `v0.1` |
| **Q08** | Closed vocabulary constraint | **P1-DEFERRABLE** | Closed dictionary of 48 tokens in MVP; macros deferred to post-v1.0. | `v0.1` |
| **Q09** | Exact Effect Matching enforcement | **P0-BLOCKING** | Exact set equality ($E_{\text{decl}} = E_{\text{inf}}$) enforced across all modes; auto-fix via JSON Patch. | `v0.1` (Implemented) |
| **Q10** | Core effect lattice definition | **P1-DEFERRABLE** | Core MVP lattice: `Pure`, `Console`, `Fs.Read/Write`, `Net.Http`, `Ai.Infer`, `Diverge`. | `v0.1` |
| **Q11** | Representation of Quantity triad | **P1-DEFERRABLE** | Primitives (Unity), Slices (Plurality), Exhaustive Enums (Totality). Dependent types deferred. | `v0.1` |
| **Q12** | Dynamic call isolation | **P1-DEFERRABLE** | Restrict to `dyn { t_1..t_n }` and closed dispatch tables. No raw function pointers. | `v0.1` |
| **Q13** | Loop constructs vs Decreasing recursion | **P1-DEFERRABLE** | Iteration restricted to functional combinators (`map/fold`) and verified `decreases` recursion. | `v0.1` |
| **Q14** | Row polymorphism for effects | **P2-DEFERRABLE** | Explicit effect sums and `effects of(f)` inheritance. Row polymorphism deferred to v0.5. | `v0.5` |
| **Q15** | Category of Community (Stream channels) | **P2-DEFERRABLE** | Typed `!Stream<T>` types declared in stdlib; sequential evaluation in MVP; multi-threading in v0.5. | `v0.5` |
| **Q16** | Typed hole expressions (`?hole`) | **P1-DEFERRABLE** | Fully supported in parser and type checker to facilitate incremental agent generation. | `v0.1` |
| **Q17** | Contract verifier architecture | **P0-BLOCKING** | 3-tier system: Internal simplifier + Z3 SMT (10s budget) for Tier 1; Tier 3 runtime fallback. | `v0.1` (Implemented) |
| **Q18** | Cyclic graphs in Perceus memory | **P1-DEFERRABLE** | Direct pointer cycles prohibited at type level (Lean 4 approach); arena indices for graphs. | `v0.1` |
| **Q19** | Reference count atomicity in Perceus | **P2-DEFERRABLE** | Fast thread-local RC in MVP; atomic RC upgrade deferred to v0.5 concurrent runtime. | `v0.5` |
| **Q20** | Secret taint analysis and zeroization | **P2-DEFERRABLE** | `Secret<T>` wrapper type with constant-time branching checks and zeroize-on-drop. | `v0.1` |
| **Q21** | Affine ownership for capabilities | **P1-DEFERRABLE** | Affine (move-only) checks enforced strictly on capability tokens; normal values managed by Perceus. | `v0.1` |
| **Q22** | Formal proof export to Lean 4 / Dafny | **P2-DEFERRABLE** | Deferred to v0.2; contract AST designed with clean `ProofExporter` trait boundary. | `v0.2` |
| **Q23** | Human-in-the-loop approval gates | **P1-DEFERRABLE** | Built-in `approval_gate(policy)` suspending continuation in evaluator/runtime. | `v0.1` |
| **Q24** | Deterministic mode enforcement | **P1-DEFERRABLE** | Determinism default: non-deterministic sources require explicit `ClockCap` or `EntropyCap`. | `v0.1` |
| **Q25** | Target backends for MVP | **P0-BLOCKING** | Reference KANT-IR Evaluator + Cranelift JIT/AOT (x86-64 / ARM64). WASM deferred to v0.2. | `v0.1` (Implemented) |
| **Q26** | Compiler error format | **P1-DEFERRABLE** | Structured JSON with fixed error codes, `FixSafety: SAFE/REVIEW`, and RFC 6902 patches. | `v0.1` |
| **Q27** | Background agent daemon and MCP | **P1-DEFERRABLE** | Include `kantc serv` and `kant-mcp` (10 canonical tools) in MVP. | `v0.1` |
| **Q28** | Context budgeting tool | **P1-DEFERRABLE** | Include `kantc context --budget <kb>` in MVP for efficient agent prompt construction. | `v0.1` |
| **Q29** | Content-addressed test caching | **P1-DEFERRABLE** | Pinned dependency cones; `kantc test` reruns only invalidated defs. | `v0.1` |
| **Q30** | Constrained decoding grammar export | **P2-DEFERRABLE** | `kantc grammar --export-xgrammar` included in MVP; live speculative sampling socket deferred. | `v0.2` |
| **Q31** | Compiler-injected telemetry | **P2-DEFERRABLE** | Hash-chained Merkle evidence bundles in MVP; OpenTelemetry spans deferred to v0.5. | `v0.5` |
| **Q32** | Graphical UI monitor | **P2-DEFERRABLE** | Focus 100% on CLI, MCP, and LSP in MVP; GPUI graphical monitor deferred to v0.5. | `v0.5` |

---

## 2. Milestone Roadmap: From MVP to Self-Hosting

### Phase I: Transcendental MVP (`v0.1`) — *Current Target*
* 8 Reference Specification files pinned in root and `docs/spec/`.
* Complete Pratt/LL(1) parser, De Bruijn canonicalizer, and SHA-256 content addressing.
* 12-Categories type inference engine and exact effect verification.
* KANT-IR SSA lowering pass and Perceus drop-guided reuse.
* Dual execution: Reference Evaluator + Cranelift JIT/AOT.
* Structured JSON diagnostics with automated RFC 6902 patch repair.
* 10-tool MCP server daemon (`kant-mcp`).

### Phase II: Verified Kant (`v0.2`)
* Persistent Z3 SMT solver session integrated into LSP.
* Formal proof export to Lean 4 and Dafny (`ProofExporter`).
* WebAssembly (WASI Preview 2) compilation target.
* Live speculative type-directed sampling integration.

### Phase III: Concurrent Kant (`v0.5`)
* Atomic reference counting (`Atomic RC`) in Perceus with frame-limited borrowing.
* Multi-threaded typed stream channels (`!Stream<T>`) with barrier synchronization.
* OpenTelemetry automated tracing span injection.
* GPUI-based high-performance desktop execution monitor.

### Phase IV: Self-Hosting Fixed Point (`v1.0`)
* The entire `kantc` toolchain rewritten natively in `.kant`.
* Bit-for-bit identical self-compilation verification gate.
* Optional LLVM backend for extreme optimization.
