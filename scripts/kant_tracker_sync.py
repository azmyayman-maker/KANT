#!/usr/bin/env python3
"""
kant_tracker_sync.py: SQLite-backed Telemetry Engine & Live SSE Server for Kant (.kant) v0.1 Roadmap Tracker.
Provides SQLite database persistence at .kant-tracker/kant_telemetry.db, backward-compatible state.json sync,
real-time Server-Sent Events (SSE) streaming, gate verification audit logging, and CLI commands.
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

DEFAULT_ROADMAP = {
    "version": "0.1.0",
    "last_updated": "2026-11-06T14:30:00Z",
    "current_circle_focus": "C1",
    "global_stats": {
        "total_tasks": 54,
        "completed_tasks": 12,
        "blocked_tasks": 0,
        "progress_percent": 22.2
    },
    "circles": [
        {
            "id": "C0",
            "name": "Epistemological Pinning & Clarification Gate",
            "short_title": "Epistemic Foundation",
            "wave": "Pre-Wave Foundation",
            "gate_status": "VERIFIED_PASSED",
            "iteration": 1,
            "dependencies": [],
            "gate_checklist": {
                "spec_pinning": True,
                "lexicon_mapping": True,
                "clarification_triage": True,
                "toolchain_hashes": True,
                "git_lane_hygiene": True
            },
            "iterations": [
                {
                    "number": 1,
                    "timestamp": "2026-11-06T14:17:00Z",
                    "status": "VERIFIED_PASSED",
                    "summary": "Pinned 8 reference .md documents and toolchain SHA-256 hashes. Triaged 32 questions with pragmatic deferrals."
                }
            ],
            "main_headings": [
                {
                    "id": "C0.H1",
                    "title": "Reference .md Architecture & Toolchain Hash Pinning",
                    "crate_lane": "Cargo.toml, AGENTS.md, docs/spec/",
                    "assigned_agent": "SA-01",
                    "sub_headings": [
                        {
                            "id": "C0.H1.S1",
                            "title": "Root Constitution & Lexicon (AGENTS.md & 01_EPISTEMOLOGY.md)",
                            "tasks": [
                                {
                                    "id": "C0.H1.S1.T01",
                                    "title": "Author AGENTS.md (<350 lines) with 16 isolated file lanes & 5-step verification law",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "git status --porcelain AGENTS.md",
                                    "notes": "Verified <350 lines, lanes SA-01 to SA-16 defined."
                                },
                                {
                                    "id": "C0.H1.S1.T02",
                                    "title": "Define Moussa Wehbe terminology mapping (mujauz, afhoum, shaym, noumenon, amthoul)",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "test -f docs/spec/01_EPISTEMOLOGY_AND_LEXICON.md",
                                    "notes": "Philological dictionary and Martin-Löf constructive type theory mapping verified."
                                },
                                {
                                    "id": "C0.H1.S1.T03",
                                    "title": "Enforce namespace isolation (kantc binary, kant-lang-* packages, #![kant(v0.1)] header)",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "grep '#!\\[kant(v0.1)\\]' AGENTS.md",
                                    "notes": "Disambiguated from legacy CAS, Langium DSL, and crates.io micro-crates."
                                }
                            ]
                        },
                        {
                            "id": "C0.H1.S2",
                            "title": "Deep Specification Suite (02–07 .md files & kant-toolchain.toml)",
                            "tasks": [
                                {
                                    "id": "C0.H1.S2.T01",
                                    "title": "Author 02_AESTHETICS_GRAMMAR_AND_AST.md (EBNF, De Bruijn indices, and SHA-256 identity)",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "test -f docs/spec/02_AESTHETICS_GRAMMAR_AND_AST.md",
                                    "notes": "Flattened toplevel EBNF and 5 canonicalization rules locked."
                                },
                                {
                                    "id": "C0.H1.S2.T02",
                                    "title": "Author 03_ANALYTIC_CATEGORIES_AND_EFFECTS.md (12 Categories + Exact Effect Matching)",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "test -f docs/spec/03_ANALYTIC_CATEGORIES_AND_EFFECTS.md",
                                    "notes": "Quantity, Quality, Relation, Modality triads and Sigil Law formalized."
                                },
                                {
                                    "id": "C0.H1.S2.T03",
                                    "title": "Author 04_SCHEMATISM_IR_AND_PERCEUS.md (30 SSA ops, directed time category & Perceus)",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "test -f docs/spec/04_SCHEMATISM_IR_AND_PERCEUS.md",
                                    "notes": "30 KANT-IR ops, frame-limited Alloc@r reuse tokens, cycle-free arena design."
                                },
                                {
                                    "id": "C0.H1.S2.T04",
                                    "title": "Author 05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md (Paralogism, Antinomy & Noumena)",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "test -f docs/spec/05_DIALECTIC_VERIFICATION_AND_CAPABILITIES.md",
                                    "notes": "Affine capability ownership, Secret<T> taint analysis, 3-tier contract proofs."
                                },
                                {
                                    "id": "C0.H1.S2.T05",
                                    "title": "Author 06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md (Dual Engine & Merkle Audit)",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "test -f docs/spec/06_METHOD_CRANELIFT_VM_AND_EVIDENCE.md",
                                    "notes": "KANT-IR evaluator, Cranelift JIT/AOT backend, Merkle evidence format."
                                },
                                {
                                    "id": "C0.H1.S2.T06",
                                    "title": "Author 07_AGENT_SURFACE_SIDECAR_AND_MCP.md (JSON Diagnostics, R1–R6 & 10 MCP Tools)",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "test -f docs/spec/07_AGENT_SURFACE_SIDECAR_AND_MCP.md",
                                    "notes": "RFC 6902 JSON patch auto-fixes and XGrammar constrained sampling."
                                },
                                {
                                    "id": "C0.H1.S2.T07",
                                    "title": "Compute BLAKE3/SHA-256 digests and pin in kant-toolchain.toml",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "test -f kant-toolchain.toml",
                                    "notes": "Pinned all 8 document hashes and subagent rules."
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "C0.H2",
                    "title": "32-Question Clarification & Pragmatic Deferral Engine",
                    "crate_lane": "docs/DECISIONS_AND_DEFERRED_ROADMAP.md",
                    "assigned_agent": "SA-01",
                    "sub_headings": [
                        {
                            "id": "C0.H2.S1",
                            "title": "P0-Blocking Architectural Decisions (Q01–Q05, Q09, Q17, Q25)",
                            "tasks": [
                                {
                                    "id": "C0.H2.S1.T01",
                                    "title": "Lock Latin/Arabic surface representation & .kantd sidecar format",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "grep 'Q01' docs/DECISIONS_AND_DEFERRED_ROADMAP.md",
                                    "notes": "Latin ASCII for tokenizer fidelity, Arabic .kantd sidecar for inspection."
                                },
                                {
                                    "id": "C0.H2.S1.T02",
                                    "title": "Lock flattened infix grammar mode with De Bruijn slot canonical indexing",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "grep 'Q03' docs/DECISIONS_AND_DEFERRED_ROADMAP.md",
                                    "notes": "Flattened infix to avoid KV-cache misses; @T.0 De Bruijn indices for hashes."
                                },
                                {
                                    "id": "C0.H2.S1.T03",
                                    "title": "Lock exact set-equality effect matching (Sigil Law) and 3-tier contract verifier",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "grep 'Q09' docs/DECISIONS_AND_DEFERRED_ROADMAP.md",
                                    "notes": "E_decl = E_inf with SAFE quickfixes; Tier 1 SMT + Tier 3 runtime fallback."
                                },
                                {
                                    "id": "C0.H2.S1.T04",
                                    "title": "Lock dual target backends: KANT-IR Evaluator + Cranelift JIT/AOT native codegen",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "grep 'Q25' docs/DECISIONS_AND_DEFERRED_ROADMAP.md",
                                    "notes": "Evaluator for deterministic traces, Cranelift for native x86-64 / ARM64."
                                }
                            ]
                        },
                        {
                            "id": "C0.H2.S2",
                            "title": "P1/P2 Pragmatic Deferral Registry (DECISIONS_AND_DEFERRED_ROADMAP.md)",
                            "tasks": [
                                {
                                    "id": "C0.H2.S2.T01",
                                    "title": "Auto-triage 24 deferrable questions to MVP pragmatic defaults",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "test -f docs/DECISIONS_AND_DEFERRED_ROADMAP.md",
                                    "notes": "Recorded all 24 P1/P2 items in ADR format."
                                },
                                {
                                    "id": "C0.H2.S2.T02",
                                    "title": "Isolate deferred v0.2/v0.5 features (Lean 4, Atomic RC, WASM, GPUI) behind trait boundaries",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "grep 'v0.2' docs/DECISIONS_AND_DEFERRED_ROADMAP.md",
                                    "notes": "Trait boundaries defined for ProofExporter, AtomicRC, and WASM backend."
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "id": "C1",
            "name": "Wave 1: Transcendental Aesthetic (Foundation)",
            "short_title": "Wave 1: Aesthetic",
            "wave": "Wave 1",
            "gate_status": "IN_ITERATION",
            "iteration": 1,
            "dependencies": ["C0"],
            "gate_checklist": {
                "cargo_fmt": False,
                "cargo_clippy": False,
                "cargo_test": False,
                "conformance_tests": False,
                "git_status_clean": False
            },
            "iterations": [
                {
                    "number": 1,
                    "timestamp": "2026-11-06T14:26:00Z",
                    "status": "IN_ITERATION",
                    "summary": "Implemented kant-core, kant-lexer, kant-parser, and kant-canonical with conformance suites."
                }
            ],
            "main_headings": [
                {
                    "id": "C1.H1",
                    "title": "Core Primitives & Zero-Copy Lexer",
                    "crate_lane": "crates/kant-core, crates/kant-lexer",
                    "assigned_agent": "SA-01 & SA-02",
                    "sub_headings": [
                        {
                            "id": "C1.H1.S1",
                            "title": "ByteSpans, Symbol Interner & Closed Vocabulary Table",
                            "tasks": [
                                {
                                    "id": "C1.H1.S1.T01",
                                    "title": "Implement ByteSpan, SymbolId, and DefHash in kant-core",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-core -- --nocapture",
                                    "notes": "ByteSpan with merge/len, SymbolId interner, DefHash with SHA-256."
                                },
                                {
                                    "id": "C1.H1.S1.T02",
                                    "title": "Define closed 48-token vocabulary table in kant-lexer",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-lexer test_closed_epistemic_keywords",
                                    "notes": "Closed keywords matching Moussa Wehbe lexicon and effect operators."
                                },
                                {
                                    "id": "C1.H1.S1.T03",
                                    "title": "Implement zero-copy tokenizer for literals, keywords, contracts, and ?hole tokens",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-lexer conformance_lexer",
                                    "notes": "Magic header, ?hole, @T.0 De Bruijn slots, strings, numbers."
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "C1.H2",
                    "title": "Flattened Pratt & LL(1) Parser",
                    "crate_lane": "crates/kant-parser",
                    "assigned_agent": "SA-03",
                    "sub_headings": [
                        {
                            "id": "C1.H2.S1",
                            "title": "Toplevel Flattened Declarations & Contract Clauses",
                            "tasks": [
                                {
                                    "id": "C1.H2.S1.T01",
                                    "title": "Parse afhoum (types/enums/structs) and top-level fn signatures",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-parser test_parse_afhoum_and_cap",
                                    "notes": "Toplevel declarations parsed cleanly without deep nesting."
                                },
                                {
                                    "id": "C1.H2.S1.T02",
                                    "title": "Parse mandatory contract blocks (intent, requires, ensures, decreases, effects)",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-parser test_parse_full_function_with_contracts",
                                    "notes": "Contract blocks parsed before function body."
                                },
                                {
                                    "id": "C1.H2.S1.T03",
                                    "title": "Parse decision blocks and dyn { ... } quarantine blocks",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-parser test_parse_decision_block",
                                    "notes": "Structured metadata parsed for compiler and spec views."
                                },
                                {
                                    "id": "C1.H2.S1.T04",
                                    "title": "Implement error recovery reducing malformed syntax to Expr::Hole",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-parser test_parse_typed_hole_and_operator_precedence",
                                    "notes": "Zero panics on syntax errors; emits Expr::Hole for agent repair."
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "C1.H3",
                    "title": "Spatial Canonicalizer & Lockfile Engine",
                    "crate_lane": "crates/kant-canonical",
                    "assigned_agent": "SA-04",
                    "sub_headings": [
                        {
                            "id": "C1.H3.S1",
                            "title": "De Bruijn Slot Erasure & Deterministic SHA-256 AST Identity",
                            "tasks": [
                                {
                                    "id": "C1.H3.S1.T01",
                                    "title": "Erase local variable/parameter names to @T.0, @T.1 binding-order slots",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-canonical test_alpha_equivalence_invariant",
                                    "notes": "Renaming local variables produces 100% identical DefHash."
                                },
                                {
                                    "id": "C1.H3.S1.T02",
                                    "title": "Sort record fields lexicographically and normalize recursive calls to @self",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-canonical test_type_field_order_invariance",
                                    "notes": "Field ordering invariance verified."
                                },
                                {
                                    "id": "C1.H3.S1.T03",
                                    "title": "Round-trip display names losslessly via .kantd JSON sidecar",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-canonical test_kantd_roundtrip",
                                    "notes": "Generates .kantd file mapping De Bruijn slots back to human names."
                                }
                            ]
                        },
                        {
                            "id": "C1.H3.S2",
                            "title": "Sidecar Lockfile (module.kant.lock) Reconciliation Rules R1–R6",
                            "tasks": [
                                {
                                    "id": "C1.H3.S2.T01",
                                    "title": "Implement R1 (Match) & R6 (New Pin) in LockfileEngine",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-canonical test_lockfile_reconciliation_r1_and_r4_mechanical_rename",
                                    "notes": "Pushed to lockfile seamlessly on matching and novel defs."
                                },
                                {
                                    "id": "C1.H3.S2.T02",
                                    "title": "Implement R2 (Resolution Changed Hard Error) and R3 (Content Drift)",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-canonical conformance_canonical",
                                    "notes": "Prevents silent rebinding hijacks; enforces --frozen in CI."
                                },
                                {
                                    "id": "C1.H3.S2.T03",
                                    "title": "Implement R4 (Rename Detection by Identity Hash) emitting mechanical rename_reference patch",
                                    "status": "DONE_VERIFIED",
                                    "iteration_completed": 1,
                                    "verification_cmd": "cargo test -p kant-canonical test_lockfile_reconciliation_r1_and_r4_mechanical_rename",
                                    "notes": "Emits RFC 6902 patch updating callers automatically."
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "id": "C2",
            "name": "Wave 2: Transcendental Analytic & Al-Shaym IR",
            "short_title": "Wave 2: Analytic & IR",
            "wave": "Wave 2",
            "gate_status": "LOCKED",
            "iteration": 0,
            "dependencies": ["C1"],
            "gate_checklist": {
                "cargo_fmt": False,
                "cargo_clippy": False,
                "cargo_test": False,
                "conformance_tests": False,
                "git_status_clean": False
            },
            "iterations": [],
            "main_headings": [
                {
                    "id": "C2.H1",
                    "title": "12-Categories Type System",
                    "crate_lane": "crates/kant-types",
                    "assigned_agent": "SA-05",
                    "sub_headings": [
                        {
                            "id": "C2.H1.S1",
                            "title": "Triads of Quantity, Quality, Relation & Modality",
                            "tasks": [
                                {
                                    "id": "C2.H1.S1.T01",
                                    "title": "Implement Quantity (Unity primitives, Plurality slices, Totality exhaustive ADTs)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-types test_category_quantity",
                                    "notes": "Type categories assigned to TypedModule AST."
                                },
                                {
                                    "id": "C2.H1.S1.T02",
                                    "title": "Implement Quality (Reality inhabited check, Negation never type !, Limitation Secret<T>)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-types test_category_quality",
                                    "notes": "Check inhabitation and Secret<T> wrapper."
                                },
                                {
                                    "id": "C2.H1.S1.T03",
                                    "title": "Implement Relation (Substance immutable structs, Causality function arrows fn -> T ! E)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-types test_category_relation",
                                    "notes": "Arrows carrying explicit effect sets."
                                },
                                {
                                    "id": "C2.H1.S1.T04",
                                    "title": "Implement Modality (Possibility Option/Result, Actuality cap handles, Necessity const)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-types test_category_modality",
                                    "notes": "Option/Result, linear cap types, and proved consts."
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "C2.H2",
                    "title": "Exact Effect Matcher & Quarantined Dynamism",
                    "crate_lane": "crates/kant-effects",
                    "assigned_agent": "SA-06",
                    "sub_headings": [
                        {
                            "id": "C2.H2.S1",
                            "title": "Sigil-Style Set Equality Effect Verification",
                            "tasks": [
                                {
                                    "id": "C2.H2.S1.T01",
                                    "title": "Build atomic effect lattice (console, fs, net, ai, clock, entropy, diverge)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-effects test_01_pure_function_exact_match",
                                    "notes": "AtomicEffect enum and EffectSet operations."
                                },
                                {
                                    "id": "C2.H2.S1.T02",
                                    "title": "Verify E_decl(f) = E_inf(f) strict set equality and emit KANT-E301/E302 with SAFE JSON patches",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-effects test_02_undeclared_effect_rejected_with_safe_patch",
                                    "notes": "RFC 6902 patch replacement of /functions/<idx>/effects."
                                },
                                {
                                    "id": "C2.H2.S1.T03",
                                    "title": "Support higher-order effects of(f) parameter substitution",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-effects test_04_higher_order_effects_of_param",
                                    "notes": "Substitutes concrete lambda effects into caller signature."
                                }
                            ]
                        },
                        {
                            "id": "C2.H2.S2",
                            "title": "Quarantined Dynamism (G1–G4 Guarantees)",
                            "tasks": [
                                {
                                    "id": "C2.H2.S2.T01",
                                    "title": "Enforce inert function references &fn and restrict indirect calls to dyn { t1..tn }",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-effects test_05_unquarantined_funref_call_rejected",
                                    "notes": "Reject escaped function pointers outside dyn blocks."
                                },
                                {
                                    "id": "C2.H2.S2.T02",
                                    "title": "Implement intraprocedural funref may-reach analysis proposing minimal dyn target sets",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-effects test_06_quarantine_under_approximation_detected",
                                    "notes": "Emits KANT-E306 if actual callee targets exceed declared list."
                                },
                                {
                                    "id": "C2.H2.S2.T03",
                                    "title": "Compute transitive reverse-caller blast radius and reference exactness ratio",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-effects test_10_blast_radius_and_exactness_metric",
                                    "notes": "G1/G2 blast radius and exactness ratio computed in O(V+E)."
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "C2.H3",
                    "title": "Al-Shaym SSA IR & Perceus Memory Engine",
                    "crate_lane": "crates/kant-ir, crates/kant-perceus",
                    "assigned_agent": "SA-07 & SA-08",
                    "sub_headings": [
                        {
                            "id": "C2.H3.S1",
                            "title": "30-Instruction SSA KANT-IR & Continuation Lowering",
                            "tasks": [
                                {
                                    "id": "C2.H3.S1.T01",
                                    "title": "Lower typed AST to basic-block SSA form (30 canonical instructions)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-ir test_lower_basic_blocks",
                                    "notes": "SSA dominance and def-use chain verification."
                                },
                                {
                                    "id": "C2.H3.S1.T02",
                                    "title": "Lower handle { ... } with governor { ... } to continuation capture/resume primitives",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-ir test_effect_handler_lowering",
                                    "notes": "Reified stack frames and continuation tokens."
                                }
                            ]
                        },
                        {
                            "id": "C2.H3.S2",
                            "title": "Perceus Garbage-Free Reference Counting & Drop-Guided Reuse",
                            "tasks": [
                                {
                                    "id": "C2.H3.S2.T01",
                                    "title": "Emit precise dup and drop instructions (zero garbage at each step)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-perceus test_dup_drop_placement",
                                    "notes": "Free at syntactically last use in time."
                                },
                                {
                                    "id": "C2.H3.S2.T02",
                                    "title": "Implement drop-guided reuse pass matching dead unique cells with same-size allocations (Alloc@r)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-perceus test_drop_guided_reuse",
                                    "notes": "In-place buffer recycling with frame-limited memory guarantees."
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "id": "C3",
            "name": "Wave 3: Transcendental Dialectic, Security & Spec Extraction",
            "short_title": "Wave 3: Dialectic",
            "wave": "Wave 3",
            "gate_status": "LOCKED",
            "iteration": 0,
            "dependencies": ["C2"],
            "gate_checklist": {
                "cargo_fmt": False,
                "cargo_clippy": False,
                "cargo_test": False,
                "conformance_tests": False,
                "git_status_clean": False
            },
            "iterations": [],
            "main_headings": [
                {
                    "id": "C3.H1",
                    "title": "Paralogism Guard — Affine Capabilities & Secret Taint",
                    "crate_lane": "crates/kant-paralogism",
                    "assigned_agent": "SA-09",
                    "sub_headings": [
                        {
                            "id": "C3.H1.S1",
                            "title": "Affine Capability Tracking & Constant-Time Secret Discipline",
                            "tasks": [
                                {
                                    "id": "C3.H1.S1.T01",
                                    "title": "Track Available | Borrowed | Moved state for capability handles",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-paralogism test_use_after_move",
                                    "notes": "Emits E004 use-after-move, E005 double-move, E009 branch mismatch."
                                },
                                {
                                    "id": "C3.H1.S1.T02",
                                    "title": "Implement Secret<T> with zeroize-on-drop and IR taint analysis",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-paralogism test_secret_taint_branch_leak",
                                    "notes": "Rejects secret values in branch conditions and cache indices."
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "C3.H2",
                    "title": "Antinomy Verifier — 3-Tier Contracts & Termination",
                    "crate_lane": "crates/kant-antinomy",
                    "assigned_agent": "SA-10",
                    "sub_headings": [
                        {
                            "id": "C3.H2.S1",
                            "title": "Tier 1 Static Proof (SMT) & Tier 3 Runtime Fallback",
                            "tasks": [
                                {
                                    "id": "C3.H2.S1.T01",
                                    "title": "Discharge requires/ensures obligations via Tier 1 interval solver & Z3 SMT (10s budget)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-antinomy test_tier1_smt_discharge",
                                    "notes": "Fast interval evaluation with Z3 SMT solver fallback."
                                },
                                {
                                    "id": "C3.H2.S1.T02",
                                    "title": "Synthesize Tier 3 compiled runtime assertion guards on solver timeout",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-antinomy test_tier3_runtime_guard_synthesis",
                                    "notes": "Lowers unproved obligations to checked asserts with reconciliation."
                                },
                                {
                                    "id": "C3.H2.S1.T03",
                                    "title": "Enforce mandatory decreases measure on recursive SCCs (E137)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-antinomy test_decreases_termination_check",
                                    "notes": "Requires decreases clause or explicit diverge effect."
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "C3.H3",
                    "title": "Noumena Governor & Amthoul Spec Extractor",
                    "crate_lane": "crates/kant-noumena, crates/kant-spec",
                    "assigned_agent": "SA-11 & SA-12",
                    "sub_headings": [
                        {
                            "id": "C3.H3.S1",
                            "title": "Session-Governor-Executor Protocol & Spec Rendering",
                            "tasks": [
                                {
                                    "id": "C3.H3.S1.T01",
                                    "title": "Enforce trust none module default and unforgeable ZST capability tokens",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-noumena test_trust_none_enforcement",
                                    "notes": "Private constructor tokens passed only from entrypoint."
                                },
                                {
                                    "id": "C3.H3.S1.T02",
                                    "title": "Implement approval_gate continuation suspension for human sign-off",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-noumena test_approval_gate_suspension",
                                    "notes": "Suspends execution until CLI or IDE signature provided."
                                },
                                {
                                    "id": "C3.H3.S1.T03",
                                    "title": "Implement kantc spec contract surface renderer and kantc graph --of <fn> blast radius",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-spec test_spec_and_graph_extraction",
                                    "notes": "Generates concise .spec file for human signing and token-budgeted slices."
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "id": "C4",
            "name": "Wave 4: Doctrine of Method, Native Codegen & Agent Surface",
            "short_title": "Wave 4: Codegen & Tools",
            "wave": "Wave 4",
            "gate_status": "LOCKED",
            "iteration": 0,
            "dependencies": ["C3"],
            "gate_checklist": {
                "cargo_fmt": False,
                "cargo_clippy": False,
                "cargo_test": False,
                "conformance_tests": False,
                "git_status_clean": False
            },
            "iterations": [],
            "main_headings": [
                {
                    "id": "C4.H1",
                    "title": "Reference Evaluator & Merkle Evidence Bundles",
                    "crate_lane": "crates/kant-eval",
                    "assigned_agent": "SA-13",
                    "sub_headings": [
                        {
                            "id": "C4.H1.S1",
                            "title": "Deterministic KANT-IR VM & Tamper-Evident Audit Trail",
                            "tasks": [
                                {
                                    "id": "C4.H1.S1.T01",
                                    "title": "Implement deterministic KANT-IR reference interpreter (kantc run --eval)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-eval test_deterministic_evaluator",
                                    "notes": "Interprets 30 KANT-IR SSA opcodes with state trace."
                                },
                                {
                                    "id": "C4.H1.S1.T02",
                                    "title": "Record Noumena invocations into hash-chained Merkle evidence bundle (.kant.evidence.jsonl)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-eval test_merkle_evidence_logging",
                                    "notes": "Cryptographic audit trail with parent hash chaining."
                                },
                                {
                                    "id": "C4.H1.S1.T03",
                                    "title": "Implement bit-identical deterministic workflow replay (kantc replay <bundle>)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-eval test_deterministic_replay",
                                    "notes": "Offline replay without hitting external APIs."
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "C4.H2",
                    "title": "Cranelift JIT & Native AOT Backend",
                    "crate_lane": "crates/kant-codegen",
                    "assigned_agent": "SA-14",
                    "sub_headings": [
                        {
                            "id": "C4.H2.S1",
                            "title": "Sub-3ms JIT Loop & Static Native Binary Emission",
                            "tasks": [
                                {
                                    "id": "C4.H2.S1.T01",
                                    "title": "Lower KANT-IR SSA to Cranelift IR (CLIF) for x86-64 and ARM64",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-codegen test_clif_lowering",
                                    "notes": "Maps SSA values and basic blocks to Cranelift variables."
                                },
                                {
                                    "id": "C4.H2.S1.T02",
                                    "title": "Implement fast in-memory JIT execution engine (kantc run) for agent iterations",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-codegen test_jit_execution",
                                    "notes": "Sub-3ms execution turnaround."
                                },
                                {
                                    "id": "C4.H2.S1.T03",
                                    "title": "Emit standalone static native executables (kantc build) with deterministic timestamps",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-codegen test_aot_binary_emission",
                                    "notes": "Byte-identical native binaries across runs."
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "C4.H3",
                    "title": "JSON Patch Auto-Fix, Agent Server & MCP",
                    "crate_lane": "crates/kant-diag, crates/kant-cli, crates/kant-mcp",
                    "assigned_agent": "SA-15 & SA-16",
                    "sub_headings": [
                        {
                            "id": "C4.H3.S1",
                            "title": "RFC 6902 Automated Repair Loop & Test Cache",
                            "tasks": [
                                {
                                    "id": "C4.H3.S1.T01",
                                    "title": "Unify compiler diagnostics with FixSafety: SAFE|REVIEW and RFC 6902 JSON Patch payloads",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-diag test_diagnostic_patch_serialization",
                                    "notes": "Standardized JSON schema with patch operations."
                                },
                                {
                                    "id": "C4.H3.S1.T02",
                                    "title": "Implement kantc fix --apply iterative convergence loop",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-diag test_auto_repair_convergence",
                                    "notes": "Applies SAFE patches iteratively until clean."
                                },
                                {
                                    "id": "C4.H3.S1.T03",
                                    "title": "Implement content-addressed test caching (kantc test) keyed by dependency cone SHA-256",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-cli test_cached_test_runner",
                                    "notes": "Reruns only tests whose dependency cone hash drifted."
                                }
                            ]
                        },
                        {
                            "id": "C4.H3.S2",
                            "title": "Long-Lived kantc serv, 10-Tool kant-mcp & XGrammar Exporter",
                            "tasks": [
                                {
                                    "id": "C4.H3.S2.T01",
                                    "title": "Build persistent JSON-RPC daemon (kantc serv) for zero-spawn agent checks",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-cli test_agent_server_rpc",
                                    "notes": "Zero process startup overhead."
                                },
                                {
                                    "id": "C4.H3.S2.T02",
                                    "title": "Build kant-mcp server exposing 10 structured tools (check, fix, spec, graph, eval, etc.)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-mcp test_10_mcp_tools",
                                    "notes": "Model Context Protocol interface for Claude Code, Cursor, Codex."
                                },
                                {
                                    "id": "C4.H3.S2.T03",
                                    "title": "Implement kantc grammar --export-xgrammar generating CFG/PDA masks for constrained decoding",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test -p kant-cli test_xgrammar_export",
                                    "notes": "Enforces 100% syntactically valid code during token sampling."
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "id": "C5",
            "name": "The Four Mandatory MVP Bootstrap & Quality Proofs",
            "short_title": "MVP Quality Proofs",
            "wave": "Quality & Verification",
            "gate_status": "LOCKED",
            "iteration": 0,
            "dependencies": ["C4"],
            "gate_checklist": {
                "differential_proof": False,
                "byte_determinism_proof": False,
                "repair_convergence_proof": False,
                "zero_escape_security_proof": False,
                "git_status_clean": False
            },
            "iterations": [],
            "main_headings": [
                {
                    "id": "C5.H1",
                    "title": "Execution & Determinism Verification Proofs",
                    "crate_lane": "tests/bootstrap_proofs",
                    "assigned_agent": "SA-13 & SA-14",
                    "sub_headings": [
                        {
                            "id": "C5.H1.S1",
                            "title": "Proof 1 (Differential Oracle) & Proof 2 (Byte-Identical Determinism)",
                            "tasks": [
                                {
                                    "id": "C5.H1.S1.T01",
                                    "title": "Execute 50 reference .kant programs across kant-eval and kant-codegen (100% identical outputs)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test --test proof_01_differential_oracle",
                                    "notes": "0 output or state trace deviations."
                                },
                                {
                                    "id": "C5.H1.S1.T02",
                                    "title": "Run dual independent compilations verifying 0 byte mismatches across generated binaries",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test --test proof_02_byte_determinism",
                                    "notes": "Bit-for-bit identical binary output."
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "C5.H2",
                    "title": "Autonomous Repair & Epistemic Security Proofs",
                    "crate_lane": "tests/bootstrap_proofs",
                    "assigned_agent": "SA-15 & SA-11",
                    "sub_headings": [
                        {
                            "id": "C5.H2.S1",
                            "title": "Proof 3 (Repair Convergence) & Proof 4 (Noumena Zero-Escape)",
                            "tasks": [
                                {
                                    "id": "C5.H2.S1.T01",
                                    "title": "Run kantc fix --apply across 30 seeded defective programs (100% convergence to valid builds)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test --test proof_03_repair_convergence",
                                    "notes": "Iterative patch application reaches fixed point."
                                },
                                {
                                    "id": "C5.H2.S1.T02",
                                    "title": "Run adversarial security suite verifying 100% rejection of unmediated I/O and capability forgery",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "cargo test --test proof_04_noumena_zero_escape",
                                    "notes": "Trust none boundary and secret zeroization verified."
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "id": "C6",
            "name": "Kant v0.1 Distributable Release & Ecosystem Launch",
            "short_title": "v0.1 Release Launch",
            "wave": "Release & Distribution",
            "gate_status": "LOCKED",
            "is_final_destination": True,
            "iteration": 0,
            "dependencies": ["C5"],
            "gate_checklist": {
                "clean_git_tree": False,
                "tarballs_generated": False,
                "checksums_verified": False,
                "installer_smoke_tested": False,
                "agent_portal_ready": False
            },
            "iterations": [],
            "main_headings": [
                {
                    "id": "C6.H1",
                    "title": "Automated Distribution Sub-Function (kantc dist & scripts/distribute_v0_1.sh)",
                    "crate_lane": "scripts/distribute_v0_1.sh, dist/",
                    "assigned_agent": "SA-16",
                    "sub_headings": [
                        {
                            "id": "C6.H1.S1",
                            "title": "Cross-Platform Binary Bundling & Cryptographic Checksums",
                            "tasks": [
                                {
                                    "id": "C6.H1.S1.T01",
                                    "title": "Implement kantc dist --release v0.1.0 subcommand and scripts/distribute_v0_1.sh",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "bash scripts/distribute_v0_1.sh --dry-run",
                                    "notes": "Package stripped release binaries for linux-x86_64, darwin-arm64, windows-x86_64."
                                },
                                {
                                    "id": "C6.H1.S1.T02",
                                    "title": "Bundle standard library, byte-pinned primer (kant-toolchain.toml), and SHA-256SUMS manifest",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "sha256sum -c dist/v0.1.0/SHA256SUMS",
                                    "notes": "Create .tar.gz and .zip release archives."
                                }
                            ]
                        },
                        {
                            "id": "C6.H1.S2",
                            "title": "One-Command Universal Installer & Agent Plugin Packages",
                            "tasks": [
                                {
                                    "id": "C6.H1.S2.T01",
                                    "title": "Generate universal shell installer install.sh (curl -fsSL .../install.sh | sh)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "bash scripts/distribute_v0_1.sh --verify-installer",
                                    "notes": "Auto-detects OS/arch, verifies SHA-256, installs to ~/.kant/bin."
                                },
                                {
                                    "id": "C6.H1.S2.T02",
                                    "title": "Generate Python MCP wrapper package (kant-lang) and Agent skill plugin (SKILL.md)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "test -f dist/packages/SKILL.md",
                                    "notes": "pipx install 'kant-lang[mcp]' and Claude Code / Cursor / Gemini CLI skill."
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "C6.H2",
                    "title": "Machine-Readable Agent Portal & Pre-Release Git Sanitization",
                    "crate_lane": "agent/v0.1/, .gitignore",
                    "assigned_agent": "SA-16",
                    "sub_headings": [
                        {
                            "id": "C6.H2.S1",
                            "title": "Versioned /agent/v0.1/ JSON Portal & /llms.txt Specification",
                            "tasks": [
                                {
                                    "id": "C6.H2.S1.T01",
                                    "title": "Generate /llms.txt and /llms-full.txt single-page cold-start specs (<3,200 tokens)",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "wc -w dist/agent/llms.txt",
                                    "notes": "10/10 builtin recall on LLM cold starts."
                                },
                                {
                                    "id": "C6.H2.S1.T02",
                                    "title": "Generate /agent/v0.1/manifest.json, schemas/diagnostics.json, and examples/catalog.json",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "test -f dist/agent/v0.1/manifest.json",
                                    "notes": "Machine discovery endpoint with paired .kant and .spec examples."
                                }
                            ]
                        },
                        {
                            "id": "C6.H2.S2",
                            "title": "Git Hygiene Gate & GitHub Release Tagging (v0.1.0)",
                            "tasks": [
                                {
                                    "id": "C6.H2.S2.T01",
                                    "title": "Run automated pre-release sanitizer verifying tracker files are ignored and absent from git status",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "git check-ignore kant-roadmap-tracker.html .kant-tracker/",
                                    "notes": "Strict git cleanliness check."
                                },
                                {
                                    "id": "C6.H2.S2.T02",
                                    "title": "Tag v0.1.0 release, build release notes, and generate distribution SHA-256 manifest",
                                    "status": "TODO",
                                    "iteration_completed": 0,
                                    "verification_cmd": "git tag -l v0.1.0",
                                    "notes": "Official GitHub release tag and release notes."
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

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
            updated_at TEXT NOT NULL
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
            updated_at TEXT NOT NULL
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
                print(f"[!] Warning reading existing state.json during migration: {e}", file=sys.stderr)
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
        print(f"[✓] Initialized SQLite telemetry database at {DB_FILE} with auto-migration from state.json.")

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
                        INSERT OR REPLACE INTO tasks (id, subheading_id, heading_id, circle_id, title, status, iteration_completed, verification_cmd, notes, ordering, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        tid,
                        sid,
                        hid,
                        cid,
                        task.get("title", tid),
                        task.get("status", "TODO"),
                        task.get("iteration_completed", 0),
                        task.get("verification_cmd", ""),
                        task.get("notes", ""),
                        t_idx,
                        now_iso
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
                cur.execute("SELECT id, title, status, iteration_completed, verification_cmd, notes FROM tasks WHERE subheading_id = ? ORDER BY ordering ASC, id ASC", (sid,))
                trows = cur.fetchall()

                tasks = []
                for trow in trows:
                    total_tasks += 1
                    tstatus = trow["status"]
                    if tstatus == "DONE_VERIFIED":
                        completed_tasks += 1
                    elif tstatus == "BLOCKED":
                        blocked_tasks += 1

                    tasks.append({
                        "id": trow["id"],
                        "title": trow["title"],
                        "status": trow["status"],
                        "iteration_completed": trow["iteration_completed"] or 0,
                        "verification_cmd": trow["verification_cmd"] or "",
                        "notes": trow["notes"] or ""
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
        print(f"[x] Error: Task ID '{task_id}' not found in database.", file=sys.stderr)
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
            print(f"[!] REGRESSION DETECTED in Circle {cid}: Task {task_id} shifted from {old_status} to {new_status}. Bumped to Iteration #{new_iter}.")
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
    print(f"[✓] Task {task_id} updated: {diff}. Telemetry event #{event.get('id')} recorded.")
    return event

def update_circle_gate(circle_id, gate_status):
    init_db()
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, gate_status FROM circles WHERE id = ?", (circle_id,))
    c_row = cur.fetchone()
    if not c_row:
        print(f"[x] Error: Circle ID '{circle_id}' not found.", file=sys.stderr)
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
    print(f"[✓] Circle {circle_id} gate status transitioned from {old_status} to {gate_status}.")
    return event

# ------------------------------------------------------------------------------
# Terminal Dashboard & Reporting
# ------------------------------------------------------------------------------
def print_summary():
    state = load_state()
    stats = state.get("global_stats", {})
    print("=" * 72)
    print("  KANT (.kant) v0.1 ROADMAP & TELEMETRY PROGRESS SUMMARY")
    print("=" * 72)
    print(f"  Overall Progress: {stats.get('progress_percent', 0)}% "
          f"({stats.get('completed_tasks', 0)} / {stats.get('total_tasks', 0)} tasks verified)")
    print(f"  Blocked Tasks:    {stats.get('blocked_tasks', 0)}")
    print(f"  Database Engine:  SQLite ({DB_FILE}) [WAL Mode Active]")
    print(f"  Current Focus:    Circle {state.get('current_circle_focus', 'C1')}")
    print("-" * 72)
    print(f"  {'Node':<6} | {'Gate Status':<20} | {'Iter':<6} | {'Completed':<10} | {'Circle Name'}")
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
    print("=" * 72)
    print(f"[*] Kant Roadmap Tracker & Telemetry SSE Server Active")
    print("=" * 72)
    print(f"[*] Web Interface:        http://localhost:{port}/")
    print(f"[*] Real-Time SSE Stream: http://localhost:{port}/api/events")
    print(f"[*] State JSON API:       http://localhost:{port}/api/state")
    print(f"[*] Telemetry Audit API:  http://localhost:{port}/api/telemetry")
    print(f"[*] Gate Runs Audit API:  http://localhost:{port}/api/gate_runs")
    print(f"[*] Database Persistence: SQLite at {DB_FILE} (WAL mode)")
    print(f"[*] Serving kant-roadmap-tracker.html directly with zero-polling SSE.")
    print("=" * 72)
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
        print(f"[✓] Initialized fresh roadmap schema in {DB_FILE} and {STATE_FILE} with 7 Circles (C0-C6).")
        print_summary()
    elif args.migrate:
        init_db()
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
            save_state_to_db(s, record_telemetry=True, action_detail="CLI explicit --migrate from state.json")
            print(f"[✓] Successfully migrated state.json into SQLite: {DB_FILE}")
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
            print("[x] Error: --circle, --step, and --run-status are required for --record-gate-run", file=sys.stderr)
            sys.exit(1)
        res = record_gate_run(args.circle, args.iteration or 1, args.step, args.run_status, args.cmd, args.output)
        print(f"[✓] Recorded gate verification run #{res['run_id']} for {args.circle} ({args.step}: {args.run_status}).")
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

