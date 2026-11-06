# 05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md: Transcendental Dialectic, Verification & Noumena

In the *Critique of Pure Reason*, the **Transcendental Dialectic** is Kant's "Logic of Illusion" (*Logik des Scheins*). It exposes and dismantles the dialectical fallacies that inevitably arise when Pure Reason oversteps the boundaries of sensible experience to speculate on the unconditioned (*Noumena*, the Soul, the Cosmos, God).

In `kantc`, the Dialectic acts as the **Epistemological Security Firewall**, comprising three subsystems:
1. **The Paralogism Guard:** Eliminates aliasing, capability cloning, and side-channel secret leaks.
2. **The Antinomy Verifier:** Enforces loop/recursion termination and 3-tier contract proofs.
3. **The Noumena Boundary:** Enforces default `trust none` and linear capability access to the outside world.

---

## 1. The Paralogism Guard: Affine Ownership & Secret Taint

Kantian paralogisms are errors of substantiality and misattributed identity. In software, these manifest as data races, use-after-free, double-spending of capabilities, and timing side-channels.

### 1.1. Linear / Affine Ownership for Capabilities
Unlike normal values (which are managed automatically by Perceus), **Capability Tokens** (`CapToken`) obey an affine ownership discipline:
* **State Space:** `Available` $\to$ `Moved` (consumed).
* A capability cannot be cloned, copied, or stored in global mutable memory.
* Passing a capability token transfers ownership. Calling an operation on a consumed capability yields error `KANT-E401` (Capability Use-After-Move).

### 1.2. Constant-Time & Secret Taint Analysis
To eliminate cryptographic and API key leakage:
* Types wrapped in `Secret<T>` (e.g., `Secret<String>` for an API token or private key) are tracked via static taint analysis.
* **Invariant T1 (No Secret-Dependent Branches):** `if secret_val { ... }` triggers `KANT-E405` (Secret Branch Leak).
* **Invariant T2 (No Secret-Dependent Memory Indices):** `buffer[secret_val]` triggers `KANT-E406` (Secret Cache Side-Channel).
* **Zeroize-on-Drop:** Memory holding `Secret<T>` is overwritten with cryptographic zeros immediately upon drop.

---

## 2. The Antinomy Verifier: Contracts & Termination

Antinomies occur when reason can prove both a proposition and its contradiction due to an infinite, ungrounded regression. In computing, an antinomy is an **infinite loop**, a **non-terminating recursive cycle**, or a **deadlock**.

### 2.1. The 3-Tier Verification Architecture (Vera Pattern)
Kant adopts a pragmatic 3-tier verification pipeline to guarantee progress without being paralyzed by SMT timeouts:

```
                    ┌─────────────────────────┐
                    │ Contract: requires /    │
                    │         ensures         │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       [Simple Arithmetic]             [Complex Induction]
                 │                               │
                 ▼                               ▼
        ┌──────────────────┐            ┌──────────────────┐
        │ Tier 1: Internal │            │ Tier 1: Z3 SMT   │
        │ Simplifier / SMT │            │ (10s Budget)     │
        └────────┬─────────┘            └────────┬─────────┘
                 │ Proved                        │ Proved
                 ├───────────────────────────────┤
                 ▼                               │ Timeout / Unproven
        ┌──────────────────┐                     ▼
        │ Static Guarantee │            ┌──────────────────┐
        │ (Zero Overhead)  │            │ Tier 3: Runtime  │
        └──────────────────┘            │ Fallback Guard   │
                                        └──────────────────┘
```

1. **Tier 1 (Static SMT):** Evaluates arithmetic bounds and algebraic equations using a built-in interval simplifier and an optional Z3 SMT solver session (with a configurable 10-second timeout).
2. **Tier 2 (Agent Proof Hints):** In the event of an unproved theorem, the compiler surfaces the unproved goal as an explicit JSON diagnostic, allowing the agent to provide intermediate lemmas.
3. **Tier 3 (Runtime Fallback Guard):** If Tier 1 cannot prove a contract statically within budget, the compiler lowers the contract into a lightweight, compiled runtime check (`assert!`) accompanied by a proof-reconciliation record.

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
If a recursive function lacks a verified `decreases` clause, compilation fails with `KANT-E501` unless the function explicitly includes the `<diverge>` effect in its contract.

---

## 3. The Noumena Boundary & Capability Governance

In Kant's philosophy, reason cannot transcend experience to grasp the "Thing-in-itself" (*Noumenon*). In `kantc`, the external world (OS system calls, disk I/O, network sockets, external AI models) is the Noumenon.

### 3.1. Default Epistemic Posture: `trust none`
* Every `.kant` file has `trust none` enabled by default.
* Raw system calls and unmediated ambient authority are strictly prohibited.

### 3.2. Session-Governor-Executor Pattern
To execute an effect that crosses into the Noumenon:
1. **The Capability Token:** The caller must hold an unforgeable, zero-sized capability token (e.g., `NetCap`, `FsCap`, `AiCap`) created exclusively in the root entrypoint (`main`).
2. **The Governor Handler:** Effectful operations must run within the scope of an enclosing `handle { ... } with governor { ... }` block.
3. **Human Approval Gates:** High-risk operations (e.g., writing to sensitive file paths, committing financial transactions, or issuing untrusted external prompts) can invoke `approval_gate(policy)`, suspending execution until a cryptographically signed approval token is provided via the CLI or IDE.
