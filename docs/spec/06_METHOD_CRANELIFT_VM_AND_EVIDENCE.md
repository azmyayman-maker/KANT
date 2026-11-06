# 06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md: Doctrine of Method, Cranelift Codegen & Merkle Bundles

The **Transcendental Doctrine of Method** (*Transzendentale Methodenlehre*) is the final division of the *Critique of Pure Reason*. Having analyzed the elements of pure reason, Kant specifies the formal conditions for erecting a complete, disciplined, and reliable scientific system.

In `kantc`, the Doctrine of Method realizes this through the **Dual Execution Engine**, **Differential Verification**, and **Merkle Evidence Bundles**.

---

## 1. Dual Execution Engine Architecture

Kant provides two complementary execution backends for KANT-IR:

```
                            ┌────────────────┐
                            │    KANT-IR     │
                            │ (SSA & Perceus)│
                            └───────┬────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 ▼                                     ▼
      ┌──────────────────────┐              ┌──────────────────────┐
      │  Reference KANT-IR   │              │    Cranelift JIT     │
      │      Evaluator       │              │   & Native AOT       │
      │  (`kantc run --eval`)│              │   (`kantc build`)    │
      └──────────┬───────────┘              └──────────┬───────────┘
                 │                                     │
                 │              Differential           │
                 └────────────── Verification ─────────┘
                                       │
                                       ▼
                             ┌──────────────────┐
                             │ Byte & Semantic  │
                             │  Identity Proof  │
                             └──────────────────┘
```

### 1.1. Reference KANT-IR Evaluator (`kant-eval`)
* A pure, deterministic SSA interpreter written in safe Rust.
* Directly interprets the 30 KANT-IR opcodes.
* Maintains an explicit execution trace, step counters, and virtualized Noumena handlers.
* Serves as the primary behavioral oracle for debugging and agent simulation.

### 1.2. Cranelift JIT & Native AOT Backend (`kant-codegen`)
* Translates KANT-IR basic blocks directly into Cranelift IR (CLIF).
* Leverages Cranelift's lightning-fast code generation (~2.6 ms per function, ~4x faster compilation than LLVM).
* Supports **JIT Mode** (`kantc run`) for instant developer iterations and **AOT Mode** (`kantc build`) producing standalone, zero-dependency static binaries for x86-64 and ARM64.

---

## 2. Differential Testing & Determinism Proofs

To guarantee that compiler optimizations and native lowering introduce zero semantic drift:

1. **The Conformance Harness:** A suite of 50 foundational test programs covering all 12 categories, recursive functions, Perceus in-place updates, and algebraic handlers is run simultaneously against both engines.
2. **Acceptance Invariant:** The terminal output, exit status, and memory mutation trace of the Cranelift binary must match the Reference Evaluator byte-for-byte:
   $$\text{Trace}(\text{Cranelift}(P)) \equiv \text{Trace}(\text{Evaluator}(P))$$
3. **Byte-Identical Builds:** Compiling a `.kant` file with identical dependency lockfiles on two independent machines must produce bit-for-bit identical native binaries (`0 byte mismatches`), establishing a reproducible chain of custody.

---

## 3. Hash-Chained Merkle Evidence Bundles (The Boruna Model)

Every mission-critical agentic workflow requires tamper-evident auditing. When a `.kant` program executes, particularly when interacting with the Noumenon, it generates an append-only JSON Lines evidence log: `module.kant.evidence.jsonl`.

### Structure of an Evidence Block
```json
{
  "sequence_id": 104,
  "prev_block_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "block_hash": "a82f9c43b0e271427189f381d643d922bc942b039498e85496a7824ee182e043",
  "timestamp_utc": "2026-11-06T14:12:00Z",
  "epistemic_stage": "dialectic.noumena",
  "action": "net.http.request",
  "capability_id": "Cap_0x8f2a",
  "request_payload_digest": "4a5e...",
  "response_payload_digest": "9b1c...",
  "human_approval_signature": "sig_ed25519_...",
  "merkle_root": "7f81..."
}
```

### Deterministic Replay Engine (`kantc replay`)
Using `kantc replay --evidence module.kant.evidence.jsonl`:
* The compiler boots in replay mode.
* When code encounters a Noumena call (e.g., `net.http` or `ai.infer`), the engine validates the cryptographic hash chain and injects the recorded output without calling the real external network.
* Enables offline regression testing and absolute verification of agent actions.
