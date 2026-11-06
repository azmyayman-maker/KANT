use kant_core::{ByteSpan, SymbolId};
use kant_lexer::{Token, TokenKind};
use crate::ast::*;

pub struct Parser {
    tokens: Vec<Token>,
    cursor: usize,
}

impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Self { tokens, cursor: 0 }
    }

    pub fn parse_source_file(&mut self) -> SourceFile {
        let start = self.current_span().start;
        let mut has_magic_header = false;

        if self.check(&TokenKind::MagicHeader) {
            has_magic_header = true;
            self.advance();
        }

        let mut items = Vec::new();
        while !self.is_at_end() {
            if let Some(item) = self.parse_toplevel_item() {
                items.push(item);
            } else {
                // Recover to next toplevel item
                self.advance();
            }
        }

        let end = self.current_span().end;
        SourceFile {
            span: ByteSpan::new(start, end),
            has_magic_header,
            items,
        }
    }

    fn parse_toplevel_item(&mut self) -> Option<ToplevelItem> {
        match self.peek_kind() {
            TokenKind::KwDecision => self.parse_decision_block().map(ToplevelItem::Decision),
            TokenKind::KwAfhoum => self.parse_type_def().map(ToplevelItem::Type),
            TokenKind::KwCap => self.parse_capability_def().map(ToplevelItem::Capability),
            TokenKind::KwPub | TokenKind::KwFn => self.parse_function_def().map(ToplevelItem::Function),
            _ => None,
        }
    }

    fn parse_decision_block(&mut self) -> Option<DecisionBlock> {
        let start = self.current_span().start;
        self.consume(&TokenKind::KwDecision)?;
        let name = self.consume_ident()?;
        self.consume(&TokenKind::LBrace)?;

        let mut fields = Vec::new();
        while !self.check(&TokenKind::RBrace) && !self.is_at_end() {
            let field_name = self.consume_ident()?;
            self.consume(&TokenKind::Colon)?;
            let field_val = self.consume_string()?;
            self.consume(&TokenKind::Semicolon)?;
            fields.push((field_name, field_val));
        }
        self.consume(&TokenKind::RBrace)?;
        let end = self.current_span().end;

        Some(DecisionBlock {
            span: ByteSpan::new(start, end),
            name,
            fields,
        })
    }

    fn parse_type_def(&mut self) -> Option<TypeDef> {
        let start = self.current_span().start;
        self.consume(&TokenKind::KwAfhoum)?;
        let name = self.consume_ident()?;
        self.consume(&TokenKind::LBrace)?;

        let mut fields = Vec::new();
        while !self.check(&TokenKind::RBrace) && !self.is_at_end() {
            let field_start = self.current_span().start;
            let field_name = self.consume_ident()?;
            self.consume(&TokenKind::Colon)?;
            let ty = self.parse_type_expr()?;
            self.consume(&TokenKind::Semicolon)?;
            let field_end = self.current_span().end;
            fields.push(StructField {
                span: ByteSpan::new(field_start, field_end),
                name: field_name,
                ty,
            });
        }
        self.consume(&TokenKind::RBrace)?;
        let end = self.current_span().end;

        Some(TypeDef {
            span: ByteSpan::new(start, end),
            name,
            fields,
        })
    }

    fn parse_capability_def(&mut self) -> Option<CapabilityDef> {
        let start = self.current_span().start;
        self.consume(&TokenKind::KwCap)?;
        let name = self.consume_ident()?;
        self.consume(&TokenKind::LBrace)?;

        let mut permissions = Vec::new();
        while !self.check(&TokenKind::RBrace) && !self.is_at_end() {
            let perm_start = self.current_span().start;
            let perm_name = self.consume_ident()?;
            self.consume(&TokenKind::LParen)?;
            let mut params = Vec::new();
            while !self.check(&TokenKind::RParen) && !self.is_at_end() {
                if let Some(param_ty) = self.parse_type_expr() {
                    params.push(param_ty);
                }
                if self.check(&TokenKind::Comma) {
                    self.advance();
                } else {
                    break;
                }
            }
            self.consume(&TokenKind::RParen)?;
            self.consume(&TokenKind::Semicolon)?;
            let perm_end = self.current_span().end;
            permissions.push(CapPermission {
                span: ByteSpan::new(perm_start, perm_end),
                name: perm_name,
                params,
            });
        }
        self.consume(&TokenKind::RBrace)?;
        let end = self.current_span().end;

        Some(CapabilityDef {
            span: ByteSpan::new(start, end),
            name,
            permissions,
        })
    }

    fn parse_function_def(&mut self) -> Option<FunctionDef> {
        let start = self.current_span().start;
        let is_pub = if self.check(&TokenKind::KwPub) {
            self.advance();
            true
        } else {
            false
        };

        self.consume(&TokenKind::KwFn)?;
        let name = self.consume_ident()?;
        self.consume(&TokenKind::LParen)?;

        let mut params = Vec::new();
        while !self.check(&TokenKind::RParen) && !self.is_at_end() {
            let param_start = self.current_span().start;
            let param_name = self.consume_ident()?;
            self.consume(&TokenKind::Colon)?;
            let param_ty = self.parse_type_expr()?;
            let param_end = self.current_span().end;
            params.push(Param {
                span: ByteSpan::new(param_start, param_end),
                name: param_name,
                ty: param_ty,
            });
            if self.check(&TokenKind::Comma) {
                self.advance();
            } else {
                break;
            }
        }
        self.consume(&TokenKind::RParen)?;

        let return_type = if self.check(&TokenKind::Arrow) {
            self.advance();
            self.parse_type_expr()?
        } else {
            TypeExpr::Unit(ByteSpan::point(self.current_span().start))
        };

        let contracts = if self.check(&TokenKind::LBrace) && !self.peek_is_body_assignment() {
            self.parse_contract_block()
        } else {
            None
        };

        if self.check(&TokenKind::Eq) {
            self.advance();
        }

        let body = self.parse_block_expr()?;
        let end = body.span.end;

        Some(FunctionDef {
            span: ByteSpan::new(start, end),
            is_pub,
            name,
            params,
            return_type,
            contracts,
            body,
        })
    }

    fn peek_is_body_assignment(&self) -> bool {
        // If there's an '=' before the '{', then '{' is the body, not contracts
        // Look back 1 token if current is '{'
        if self.cursor > 0 {
            self.tokens[self.cursor - 1].kind == TokenKind::Eq
        } else {
            false
        }
    }

    fn parse_contract_block(&mut self) -> Option<ContractBlock> {
        let start = self.current_span().start;
        self.consume(&TokenKind::LBrace)?;

        let mut intent = None;
        let mut requires = Vec::new();
        let mut ensures = Vec::new();
        let mut decreases = None;
        let mut effects = Vec::new();

        while !self.check(&TokenKind::RBrace) && !self.is_at_end() {
            match self.peek_kind() {
                TokenKind::KwIntent => {
                    self.advance();
                    intent = self.consume_string();
                }
                TokenKind::KwRequires => {
                    self.advance();
                    if let Some(expr) = self.parse_expr(0) {
                        requires.push(expr);
                    }
                }
                TokenKind::KwEnsures => {
                    self.advance();
                    if let Some(expr) = self.parse_expr(0) {
                        ensures.push(expr);
                    }
                }
                TokenKind::KwDecreases => {
                    self.advance();
                    decreases = self.parse_expr(0);
                }
                TokenKind::KwEffects => {
                    self.advance();
                    effects = self.parse_effect_list();
                }
                _ => {
                    self.advance();
                }
            }
        }
        self.consume(&TokenKind::RBrace)?;
        let end = self.current_span().end;

        Some(ContractBlock {
            span: ByteSpan::new(start, end),
            intent,
            requires,
            ensures,
            decreases,
            effects,
        })
    }

    fn parse_effect_list(&mut self) -> Vec<EffectAtom> {
        let mut list = Vec::new();
        if self.check(&TokenKind::KwPure) {
            self.advance();
            list.push(EffectAtom::Pure);
            return list;
        }

        while !self.is_at_end() {
            if self.check(&TokenKind::KwOf) {
                self.advance();
                self.consume(&TokenKind::LParen);
                if let Some(param) = self.consume_ident() {
                    list.push(EffectAtom::Of(param));
                }
                self.consume(&TokenKind::RParen);
            } else if let Some(first) = self.consume_ident() {
                let mut name = first.to_string();
                if self.check(&TokenKind::Dot) {
                    self.advance();
                    if let Some(second) = self.consume_ident() {
                        name = format!("{}.{}", name, second);
                    }
                }
                list.push(EffectAtom::Named(name));
            } else {
                break;
            }

            if self.check(&TokenKind::Comma) {
                self.advance();
            } else {
                break;
            }
        }
        list
    }

    pub fn parse_type_expr(&mut self) -> Option<TypeExpr> {
        let start = self.current_span().start;
        match self.peek_kind() {
            TokenKind::Bang => {
                self.advance();
                Some(TypeExpr::Never(ByteSpan::new(start, self.current_span().end)))
            }
            TokenKind::Hole => {
                self.advance();
                Some(TypeExpr::Hole(ByteSpan::new(start, self.current_span().end)))
            }
            TokenKind::KwSecret => {
                self.advance();
                self.consume(&TokenKind::Lt)?;
                let inner = self.parse_type_expr()?;
                self.consume(&TokenKind::Gt)?;
                let end = self.current_span().end;
                Some(TypeExpr::Secret {
                    span: ByteSpan::new(start, end),
                    inner: Box::new(inner),
                })
            }
            TokenKind::LBracket => {
                self.advance();
                let inner = self.parse_type_expr()?;
                self.consume(&TokenKind::RBracket)?;
                let end = self.current_span().end;
                Some(TypeExpr::Slice {
                    span: ByteSpan::new(start, end),
                    element: Box::new(inner),
                })
            }
            TokenKind::LParen => {
                self.advance();
                if self.check(&TokenKind::RParen) {
                    self.advance();
                    return Some(TypeExpr::Unit(ByteSpan::new(start, self.current_span().end)));
                }
                let mut elements = Vec::new();
                while !self.check(&TokenKind::RParen) && !self.is_at_end() {
                    elements.push(self.parse_type_expr()?);
                    if self.check(&TokenKind::Comma) {
                        self.advance();
                    } else {
                        break;
                    }
                }
                self.consume(&TokenKind::RParen)?;
                let end = self.current_span().end;
                Some(TypeExpr::Tuple {
                    span: ByteSpan::new(start, end),
                    elements,
                })
            }
            TokenKind::Ident(ref name) => {
                let name = name.clone();
                self.advance();
                let end = self.current_span().end;
                let span = ByteSpan::new(start, end);
                match name.as_str() {
                    "Unit" | "Bool" | "Int64" | "Float64" | "String" => {
                        Some(TypeExpr::Primitive { span, name })
                    }
                    _ => Some(TypeExpr::Named {
                        span,
                        name: SymbolId::new(name),
                    }),
                }
            }
            _ => None,
        }
    }

    pub fn parse_block_expr(&mut self) -> Option<BlockExpr> {
        let start = self.current_span().start;
        self.consume(&TokenKind::LBrace)?;

        let mut stmts = Vec::new();
        let mut trailing_expr = None;

        while !self.check(&TokenKind::RBrace) && !self.is_at_end() {
            if self.check(&TokenKind::KwLet) {
                if let Some(stmt) = self.parse_let_stmt() {
                    stmts.push(stmt);
                }
            } else {
                if let Some(expr) = self.parse_expr(0) {
                    if self.check(&TokenKind::Semicolon) {
                        self.advance();
                        stmts.push(Stmt::Expr(expr));
                    } else if self.check(&TokenKind::RBrace) {
                        trailing_expr = Some(Box::new(expr));
                        break;
                    } else {
                        stmts.push(Stmt::Expr(expr));
                    }
                } else {
                    self.advance();
                }
            }
        }
        self.consume(&TokenKind::RBrace)?;
        let end = self.current_span().end;

        Some(BlockExpr {
            span: ByteSpan::new(start, end),
            stmts,
            trailing_expr,
        })
    }

    fn parse_let_stmt(&mut self) -> Option<Stmt> {
        let start = self.current_span().start;
        self.consume(&TokenKind::KwLet)?;
        let is_mut = if self.check(&TokenKind::KwMut) {
            self.advance();
            true
        } else {
            false
        };
        let name = self.consume_ident()?;
        let ty = if self.check(&TokenKind::Colon) {
            self.advance();
            self.parse_type_expr()
        } else {
            None
        };
        self.consume(&TokenKind::Eq)?;
        let value = self.parse_expr(0)?;
        self.consume(&TokenKind::Semicolon)?;
        let end = self.current_span().end;

        Some(Stmt::Let {
            span: ByteSpan::new(start, end),
            is_mut,
            name,
            ty,
            value,
        })
    }

    pub fn parse_expr(&mut self, min_bp: u8) -> Option<Expr> {
        let mut lhs = self.parse_prefix_atom()?;

        loop {
            if self.is_at_end() {
                break;
            }

            // Postfix: Call Expr(args)
            if self.check(&TokenKind::LParen) {
                let l_bp = 100;
                if l_bp < min_bp {
                    break;
                }
                self.advance();
                let mut args = Vec::new();
                while !self.check(&TokenKind::RParen) && !self.is_at_end() {
                    if let Some(arg) = self.parse_expr(0) {
                        args.push(arg);
                    }
                    if self.check(&TokenKind::Comma) {
                        self.advance();
                    } else {
                        break;
                    }
                }
                self.consume(&TokenKind::RParen);
                let start = lhs.span().start;
                let end = self.current_span().end;
                lhs = Expr::Call {
                    span: ByteSpan::new(start, end),
                    callee: Box::new(lhs),
                    args,
                };
                continue;
            }

            // Postfix: Field access Expr.field
            if self.check(&TokenKind::Dot) {
                let l_bp = 100;
                if l_bp < min_bp {
                    break;
                }
                self.advance();
                if let Some(field) = self.consume_ident() {
                    let start = lhs.span().start;
                    let end = self.current_span().end;
                    lhs = Expr::FieldAccess {
                        span: ByteSpan::new(start, end),
                        target: Box::new(lhs),
                        field,
                    };
                    continue;
                }
            }

            // Infix binary operators
            let (op, l_bp, r_bp) = match self.peek_kind() {
                TokenKind::PipePipe => (BinaryOp::Or, 10, 11),
                TokenKind::AmpAmp => (BinaryOp::And, 20, 21),
                TokenKind::EqEq => (BinaryOp::Eq, 30, 31),
                TokenKind::BangEq => (BinaryOp::NotEq, 30, 31),
                TokenKind::Lt => (BinaryOp::Lt, 40, 41),
                TokenKind::LtEq => (BinaryOp::LtEq, 40, 41),
                TokenKind::Gt => (BinaryOp::Gt, 40, 41),
                TokenKind::GtEq => (BinaryOp::GtEq, 40, 41),
                TokenKind::Plus => (BinaryOp::Add, 50, 51),
                TokenKind::Minus => (BinaryOp::Sub, 50, 51),
                TokenKind::Star => (BinaryOp::Mul, 60, 61),
                TokenKind::Slash => (BinaryOp::Div, 60, 61),
                TokenKind::Percent => (BinaryOp::Rem, 60, 61),
                _ => break,
            };

            if l_bp < min_bp {
                break;
            }

            self.advance(); // consume op
            let rhs = self.parse_expr(r_bp)?;
            let span = lhs.span().merge(rhs.span());
            lhs = Expr::Binary {
                span,
                op,
                lhs: Box::new(lhs),
                rhs: Box::new(rhs),
            };
        }

        Some(lhs)
    }

    fn parse_prefix_atom(&mut self) -> Option<Expr> {
        let start = self.current_span().start;
        match self.peek_kind() {
            TokenKind::Hole => {
                self.advance();
                let end = self.current_span().end;
                Some(Expr::Hole {
                    span: ByteSpan::new(start, end),
                    expected_type: None,
                })
            }
            TokenKind::IntLit(n) => {
                let n = *n;
                self.advance();
                let end = self.current_span().end;
                Some(Expr::Literal {
                    span: ByteSpan::new(start, end),
                    lit: Literal::Int(n),
                })
            }
            TokenKind::FloatLit(ref s) => {
                let s = s.clone();
                self.advance();
                let end = self.current_span().end;
                Some(Expr::Literal {
                    span: ByteSpan::new(start, end),
                    lit: Literal::Float(s),
                })
            }
            TokenKind::StringLit(ref s) => {
                let s = s.clone();
                self.advance();
                let end = self.current_span().end;
                Some(Expr::Literal {
                    span: ByteSpan::new(start, end),
                    lit: Literal::String(s),
                })
            }
            TokenKind::BoolLit(b) => {
                let b = *b;
                self.advance();
                let end = self.current_span().end;
                Some(Expr::Literal {
                    span: ByteSpan::new(start, end),
                    lit: Literal::Bool(b),
                })
            }
            TokenKind::Ident(ref name) => {
                let name = SymbolId::new(name.clone());
                self.advance();
                let end = self.current_span().end;
                Some(Expr::Ident {
                    span: ByteSpan::new(start, end),
                    name,
                })
            }
            TokenKind::DeBruijnSlot { ref type_tag, index } => {
                let tag = type_tag.clone();
                let idx = *index;
                self.advance();
                let end = self.current_span().end;
                Some(Expr::DeBruijnSlot {
                    span: ByteSpan::new(start, end),
                    type_tag: tag,
                    index: idx,
                })
            }
            TokenKind::KwIf => self.parse_if_expr(),
            TokenKind::KwMatch => self.parse_match_expr(),
            TokenKind::KwHandle => self.parse_handle_expr(),
            TokenKind::KwDyn => self.parse_dyn_expr(),
            TokenKind::LBrace => self.parse_block_expr().map(Expr::Block),
            TokenKind::LParen => {
                self.advance();
                let inner = self.parse_expr(0)?;
                self.consume(&TokenKind::RParen)?;
                Some(inner)
            }
            TokenKind::Minus => {
                self.advance();
                let operand = self.parse_prefix_atom()?;
                let end = operand.span().end;
                Some(Expr::Unary {
                    span: ByteSpan::new(start, end),
                    op: UnaryOp::Neg,
                    operand: Box::new(operand),
                })
            }
            TokenKind::Bang => {
                self.advance();
                let operand = self.parse_prefix_atom()?;
                let end = operand.span().end;
                Some(Expr::Unary {
                    span: ByteSpan::new(start, end),
                    op: UnaryOp::Not,
                    operand: Box::new(operand),
                })
            }
            _ => {
                // Recovery: return Hole instead of crashing
                self.advance();
                let end = self.current_span().end;
                Some(Expr::Hole {
                    span: ByteSpan::new(start, end),
                    expected_type: None,
                })
            }
        }
    }

    fn parse_if_expr(&mut self) -> Option<Expr> {
        let start = self.current_span().start;
        self.consume(&TokenKind::KwIf)?;
        let cond = self.parse_expr(0)?;
        let then_branch = self.parse_block_expr()?;
        let else_branch = if self.check(&TokenKind::KwElse) {
            self.advance();
            if self.check(&TokenKind::KwIf) {
                // else if -> wrap in synthetic block
                let nested_if = self.parse_if_expr()?;
                let span = nested_if.span();
                Some(BlockExpr {
                    span,
                    stmts: vec![],
                    trailing_expr: Some(Box::new(nested_if)),
                })
            } else {
                self.parse_block_expr()
            }
        } else {
            None
        };
        let end = else_branch
            .as_ref()
            .map(|b| b.span.end)
            .unwrap_or(then_branch.span.end);

        Some(Expr::If {
            span: ByteSpan::new(start, end),
            cond: Box::new(cond),
            then_branch,
            else_branch,
        })
    }

    fn parse_match_expr(&mut self) -> Option<Expr> {
        let start = self.current_span().start;
        self.consume(&TokenKind::KwMatch)?;
        let scrutinee = self.parse_expr(0)?;
        self.consume(&TokenKind::LBrace)?;

        let mut arms = Vec::new();
        while !self.check(&TokenKind::RBrace) && !self.is_at_end() {
            let arm_start = self.current_span().start;
            let pattern = self.parse_pattern()?;
            self.consume(&TokenKind::FatArrow)?;
            let body = self.parse_expr(0)?;
            if self.check(&TokenKind::Comma) {
                self.advance();
            }
            let arm_end = body.span().end;
            arms.push(MatchArm {
                span: ByteSpan::new(arm_start, arm_end),
                pattern,
                body,
            });
        }
        self.consume(&TokenKind::RBrace)?;
        let end = self.current_span().end;

        Some(Expr::Match {
            span: ByteSpan::new(start, end),
            scrutinee: Box::new(scrutinee),
            arms,
        })
    }

    fn parse_pattern(&mut self) -> Option<Pattern> {
        let span = self.current_span();
        match self.peek_kind() {
            TokenKind::Ident(ref s) => {
                let sym = SymbolId::new(s.clone());
                self.advance();
                if sym.as_str() == "_" {
                    Some(Pattern::Wildcard(span))
                } else {
                    Some(Pattern::Ident(span, sym))
                }
            }
            TokenKind::IntLit(n) => {
                let n = *n;
                self.advance();
                Some(Pattern::Literal(span, Literal::Int(n)))
            }
            TokenKind::BoolLit(b) => {
                let b = *b;
                self.advance();
                Some(Pattern::Literal(span, Literal::Bool(b)))
            }
            _ => None,
        }
    }

    fn parse_handle_expr(&mut self) -> Option<Expr> {
        let start = self.current_span().start;
        self.consume(&TokenKind::KwHandle)?;
        let body = self.parse_block_expr()?;
        self.consume(&TokenKind::KwWith)?;
        self.consume(&TokenKind::KwGovernor)?;
        self.consume(&TokenKind::LBrace)?;

        let mut arms = Vec::new();
        while !self.check(&TokenKind::RBrace) && !self.is_at_end() {
            let effect_atom = if let Some(first) = self.consume_ident() {
                let mut name = first.to_string();
                if self.check(&TokenKind::Dot) {
                    self.advance();
                    if let Some(second) = self.consume_ident() {
                        name = format!("{}.{}", name, second);
                    }
                }
                EffectAtom::Named(name)
            } else {
                break;
            };

            self.consume(&TokenKind::Arrow)?;
            let handler_fn = self.parse_expr(0)?;
            if self.check(&TokenKind::Comma) {
                self.advance();
            }
            arms.push((effect_atom, handler_fn));
        }
        self.consume(&TokenKind::RBrace)?;
        let end = self.current_span().end;

        Some(Expr::HandleWith {
            span: ByteSpan::new(start, end),
            body,
            governor_arms: arms,
        })
    }

    fn parse_dyn_expr(&mut self) -> Option<Expr> {
        let start = self.current_span().start;
        self.consume(&TokenKind::KwDyn)?;
        self.consume(&TokenKind::LBrace)?;

        let mut targets = Vec::new();
        while !self.check(&TokenKind::RBrace) && !self.is_at_end() {
            if let Some(tgt) = self.consume_ident() {
                targets.push(tgt);
            }
            if self.check(&TokenKind::Comma) {
                self.advance();
            } else {
                break;
            }
        }
        self.consume(&TokenKind::RBrace)?;
        self.consume(&TokenKind::LParen)?;

        let callee = self.parse_expr(0)?;
        let mut args = Vec::new();
        while self.check(&TokenKind::Comma) {
            self.advance();
            if let Some(arg) = self.parse_expr(0) {
                args.push(arg);
            }
        }
        self.consume(&TokenKind::RParen)?;
        let end = self.current_span().end;

        Some(Expr::DynQuarantine {
            span: ByteSpan::new(start, end),
            declared_targets: targets,
            callee: Box::new(callee),
            args,
        })
    }

    // Helper functions
    fn check(&self, expected: &TokenKind) -> bool {
        if self.is_at_end() {
            false
        } else {
            &self.tokens[self.cursor].kind == expected
        }
    }

    fn peek_kind(&self) -> &TokenKind {
        if self.is_at_end() {
            &TokenKind::Eof
        } else {
            &self.tokens[self.cursor].kind
        }
    }

    fn current_span(&self) -> ByteSpan {
        if self.cursor < self.tokens.len() {
            self.tokens[self.cursor].span
        } else if let Some(last) = self.tokens.last() {
            ByteSpan::point(last.span.end)
        } else {
            ByteSpan::empty()
        }
    }

    fn advance(&mut self) {
        if !self.is_at_end() {
            self.cursor += 1;
        }
    }

    fn consume(&mut self, expected: &TokenKind) -> Option<()> {
        if self.check(expected) {
            self.advance();
            Some(())
        } else {
            None
        }
    }

    fn consume_ident(&mut self) -> Option<SymbolId> {
        if let TokenKind::Ident(ref s) = self.peek_kind() {
            let sym = SymbolId::new(s.clone());
            self.advance();
            Some(sym)
        } else {
            None
        }
    }

    fn consume_string(&mut self) -> Option<String> {
        if let TokenKind::StringLit(ref s) = self.peek_kind() {
            let s = s.clone();
            self.advance();
            Some(s)
        } else {
            None
        }
    }

    fn is_at_end(&self) -> bool {
        self.cursor >= self.tokens.len() || self.tokens[self.cursor].kind == TokenKind::Eof
    }
}
