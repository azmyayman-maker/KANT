# Kant Compiler Toolchain Documentation Hub

Welcome to the central engineering documentation and architecture repository for the **Kant** (`.kant`) programming language compiler toolchain (`kantc`).

Kant is an epistemologically rigorous, AI-native programming language inspired by Immanuel Kant's *Critique of Pure Reason* (*Kritik der reinen Vernunft*)—specifically through the seminal Arabic translation and conceptual apparatus of Lebanese philosopher **Moussa Wehbe** (Beirut, 1988/1990)—fused with constructive type theory, algebraic effect systems, capability security, and Perceus zero-GC memory management.

---

## 1. Documentation Structure & Map

The documentation hierarchy under `docs/` is organized into six formal subsystems:

```
docs/
├── README.md                      # Master navigation hub (This document)
├── DECISIONS_AND_DEFERRED_ROADMAP.md # The 32 decisions triage & v0.1-v1.0 roadmap
├── architecture/                  # Deep systems architecture treatises
│   ├── 01_COMPILER_PIPELINE.md   # End-to-end AST to Cranelift compilation phases
│   ├── 02_MEMORY_MODEL_PERCEUS.md# Perceus deterministic RC, drop reuse & zero GC
│   ├── 03_TYPE_THEORY_12_CATEGORIES.md # Martin-Löf constructive type theory & 12 categories
│   ├── 04_EFFECT_SYSTEM_QUARANTINE.md  # Exact effect matching & dyn isolation
│   └── 05_NOUMENA_CAPABILITY_MODEL.md  # Linear capability tokens & runtime governor
├── adr/                           # Markdown Architecture Decision Records (MADR format)
│   ├── README.md                  # ADR index, decision matrix & status overview
│   ├── ADR-0001-de-bruijn-ast-canonicalization.md
│   ├── ADR-0002-exact-effect-signature-matching.md
│   ├── ADR-0003-perceus-reference-counting-and-reuse.md
│   ├── ADR-0004-noumena-capability-token-system.md
│   ├── ADR-0005-cranelift-native-backend-selection.md
│   ├── ADR-0006-dual-surface-sidecar-projection.md
│   ├── ADR-0007-three-tier-contract-verification.md
│   └── ADR-0008-rfc-6902-json-structured-diagnostics.md
├── rfcs/                          # Formal Request for Comments pipeline
│   ├── README.md                  # RFC process lifecycle, states & approval gates
│   └── 0000-template.md           # Standard RFC specification template
├── guides/                        # Engineering and contributor onboarding guides
│   ├── DEVELOPER_ONBOARDING.md   # Prerequisites, building, running tests & portal
│   ├── MULTI_AGENT_PROTOCOL.md   # Multi-agent coordination constitution & 16 lanes
│   └── VERIFICATION_HARNESS.md   # The Five-Step Verification Harness execution manual
├── spec/                          # Epistemic foundation & language specifications
│   ├── 01_EPISTEMOLOGY_AND_LEXICON.md
│   ├── 02_AESTHETICS_GRAMMAR_AND_AST.md
│   ├── 03_ANALYTIC_CATEGORIES_AND_EFFECTS.md
│   ├── 04_SCHEMATISM_IR_AND_PERCEUS.md
│   ├── 05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md
│   ├── 06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md
│   └── 07_AGENT_SURFACE_SIDECAR_AND_MCP.md
└── reports/                       # Sub-agent milestone reports & verification evidence
    ├── SA_REPO_PREPARATION_ZERO_STATE_REPORT.md
    └── SA_DOCS_SYSTEMS_ARCHITECT_REPORT.md
```

---

## 2. Reading Pathways by Engineering Role

To navigate the knowledge base effectively according to your engineering specialization:

### Pathway A: Compiler Frontend & AST Engineer
1. Read [`docs/spec/02_AESTHETICS_GRAMMAR_AND_AST.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/spec/02_AESTHETICS_GRAMMAR_AND_AST.md) for flattened EBNF grammar and typed holes.
2. Read [`docs/architecture/01_COMPILER_PIPELINE.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/architecture/01_COMPILER_PIPELINE.md) for the 6-stage transformation flow.
3. Read [`docs/adr/ADR-0001-de-bruijn-ast-canonicalization.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/adr/ADR-0001-de-bruijn-ast-canonicalization.md) for alpha-normalization rules.
4. Read [`docs/adr/ADR-0006-dual-surface-sidecar-projection.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/adr/ADR-0006-dual-surface-sidecar-projection.md) for the ASCII `.kant` vs `.kantd` sidecar contract.

### Pathway B: Type Theorist & Formal Verification Specialist
1. Read [`docs/spec/01_EPISTEMOLOGY_AND_LEXICON.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/spec/01_EPISTEMOLOGY_AND_LEXICON.md) for Martin-Löf constructive type theory mappings.
2. Read [`docs/architecture/03_TYPE_THEORY_12_CATEGORIES.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/architecture/03_TYPE_THEORY_12_CATEGORIES.md) for bidirectional deduction rules and the 12 categorical triads.
3. Read [`docs/architecture/04_EFFECT_SYSTEM_QUARANTINE.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/architecture/04_EFFECT_SYSTEM_QUARANTINE.md) for the Sigil Invariant ($E_{\text{decl}} = E_{\text{inf}}$).
4. Read [`docs/adr/ADR-0007-three-tier-contract-verification.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/adr/ADR-0007-three-tier-contract-verification.md) for the Vera 3-tier SMT verifier.

### Pathway C: Memory, IR & Codegen Backend Hacker
1. Read [`docs/architecture/02_MEMORY_MODEL_PERCEUS.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/architecture/02_MEMORY_MODEL_PERCEUS.md) for Perceus RC, structural acyclicity, and `@r` buffer reuse.
2. Read [`docs/spec/04_SCHEMATISM_IR_AND_PERCEUS.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/spec/04_SCHEMATISM_IR_AND_PERCEUS.md) for the 30 canonical SSA opcodes.
3. Read [`docs/architecture/05_NOUMENA_CAPABILITY_MODEL.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/architecture/05_NOUMENA_CAPABILITY_MODEL.md) for affine capabilities and secret taint zeroization.
4. Read [`docs/adr/ADR-0005-cranelift-native-backend-selection.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/adr/ADR-0005-cranelift-native-backend-selection.md) for Cranelift JIT/AOT code generation.

### Pathway D: AI Agent & Multi-Agent Contributor
1. Read [`docs/guides/MULTI_AGENT_PROTOCOL.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/guides/MULTI_AGENT_PROTOCOL.md) for lane boundaries (SA-01 to SA-16) and commit hygiene.
2. Read [`docs/guides/VERIFICATION_HARNESS.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/guides/VERIFICATION_HARNESS.md) for the mandatory Five-Step Verification Harness.
3. Read [`docs/adr/ADR-0008-rfc-6902-json-structured-diagnostics.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/adr/ADR-0008-rfc-6902-json-structured-diagnostics.md) for structured JSON diagnostics and auto-repair.
4. Read [`docs/spec/07_AGENT_SURFACE_SIDECAR_AND_MCP.md`](file:///C:/Users/AdminOS/.gemini/antigravity/worktrees/1365faf8-e947-4948-a0c3-0ae0daefe8da/subagent-Documentation-Systems-Architect-sa-docs-systems-architect-fb74cb30/docs/spec/07_AGENT_SURFACE_SIDECAR_AND_MCP.md) for the 10 canonical MCP tools.

---

## 3. The 4 Fundamental Compiler Invariants

Every subsystem in `kantc` upholds four non-negotiable architectural invariants:

1. **Invariant $I_1$ (Deterministic Content-Addressing):**
   Every definition's canonical representation has a 32-byte SHA-256 digest (`DefHash`). Renaming local variables, formatting whitespace, or adjusting comments produces 0 hash changes.
2. **Invariant $I_2$ (Exact Effect Matching / The Sigil Law):**
   A function $f$ is well-typed if and only if $E_{\text{decl}}(f) = E_{\text{inf}}(f)$. Undeclared effects (`KANT-E301`) or unused declared effects (`KANT-E302`) trigger compiler halts with RFC 6902 quick-fixes.
3. **Invariant $I_3$ (Garbage-Free Deterministic Memory):**
   Pointer cycles are prohibited by the type system. Memory is reclaimed deterministically via Perceus reference counting and drop-guided in-place reuse without any tracing garbage collector.
4. **Invariant $I_4$ (Noumena Zero-Escape Boundary):**
   Default execution operates under `trust none`. External resources (OS, disk, network, external models) cannot be accessed without an explicit, affine, unforgeable capability token governed by an algebraic handler.
