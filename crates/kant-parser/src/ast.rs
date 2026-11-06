use kant_core::{ByteSpan, SymbolId};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SourceFile {
    pub span: ByteSpan,
    pub has_magic_header: bool,
    pub items: Vec<ToplevelItem>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ToplevelItem {
    Decision(DecisionBlock),
    Type(TypeDef),
    Capability(CapabilityDef),
    Function(FunctionDef),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DecisionBlock {
    pub span: ByteSpan,
    pub name: SymbolId,
    pub fields: Vec<(SymbolId, String)>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TypeDef {
    pub span: ByteSpan,
    pub name: SymbolId,
    pub fields: Vec<StructField>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StructField {
    pub span: ByteSpan,
    pub name: SymbolId,
    pub ty: TypeExpr,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CapabilityDef {
    pub span: ByteSpan,
    pub name: SymbolId,
    pub permissions: Vec<CapPermission>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CapPermission {
    pub span: ByteSpan,
    pub name: SymbolId,
    pub params: Vec<TypeExpr>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FunctionDef {
    pub span: ByteSpan,
    pub is_pub: bool,
    pub name: SymbolId,
    pub params: Vec<Param>,
    pub return_type: TypeExpr,
    pub contracts: Option<ContractBlock>,
    pub body: BlockExpr,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Param {
    pub span: ByteSpan,
    pub name: SymbolId,
    pub ty: TypeExpr,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ContractBlock {
    pub span: ByteSpan,
    pub intent: Option<String>,
    pub requires: Vec<Expr>,
    pub ensures: Vec<Expr>,
    pub decreases: Option<Expr>,
    pub effects: Vec<EffectAtom>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EffectAtom {
    Pure,
    Named(String),
    Of(SymbolId),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum TypeExpr {
    Unit(ByteSpan),
    Primitive { span: ByteSpan, name: String },
    Named { span: ByteSpan, name: SymbolId },
    Reference { span: ByteSpan, inner: Box<TypeExpr> },
    Slice { span: ByteSpan, element: Box<TypeExpr> },
    Tuple { span: ByteSpan, elements: Vec<TypeExpr> },
    Never(ByteSpan),
    Secret { span: ByteSpan, inner: Box<TypeExpr> },
    Hole(ByteSpan),
}

impl TypeExpr {
    pub fn span(&self) -> ByteSpan {
        match self {
            Self::Unit(s)
            | Self::Primitive { span: s, .. }
            | Self::Named { span: s, .. }
            | Self::Reference { span: s, .. }
            | Self::Slice { span: s, .. }
            | Self::Tuple { span: s, .. }
            | Self::Never(s)
            | Self::Secret { span: s, .. }
            | Self::Hole(s) => *s,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BlockExpr {
    pub span: ByteSpan,
    pub stmts: Vec<Stmt>,
    pub trailing_expr: Option<Box<Expr>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Stmt {
    Let {
        span: ByteSpan,
        is_mut: bool,
        name: SymbolId,
        ty: Option<TypeExpr>,
        value: Expr,
    },
    Expr(Expr),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Expr {
    Literal {
        span: ByteSpan,
        lit: Literal,
    },
    Ident {
        span: ByteSpan,
        name: SymbolId,
    },
    DeBruijnSlot {
        span: ByteSpan,
        type_tag: String,
        index: u32,
    },
    Binary {
        span: ByteSpan,
        op: BinaryOp,
        lhs: Box<Expr>,
        rhs: Box<Expr>,
    },
    Unary {
        span: ByteSpan,
        op: UnaryOp,
        operand: Box<Expr>,
    },
    Call {
        span: ByteSpan,
        callee: Box<Expr>,
        args: Vec<Expr>,
    },
    FieldAccess {
        span: ByteSpan,
        target: Box<Expr>,
        field: SymbolId,
    },
    Block(BlockExpr),
    If {
        span: ByteSpan,
        cond: Box<Expr>,
        then_branch: BlockExpr,
        else_branch: Option<BlockExpr>,
    },
    Match {
        span: ByteSpan,
        scrutinee: Box<Expr>,
        arms: Vec<MatchArm>,
    },
    HandleWith {
        span: ByteSpan,
        body: BlockExpr,
        governor_arms: Vec<(EffectAtom, Expr)>,
    },
    DynQuarantine {
        span: ByteSpan,
        declared_targets: Vec<SymbolId>,
        callee: Box<Expr>,
        args: Vec<Expr>,
    },
    Hole {
        span: ByteSpan,
        expected_type: Option<Box<TypeExpr>>,
    },
}

impl Expr {
    pub fn span(&self) -> ByteSpan {
        match self {
            Self::Literal { span, .. }
            | Self::Ident { span, .. }
            | Self::DeBruijnSlot { span, .. }
            | Self::Binary { span, .. }
            | Self::Unary { span, .. }
            | Self::Call { span, .. }
            | Self::FieldAccess { span, .. }
            | Self::If { span, .. }
            | Self::Match { span, .. }
            | Self::HandleWith { span, .. }
            | Self::DynQuarantine { span, .. }
            | Self::Hole { span, .. } => *span,
            Self::Block(b) => b.span,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MatchArm {
    pub span: ByteSpan,
    pub pattern: Pattern,
    pub body: Expr,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Pattern {
    Wildcard(ByteSpan),
    Ident(ByteSpan, SymbolId),
    Literal(ByteSpan, Literal),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Literal {
    Int(i64),
    Float(String),
    String(String),
    Bool(bool),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum BinaryOp {
    Add,
    Sub,
    Mul,
    Div,
    Rem,
    Eq,
    NotEq,
    Lt,
    LtEq,
    Gt,
    GtEq,
    And,
    Or,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum UnaryOp {
    Neg,
    Not,
}
