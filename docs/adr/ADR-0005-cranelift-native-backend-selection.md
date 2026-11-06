# ADR-0005: Cranelift Native Code Generator Selection over LLVM/GCC

* **Status:** Accepted
* **Deciders:** Kant Architecture Working Group, Compiler Backend Engineers
* **Date:** 2026-11-06
* **Technical Subsystem:** `crates/kant-codegen`
* **Related Invariant:** Milestone MVP v0.1 Target Backend (Q25)

---

## Context & Problem Statement

A core goal of the Kant toolchain (`kantc`) is to provide an ultra-responsive, sub-second feedback loop for AI agents. In iterative agent workflows (e.g., prompt -> generate -> check -> fix -> run), compilation latency dominates the agent interaction cycle.
- LLVM provides state-of-the-art global optimizations, but suffers from high compile-time latency (often several seconds per compilation unit) and massive binary dependencies (>500MB C++ toolchain).
- Generating C code and calling GCC/Clang adds external process orchestration overhead and requires a C development environment on host machines.

Which code generation engine should `kantc` adopt for native compilation in v0.1?

---

## Decision Drivers

1. **Compilation Speed:** Must support near-instantaneous JIT compilation (<10 ms per function) to support interactive agent execution loops.
2. **Pure Rust Integration:** Must compile as a pure Rust dependency without requiring complex external C/C++ toolchain installations.
3. **Dual Execution Architecture:** Must support both instant in-memory JIT (`kantc run`) and static native standalone binaries (`kantc build`).
4. **Architecture Support:** Target x86-64 and AArch64 (Apple Silicon / Linux ARM64).

---

## Considered Options

* **Option 1: LLVM C++ Backend via `inkwell` or `llvm-sys`**
* **Option 2: Pure Rust Cranelift Code Generator (`cranelift-codegen`)**
* **Option 3: C Source Transpilation (`kantc -> .c -> gcc/clang`)**

---

## Decision Outcome

**Chosen Option:** **Option 2: Pure Rust Cranelift Code Generator (`cranelift-codegen`)**.

We adopt Cranelift as the native code generator for `kant-codegen`. KANT-IR SSA basic blocks lower directly to Cranelift IR (CLIF). Cranelift provides sub-3ms per function compilation speeds (~4x faster than LLVM), zero non-Rust native library dependencies, and native support for both in-memory JIT execution and ELF/PE/Mach-O static object emission.

### Positive Consequences
- Instant JIT execution via `kantc run` without external build tools.
- Fast, deterministic compilation cycles ideal for autonomous AI agent loops.
- Standalone native binary emission for deployment.
- High memory safety in the compiler backend itself (pure safe Rust).

### Negative Consequences
- Cranelift's peak loop vectorization and floating-point micro-optimizations lag behind LLVM by ~15-20% in raw throughput (acceptable for v0.1; LLVM backend deferred to v1.0).

---

## Pros and Cons of Options

### Option 1: LLVM Backend
* *Pros:* Top-tier peak execution performance and advanced vectorization passes.
* *Cons:* Extreme compile times; heavy memory footprint; cumbersome multi-platform C++ dependency.

### Option 2: Cranelift Backend (Selected)
* *Pros:*
  - Sub-millisecond compilation throughput.
  - Native pure Rust crate ecosystem.
  - Seamless unified JIT and AOT pipeline.
* *Cons:* Slightly lower peak throughput on heavily vectorized numeric micro-benchmarks.

### Option 3: C Transpilation
* *Pros:* Easy to generate C text; leverages host compiler.
* *Cons:* Fragile external toolchain dependency; slow process spawning; non-deterministic C compiler versions.

---

## Validation

Validated via `kant-codegen` benchmark harness:
- Test functions compile to machine code in $< 3.0 \text{ ms}$ on x86-64 and ARM64.
- Bit-identical execution trace confirmed against reference evaluator (`kant-eval`).
