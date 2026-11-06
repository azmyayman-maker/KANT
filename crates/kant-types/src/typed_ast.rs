use std::collections::BTreeMap;
use kant_core::{ByteSpan, DefHash, SymbolId};
use crate::category::KantianCategory;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Type {
    Unit,
    Bool,
    Int64,
    Float64,
    String,
    Never,
    Named(SymbolId),
    Reference(Box<Type>),
    Slice(Box<Type>),
    Tuple(Vec<Type>),
    Secret(Box<Type>),
    Capability(SymbolId),
    Function {
        params: Vec<Type>,
        return_type: Box<Type>,
    },
    Hole(u32),
}

impl Type {
    pub fn category(&self) -> KantianCategory {
        match self {
            Self::Unit | Self::Bool | Self::Int64 | Self::Float64 | Self::String => {
                KantianCategory::Unity
            }
            Self::Slice(_) | Self::Tuple(_) => KantianCategory::Plurality,
            Self::Named(_) => KantianCategory::Substance,
            Self::Never => KantianCategory::Negation,
            Self::Secret(_) => KantianCategory::Limitation,
            Self::Capability(_) => KantianCategory::Actuality,
            Self::Reference(_) => KantianCategory::Substance,
            Self::Function { .. } => KantianCategory::Causality,
            Self::Hole(_) => KantianCategory::Possibility,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TypedModule {
    pub name: String,
    pub functions: BTreeMap<DefHash, TypedFunction>,
    pub types: BTreeMap<SymbolId, Type>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TypedFunction {
    pub name: SymbolId,
    pub hash: DefHash,
    pub params: Vec<(SymbolId, Type)>,
    pub return_type: Type,
    pub effects: Vec<String>,
    pub body: TypedBlock,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TypedBlock {
    pub span: ByteSpan,
    pub stmts: Vec<TypedStmt>,
    pub trailing_expr: Option<Box<TypedExpr>>,
    pub ty: Type,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum TypedStmt {
    Let {
        span: ByteSpan,
        name: SymbolId,
        ty: Type,
        value: TypedExpr,
    },
    Expr(TypedExpr),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TypedExpr {
    pub span: ByteSpan,
    pub ty: Type,
    pub kind: TypedExprKind,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum TypedExprKind {
    LiteralInt(i64),
    LiteralFloat(String),
    LiteralString(String),
    LiteralBool(bool),
    Var(SymbolId),
    DeBruijnSlot(u32),
    Binary {
        op: String,
        lhs: Box<TypedExpr>,
        rhs: Box<TypedExpr>,
    },
    Unary {
        op: String,
        operand: Box<TypedExpr>,
    },
    Call {
        callee: Box<TypedExpr>,
        args: Vec<TypedExpr>,
    },
    FieldAccess {
        target: Box<TypedExpr>,
        field: SymbolId,
    },
    Block(TypedBlock),
    If {
        cond: Box<TypedExpr>,
        then_branch: TypedBlock,
        else_branch: Option<TypedBlock>,
    },
    Hole(u32),
}
