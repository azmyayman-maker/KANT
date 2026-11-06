use kant_core::ByteSpan;
use crate::token::{Token, TokenKind};

pub struct Lexer<'a> {
    source: &'a str,
    bytes: &'a [u8],
    cursor: usize,
}

impl<'a> Lexer<'a> {
    pub fn new(source: &'a str) -> Self {
        Self {
            source,
            bytes: source.as_bytes(),
            cursor: 0,
        }
    }

    pub fn tokenize_all(mut self) -> Vec<Token> {
        let mut tokens = Vec::new();
        loop {
            let tok = self.next_token();
            let is_eof = tok.kind == TokenKind::Eof;
            tokens.push(tok);
            if is_eof {
                break;
            }
        }
        tokens
    }

    pub fn next_token(&mut self) -> Token {
        self.skip_whitespace_and_comments();

        let start = self.cursor;
        if self.cursor >= self.bytes.len() {
            return Token::new(TokenKind::Eof, ByteSpan::point(start));
        }

        let b = self.bytes[self.cursor];

        // Magic Header: #![kant(v0.1)]
        if b == b'#' && self.source[self.cursor..].starts_with("#![kant(v0.1)]") {
            self.cursor += "#![kant(v0.1)]".len();
            return Token::new(TokenKind::MagicHeader, ByteSpan::new(start, self.cursor));
        }

        // Typed Hole: ?hole
        if b == b'?' {
            if self.source[self.cursor..].starts_with("?hole") {
                self.cursor += 5;
                return Token::new(TokenKind::Hole, ByteSpan::new(start, self.cursor));
            }
            self.cursor += 1;
            return Token::new(TokenKind::Unknown('?'), ByteSpan::new(start, self.cursor));
        }

        // De Bruijn Slot or At: @T.0 or @
        if b == b'@' {
            self.cursor += 1;
            // Check if followed by identifier, dot, and integer (e.g. @T.0)
            let tag_start = self.cursor;
            while self.cursor < self.bytes.len() && (self.bytes[self.cursor].is_ascii_alphanumeric() || self.bytes[self.cursor] == b'_') {
                self.cursor += 1;
            }
            if tag_start < self.cursor && self.cursor < self.bytes.len() && self.bytes[self.cursor] == b'.' {
                let tag = &self.source[tag_start..self.cursor];
                self.cursor += 1; // skip '.'
                let num_start = self.cursor;
                while self.cursor < self.bytes.len() && self.bytes[self.cursor].is_ascii_digit() {
                    self.cursor += 1;
                }
                if num_start < self.cursor {
                    let idx: u32 = self.source[num_start..self.cursor].parse().unwrap_or(0);
                    return Token::new(
                        TokenKind::DeBruijnSlot {
                            type_tag: tag.to_string(),
                            index: idx,
                        },
                        ByteSpan::new(start, self.cursor),
                    );
                }
            }
            // Fallback to standalone At token
            self.cursor = start + 1;
            return Token::new(TokenKind::At, ByteSpan::new(start, self.cursor));
        }

        // Multi-character & Single-character symbols
        match b {
            b':' => {
                self.cursor += 1;
                if self.cursor < self.bytes.len() && self.bytes[self.cursor] == b':' {
                    self.cursor += 1;
                    Token::new(TokenKind::DoubleColon, ByteSpan::new(start, self.cursor))
                } else {
                    Token::new(TokenKind::Colon, ByteSpan::new(start, self.cursor))
                }
            }
            b'-' => {
                self.cursor += 1;
                if self.cursor < self.bytes.len() && self.bytes[self.cursor] == b'>' {
                    self.cursor += 1;
                    Token::new(TokenKind::Arrow, ByteSpan::new(start, self.cursor))
                } else {
                    Token::new(TokenKind::Minus, ByteSpan::new(start, self.cursor))
                }
            }
            b'=' => {
                self.cursor += 1;
                if self.cursor < self.bytes.len() && self.bytes[self.cursor] == b'=' {
                    self.cursor += 1;
                    Token::new(TokenKind::EqEq, ByteSpan::new(start, self.cursor))
                } else if self.cursor < self.bytes.len() && self.bytes[self.cursor] == b'>' {
                    self.cursor += 1;
                    Token::new(TokenKind::FatArrow, ByteSpan::new(start, self.cursor))
                } else {
                    Token::new(TokenKind::Eq, ByteSpan::new(start, self.cursor))
                }
            }
            b'!' => {
                self.cursor += 1;
                if self.cursor < self.bytes.len() && self.bytes[self.cursor] == b'=' {
                    self.cursor += 1;
                    Token::new(TokenKind::BangEq, ByteSpan::new(start, self.cursor))
                } else {
                    Token::new(TokenKind::Bang, ByteSpan::new(start, self.cursor))
                }
            }
            b'<' => {
                self.cursor += 1;
                if self.cursor < self.bytes.len() && self.bytes[self.cursor] == b'=' {
                    self.cursor += 1;
                    Token::new(TokenKind::LtEq, ByteSpan::new(start, self.cursor))
                } else {
                    Token::new(TokenKind::Lt, ByteSpan::new(start, self.cursor))
                }
            }
            b'>' => {
                self.cursor += 1;
                if self.cursor < self.bytes.len() && self.bytes[self.cursor] == b'=' {
                    self.cursor += 1;
                    Token::new(TokenKind::GtEq, ByteSpan::new(start, self.cursor))
                } else {
                    Token::new(TokenKind::Gt, ByteSpan::new(start, self.cursor))
                }
            }
            b'&' => {
                self.cursor += 1;
                if self.cursor < self.bytes.len() && self.bytes[self.cursor] == b'&' {
                    self.cursor += 1;
                    Token::new(TokenKind::AmpAmp, ByteSpan::new(start, self.cursor))
                } else {
                    Token::new(TokenKind::Unknown('&'), ByteSpan::new(start, self.cursor))
                }
            }
            b'|' => {
                self.cursor += 1;
                if self.cursor < self.bytes.len() && self.bytes[self.cursor] == b'|' {
                    self.cursor += 1;
                    Token::new(TokenKind::PipePipe, ByteSpan::new(start, self.cursor))
                } else {
                    Token::new(TokenKind::Unknown('|'), ByteSpan::new(start, self.cursor))
                }
            }
            b'{' => {
                self.cursor += 1;
                Token::new(TokenKind::LBrace, ByteSpan::new(start, self.cursor))
            }
            b'}' => {
                self.cursor += 1;
                Token::new(TokenKind::RBrace, ByteSpan::new(start, self.cursor))
            }
            b'(' => {
                self.cursor += 1;
                Token::new(TokenKind::LParen, ByteSpan::new(start, self.cursor))
            }
            b')' => {
                self.cursor += 1;
                Token::new(TokenKind::RParen, ByteSpan::new(start, self.cursor))
            }
            b'[' => {
                self.cursor += 1;
                Token::new(TokenKind::LBracket, ByteSpan::new(start, self.cursor))
            }
            b']' => {
                self.cursor += 1;
                Token::new(TokenKind::RBracket, ByteSpan::new(start, self.cursor))
            }
            b',' => {
                self.cursor += 1;
                Token::new(TokenKind::Comma, ByteSpan::new(start, self.cursor))
            }
            b';' => {
                self.cursor += 1;
                Token::new(TokenKind::Semicolon, ByteSpan::new(start, self.cursor))
            }
            b'.' => {
                self.cursor += 1;
                Token::new(TokenKind::Dot, ByteSpan::new(start, self.cursor))
            }
            b'+' => {
                self.cursor += 1;
                Token::new(TokenKind::Plus, ByteSpan::new(start, self.cursor))
            }
            b'*' => {
                self.cursor += 1;
                Token::new(TokenKind::Star, ByteSpan::new(start, self.cursor))
            }
            b'/' => {
                self.cursor += 1;
                Token::new(TokenKind::Slash, ByteSpan::new(start, self.cursor))
            }
            b'%' => {
                self.cursor += 1;
                Token::new(TokenKind::Percent, ByteSpan::new(start, self.cursor))
            }
            b'"' => self.lex_string(start),
            _ if b.is_ascii_digit() => self.lex_number(start),
            _ if b.is_ascii_alphabetic() || b == b'_' => self.lex_ident_or_keyword(start),
            _ => {
                let ch = self.source[self.cursor..].chars().next().unwrap_or('?');
                self.cursor += ch.len_utf8();
                Token::new(TokenKind::Unknown(ch), ByteSpan::new(start, self.cursor))
            }
        }
    }

    fn skip_whitespace_and_comments(&mut self) {
        while self.cursor < self.bytes.len() {
            let b = self.bytes[self.cursor];
            if b.is_ascii_whitespace() {
                self.cursor += 1;
            } else if b == b'/' && self.cursor + 1 < self.bytes.len() && self.bytes[self.cursor + 1] == b'/' {
                // Line comment
                self.cursor += 2;
                while self.cursor < self.bytes.len() && self.bytes[self.cursor] != b'\n' {
                    self.cursor += 1;
                }
            } else {
                break;
            }
        }
    }

    fn lex_string(&mut self, start: usize) -> Token {
        self.cursor += 1; // skip opening "
        let mut s = String::new();
        while self.cursor < self.bytes.len() {
            let b = self.bytes[self.cursor];
            if b == b'"' {
                self.cursor += 1; // skip closing "
                return Token::new(TokenKind::StringLit(s), ByteSpan::new(start, self.cursor));
            } else if b == b'\\' && self.cursor + 1 < self.bytes.len() {
                self.cursor += 1;
                match self.bytes[self.cursor] {
                    b'n' => s.push('\n'),
                    b't' => s.push('\t'),
                    b'r' => s.push('\r'),
                    b'\\' => s.push('\\'),
                    b'"' => s.push('"'),
                    other => s.push(other as char),
                }
                self.cursor += 1;
            } else {
                let ch = self.source[self.cursor..].chars().next().unwrap_or('\0');
                s.push(ch);
                self.cursor += ch.len_utf8();
            }
        }
        Token::new(TokenKind::StringLit(s), ByteSpan::new(start, self.cursor))
    }

    fn lex_number(&mut self, start: usize) -> Token {
        let mut is_float = false;
        while self.cursor < self.bytes.len() && self.bytes[self.cursor].is_ascii_digit() {
            self.cursor += 1;
        }
        if self.cursor < self.bytes.len() && self.bytes[self.cursor] == b'.' {
            // Check if next char is digit to distinguish from field access
            if self.cursor + 1 < self.bytes.len() && self.bytes[self.cursor + 1].is_ascii_digit() {
                is_float = true;
                self.cursor += 1;
                while self.cursor < self.bytes.len() && self.bytes[self.cursor].is_ascii_digit() {
                    self.cursor += 1;
                }
            }
        }

        let slice = &self.source[start..self.cursor];
        if is_float {
            Token::new(TokenKind::FloatLit(slice.to_string()), ByteSpan::new(start, self.cursor))
        } else {
            let n: i64 = slice.parse().unwrap_or(0);
            Token::new(TokenKind::IntLit(n), ByteSpan::new(start, self.cursor))
        }
    }

    fn lex_ident_or_keyword(&mut self, start: usize) -> Token {
        while self.cursor < self.bytes.len() {
            let b = self.bytes[self.cursor];
            if b.is_ascii_alphanumeric() || b == b'_' {
                self.cursor += 1;
            } else {
                break;
            }
        }

        let ident = &self.source[start..self.cursor];
        let kind = match ident {
            "afhoum" => TokenKind::KwAfhoum,
            "shaym" => TokenKind::KwShaym,
            "noumenon" => TokenKind::KwNoumenon,
            "synthetic" => TokenKind::KwSynthetic,
            "decision" => TokenKind::KwDecision,
            "intent" => TokenKind::KwIntent,
            "requires" => TokenKind::KwRequires,
            "ensures" => TokenKind::KwEnsures,
            "decreases" => TokenKind::KwDecreases,
            "effects" => TokenKind::KwEffects,
            "pub" => TokenKind::KwPub,
            "fn" => TokenKind::KwFn,
            "pure" => TokenKind::KwPure,
            "handle" => TokenKind::KwHandle,
            "with" => TokenKind::KwWith,
            "governor" => TokenKind::KwGovernor,
            "approval_gate" => TokenKind::KwApprovalGate,
            "dyn" => TokenKind::KwDyn,
            "table" => TokenKind::KwTable,
            "of" => TokenKind::KwOf,
            "perform" => TokenKind::KwPerform,
            "resume" => TokenKind::KwResume,
            "let" => TokenKind::KwLet,
            "mut" => TokenKind::KwMut,
            "if" => TokenKind::KwIf,
            "else" => TokenKind::KwElse,
            "match" => TokenKind::KwMatch,
            "return" => TokenKind::KwReturn,
            "const" => TokenKind::KwConst,
            "proof" => TokenKind::KwProof,
            "type" => TokenKind::KwType,
            "cap" => TokenKind::KwCap,
            "unity" => TokenKind::KwUnity,
            "plurality" => TokenKind::KwPlurality,
            "totality" => TokenKind::KwTotality,
            "reality" => TokenKind::KwReality,
            "negation" => TokenKind::KwNegation,
            "limitation" => TokenKind::KwLimitation,
            "substance" => TokenKind::KwSubstance,
            "causality" => TokenKind::KwCausality,
            "community" => TokenKind::KwCommunity,
            "possible" => TokenKind::KwPossible,
            "actual" => TokenKind::KwActual,
            "necessary" => TokenKind::KwNecessary,
            "never" => TokenKind::KwNever,
            "secret" => TokenKind::KwSecret,
            "true" => TokenKind::BoolLit(true),
            "false" => TokenKind::BoolLit(false),
            _ => TokenKind::Ident(ident.to_string()),
        };

        Token::new(kind, ByteSpan::new(start, self.cursor))
    }
}
