use std::collections::BTreeMap;
use kant_canonical::CanonicalModule;
use kant_core::{ByteSpan, DefHash, SymbolId};
use kant_parser::*;
use crate::typed_ast::*;

pub struct TypeChecker {
    types: BTreeMap<SymbolId, Type>,
    env: BTreeMap<SymbolId, Type>,
    hole_counter: u32,
}

impl TypeChecker {
    pub fn new() -> Self {
        let mut types = BTreeMap::new();
        types.insert(SymbolId::new("Unit"), Type::Unit);
        types.insert(SymbolId::new("Bool"), Type::Bool);
        types.insert(SymbolId::new("Int64"), Type::Int64);
        types.insert(SymbolId::new("Float64"), Type::Float64);
        types.insert(SymbolId::new("String"), Type::String);

        Self {
            types,
            env: BTreeMap::new(),
            hole_counter: 0,
        }
    }

    pub fn check_module(
        &mut self,
        file: &SourceFile,
        canonical: &CanonicalModule,
    ) -> Result<TypedModule, String> {
        let mut functions = BTreeMap::new();

        // Pass 1: Register all toplevel types
        for item in &file.items {
            if let ToplevelItem::Type(t) = item {
                self.types.insert(t.name.clone(), Type::Named(t.name.clone()));
            }
        }

        // Pass 2: Typecheck function signatures and bodies
        for item in &file.items {
            if let ToplevelItem::Function(f) = item {
                let canon_def = canonical
                    .definitions
                    .get(&f.name)
                    .ok_or_else(|| format!("Missing canonical definition for {}", f.name))?;
                let hash = canon_def.def_hash();

                let typed_fn = self.check_function(f, hash)?;
                functions.insert(hash, typed_fn);
            }
        }

        Ok(TypedModule {
            name: "main".to_string(),
            functions,
            types: self.types.clone(),
        })
    }

    fn check_function(&mut self, f: &FunctionDef, hash: DefHash) -> Result<TypedFunction, String> {
        self.env.clear();

        let mut params = Vec::new();
        for p in &f.params {
            let ty = self.resolve_type_expr(&p.ty);
            self.env.insert(p.name.clone(), ty.clone());
            params.push((p.name.clone(), ty));
        }

        let return_type = self.resolve_type_expr(&f.return_type);
        let body = self.check_block(&f.body)?;

        let mut effects = Vec::new();
        if let Some(contracts) = &f.contracts {
            for eff in &contracts.effects {
                match eff {
                    EffectAtom::Pure => effects.push("pure".to_string()),
                    EffectAtom::Named(n) => effects.push(n.clone()),
                    EffectAtom::Of(s) => effects.push(format!("of({})", s)),
                }
            }
        }

        Ok(TypedFunction {
            name: f.name.clone(),
            hash,
            params,
            return_type,
            effects,
            body,
        })
    }

    fn check_block(&mut self, b: &BlockExpr) -> Result<TypedBlock, String> {
        let mut stmts = Vec::new();
        for stmt in &b.stmts {
            match stmt {
                Stmt::Let { span, name, ty, value, .. } => {
                    let typed_val = self.check_expr(value)?;
                    let let_ty = if let Some(t_expr) = ty {
                        self.resolve_type_expr(t_expr)
                    } else {
                        typed_val.ty.clone()
                    };
                    self.env.insert(name.clone(), let_ty.clone());
                    stmts.push(TypedStmt::Let {
                        span: *span,
                        name: name.clone(),
                        ty: let_ty,
                        value: typed_val,
                    });
                }
                Stmt::Expr(e) => {
                    let typed_expr = self.check_expr(e)?;
                    stmts.push(TypedStmt::Expr(typed_expr));
                }
            }
        }

        let trailing_expr = if let Some(trailing) = &b.trailing_expr {
            Some(Box::new(self.check_expr(trailing)?))
        } else {
            None
        };

        let block_ty = trailing_expr
            .as_ref()
            .map(|e| e.ty.clone())
            .unwrap_or(Type::Unit);

        Ok(TypedBlock {
            span: b.span,
            stmts,
            trailing_expr,
            ty: block_ty,
        })
    }

    fn check_expr(&mut self, e: &Expr) -> Result<TypedExpr, String> {
        let span = e.span();
        match e {
            Expr::Literal { lit, span } => match lit {
                Literal::Int(n) => Ok(TypedExpr {
                    span: *span,
                    ty: Type::Int64,
                    kind: TypedExprKind::LiteralInt(*n),
                }),
                Literal::Float(f) => Ok(TypedExpr {
                    span: *span,
                    ty: Type::Float64,
                    kind: TypedExprKind::LiteralFloat(f.clone()),
                }),
                Literal::String(s) => Ok(TypedExpr {
                    span: *span,
                    ty: Type::String,
                    kind: TypedExprKind::LiteralString(s.clone()),
                }),
                Literal::Bool(b) => Ok(TypedExpr {
                    span: *span,
                    ty: Type::Bool,
                    kind: TypedExprKind::LiteralBool(*b),
                }),
            },
            Expr::Ident { name, span } => {
                let ty = self
                    .env
                    .get(name)
                    .cloned()
                    .unwrap_or_else(|| Type::Named(name.clone()));
                Ok(TypedExpr {
                    span: *span,
                    ty,
                    kind: TypedExprKind::Var(name.clone()),
                })
            }
            Expr::DeBruijnSlot { type_tag, index, span } => {
                let ty = match type_tag.as_str() {
                    "Int64" => Type::Int64,
                    "Float64" => Type::Float64,
                    "Bool" => Type::Bool,
                    "String" => Type::String,
                    _ => Type::Named(SymbolId::new(type_tag.clone())),
                };
                Ok(TypedExpr {
                    span: *span,
                    ty,
                    kind: TypedExprKind::DeBruijnSlot(*index),
                })
            }
            Expr::Binary { op, lhs, rhs, span } => {
                let typed_lhs = self.check_expr(lhs)?;
                let typed_rhs = self.check_expr(rhs)?;
                let res_ty = match op {
                    BinaryOp::Add | BinaryOp::Sub | BinaryOp::Mul | BinaryOp::Div | BinaryOp::Rem => {
                        typed_lhs.ty.clone()
                    }
                    BinaryOp::Eq
                    | BinaryOp::NotEq
                    | BinaryOp::Lt
                    | BinaryOp::LtEq
                    | BinaryOp::Gt
                    | BinaryOp::GtEq
                    | BinaryOp::And
                    | BinaryOp::Or => Type::Bool,
                };
                Ok(TypedExpr {
                    span: *span,
                    ty: res_ty,
                    kind: TypedExprKind::Binary {
                        op: format!("{:?}", op),
                        lhs: Box::new(typed_lhs),
                        rhs: Box::new(typed_rhs),
                    },
                })
            }
            Expr::Unary { op, operand, span } => {
                let typed_op = self.check_expr(operand)?;
                let res_ty = match op {
                    UnaryOp::Neg => typed_op.ty.clone(),
                    UnaryOp::Not => Type::Bool,
                };
                Ok(TypedExpr {
                    span: *span,
                    ty: res_ty,
                    kind: TypedExprKind::Unary {
                        op: format!("{:?}", op),
                        operand: Box::new(typed_op),
                    },
                })
            }
            Expr::Call { callee, args, span } => {
                let typed_callee = self.check_expr(callee)?;
                let mut typed_args = Vec::new();
                for a in args {
                    typed_args.push(self.check_expr(a)?);
                }
                let ret_ty = if let Type::Function { return_type, .. } = &typed_callee.ty {
                    *return_type.clone()
                } else {
                    Type::Int64 // Default return inference
                };
                Ok(TypedExpr {
                    span: *span,
                    ty: ret_ty,
                    kind: TypedExprKind::Call {
                        callee: Box::new(typed_callee),
                        args: typed_args,
                    },
                })
            }
            Expr::FieldAccess { target, field, span } => {
                let typed_target = self.check_expr(target)?;
                Ok(TypedExpr {
                    span: *span,
                    ty: Type::Int64,
                    kind: TypedExprKind::FieldAccess {
                        target: Box::new(typed_target),
                        field: field.clone(),
                    },
                })
            }
            Expr::Block(b) => {
                let typed_b = self.check_block(b)?;
                let ty = typed_b.ty.clone();
                Ok(TypedExpr {
                    span: typed_b.span,
                    ty,
                    kind: TypedExprKind::Block(typed_b),
                })
            }
            Expr::If { cond, then_branch, else_branch, span } => {
                let typed_cond = self.check_expr(cond)?;
                let typed_then = self.check_block(then_branch)?;
                let typed_else = if let Some(e) = else_branch {
                    Some(self.check_block(e)?)
                } else {
                    None
                };
                let ty = typed_then.ty.clone();
                Ok(TypedExpr {
                    span: *span,
                    ty,
                    kind: TypedExprKind::If {
                        cond: Box::new(typed_cond),
                        then_branch: typed_then,
                        else_branch: typed_else,
                    },
                })
            }
            Expr::Hole { span, .. } => {
                self.hole_counter += 1;
                let id = self.hole_counter;
                Ok(TypedExpr {
                    span: *span,
                    ty: Type::Hole(id),
                    kind: TypedExprKind::Hole(id),
                })
            }
            _ => Ok(TypedExpr {
                span,
                ty: Type::Unit,
                kind: TypedExprKind::LiteralInt(0),
            }),
        }
    }

    fn resolve_type_expr(&self, ty_expr: &TypeExpr) -> Type {
        match ty_expr {
            TypeExpr::Unit(_) => Type::Unit,
            TypeExpr::Primitive { name, .. } => match name.as_str() {
                "Int64" => Type::Int64,
                "Float64" => Type::Float64,
                "Bool" => Type::Bool,
                "String" => Type::String,
                _ => Type::Named(SymbolId::new(name)),
            },
            TypeExpr::Named { name, .. } => Type::Named(name.clone()),
            TypeExpr::Reference { inner, .. } => {
                Type::Reference(Box::new(self.resolve_type_expr(inner)))
            }
            TypeExpr::Slice { element, .. } => {
                Type::Slice(Box::new(self.resolve_type_expr(element)))
            }
            TypeExpr::Tuple { elements, .. } => {
                Type::Tuple(elements.iter().map(|e| self.resolve_type_expr(e)).collect())
            }
            TypeExpr::Never(_) => Type::Never,
            TypeExpr::Secret { inner, .. } => {
                Type::Secret(Box::new(self.resolve_type_expr(inner)))
            }
            TypeExpr::Hole(_) => Type::Hole(0),
        }
    }
}

impl Default for TypeChecker {
    fn default() -> Self {
        Self::new()
    }
}
