# ADR-0008: Structured JSON Diagnostics with RFC 6902 Auto-Fix Patches

* **Status:** Accepted
* **Deciders:** Kant Architecture Working Group, Tooling & Diagnostics Engineers
* **Date:** 2026-11-06
* **Technical Subsystem:** `crates/kant-diag`
* **Related Invariant:** Invariant $G_2$ & Agent Surface Spec (`docs/spec/07_AGENT_SURFACE_SIDECAR_AND_MCP.md`)

---

## Context & Problem Statement

Traditional compilers format errors for human visual consumption using ASCII color codes, terminal art, and multi-line carets. When autonomous AI agents invoke compilers, they are forced to regex-scrape terminal text to identify error line numbers, error descriptions, and recommended fixes. This leads to brittle parsing, mislocated edits, and repetitive compile-fail loops.

How can `kantc` deliver first-class, machine-native error reporting that empowers AI agents and IDEs to diagnose issues accurately and apply instant, automated code repairs?

---

## Decision Drivers

1. **Machine-First Serialization:** All diagnostics must be representable as standardized JSON schema.
2. **Deterministic Auto-Repair:** Mechanical fixes (e.g., adding missing effect annotations, sorting fields, adjusting De Bruijn bindings) must be emitted as declarative patches.
3. **Safety Boundaries:** Distinguish between provably non-destructive fixes (`SAFE`) and modifications requiring human oversight (`REVIEW`).
4. **Universal Protocol Support:** Direct integration with LSP and Model Context Protocol (MCP).

---

## Considered Options

* **Option 1: Human-Only Terminal Text Output with Regex Scraping**
* **Option 2: Basic JSON Output with File/Line/Column Coordinates Only**
* **Option 3: Structured JSON Diagnostics with Embedded RFC 6902 JSON Patches & FixSafety Metadata**

---

## Decision Outcome

**Chosen Option:** **Option 3: Structured JSON Diagnostics with Embedded RFC 6902 JSON Patches & FixSafety Metadata**.

Every command in the `kantc` toolchain supports `--json`. Diagnostics are structured under a strict JSON schema (`diagnostics-v0.1.json`), containing standardized numeric error codes (`KANT-Exxx`), source byte spans, semantic contexts (`got` vs `want`), a `fix_safety` enumeration (`SAFE` or `REVIEW`), and declarative **RFC 6902 JSON Patches**. 

Agents can query `kantc check --json` and immediately execute `kantc fix --apply` or apply the patch directly to their internal AST representations without human intervention.

### Positive Consequences
- AI agents repair syntax and effect errors in $O(1)$ operations without prompt retries.
- Eliminates regex parsing fragility across different terminal emulators and OS environments.
- Clean contract boundary for the `kant-mcp` daemon and IDE language servers.

### Negative Consequences
- Slightly increased diagnostic payload size.
- Compiler passes must construct AST patches alongside human-readable explanations.

---

## Pros and Cons of Options

### Option 1: Human Terminal Text Only
* *Pros:* No additional JSON schema development needed.
* *Cons:* Extreme fragility for agents; high token waste; prone to misparsed line coordinates.

### Option 2: Basic Coordinate JSON
* *Pros:* Standard for older IDE integrations.
* *Cons:* Lacks actionable patch instructions; agents must re-infer the fix from prose.

### Option 3: RFC 6902 Structured JSON Diagnostics (Selected)
* *Pros:*
  - Fully declarative, standards-based patch protocol (RFC 6902).
  - Explicit `fix_safety` annotations prevent unsafe automated mutations.
  - Native integration with MCP tool `kant_fix`.
* *Cons:* Requires each compiler stage to implement patch generation logic.

---

## Validation

Validated via `kant-diag` integration tests:
- Synthetic compilation errors parsed against `diagnostics-v0.1.json` schema.
- Automated application of RFC 6902 patches via `kantc fix --apply` restores failing files to valid compilation state in zero-shot tests.
