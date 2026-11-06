# 01_EPISTEMOLOGY_AND_LEXICON.md: The Moussa Wehbe Kantian Lexicon & Type Theory Mapping

This document establishes the official philosophical and type-theoretic foundations of the **Kant** programming language (`.kant`). It establishes the formal bridge between the epistemological architecture of Immanuel Kant's *Critique of Pure Reason* (*Kritik der reinen Vernunft*), through the seminal Arabic translation and critical apparatus of Lebanese philosopher **Moussa Wehbe** (Centre for National Development, Beirut, 1988/1990), and modern constructive type theory, algebraic effect systems, and compiler design.

---

## 1. Moussa Wehbe's Epistemological Lexicon

Moussa Wehbe demonstrated that Kant's critical project is primarily founded on logic rather than merely physics or mathematics, asserting that the *Critique* is an autonomous, self-grounded philosophical discourse. Below are the core terms coined by Wehbe and their structural realization in `kantc`:

### 1.1. Al-Mujāwaz (المُجاوِز) — The Transcendental
* **Kant's Term:** *Transzendental* / *Le Transcendantal*.
* **Wehbe's Philological Insight:** Wehbe decisively rejected the common Arabized loanword "الترنسندنتال" as well as the ambiguous translation "المتعالي" (which conflates the condition of possibility with *Le Transcendant* / المفارق). Drawing from classical Arabic grammar, where a transitive verb is termed *Fi'l Mujāwaz* (فعل مجاوز) because its action crosses over from the subject to an object, Wehbe defined the transcendental subject as an active epistemological structure that crosses over to raw sense data to shape and organize it.
* **Compiler Embodiment (`kantc`):** The compile-time verification pipeline itself acts as the *Transcendental Subject*. It does not passively accept arbitrary token streams from an AI agent; rather, it imposes a priori conditions of possibility (syntactic canonicalization, category-based typing, exact effect matching, and termination proofs) before executing any empirical (runtime) interaction.
* **Source Token:** `@transcendental` / `mujauz`.

### 1.2. Al-Afhūm (الأفهوم، ج: أفاهيم) — The Pure Concept of Understanding
* **Kant's Term:** *Reiner Begriff des Verstandes* / *Concept pur de l'entendement*.
* **Wehbe's Philological Insight:** Formed on the Arabic morphological pattern *Af'ūl* (أفعول, such as أسلوب or أنموذج), indicating an active, dynamic deed of thought rather than a static essence or passive thing. It designates an act of understanding that posits rules.
* **Compiler Embodiment:** Formal structural type definitions, algebraic data types (ADTs), interfaces, and refinement predicates.
* **Source Token:** `afhoum` (alias for `type` / `struct` / `enum`).

### 1.3. Al-Hads wal-Hassāsiyya (الحدس والحساسية) — Sensibility and Intuition
* **Kant's Term:** *Sinnlichkeit und Anschauung*.
* **Wehbe's Philological Insight:** The receptive faculty through which objects are given to us immediately. Space and Time are not empirical concepts drawn from experience, but the two pure forms of sensible intuition.
* **Compiler Embodiment:** The front-end ingestion layer. The Lexer, Pratt/LL(1) parser, and Canonical AST normalization represent the sensible reception of source tokens, structuring raw code into spatial and temporal forms.
* **Source Token:** `intuition` / `hads`.

### 1.4. Pure Space and Time (المكان والزمان القبليان)
* **A Priori Space (المكان القبلي):** In Kant, space is the form of all outer intuitions (coexistence). In `kantc`, space is represented by **Content-Addressed Code**. Every definition's identity is not its transient file path or line number, but the 32-byte SHA-256 digest of its canonical abstract syntax tree (`DefHash`).
* **A Priori Time (الزمان القبلي):** In Kant, time is the form of inner sense (succession). Following the categorical logic model of Achourioti & van Lambalgen, time is formalized as a directed index category. In `kantc`, time is embodied in the **Static Single Assignment (SSA) KANT-IR** coupled with the **Perceus memory engine**, ensuring deterministic lifetime tracking, instant reuse, and cycle-free drop sequences.
* **Source Tokens:** `space_hash`, `time_ssa`.

### 1.5. Phenomena vs. Noumena (الظاهرات والنومان)
* **Phenomena (الظاهرات / الفينمانات):** Sensible appearances structured by space, time, and the categories. In `kantc`, these are fully verified, in-memory, memory-safe data structures residing within the program's bounded heap/stack.
* **Noumena / Ding an sich (النومان / الشيء في ذاته):** The intelligible realm lying beyond the boundaries of sensible intuition. It cannot be directly known or arbitrarily manipulated by understanding. In `kantc`, the Noumenon represents the **Untrusted External World**: file systems, network sockets, OS system calls, clock timers, random seeds, and external large language models (LLMs). The runtime operates under `trust none`: code cannot breach the Noumenon without holding a linear, unforgeable capability token governed by an explicit handler.
* **Source Tokens:** `phenomenon` / `dhahira`, `noumenon` / `external`.

### 1.6. Synthetic A Priori Judgments (الأحكام التأليفية قبلياً)
* **Kant's Term:** *Synthetische Urteile a priori*.
* **Wehbe's Philological Insight:** Judgments that expand our knowledge (synthetic, unlike analytic tautologies) yet are universal and necessary (a priori, unlike empirical post-facto observations).
* **Compiler Embodiment:** Compile-time function contracts (`requires`, `ensures`, `decreases`, `effects`) verified statically via Z3 SMT solving and algebraic refinement before any code is permitted to execute.
* **Source Token:** `synthetic` / `judgment`.

### 1.7. Al-Shaym (الشَّيْم) — The Schematism of Pure Concepts
* **Kant's Term:** *Der Schematismus der reinen Verstandesbegriffe*.
* **Wehbe's Philological Insight:** Wehbe translated *Schema* as *Al-Shaym* (الشيم), inspired by the classical Arabic idiom "شيم البرق" (anticipating and tracing the flash of lightning), conveying the dynamic temporal mediation between an abstract category and concrete appearances.
* **Compiler Embodiment:** The **KANT-IR lowering pass**, which bridges abstract type declarations with low-level SSA execution, Perceus in-place buffer reuse tokens (`@r`), and algebraic effect continuations.
* **Source Token:** `shaym` / `schema`.

### 1.8. Dialectical Illusions: Paralogisms and Antinomies (الأغاليط والنقائض)
* **Paralogisms (الأغاليط المجاوزة):** Fallacies of identity and substantiality. In `kantc`, paralogisms are aliasing errors, capability duplication, and secret taint leaks (e.g., using a secret key in a branch condition). Guarded by `kant-paralogism`.
* **Antinomies (النقائض المجاوزة):** Structural contradictions when reason oversteps experience (e.g., infinite regression vs. first cause). In `kantc`, antinomies correspond to infinite non-terminating loops, deadlocks, and race conditions. Guarded by `kant-antinomy` (mandatory `decreases` clauses).
* **Source Tokens:** `paralogism` (Error prefix `KANT-E4xx`), `antinomy` (Error prefix `KANT-E5xx`).

### 1.9. Transcendental Doctrine of Method (مبحث المنهج المجاوز)
* **Kant's Division:**
  1. *Discipline of Pure Reason (انضباط العقل المحض):* Negative determination preventing error. Implemented via **XGrammar** constrained decoding masks that restrict AI agent token sampling to valid AST syntax.
  2. *Canon of Pure Reason (قانون العقل المحض):* Positive synthetic principles. Implemented via **Exact Effect Matching**.
  3. *Architectonic of Pure Reason (معمارية العقل المحض):* Systematic unity of the sciences. Implemented via dependency graphs (`kantc graph`) and **Merkle Evidence Bundles** for deterministic auditability.

---

## 2. Formal Mapping: Kant to Constructive Type Theory

Following Per Martin-Löf's *Analytic and Synthetic Judgments in Type Theory*:

$$\begin{array}{rcl}
\text{Kantian Epistemology} & \longleftrightarrow & \text{Constructive Type Theory} \\
\hline
\text{Pure Concept (الأفهوم)} & \longleftrightarrow & \text{Type } A \\
\text{Object given in Intuition (الموضوع في الحدس)} & \longleftrightarrow & \text{Canonical Program / Term } a \\
\text{Judgment of Experience (الحكم)} & \longleftrightarrow & \text{Typing Judgment } a : A \\
\text{Analytic Judgment (الحكم التحليلي)} & \longleftrightarrow & \text{Definitional Equality } a \equiv b : A \\
\text{Synthetic A Priori Judgment (الحكم التأليفي القبلي)} & \longleftrightarrow & \text{Propositional Equality / Proof Object } p : \text{Id}_A(a, b) \\
\text{Categories of Quantity (مقولات الكم)} & \longleftrightarrow & \text{Primitive, Finite, and Sum Types} \\
\text{Categories of Quality (مقولات الكيف)} & \longleftrightarrow & \text{Inhabitation, Bottom/Empty Type } \bot, \text{ Refinements} \\
\text{Categories of Relation (مقولات الإضافة)} & \longleftrightarrow & \text{Function Spaces } A \to B ! E, \text{ Linear Stream Morphisms} \\
\text{Categories of Modality (مقولات الجهة)} & \longleftrightarrow & \text{Option/Result, Capability Tokens, Const Invariants}
\end{array}$$

---

## 3. Dual Syntax Representation & Closed Vocabulary

To guarantee 100% interoperability with modern LLM tokenizers while honoring the Arabic philosophical heritage:

1. **Primary Compilation Syntax (`.kant`):** Uses standardized ASCII Latin keywords matching Wehbe's transliterated concepts (`afhoum`, `shaym`, `noumenon`) to prevent multi-token fragmentation during model inference.
2. **Sidecar Visual Projection (`.kantd`):** A JSON/YAML sidecar mapping byte spans to full Arabic philosophical terms for human philosophers and bilingual developers.

### The 48 Closed Vocabulary Tokens

```
// Toplevel Keywords
afhoum          shaym           noumenon        synthetic       decision
intent          requires        ensures         decreases       effects

// Effect & Governance Keywords
pure            handle          with            governor        approval_gate
dyn             table           of              perform         resume

// Control & Expression Keywords
let             mut             if              else            match
return          const           proof           type            cap

// Modality & Type Keywords
unity           plurality       totality        reality         negation
limitation      substance       causality       community       possible
actual          necessary       never           secret

// Symbols & Punctuation
:               ::              ->              !               ?hole
{               }               (               )               [               ]
,               ;               .               =               @
```
