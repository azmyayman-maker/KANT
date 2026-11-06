# 07_AGENT_SURFACE_SIDECAR_AND_MCP.md: Machine Surface, Lockfile Sidecar & MCP Protocol

To achieve seamless, zero-friction pair programming with AI agents, `kantc` exposes an advanced machine-first interface alongside its human CLI. This includes **Structured JSON Diagnostics**, **RFC 6902 JSON Patch Auto-Fixes**, **Deterministic Sidecar Reconciliation Rules (R1–R6)**, and an official **Model Context Protocol (MCP) Server**.

---

## 1. Sidecar Reconciliation Engine (`module.kant.lock`)

The lockfile pins every definition's content hash (`DefHash`). When an AI agent edits a file, the compiler reconciles the AST against `module.kant.lock` using six deterministic rules:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   SIDECAR RECONCILIATION RULES (R1–R6)                  │
├──────┬──────────────────────┬──────────────────────────────────────────┤
│ Rule │ Condition            │ Compiler Action                          │
├──────┼──────────────────────┼──────────────────────────────────────────┤
│ R1   │ Name & Hash Match    │ Accept without modification.             │
│ R2   │ Resolution Changed   │ Fatal Error: Name reassigned to another  │
│      │                      │ existing definition (prevents hijack).   │
│ R3   │ Content Drift        │ Development: Update hash.                │
│      │                      │ CI (`--frozen`): Error KANT-E601.         │
│ R4   │ Mechanical Rename    │ Detect old hash with new name. Emit SAFE │
│      │                      │ patch updating callers to new name.      │
│ R5   │ Unresolved Symbol    │ Lookup upstream library or emit hole.    │
│ R6   │ New Definition       │ Compute canonical SHA-256 and append pin.│
└──────┴──────────────────────┴──────────────────────────────────────────┘
```

---

## 2. Structured JSON Diagnostics & RFC 6902 Auto-Fixes

Every `kantc` command supports the `--json` flag. Diagnostics are output in a standardized machine-readable schema:

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

### The `FixSafety` Contract:
* `SAFE`: Guaranteed semantic preservation. The agent may apply the patch automatically via `kantc fix --apply` without human intervention.
* `REVIEW`: Requires human confirmation or architectural review (e.g., adding a new Noumena capability parameter or modifying contract bounds).

---

## 3. The 10 Canonical MCP Tools (`kant-mcp`)

The `kant-mcp` daemon implements the Model Context Protocol (MCP), providing direct programmatic control to agent hosts (Claude Code, Cursor, Codex, Gemini CLI):

1. `kant_check(path)`: Fast syntax, De Bruijn indexing, and 12-categories type checking. Returns typed holes and errors.
2. `kant_effects(path)`: Computes exact effect inference and validates `dyn` quarantine sets.
3. `kant_spec(path)`: Generates or updates the concise `.spec` contract view for human signing.
4. `kant_graph(fn_name)`: Returns the exact blast radius (transitive callers and callee dependencies) as JSON.
5. `kant_context(symbol, budget_kb)`: Exports a token-budgeted semantic slice (types, signatures, and contracts) of relevant dependencies.
6. `kant_fix(diagnostics_json)`: Executes RFC 6902 patches marked `SAFE` on target source files.
7. `kant_eval(path, args)`: Runs the deterministic reference KANT-IR interpreter and returns execution traces.
8. `kant_build(path, target)`: Invokes Cranelift to generate native static machine executables.
9. `kant_replay(evidence_path)`: Replays past executions deterministically from the Merkle audit trail.
10. `kant_grammar(output_format)`: Exports XGrammar/LLGuidance constrained sampling tables.

---

## 4. Constrained Decoding Integration (XGrammar)

To prevent syntactic halluncinations before tokens are even sampled:
* `kantc grammar --export-xgrammar` emits the formal EBNF grammar in pre-compiled Trie/State Machine format.
* Compatible with modern inference engines (vLLM, SGLang, Ollama) to enforce 100% syntactically valid `.kant` generation with negligible overhead (~40 $\mu\text{s}$ per token mask).
