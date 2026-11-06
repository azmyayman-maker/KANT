# 02_AESTHETICS_GRAMMAR_AND_AST.md: Transcendental Aesthetic, Flattened Grammar & Canonical AST

The **Transcendental Aesthetic** in Kant governs the a priori forms of sensibility: **Space** and **Time**. In the `kantc` compiler, this translates into how source text is perceived, structured, and given an invariant identity.

This specification details the **Flattened EBNF Grammar**, the **Closed Vocabulary Constraint**, and the **Canonicalization Pipeline** that produces content-addressed, 32-byte SHA-256 definition identities (`DefHash`).

---

## 1. Flattened Toplevel Design Principles

Deeply nested code structures (classes inside namespaces inside modules, or deeply nested local functions) cause frequent KV-cache misses in Transformer-based LLMs and require agents to maintain large contextual stacks. Following the empirical success of MoonBit (LLM4Code 2024), Kant enforces a **Flattened Toplevel Architecture**:

1. **No Nested Types or Functions:** All type definitions (`afhoum`), functions, decision blocks, and capability signatures exist strictly at the file toplevel.
2. **Explicit Dependency Bounds:** Functions access ambient context solely through explicit parameter lists or linear capability handles.
3. **Linear Scan & Infix Operators:** Expressions follow standard mathematical infix notation with shallow block depths, optimizing auto-regressive generation.

---

## 2. Complete Formal Grammar (EBNF)

```ebnf
(* Source File & Toplevel *)
SourceFile        ::= MagicHeader ToplevelItem* EOF
MagicHeader       ::= "#![kant(" VersionIdentifier ")]"
VersionIdentifier ::= "v0.1"

ToplevelItem      ::= DecisionBlock
                    | TypeDef
                    | CapabilityDef
                    | FunctionDef

(* Architectural Decision Records (ADRs in Code) *)
DecisionBlock     ::= "decision" Identifier "{" DecisionField* "}"
DecisionField     ::= Identifier ":" StringLiteral ";"

(* Types: The Pure Concepts (Afahim) *)
TypeDef           ::= "afhoum" Identifier "{" StructField* "}"
StructField       ::= Identifier ":" TypeExpr ";"

CapabilityDef     ::= "cap" Identifier "{" CapPermission* "}"
CapPermission     ::= Identifier "(" TypeExpr* ")" ";"

(* Function Declarations with Mandatory Epistemic Contracts *)
FunctionDef       ::= "pub"? "fn" Identifier "(" ParamList? ")" "->" TypeExpr
                      ContractBlock?
                      "=" BlockExpr

ParamList         ::= Param ("," Param)*
Param             ::= Identifier ":" TypeExpr

ContractBlock     ::= "{" ContractClause* "}"
ContractClause    ::= IntentClause
                    | RequiresClause
                    | EnsuresClause
                    | DecreasesClause
                    | EffectsClause

IntentClause      ::= "intent" StringLiteral
RequiresClause    ::= "requires" Expr
EnsuresClause     ::= "ensures" Expr
DecreasesClause   ::= "decreases" Expr
EffectsClause     ::= "effects" EffectSet

EffectSet         ::= "pure" | (EffectAtom ("," EffectAtom)*)
EffectAtom        ::= Identifier ("." Identifier)?
                    | "of" "(" Identifier ")"

(* Types *)
TypeExpr          ::= PrimitiveType
                    | Identifier
                    | "&" TypeExpr
                    | "[" TypeExpr "]"
                    | "(" (TypeExpr ("," TypeExpr)*)? ")"
                    | "!"

PrimitiveType     ::= "Unit" | "Bool" | "Int64" | "Float64" | "String" | "Secret" "<" TypeExpr ">"

(* Expressions *)
BlockExpr         ::= "{" Stmt* Expr? "}"
Stmt              ::= LetStmt | ExprStmt ";"
LetStmt           ::= "let" "mut"? Identifier (":" TypeExpr)? "=" Expr ";"
ExprStmt          ::= Expr

Expr              ::= IfExpr
                    | MatchExpr
                    | HandleExpr
                    | DynQuarantineExpr
                    | HoleExpr
                    | BinaryExpr

HoleExpr          ::= "?hole" (":" TypeExpr)?
DynQuarantineExpr ::= "dyn" "{" TargetList "}" "(" Expr ("," Expr)* ")"
TargetList        ::= Identifier ("," Identifier)*

HandleExpr        ::= "handle" BlockExpr "with" "governor" "{" HandlerArm* "}"
HandlerArm        ::= EffectAtom "->" Expr

IfExpr            ::= "if" Expr BlockExpr ("else" BlockExpr)?
MatchExpr         ::= "match" Expr "{" MatchArm* "}"
MatchArm          ::= Pattern "=>" Expr ","?
Pattern           ::= Identifier | Literal | "_"

BinaryExpr        ::= UnaryExpr (BinaryOp UnaryExpr)*
BinaryOp          ::= "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<" | "<=" | ">" | ">=" | "&&" | "||"
UnaryExpr         ::= ("-" | "!")? AtomExpr
AtomExpr          ::= Literal
                    | Identifier
                    | DeBruijnSlot
                    | CallExpr
                    | FieldAccess
                    | "(" Expr ")"

DeBruijnSlot      ::= "@" Identifier "." IntegerLiteral
CallExpr          ::= Identifier "(" (Expr ("," Expr)*)? ")"
FieldAccess       ::= AtomExpr "." Identifier
Literal           ::= IntegerLiteral | FloatLiteral | StringLiteral | BoolLiteral
```

---

## 3. Canonicalization Rules & SHA-256 Identity (Space)

In the Transcendental Aesthetic, **Space** corresponds to the invariant content-addressed identity of code. Two functions that differ only in formatting, variable names, or comments represent the exact same mathematical entity.

The Canonicalizer converts a `SurfaceAST` into a `CanonicalAST` via five strict deterministic rules:

1. **Rule C1 (De Bruijn Slot Alpha-Conversion):**
   * Replace all formal parameter names with `@T.0`, `@T.1`, etc., ordered by declaration position.
   * Replace all local `let` bindings with scope-relative De Bruijn indices (`@T.k`).
   * Preserve original identifier names exclusively in the sidecar metadata file (`module.kantd`).

2. **Rule C2 (Alphabetical Normalization):**
   * Sort all struct field definitions alphabetically by field identifier.
   * Sort all declared atomic effects alphabetically in the canonical effect set (e.g., `[fs.read, net.http]` instead of `[net.http, fs.read]`).

3. **Rule C3 (Content-Addressed Cross-References):**
   * Replace references to imported external definitions with their pinned 32-byte hexadecimal content hashes (`0x3f7a...`).

4. **Rule C4 (Recursive Self-Reference Invariance):**
   * In recursive calls, replace the function name identifier with a fixed `@self` token so that renaming a recursive function does not alter its canonical hash.

5. **Rule C5 (Lexical Stripping & Hash Computation):**
   * Strip all comments, docstrings, and whitespace.
   * Serialize the normalized AST into canonical binary bytes (deterministic CBOR or canonical JSON).
   * Compute the 32-byte digest:
     $$\text{DefHash} = \text{SHA-256}(\text{CanonicalBytes})$$

---

## 4. Typed Hole Nodes (`?hole`)

AI agents frequently construct programs incrementally. To support partial compilation, type-inference queries, and AST repairs without syntax crashes:

* A typed hole `?hole` or `?hole: T` is a valid AST expression node (`Expr::Hole`).
* When the parser encounters `?hole`, it builds a valid AST node tagged with a unique `HoleId`.
* The type checker assigns the hole a unification type variable $\tau_{\text{hole}}$ and infers its required type context from enclosing expressions.
* The effect checker tracks the available effect budget for the hole without failing compilation.
* Emits a structured diagnostic (`KANT-I001`) with the expected type and permitted effect set, enabling the agent to fill the hole with precision.
