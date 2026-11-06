# 06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md: Doctrine of Method: Deterministic Tree-Walk VM, Cranelift JIT/AOT & Merkle Evidence Traces

The **Doctrine of Method** formalizes the execution backends, differential verification harness, and cryptographic auditability pipelines of `kantc`. It governs code generation, execution trace equivalence, and reproducible chain-of-custody verification.

---

## 1. Dual Execution Backend Architecture

Kant incorporates two independent execution backends for KANT-IR to guarantee semantic determinism:

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
      │   Tree-Walk VM       │              │     & Native AOT     │
      │  (`kantc run --eval`)│              │   (`kantc build`)    │
      └──────────┬───────────┘              └──────────┬───────────┘
                 │                                     │
                 │              Differential           │
                 └────────────── Verification ─────────┘
                                       │
                                       ▼
                             ┌──────────────────┐
                             │ Byte & Semantic  │
                             │  Trace Identity  │
                             └──────────────────┘
```

### 1.1. Reference SSA Evaluator (`kant-eval`)
* **Deterministic Tree-Walk Interpreter:** Implements direct interpretation over the 30 KANT-IR SSA opcodes in pure, memory-safe Rust.
* **Virtualized Execution Environment:** Simulates memory layout, explicit call frames, gas metering, step counters, and virtualized Noumena handlers without issuing direct host OS system calls.
* **Behavioral Oracle:** Acts as the ground-truth behavioral oracle against which optimizing code generators are validated.

### 1.2. Cranelift JIT & Native AOT Backend (`kant-codegen`)
* **SSA-to-CLIF Lowering:** Translates KANT-IR SSA basic blocks directly into Cranelift Intermediate Format (CLIF), mapping SSA value ids to Cranelift variables.
* **Calling Conventions & ABI:** Complies with platform standard calling conventions (`SystemV` for Linux/macOS, `Windows x64` for Windows).
* **Execution Modes:**
  * **JIT Mode (`kantc run`):** In-memory compilation and immediate execution (~2.6 ms compilation latency).
  * **AOT Mode (`kantc build`):** Generates standalone, zero-dependency static native binaries targeting x86-64 and ARM64.

---

## 2. Differential Testing & Determinism Proofs

To eliminate semantic drift between the reference VM and native code generation passes:

1. **50 Canonical Conformance Test Vectors:** A formal conformance suite spanning all 12 categorical types, recursive functions, Perceus in-place updates, and algebraic effect handlers is executed across both backends.
2. **Execution Trace Equivalence Invariant:** The terminal output, return exit code, and heap mutation trace of the native binary must match the reference VM trace byte-for-byte:
   $$\forall P \in \text{ConformanceSuite}, \quad \text{Trace}(\text{Cranelift}(P)) \equiv \text{Trace}(\text{Evaluator}(P))$$
3. **Bit-Identical Reproducible Builds:** Compiling a `.kant` file with identical dependency lockfiles (`module.kant.lock`) on independent environments yields bit-for-bit identical native machine binaries (`0 byte difference`), certifying end-to-end build reproducibility.

---

## 3. Hash-Chained Merkle Evidence Bundles

When a `.kant` program executes, particularly operations crossing the Noumena boundary, it produces an append-only JSON Lines evidence log: `module.kant.evidence.jsonl`.

### Structure of an Evidence Log Record
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
The execution trace can be audited via `kantc replay --evidence module.kant.evidence.jsonl`:
1. The compiler executes in deterministic replay mode.
2. When execution encounters an external Noumena effect (`net.http`, `ai.infer`), the engine validates the cryptographic hash chain and injects the recorded payload without invoking external network sockets.
3. Guarantees deterministic regression testing and cryptographic auditability for autonomous software workflows.
