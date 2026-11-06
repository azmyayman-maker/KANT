# Security Policy for Kant (`kantc`)

The Kant compiler architecture is engineered for high-assurance, safety-critical systems.
This document details our threat model, security guarantees, and the vulnerability disclosure process.

---

## 1. Security Architecture & Threat Model

Kant operates under a zero-trust model (*trust none*) designed to safeguard both developer systems
and compiled artifacts against memory vulnerabilities, untrusted execution escapes, and supply-chain tampering.

### Threat Model Boundaries
1. **Sandboxed Compiler Execution:** The `kantc` compiler, when analyzing and executing compile-time
   evaluations (const expressions, amthoul specs, and type-level checking), operates within a strictly
   sandboxed virtual runtime (`crates/kant-eval/`) that prevents arbitrary host filesystem or network access.
2. **Noumena Capability Tokens:** All runtime side-effects (I/O, network sockets, clock access, subprocess
   spawning) are mediated by explicit, linear, non-forgeable capability tokens (`crates/kant-noumena/`).
   No capability may be synthesized out of void; capabilities can only be passed down from entry points.
3. **Deterministic Reproducibility:** Every build artifact is pinned by content-addressed definition
   hashes (`DefHash`) and reproducible lockfiles (`module.kant.lock`). Compiler outputs are bit-for-bit
   deterministic across identical toolchain releases.

---

## 2. Scope of Security Guarantees

| Subsystem | Security Guarantee | Assurance Mechanism |
| :--- | :--- | :--- |
| **Lexer & Parser** | Absolute memory safety on arbitrary adversarial inputs | Pure Rust, zero unsafe blocks, continuous AFL/libFuzzer fuzzing |
| **Perceus Runtime** | Cycle safety and zero memory leaks | Static drop-guided reference counting with antinomy cycle detection |
| **Effect & Capability Engine** | Zero ambient authority and escalation prevention | Static affine type verification ($E_{\text{decl}} = E_{\text{inf}}$) |
| **Code Generation** | Control flow integrity and memory bounds | Cranelift backend with deterministic runtime fault trapping |

### Out-of-Scope Vulnerabilities
- Attacks requiring physical access or root privileges on the compilation host.
- Denial of Service due to computationally bounded termination checks (guarded by timeout bounds).
- Non-conforming third-party unsafe extensions that deliberately violate Rust FFI contracts.

---

## 3. Reporting a Vulnerability

We deeply appreciate the efforts of the security research community in identifying potential flaws.
If you discover a security vulnerability in Kant or `kantc`, please report it responsibly.

### Reporting Procedure
**DO NOT file a public GitHub issue.** Instead, email our security team directly:
* **Email:** `security@kant-lang.org`
* **Alternate:** `admin@kant-lang.org`
* **PGP Key:** Security team PGP key available upon request or via keyserver fingerprint:
  `KANT-SEC-KEY-2026-F61D-9B8A`

Please include in your report:
1. Clear description of the vulnerability and its potential impact.
2. Minimal reproduction steps, including sample `.kant` code and compiler invocation flags.
3. Affected versions of `kantc` and host architecture.
4. Any proposed patches or mitigations.

### Disclosure Policy & Response Timeline
- **Initial Acknowledgment:** Within 48 hours of receipt.
- **Triage & Reproduction:** Within 7 calendar days.
- **Fix & Advisory Release:** We aim to release security patches within 30 days of confirmed reproduction.
- **Responsible Disclosure Window:** We request a 90-day embargo before public disclosure to allow
  users and downstream integrations to deploy mitigations.
- Security advisories are published via GitHub Security Advisories and the RustSec database.
