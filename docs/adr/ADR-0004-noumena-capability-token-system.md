# ADR-0004: Noumena Affine Capability Token Security System

* **Status:** Accepted
* **Deciders:** Kant Architecture Working Group, Security Architects
* **Date:** 2026-11-06
* **Technical Subsystem:** `crates/kant-noumena`, `crates/kant-paralogism`
* **Related Invariant:** Invariant $I_4$ (Noumena Zero-Escape Boundary / `trust none`)

---

## Context & Problem Statement

Autonomous AI agents executing generated code pose severe security risks when operating with ambient system authority:
- Accidental filesystem wipes or data exfiltration.
- Unconstrained outbound HTTP calls to untrusted external endpoints.
- Inability to enforce least-privilege sandboxing at runtime without heavy container overhead.

Traditional OS permissions and ambient language primitives (such as Python's `open()` or Node's `fs`) provide zero compile-time isolation. How can `kantc` structurally guarantee that unverified code cannot access the external world (the Noumenon) without explicit, auditable, and unforgeable authorization?

---

## Decision Drivers

1. **Default Posture:** Default execution environment must enforce `trust none`.
2. **Unforgeability:** Authorization handles must not be forgeable, duplicable, or synthesizable from arbitrary integer/string literals.
3. **Auditability:** Every privileged interaction must be cryptographically logged to an append-only Merkle trail.
4. **Human Oversight:** High-risk actions must support synchronous suspension for interactive human approval.

---

## Considered Options

* **Option 1: Traditional Ambient Authority with OS Containerization (Docker/cgroups)**
* **Option 2: Path/Domain String Access Control Lists (ACLs) checked at runtime**
* **Option 3: Affine Linear Capability Tokens (`CapToken`) Governed by Algebraic Handlers**

---

## Decision Outcome

**Chosen Option:** **Option 3: Affine Linear Capability Tokens (`CapToken`) Governed by Algebraic Handlers**.

All interaction with the Noumenon requires an affine (move-only) capability token (`cap &Cap`). Tokens are minted exclusively at the program entrypoint (`main`) and cannot be copied. Passing a token transfers ownership; attempting to reuse a consumed token fails compilation with `KANT-E401`. Furthermore, capabilities are executed inside `handle ... with governor` blocks, allowing attenuation and interactive `approval_gate` checkpoints.

### Positive Consequences
- Static mathematical proof of zero ambient authority breaches.
- Fine-grained capability attenuation (`cap.attenuate_subpath("/tmp")`).
- Safe execution of autonomous AI agent scripts without container spin-up overhead.

### Negative Consequences
- Root functions must explicitly thread capability tokens to subroutines requiring external IO.

---

## Pros and Cons of Options

### Option 1: Ambient Authority with OS Containers
* *Pros:* Familiar standard libraries; no language changes.
* *Cons:* Heavy resource footprint; zero compile-time verification; vulnerable to container breakout bugs.

### Option 2: Runtime String ACLs
* *Pros:* Flexible configuration at runtime.
* *Cons:* Fragile path parsing and canonicalization bypasses (symlinks, path traversal); failures occur only at runtime.

### Option 3: Affine Capability Tokens (Selected)
* *Pros:*
  - Zero-cost compile-time verification.
  - Impossibility of ambient privilege escalation.
  - Direct integration with algebraic effect governors.
* *Cons:* Requires capability threading in function parameter lists.

---

## Validation

Validated via `kant-noumena` and `kant-paralogism` tests:
- Attempting to invoke `fs.read` without `FsCap` in scope triggers `KANT-E701`.
- Moving a capability into a helper and calling it again triggers `KANT-E401`.
- Capabilities attenuated to subpaths successfully reject out-of-boundary access.
