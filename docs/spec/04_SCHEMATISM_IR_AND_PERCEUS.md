# 04_SCHEMATISM_IR_AND_PERCEUS.md: Al-Shaym (The Schematism), SSA IR & Perceus Memory

In the *Critique of Pure Reason*, the **Schematism of the Pure Concepts of the Understanding** (*Von dem Schematismus der reinen Verstandesbegriffe*) resolves the core mystery of Kant's epistemology: how can pure, non-sensible categories be applied to sensible appearances? 

Moussa Wehbe translates *Schema* as **Al-Shaym** (الشيم), evoking the Arab idiom "شيم البرق" (tracing the temporal manifestation of the unseen flash). In the `kantc` compiler, **Al-Shaym is the intermediate lowering layer (KANT-IR)** that temporalizes abstract categories into sequential machine operations, precise memory lifetimes, and in-place buffer recycling.

---

## 1. KANT-IR: Static Single Assignment (SSA) Representation

KANT-IR formalizes Time as a **Directed Index Category** ($\mathcal{T}$). Every basic block is an ordered sequence of SSA value definitions, where each value is defined exactly once and consumed along directed morphisms.

### The 30 Canonical KANT-IR Instructions

```
// 1. Literal & Value Construction
ConstInt(v: i64)                ConstFloat(v: f64)              ConstBool(v: bool)
ConstString(v: String)          AllocStruct(type_id, fields)    AllocUnion(tag, val)

// 2. Memory & Perceus Reference Counting
Dup(val_id)                     Drop(val_id)                    AllocReuse(reuse_tok, type_id, fields)
GetField(val_id, idx)           SetField(val_id, idx, new_val)

// 3. Arithmetic & Comparison
Add(l, r)                       Sub(l, r)                       Mul(l, r)
Div(l, r)                       Rem(l, r)                       Neg(val)
Eq(l, r)                        Ne(l, r)                        Lt(l, r)
Le(l, r)                        Gt(l, r)                        Ge(l, r)

// 4. Control Flow & Jumps
Jump(target_block, args)        Branch(cond, then_block, else_block)
Return(val_id)                  Unreachable

// 5. Functions & Higher-Order Calls
CallDirect(fn_hash, args)       CallDyn(target_hashes, callee, args)

// 6. Algebraic Effects & Continuations
Perform(effect_id, args)        HandleWith(body_fn, governor_fn)
Resume(continuation_id, val)
```

---

## 2. Perceus Garbage-Free Reference Counting

Unlike Python, Go, or Java which rely on a non-deterministic tracing Garbage Collector (GC), and unlike Rust which burdens AI agents with intricate borrow-checker lifetimes, Kant adopts the **Perceus algorithm** (as proven in Koka and Lean 4):

1. **Cycle-Free Structural Soundness:** Circular pointer references are prohibited by the type system (following Lean 4). Any graph or cyclic structure must use explicit Arena Indices (`ArenaIdx<T>`).
2. **Deterministic Destructors:** For any value $x$, `drop(x)` is inserted immediately following its syntactically last use in time.
3. **Zero Leaks:** A program with no cyclic references that finishes its execution path frees 100% of allocated heap memory without any sweep phase or runtime latency spikes.

---

## 3. Drop-Guided In-Place Reuse (Alloc@r)

The critical performance innovation of Perceus in `kantc` is **Drop-Guided Reuse**:

When a data structure (e.g., a node in an immutable tree or list) has a reference count of 1 and is about to be dropped, its memory cell is not returned to the global OS allocator. Instead, if an allocation of the same memory size occurs in the same lexical frame, the dropped cell is recycled in-place:

$$\text{match } x \text{ with } \text{Cons}(hd, tl) \implies \text{drop}(x) \ ; \ \text{let } y = \text{Cons}(hd + 1, tl) \quad \longrightarrow \quad \text{Cons}@r(x, hd + 1, tl)$$

### Invariant: Frame-Limited Reuse
* A reuse token `@r` is strictly scoped within the executing stack frame.
* If the reference count of $x > 1$ (shared data), Perceus falls back to standard allocation; if $\text{RC} == 1$, it executes a destructive in-place mutation of the existing memory buffer, providing the speed of imperative C with the mathematical purity of functional programming.

---

## 4. Algebraic Effects & Continuation Lowering

* **Perform:** Lowered into a runtime trap that captures the activation frame up to the nearest enclosing `HandleWith` boundary.
* **Resume:** Invokes the reified continuation as an ordinary linear function, releasing the captured stack frame when finished.
* **Governor Runtime:** Evaluates handler arms deterministically or suspends execution for interactive human-in-the-loop approvals.
