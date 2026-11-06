# 02_AESTHETICS_GRAMMAR_AND_AST.md: Transcendental Aesthetic: Constructive Spatial Normalization, EBNF Grammar & Canonical AST

The **Transcendental Aesthetic** formalizes the constructive spatial and temporal normalization of programs in the `kantc` toolchain. Spatial normalization governs lexical scanning, grammar parsing, De Bruijn index conversion, and deterministic content-addressed identification (`DefHash`). Temporal normalization governs instruction ordering in Static Single Assignment (SSA) intermediate representation.

---

## 1. Flattened Top-Level Architecture Principles

To optimize parsing velocity, eliminate deep contextual stacks in automated reasoning tools, and prevent KV-cache context misses in autoregressive LLMs, Kant enforces a **Flattened Top-Level Architecture**:

1. **Zero Nesting of Types or Functions:** All struct definitions (`afhoum`), function declarations (`fn`), capability definitions (`cap`), and architectural decision blocks (`decision`) exist strictly at the file top-level. Nested function or class declarations are disallowed by the grammar.
2. **Explicit Dependency Bounds:** Global variables and ambient execution environments are prohibited. Functions access execution contexts exclusively via explicit parameter lists or linear capability handles.
3. **Infix Expressions with Bounded Precedence:** Expressions follow standard infix notation with shallow block nesting to facilitate deterministic single-pass Pratt precedence parsing.

---

## 2. The 48 Closed Lexical Tokens

The lexical analyzer (`kant-lexer`) operates on an invariant, closed set of 48 reserved tokens, preventing arbitrary macro or keyword inflation:

1. **Top-Level Keywords (10):** `afhoum`, `shaym`, `noumenon`, `synthetic`, `decision`, `intent`, `requires`, `ensures`, `decreases`, `effects`.
2. **Effect & Governance Keywords (10):** `pure`, `handle`, `with`, `governor`, `approval_gate`, `dyn`, `table`, `of`, `perform`, `resume`.
3. **Control & Binding Keywords (10):** `let`, `mut`, `if`, `else`, `match`, `return`, `const`, `proof`, `type`, `cap`.
4. **Categorical Descriptors (14):** `unity`, `plurality`, `totality`, `reality`, `negation`, `limitation`, `substance`, `causality`, `community`, `possible`, `actual`, `necessary`, `never`, `secret`.
5. **Punctuation & Delimiters (14):** `:`, `::`, `->`, `!`, `?hole`, `{`, `}`, `(`, `)`, `[`, `]`, `,`, `;`, `.`, `=`, `@`.

---

## 3. Formal EBNF Grammar

```ebnf
(* Source File & Compilation Unit *)
SourceFile        ::= MagicHeader ToplevelItem* EOF
MagicHeader       ::= "#![kant(" VersionIdentifier ")]"
VersionIdentifier ::= "v0.1"

ToplevelItem      ::= DecisionBlock
                    | TypeDef
                    | CapabilityDef
                    | FunctionDef

(* Architectural Decision Records (ADRs) Embedded in AST *)
DecisionBlock     ::= "decision" Identifier "{" DecisionField* "}"
DecisionField     ::= Identifier ":" StringLiteral ";"

(* Pure Concept Type Definitions (Product Types) *)
TypeDef           ::= "afhoum" Identifier "{" StructField* "}"
StructField       ::= Identifier ":" TypeExpr ";"

(* Capability Declarations *)
CapabilityDef     ::= "cap" Identifier "{" CapPermission* "}"
CapPermission     ::= Identifier "(" TypeExpr* ")" ";"

(* Function Definitions with Epistemic Contracts *)
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

(* Type Expressions *)
TypeExpr          ::= PrimitiveType
                    | Identifier
                    | "&" TypeExpr
                    | "[" TypeExpr "]"
                    | "(" (TypeExpr ("," TypeExpr)*)? ")"
                    | "!"

PrimitiveType     ::= "Unit" | "Bool" | "Int64" | "Float64" | "String" | "Secret" "<" TypeExpr ">"

(* Statements & Expressions *)
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

## 4. Canonical AST & Content-Addressed Identity ($I_1$)

The Canonicalizer pass (`kant-canonical`) transforms a raw `SurfaceAST` into a normalized `CanonicalAST`. Two code fragments that differ solely in formatting, comments, or local identifier names produce an identical cryptographic hash.

### 4.1. The Five Canonicalization Transformations

1. **Rule C1: De Bruijn Slot Alpha-Conversion:**
   * Function parameter identifiers are mapped to positional indices `@T.0`, `@T.1`, ..., `@T.k-1`.
   * Local variable bindings introduced via `let` are transformed into scope-relative De Bruijn indices.
   * Original variable names are preserved exclusively in the non-semantic sidecar file (`module.kantd`).
2. **Rule C2: Alphabetical Ordering:**
   * Fields in struct declarations (`afhoum`) are sorted lexicographically by field identifier.
   * Atomic effect sets are sorted lexicographically (e.g., `[fs.read, net.http]` instead of `[net.http, fs.read]`).
3. **Rule C3: Content-Addressed Import Binding:**
   * External imported symbol references are resolved and replaced by their pinned 32-byte hexadecimal hash (`0x...`).
4. **Rule C4: Fixed-Point Self-Reference Invariance:**
   * In recursive invocations, the function identifier is replaced with `@self`, ensuring that renaming a recursive function does not alter its canonical hash.
5. **Rule C5: Deterministic Serialization & Hashing:**
   * All comments, docstrings, and non-semantic whitespace are stripped.
   * The canonical AST is serialized into deterministic canonical binary format (deterministic CBOR or canonical JSON).
   * The 32-byte SHA-256 digest is computed:
     $$\text{DefHash} = \text{SHA-256}(\text{CanonicalSerializedBytes})$$

---

## 5. Typed Hole Expressions (`?hole`)

To facilitate incremental program synthesis, interactive type inspection, and automated code repair without causing parse failures:

1. **Syntactic Representation:** A typed hole is authored as `?hole` or `?hole: T`, parsed as `Expr::Hole(HoleId, Option<TypeExpr>)`.
2. **Type Inference Integration:** The type checker creates a fresh unification variable $\tau_{\text{hole}}$ and infers its required type from the enclosing typing context $\Gamma$.
3. **Effect Budget Propagation:** The effect system tracks available ambient effects at the hole's lexical site.
4. **Structured Diagnostic Emission:** The compiler generates a non-fatal diagnostic `KANT-I001` containing the inferred expected type, available variables in scope, and allowed effect budget:
   ```json
   {
     "code": "KANT-I001",
     "severity": "INFO",
     "span": [88, 93],
     "expected_type": "Int64",
     "effect_budget": ["pure"],
     "in_scope": [
       {"name": "n", "type": "Int64", "slot": "@T.0"}
     ]
   }
   ```
