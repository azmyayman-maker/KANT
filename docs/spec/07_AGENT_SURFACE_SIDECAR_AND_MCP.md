# 07_AGENT_SURFACE_SIDECAR_AND_MCP.md: Agent Surface: RFC 6902 Auto-Fix Diagnostics, Sidecar Engine & Model Context Protocol

The **Agent Surface** formalizes the programmatic machine interfaces of `kantc`. It provides structured compiler diagnostics, RFC 6902 JSON Patch automated repairs, deterministic sidecar reconciliation rules (R1–R6), and a standardized Model Context Protocol (MCP) server daemon for autonomous agents and development environments.

---

## 1. Sidecar Reconciliation Engine (`module.kant.lock`)

The lockfile pins each definition's content-addressed identity (`DefHash`). When an agent or developer updates a source file, the compiler reconciles the modified AST against `module.kant.lock` using six deterministic rules:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   SIDECAR RECONCILIATION RULES (R1–R6)                  │
├──────┬──────────────────────┬──────────────────────────────────────────┤
│ Rule │ Precondition         │ Reconciliation Action                    │
├──────┼──────────────────────┼──────────────────────────────────────────┤
│ R1   │ Name & Hash Match    │ Accept AST without lockfile mutation.    │
│ R2   │ Resolution Collision │ Fatal Error: Name reassigned to another  │
│      │                      │ existing definition (anti-hijack guard). │
│ R3   │ Content Drift        │ Development: Recompute hash and update.  │
│      │                      │ CI (`--frozen`): Fatal Error KANT-E601.  │
│ R4   │ Mechanical Rename    │ Detect invariant hash with updated name; │
│      │                      │ emit SAFE patch updating call sites.     │
│ R5   │ Unresolved Symbol    │ Resolve via upstream index or synthesize │
│      │                      │ typed hole node `?hole`.                 │
│ R6   │ Fresh Definition     │ Compute canonical SHA-256 and append pin.│
└──────┴──────────────────────┴──────────────────────────────────────────┘
```

---

## 2. Structured JSON Diagnostics & RFC 6902 Auto-Fix Patches

Every invocation of `kantc` supports `--json`. Diagnostics are structured according to a formal machine-readable schema:

```json
{
  "$schema": "https://kant-lang.org/schemas/diagnostics-v0.1.json",
  "diagnostics": [
    {
      "code": "KANT-E301",
      "phase": "analytic.effects",
      "severity": "ERROR",
      "span": [142, 178],
      "file": "src/service.kant",
      "message": "Undeclared effect escape: operation invokes 'fs.read' which is not in the declared effect set.",
      "got_effects": ["console.write", "fs.read"],
      "want_effects": ["console.write"],
      "fix_safety": "SAFE",
      "quickfix_patch": [
        {
          "op": "replace",
          "path": "/functions/process_data/effects",
          "value": ["console.write", "fs.read"]
        }
      ]
    }
  ]
}
```

### The `FixSafety` Classification
* **`SAFE`:** Guaranteed semantic and invariant preservation. The agent can apply the RFC 6902 patch automatically via `kantc fix --apply` without human intervention.
* **`REVIEW`:** Requires human authorization or architectural review (e.g., adding an unvetted capability parameter, weakening a contract bound, or altering public signatures).

---

## 3. The 10 Canonical MCP Server Tools (`kant-mcp`)

The `kant-mcp` daemon implements the Model Context Protocol (MCP), exposing 10 atomic programmatic tools:

1. `kant_check(path)`: Executes syntax parsing, De Bruijn indexing, and 12-categories type checking. Returns typed holes and diagnostic errors.
2. `kant_effects(path)`: Computes exact effect inference and validates `dyn` quarantine call sets.
3. `kant_spec(path)`: Generates or synchronizes the `.spec` contract view for human and agent review.
4. `kant_graph(fn_name)`: Returns the exact blast radius (transitive callers and callee dependencies) as a structured JSON graph.
5. `kant_context(symbol, budget_kb)`: Exports a token-budgeted semantic slice (types, signatures, and contracts) of relevant dependencies.
6. `kant_fix(diagnostics_json)`: Executes RFC 6902 patches marked `SAFE` across target source files.
7. `kant_eval(path, args)`: Executes the deterministic reference KANT-IR interpreter and returns execution traces.
8. `kant_build(path, target)`: Invokes the Cranelift backend to compile standalone native machine executables.
9. `kant_replay(evidence_path)`: Replays past executions deterministically from the Merkle audit trail.
10. `kant_grammar(output_format)`: Exports EBNF grammar in XGrammar / LLGuidance constrained decoding tables.

---

## 4. Constrained Decoding Integration (XGrammar)

To prevent syntactic and structural hallucinations at inference time:
* `kantc grammar --export-xgrammar` emits the formal EBNF grammar compiled into a deterministic finite-state automaton (DFA) / Trie mask format.
* Integrates directly into model serving runtimes (vLLM, SGLang, Ollama) to enforce valid `.kant` syntax per token sample with negligible latency (~40 $\mu\text{s}$ per token mask evaluation).
