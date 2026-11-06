# 03_ANALYTIC_CATEGORIES_AND_EFFECTS.md: Transcendental Analytic: Constructive 12-Categorical Type System & Algebraic Effect Quarantine

The **Transcendental Analytic** formalizes the logic of constructive judgment in `kantc`. It organizes the type system across the twelve categorical judgment forms of Martin-Löf type theory, enforces the Sigil Law of Exact Algebraic Effect Matching ($E_{\text{decl}} = E_{\text{inf}}$), and guarantees sound call-graph bounds via Quarantined Dynamism.

---

## 1. The 12 Categorical Judgment Forms in Type Theory

In constructive type theory, computational expressions are verified via judgments of the form $\Gamma \vdash e : \tau$, where typing context $\Gamma$ binds variables to types, $e$ is an expression term, and $\tau$ is a type. Types in Kant are structured into four triads:

```
                           THE 12 CATEGORICAL JUDGMENTS
                     ┌────────────────────────────────┐
                     │          1. QUANTITY           │
                     │  • Unity (Primitive Scalars)   │
                     │  • Plurality (Linear Slices)   │
                     │  • Totality (Exhaustive ADTs)  │
                     └────────────────┬───────────────┘
                                      │
     ┌────────────────────────────────┼────────────────────────────────┐
     │                                │                                │
┌────┴───────────────────────────┐    │    ┌───────────────────────────┴────┐
│          2. QUALITY            │    │    │          3. RELATION           │
│  • Reality (Inhabited Proofs)  │    │    │  • Substance (Product Records) │
│  • Negation (Bottom / Never !) │    │    │  • Causality (Effectful Arrows)│
│  • Limitation (Taint / Secrets)│    │    │  • Community (Stream Channels) │
└────────────────────────────────┘    │    └────────────────────────────────┘
                                      │
                     ┌────────────────┴───────────────┐
                     │          4. MODALITY           │
                     │  • Possibility (Option/Result) │
                     │  • Actuality (Live Cap Tokens) │
                     │  • Necessity (Verified Consts) │
                     └────────────────────────────────┘
```

### 1.1. Triad of Quantity
1. **Unity (`unity`):** Indivisible atomic scalar primitives.
   $$\Gamma \vdash c : \text{Int64}, \quad \Gamma \vdash b : \text{Bool}, \quad \Gamma \vdash f : \text{Float64}, \quad \Gamma \vdash () : \text{Unit}$$
2. **Plurality (`plurality`):** Homogeneous linear sequences and contiguous memory slices.
   $$\frac{\Gamma \vdash e_i : \tau \quad (0 \le i < N)}{\Gamma \vdash [e_0, \dots, e_{N-1}] : [ \tau ; N ]}, \quad \Gamma \vdash \text{slice} : \text{Slice}\langle \tau \rangle$$
3. **Totality (`totality`):** Exhaustive finite sum types and bounded refinement intervals.
   $$\tau = \sum_{k=1}^{M} C_k(\tau_k) \quad \text{where all variants are statically enumerated and matchable.}$$

### 1.2. Triad of Quality
1. **Reality (`reality`):** Inhabited types containing constructive proof witnesses.
   $$\Gamma \vdash e : \tau \quad \text{witnesses that type } \tau \text{ is non-empty.}$$
2. **Negation (`negation`):** The uninhabited bottom type $\bot$ (`!`).
   $$\frac{\Gamma \vdash e : !}{\Gamma \vdash \text{abort}(e) : \tau} \quad (\text{Principle of Explosion / Ex Falso Quodlibet})$$
3. **Limitation (`limitation`):** Information-flow taint wrappers and domain attenuations.
   $$\Gamma \vdash s : \text{Secret}\langle \tau \rangle \implies \text{Prohibits secret-dependent branches and index expressions.}$$

### 1.3. Triad of Relation
1. **Substance (`substance`):** Persistent product records (`afhoum`) with structural equality.
   $$\tau = \prod_{i=1}^{K} f_i : \tau_i, \quad \text{with deterministic alphabetical field layout.}$$
2. **Causality (`causality`):** Directed function arrows annotated with exact algebraic effects:
   $$\Gamma \vdash f : \tau_1 \xrightarrow{!E} \tau_2$$
3. **Community (`community`):** Synchronous typed stream channels (`!Stream<T>`) governing bidirectional message transmission under strict conservation laws.

### 1.4. Triad of Modality
1. **Possibility (`possible`):** Monadic failure envelopes for partial computable functions:
   $$\text{Option}\langle \tau \rangle \cong \tau + \text{Unit}, \quad \text{Result}\langle \tau, \epsilon \rangle \cong \tau + \epsilon$$
2. **Actuality (`actual`):** Unforgeable, linear hardware capability tokens certifying runtime authorization:
   $$\Gamma, c : \text{Cap}\langle \kappa \rangle \vdash \text{invoke}(c, \text{args}) : \tau \quad (\text{affine consumption: } c \text{ is moved}).$$
3. **Necessity (`necessary`):** Statically proven compile-time constants, invariant propositions, and SMT theorems verified prior to code emission:
   $$\Gamma \vdash \text{const } C : \tau = v, \quad \text{satisfying } \models_{\text{Z3}} \text{Invariant}(C).$$

---

## 2. Exact Algebraic Effect Matching (The Sigil Law)

Conventional languages treat side effects implicitly or through effect subtyping (subsumption), which permits pure functions to be silently coerced into effectful contexts and allows dead effects to accumulate undetected. Kant enforces **Exact Algebraic Effect Matching**:

$$\text{A function declaration } f \text{ is well-typed} \iff E_{\text{decl}}(f) = E_{\text{inf}}(f)$$

### 2.1. Invariant Violations and Machine Diagnostics
1. **Undeclared Effect Escape (`KANT-E301`):**
   * Condition: $E_{\text{inf}}(f) \setminus E_{\text{decl}}(f) \neq \emptyset$.
   * Semantic: An operation within $f$'s body invokes an effect not present in its declared signature.
   * Diagnostic: Halts compilation; generates RFC 6902 JSON patch with `FixSafety: SAFE` inserting the missing effect.
2. **Unused Declared Effect Drift (`KANT-E302`):**
   * Condition: $E_{\text{decl}}(f) \setminus E_{\text{inf}}(f) \neq \emptyset$.
   * Semantic: A declared effect is never triggered by $f$ or any of its transitive callees.
   * Diagnostic: Halts compilation; generates RFC 6902 JSON patch with `FixSafety: SAFE` stripping the superfluous effect.

### 2.2. The Core Primitive Effect Lattice

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

Unconstrained dynamic dispatch and raw function pointers destroy the static call graph, introducing unprovable side effects and breaking automated refactoring blast-radius analysis. Kant enforces **Quarantined Dynamism**:

* **Guarantee G1 (Sound Blast Radius):** Modifying a definition $D$ requires re-analyzing strictly the transitive callers registered in `EffectCallGraph.reverse_callers`.
* **Guarantee G2 (Complete Static Edges):** Every edge in the execution call graph is statically enumerated at compile time.
* **Guarantee G3 (Bounded Dynamic Dispatch):** Higher-order function dispatch is permitted exclusively through:
  1. Parameterized effect inheritance: `effects of(param)`.
  2. Bounded dynamic calls: `dyn { target_1, ..., target_n }(callee, args)`, where the compiler proves $callee \in \{ target_1, \dots, target_n \}$.
  3. Closed compile-time dispatch tables: `table Dispatcher { "opA" => fnA, "opB" => fnB }`.
* **Guarantee G4 (Exact Union Soundness):** The inferred effect set of a `dyn` invocation is the exact union of all declared targets:
  $$E_{\text{inf}}(\text{dyn } \{t_1, \dots, t_n\}) = \bigcup_{i=1}^{n} E_{\text{decl}}(t_i)$$
