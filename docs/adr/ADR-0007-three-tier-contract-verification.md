# ADR-0007: Three-Tier Contract Verification Pipeline (Vera Pattern)

* **Status:** Accepted
* **Deciders:** Kant Architecture Working Group, Formal Verification Architects
* **Date:** 2026-11-06
* **Technical Subsystem:** `crates/kant-antinomy`
* **Related Invariant:** Milestone MVP v0.1 Contract Verifier (Q17)

---

## Context & Problem Statement

Formal verification using Satisfiability Modulo Theories (SMT) solvers (like Z3 or CVC5) is powerful for proving arithmetic bounds, invariants, and termination metrics. However, SMT solvers are susceptible to:
1. Non-linear arithmetic intractability (undecidability).
2. Solver timeouts on complex inductive goals.
3. Brittle proof failures that completely halt compiler builds, frustrating developer and AI agent momentum.

How can `kantc` offer uncompromising formal guarantees where solvable while providing a pragmatic, non-blocking pipeline for complex invariants?

---

## Decision Drivers

1. **Safety Guarantee:** Proved contracts must incur zero runtime overhead.
2. **Predictable Compile Time:** Solvers must not hang indefinitely during compilation.
3. **Non-Blocking Development:** Unsolvable or complex inductive properties must not abort compilation if safe fallback checks can be compiled.
4. **Agent Collaboration:** Unproved lemmas should be emitted as structured hints for AI agents to supply intermediate lemmas.

---

## Considered Options

* **Option 1: Pure Static SMT Verification Only (Dafny/F* model: compile error on any unproved contract)**
* **Option 2: Pure Runtime Assertions Only (Eiffel/Contracts model: contracts compiled directly to `assert!`)**
* **Option 3: Three-Tier Pragmatic Verification Pipeline (The Vera Pattern)**

---

## Decision Outcome

**Chosen Option:** **Option 3: Three-Tier Pragmatic Verification Pipeline (The Vera Pattern)**.

`kant-antinomy` executes verification across three distinct tiers:
- **Tier 1 (Static SMT):** Evaluates arithmetic bounds and linear equations using an internal interval simplifier and an optional Z3 SMT session with a hard 10-second timeout budget. If proved, contracts are verified statically with zero runtime cost.
- **Tier 2 (Agent Proof Hints):** If an invariant cannot be proved automatically within budget, the compiler emits an informative diagnostic (`KANT-W502`) detailing the unproved goal, allowing AI agents to supply intermediate `proof` assertions or lemmas.
- **Tier 3 (Runtime Fallback Guard):** If the invariant remains unproved at build time, the compiler compiles the contract into a lightweight, instrumented runtime check (`assert!`) and logs an audit marker in the binary's evidence manifest.

### Positive Consequences
- Zero runtime overhead for the majority of solvable contracts.
- Immune to SMT solver timeouts and compilation hangs.
- Continuous development progress without sacrificing soundness or safety.

### Negative Consequences
- Programs relying on Tier 3 fallbacks incur a minor runtime evaluation cost for those specific assertions.

---

## Pros and Cons of Options

### Option 1: Pure Static SMT
* *Pros:* 100% static guarantees; zero runtime checks.
* *Cons:* Brittle; SMT timeouts halt builds; difficult for automated agents without expert theorem proving.

### Option 2: Pure Runtime Assertions
* *Pros:* Simple to implement; no SMT solver required.
* *Cons:* Runtime performance degradation; errors caught only when specific code paths execute.

### Option 3: Three-Tier Verification (Selected)
* *Pros:*
  - Best of both worlds: static optimization when provable, runtime safety fallback when undecidable.
  - SMT budget bounded to 10 seconds.
  - Native integration with agent hints.
* *Cons:* Requires managing both SMT goal translation and runtime assert lowering.

---

## Validation

Validated via `kant-antinomy` test suite:
- Simple linear contracts (`requires x > 0`, `ensures ret > x`) proved statically by Tier 1; 0 instructions emitted in native codegen.
- Intentionally complex non-linear modulo constraints successfully fall back to Tier 3 runtime guards with verifiable assertion failures on invalid inputs.
