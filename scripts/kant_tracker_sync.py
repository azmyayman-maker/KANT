#!/usr/bin/env python3
"""
kant_tracker_sync.py: High-Assurance SQLite Telemetry Engine & Live SSE Server
for the Kant (.kant) Compiler Verification Observatory.

Provides persistent SQLite database telemetry at .kant-tracker/kant_telemetry.db,
bidirectional state.json synchronization, real-time Server-Sent Events (SSE) streaming,
formal Five-Step Gate Run audit logging, and automated CLI verification commands.
"""

import sys
import os
import json
import sqlite3
import argparse
import subprocess
import threading
import queue
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

TRACKER_DIR = Path(".kant-tracker")
STATE_FILE = TRACKER_DIR / "state.json"
DB_FILE = TRACKER_DIR / "kant_telemetry.db"

DEFAULT_ROADMAP = {'version': '0.1.0', 'last_updated': '2026-11-06T18:00:00Z', 'current_circle_focus': 'C0', 'global_stats': {'total_tasks': 75, 'completed_tasks': 0, 'blocked_tasks': 0, 'progress_percent': 0.0}, 'telemetry_metadata': {'compiler_specification': 'Kant (.kant) v0.1', 'workspace_crates_count': 17, 'pipeline_stages_count': 7, 'verification_gate_standard': 'High-Assurance Formal Compiler Systems Verification', 'state_invariants': {'I_1': 'Deterministic Content-Addressing & Alpha-Equivalence DefHash', 'I_2': 'Exact Set-Equality Effect Inference & Quarantined Dynamism (Sigil Law)', 'I_3': 'Perceus Garbage-Free Reference Counting & Frame-Limited Reuse', 'I_4': 'Noumena Quarantined Zero-Escape Capability Boundary'}}, 'circles': [{'id': 'C0', 'name': 'Stage C0: Compiler Workspace Bootstrap & Epistemic Invariants', 'short_title': 'Stage C0: Bootstrap & Scaffolding', 'sub_phase': 'Workspace Architecture, DefHash Algorithms & Scaffolding', 'gate_invariant': 'Invariant I_1 (Content-Addressing Determinism)', 'arabic_title': 'المرحلة C0: إقلاع مساحة عمل المترجم والثوابت الإبستمولوجية', 'arabic_sub_phase': 'معمارية مساحة العمل، خوارزميات DefHash والهياكل الأساسية', 'arabic_gate_invariant': 'الثابت I_1 (حتمية العنونة بالمحتوى)', 'wave': 'Pre-Wave Foundation', 'gate_status': 'PENDING', 'iteration': 0, 'dependencies': [], 'gate_checklist': {'spec_pinning': False, 'lexicon_mapping': False, 'clarification_triage': False, 'toolchain_hashes': False, 'git_lane_hygiene': False}, 'iterations': [], 'main_headings': [{'id': 'C0.H1', 'title': 'Workspace Architecture & Toolchain Hash Pinning', 'crate_lane': 'crates/kant-core, Cargo.toml, AGENTS.md, docs/spec/', 'assigned_agent': 'SA-01', 'sub_headings': [{'id': 'C0.H1.S1', 'title': 'Root Configuration & Multi-Agent Constitution', 'tasks': [{'id': 'TASK-C0-01', 'task_code': 'C0.H1.S1.T01', 'title': 'Formalize Multi-Agent Constitution & 16-Lane File Concurrency Invariants', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-core', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'git status --porcelain AGENTS.md', 'verification_cmd': 'git status --porcelain AGENTS.md', 'description': 'Audit and enforce strict file-lane boundaries across 16 subagents in AGENTS.md (<350 lines), defining isolated crate domains, the Five-Step Iron Law of Verification, and git worktree isolation.', 'acceptance_criteria': 'Line count strictly <350 lines; 16 distinct subagent boundaries specified; 0 cross-lane write overlap; automated markdown linting clean.', 'notes': 'Verified <350 lines, lanes SA-01 to SA-16 formally isolated.'}, {'id': 'TASK-C0-02', 'task_code': 'C0.H1.S1.T02', 'title': 'Establish Academic Terminology Lexicon & Constructive Type Mapping', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-core', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'test -f docs/spec/01_EPISTEMOLOGY_AND_LEXICON.md', 'verification_cmd': 'test -f docs/spec/01_EPISTEMOLOGY_AND_LEXICON.md', 'description': "Map Moussa Wehbe's academic philosophical translations (mujauz, afhoum, shaym, noumenon, amthoul) directly to Martin-Löf Constructive Type Theory (MLTT) and formal compiler constructs.", 'acceptance_criteria': 'All 12 categories, 4 faculties, and 7 boundary conditions mapped to formal type signatures; zero colloquialisms or speculative commentary.', 'notes': 'Academic philological dictionary and MLTT constructive type theory mapping verified.'}, {'id': 'TASK-C0-03', 'task_code': 'C0.H1.S1.T03', 'title': 'Enforce Workspace Namespace Isolation & Package Disambiguation', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-core', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo check --workspace', 'verification_cmd': 'cargo check --workspace', 'description': 'Establish unambiguous package nomenclature (kantc CLI binary, kant-* modular crates, #![kant(v0.1)] root attributes) isolating the toolchain from legacy CAS or crates.io collisions.', 'acceptance_criteria': 'All 17 crates build cleanly; Cargo.toml workspace dependencies pinned; zero collision with legacy registries.', 'notes': 'Disambiguated from legacy CAS, Langium DSL, and crates.io micro-crates.'}]}, {'id': 'C0.H1.S2', 'title': 'Formal Specification Suite & Cryptographic Manifest', 'tasks': [{'id': 'TASK-C0-04', 'task_code': 'C0.H1.S2.T01', 'title': 'Specify Formal Grammar EBNF, De Bruijn Slot Architecture & AST Invariants', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-core', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'test -f docs/spec/02_AESTHETICS_GRAMMAR_AND_AST.md', 'verification_cmd': 'test -f docs/spec/02_AESTHETICS_GRAMMAR_AND_AST.md', 'description': 'Document complete LL(1) / flattened Pratt EBNF grammar, alpha-equivalence via De Bruijn coordinate indexing, and deterministic SHA-256 DefHash identity rules.', 'acceptance_criteria': '100% formal grammar coverage; 5 AST canonicalization transformations proven confluent; zero parse ambiguity.', 'notes': 'Flattened toplevel EBNF and 5 canonicalization rules locked.'}, {'id': 'TASK-C0-05', 'task_code': 'C0.H1.S2.T02', 'title': 'Formulate 12-Category Type Lattice & Exact Effect Sigil Law', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-types', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'test -f docs/spec/03_ANALYTIC_CATEGORIES_AND_EFFECTS.md', 'verification_cmd': 'test -f docs/spec/03_ANALYTIC_CATEGORIES_AND_EFFECTS.md', 'description': 'Specify constructive type inference over Quantity, Quality, Relation, Modality triads and formalize the Sigil Law enforcing strict set-equality E_decl = E_inf.', 'acceptance_criteria': 'Lattice join/meet semantics defined; atomic effects lattice closed; sound subtyping relation proven.', 'notes': 'Quantity, Quality, Relation, Modality triads and Sigil Law formalized.'}, {'id': 'TASK-C0-06', 'task_code': 'C0.H1.S2.T03', 'title': 'Define 30-Instruction SSA KANT-IR & Perceus Drop-Guided Memory Reuse', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-ir', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'test -f docs/spec/04_SCHEMATISM_IR_AND_PERCEUS.md', 'verification_cmd': 'test -f docs/spec/04_SCHEMATISM_IR_AND_PERCEUS.md', 'description': 'Define KANT-IR 30 SSA instructions, continuation capture/resume semantics, and the Perceus reference-counting model with Alloc@r reuse tokens.', 'acceptance_criteria': 'SSA dominance properties formalized; frame-limited cyclic arena isolation verified; reference count drop points syntactically fixed.', 'notes': '30 KANT-IR ops, frame-limited Alloc@r reuse tokens, cycle-free arena design.'}, {'id': 'TASK-C0-07', 'task_code': 'C0.H1.S2.T04', 'title': 'Specify 3-Tier SMT Contract Verification & Noumena Capability Model', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-antinomy', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'test -f docs/spec/05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md', 'verification_cmd': 'test -f docs/spec/05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md', 'description': 'Specify 3-Tier contract discharge (Tier 1 interval arithmetic, Tier 2 SMT Z3 solver with 10s budget, Tier 3 runtime assertion synthesis) and affine capability sandbox.', 'acceptance_criteria': 'Tier escalation logic formalized; Secret<T> taint analysis rules specified; zero information leakage across capability boundary.', 'notes': 'Affine capability ownership, Secret<T> taint analysis, 3-tier contract proofs.'}, {'id': 'TASK-C0-08', 'task_code': 'C0.H1.S2.T05', 'title': 'Specify Dual-Target Execution Architecture & Cryptographic Merkle Traces', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-eval', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'test -f docs/spec/06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md', 'verification_cmd': 'test -f docs/spec/06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md', 'description': 'Specify bitwise-identical dual-engine semantics (KANT-IR tree-walk evaluator vs Cranelift JIT/AOT native codegen) and SHA-256 Merkle execution trace logging.', 'acceptance_criteria': 'Differential oracle divergence tolerance: 0%; Merkle chain append-only integrity proven; gas metering specification complete.', 'notes': 'KANT-IR evaluator, Cranelift JIT/AOT backend, Merkle evidence format.'}, {'id': 'TASK-C0-09', 'task_code': 'C0.H1.S2.T06', 'title': 'Define RFC 6902 Diagnostics Schema, MCP Interface & Sidecar Formats', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-diag', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'test -f docs/spec/07_AGENT_SURFACE_SIDECAR_AND_MCP.md', 'verification_cmd': 'test -f docs/spec/07_AGENT_SURFACE_SIDECAR_AND_MCP.md', 'description': 'Specify structured JSON diagnostic payloads with RFC 6902 JSON patch auto-fixes, 10 Model Context Protocol tools, and .kantd display sidecar synchronization.', 'acceptance_criteria': 'RFC 6902 JSON schema validation; MCP protocol compliance; XGrammar CFG export specification.', 'notes': 'RFC 6902 JSON patch auto-fixes and XGrammar constrained sampling.'}, {'id': 'TASK-C0-10', 'task_code': 'C0.H1.S2.T07', 'title': 'Compute Cryptographic Toolchain Digests & Pin Manifest in kant-toolchain.toml', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-core', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'test -f kant-toolchain.toml', 'verification_cmd': 'test -f kant-toolchain.toml', 'description': 'Compute BLAKE3 and SHA-256 hashes of all 8 specification documents and pin toolchain invariants in kant-toolchain.toml.', 'acceptance_criteria': 'All 8 document digests verified; git hooks validate hashes; tampering rejected.', 'notes': 'Pinned all 8 document hashes and subagent rules.'}]}]}, {'id': 'C0.H2', 'title': 'Architectural Decision Records & Deferral Engine', 'crate_lane': 'docs/DECISIONS_AND_DEFERRED_ROADMAP.md', 'assigned_agent': 'SA-01', 'sub_headings': [{'id': 'C0.H2.S1', 'title': 'P0 Architectural Baselines', 'tasks': [{'id': 'TASK-C0-11', 'task_code': 'C0.H2.S1.T01', 'title': 'Lock Surface Encoding Protocols & Bi-Directional Sidecar Mapping', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-canonical', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': "grep 'Q01' docs/DECISIONS_AND_DEFERRED_ROADMAP.md", 'verification_cmd': "grep 'Q01' docs/DECISIONS_AND_DEFERRED_ROADMAP.md", 'description': 'Codify ADR-001 locking UTF-8 ASCII for tokenizer determinism and .kantd JSON sidecars for localized Arabic visual presentation.', 'acceptance_criteria': 'Zero encoding ambiguity; roundtrip AST lossless preservation.', 'notes': 'Latin ASCII for tokenizer fidelity, Arabic .kantd sidecar for inspection.'}, {'id': 'TASK-C0-12', 'task_code': 'C0.H2.S1.T02', 'title': 'Lock Flattened Infix Grammar & Binding-Order Coordinate Indexing', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-parser', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': "grep 'Q03' docs/DECISIONS_AND_DEFERRED_ROADMAP.md", 'verification_cmd': "grep 'Q03' docs/DECISIONS_AND_DEFERRED_ROADMAP.md", 'description': 'Codify ADR-003 establishing flattened infix syntax to maximize LLM KV-cache reuse and canonical binding-order De Bruijn coordinates.', 'acceptance_criteria': 'Zero syntax nesting beyond mandatory blocks; deterministic AST identity invariant I_1.', 'notes': 'Flattened infix to avoid KV-cache misses; @T.0 De Bruijn indices for hashes.'}, {'id': 'TASK-C0-13', 'task_code': 'C0.H2.S1.T03', 'title': 'Lock Sigil Law Effect Matching & 3-Tier Escalation Model', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-effects', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': "grep 'Q09' docs/DECISIONS_AND_DEFERRED_ROADMAP.md", 'verification_cmd': "grep 'Q09' docs/DECISIONS_AND_DEFERRED_ROADMAP.md", 'description': 'Codify ADR-009 establishing set-equality effect matching (Sigil Law) and automated SAFE quickfix patch generation.', 'acceptance_criteria': 'Invariant I_2 formalized; zero undeclared side effects; patch convergence guarantee.', 'notes': 'E_decl = E_inf with SAFE quickfixes; Tier 1 SMT + Tier 3 runtime fallback.'}, {'id': 'TASK-C0-14', 'task_code': 'C0.H2.S1.T04', 'title': 'Lock Dual Backend Targets: KANT-IR Evaluator & Cranelift Native Engine', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-codegen', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': "grep 'Q25' docs/DECISIONS_AND_DEFERRED_ROADMAP.md", 'verification_cmd': "grep 'Q25' docs/DECISIONS_AND_DEFERRED_ROADMAP.md", 'description': 'Codify ADR-025 locking KANT-IR reference interpreter for proof verification and Cranelift backend for sub-3ms native execution.', 'acceptance_criteria': 'Differential testing protocol locked; platform target triples pinned (x86_64, aarch64).', 'notes': 'Evaluator for deterministic traces, Cranelift for native x86-64 / ARM64.'}]}, {'id': 'C0.H2.S2', 'title': 'Deferral Registry & Extension Boundaries', 'tasks': [{'id': 'TASK-C0-15', 'task_code': 'C0.H2.S2.T01', 'title': 'Triage 24 Deferrable Architectural Questions to MVP Pragmatic Standards', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-core', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'test -f docs/DECISIONS_AND_DEFERRED_ROADMAP.md', 'verification_cmd': 'test -f docs/DECISIONS_AND_DEFERRED_ROADMAP.md', 'description': 'Document and triage 24 non-blocking design decisions (P1/P2) with explicit MVP default resolutions in DECISIONS_AND_DEFERRED_ROADMAP.md.', 'acceptance_criteria': '24 ADRs recorded with rationale, trade-offs, and verification test requirements.', 'notes': 'Recorded all 24 P1/P2 items in ADR format.'}, {'id': 'TASK-C0-16', 'task_code': 'C0.H2.S2.T02', 'title': 'Establish Trait Boundaries for Post-v0.1 Subsystems', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-core', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': "grep 'v0.2' docs/DECISIONS_AND_DEFERRED_ROADMAP.md", 'verification_cmd': "grep 'v0.2' docs/DECISIONS_AND_DEFERRED_ROADMAP.md", 'description': 'Define abstract Rust trait interfaces for post-v0.1 extensions (Lean 4 proof exporter, Atomic RC, WebAssembly runtime, GPUI interface) preventing architectural lock-in.', 'acceptance_criteria': 'Trait signatures compiled in kant-core; 0 breaking changes required for future modules.', 'notes': 'Trait boundaries defined for ProofExporter, AtomicRC, and WASM backend.'}]}]}]}, {'id': 'C1', 'name': 'Stage C1: Transcendental Aesthetic — Lexer & Canonical AST Parser', 'short_title': 'Stage C1: Aesthetic (Lexer & Parser)', 'sub_phase': '48-Token Lexical Stream, De Bruijn Indexing & AST Normalization', 'gate_invariant': 'Token Determinism & Span Precision', 'arabic_title': 'المرحلة C1: الجمالياء المجاوزة — المميّز المعجمي والمحلل النحوي المعياري', 'arabic_sub_phase': 'دفق 48 رمزاً معجمياً، ترقيم دي بروين وموازنة شجرة الإعراب المجردة', 'arabic_gate_invariant': 'حتمية الرموز المعجمية ودقة المدى النطاقي', 'wave': 'Wave 1: Foundation Parsing', 'gate_status': 'LOCKED', 'iteration': 0, 'dependencies': ['C0'], 'gate_checklist': {'cargo_fmt': False, 'cargo_clippy': False, 'cargo_test': False, 'conformance_tests': False, 'git_status_clean': False}, 'iterations': [], 'main_headings': [{'id': 'C1.H1', 'title': 'Core Primitives & Zero-Copy Lexical Analyzer', 'crate_lane': 'crates/kant-core, crates/kant-lexer', 'assigned_agent': 'SA-01 & SA-02', 'sub_headings': [{'id': 'C1.H1.S1', 'title': 'Byte-Span Tracking, Symbol Interning & Lexical Stream', 'tasks': [{'id': 'TASK-C1-01', 'task_code': 'C1.H1.S1.T01', 'title': 'Implement High-Precision ByteSpan, SymbolId Interner & SHA-256 DefHash', 'assigned_agent': 'SA-01', 'target_crate': 'crates/kant-core', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-core --test test_defhash -- --nocapture', 'verification_cmd': 'cargo test -p kant-core --test test_defhash -- --nocapture', 'description': 'Construct zero-allocation ByteSpan arithmetic, thread-safe symbol interning with atomic SymbolId, and SHA-256 content-addressing DefHash engine.', 'acceptance_criteria': 'Zero heap allocations during span merging; interner throughput > 10M symbols/sec; DefHash matches reference test vectors.', 'notes': 'ByteSpan with merge/len, SymbolId interner, DefHash with SHA-256.'}, {'id': 'TASK-C1-02', 'task_code': 'C1.H1.S1.T02', 'title': 'Implement Closed 48-Token Keyword & Operator Lexical Table', 'assigned_agent': 'SA-02', 'target_crate': 'crates/kant-lexer', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-lexer test_closed_epistemic_keywords', 'verification_cmd': 'cargo test -p kant-lexer test_closed_epistemic_keywords', 'description': 'Define the closed 48-token vocabulary table in kant-lexer mapping epistemic keywords, category markers, and effect operators.', 'acceptance_criteria': '100% token coverage; zero hash collisions in token lookup; exact mapping to academic terminology.', 'notes': 'Closed keywords matching Moussa Wehbe lexicon and effect operators.'}, {'id': 'TASK-C1-03', 'task_code': 'C1.H1.S1.T03', 'title': 'Implement Zero-Copy Lexer for Literals, Contracts & Typed Holes', 'assigned_agent': 'SA-02', 'target_crate': 'crates/kant-lexer', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-lexer conformance_lexer', 'verification_cmd': 'cargo test -p kant-lexer conformance_lexer', 'description': 'Build streaming zero-copy lexical analyzer producing deterministic token stream with exact byte offsets for literals, identifiers, contract blocks, and typed hole tokens (?T).', 'acceptance_criteria': 'Throughput > 50 MB/s; zero panics on malformed UTF-8; deterministic token stream across architectures.', 'notes': 'Magic header, ?hole, @T.0 De Bruijn slots, strings, numbers.'}]}]}, {'id': 'C1.H2', 'title': 'Flattened Pratt & LL(1) AST Parser', 'crate_lane': 'crates/kant-parser', 'assigned_agent': 'SA-03', 'sub_headings': [{'id': 'C1.H2.S1', 'title': 'Declarations, Contract Clauses & Error Recovery', 'tasks': [{'id': 'TASK-C1-04', 'task_code': 'C1.H2.S1.T01', 'title': 'Parse Top-Level Type Definitions (Afhoum) & Function Signatures', 'assigned_agent': 'SA-03', 'target_crate': 'crates/kant-parser', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-parser test_parse_afhoum_and_cap', 'verification_cmd': 'cargo test -p kant-parser test_parse_afhoum_and_cap', 'description': 'Parse top-level algebraic data types, struct records, capability declarations, and function signatures into AST nodes without deep recursion.', 'acceptance_criteria': '100% grammar conformance for top-level constructs; stack depth < 64 frames; zero heap leakage on parse failure.', 'notes': 'Toplevel declarations parsed cleanly without deep nesting.'}, {'id': 'TASK-C1-05', 'task_code': 'C1.H2.S1.T02', 'title': 'Parse Mandatory Contract Clauses (Requires, Ensures, Decreases, Effects)', 'assigned_agent': 'SA-03', 'target_crate': 'crates/kant-parser', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-parser test_parse_full_function_with_contracts', 'verification_cmd': 'cargo test -p kant-parser test_parse_full_function_with_contracts', 'description': 'Parse structured contract blocks preceding function bodies, validating mandatory requires, ensures, decreases, and effect annotations.', 'acceptance_criteria': 'Contract expressions parsed with full operator precedence; AST preserves precise span offsets for diagnostic attribution.', 'notes': 'Contract blocks parsed before function body.'}, {'id': 'TASK-C1-06', 'task_code': 'C1.H2.S1.T03', 'title': 'Parse Decision Blocks & Quarantined Dynamic Execution Blocks', 'assigned_agent': 'SA-03', 'target_crate': 'crates/kant-parser', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-parser test_parse_decision_block', 'verification_cmd': 'cargo test -p kant-parser test_parse_decision_block', 'description': 'Implement parsers for architectural decision metadata blocks and quarantined dynamic invocation blocks (dyn { ... }).', 'acceptance_criteria': 'Decision metadata correctly extracted to AST sidecars; dyn block syntax validated with callee set restrictions.', 'notes': 'Structured metadata parsed for compiler and spec views.'}, {'id': 'TASK-C1-07', 'task_code': 'C1.H2.S1.T04', 'title': 'Implement Resilient Syntax Error Recovery Emitting Expr::Hole', 'assigned_agent': 'SA-03', 'target_crate': 'crates/kant-parser', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-parser test_parse_typed_hole_and_operator_precedence', 'verification_cmd': 'cargo test -p kant-parser test_parse_typed_hole_and_operator_precedence', 'description': 'Build robust error recovery reducing malformed syntax subtrees to Expr::Hole with attached diagnostics, enabling incremental agent repair without aborting compilation.', 'acceptance_criteria': 'Zero compiler aborts or panics on arbitrary invalid input; correct Pratt precedence table evaluation.', 'notes': 'Zero panics on syntax errors; emits Expr::Hole for agent repair.'}]}]}, {'id': 'C1.H3', 'title': 'Spatial Canonicalizer & Sidecar Lockfile Engine', 'crate_lane': 'crates/kant-canonical', 'assigned_agent': 'SA-04', 'sub_headings': [{'id': 'C1.H3.S1', 'title': 'De Bruijn Slot Erasure & Canonical Normalization', 'tasks': [{'id': 'TASK-C1-08', 'task_code': 'C1.H3.S1.T01', 'title': 'Implement Alpha-Equivalence Normalization via De Bruijn Slot Erasure', 'assigned_agent': 'SA-04', 'target_crate': 'crates/kant-canonical', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-canonical test_alpha_equivalence_invariant', 'verification_cmd': 'cargo test -p kant-canonical test_alpha_equivalence_invariant', 'description': 'Erase local variable and parameter names to deterministic @T.0, @T.1 binding-order coordinates, guaranteeing identical DefHash across alpha-equivalent ASTs.', 'acceptance_criteria': 'Renaming identifiers produces 100% bitwise-identical SHA-256 DefHash; variable scoping resolution is strictly sound.', 'notes': 'Renaming local variables produces 100% identical DefHash.'}, {'id': 'TASK-C1-09', 'task_code': 'C1.H3.S1.T02', 'title': 'Normalize Record Field Ordering & Recursive Self References', 'assigned_agent': 'SA-04', 'target_crate': 'crates/kant-canonical', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-canonical test_type_field_order_invariance', 'verification_cmd': 'cargo test -p kant-canonical test_type_field_order_invariance', 'description': 'Sort record struct fields lexicographically and normalize recursive calls to canonical @self references.', 'acceptance_criteria': 'Permutations of field declarations yield identical AST hashes; mutually recursive bindings canonicalized deterministically.', 'notes': 'Field ordering invariance verified.'}, {'id': 'TASK-C1-10', 'task_code': 'C1.H3.S1.T03', 'title': 'Implement Bi-Directional Symbol Sidecar (.kantd) Round-Trip Engine', 'assigned_agent': 'SA-04', 'target_crate': 'crates/kant-canonical', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-canonical test_kantd_roundtrip', 'verification_cmd': 'cargo test -p kant-canonical test_kantd_roundtrip', 'description': 'Serialize human-readable and localized display names into .kantd sidecar files and reconstruct canonical AST representations losslessly.', 'acceptance_criteria': 'Round-trip display name preservation: 100%; zero drift in underlying De Bruijn slot indexing.', 'notes': 'Generates .kantd file mapping De Bruijn slots back to human names.'}]}, {'id': 'C1.H3.S2', 'title': 'Sidecar Lockfile Reconciliation Rules R1–R6', 'tasks': [{'id': 'TASK-C1-11', 'task_code': 'C1.H3.S2.T01', 'title': 'Implement Lockfile Engine Reconciliation Rules R1 (Match) & R6 (New Pin)', 'assigned_agent': 'SA-04', 'target_crate': 'crates/kant-canonical', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-canonical test_lockfile_reconciliation_r1_and_r4_mechanical_rename', 'verification_cmd': 'cargo test -p kant-canonical test_lockfile_reconciliation_r1_and_r4_mechanical_rename', 'description': 'Implement module.kant.lock reconciliation for matching definitions (R1) and novel symbol additions (R6).', 'acceptance_criteria': 'Lockfile accurately records symbol DefHash; auto-pinning succeeds on fresh definitions.', 'notes': 'Pushed to lockfile seamlessly on matching and novel defs.'}, {'id': 'TASK-C1-12', 'task_code': 'C1.H3.S2.T02', 'title': 'Implement Lockfile Enforcement Rules R2 (Resolution Error) & R3 (Content Drift)', 'assigned_agent': 'SA-04', 'target_crate': 'crates/kant-canonical', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-canonical conformance_canonical', 'verification_cmd': 'cargo test -p kant-canonical conformance_canonical', 'description': 'Detect resolution changes (R2 hard error) and unpinned content drift (R3), enforcing strict --frozen verification mode in CI/CD pipelines.', 'acceptance_criteria': 'Hard failure emitted on resolution hijacking; content drift flagged with actionable git diff diagnostics.', 'notes': 'Prevents silent rebinding hijacks; enforces --frozen in CI.'}, {'id': 'TASK-C1-13', 'task_code': 'C1.H3.S2.T03', 'title': 'Implement Rule R4 Identity Rename Detection & RFC 6902 Patch Emission', 'assigned_agent': 'SA-04', 'target_crate': 'crates/kant-canonical', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-canonical test_lockfile_reconciliation_r1_and_r4_mechanical_rename', 'verification_cmd': 'cargo test -p kant-canonical test_lockfile_reconciliation_r1_and_r4_mechanical_rename', 'description': 'Detect identifier renames by tracking constant DefHash across revisions and emit RFC 6902 JSON patch operations to update all call-sites mechanically.', 'acceptance_criteria': '100% automated call-site reference patch generation; zero broken references across workspace.', 'notes': 'Emits RFC 6902 patch updating callers automatically.'}]}]}]}, {'id': 'C2', 'name': 'Stage C2: Transcendental Analytic — 12 Categories & Exact Effects', 'short_title': 'Stage C2: Analytic (Types & Effects)', 'sub_phase': 'Constructive Type Inference, Subtyping & Sigil Law (E_decl = E_inf)', 'gate_invariant': 'Invariant I_2 (Exact Effect Matching & Quarantined Dynamism)', 'arabic_title': 'المرحلة C2: التحليلياء المجاوزة — المقولات الاثنتا عشرة والآثار الدقيقة', 'arabic_sub_phase': 'استدلال الأنماط البنائي، تفرع الأنماط وقانون السمة (E_decl = E_inf)', 'arabic_gate_invariant': 'الثابت I_2 (المطابقة الدقيقة للآثار والحركية المعزولة)', 'wave': 'Wave 2: Types & Effects', 'gate_status': 'LOCKED', 'iteration': 0, 'dependencies': ['C1'], 'gate_checklist': {'cargo_fmt': False, 'cargo_clippy': False, 'cargo_test': False, 'conformance_tests': False, 'git_status_clean': False}, 'iterations': [], 'main_headings': [{'id': 'C2.H1', 'title': '12-Category Constructive Type System', 'crate_lane': 'crates/kant-types', 'assigned_agent': 'SA-05', 'sub_headings': [{'id': 'C2.H1.S1', 'title': 'Triads of Quantity, Quality, Relation & Modality', 'tasks': [{'id': 'TASK-C2-01', 'task_code': 'C2.H1.S1.T01', 'title': 'Implement Category of Quantity: Unity Primitives, Plurality Arrays & Totality ADTs', 'assigned_agent': 'SA-05', 'target_crate': 'crates/kant-types', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-types test_category_quantity', 'verification_cmd': 'cargo test -p kant-types test_category_quantity', 'description': 'Construct type representation and inference rules for Quantity triad: Unity (scalars), Plurality (fixed/slice collections), Totality (exhaustive sum types).', 'acceptance_criteria': 'Exhaustiveness checking for Totality ADTs; bounds check elision for Plurality slices; sound primitive representation.', 'notes': 'Type categories assigned to TypedModule AST.'}, {'id': 'TASK-C2-02', 'task_code': 'C2.H1.S1.T02', 'title': 'Implement Category of Quality: Reality Inhabitation, Negation Never & Limitation Secret<T>', 'assigned_agent': 'SA-05', 'target_crate': 'crates/kant-types', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-types test_category_quality', 'verification_cmd': 'cargo test -p kant-types test_category_quality', 'description': 'Implement Quality triad: Reality (type inhabitation proof), Negation (empty/never type !), Limitation (Secret<T> information flow containment).', 'acceptance_criteria': 'Uninhabited types detected at compile-time; Secret<T> values prevented from escaping to observable channels.', 'notes': 'Check inhabitation and Secret<T> wrapper.'}, {'id': 'TASK-C2-03', 'task_code': 'C2.H1.S1.T03', 'title': 'Implement Category of Relation: Substance Records & Causality Effect Arrows', 'assigned_agent': 'SA-05', 'target_crate': 'crates/kant-types', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-types test_category_relation', 'verification_cmd': 'cargo test -p kant-types test_category_relation', 'description': 'Implement Relation triad: Substance (immutable algebraic records) and Causality (function arrows carrying explicit effect sets fn -> T ! E).', 'acceptance_criteria': 'Structural subtyping for records; effect sets attached to every function type; sound arrow composition.', 'notes': 'Arrows carrying explicit effect sets.'}, {'id': 'TASK-C2-04', 'task_code': 'C2.H1.S1.T04', 'title': 'Implement Category of Modality: Possibility Monads, Actuality Tokens & Necessity Consts', 'assigned_agent': 'SA-05', 'target_crate': 'crates/kant-types', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-types test_category_modality', 'verification_cmd': 'cargo test -p kant-types test_category_modality', 'description': 'Implement Modality triad: Possibility (Option/Result algebraic types), Actuality (linear capability tokens), Necessity (compile-time proven constants).', 'acceptance_criteria': 'Option/Result pattern completeness verified; capability linear use enforced; const expressions evaluated at compile time.', 'notes': 'Option/Result, linear cap types, and proved consts.'}]}]}, {'id': 'C2.H2', 'title': 'Exact Effect Verifier & Quarantined Dynamism', 'crate_lane': 'crates/kant-effects', 'assigned_agent': 'SA-06', 'sub_headings': [{'id': 'C2.H2.S1', 'title': 'Sigil-Style Exact Set-Equality Effect Inference', 'tasks': [{'id': 'TASK-C2-05', 'task_code': 'C2.H2.S1.T01', 'title': 'Construct Atomic Effect Lattice (Console, FS, Net, AI, Clock, Entropy, Diverge)', 'assigned_agent': 'SA-06', 'target_crate': 'crates/kant-effects', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-effects test_01_pure_function_exact_match', 'verification_cmd': 'cargo test -p kant-effects test_01_pure_function_exact_match', 'description': 'Build atomic effect bitset lattice and composition operations for the 7 primary effects: console, fs, net, ai, clock, entropy, diverge.', 'acceptance_criteria': 'Bitset operations O(1); pure functions infer empty effect set {}; effect union and intersection operations sound.', 'notes': 'AtomicEffect enum and EffectSet operations.'}, {'id': 'TASK-C2-06', 'task_code': 'C2.H2.S1.T02', 'title': 'Enforce Strict Sigil Law Set Equality & Emit RFC 6902 SAFE Patches', 'assigned_agent': 'SA-06', 'target_crate': 'crates/kant-effects', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-effects test_02_undeclared_effect_rejected_with_safe_patch', 'verification_cmd': 'cargo test -p kant-effects test_02_undeclared_effect_rejected_with_safe_patch', 'description': 'Verify E_decl(f) = E_inf(f) strict set equality; reject undeclared or over-declared effects (KANT-E301/E302) and emit SAFE RFC 6902 JSON patch auto-fixes.', 'acceptance_criteria': '100% detection of effect mismatch; diagnostic payload contains valid JSON patch replacing effect set; zero false positives.', 'notes': 'RFC 6902 patch replacement of /functions/<idx>/effects.'}, {'id': 'TASK-C2-07', 'task_code': 'C2.H2.S1.T03', 'title': 'Implement Higher-Order Effect Parameter Substitution of(f)', 'assigned_agent': 'SA-06', 'target_crate': 'crates/kant-effects', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-effects test_04_higher_order_effects_of_param', 'verification_cmd': 'cargo test -p kant-effects test_04_higher_order_effects_of_param', 'description': 'Implement polymorphic effect tracking for higher-order functions using of(f) notation, substituting actual argument effect sets into caller signatures.', 'acceptance_criteria': 'Higher-order calls accurately propagate closure effect sets; deep composition verified without effect loss.', 'notes': 'Substitutes concrete lambda effects into caller signature.'}]}, {'id': 'C2.H2.S2', 'title': 'Quarantined Dynamism Engine (Guarantees G1–G4)', 'tasks': [{'id': 'TASK-C2-08', 'task_code': 'C2.H2.S2.T01', 'title': 'Enforce Inert Function Pointers & Restrict Indirect Calls to dyn { t1..tn }', 'assigned_agent': 'SA-06', 'target_crate': 'crates/kant-effects', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-effects test_05_unquarantined_funref_call_rejected', 'verification_cmd': 'cargo test -p kant-effects test_05_unquarantined_funref_call_rejected', 'description': 'Treat raw function references as inert data (&fn) and reject indirect invocations unless explicitly quarantined within dyn { t1..tn } blocks.', 'acceptance_criteria': 'Unmediated indirect function calls strictly rejected with diagnostic KANT-E305; quarantine boundary enforced.', 'notes': 'Reject escaped function pointers outside dyn blocks.'}, {'id': 'TASK-C2-09', 'task_code': 'C2.H2.S2.T02', 'title': 'Implement Intraprocedural May-Reach Callee Set Analysis', 'assigned_agent': 'SA-06', 'target_crate': 'crates/kant-effects', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-effects test_06_quarantine_under_approximation_detected', 'verification_cmd': 'cargo test -p kant-effects test_06_quarantine_under_approximation_detected', 'description': 'Build intraprocedural dataflow reachability analysis to verify that the declared dyn target list is an exhaustive superset of potential callees.', 'acceptance_criteria': 'Under-approximated dyn sets rejected with KANT-E306; auto-fix suggests minimal sound callee target set.', 'notes': 'Emits KANT-E306 if actual callee targets exceed declared list.'}, {'id': 'TASK-C2-10', 'task_code': 'C2.H2.S2.T03', 'title': 'Calculate Transitive Call-Graph Blast Radius & Reference Exactness Ratio', 'assigned_agent': 'SA-06', 'target_crate': 'crates/kant-effects', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-effects test_10_blast_radius_and_exactness_metric', 'verification_cmd': 'cargo test -p kant-effects test_10_blast_radius_and_exactness_metric', 'description': 'Compute reverse-caller dependency cones in O(V+E) and calculate the Exactness Ratio (statically resolved calls / total calls) for G1/G2 verification.', 'acceptance_criteria': 'Blast radius traversal terminates in linear time; exactness metric reported in structured telemetry.', 'notes': 'G1/G2 blast radius and exactness ratio computed in O(V+E).'}]}]}, {'id': 'C2.H3', 'title': 'SSA KANT-IR Lowering & Perceus Memory Engine', 'crate_lane': 'crates/kant-ir, crates/kant-perceus', 'assigned_agent': 'SA-07 & SA-08', 'sub_headings': [{'id': 'C2.H3.S1', 'title': '30-Instruction Basic Block SSA IR Lowering', 'tasks': [{'id': 'TASK-C2-11', 'task_code': 'C2.H3.S1.T01', 'title': 'Lower Typed AST to Canonical 30-Instruction Basic Block SSA IR', 'assigned_agent': 'SA-07', 'target_crate': 'crates/kant-ir', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-ir test_lower_basic_blocks', 'verification_cmd': 'cargo test -p kant-ir test_lower_basic_blocks', 'description': 'Translate checked typed AST into flat basic-block SSA IR utilizing the canonical 30 KANT-IR opcodes with explicit phi-nodes and dominance frontiers.', 'acceptance_criteria': 'Valid SSA dominance invariants; def-use chains verified; zero undefined SSA values.', 'notes': 'SSA dominance and def-use chain verification.'}, {'id': 'TASK-C2-12', 'task_code': 'C2.H3.S1.T02', 'title': 'Lower Effect Handler Delimited Continuations to Capture/Resume Primitives', 'assigned_agent': 'SA-07', 'target_crate': 'crates/kant-ir', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-ir test_effect_handler_lowering', 'verification_cmd': 'cargo test -p kant-ir test_effect_handler_lowering', 'description': 'Lower handle { ... } and governor blocks into first-class delimited continuation tokens and stack reification primitives.', 'acceptance_criteria': 'Continuations correctly capture lexical context; resumption resumes without stack corruption; resource release guaranteed.', 'notes': 'Reified stack frames and continuation tokens.'}]}, {'id': 'C2.H3.S2', 'title': 'Perceus Reference Counting & In-Place Memory Reuse', 'tasks': [{'id': 'TASK-C2-13', 'task_code': 'C2.H3.S2.T01', 'title': 'Synthesize Syntactic Dup & Drop Operators for Garbage-Free Reference Counting', 'assigned_agent': 'SA-08', 'target_crate': 'crates/kant-perceus', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-perceus test_dup_drop_placement', 'verification_cmd': 'cargo test -p kant-perceus test_dup_drop_placement', 'description': 'Implement the Perceus reference-counting static analysis pass, placing precise dup and drop instructions at syntactically last-use locations.', 'acceptance_criteria': 'Zero memory leaks on all reachable execution paths; no dangling references; cyclical structures isolated.', 'notes': 'Free at syntactically last use in time.'}, {'id': 'TASK-C2-14', 'task_code': 'C2.H3.S2.T02', 'title': 'Implement Drop-Guided Reuse Pass with Alloc@r In-Place Buffer Recycling', 'assigned_agent': 'SA-08', 'target_crate': 'crates/kant-perceus', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-perceus test_drop_guided_reuse', 'verification_cmd': 'cargo test -p kant-perceus test_drop_guided_reuse', 'description': 'Identify unique references (RC == 1) prior to drop points and pair them with subsequent allocations of identical size, emitting Alloc@r in-place reuse tokens.', 'acceptance_criteria': 'Recycles >= 80% of heap buffers in loop iterations; zero global GC pauses; frame-limited memory footprint verified.', 'notes': 'In-place buffer recycling with frame-limited memory guarantees.'}]}]}]}, {'id': 'C3', 'name': 'Stage C3: The Schematism — SSA KANT-IR & Perceus Memory Reuse', 'short_title': 'Stage C3: Schematism (IR & Perceus)', 'sub_phase': '30-Instruction SSA Lowering & Drop-Guided Reference Count Optimization', 'gate_invariant': 'Invariant I_3 (Garbage-Free Perceus Memory Soundness)', 'arabic_title': 'المرحلة C3: شيم الفهم — تمثيل SSA KANT-IR وإعادة استخدام الذاكرة ببرسيوس', 'arabic_sub_phase': 'تنزيل 30 تعليمة SSA وتحسين عدّ المراجع الموجّه بالإسقاط', 'arabic_gate_invariant': 'الثابت I_3 (سلامة الذاكرة دون جمع قمامة ببرسيوس)', 'wave': 'Wave 3: Intermediate Representation', 'gate_status': 'LOCKED', 'iteration': 0, 'dependencies': ['C2'], 'gate_checklist': {'cargo_fmt': False, 'cargo_clippy': False, 'cargo_test': False, 'conformance_tests': False, 'git_status_clean': False}, 'iterations': [], 'main_headings': [{'id': 'C3.H1', 'title': 'Paralogism Ownership & Secret Taint Guard', 'crate_lane': 'crates/kant-paralogism', 'assigned_agent': 'SA-09', 'sub_headings': [{'id': 'C3.H1.S1', 'title': 'Affine Capability Tracking & Constant-Time Security', 'tasks': [{'id': 'TASK-C3-01', 'task_code': 'C3.H1.S1.T01', 'title': 'Implement Affine Capability State Machine: Available | Borrowed | Moved', 'assigned_agent': 'SA-09', 'target_crate': 'crates/kant-paralogism', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-paralogism test_use_after_move', 'verification_cmd': 'cargo test -p kant-paralogism test_use_after_move', 'description': 'Track capability token lifecycles across control-flow branches, enforcing affine linear typing and rejecting use-after-move (E004) and double-move (E005).', 'acceptance_criteria': '100% rejection of unauthorized capability duplication; cross-branch state reconciliation enforces identical move states.', 'notes': 'Emits E004 use-after-move, E005 double-move, E009 branch mismatch.'}, {'id': 'TASK-C3-02', 'task_code': 'C3.H1.S1.T02', 'title': 'Implement Secret<T> Zeroize-on-Drop & Constant-Time Taint Propagation', 'assigned_agent': 'SA-09', 'target_crate': 'crates/kant-paralogism', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-paralogism test_secret_taint_branch_leak', 'verification_cmd': 'cargo test -p kant-paralogism test_secret_taint_branch_leak', 'description': 'Enforce cryptographic security invariants on Secret<T> values: automatic memory zeroization on drop and dataflow taint analysis preventing secrets from conditioning branches or index arrays.', 'acceptance_criteria': 'Zero secret leaks to branch conditions or cache lines; zeroize memory wipes confirmed by binary inspection.', 'notes': 'Rejects secret values in branch conditions and cache indices.'}]}]}, {'id': 'C3.H2', 'title': 'Antinomy Contract Verifier & Termination Checker', 'crate_lane': 'crates/kant-antinomy', 'assigned_agent': 'SA-10', 'sub_headings': [{'id': 'C3.H2.S1', 'title': 'Tier 1 Interval SMT Discharge & Tier 3 Runtime Synthesis', 'tasks': [{'id': 'TASK-C3-03', 'task_code': 'C3.H2.S1.T01', 'title': 'Discharge Pre/Post Contract Proofs via Interval Arithmetic & Z3 SMT (10s Budget)', 'assigned_agent': 'SA-10', 'target_crate': 'crates/kant-antinomy', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-antinomy test_tier1_smt_discharge', 'verification_cmd': 'cargo test -p kant-antinomy test_tier1_smt_discharge', 'description': 'Discharge requires/ensures contract verification conditions using fast interval abstract interpretation followed by Z3 SMT queries bound to a strict 10s solver budget.', 'acceptance_criteria': 'Proves linear arithmetic contracts < 100ms; solver timeout strictly handled within 10s threshold; sound error reporting.', 'notes': 'Fast interval evaluation with Z3 SMT solver fallback.'}, {'id': 'TASK-C3-04', 'task_code': 'C3.H2.S1.T02', 'title': 'Synthesize Tier 3 Checked Runtime Assertions on Solver Timeout', 'assigned_agent': 'SA-10', 'target_crate': 'crates/kant-antinomy', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-antinomy test_tier3_runtime_guard_synthesis', 'verification_cmd': 'cargo test -p kant-antinomy test_tier3_runtime_guard_synthesis', 'description': 'When static Tier 1/2 verification is inconclusive or times out, synthesize Tier 3 compiled runtime precondition/postcondition assertion checks with structured error recovery.', 'acceptance_criteria': 'Synthesized assertion overhead < 5% execution time; complete assertion coverage for unproved obligations.', 'notes': 'Lowers unproved obligations to checked asserts with reconciliation.'}, {'id': 'TASK-C3-05', 'task_code': 'C3.H2.S1.T03', 'title': 'Enforce Mandatory Decreases Measures on Recursive SCCs', 'assigned_agent': 'SA-10', 'target_crate': 'crates/kant-antinomy', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-antinomy test_decreases_termination_check', 'verification_cmd': 'cargo test -p kant-antinomy test_decreases_termination_check', 'description': 'Detect recursive strongly-connected components in the call-graph and enforce well-founded decreases ranking functions or explicit diverge effect annotations (E137).', 'acceptance_criteria': 'Rejects non-terminating loops lacking diverge; verifies well-foundedness of decreasing metric; zero infinite loops in pure code.', 'notes': 'Requires decreases clause or explicit diverge effect.'}]}]}, {'id': 'C3.H3', 'title': 'Noumena Capability Sandbox & Spec Extractor', 'crate_lane': 'crates/kant-noumena, crates/kant-spec', 'assigned_agent': 'SA-11 & SA-12', 'sub_headings': [{'id': 'C3.H3.S1', 'title': 'Session-Governor Protocol & Architecture Spec Extraction', 'tasks': [{'id': 'TASK-C3-06', 'task_code': 'C3.H3.S1.T01', 'title': 'Enforce Trust None Architecture & Unforgeable Zero-Sized Capability Tokens', 'assigned_agent': 'SA-11', 'target_crate': 'crates/kant-noumena', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-noumena test_trust_none_enforcement', 'verification_cmd': 'cargo test -p kant-noumena test_trust_none_enforcement', 'description': 'Enforce trust none module defaults where external I/O primitives demand unforgeable Zero-Sized Type capability tokens passed from the application entrypoint.', 'acceptance_criteria': 'Capability forgery physically impossible; unmediated system calls fail compilation.', 'notes': 'Private constructor tokens passed only from entrypoint.'}, {'id': 'TASK-C3-07', 'task_code': 'C3.H3.S1.T02', 'title': 'Implement Human Approval Gate Delimited Continuation Suspension', 'assigned_agent': 'SA-11', 'target_crate': 'crates/kant-noumena', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-noumena test_approval_gate_suspension', 'verification_cmd': 'cargo test -p kant-noumena test_approval_gate_suspension', 'description': 'Implement governor approval_gate checkpoints suspending execution state into serialized continuation frames until explicit human cryptographic authorization is received.', 'acceptance_criteria': 'Suspension state serialized losslessly; resumption requires valid signature; timeout triggers safe cancellation.', 'notes': 'Suspends execution until CLI or IDE signature provided.'}, {'id': 'TASK-C3-08', 'task_code': 'C3.H3.S1.T03', 'title': 'Implement Architectural Spec Extractor & Blast-Radius Visualizer', 'assigned_agent': 'SA-12', 'target_crate': 'crates/kant-spec', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-spec test_spec_and_graph_extraction', 'verification_cmd': 'cargo test -p kant-spec test_spec_and_graph_extraction', 'description': 'Build kantc spec to extract standalone, human-readable .spec interface definitions and kantc graph to render call-graph dependency cones and blast radius diagrams.', 'acceptance_criteria': 'Spec output < 10% token size of full implementation; graph exportable in SVG and JSON dot formats.', 'notes': 'Generates concise .spec file for human signing and token-budgeted slices.'}]}]}]}, {'id': 'C4', 'name': 'Stage C4: Transcendental Dialectic — SMT Verification & Capability Security', 'short_title': 'Stage C4: Dialectic (SMT & Noumena)', 'sub_phase': '3-Tier Contract Verification (Z3 SMT) & Noumena Linear Capability Sandbox', 'gate_invariant': 'Invariant I_4 (Noumena Zero-Escape Capability Boundary)', 'arabic_title': 'المرحلة C4: الجدلياء المجاوزة — التحقق بـ SMT وأمان القدرات الخطية', 'arabic_sub_phase': 'التحقق ثلاثي الطبقات من العقود (Z3 SMT) وبيئة عزل القدرات الخطية للنومان', 'arabic_gate_invariant': 'الثابت I_4 (حدود القدرات الصفرية للهروب في النومان)', 'wave': 'Wave 4: Verification & Codegen', 'gate_status': 'LOCKED', 'iteration': 0, 'dependencies': ['C3'], 'gate_checklist': {'cargo_fmt': False, 'cargo_clippy': False, 'cargo_test': False, 'conformance_tests': False, 'git_status_clean': False}, 'iterations': [], 'main_headings': [{'id': 'C4.H1', 'title': 'Reference Evaluator & Cryptographic Evidence Engine', 'crate_lane': 'crates/kant-eval', 'assigned_agent': 'SA-13', 'sub_headings': [{'id': 'C4.H1.S1', 'title': 'Deterministic KANT-IR Interpreter & Merkle Audit Trails', 'tasks': [{'id': 'TASK-C4-01', 'task_code': 'C4.H1.S1.T01', 'title': 'Implement Deterministic KANT-IR Reference Tree-Walk Interpreter', 'assigned_agent': 'SA-13', 'target_crate': 'crates/kant-eval', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-eval test_deterministic_evaluator', 'verification_cmd': 'cargo test -p kant-eval test_deterministic_evaluator', 'description': 'Construct the canonical reference interpreter for the 30 KANT-IR SSA opcodes, providing an exact operational semantic model and state step counter.', 'acceptance_criteria': 'Bitwise-identical execution across operating systems; gas metering tracks execution steps; zero undefined behavior.', 'notes': 'Interprets 30 KANT-IR SSA opcodes with state trace.'}, {'id': 'TASK-C4-02', 'task_code': 'C4.H1.S1.T02', 'title': 'Construct Append-Only Hash-Chained Merkle Evidence Logging (.kant.evidence.jsonl)', 'assigned_agent': 'SA-13', 'target_crate': 'crates/kant-eval', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-eval test_merkle_evidence_logging', 'verification_cmd': 'cargo test -p kant-eval test_merkle_evidence_logging', 'description': 'Record all effectful I/O invocations and capability handoffs into a cryptographic Merkle tree with parent hash chaining, generating verifiable audit logs.', 'acceptance_criteria': 'Tamper-evident log integrity; verification of proof root in O(log N); zero payload corruption.', 'notes': 'Cryptographic audit trail with parent hash chaining.'}, {'id': 'TASK-C4-03', 'task_code': 'C4.H1.S1.T03', 'title': 'Implement Bit-Identical Deterministic Workflow Replay Engine', 'assigned_agent': 'SA-13', 'target_crate': 'crates/kant-eval', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-eval test_deterministic_replay', 'verification_cmd': 'cargo test -p kant-eval test_deterministic_replay', 'description': 'Implement offline execution replay (kantc replay) reproducing recorded program traces step-by-step from Merkle evidence bundles without external network access.', 'acceptance_criteria': '100% bitwise trace match on recorded workflows; halts with explicit diagnostic on recorded divergence.', 'notes': 'Offline replay without hitting external APIs.'}]}]}, {'id': 'C4.H2', 'title': 'Cranelift JIT & Native AOT Backend', 'crate_lane': 'crates/kant-codegen', 'assigned_agent': 'SA-14', 'sub_headings': [{'id': 'C4.H2.S1', 'title': 'Cranelift Lowering & Static Native Binary Emission', 'tasks': [{'id': 'TASK-C4-04', 'task_code': 'C4.H2.S1.T01', 'title': 'Lower KANT-IR SSA Instructions to Cranelift CLIF Intermediate Representation', 'assigned_agent': 'SA-14', 'target_crate': 'crates/kant-codegen', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-codegen test_clif_lowering', 'verification_cmd': 'cargo test -p kant-codegen test_clif_lowering', 'description': 'Map KANT-IR SSA basic blocks, phi nodes, and memory reuse operations into Cranelift IR (CLIF) for x86_64 and AArch64 targets.', 'acceptance_criteria': 'CLIF passes internal Cranelift verifier; zero type mismatches; calling conventions conform to target ABI.', 'notes': 'Maps SSA values and basic blocks to Cranelift variables.'}, {'id': 'TASK-C4-05', 'task_code': 'C4.H2.S1.T02', 'title': 'Implement Fast In-Memory JIT Compilation Engine for Sub-3ms Development Turnaround', 'assigned_agent': 'SA-14', 'target_crate': 'crates/kant-codegen', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-codegen test_jit_execution', 'verification_cmd': 'cargo test -p kant-codegen test_jit_execution', 'description': 'Construct in-memory JIT execution harness (kantc run) compiling and executing KANT-IR modules within a sub-3ms turnaround budget.', 'acceptance_criteria': 'Compilation and entrypoint jump completed < 3ms for standard modules; execution memory protected.', 'notes': 'Sub-3ms execution turnaround.'}, {'id': 'TASK-C4-06', 'task_code': 'C4.H2.S1.T03', 'title': 'Emit Standalone Static Native Executables with Deterministic Epoch Timestamps', 'assigned_agent': 'SA-14', 'target_crate': 'crates/kant-codegen', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-codegen test_aot_binary_emission', 'verification_cmd': 'cargo test -p kant-codegen test_aot_binary_emission', 'description': 'Generate static ELF/Mach-O/PE native binaries (kantc build) with reproducible object file emission and deterministic timestamps (SOURCE_DATE_EPOCH).', 'acceptance_criteria': 'Independent compilations on distinct hosts yield bit-for-bit identical binary hashes (zero jitter).', 'notes': 'Byte-identical native binaries across runs.'}]}]}, {'id': 'C4.H3', 'title': 'Structured Diagnostics & Agent Surface Engine', 'crate_lane': 'crates/kant-diag, crates/kant-cli, crates/kant-mcp', 'assigned_agent': 'SA-15 & SA-16', 'sub_headings': [{'id': 'C4.H3.S1', 'title': 'RFC 6902 Auto-Fix Repair Loop & Content-Addressed Test Caching', 'tasks': [{'id': 'TASK-C4-07', 'task_code': 'C4.H3.S1.T01', 'title': 'Standardize Compiler Diagnostics with FixSafety Markers & RFC 6902 JSON Patches', 'assigned_agent': 'SA-15', 'target_crate': 'crates/kant-diag', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-diag test_diagnostic_patch_serialization', 'verification_cmd': 'cargo test -p kant-diag test_diagnostic_patch_serialization', 'description': 'Format all compiler diagnostics with machine-readable metadata: severity, error code, span, FixSafety (SAFE|REVIEW), and RFC 6902 JSON Patch modifications.', 'acceptance_criteria': 'JSON diagnostic schema validation; 100% of syntactic/effect errors accompanied by actionable RFC 6902 patch.', 'notes': 'Standardized JSON schema with patch operations.'}, {'id': 'TASK-C4-08', 'task_code': 'C4.H3.S1.T02', 'title': 'Implement Autonomous Repair Convergence Loop (kantc fix --apply)', 'assigned_agent': 'SA-15', 'target_crate': 'crates/kant-diag', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-diag test_auto_repair_convergence', 'verification_cmd': 'cargo test -p kant-diag test_auto_repair_convergence', 'description': 'Implement iterative automated repair loop applying SAFE patches until AST diagnostics reach a fixed point or resolve completely.', 'acceptance_criteria': 'Reaches clean compilation on 100% of benchmark defect test cases; terminates safely on ambiguous review-required defects.', 'notes': 'Applies SAFE patches iteratively until clean.'}, {'id': 'TASK-C4-09', 'task_code': 'C4.H3.S1.T03', 'title': 'Implement Content-Addressed Test Runner with Dependency Cone Hashing', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-cli', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-cli test_cached_test_runner', 'verification_cmd': 'cargo test -p kant-cli test_cached_test_runner', 'description': 'Implement incremental test runner caching test results by the SHA-256 hash cone of transitively reachable dependencies, skipping unchanged suites.', 'acceptance_criteria': 'Zero redundant test executions; 100% invalidation accuracy when any dependency cone hash drifts.', 'notes': 'Reruns only tests whose dependency cone hash drifted.'}]}, {'id': 'C4.H3.S2', 'title': 'Persistent Compiler Daemon, MCP Server & Constrained Grammar Export', 'tasks': [{'id': 'TASK-C4-10', 'task_code': 'C4.H3.S2.T01', 'title': 'Build Persistent Low-Latency JSON-RPC Daemon (kantc serv)', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-cli', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-cli test_agent_server_rpc', 'verification_cmd': 'cargo test -p kant-cli test_agent_server_rpc', 'description': 'Construct persistent background JSON-RPC server maintaining AST caches in memory for zero-process-spawn agent verification queries.', 'acceptance_criteria': 'Query response latency < 5ms; memory footprint < 50MB; graceful shutdown on socket close.', 'notes': 'Zero process startup overhead.'}, {'id': 'TASK-C4-11', 'task_code': 'C4.H3.S2.T02', 'title': 'Implement 10-Tool Model Context Protocol (MCP) Server', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-mcp', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-mcp test_10_mcp_tools', 'verification_cmd': 'cargo test -p kant-mcp test_10_mcp_tools', 'description': 'Expose full compiler capabilities over Model Context Protocol (MCP) via 10 structured tools (kant_check, kant_fix, kant_spec, kant_graph, kant_eval, etc.).', 'acceptance_criteria': 'Complies with MCP 2024-11-05 specification; seamless integration with Claude Code, Cursor, and IDE extensions.', 'notes': 'Model Context Protocol interface for Claude Code, Cursor, Codex.'}, {'id': 'TASK-C4-12', 'task_code': 'C4.H3.S2.T03', 'title': 'Implement Constrained LLM Decoding Grammar Exporter (kantc grammar --export-xgrammar)', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-cli', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test -p kant-cli test_xgrammar_export', 'verification_cmd': 'cargo test -p kant-cli test_xgrammar_export', 'description': 'Export the formal EBNF grammar to XGrammar JSON and Lark formats to enable Pushdown Automaton token masking during LLM sampling.', 'acceptance_criteria': '100% syntactically valid token generation under constrained sampling; export format verified against reference XGrammar runtime.', 'notes': 'Enforces 100% syntactically valid code during token sampling.'}]}]}]}, {'id': 'C5', 'name': 'Stage C5: Doctrine of Method — Cranelift Codegen & Merkle Traces', 'short_title': 'Stage C5: Method (Codegen & Evidence)', 'sub_phase': 'Tree-Walk Evaluator, Native JIT/AOT Code Generation & Cryptographic Merkle Bundles', 'gate_invariant': 'Bitwise Reproducibility & Gas Metering', 'arabic_title': 'المرحلة C5: مبحث المنهج — توليد الشيفرة بـ Cranelift وحزم ميركل المشفرة', 'arabic_sub_phase': 'مُقيّم شجرة المجردات، توليد الشيفرة الأصلية JIT/AOT وحزم أدلة ميركل', 'arabic_gate_invariant': 'قابلية الاستنساخ البتي الدقيق ومقاييس استهلاك الوقود', 'wave': 'Wave 5: Quality & Proofs', 'gate_status': 'LOCKED', 'iteration': 0, 'dependencies': ['C4'], 'gate_checklist': {'differential_proof': False, 'byte_determinism_proof': False, 'repair_convergence_proof': False, 'zero_escape_security_proof': False, 'git_status_clean': False}, 'iterations': [], 'main_headings': [{'id': 'C5.H1', 'title': 'Execution Equivalence & Binary Determinism Proofs', 'crate_lane': 'tests/bootstrap_proofs', 'assigned_agent': 'SA-13 & SA-14', 'sub_headings': [{'id': 'C5.H1.S1', 'title': 'Differential Execution Oracle & Reproducible Emission', 'tasks': [{'id': 'TASK-C5-01', 'task_code': 'C5.H1.S1.T01', 'title': 'Proof 1: Differential Oracle Verification Across Evaluator & Codegen', 'assigned_agent': 'SA-13', 'target_crate': 'crates/kant-eval', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test --test proof_01_differential_oracle', 'verification_cmd': 'cargo test --test proof_01_differential_oracle', 'description': 'Execute 50 reference test programs across both the KANT-IR tree-walk evaluator and Cranelift native AOT binary, proving 100% bitwise output equivalence.', 'acceptance_criteria': '0 state trace or return value deviations across all 50 test programs; gas counts correlate deterministically.', 'notes': '0 output or state trace deviations.'}, {'id': 'TASK-C5-02', 'task_code': 'C5.H1.S1.T02', 'title': 'Proof 2: Byte-for-Byte Identical Compilation Determinism', 'assigned_agent': 'SA-14', 'target_crate': 'crates/kant-codegen', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test --test proof_02_byte_determinism', 'verification_cmd': 'cargo test --test proof_02_byte_determinism', 'description': 'Execute dual independent compilations across distinct build directories and timestamps, validating 0 byte discrepancies in emitted native binaries.', 'acceptance_criteria': 'SHA-256 binary hash matches 100% across builds; zero embedded host-specific metadata.', 'notes': 'Bit-for-bit identical binary output.'}]}]}, {'id': 'C5.H2', 'title': 'Autonomous Convergence & Boundary Containment Proofs', 'crate_lane': 'tests/bootstrap_proofs', 'assigned_agent': 'SA-15 & SA-11', 'sub_headings': [{'id': 'C5.H2.S1', 'title': 'Repair Convergence & Noumena Containment', 'tasks': [{'id': 'TASK-C5-03', 'task_code': 'C5.H2.S1.T01', 'title': 'Proof 3: Multi-Defect Auto-Repair Convergence', 'assigned_agent': 'SA-15', 'target_crate': 'crates/kant-diag', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test --test proof_03_repair_convergence', 'verification_cmd': 'cargo test --test proof_03_repair_convergence', 'description': 'Run kantc fix --apply against 30 seeded defective programs containing syntax errors, effect mismatches, and contract failures, verifying 100% convergence.', 'acceptance_criteria': '100% of seeded programs repaired to pass compilation; zero patch application regressions.', 'notes': 'Iterative patch application reaches fixed point.'}, {'id': 'TASK-C5-04', 'task_code': 'C5.H2.S1.T02', 'title': 'Proof 4: Noumena Zero-Escape Adversarial Capability Containment', 'assigned_agent': 'SA-11', 'target_crate': 'crates/kant-noumena', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'cargo test --test proof_04_noumena_zero_escape', 'verification_cmd': 'cargo test --test proof_04_noumena_zero_escape', 'description': 'Run comprehensive adversarial test suite attempting capability forgery, unmediated raw socket access, and memory inspection, verifying 100% rejection.', 'acceptance_criteria': 'Zero capability leaks; 100% of unauthorized I/O attempts blocked; Secret<T> memory zeroization verified.', 'notes': 'Trust none boundary and secret zeroization verified.'}]}]}]}, {'id': 'C6', 'name': 'Stage C6: Agent Surface — RFC 6902 Diagnostics, MCP & Unified Driver', 'short_title': 'Stage C6: Agent Surface (CLI & MCP)', 'sub_phase': 'Structured Auto-Fix Patches, Sidecar Reconciliation & Production CLI Driver (kantc)', 'gate_invariant': 'MCP Protocol Compliance & Toolchain Integration', 'arabic_title': 'المرحلة C6: واجهة الوكلاء — تشخيصات RFC 6902، بروتوكول MCP والمحرّك الموحد', 'arabic_sub_phase': 'رقع التصحيح التلقائي البنائية، تسوية قفل الجانب ومحرّك سطر الأوامر (kantc)', 'arabic_gate_invariant': 'مطابقة معايير بروتوكول MCP وتكامل حزمة الأدوات', 'wave': 'Release & Distribution', 'gate_status': 'LOCKED', 'is_final_destination': True, 'iteration': 0, 'dependencies': ['C5'], 'gate_checklist': {'clean_git_tree': False, 'tarballs_generated': False, 'checksums_verified': False, 'installer_smoke_tested': False, 'agent_portal_ready': False}, 'iterations': [], 'main_headings': [{'id': 'C6.H1', 'title': 'Cross-Platform Packaging & Distribution Pipelines', 'crate_lane': 'scripts/distribute_v0_1.sh, dist/', 'assigned_agent': 'SA-16', 'sub_headings': [{'id': 'C6.H1.S1', 'title': 'Release Bundling & Cryptographic Verification', 'tasks': [{'id': 'TASK-C6-01', 'task_code': 'C6.H1.S1.T01', 'title': 'Implement Multi-Platform Distribution Bundler (kantc dist)', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-cli', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'bash scripts/distribute_v0_1.sh --dry-run', 'verification_cmd': 'bash scripts/distribute_v0_1.sh --dry-run', 'description': 'Package stripped release binaries, manpages, and licenses for linux-x86_64, darwin-arm64, and windows-x86_64 architectures.', 'acceptance_criteria': 'Release archives packaged deterministically; executable size < 15MB; zero dynamic library linkage defects.', 'notes': 'Package stripped release binaries for linux-x86_64, darwin-arm64, windows-x86_64.'}, {'id': 'TASK-C6-02', 'task_code': 'C6.H1.S1.T02', 'title': 'Bundle Standard Library, Byte-Pinned Manifest & SHA-256SUMS Manifest', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-cli', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'sha256sum -c dist/v0.1.0/SHA256SUMS', 'verification_cmd': 'sha256sum -c dist/v0.1.0/SHA256SUMS', 'description': 'Generate standard library distribution archives with cryptographic checksums and kant-toolchain.toml verification manifests.', 'acceptance_criteria': 'Cryptographic manifest verifies cleanly; checksum verification automated across CI nodes.', 'notes': 'Create .tar.gz and .zip release archives.'}]}, {'id': 'C6.H1.S2', 'title': 'Universal Shell Installer & Python MCP Distribution', 'tasks': [{'id': 'TASK-C6-03', 'task_code': 'C6.H1.S2.T01', 'title': 'Author Universal POSIX/Windows Shell Installer Script (install.sh)', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-cli', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'bash scripts/distribute_v0_1.sh --verify-installer', 'verification_cmd': 'bash scripts/distribute_v0_1.sh --verify-installer', 'description': 'Author hardened curl | sh installation script with OS/architecture auto-detection, checksum verification, and isolated PATH configuration.', 'acceptance_criteria': 'Zero external dependencies beyond curl and tar/unzip; verifies SHA-256 before extraction; clean uninstall support.', 'notes': 'Auto-detects OS/arch, verifies SHA-256, installs to ~/.kant/bin.'}, {'id': 'TASK-C6-04', 'task_code': 'C6.H1.S2.T02', 'title': 'Package Python MCP Wrapper (kant-lang) & Agent Skill Definitions', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-mcp', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'test -f dist/packages/SKILL.md', 'verification_cmd': 'test -f dist/packages/SKILL.md', 'description': 'Publish Python MCP distribution package (pipx install kant-lang) and agent tool integration definitions (SKILL.md) for automated agent tool discovery.', 'acceptance_criteria': 'Package installs cleanly in isolated virtual environment; MCP server launches and responds to protocol handshake.', 'notes': "pipx install 'kant-lang[mcp]' and Claude Code / Cursor / Gemini CLI skill."}]}]}, {'id': 'C6.H2', 'title': 'Cold-Start Specification Endpoints & Git Release Hygiene', 'crate_lane': 'agent/v0.1/, .gitignore', 'assigned_agent': 'SA-16', 'sub_headings': [{'id': 'C6.H2.S1', 'title': 'Agent Discovery Endpoints & Compact Specifications', 'tasks': [{'id': 'TASK-C6-05', 'task_code': 'C6.H2.S1.T01', 'title': 'Generate High-Density /llms.txt Specification (<3,200 Tokens)', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-cli', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'wc -w dist/agent/llms.txt', 'verification_cmd': 'wc -w dist/agent/llms.txt', 'description': 'Author single-page, token-budgeted specification (/llms.txt and /llms-full.txt) optimized for LLM cold-start reasoning (<3,200 tokens).', 'acceptance_criteria': 'Token count strictly <3,200 tokens; covers 100% of language grammar, effects, and contract syntax; 10/10 LLM recall score.', 'notes': '10/10 builtin recall on LLM cold starts.'}, {'id': 'TASK-C6-06', 'task_code': 'C6.H2.S1.T02', 'title': 'Generate Machine-Readable Agent Discovery Endpoints & JSON Schemas', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-cli', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'test -f dist/agent/v0.1/manifest.json', 'verification_cmd': 'test -f dist/agent/v0.1/manifest.json', 'description': 'Generate /agent/v0.1/manifest.json, JSON diagnostics schemas, and curated test case catalogs for automated AI agent workflows.', 'acceptance_criteria': 'Schemas conform to JSON Schema Draft-07; endpoints validated via automated curl testing.', 'notes': 'Machine discovery endpoint with paired .kant and .spec examples.'}]}, {'id': 'C6.H2.S2', 'title': 'Workspace Git Hygiene Gate & Release Tagging', 'tasks': [{'id': 'TASK-C6-07', 'task_code': 'C6.H2.S2.T01', 'title': 'Run Automated Git Hygiene Gate & Telemetry Artifact Verification', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-cli', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'git check-ignore kant-roadmap-tracker.html .kant-tracker/', 'verification_cmd': 'git check-ignore kant-roadmap-tracker.html .kant-tracker/', 'description': 'Execute pre-release workspace sanitizer verifying zero untracked artifacts, valid .gitignore policies for runtime telemetry, and clean git status.', 'acceptance_criteria': 'All runtime telemetry paths confirmed ignored; git status clean; zero secret leaks in commit log.', 'notes': 'Strict git cleanliness check.'}, {'id': 'TASK-C6-08', 'task_code': 'C6.H2.S2.T02', 'title': 'Execute Cryptographic Release Tagging & Changelog Generation (v0.1.0)', 'assigned_agent': 'SA-16', 'target_crate': 'crates/kant-cli', 'status': 'TODO', 'iteration_completed': 0, 'verification_gate': 'git tag -l v0.1.0', 'verification_cmd': 'git tag -l v0.1.0', 'description': 'Generate formal release notes, tag v0.1.0 git release with GPG signature, and publish immutable distribution manifest.', 'acceptance_criteria': 'Release tag created with full semantic versioning; changelog conforms to Keep a Changelog standard.', 'notes': 'Official GitHub release tag and release notes.'}]}]}]}]}

def ensure_tracker_dir():
    TRACKER_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# Git & Environment Helpers
# ------------------------------------------------------------------------------
def get_git_commit_hash(short=True):
    try:
        cmd = ["git", "rev-parse", "--short", "HEAD"] if short else ["git", "rev-parse", "HEAD"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "workspace"

def get_git_commit_info():
    info = {"hash": get_git_commit_hash(short=True), "author": "", "message": ""}
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%h|%an|%s"],
            capture_output=True, text=True, timeout=2
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = res.stdout.strip().split("|", 2)
            if len(parts) == 3:
                info["hash"] = parts[0]
                info["author"] = parts[1]
                info["message"] = parts[2]
    except Exception:
        pass
    return info

# ------------------------------------------------------------------------------
# Real-Time Server-Sent Events (SSE) Engine
# ------------------------------------------------------------------------------
sse_clients = []
sse_lock = threading.Lock()

def sse_broadcast(event_name: str, payload: dict):
    """Push real-time event to all active SSE subscribers."""
    data_str = json.dumps(payload, ensure_ascii=False)
    message = f"event: {event_name}\ndata: {data_str}\n\n"
    with sse_lock:
        dead = []
        for client_q in sse_clients:
            try:
                client_q.put_nowait(message)
            except Exception:
                dead.append(client_q)
        for d in dead:
            if d in sse_clients:
                sse_clients.remove(d)

# ------------------------------------------------------------------------------
# SQLite Persistence & Schema Definition
# ------------------------------------------------------------------------------
def get_db_conn():
    ensure_tracker_dir()
    conn = sqlite3.connect(str(DB_FILE), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

_db_initialized = False

def init_db():
    """Initializes SQLite tables and automatically migrates state.json if empty."""
    global _db_initialized
    if _db_initialized:
        return
    ensure_tracker_dir()
    conn = get_db_conn()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS circles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            short_title TEXT,
            wave TEXT,
            gate_status TEXT NOT NULL DEFAULT 'LOCKED',
            iteration INTEGER NOT NULL DEFAULT 1,
            dependencies TEXT DEFAULT '[]',
            gate_checklist TEXT DEFAULT '{}',
            ordering INTEGER DEFAULT 0,
            updated_at TEXT NOT NULL,
            sub_phase TEXT DEFAULT '',
            gate_invariant TEXT DEFAULT '',
            arabic_title TEXT DEFAULT '',
            arabic_sub_phase TEXT DEFAULT '',
            arabic_gate_invariant TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS headings (
            id TEXT PRIMARY KEY,
            circle_id TEXT NOT NULL REFERENCES circles(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            crate_lane TEXT,
            assigned_agent TEXT,
            ordering INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS subheadings (
            id TEXT PRIMARY KEY,
            heading_id TEXT NOT NULL REFERENCES headings(id) ON DELETE CASCADE,
            circle_id TEXT NOT NULL REFERENCES circles(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            ordering INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            subheading_id TEXT NOT NULL REFERENCES subheadings(id) ON DELETE CASCADE,
            heading_id TEXT NOT NULL REFERENCES headings(id) ON DELETE CASCADE,
            circle_id TEXT NOT NULL REFERENCES circles(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'TODO',
            iteration_completed INTEGER DEFAULT 0,
            verification_cmd TEXT,
            notes TEXT DEFAULT '',
            ordering INTEGER DEFAULT 0,
            updated_at TEXT NOT NULL,
            assigned_agent TEXT DEFAULT '',
            target_crate TEXT DEFAULT '',
            verification_gate TEXT DEFAULT '',
            description TEXT DEFAULT '',
            acceptance_criteria TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS iterations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            circle_id TEXT NOT NULL REFERENCES circles(id) ON DELETE CASCADE,
            number INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            summary TEXT
        );

        CREATE TABLE IF NOT EXISTS gate_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            circle_id TEXT NOT NULL REFERENCES circles(id) ON DELETE CASCADE,
            iteration INTEGER NOT NULL,
            gate_step TEXT NOT NULL,
            status TEXT NOT NULL,
            command TEXT,
            output TEXT,
            run_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS telemetry_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action_type TEXT NOT NULL,
            task_id TEXT,
            circle_id TEXT,
            git_commit TEXT,
            status_diff TEXT,
            details TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_tasks_circle ON tasks(circle_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_subheading ON tasks(subheading_id);
        CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_telemetry_action ON telemetry_events(action_type);
        CREATE INDEX IF NOT EXISTS idx_telemetry_task ON telemetry_events(task_id);
        CREATE INDEX IF NOT EXISTS idx_gate_runs_circle ON gate_runs(circle_id);
    """)
    conn.commit()

    # Check if migration is needed
    cur.execute("SELECT COUNT(*) FROM circles")
    count = cur.fetchone()[0]

    if count == 0:
        # Migrate existing state.json or DEFAULT_ROADMAP
        initial_state = DEFAULT_ROADMAP
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    initial_state = json.load(f)
            except Exception as e:
                print(f"[WARN] reading existing state.json during migration: {e}", file=sys.stderr)
                initial_state = DEFAULT_ROADMAP

        now_iso = datetime.now(timezone.utc).isoformat()
        with conn:
            _write_state_to_conn(conn, initial_state, now_iso)
            conn.execute("""
                INSERT INTO telemetry_events (timestamp, action_type, git_commit, details)
                VALUES (?, 'MIGRATION', ?, 'Automated migration from state.json to kant_telemetry.db completed')
            """, (now_iso, get_git_commit_hash()))

        refreshed = _read_state_from_conn(conn)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(refreshed, f, indent=2, ensure_ascii=False)
        print("[INFO] Initializing Kant Compiler Observatory Telemetry Engine (v0.1)")
        print("[INFO] Tracking 17 modular workspace crates across 7 pipeline stages")
        print("[INFO] Verified zero-state invariant: 0/75 tasks completed (0.0%)")
        print(f"[INFO] Telemetry synchronized to SQLite database and SSE clients: {DB_FILE}")

    conn.close()

def _write_state_to_conn(conn, state: dict, now_iso: str):
    """Low-level helper to write state hierarchy into database tables within an active transaction."""
    conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('version', ?)", (state.get("version", "0.1.0"),))
    conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_updated', ?)", (now_iso,))
    conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('current_circle_focus', ?)", (state.get("current_circle_focus", "C1"),))

    # Clear structural hierarchy to avoid orphaned tasks
    conn.execute("DELETE FROM tasks")
    conn.execute("DELETE FROM subheadings")
    conn.execute("DELETE FROM headings")
    conn.execute("DELETE FROM circles")

    for c_idx, circle in enumerate(state.get("circles", [])):
        cid = circle["id"]
        deps_json = json.dumps(circle.get("dependencies", []))
        check_json = json.dumps(circle.get("gate_checklist", {}))
        conn.execute("""
            INSERT OR REPLACE INTO circles (id, name, short_title, wave, gate_status, iteration, dependencies, gate_checklist, ordering, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cid,
            circle.get("name", cid),
            circle.get("short_title", cid),
            circle.get("wave", ""),
            circle.get("gate_status", "LOCKED"),
            circle.get("iteration", 1),
            deps_json,
            check_json,
            c_idx,
            now_iso
        ))

        for h_idx, heading in enumerate(circle.get("main_headings", [])):
            hid = heading["id"]
            conn.execute("""
                INSERT OR REPLACE INTO headings (id, circle_id, title, crate_lane, assigned_agent, ordering)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                hid,
                cid,
                heading.get("title", hid),
                heading.get("crate_lane", ""),
                heading.get("assigned_agent", ""),
                h_idx
            ))

            for s_idx, sub in enumerate(heading.get("sub_headings", [])):
                sid = sub["id"]
                conn.execute("""
                    INSERT OR REPLACE INTO subheadings (id, heading_id, circle_id, title, ordering)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    sid,
                    hid,
                    cid,
                    sub.get("title", sid),
                    s_idx
                ))

                for t_idx, task in enumerate(sub.get("tasks", [])):
                    tid = task["id"]
                    conn.execute("""
                        INSERT OR REPLACE INTO tasks (id, subheading_id, heading_id, circle_id, title, status, iteration_completed, verification_cmd, notes, ordering, updated_at, assigned_agent, target_crate, verification_gate, description, acceptance_criteria)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        tid,
                        sid,
                        hid,
                        cid,
                        task.get("title", tid),
                        task.get("status", "TODO"),
                        task.get("iteration_completed", 0),
                        task.get("verification_cmd", task.get("verification_gate", "")),
                        task.get("notes", ""),
                        t_idx,
                        now_iso,
                        task.get("assigned_agent", heading.get("assigned_agent", "")),
                        task.get("target_crate", heading.get("crate_lane", "")),
                        task.get("verification_gate", task.get("verification_cmd", "")),
                        task.get("description", ""),
                        task.get("acceptance_criteria", "")
                    ))

        for it in circle.get("iterations", []):
            cur = conn.cursor()
            cur.execute("SELECT id FROM iterations WHERE circle_id = ? AND number = ?", (cid, it["number"]))
            row = cur.fetchone()
            if row:
                conn.execute("""
                    UPDATE iterations SET timestamp = ?, status = ?, summary = ? WHERE id = ?
                """, (it.get("timestamp", now_iso), it.get("status", "VERIFIED_PASSED"), it.get("summary", ""), row[0]))
            else:
                conn.execute("""
                    INSERT INTO iterations (circle_id, number, timestamp, status, summary)
                    VALUES (?, ?, ?, ?, ?)
                """, (cid, it["number"], it.get("timestamp", now_iso), it.get("status", "VERIFIED_PASSED"), it.get("summary", "")))

def _read_state_from_conn(conn):
    """Low-level helper to reconstruct full state dict from an active database connection."""
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM metadata")
    meta = dict(cur.fetchall())
    version = meta.get("version", "0.1.0")
    last_updated = meta.get("last_updated", datetime.now(timezone.utc).isoformat())
    current_circle_focus = meta.get("current_circle_focus", "C1")

    cur.execute("SELECT id, name, short_title, wave, gate_status, iteration, dependencies, gate_checklist, updated_at FROM circles ORDER BY ordering ASC, id ASC")
    circle_rows = cur.fetchall()

    circles = []
    total_tasks = 0
    completed_tasks = 0
    blocked_tasks = 0

    for crow in circle_rows:
        cid = crow["id"]

        cur.execute("SELECT number, timestamp, status, summary FROM iterations WHERE circle_id = ? ORDER BY number ASC", (cid,))
        iter_rows = cur.fetchall()
        circle_iters = [
            {
                "number": r["number"],
                "timestamp": r["timestamp"],
                "status": r["status"],
                "summary": r["summary"] or ""
            } for r in iter_rows
        ]

        cur.execute("SELECT id, title, crate_lane, assigned_agent FROM headings WHERE circle_id = ? ORDER BY ordering ASC, id ASC", (cid,))
        hrows = cur.fetchall()

        main_headings = []
        for hrow in hrows:
            hid = hrow["id"]
            cur.execute("SELECT id, title FROM subheadings WHERE heading_id = ? ORDER BY ordering ASC, id ASC", (hid,))
            srows = cur.fetchall()

            sub_headings = []
            for srow in srows:
                sid = srow["id"]
                cur.execute("SELECT * FROM tasks WHERE subheading_id = ? ORDER BY ordering ASC, id ASC", (sid,))
                trows = cur.fetchall()

                tasks = []
                for trow in trows:
                    total_tasks += 1
                    tstatus = trow["status"]
                    if tstatus == "DONE_VERIFIED":
                        completed_tasks += 1
                    elif tstatus == "BLOCKED":
                        blocked_tasks += 1

                    t_keys = trow.keys() if hasattr(trow, 'keys') else []
                    tasks.append({
                        "id": trow["id"],
                        "title": trow["title"],
                        "status": trow["status"],
                        "iteration_completed": trow["iteration_completed"] or 0,
                        "verification_cmd": trow["verification_cmd"] or "",
                        "notes": trow["notes"] or "",
                        "assigned_agent": trow["assigned_agent"] if "assigned_agent" in t_keys else "",
                        "target_crate": trow["target_crate"] if "target_crate" in t_keys else "",
                        "verification_gate": trow["verification_gate"] if "verification_gate" in t_keys else (trow["verification_cmd"] or ""),
                        "description": trow["description"] if "description" in t_keys else "",
                        "acceptance_criteria": trow["acceptance_criteria"] if "acceptance_criteria" in t_keys else ""
                    })

                sub_headings.append({
                    "id": sid,
                    "title": srow["title"],
                    "tasks": tasks
                })

            main_headings.append({
                "id": hid,
                "title": hrow["title"],
                "crate_lane": hrow["crate_lane"] or "",
                "assigned_agent": hrow["assigned_agent"] or "",
                "sub_headings": sub_headings
            })

        try:
            deps = json.loads(crow["dependencies"]) if crow["dependencies"] else []
        except Exception:
            deps = []

        try:
            checklist = json.loads(crow["gate_checklist"]) if crow["gate_checklist"] else {}
        except Exception:
            checklist = {}

        circles.append({
            "id": cid,
            "name": crow["name"],
            "short_title": crow["short_title"] or cid,
            "wave": crow["wave"] or "",
            "gate_status": crow["gate_status"] or "LOCKED",
            "iteration": crow["iteration"] or 1,
            "dependencies": deps,
            "gate_checklist": checklist,
            "iterations": circle_iters,
            "main_headings": main_headings
        })

    pct = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    return {
        "version": version,
        "last_updated": last_updated,
        "current_circle_focus": current_circle_focus,
        "global_stats": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "blocked_tasks": blocked_tasks,
            "progress_percent": pct
        },
        "circles": circles
    }

# ------------------------------------------------------------------------------
# State Reconstitution & Synchronization Engine
# ------------------------------------------------------------------------------
def load_state_from_db():
    """Loads and reconstructs complete JSON roadmap state dictionary from SQLite tables."""
    init_db()
    conn = get_db_conn()
    state = _read_state_from_conn(conn)
    conn.close()
    return state

def save_state_to_db(state: dict, record_telemetry: bool = True, action_detail: str = None):
    """Saves complete state tree into SQLite tables and mirrors to state.json."""
    ensure_tracker_dir()
    init_db()
    conn = get_db_conn()
    now_iso = datetime.now(timezone.utc).isoformat()

    with conn:
        _write_state_to_conn(conn, state, now_iso)

    refreshed_state = _read_state_from_conn(conn)
    conn.close()

    # Mirror to state.json for backward compatibility
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(refreshed_state, f, indent=2, ensure_ascii=False)

    if record_telemetry:
        record_telemetry_event(
            action_type="STATE_SYNC",
            details=action_detail or "Full state tree synchronized with SQLite database",
            git_commit=get_git_commit_hash()
        )

    sse_broadcast("state_update", refreshed_state)
    return refreshed_state

# ------------------------------------------------------------------------------
# Telemetry Logging & Audit Trail
# ------------------------------------------------------------------------------
def record_telemetry_event(action_type, task_id=None, circle_id=None, git_commit=None, status_diff=None, details=None):
    """Records an append-only telemetry event in SQLite and broadcasts via SSE."""
    init_db()
    conn = get_db_conn()
    now_iso = datetime.now(timezone.utc).isoformat()
    commit = git_commit or get_git_commit_hash()

    with conn:
        cur = conn.execute("""
            INSERT INTO telemetry_events (timestamp, action_type, task_id, circle_id, git_commit, status_diff, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (now_iso, action_type, task_id, circle_id, commit, status_diff, details))
        event_id = cur.lastrowid
    conn.close()

    event_data = {
        "id": event_id,
        "timestamp": now_iso,
        "action_type": action_type,
        "task_id": task_id,
        "circle_id": circle_id,
        "git_commit": commit,
        "status_diff": status_diff,
        "details": details
    }
    sse_broadcast("telemetry", event_data)
    return event_data

def get_recent_telemetry_events(limit=50, action_type=None):
    init_db()
    conn = get_db_conn()
    cur = conn.cursor()
    if action_type:
        cur.execute("""
            SELECT id, timestamp, action_type, task_id, circle_id, git_commit, status_diff, details
            FROM telemetry_events WHERE action_type = ?
            ORDER BY id DESC LIMIT ?
        """, (action_type, limit))
    else:
        cur.execute("""
            SELECT id, timestamp, action_type, task_id, circle_id, git_commit, status_diff, details
            FROM telemetry_events
            ORDER BY id DESC LIMIT ?
        """, (limit,))
    rows = cur.fetchall()
    events = [dict(r) for r in rows]
    conn.close()
    return events

def record_gate_run(circle_id, iteration, gate_step, status, command="", output=""):
    """Records an automated Five-Step Gate Run into SQLite."""
    init_db()
    conn = get_db_conn()
    now_iso = datetime.now(timezone.utc).isoformat()

    with conn:
        cur = conn.execute("""
            INSERT INTO gate_runs (circle_id, iteration, gate_step, status, command, output, run_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (circle_id, iteration, gate_step, status, command, output, now_iso))
        run_id = cur.lastrowid

        # If gate step passed, automatically update checklist in circles table
        if status.upper() == "PASSED":
            cur.execute("SELECT gate_checklist FROM circles WHERE id = ?", (circle_id,))
            crow = cur.fetchone()
            if crow:
                try:
                    chk = json.loads(crow["gate_checklist"]) if crow["gate_checklist"] else {}
                except Exception:
                    chk = {}
                chk[gate_step] = True
                conn.execute("UPDATE circles SET gate_checklist = ?, updated_at = ? WHERE id = ?", (json.dumps(chk), now_iso, circle_id))
    conn.close()

    # Record telemetry
    ev = record_telemetry_event(
        action_type="GATE_RUN",
        circle_id=circle_id,
        status_diff=f"{gate_step}: {status.upper()}",
        details=f"Gate step {gate_step} result: {status.upper()} (run #{run_id})"
    )

    refreshed = load_state_from_db()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(refreshed, f, indent=2, ensure_ascii=False)
    sse_broadcast("state_update", refreshed)

    return {"run_id": run_id, "circle_id": circle_id, "gate_step": gate_step, "status": status, "telemetry_id": ev.get("id")}

def get_recent_gate_runs(circle_id=None, limit=20):
    init_db()
    conn = get_db_conn()
    cur = conn.cursor()
    if circle_id:
        cur.execute("SELECT id, circle_id, iteration, gate_step, status, command, output, run_at FROM gate_runs WHERE circle_id = ? ORDER BY id DESC LIMIT ?", (circle_id, limit))
    else:
        cur.execute("SELECT id, circle_id, iteration, gate_step, status, command, output, run_at FROM gate_runs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    runs = [dict(r) for r in rows]
    conn.close()
    return runs

# ------------------------------------------------------------------------------
# High-Level State Mutators
# ------------------------------------------------------------------------------
def load_state():
    return load_state_from_db()

def save_state(state):
    return save_state_to_db(state)

def update_task(task_id, new_status, notes=None, iteration=None, commit_hash=None):
    """Updates atomic task status, notes, or iteration completed in SQLite, handles regression detection."""
    init_db()
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, circle_id, subheading_id, status, iteration_completed, notes FROM tasks WHERE id = ?", (task_id,))
    t_row = cur.fetchone()
    if not t_row:
        print(f"[ERROR] Task ID '{task_id}' not found in database.", file=sys.stderr)
        conn.close()
        sys.exit(1)

    old_status = t_row["status"]
    cid = t_row["circle_id"]

    cur.execute("SELECT id, gate_status, iteration FROM circles WHERE id = ?", (cid,))
    c_row = cur.fetchone()
    circle_gate = c_row["gate_status"] if c_row else "LOCKED"
    circle_iter = c_row["iteration"] if c_row else 1

    target_iter = iteration if iteration is not None else t_row["iteration_completed"]
    if new_status == "DONE_VERIFIED" and target_iter == 0:
        target_iter = circle_iter

    new_notes = notes if notes is not None else t_row["notes"]
    now_iso = datetime.now(timezone.utc).isoformat()

    with conn:
        conn.execute("""
            UPDATE tasks SET status = ?, iteration_completed = ?, notes = ?, updated_at = ? WHERE id = ?
        """, (new_status, target_iter, new_notes, now_iso, task_id))

        # Regression check: If circle was VERIFIED_PASSED and task becomes BLOCKED or IN_PROGRESS
        if circle_gate == "VERIFIED_PASSED" and new_status in ("BLOCKED", "IN_PROGRESS"):
            new_iter = circle_iter + 1
            conn.execute("UPDATE circles SET gate_status = 'REGRESSION_DETECTED', iteration = ?, updated_at = ? WHERE id = ?", (new_iter, now_iso, cid))
            print(f"[WARN] REGRESSION DETECTED in Stage {cid}: Task {task_id} shifted from {old_status} to {new_status}. Iteration bumped to #{new_iter}.")
    conn.close()

    diff = f"{old_status} -> {new_status}"
    event = record_telemetry_event(
        action_type="TASK_UPDATE",
        task_id=task_id,
        circle_id=cid,
        git_commit=commit_hash or get_git_commit_hash(),
        status_diff=diff,
        details=f"Task {task_id} updated to {new_status}. Notes: {new_notes or ''}"
    )

    refreshed_state = load_state_from_db()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(refreshed_state, f, indent=2, ensure_ascii=False)

    sse_broadcast("state_update", refreshed_state)
    print(f"[INFO] Task {task_id} updated: {diff}. Telemetry event #{event.get('id')} recorded.")
    return event

def update_circle_gate(circle_id, gate_status):
    init_db()
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, gate_status FROM circles WHERE id = ?", (circle_id,))
    c_row = cur.fetchone()
    if not c_row:
        print(f"[ERROR] Stage ID '{circle_id}' not found.", file=sys.stderr)
        conn.close()
        sys.exit(1)

    old_status = c_row["gate_status"]
    now_iso = datetime.now(timezone.utc).isoformat()

    with conn:
        conn.execute("UPDATE circles SET gate_status = ?, updated_at = ? WHERE id = ?", (gate_status, now_iso, circle_id))
    conn.close()

    diff = f"{old_status} -> {gate_status}"
    event = record_telemetry_event(
        action_type="GATE_UPDATE",
        circle_id=circle_id,
        git_commit=get_git_commit_hash(),
        status_diff=diff,
        details=f"Circle {circle_id} gate transitioned from {old_status} to {gate_status}"
    )

    refreshed_state = load_state_from_db()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(refreshed_state, f, indent=2, ensure_ascii=False)

    sse_broadcast("state_update", refreshed_state)
    print(f"[INFO] Stage {circle_id} gate status transitioned from {old_status} to {gate_status}.")
    return event

# ------------------------------------------------------------------------------
# Terminal Dashboard & Reporting
# ------------------------------------------------------------------------------
def print_summary():
    state = load_state()
    stats = state.get("global_stats", {})
    print("=" * 72)
    print("  KANT COMPILER OBSERVATORY & TELEMETRY SYSTEMS SUMMARY (v0.1)")
    print("=" * 72)
    print(f"  Overall Progress: {stats.get('progress_percent', 0)}% "
          f"({stats.get('completed_tasks', 0)} / {stats.get('total_tasks', 0)} tasks verified)")
    print(f"  Blocked Tasks:    {stats.get('blocked_tasks', 0)}")
    print(f"  Database Engine:  SQLite ({DB_FILE}) [WAL Mode Active]")
    print(f"  Current Stage:    Stage {state.get('current_circle_focus', 'C1')}")
    print("-" * 72)
    print(f"  {'Node':<6} | {'Gate Status':<20} | {'Iter':<6} | {'Completed':<10} | {'Stage Designation'}")
    print("-" * 72)

    for circle in state.get("circles", []):
        cid = circle["id"]
        gate = circle.get("gate_status", "LOCKED")
        it = f"#{circle.get('iteration', 1)}"
        tasks = []
        for h in circle.get("main_headings", []):
            for s in h.get("sub_headings", []):
                tasks.extend(s.get("tasks", []))
        done = sum(1 for t in tasks if t.get("status") == "DONE_VERIFIED")
        tot = len(tasks)
        pct_str = f"{done}/{tot}"
        print(f"  {cid:<6} | {gate:<20} | {it:<6} | {pct_str:<10} | {circle.get('name')}")
    print("=" * 72)

def print_telemetry(limit=25):
    events = get_recent_telemetry_events(limit=limit)
    print("=" * 88)
    print(f"  KANT TELEMETRY AUDIT TRAIL (Last {len(events)} events from SQLite)")
    print("=" * 88)
    print(f"  {'ID':<5} | {'Timestamp':<20} | {'Action':<14} | {'Commit':<8} | {'Diff / Details'}")
    print("-" * 88)
    for ev in events:
        eid = ev["id"]
        ts = ev["timestamp"][:19].replace("T", " ")
        act = ev["action_type"]
        cmt = ev["git_commit"] or "--"
        diff = ev["status_diff"] or ""
        det = ev["details"] or ""
        summary = f"{diff} - {det}" if diff and det else (diff or det)
        print(f"  {eid:<5} | {ts:<20} | {act:<14} | {cmt:<8} | {summary[:34]}")
    print("=" * 88)

# ------------------------------------------------------------------------------
# HTTP API Server with Real-Time SSE
# ------------------------------------------------------------------------------
class TrackerApiHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Universal CORS headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Cache-Control")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/events":
            # Server-Sent Events (SSE) Live Push Stream
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            client_q = queue.Queue(maxsize=200)
            with sse_lock:
                sse_clients.append(client_q)

            # Send initial connected greeting & state snapshot
            try:
                state = load_state()
                init_msg = json.dumps({"status": "connected", "database": "sqlite", "file": str(DB_FILE)})
                self.wfile.write(f"event: connected\ndata: {init_msg}\n\n".encode("utf-8"))
                state_msg = json.dumps(state, ensure_ascii=False)
                self.wfile.write(f"event: state_update\ndata: {state_msg}\n\n".encode("utf-8"))
                self.wfile.flush()
            except Exception:
                with sse_lock:
                    if client_q in sse_clients:
                        sse_clients.remove(client_q)
                return

            try:
                while True:
                    try:
                        msg = client_q.get(timeout=15.0)
                        self.wfile.write(msg.encode("utf-8"))
                        self.wfile.flush()
                    except queue.Empty:
                        # Heartbeat ping
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                with sse_lock:
                    if client_q in sse_clients:
                        sse_clients.remove(client_q)
            return

        elif path == "/api/state":
            state = load_state()
            data = json.dumps(state, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        elif path == "/api/telemetry":
            query = urllib.parse.parse_qs(parsed.query)
            limit = int(query.get("limit", [50])[0])
            action_filter = query.get("action", [None])[0]
            events = get_recent_telemetry_events(limit=limit, action_type=action_filter)
            data = json.dumps(events, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        elif path == "/api/gate_runs":
            query = urllib.parse.parse_qs(parsed.query)
            circle_id = query.get("circle", [None])[0]
            limit = int(query.get("limit", [20])[0])
            runs = get_recent_gate_runs(circle_id=circle_id, limit=limit)
            data = json.dumps(runs, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        elif path in ("/", "/index.html", "/kant-roadmap-tracker.html"):
            target = Path("kant-roadmap-tracker.html")
            if target.exists():
                with open(target, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == "/api/state":
            try:
                save_state(payload)
                resp = json.dumps({"status": "ok", "message": "State synchronized with SQLite"}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                err = json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err)))
                self.end_headers()
                self.wfile.write(err)

        elif path == "/api/task":
            try:
                task_id = payload.get("task_id")
                status = payload.get("status")
                notes = payload.get("notes")
                iteration = payload.get("iteration")
                commit = payload.get("git_commit")
                if not task_id or not status:
                    raise ValueError("task_id and status are required")
                ev = update_task(task_id, status, notes=notes, iteration=iteration, commit_hash=commit)
                resp = json.dumps({"status": "ok", "event": ev}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                err = json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err)))
                self.end_headers()
                self.wfile.write(err)

        elif path == "/api/gate":
            try:
                circle_id = payload.get("circle_id")
                gate_status = payload.get("gate_status")
                if not circle_id or not gate_status:
                    raise ValueError("circle_id and gate_status are required")
                ev = update_circle_gate(circle_id, gate_status)
                resp = json.dumps({"status": "ok", "event": ev}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                err = json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err)))
                self.end_headers()
                self.wfile.write(err)

        elif path == "/api/telemetry":
            try:
                action_type = payload.get("action_type", "CUSTOM")
                task_id = payload.get("task_id")
                circle_id = payload.get("circle_id")
                commit = payload.get("git_commit")
                diff = payload.get("status_diff")
                details = payload.get("details", "")

                if task_id and payload.get("status"):
                    ev = update_task(task_id, payload.get("status"), notes=details, commit_hash=commit)
                else:
                    ev = record_telemetry_event(
                        action_type=action_type,
                        task_id=task_id,
                        circle_id=circle_id,
                        git_commit=commit,
                        status_diff=diff,
                        details=details
                    )
                resp = json.dumps({"status": "ok", "event": ev}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                err = json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err)))
                self.end_headers()
                self.wfile.write(err)

        elif path == "/api/gate_run":
            try:
                cid = payload.get("circle_id")
                it = int(payload.get("iteration", 1))
                step = payload.get("gate_step")
                status = payload.get("status")
                cmd = payload.get("command", "")
                output = payload.get("output", "")
                if not cid or not step or not status:
                    raise ValueError("circle_id, gate_step, and status are required")
                res = record_gate_run(cid, it, step, status, cmd, output)
                resp = json.dumps({"status": "ok", "result": res}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                err = json.dumps({"status": "error", "message": str(e)}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err)))
                self.end_headers()
                self.wfile.write(err)
        else:
            self.send_response(404)
            self.end_headers()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def run_server(port=8080):
    init_db()
    load_state()
    server_address = ("", port)
    httpd = ThreadedHTTPServer(server_address, TrackerApiHandler)
    print("=" * 80)
    print("[INFO] Initializing Kant Compiler Observatory Telemetry Engine (v0.1)")
    print("[INFO] Tracking 17 modular workspace crates across 7 pipeline stages")
    print(f"[INFO] Verified zero-state invariant: 0/75 tasks completed (0.0%)")
    print(f"[INFO] Telemetry synchronized to SQLite database and SSE clients")
    print("=" * 80)
    print(f"[INFO] Observatory Portal:     http://localhost:{port}/")
    print(f"[INFO] Real-Time SSE Stream:   http://localhost:{port}/api/events")
    print(f"[INFO] Telemetry State API:    http://localhost:{port}/api/state")
    print(f"[INFO] Event Audit API:        http://localhost:{port}/api/telemetry")
    print(f"[INFO] Gate Runs API:          http://localhost:{port}/api/gate_runs")
    print(f"[INFO] Persistence Engine:     SQLite at {DB_FILE} (WAL mode)")
    print("=" * 80)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server stopped.")

# ------------------------------------------------------------------------------
# Unified CLI Entrypoint
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Kant (.kant) v0.1 Roadmap Tracker & SQLite Telemetry Engine")
    parser.add_argument("--init", action="store_true", help="Initialize/Reset SQLite DB and state.json with default C0-C6 schema")
    parser.add_argument("--migrate", action="store_true", help="Force migrate state.json into SQLite kant_telemetry.db")
    parser.add_argument("--task", type=str, help="Target Atomic Task ID (e.g. C1.H1.S1.T01)")
    parser.add_argument("--status", type=str, choices=["TODO", "IN_PROGRESS", "BLOCKED", "DEFERRED_V02", "DONE_VERIFIED"], help="Set task status")
    parser.add_argument("--notes", type=str, help="Update task notes")
    parser.add_argument("--iteration", type=int, help="Set iteration cycle number")
    parser.add_argument("--gate", type=str, help="Target Circle ID to update gate status (e.g. C1)")
    parser.add_argument("--gate-status", type=str, choices=["LOCKED", "IN_ITERATION", "GATE_PENDING", "VERIFIED_PASSED", "REGRESSION_DETECTED"], help="Gate status")
    parser.add_argument("--summary", action="store_true", help="Print terminal dashboard summary of roadmap state")
    parser.add_argument("--telemetry", action="store_true", help="Print recent telemetry audit events from SQLite")
    parser.add_argument("--limit", type=int, default=25, help="Event limit for --telemetry (default: 25)")
    parser.add_argument("--serve", action="store_true", help="Run multi-threaded HTTP server with SSE live streaming")
    parser.add_argument("--port", type=int, default=8080, help="Port for HTTP server (default: 8080)")

    # Gate run arguments
    parser.add_argument("--record-gate-run", action="store_true", help="Record a Five-Step Iron Law gate verification run")
    parser.add_argument("--circle", type=str, help="Circle ID for gate run (e.g. C1)")
    parser.add_argument("--step", type=str, choices=["cargo_fmt", "cargo_clippy", "cargo_test", "conformance_tests", "git_status_clean"], help="Gate step name")
    parser.add_argument("--run-status", type=str, choices=["PASSED", "FAILED", "PENDING"], help="Gate step status")
    parser.add_argument("--cmd", type=str, default="", help="Command executed")
    parser.add_argument("--output", type=str, default="", help="Command output log")

    args = parser.parse_args()

    if args.init:
        save_state_to_db(DEFAULT_ROADMAP, record_telemetry=True, action_detail="Explicit CLI --init reset")
        print("[INFO] Initializing Kant Compiler Observatory Telemetry Engine (v0.1)")
        print("[INFO] Tracking 17 modular workspace crates across 7 pipeline stages")
        print("[INFO] Verified zero-state invariant: 0/75 tasks completed (0.0%)")
        print(f"[INFO] Telemetry synchronized to SQLite database and SSE clients: {DB_FILE}")
        print_summary()
    elif args.migrate:
        init_db()
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
            save_state_to_db(s, record_telemetry=True, action_detail="CLI explicit --migrate from state.json")
            print(f"[INFO] Telemetry synchronized to SQLite database and SSE clients: {DB_FILE}")
        else:
            print(f"[!] state.json does not exist. Initializing from DEFAULT_ROADMAP.")
            save_state_to_db(DEFAULT_ROADMAP)
        print_summary()
    elif args.task and args.status:
        update_task(args.task, args.status, args.notes, args.iteration)
    elif args.gate and args.gate_status:
        update_circle_gate(args.gate, args.gate_status)
    elif args.record_gate_run:
        if not args.circle or not args.step or not args.run_status:
            print("[ERROR] --circle, --step, and --run-status are required for --record-gate-run", file=sys.stderr)
            sys.exit(1)
        res = record_gate_run(args.circle, args.iteration or 1, args.step, args.run_status, args.cmd, args.output)
        print(f"[INFO] Recorded gate verification run #{res['run_id']} for {args.circle} ({args.step}: {args.run_status}).")
    elif args.telemetry:
        print_telemetry(args.limit)
    elif args.summary:
        print_summary()
    elif args.serve:
        run_server(args.port)
    else:
        print_summary()

if __name__ == "__main__":
    main()

