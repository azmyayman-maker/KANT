# Synthetic Multi-Agent Coordination Protocol

## 1. Principles of Synthetic Multi-Agent Software Engineering

The development of the Kant programming language compiler toolchain (`kantc`) employs a coordinated synthetic multi-agent architecture. Autonomous AI agents collaborate simultaneously across the codebase under formal structural constraints.

To eliminate race conditions, merge conflicts, and epistemic drift, the protocol enforces four core principles:
1. **Strict Spatial Confinement (Lane Isolation):** Each agent is assigned an exclusive write-allowlist directory lane. Modifying files outside your assigned lane triggers immediate commit rejection.
2. **Pipelined Wave Progression:** Agents operate in sequenced chronological waves. Upstream dependencies are consumed in a read-only state.
3. **The Iron Law of Verification:** No agent may declare a task complete without executing the Five-Step Verification Harness and attaching raw terminal outputs to their milestone report.
4. **Deterministic Auditability:** Every commit is validated by automated hooks and logged to the central telemetry tracker (`scripts/kant_tracker_sync.py`).

---

## 2. The 16 Isolated Sub-Agent Lanes (SA-01 to SA-16)

```
crates/
├── kant-core/          [SA-01: Epistemic & Workspace Bootstrapper]
├── kant-lexer/         [SA-02: Transcendental Aesthetic Lexer]
├── kant-parser/        [SA-03: Flattened Pratt & LL(1) Parser]
├── kant-canonical/     [SA-04: Spatial Canonicalizer & Sidecar Engine]
├── kant-types/         [SA-05: 12-Categories Type Checker]
├── kant-effects/       [SA-06: Exact Effect & Quarantine Analyzer]
├── kant-ir/            [SA-07: Al-Shaym SSA IR Lowering Engine]
├── kant-perceus/       [SA-08: Perceus Memory & Reuse Pass]
├── kant-paralogism/    [SA-09: Paralogism Ownership & Taint Guard]
├── kant-antinomy/      [SA-10: Antinomy Contract & Termination Verifier]
├── kant-noumena/       [SA-11: Noumena Capability & Governor Runtime]
├── kant-spec/          [SA-12: Amthoul Spec & Graph Extractor]
├── kant-eval/          [SA-13: Reference KANT-IR Evaluator & Merkle Trace]
├── kant-codegen/       [SA-14: Cranelift JIT & Native AOT Backend]
├── kant-diag/          [SA-15: Structured Diagnostics & Auto-Fix Engine]
├── kant-cli/           [SA-16: Unified CLI Driver (kantc)]
└── kant-mcp/           [SA-16: Model Context Protocol Server]
```

### 2.1. Sub-Agent Allocation & Wave Matrix

| Agent ID | Role / Domain | Exclusive Write Lane | Read-Only Upstream Dependencies | Wave |
| :--- | :--- | :--- | :--- | :--- |
| **SA-01** | Epistemic Bootstrapper | `crates/kant-core/` | Spec Docs, Root Manifest | **Wave 1** |
| **SA-02** | Aesthetic Lexer | `crates/kant-lexer/` | `kant-core` | **Wave 1** |
| **SA-03** | Pratt & LL(1) Parser | `crates/kant-parser/` | `kant-core`, `kant-lexer` | **Wave 1** |
| **SA-04** | Spatial Canonicalizer | `crates/kant-canonical/` | `kant-core`, `kant-parser` | **Wave 1** |
| **SA-05** | 12-Categories Type Checker | `crates/kant-types/` | `kant-core`, `kant-canonical` | **Wave 2** |
| **SA-06** | Exact Effect Analyzer | `crates/kant-effects/` | `kant-core`, `kant-canonical`, `kant-types` | **Wave 2** |
| **SA-07** | SSA IR Lowering Engine | `crates/kant-ir/` | `kant-types`, `kant-effects` | **Wave 2** |
| **SA-08** | Perceus Memory Pass | `crates/kant-perceus/` | `kant-ir` | **Wave 2** |
| **SA-09** | Paralogism Guard | `crates/kant-paralogism/`| `kant-ir`, `kant-types` | **Wave 3** |
| **SA-10** | Antinomy SMT Verifier | `crates/kant-antinomy/`  | `kant-ir`, `kant-types` | **Wave 3** |
| **SA-11** | Noumena Sandbox Runtime| `crates/kant-noumena/`   | `kant-effects`, `kant-ir` | **Wave 3** |
| **SA-12** | Spec & Graph Extractor | `crates/kant-spec/`      | `kant-types`, `kant-effects` | **Wave 3** |
| **SA-13** | Evaluator & Merkle Trace| `crates/kant-eval/`      | `kant-ir`, `kant-noumena`, `kant-perceus` | **Wave 4** |
| **SA-14** | Cranelift Codegen Backend| `crates/kant-codegen/` | `kant-ir`, `kant-eval` | **Wave 4** |
| **SA-15** | Structured Diagnostics | `crates/kant-diag/`      | `kant-canonical` .. `kant-antinomy` | **Wave 4** |
| **SA-16** | Unified CLI & MCP Daemon| `crates/kant-cli/`, `kant-mcp/` | All Crates | **Wave 4** |

---

## 3. Write-Allowlist Rules & Collision Prevention

To maintain branch hygiene and prevent multi-agent merge deadlocks:
1. **Zero-Code Invariant [Z0]:** Architectural and documentation agents (such as `sa_docs_systems_architect`) must NEVER modify compiler implementation code in `crates/*/src/`.
2. **Lane Boundary Check:** Git commit hooks inspect modified file paths against the agent's assigned lane. Modifying files outside your assigned prefix (e.g. `docs/` for Docs Architect) triggers a hook failure.
3. **Isolated Git Branches:** Every agent operates on an isolated feature branch named according to its role:
   ```
   feat/docs-systems-architecture
   feat/sa-01-kant-core
   feat/sa-02-kant-lexer
   ```

---

## 4. Conventional Commits & Telemetry Integration

All commits across all agents must strictly conform to the **Conventional Commits 1.0.0** specification.

### 4.1. Permitted Types & Scopes
- **Types:** `docs`, `feat`, `fix`, `refactor`, `chore`, `test`.
- **Scopes:** Matching crate names (`core`, `lexer`, `parser`, `types`, `effects`, `ir`, `perceus`, `codegen`, `diag`, `cli`) or system domains (`architecture`, `adr`, `guides`, `reports`, `workspace`).
- **Subject Length:** Maximum 100 characters per subject line.

### 4.2. Commit Examples
```
docs(architecture): author deep systems architecture documents 01 to 05
docs(adr): establish MADR decision records repository ADR-0001 to ADR-0008
refactor(workspace): establish pristine zero-state scaffolding and portal isolation
```

### 4.3. Automated Telemetry Logging
Upon every successful commit, the local git hook executes `scripts/kant_tracker_sync.py`, recording:
- Commit SHA and author identity.
- Modified files and line insertions/deletions.
- Milestone advancement markers visible on the local roadmap observatory.
