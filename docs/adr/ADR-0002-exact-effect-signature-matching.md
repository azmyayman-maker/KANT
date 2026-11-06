# ADR-0002: Exact Algebraic Effect Signature Matching ($E_{\text{decl}} = E_{\text{inf}}$)

* **Status:** Accepted
* **Deciders:** Kant Architecture Working Group, Epistemic Core Architects
* **Date:** 2026-11-06
* **Technical Subsystem:** `crates/kant-effects`
* **Related Invariant:** Invariant $I_2$ (Exact Effect Matching / The Sigil Law)

---

## Context & Problem Statement

Most modern effect systems (such as Koka, Eff, or Frank) and capability systems rely on subtyping or effect subsumption: if a function $f$ requires effects $\{E_1\}$, it is permitted to be declared with $\{E_1, E_2\}$, or pure functions are silently coerced into effectful contexts without notation. 

In agent-driven development, empirical studies (SIGIL, arXiv:2607.27309) reveal that effect subsumption leads to "effect rot" and ambient permission creep: AI models over-declare capabilities (e.g. declaring `fs.write` "just in case"), or callers lose visibility into whether a sub-routine actually interacts with the Noumenon.

How can `kantc` guarantee that function effect signatures reflect reality with 100% precision without manual developer friction?

---

## Decision Drivers

1. **Epistemic Honesty:** What is declared in code must mirror exact operational execution.
2. **Blast Radius Predictability:** Refactoring must not hide transitive side effects.
3. **Automated Machine Repair:** Compiler errors regarding effect mismatches must be safely and deterministically auto-fixable by AI agents.
4. **Zero Ambient Coercion:** Pure functions must remain provably pure.

---

## Considered Options

* **Option 1: Traditional Subsumptive Effect Polymorphism (Subtyping $E_{\text{inf}} \subseteq E_{\text{decl}}$)**
* **Option 2: Exact Set Equality Matching ($E_{\text{decl}} = E_{\text{inf}}$) with RFC 6902 Auto-Fixes**
* **Option 3: Implicit Effect Inference without Explicit Source Annotations**

---

## Decision Outcome

**Chosen Option:** **Option 2: Exact Set Equality Matching ($E_{\text{decl}} = E_{\text{inf}}$) with RFC 6902 Auto-Fixes**.

Every function declaration must specify an effect set that matches the inferred effect set bit-for-bit:
$$E_{\text{decl}}(f) = E_{\text{inf}}(f)$$

If an undeclared effect is performed, the compiler halts with `KANT-E301`. If a declared effect is never performed, the compiler halts with `KANT-E302`. In both scenarios, the compiler emits a machine-readable RFC 6902 JSON patch with `FixSafety: SAFE`, allowing agents to run `kantc fix --apply` for immediate repair.

### Positive Consequences
- Zero capability creep or unexercised privilege declarations.
- AI agents cannot hallucinate or silently accumulate dangerous permissions.
- Effect sets serve as verifiable contracts.

### Negative Consequences
- Developers or agents writing code manually must update effect annotations when adding effectful sub-calls (mitigated by automated quick-fix tooling).

---

## Pros and Cons of Options

### Option 1: Subsumptive Effect Polymorphism
* *Pros:* Familiar from traditional academic type systems; less noisy during initial drafting.
* *Cons:* Encourages permission inflation; creates stale signatures; weakens auditability.

### Option 2: Exact Set Equality Matching (Selected)
* *Pros:*
  - Strict mathematical guarantees.
  - Zero permission drift.
  - Deterministic auto-repair path via RFC 6902 patches.
* *Cons:* Requires automated tooling to prevent repetitive manual edits.

### Option 3: Implicit Inference without Annotations
* *Pros:* Zero developer annotation burden.
* *Cons:* Invisible breaking changes; modifying an internal leaf function silently alters the effect type of all upstream callers.

---

## Validation

Validated via `kant-effects` test harness:
- Test case with missing effect triggers `KANT-E301` and generates valid RFC 6902 patch.
- Test case with superfluous effect triggers `KANT-E302` and generates valid cleanup patch.
- Applying the generated JSON patch resolves compilation cleanly.
