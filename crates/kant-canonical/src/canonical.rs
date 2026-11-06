use std::collections::BTreeMap;
use kant_core::{DefHash, SymbolId};
use kant_parser::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CanonicalModule {
    pub definitions: BTreeMap<SymbolId, CanonicalDef>,
    pub module_hash: DefHash,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum CanonicalDef {
    Function(CanonicalFunction),
    Type(CanonicalType),
}

impl CanonicalDef {
    pub fn def_hash(&self) -> DefHash {
        match self {
            Self::Function(f) => f.hash,
            Self::Type(t) => t.hash,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CanonicalFunction {
    pub name: SymbolId,
    pub is_pub: bool,
    pub param_count: usize,
    pub return_type_repr: String,
    pub effects: Vec<String>,
    pub canonical_body_repr: String,
    pub hash: DefHash,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CanonicalType {
    pub name: SymbolId,
    pub fields_sorted: Vec<(String, String)>,
    pub hash: DefHash,
}

pub struct Canonicalizer;

impl Canonicalizer {
    pub fn canonicalize_source(file: &SourceFile) -> CanonicalModule {
        let mut defs = BTreeMap::new();

        for item in &file.items {
            match item {
                ToplevelItem::Function(f) => {
                    let canon_fn = Self::canonicalize_function(f);
                    defs.insert(f.name.clone(), CanonicalDef::Function(canon_fn));
                }
                ToplevelItem::Type(t) => {
                    let canon_ty = Self::canonicalize_type(t);
                    defs.insert(t.name.clone(), CanonicalDef::Type(canon_ty));
                }
                _ => {}
            }
        }

        // Module hash is the SHA-256 of all sorted definitions' hashes
        let mut combined_bytes = Vec::new();
        for (name, def) in &defs {
            combined_bytes.extend_from_slice(name.as_str().as_bytes());
            combined_bytes.extend_from_slice(&def.def_hash().0);
        }
        let module_hash = DefHash::from_bytes(&combined_bytes);

        CanonicalModule {
            definitions: defs,
            module_hash,
        }
    }

    pub fn canonicalize_type(ty_def: &TypeDef) -> CanonicalType {
        // Rule C2: Alphabetically sort fields by name
        let mut fields: Vec<(String, String)> = ty_def
            .fields
            .iter()
            .map(|f| (f.name.to_string(), Self::format_type_expr(&f.ty)))
            .collect();
        fields.sort_by(|a, b| a.0.cmp(&b.0));

        // Compute deterministic hash
        let mut payload = format!("afhoum:{}", ty_def.name);
        for (k, v) in &fields {
            payload.push_str(&format!(";{}:{}", k, v));
        }
        let hash = DefHash::from_bytes(payload.as_bytes());

        CanonicalType {
            name: ty_def.name.clone(),
            fields_sorted: fields,
            hash,
        }
    }

    pub fn canonicalize_function(f: &FunctionDef) -> CanonicalFunction {
        // Rule C1: Alpha-rename parameters to De Bruijn slots: @T.0, @T.1
        let mut env: BTreeMap<String, String> = BTreeMap::new();
        for (idx, p) in f.params.iter().enumerate() {
            let slot = format!("@T.{}", idx);
            env.insert(p.name.to_string(), slot);
        }

        // Rule C2: Sort effects
        let mut effects = Vec::new();
        if let Some(contracts) = &f.contracts {
            for eff in &contracts.effects {
                match eff {
                    EffectAtom::Pure => effects.push("pure".to_string()),
                    EffectAtom::Named(s) => effects.push(s.clone()),
                    EffectAtom::Of(sym) => effects.push(format!("of({})", sym)),
                }
            }
        }
        effects.sort();

        // Rule C4: Self-recursive call normalization to @self
        let fn_name = f.name.to_string();

        let ret_repr = Self::format_type_expr(&f.return_type);
        let body_repr = Self::format_block_with_env(&f.body, &env, &fn_name);

        // Compute deterministic hash
        let mut payload = format!(
            "fn:{}:pub={}:ret={}:effects={}:body={}",
            f.name,
            f.is_pub,
            ret_repr,
            effects.join(","),
            body_repr
        );
        let hash = DefHash::from_bytes(payload.as_bytes());

        CanonicalFunction {
            name: f.name.clone(),
            is_pub: f.is_pub,
            param_count: f.params.len(),
            return_type_repr: ret_repr,
            effects,
            canonical_body_repr: body_repr,
            hash,
        }
    }

    fn format_type_expr(ty: &TypeExpr) -> String {
        match ty {
            TypeExpr::Unit(_) => "Unit".to_string(),
            TypeExpr::Primitive { name, .. } => name.clone(),
            TypeExpr::Named { name, .. } => name.to_string(),
            TypeExpr::Reference { inner, .. } => format!("&{}", Self::format_type_expr(inner)),
            TypeExpr::Slice { element, .. } => format!("[{}]", Self::format_type_expr(element)),
            TypeExpr::Tuple { elements, .. } => {
                let parts: Vec<_> = elements.iter().map(Self::format_type_expr).collect();
                format!("({})", parts.join(","))
            }
            TypeExpr::Never(_) => "!".to_string(),
            TypeExpr::Secret { inner, .. } => format!("Secret<{}>", Self::format_type_expr(inner)),
            TypeExpr::Hole(_) => "?hole".to_string(),
        }
    }

    fn format_block_with_env(
        b: &BlockExpr,
        env: &BTreeMap<String, String>,
        self_name: &str,
    ) -> String {
        let mut local_env = env.clone();
        let mut pieces = Vec::new();

        for stmt in &b.stmts {
            match stmt {
                Stmt::Let { name, value, .. } => {
                    let slot = format!("@L.{}", local_env.len());
                    let val_str = Self::format_expr_with_env(value, &local_env, self_name);
                    local_env.insert(name.to_string(), slot.clone());
                    pieces.push(format!("let {}={}", slot, val_str));
                }
                Stmt::Expr(e) => {
                    pieces.push(Self::format_expr_with_env(e, &local_env, self_name));
                }
            }
        }

        if let Some(trailing) = &b.trailing_expr {
            pieces.push(Self::format_expr_with_env(trailing, &local_env, self_name));
        }

        format!("{{{}}}", pieces.join(";"))
    }

    fn format_expr_with_env(
        e: &Expr,
        env: &BTreeMap<String, String>,
        self_name: &str,
    ) -> String {
        match e {
            Expr::Literal { lit, .. } => match lit {
                Literal::Int(n) => n.to_string(),
                Literal::Float(f) => f.clone(),
                Literal::String(s) => format!("\"{}\"", s),
                Literal::Bool(b) => b.to_string(),
            },
            Expr::Ident { name, .. } => {
                let n = name.as_str();
                if n == self_name {
                    "@self".to_string()
                } else if let Some(slot) = env.get(n) {
                    slot.clone()
                } else {
                    n.to_string()
                }
            }
            Expr::DeBruijnSlot { type_tag, index, .. } => format!("@{}.{}", type_tag, index),
            Expr::Binary { op, lhs, rhs, .. } => {
                let op_str = match op {
                    BinaryOp::Add => "+",
                    BinaryOp::Sub => "-",
                    BinaryOp::Mul => "*",
                    BinaryOp::Div => "/",
                    BinaryOp::Rem => "%",
                    BinaryOp::Eq => "==",
                    BinaryOp::NotEq => "!=",
                    BinaryOp::Lt => "<",
                    BinaryOp::LtEq => "<=",
                    BinaryOp::Gt => ">",
                    BinaryOp::GtEq => ">=",
                    BinaryOp::And => "&&",
                    BinaryOp::Or => "||",
                };
                format!(
                    "({}{}{})",
                    Self::format_expr_with_env(lhs, env, self_name),
                    op_str,
                    Self::format_expr_with_env(rhs, env, self_name)
                )
            }
            Expr::Unary { op, operand, .. } => {
                let op_str = match op {
                    UnaryOp::Neg => "-",
                    UnaryOp::Not => "!",
                };
                format!("({}{})", op_str, Self::format_expr_with_env(operand, env, self_name))
            }
            Expr::Call { callee, args, .. } => {
                let callee_str = Self::format_expr_with_env(callee, env, self_name);
                let args_str: Vec<_> = args
                    .iter()
                    .map(|a| Self::format_expr_with_env(a, env, self_name))
                    .collect();
                format!("{}({})", callee_str, args_str.join(","))
            }
            Expr::FieldAccess { target, field, .. } => {
                format!(
                    "{}.{}",
                    Self::format_expr_with_env(target, env, self_name),
                    field
                )
            }
            Expr::Block(b) => Self::format_block_with_env(b, env, self_name),
            Expr::If { cond, then_branch, else_branch, .. } => {
                let cond_str = Self::format_expr_with_env(cond, env, self_name);
                let then_str = Self::format_block_with_env(then_branch, env, self_name);
                let else_str = else_branch
                    .as_ref()
                    .map(|b| format!("else{}", Self::format_block_with_env(b, env, self_name)))
                    .unwrap_or_default();
                format!("if {}{}{}", cond_str, then_str, else_str)
            }
            Expr::Match { scrutinee, arms, .. } => {
                let scr_str = Self::format_expr_with_env(scrutinee, env, self_name);
                let arms_str: Vec<_> = arms
                    .iter()
                    .map(|a| {
                        let pat_str = match &a.pattern {
                            Pattern::Wildcard(_) => "_".to_string(),
                            Pattern::Ident(_, s) => s.to_string(),
                            Pattern::Literal(_, l) => match l {
                                Literal::Int(n) => n.to_string(),
                                Literal::Float(f) => f.clone(),
                                Literal::String(s) => format!("\"{}\"", s),
                                Literal::Bool(b) => b.to_string(),
                            },
                        };
                        format!("{}=>{}", pat_str, Self::format_expr_with_env(&a.body, env, self_name))
                    })
                    .collect();
                format!("match {}{{{}}}", scr_str, arms_str.join(","))
            }
            Expr::HandleWith { body, governor_arms, .. } => {
                let body_str = Self::format_block_with_env(body, env, self_name);
                let arms_str: Vec<_> = governor_arms
                    .iter()
                    .map(|(eff, h)| {
                        let eff_name = match eff {
                            EffectAtom::Pure => "pure",
                            EffectAtom::Named(n) => n.as_str(),
                            EffectAtom::Of(s) => s.as_str(),
                        };
                        format!("{}->{}", eff_name, Self::format_expr_with_env(h, env, self_name))
                    })
                    .collect();
                format!("handle{}with governor{{{}}}", body_str, arms_str.join(","))
            }
            Expr::DynQuarantine { declared_targets, callee, args, .. } => {
                let mut targets_sorted: Vec<_> = declared_targets.iter().map(|s| s.to_string()).collect();
                targets_sorted.sort();
                let callee_str = Self::format_expr_with_env(callee, env, self_name);
                let args_str: Vec<_> = args
                    .iter()
                    .map(|a| Self::format_expr_with_env(a, env, self_name))
                    .collect();
                format!("dyn{{{}}}({},{})", targets_sorted.join(","), callee_str, args_str.join(","))
            }
            Expr::Hole { .. } => "?hole".to_string(),
        }
    }
}
