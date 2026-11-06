<div align="center">

<img src="assets/kant-icon.svg" width="160" height="160" alt="Kant Programming Language Logo" />

# KANT

**Epistemologically Rigorous, AI-Native Systems Programming Language**

[![Spec Version](https://img.shields.io/badge/spec-v0.1.0--alpha-blue.svg?style=flat-square)](docs/spec/)
[![License](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-emerald.svg?style=flat-square)](LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.80%2B-orange.svg?style=flat-square)](kant-toolchain.toml)
[![Workspace](https://img.shields.io/badge/workspace-17%20crates-purple.svg?style=flat-square)](crates/)
[![Git Remote](https://img.shields.io/badge/origin-azmyayman--maker%2FKANT-cyan.svg?style=flat-square)](https://github.com/azmyayman-maker/KANT.git)

*Inspired by Immanuel Kant's Critique of Pure Reason (Kritik der reinen Vernunft) through the foundational Arabic translation and philosophical lexicon of Moussa Wehbe (موسى وهبه).*

</div>

---

## 1. Philosophical & Epistemological Foundation

**Kant** (`.kant`) is an epistemologically principled systems programming language designed from first principles for verifiable human and AI-agent collaboration. Unlike conventional programming languages that treat computation as arbitrary state mutation, Kant establishes a constructive, categorical foundation where code mirrors the architecture of human cognition:

* **Transcendental Aesthetic (*الأستطيقا المجاوزة*) — A Priori Forms of Space & Time:**
  Every computation exists within strict spatial and temporal bounds. Syntax is normalized into a canonical AST with De Bruijn indices (`@T.0`, `@T.1`), lexical spans, and SHA-256 identity hashes, eliminating cosmetic token variations and KV-cache hallucinations.
* **Transcendental Analytic (*التحليلياء المجاوزة*) — The 12 Categories (*المقولات الاثنتا عشرة*):**
  A constructive type system rooted in Martin-Löf type theory, structured strictly into the 12 categorical judgment triads:
  * **Quantity (*الكم*):** Unity (`unity` primitives), Plurality (`plurality` slices), Totality (`totality` algebraic data types).
  * **Quality (*الكيف*):** Reality (`reality` inhabited types), Negation (`negation` uninhabited `!`), Limitation (`limitation` taint-isolated `Secret<T>`).
  * **Relation (*الإضافة*):** Substance (`substance` struct records), Causality (`causality` effect-annotated function arrows `fn -> T ! E`), Community (`community` immutable shared borrows).
  * **Modality (*الجهة*):** Possibility (`possible` optional `Option<T>` / `Result<T, E>`), Actuality (`actual` affine hardware and capability tokens), Necessity (`necessary` compile-time immutable axioms).
* **The Schematism (*شيم الفهم KANT-IR*):**
  A 30-operation Static Single Assignment (SSA) intermediate representation that bridges pure categorical concepts to concrete machine operations.
* **Exact Effect Matching (*قانون السمة Sigil Law*):**
  Kant enforces exact effect equivalence ($E_{\text{decl}} = E_{\text{inf}}$). Ambient, undeclared, or implicit I/O is impossible. Non-local, indirect calls are quarantined strictly within explicit `dyn { ... }` blocks with statically proven call targets.
* **Perceus Garbage-Free Memory Management:**
  Zero-allocation reference counting with drop-guided in-place reuse (`Alloc@r`), delivering deterministic, GC-free systems execution without manual memory hazards.
* **Transcendental Dialectic (*الجدلياء المجاوزة*) & Noumena Security:**
  Eliminates speculative antinomies and security vulnerabilities via affine capability tokens (`trust none`), 3-tier contract verifiers (Z3 SMT backed), and secret taint tracking.
* **Doctrine of Method (*مبحث المنهج*):**
  Guarantees cryptographic determinism through Merkle evidence bundles, reference KANT-IR evaluation, and native machine code generation via Cranelift JIT/AOT.

---

## 2. Dual Surface Representation & Identity Isolation

Kant enforces a dual-surface architecture to empower Arabic philosophical review while guaranteeing maximum LLM token economy and compiler velocity:

```
Source Code (.kant)          Projection Sidecar (.kantd)        Deterministic Lockfile
[Pure ASCII Canonical]  <-->  [Localized Arabic Terms & Docs] <--> [module.kant.lock]
```

* **Compiler Intake (`.kant`):** Dense, ASCII-canonical syntax optimized for compiler parsing, formal verification, and LLM context efficiency.
* **Philosophical Projection (`.kantd`):** Non-semantic sidecar holding rich Arabic translations from Moussa Wehbe's lexicon (*المُجاوِز، الأفهوم، الشَّيْم، النومان، الأمثول*) and source formatting without altering definition hashes.
* **Deterministic Lockfile (`module.kant.lock`):** Mechanical reconciliation engine enforcing rules R1 through R6 for definition renaming, dependency tracking, and tamper prevention.
* **Magic Header:** All compilation units mandate the top-level magic header `#![kant(v0.1)]` to eliminate ecosystem collisions with legacy tools or package registries.

---

## 3. Architecture & Specification Index

For detailed technical specifications, consult the progressive disclosure documents in [`docs/spec/`](docs/spec/):

| Specification Document | Philosophical Stage | Domain & Technical Content |
| :--- | :--- | :--- |
| [`01_EPISTEMOLOGY_AND_LEXICON.md`](docs/spec/01_EPISTEMOLOGY_AND_LEXICON.md) | Groundwork | Philosophical dictionary, Moussa Wehbe mapping, Martin-Löf type foundations. |
| [`02_AESTHETICS_GRAMMAR_AND_AST.md`](docs/spec/02_AESTHETICS_GRAMMAR_AND_AST.md) | Aesthetic | Flattened EBNF grammar, De Bruijn indices, canonical AST, SHA-256 identity hashing. |
| [`03_ANALYTIC_CATEGORIES_AND_EFFECTS.md`](docs/spec/03_ANALYTIC_CATEGORIES_AND_EFFECTS.md) | Analytic | 12-Categories type system, Sigil Law ($E_{\text{decl}} = E_{\text{inf}}$), `dyn` quarantine. |
| [`04_SCHEMATISM_IR_AND_PERCEUS.md`](docs/spec/04_SCHEMATISM_IR_AND_PERCEUS.md) | Schematism | 30-instruction SSA KANT-IR, Perceus RC reuse, zero-allocation memory pass. |
| [`05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md`](docs/spec/05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md) | Dialectic | 3-tier contract verification, Z3 SMT bridge, Paralogism taint guard, Noumena capabilities. |
| [`06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md`](docs/spec/06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md) | Method | Deterministic KANT-IR tree-walk evaluator, Cranelift JIT/AOT backend, Merkle traces. |
| [`07_AGENT_SURFACE_SIDECAR_AND_MCP.md`](docs/spec/07_AGENT_SURFACE_SIDECAR_AND_MCP.md) | Agent Surface | RFC 6902 auto-fix JSON diagnostics, XGrammar schemas, MCP & LSP servers. |
| [`DECISIONS_AND_DEFERRED_ROADMAP.md`](docs/DECISIONS_AND_DEFERRED_ROADMAP.md) | ADR Index | Architectural Decision Records (ADRs) Q01–Q32 and deferred v0.2+ boundaries. |
| [`AGENTS.md`](AGENTS.md) | Constitution | Multi-agent coordination constitution, 16 isolated file lanes, and the Iron Law of Verification. |

---

## 4. Cargo Workspace Architecture

The Kant toolchain is organized into 17 modular Rust crates under `crates/`, partitioned into strictly isolated sub-agent write lanes (SA-01 through SA-16):

```
crates/
├── kant-core/          # [SA-01] Epistemic & Workspace Bootstrapper (ByteSpan, SymbolId, DefHash)
├── kant-lexer/         # [SA-02] Transcendental Aesthetic Lexer (48 closed epistemic tokens)
├── kant-parser/        # [SA-03] Flattened Pratt & LL(1) Parser (top-level declarations & contracts)
├── kant-canonical/     # [SA-04] Spatial Canonicalizer & Sidecar Engine (.kantd, lockfile R1–R6)
├── kant-types/         # [SA-05] 12-Categories Type Checker & Inference Engine
├── kant-effects/       # [SA-06] Exact Effect Matcher & Quarantined Dynamism Analyzer
├── kant-ir/            # [SA-07] Al-Shaym SSA IR Lowering Engine (30 instructions)
├── kant-perceus/       # [SA-08] Perceus Memory Pass (drop-guided reuse, Alloc@r)
├── kant-paralogism/    # [SA-09] Paralogism Ownership Checker & Secret Taint Guard
├── kant-antinomy/      # [SA-10] Antinomy 3-Tier Contract & AST Termination Verifier
├── kant-noumena/       # [SA-11] Noumena Affine Capability Security & Governor Runtime
├── kant-spec/          # [SA-12] Amthoul Contract Specification & Call Graph Extractor
├── kant-eval/          # [SA-13] Reference KANT-IR Evaluator & Merkle Evidence Tree
├── kant-codegen/       # [SA-14] Cranelift JIT & Native AOT Backend
├── kant-diag/          # [SA-15] Structured Diagnostics Engine (RFC 6902 auto-fix patches)
├── kant-cli/           # [SA-16] Unified CLI Driver (kantc)
└── kant-mcp/           # [SA-16] Model Context Protocol & LSP Server
```

---

## 5. Telemetry & Topological Roadmap Portal (`portal/`)

Kant features an isolated, live telemetry portal providing real-time topological visualization of the project roadmap (Macro-Circles C0 through C6, 75 atomic verification tasks, gate audits, and epistemic checkpoints).

### Launching the Portal Locally

#### Option A: Standalone Browser Mode (Zero Installation)
Double-click or open `portal/index.html` (or root `kant-roadmap-tracker.html`) in any modern browser:
```powershell
start portal/index.html
```

#### Option B: Dedicated Local Telemetry Server
Run the lightweight, zero-dependency Python server:
```powershell
python portal/server.py --port 8080
```
Open your browser at **[http://127.0.0.1:8080](http://127.0.0.1:8080)**.

> **Telemetry Isolation Guarantee:** The portal is completely isolated within `portal/`. Its local runtime logs (`.kant-tracker/`, `*.db`, `*.log`) are strictly git-ignored to ensure zero repo pollution.

---

## 6. Verification & Development

Kant enforces the **Iron Law of Verification** (mandated in `AGENTS.md`). Before any commit, the workspace must compile cleanly:

```powershell
# Run workspace check across all 17 crates
cargo check --workspace

# Run workspace unit and conformance tests
cargo test --workspace

# Run formatting check
cargo fmt --check
```

### Requirements
* **Rust:** 1.80.0 or later (`kant-toolchain.toml`)
* **Python:** 3.10+ (for local telemetry portal)
* **Git:** 2.40+

---

## 7. Repository Provenance

* **Official Remote:** `https://github.com/azmyayman-maker/KANT.git`
* **Default Branch:** `main`
* **Official Brand Icon:** `assets/kant-icon.svg` (and mirror `portal/assets/kant-icon.svg`)
* **License:** Licensed under either of [Apache License, Version 2.0](LICENSE) or [MIT License](LICENSE) at your option.

---

<div align="center">
<i>"Two things fill the mind with ever new and increasing admiration and awe: the starry heavens above me and the moral law within me."</i><br>
— Immanuel Kant, <i>Critique of Practical Reason</i> (1788)
</div>
