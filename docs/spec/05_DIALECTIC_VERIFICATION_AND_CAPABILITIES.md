# 05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md: Transcendental Dialectic: 3-Tier Contract Verification, SMT Bridge & Noumena Security

The **Transcendental Dialectic** formalizes the formal verification engine, capability security subsystem, and sandbox isolation boundaries of `kantc`. It comprises three core architectural subsystems:
1. **The Paralogism Guard (`kant-paralogism`):** Enforces affine ownership over capability tokens and prevents side-channel secret information leaks.
2. **The Antinomy Verifier (`kant-antinomy`):** Proves recursive function termination and verifies contract pre-/post-conditions via a 3-tier verification pipeline.
3. **The Noumena Boundary (`kant-noumena`):** Implements default `trust none` sandbox isolation, governing external interactions through unforgeable linear capabilities.

---

## 1. The Paralogism Guard: Affine Ownership & Secret Taint Analysis

Software paralogisms are errors of misattributed state, aliasing violations, capability cloning, and timing side-channels.

### 1.1. Linear / Affine Ownership for Capability Handles
Unlike standard values (which are managed automatically via Perceus reference counting), **Capability Tokens** (`CapToken`) strictly follow an affine ownership discipline:
* **State Transition:** $\text{Available} \xrightarrow{\text{use}} \text{Moved}$.
* **No Cloning or Duplication:** Capability tokens cannot be duplicated, copied, or stored in ambient global heaps.
* **Affine Move Semantics:** Passing a capability token transfers ownership. Invocations on consumed capability variables trigger compile-time error `KANT-E401` (Capability Use-After-Move).

### 1.2. Constant-Time Analysis & Secret Taint Guard
To prevent side-channel timing attacks and sensitive credential leakage:
* Types wrapped in `Secret<T>` (e.g., cryptographic keys, access tokens) are subjected to static taint tracking.
* **Invariant T1 (No Secret-Dependent Branches):** Using a `Secret<T>` in a control-flow condition (`if secret { ... }`) triggers error `KANT-E405` (Secret Branch Leak).
* **Invariant T2 (No Secret-Dependent Memory Addressing):** Using a `Secret<T>` as an array or buffer index (`buffer[secret]`) triggers error `KANT-E406` (Secret Cache Side-Channel).
* **Cryptographic Zeroization:** Memory allocated for `Secret<T>` values is overwritten with cryptographic zeros immediately upon drop.

---

## 2. The Antinomy Verifier: 3-Tier Contract Verification & Termination

Computational antinomies represent non-terminating regressions, infinite loops, and unsound contract assumptions.

### 2.1. 3-Tier Verification Architecture (The Vera Pattern)

To ensure verifiable guarantees without halting compiler velocity on undecidable theorems, Kant employs a 3-tier verification pipeline:

```
                    ┌─────────────────────────┐
                    │ Contract: requires /    │
                    │         ensures         │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       [Syntactic / Interval]          [Inductive / Relational]
                 │                               │
                 ▼                               ▼
        ┌──────────────────┐            ┌──────────────────┐
        │ Tier 1: Internal │            │ Tier 2: Z3 SMT   │
        │ Simplifier / AST │            │ (10s Budget)     │
        └────────┬─────────┘            └────────┬─────────┘
                 │ Proved                        │ Proved
                 ├───────────────────────────────┤
                 ▼                               │ Timeout / Unproven
        ┌──────────────────┐                     ▼
        │ Static Guarantee │            ┌──────────────────┐
        │ (Zero Overhead)  │            │ Tier 3: Runtime  │
        │                  │            │ Fallback Assert  │
        └──────────────────┘            └──────────────────┘
```

1. **Tier 1 (Syntactic & Interval Simplifier):** Evaluates arithmetic intervals, structural pattern exhaustiveness, and syntactic inequalities within the compiler frontend (`< 1ms`).
2. **Tier 2 (Automated SMT Solving via Z3):** Emits first-order linear arithmetic, bitvector, and uninterpreted function formulas to an external SMT solver (Z3) with a strict 10-second timeout budget. Unproven goals emit structured JSON diagnostics with candidate counterexamples.
3. **Tier 3 (Runtime Fallback Guard):** Contracts that cannot be discharged statically within the SMT budget are lowered into compiled runtime assertions (`assert!`), accompanied by proof-obligation audit records.

### 2.2. Mandatory Termination Proofs (`decreases`)
Every recursive function $f$ must provide a well-founded metric expression:

```kant
pub fn factorial(n: Int64) -> Int64
{
    requires n >= 0
    decreases n
    effects pure
} = {
    if n == 0 { 1 } else { n * factorial(n - 1) }
}
```

If a recursive function lacks a verified `decreases` expression proving strict monotonic descent along a well-founded ordering ($m(args_{k+1}) < m(args_k)$), compilation halts with `KANT-E501` (Unproved Termination Regression) unless the function explicitly declares the `<diverge>` effect.

---

## 3. The Noumena Boundary & Capability Governance

In Kantian epistemology, the understanding cannot transcend sensory experience to access the external world (*Noumena*) without mediation. In `kantc`, external I/O, OS system calls, network interfaces, physical timers, and external LLM APIs constitute the Noumenon.

### 3.1. Default Epistemic Posture: `trust none`
* Every `.kant` compilation unit operates under `trust none` by default.
* Ambient system authority, global file descriptors, and untyped foreign function interfaces (FFI) are strictly prohibited.

### 3.2. Session-Governor-Executor Pattern
To execute an operation across the Noumena boundary:
1. **Unforgeable Capability Tokens:** The caller must hold a linear, zero-sized capability token (`NetCap`, `FsCap`, `AiCap`) constructed exclusively at the system entry point (`main`).
2. **Governor Handlers:** Effectful operations must execute within the dynamic scope of an enclosing `handle ... with governor { ... }` block that reifies, monitors, and audits external calls.
3. **Interactive Approval Gates:** Operations classified under high security policies can invoke `approval_gate(policy)`, which suspends the delimited continuation until a cryptographically signed approval token is provided via the MCP server or CLI driver.
