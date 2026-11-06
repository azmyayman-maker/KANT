# 01_EPISTEMOLOGY_AND_LEXICON.md: Constructive Epistemology, Categorical Judgment Forms & Moussa Wehbe's Bijective Lexicon

This specification establishes the formal type-theoretic foundations of the **Kant** programming language (`.kant`). It defines the constructive translation of the epistemological architecture of Immanuel Kant's *Critique of Pure Reason* (*Kritik der reinen Vernunft*) into modern constructive type theory, algebraic effect systems, and compiler design. The Arabic terminology formulated by Lebanese philosopher and translator **Moussa Wehbe** (Centre for National Development, Beirut, 1988/1990) is formalized as a bijective dual-surface AST projection ontology.

---

## 1. Constructive Epistemology in Modern Programming Language Theory

Kant replaces speculative metaphysics with constructive mathematical logic. Programs are not treated as arbitrary state mutation or unverified string generation; they are constructive proofs operating under rigorous operational invariants:

### 1.1. Judgments and Proof Objects
In constructive type theory (Martin-Löf 1984), a judgment is an assertion of knowledge backed by evidence:
* **Analytic Judgments:** Reducible to definitional equality by computation ($\Gamma \vdash a \equiv b : A$). Verified entirely via normalization and beta-eta conversion at compile-time.
* **Synthetic *A Priori* Judgments:** Constructive propositions verified statically prior to execution ($\Gamma \vdash p : \text{Id}_A(a, b)$ or $\Gamma \vdash e : \tau \ \& \ \text{Contracts}(e)$). In `kantc`, function contracts (`requires`, `ensures`, `decreases`) and exact effect typing are synthetic *a priori* judgments proven via syntactic interval analysis and automated SMT solving (Z3).
* **Synthetic *A Posteriori* Judgments:** Empirical observations obtained via interaction with the external execution environment (*Noumena*). In `kantc`, empirical interactions are mediated strictly via linear, non-forgeable capability tokens threaded explicitly through the call graph.

### 1.2. Accessible State vs. Quarantined Environment
* **Accessible Typed State (*Phenomena* / الظاهرات):** Memory-safe, statically verified data structures bounded in stack and heap frames, governed deterministically by Perceus reference counting with cycle-free invariants.
* **Quarantined External Environment (*Noumena* / النومان):** The unconditioned external execution environment (file descriptors, network interfaces, operating system kernels, physical clocks, unvetted language model endpoints). Execution enforces default `trust none`: no ambient authority exists, and external interaction requires explicit capability tokens and sandboxed governor runtimes.

---

## 2. Moussa Wehbe's Bijective Dual-Surface Lexicon

Moussa Wehbe established that Kant's critical terminology constitutes an autonomous logical apparatus rather than empirical physics. In `kantc`, Wehbe's Arabic lexicon is defined as a formal 1:1 bijective mapping table onto compiler tokens, IR structures, and type-theoretic judgments:

| Arabic Term | ASCII Canonical Identifier | Category | PLT Type-Theoretic Semantics | Operational Invariant |
| :--- | :--- | :--- | :--- | :--- |
| **المُجاوِز** (*Al-Mujāwaz*) | `@transcendental` / `mujauz` | Epistemic Structure | Compile-time verification pipeline imposing a priori well-typedness conditions. | All terms must pass static validation prior to code generation. |
| **الأفهوم** (*Al-Afhūm*) | `afhoum` | Type Constructor | Structural record types, algebraic data types (ADTs), and product spaces. | Immutable structural value equality; field layout sorted alphabetically. |
| **الحدس والحساسية** (*Al-Hads*) | `intuition` / `hads` | Reception Layer | Lexical token stream and syntactic CST-to-AST normalization pass. | Eliminates non-semantic formatting; deterministic token ingestion. |
| **المكان القبلي** (*A Priori Space*) | `space_hash` | Identity Indexing | Content-addressed 32-byte cryptographic SHA-256 digest (`DefHash`). | $\text{DefHash} = \text{SHA-256}(\text{CanonicalAST})$; invariant under alpha-renaming. |
| **الزمان القبلي** (*A Priori Time*) | `time_ssa` | Directed Execution | Static Single Assignment (SSA) basic blocks and directed index categories. | Each SSA value is defined exactly once; lifetimes strictly ordered. |
| **الظاهرات** (*Phenomena*) | `phenomenon` / `dhahira` | Memory Space | Inhabited, verified typed values in heap and stack memory. | Memory managed deterministically via Perceus; zero leaks; cycle-free. |
| **النومان** (*Noumena*) | `noumenon` / `external` | Security Sandbox | Quarantined external environment, operating system calls, and I/O. | Ambient authority prohibited; execution requires linear capability handles. |
| **الحكم التأليفي** (*Synthetic Judgment*) | `synthetic` / `judgment` | Formal Contract | Statically proven function contracts (`requires`, `ensures`, `decreases`). | Certified by Tier 1 SMT / interval analysis or Tier 3 runtime assert. |
| **الشَّيْم** (*Al-Shaym*) | `shaym` / `schema` | Intermediate Lowering | 30-op SSA KANT-IR lowering pass bridging abstract types to machine ops. | Preserves effect sets; transforms dropped values into in-place reuse tokens. |
| **الأغلوطة** (*Paralogism*) | `paralogism` | Static Security | Aliasing errors, capability duplication, and secret taint branch leaks. | Linear capability move-only rules; secret-dependent branches rejected (`KANT-E4xx`). |
| **النقيضة** (*Antinomy*) | `antinomy` | Termination Engine | Non-terminating recursive calls, ungrounded loops, and deadlocks. | Recursive calls require well-founded `decreases` metric (`KANT-E5xx`). |
| **مبحث المنهج** (*Doctrine of Method*) | `method` | Backend Verification | Differential verification between reference interpreter and Cranelift JIT/AOT. | Dual-backend trace equivalence; cryptographic Merkle audit bundles. |
| **الأمثول** (*Amthoul*) | `amthoul` / `spec` | Specification View | Contract interface declaration extracting effect signatures and bounds. | Bijective synchronization between `.kant` source and `.spec` contracts. |
| **الحاكم / القاضي** (*Governor*) | `governor` | Capability Runtime | Algebraic effect handler and sandboxed capability execution supervisor. | Dispatches effect operations or suspends execution for approval gates. |

---

## 3. Formal Mapping: Epistemology to Martin-Löf Type Theory

Following Per Martin-Löf's *Analytic and Synthetic Judgments in Type Theory* (1994):

$$\begin{array}{rcl}
\text{Epistemological Construct} & \longleftrightarrow & \text{Constructive Type Theory} \\
\hline
\text{Pure Concept (الأفهوم)} & \longleftrightarrow & \text{Type } A \\
\text{Synthesized Term (الموضوع في الحدس)} & \longleftrightarrow & \text{Canonical Program / Proof Witness } a \\
\text{Categorical Judgment (الحكم)} & \longleftrightarrow & \text{Typing Judgment } a : A \\
\text{Analytic Truth (الحكم التحليلي)} & \longleftrightarrow & \text{Definitional Equality } a \equiv b : A \\
\text{Synthetic A Priori Proposition (الحكم التأليفي القبلي)} & \longleftrightarrow & \text{Propositional Identity Proof } p : \text{Id}_A(a, b) \\
\text{Quantity: Unity, Plurality, Totality (مقولات الكم)} & \longleftrightarrow & \text{Base Types, Slices, Sum Types } \sum_{i} T_i \\
\text{Quality: Reality, Negation, Limitation (مقولات الكيف)} & \longleftrightarrow & \text{Inhabitation, Bottom Type } \bot, \text{ Refinement Subtypes} \\
\text{Relation: Substance, Causality, Community (مقولات الإضافة)} & \longleftrightarrow & \text{Product Types } \prod_{i} T_i, \text{ Arrow Types } A \xrightarrow{!E} B, \text{ Stream Morphisms} \\
\text{Modality: Possibility, Actuality, Necessity (مقولات الجهة)} & \longleftrightarrow & \text{Option/Result Monads, Linear Capabilities, Const Invariants}
\end{array}$$

---

## 4. Dual Syntax Architecture & Closed Token Set

The language establishes an algebraic isomorphism between ASCII canonical representation and localized sidecar projections:

1. **Canonical ASCII Source (`.kant`):** Dense Latin ASCII keywords matching Wehbe's transliterated schema (`afhoum`, `shaym`, `noumenon`). Designed for minimal tokenization overhead, optimal LLM context packing, and unambiguous Lexer tokenization.
2. **Sidecar Visual Projection (`.kantd`):** A JSON-formatted sidecar file containing byte-span mappings to Arabic terms (*المُجاوِز، الأفهوم، الشَّيْم، النومان، الأمثول*) and source formatting without altering canonical definition hashes.

### The 48 Closed Lexical Tokens

The grammar operates over a closed alphabet of 48 lexical tokens:

```
// Top-Level Declarations
afhoum          shaym           noumenon        synthetic       decision
intent          requires        ensures         decreases       effects

// Effect & Governance Subsystem
pure            handle          with            governor        approval_gate
dyn             table           of              perform         resume

// Control Flow & Expression Binding
let             mut             if              else            match
return          const           proof           type            cap

// Categorical Judgment Descriptors
unity           plurality       totality        reality         negation
limitation      substance       causality       community       possible
actual          necessary       never           secret

// Delimiters, Operators & Sigils
:               ::              ->              !               ?hole
{               }               (               )               [               ]
,               ;               .               =               @
```
