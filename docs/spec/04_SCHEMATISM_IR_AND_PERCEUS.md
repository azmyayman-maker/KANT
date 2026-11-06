# 04_SCHEMATISM_IR_AND_PERCEUS.md: The Schematism: 30-Op Static Single Assignment (SSA) KANT-IR & Perceus Drop-Guided Reuse

The **Schematism** (*Al-Shaym* / الشَّيْم) formalizes the intermediate lowering layer that bridges pure categorical type declarations to concrete machine operations. In the `kantc` toolchain, this is embodied in **KANT-IR**, a 30-operation Static Single Assignment (SSA) intermediate representation coupled with the **Perceus reference-counting memory engine**, guaranteeing deterministic $\mathcal{O}(1)$ memory reclamation and drop-guided in-place reuse (`Alloc@r`).

---

## 1. KANT-IR: Static Single Assignment (SSA) Architecture

KANT-IR models execution time as a directed index category where every value is bound to a unique SSA value identifier ($v_0, v_1, \dots$). Values are strictly defined prior to their consumption, forming a directed acyclic graph within each basic block.

### The 30 Canonical KANT-IR SSA Opcode Table

| Category | Opcode & Signature | Operands | Output Type | Operational Semantics & Side Effects |
| :--- | :--- | :--- | :--- | :--- |
| **1. Literals & Allocation** | `ConstInt(v: i64)` | Immediate $v$ | `Int64` | Materializes 64-bit two's complement integer. |
| | `ConstFloat(v: f64)` | Immediate $v$ | `Float64` | Materializes IEEE-754 64-bit float. |
| | `ConstBool(v: bool)` | Immediate $v$ | `Bool` | Materializes boolean truth value. |
| | `ConstString(v: String)` | Immediate $v$ | `String` | Materializes immutable UTF-8 string pointer and length. |
| | `AllocStruct(type_id, fields)` | Type tag, $[v_0, \dots, v_{k-1}]$ | Pointer to struct | Allocates heap record initialized with field operands. |
| | `AllocUnion(tag, val)` | Variant tag, $v$ | Pointer to sum type | Allocates tagged union cell wrapping value $v$. |
| **2. Memory & Perceus RC** | `Dup(val_id)` | SSA value $v$ | `Unit` | Increments reference count: $R(v) \leftarrow R(v) + 1$. |
| | `Drop(val_id)` | SSA value $v$ | `Unit` | Decrements $R(v)$; frees memory if $R(v) = 0$. |
| | `AllocReuse(reuse_tok, type_id, fields)` | Reuse handle $r$, fields | Pointer to struct | Recycles dropped buffer in place if $R(v) = 1$. |
| | `GetField(val_id, idx)` | Base pointer $v$, index $i$ | Field type | Reads value at structural field offset $i$. |
| | `SetField(val_id, idx, new_val)` | Base pointer $v$, index $i$, $w$ | `Unit` | Destructive in-place field write (permitted only when $R(v) = 1$). |
| **3. Arithmetic & Logic** | `Add(l, r)` | Values $l, r$ | Numeric | Two's-complement addition or IEEE-754 float add. |
| | `Sub(l, r)` | Values $l, r$ | Numeric | Two's-complement subtraction or float sub. |
| | `Mul(l, r)` | Values $l, r$ | Numeric | Integer/floating-point multiplication. |
| | `Div(l, r)` | Values $l, r$ | Numeric | Division; traps on integer divide-by-zero. |
| | `Rem(l, r)` | Values $l, r$ | Numeric | Integer remainder operation. |
| | `Neg(val)` | Value $v$ | Numeric | Arithmetic negation. |
| | `Eq(l, r)` | Values $l, r$ | `Bool` | Structural or bitwise equality predicate. |
| | `Ne(l, r)` | Values $l, r$ | `Bool` | Structural or bitwise inequality predicate. |
| | `Lt(l, r)` | Values $l, r$ | `Bool` | Less-than signed/float relational comparison. |
| | `Le(l, r)` | Values $l, r$ | `Bool` | Less-than-or-equal relational comparison. |
| | `Gt(l, r)` | Values $l, r$ | `Bool` | Greater-than relational comparison. |
| | `Ge(l, r)` | Values $l, r$ | `Bool` | Greater-than-or-equal relational comparison. |
| **4. Control Flow** | `Jump(target_block, args)` | Target block label, $[v_i]$ | Bottom (`!`) | Unconditional branch transferring control to basic block. |
| | `Branch(cond, then_b, else_b)` | Boolean condition, blocks | Bottom (`!`) | Conditional branch based on boolean predicate. |
| | `Return(val_id)` | Return value $v$ | Bottom (`!`) | Returns control and result to caller frame. |
| | `Unreachable` | None | Bottom (`!`) | Traps execution; unreachable assertion failure. |
| **5. Function Calls** | `CallDirect(fn_hash, args)` | 32-byte `DefHash`, $[v_i]$ | Callee return type | Static direct dispatch to content-addressed function. |
| | `CallDyn(target_hashes, callee, args)`| Closed set $\{h_i\}$, callee, $[v_i]$| Callee return type | Bounded dynamic call with verified target bounds. |
| **6. Algebraic Effects** | `Perform(effect_id, args)` | Effect token, $[v_i]$ | Suspended resume | Delimited control trap capturing execution stack frame. |
| | `HandleWith(body_fn, gov_fn)` | Body closure, governor | Result type | Installs delimited effect handler around body expression. |
| | `Resume(continuation_id, val)` | Delimited continuation, $v$ | Continuation return | Resumes captured stack frame with provided value. |

---

## 2. Perceus Reference-Counting Memory Engine

Kant eliminates tracing garbage collection pauses and manual pointer management by adopting the **Perceus reference-counting algorithm** (proven in Koka and Lean 4):

### 2.1. Invariant $I_3$: Zero-GC Cyclic-Free Soundness
* **No Direct Pointer Cycles:** The type system disallows unmediated recursive pointer cycles. Self-referential graph structures must be indexed via explicit Arena handles (`ArenaIdx<T>`).
* **Deterministic Destructor Placement:** Every allocated variable $v$ has an inferred reference count $R(v)$. The compiler inserts `Drop(v)` immediately following its syntactically last use in time:
  $$\forall v, \quad \text{Drop}(v) \in \text{Successors}(\text{LastUse}(v))$$
* **$\mathcal{O}(1)$ Reclamation:** Heap cells are deallocated deterministically at the exact moment their reference count drops to zero, guaranteeing bounded memory overhead with zero sweep-phase latency spikes.

---

## 3. Drop-Guided In-Place Reuse (`Alloc@r`)

The core optimization of the Perceus pass (`kant-perceus`) is **Drop-Guided Reuse**. When an immutable data structure has a reference count of 1 and is subsequently dropped, its allocated heap memory is not released to the system allocator. If an allocation of matching layout occurs in the same lexical scope, the existing memory cell is recycled in place:

$$\text{match } x \text{ with } \text{Cons}(hd, tl) \implies \text{drop}(x) \ ; \ \text{let } y = \text{Cons}(hd + 1, tl) \quad \longrightarrow \quad \text{Cons}@r(x, hd + 1, tl)$$

### Operational Semantics:
1. **Dynamic Reference Check:** At the reuse site, the runtime inspects $R(x)$.
2. **Fast Path ($R(x) = 1$):** Memory allocation is bypassed. The fields of $x$ are overwritten directly in place with new values, matching the throughput and cache locality of destructive C mutations while preserving functional immutability semantics.
3. **Slow Path ($R(x) > 1$):** Data is shared across threads or bindings. A fresh memory cell is requested from the thread-local allocator.
4. **Frame-Limited Reuse Invariant:** Reuse tokens (`@r`) are strictly scoped within the active stack frame and cannot escape across unbounded stack boundaries.

---

## 4. Delimited Algebraic Effects & Continuation Lowering

* **`Perform` Lowering:** Emits a delimited trap instruction that reifies stack frames up to the matching `HandleWith` frame into a heap-allocated continuation token (`ContId`).
* **`Resume` Lowering:** Dispatches into the continuation entry point as a linear function, releasing the captured activation record upon termination.
* **Governor Runtime:** Evaluates handler expressions deterministically or suspends execution when interfacing with external Noumena capability handlers.
