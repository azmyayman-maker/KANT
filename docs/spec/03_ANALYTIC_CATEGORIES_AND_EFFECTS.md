# 03_ANALYTIC_CATEGORIES_AND_EFFECTS.md: Transcendental Analytic, 12 Categories & Exact Effects

The **Transcendental Analytic** is Kant's "Logic of Truth." It deduces the pure concepts of the understanding (*Afahim*) from the logical table of judgments into four fundamental triads (Quantity, Quality, Relation, Modality), establishing the rules that allow sensibility to yield objective knowledge.

In `kantc`, the Analytic governs the **12-Categories Type System**, **Exact Effect Matching**, and **Quarantined Dynamism**.

---

## 1. The 12 Categories of the Understanding in Type Theory

Each Kantian category corresponds to an exact structural concept in the `kant-types` type system:

```
                              THE 12 CATEGORIES
                     ┌────────────────────────────────┐
                     │          1. QUANTITY           │
                     │  • Unity (Primitives)          │
                     │  • Plurality (Collections)     │
                     │  • Totality (Exhaustive Sums)  │
                     └────────────────┬───────────────┘
                                      │
     ┌────────────────────────────────┼────────────────────────────────┐
     │                                │                                │
┌────┴───────────────────────────┐    │    ┌───────────────────────────┴────┐
│          2. QUALITY            │    │    │          3. RELATION           │
│  • Reality (Inhabited Types)   │    │    │  • Substance (Struct Values)   │
│  • Negation (Never / !)        │    │    │  • Causality (Effectful Arrows)│
│  • Limitation (Refinements)    │    │    │  • Community (Stream Channels) │
└────────────────────────────────┘    │    └────────────────────────────────┘
                                      │
                     ┌────────────────┴───────────────┐
                     │          4. MODALITY           │
                     │  • Possibility (Option/Result) │
                     │  • Actuality (Live Cap Handles)│
                     │  • Necessity (Proved Consts)   │
                     └────────────────────────────────┘
```

### 1.1. Triad of Quantity (مقولات الكم)
1. **Unity (الوحدة):** Indivisible atomic values.
   * Represented by `Unit`, `Bool`, `Int64`, `Float64`, `String`.
2. **Plurality (الكثرة):** Ordered or aggregated repetitions of items.
   * Represented by `Slice<T>`, `Vec<T>`, and fixed arrays `[T; N]`.
3. **Totality (الجملة):** The complete universe of forms bounded as a whole.
   * Represented by **Exhaustive Sum Types (ADTs)** where every case is known, and **Bounded Refinement Types** (`Int64 where value >= 0 && value < 1024`).

### 1.2. Triad of Quality (مقولات الكيف)
1. **Reality (الواقع):** Affirmative, inhabited types containing valid constructive proofs.
   * Any inhabited type `T` where values can be soundly constructed.
2. **Negation (النفي):** The uninstantiable bottom type.
   * Represented by `Never` (`!`). A function returning `!` never returns normally (aborts or diverges).
3. **Limitation (الحصر):** Attenuation and restriction of a domain.
   * Represented by `Refined<T, P>` and **Attenuated Capabilities** (e.g., restricting a `FsCapability` to a read-only subdirectory `cap.attenuate_subpath("/tmp")`).

### 1.3. Triad of Relation (مقولات الإضافة)
1. **Substance and Inherence (الجوهر والعَرَض):** The persistent entity and its dependent attributes.
   * Represented by immutable value structs (`afhoum Point { x: Int64, y: Int64 }`). Value identity is structural.
2. **Causality and Dependence (العلية والمعلولية):** Action and deterministic transition.
   * Represented by function arrow signatures with explicit effect sets:
     $$f : A \xrightarrow{!E} B$$
3. **Community and Reciprocity (المفاعلة والتفاعل المتبادل):** Mutual simultaneous interaction.
   * Represented by **Typed Stream Channels** (`!Stream<T>`) supporting category-theoretic morphisms: `copy`, `discard`, `merge`, and `barrier`.

### 1.4. Triad of Modality (مقولات الجهة)
1. **Possibility / Impossibility (الإمكان والامتناع):** Logical consistency without guaranteed physical presence.
   * Represented by `Option<T>` (`Some(T) | None`) and `Result<T, E>`.
2. **Actuality / Non-existence (التحقق واللاتحقق):** Physical existence in the current execution session.
   * Represented by **Linear Capability Tokens** (`cap &Cap`). A capability handle cannot be forged or duplicated; its runtime presence certifies empirical authorization.
3. **Necessity / Contingency (الضرورة والاتفاق):** Universal invariance under all possible executions.
   * Represented by compile-time evaluated constants (`const N: Int64`), statically verified theorems, and immutable invariants verified by Z3 SMT solving.

---

## 2. Exact Effect Matching (The Sigil Law)

Traditional languages treat effect systems via subtyping (effect subsumption), allowing pure functions to be silently coerced into effectful contexts or ignoring unused effect declarations. In `kantc`, we enforce **Exact Effect Matching**:

$$\text{Function } f \text{ is valid} \iff E_{\text{decl}}(f) = E_{\text{inf}}(f)$$

### Two Invariant Violations:
1. **Undeclared Effect Escape (`KANT-E301`):**
   * Condition: $E_{\text{inf}}(f) \setminus E_{\text{decl}}(f) \neq \emptyset$.
   * Action: The compiler halts. Emits a structured diagnostic with `FixSafety: SAFE` and an RFC 6902 JSON Patch adding the missing effect.
2. **Unused Declared Effect Drift (`KANT-E302`):**
   * Condition: $E_{\text{decl}}(f) \setminus E_{\text{inf}}(f) \neq \emptyset$.
   * Action: The compiler halts. Emits a structured diagnostic with `FixSafety: SAFE` and an RFC 6902 JSON Patch removing the dead effect annotation.

### The Primitive Effect Lattice
```
                    [All Noumena Effects]
               /       |        |        \
        [fs.write] [net.http] [ai.infer] [clock.now]
               \       |        |        /
              [fs.read]      [console.write]
                     \        /
                    [console.read]
                          |
                       [pure]
```

---

## 3. Quarantined Dynamism (Guarantees G1–G4)

Unconstrained higher-order functions or raw function pointers create invisible edges in the call graph, preventing agents from knowing the true blast radius of edits. Following the formalization in *rigid*, Kant enforces **Quarantined Dynamism**:

* **Guarantee G1 (Sound Blast Radius):** Modifying definition $D$ requires re-analyzing only the transitive callers recorded in `EffectCallGraph.reverse_callers`.
* **Guarantee G2 (Complete Static Edges):** Every potential execution flow is statically represented.
* **Guarantee G3 (Bounded Dynamic Dispatch):** Higher-order function invocation is permitted ONLY via:
  1. `effects of(param)` where the parameter's effect is inherited directly.
  2. `dyn { target_1, ..., target_n }(callee, args)` where the callee's runtime value is formally proven to belong to the closed set $\{ \text{target}_1, \dots, \text{target}_n \}$.
  3. Static closed dispatch tables (`table Dispatcher { "opA" => fnA, "opB" => fnB }`).
* **Guarantee G4 (Determinism):** Dynamic calls inherit the exact union of all declared targets' effects:
  $$E_{\text{inf}}(\text{dyn } \{t_1, \dots, t_n\}) = \bigcup_{i=1}^{n} E_{\text{decl}}(t_i)$$
