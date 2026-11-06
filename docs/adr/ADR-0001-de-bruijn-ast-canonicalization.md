# ADR-0001: De Bruijn AST Canonicalization & Content Addressing

* **Status:** Accepted
* **Deciders:** Kant Architecture Working Group, Epistemic Core Architects
* **Date:** 2026-11-06
* **Technical Subsystem:** `crates/kant-canonical`
* **Related Invariant:** Invariant $I_1$ (Deterministic Content-Addressing)

---

## Context & Problem Statement

In traditional programming languages, a function's identity is bound to transient surface properties: its file path, line number, human variable naming choices, and formatting whitespace. In an AI-native multi-agent compiler environment, AI agents continuously refactor local variable names (`x` to `counter`), format code, and adjust comments. In conventional build systems, these cosmetic modifications invalidate dependency caches, trigger unnecessary cascading re-compilations, break deterministic distributed builds, and obscure semantic diffs.

How can `kantc` represent and identify program definitions such that code identity is purely semantic and invariant to local naming, formatting, and file organization?

---

## Decision Drivers

1. **Semantic Invariance:** Renaming local variables or refactoring comments must yield an identical cryptographic identity.
2. **Deterministic Content Addressing:** Every definition must have a unique 32-byte SHA-256 identifier (`DefHash`) for incremental compilation and Merkle audit trails.
3. **Cache Efficiency:** Content-addressed caching allows `kantc test` and `kantc build` to execute only over genuinely modified dependency cones.
4. **Machine Interoperability:** Sidecar metadata must decouple visual human preferences from the compiler's canonical AST.

---

## Considered Options

* **Option 1: Surface AST Serialization with Lexical Stripping (Comments & Whitespace Only)**
* **Option 2: De Bruijn Index Slot Conversion with Canonical Binary Serialization (`CanonicalAST`)**
* **Option 3: Hash-Consed Graph Database (Unison-style Pure Functional Term Graph)**

---

## Decision Outcome

**Chosen Option:** **Option 2: De Bruijn Index Slot Conversion with Canonical Binary Serialization (`CanonicalAST`)**.

We convert the surface AST into a `CanonicalAST` by alpha-converting formal parameters and local bindings into deterministic De Bruijn slots (`@T.0`, `@T.1`), sorting record fields and effect atoms lexicographically, mapping external references to content hashes, and computing $\text{DefHash} = \text{SHA-256}(\text{CanonicalCBOR})$. Human variable names are preserved in sidecar metadata (`module.kantd`).

### Positive Consequences
- Changing variable names in `.kant` source does not alter `DefHash`, eliminating spurious cache misses.
- Recursive functions are normalized via `@self`, making identity invariant to top-level renames.
- The compilation pipeline can precisely determine the blast radius of modifications.

### Negative Consequences
- Compiler error messages must maintain a bidirectional mapping to project De Bruijn indices back to original human identifiers.
- Slight serialization overhead during canonicalization pass.

---

## Pros and Cons of Options

### Option 1: Surface AST Serialization with Lexical Stripping
* *Pros:* Very simple to implement; directly operates on the surface token stream.
* *Cons:* Renaming a local variable `foo` to `bar` produces a completely different hash; fails the semantic invariance requirement.

### Option 2: De Bruijn Index Slot Conversion (Selected)
* *Pros:* 
  - Complete alpha-equivalence invariance.
  - Standardized, deterministic normalization rules (C1–C5).
  - Decouples visual projection from semantic content.
* *Cons:* Requires maintaining the sidecar map (`module.kantd`) to reconstitute friendly diagnostics.

### Option 3: Hash-Consed Graph Database
* *Pros:* Eliminates files entirely; extreme code deduplication.
* *Cons:* Incompatible with standard git version control, text editors, and conventional developer tooling; high engineering complexity for MVP v0.1.

---

## Validation

The canonicalization algorithm is validated through the `kant-canonical` test suite:
- **Test Alpha-Invariance:** 10 variations of a function with varying variable names, docstrings, and whitespace must evaluate to the identical 32-byte `DefHash`.
- **Test Sensitivity:** Altering a single operator (`+` to `-`) or changing a type annotation must produce an entirely distinct `DefHash`.
