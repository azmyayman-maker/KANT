# ADR-0003: Perceus Reference Counting and Drop-Guided Reuse

* **Status:** Accepted
* **Deciders:** Kant Architecture Working Group, Memory Systems Architects
* **Date:** 2026-11-06
* **Technical Subsystem:** `crates/kant-perceus`
* **Related Invariant:** Invariant $I_3$ (Garbage-Free Deterministic Memory Management)

---

## Context & Problem Statement

High-performance native compilers require memory management strategies that balance developer ergonomics, latency predictability, and throughput. 
- Tracing garbage collection introduces non-deterministic stop-the-world pauses and high memory bloat, making it unsuitable for real-time systems and native agent sandboxes.
- Strict borrow-checking (as in Rust) eliminates GC pauses, but imposes high cognitive burdens and frequent compilation failures on LLMs and autonomous agents due to non-lexical lifetimes and complex borrow semantics.

How should the Kant runtime manage heap allocations deterministically with minimal runtime overhead while remaining friendly to generative AI coding agents?

---

## Decision Drivers

1. **Zero Stop-the-World Latency:** Pauses must be $0.0 \text{ ms}$ for real-time predictable systems execution.
2. **Minimal Memory Footprint:** Memory must be reclaimed immediately at the point of last use.
3. **Agent Synthesis Ergonomics:** Programs must be expressible without complex lifetime parameters or explicit borrow annotations.
4. **Functional Purity with C-Speed Mutation:** Pure immutable updates must compile to destructive in-place buffer mutations when unshared.

---

## Considered Options

* **Option 1: Tracing Garbage Collection (Generational Mark-Sweep or Go-style concurrent collector)**
* **Option 2: Strict Affine Lifetime Borrow Checking (Rust-style borrow checker)**
* **Option 3: Perceus Garbage-Free Reference Counting with Drop-Guided Reuse (`Alloc@reuse`)**

---

## Decision Outcome

**Chosen Option:** **Option 3: Perceus Garbage-Free Reference Counting with Drop-Guided Reuse (`Alloc@reuse`)**.

We adopt the Perceus algorithm (Reinking et al., PLDI 2021). The compiler enforces structural acyclicity at the type level (pointer cycles are forbidden; cyclic networks require `ArenaIdx`). Linear consumption analysis inserts `dup` and `drop` instructions at exact syntactic points. When an allocation follows a drop of a cell with $\text{RC} == 1$, the existing memory buffer is recycled in-place (`AllocReuse`).

### Positive Consequences
- Real-time predictability with zero GC pause times.
- Agents write natural, functional code without managing lifetime bounds (`'a`).
- In-place reuse delivers the performance of imperative C mutations on immutable functional data structures.

### Negative Consequences
- Cyclical graph structures require explicit arena structures rather than raw pointer cycles.
- Small runtime reference count tracking overhead for non-scalar heap objects.

---

## Pros and Cons of Options

### Option 1: Tracing Garbage Collection
* *Pros:* Simple to code; handles circular references automatically.
* *Cons:* Non-deterministic GC pause times; $2\times - 3\times$ memory bloat; incompatible with deterministic evidence logging.

### Option 2: Strict Affine Borrow Checking
* *Pros:* Zero runtime memory management overhead; no ref-count fields.
* *Cons:* Extreme barrier for agent code synthesis; causes >40% compile-repair loops in LLMs due to lifetime errors.

### Option 3: Perceus Reference Counting with Reuse (Selected)
* *Pros:*
  - Zero stop-the-world pauses.
  - Predictable execution latency.
  - In-place buffer reuse eliminates allocation overhead.
  - Ideal balance between agent generative capability and low-level performance.
* *Cons:* Requires discipline around acyclic data structures and arena index design.

---

## Validation

Validated via `kant-perceus` memory benchmarks:
- Tree and list transformations verified to achieve 0 heap allocations when running in a tight loop with $\text{RC} == 1$.
- Address trace confirms pointer reuse across `Cons` cell drops and allocations.
