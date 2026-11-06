# ADR-0006: Dual-Surface ASCII Canonical Source & Arabic Sidecar Projection

* **Status:** Accepted
* **Deciders:** Kant Architecture Working Group, Lexicon & Epistemic Architects
* **Date:** 2026-11-06
* **Technical Subsystem:** `crates/kant-lexer`, `crates/kant-canonical`
* **Related Invariant:** Milestone MVP v0.1 Syntax Design (Q01)

---

## Context & Problem Statement

The philosophical foundation of the Kant programming language is inspired by Immanuel Kant's *Critique of Pure Reason* as translated and critically conceptualized in Arabic by philosopher Moussa Wehbe (Beirut, 1988/1990).
However, modern generative AI models (OpenAI GPT-4, Anthropic Claude, Meta Llama) use Byte-Pair Encoding (BPE) tokenizers heavily optimized for Latin ASCII characters. Direct UTF-8 Arabic source code tokenizes into 3 to 6 tokens per character or sub-word, dramatically inflating context windows, increasing inference costs, and inducing high hallucination rates during code generation.

How can Kant honor its Moussa Wehbe Arabic epistemological heritage and provide full bilingual expression without compromising tokenization efficiency and LLM reasoning accuracy?

---

## Decision Drivers

1. **LLM Tokenizer Efficiency:** Code must tokenize into single-token ASCII atoms in standard BPE tokenizers.
2. **Epistemological Fidelity:** The rich Arabic conceptual vocabulary (*Al-Afhūm*, *Al-Shaym*, *Al-Mujāwaz*, *Al-Hads*) must remain first-class in the developer experience.
3. **Deterministic AST Equivalence:** Both representations must resolve to the identical canonical AST and content hash (`DefHash`).
4. **Tooling Interoperability:** Standard code linters, formatters, and IDEs must operate seamlessly.

---

## Considered Options

* **Option 1: Pure Arabic Source Code (`.kant` using UTF-8 Arabic script directly)**
* **Option 2: Latin ASCII Canonical Source (`.kant`) with Sidecar Visual Projection (`.kantd`)**
* **Option 3: Strict Dual Parsers with Dynamic Keyword Translation in the Tokenizer**

---

## Decision Outcome

**Chosen Option:** **Option 2: Latin ASCII Canonical Source (`.kant`) with Sidecar Visual Projection (`.kantd`)**.

The primary source file (`.kant`) uses standardized ASCII Latin keywords matching Moussa Wehbe's transliterated philosophical concepts (`afhoum`, `shaym`, `noumenon`, `mujauz`). Alongside the source file, `kantc` maintains a sidecar file (`module.kantd`), which maps AST byte spans and symbol identifiers to full Arabic typography (e.g. `afhoum` $\leftrightarrow$ `أفهوم`, `shaym` $\leftrightarrow$ `شيم`). IDE extensions and documentation render the Arabic projection directly for bilingual humans, while the compiler and AI agents process the ASCII `.kant` file with 100% token efficiency.

### Positive Consequences
- Single-token representation in BPE tokenizers minimizes context consumption and generation latency.
- Full respect and preservation of Moussa Wehbe's pioneering philosophical terminology.
- Canonical AST and `DefHash` calculations remain completely stable and unaffected by display language.

### Negative Consequences
- Developers interested in full Arabic visual editing must maintain the `.kantd` sidecar.

---

## Pros and Cons of Options

### Option 1: Pure Arabic Source Code
* *Pros:* Native Arabic writing experience.
* *Cons:* Severe BPE token inflation ($4\times - 6\times$ token count); high rate of agent syntactic hallucinations.

### Option 2: Latin ASCII Canonical with Arabic Sidecar (Selected)
* *Pros:*
  - Maximum LLM generation speed and reliability.
  - Full conceptual fidelity via sidecar projection.
  - Universal ASCII toolchain compatibility.
* *Cons:* Requires IDE sidecar rendering support for localized editing.

### Option 3: Dynamic Dual Parsers
* *Pros:* Allows mixing scripts in the same repo.
* *Cons:* Complex bidirectional mapping bugs; potential identifier aliasing attacks; unstable AST hashes.

---

## Validation

Validated via tokenization and parser tests:
- BPE token count measured across 10 sample functions: ASCII transliteration requires ~68% fewer tokens than raw Arabic UTF-8.
- The canonicalizer verifies that compiling `.kant` with or without `.kantd` produces identical `DefHash`.
