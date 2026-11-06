use kant_core::ByteSpan;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum TokenKind {
    // Magic Header
    MagicHeader, // #![kant(v0.1)]

    // Toplevel & Epistemic Keywords
    KwAfhoum,      // afhoum
    KwShaym,       // shaym
    KwNoumenon,    // noumenon
    KwSynthetic,   // synthetic
    KwDecision,    // decision
    KwIntent,      // intent
    KwRequires,    // requires
    KwEnsures,     // ensures
    KwDecreases,   // decreases
    KwEffects,     // effects
    KwPub,         // pub
    KwFn,          // fn

    // Effect & Governance Keywords
    KwPure,         // pure
    KwHandle,       // handle
    KwWith,         // with
    KwGovernor,     // governor
    KwApprovalGate, // approval_gate
    KwDyn,          // dyn
    KwTable,        // table
    KwOf,           // of
    KwPerform,      // perform
    KwResume,       // resume

    // Control & Expression Keywords
    KwLet,    // let
    KwMut,    // mut
    KwIf,     // if
    KwElse,   // else
    KwMatch,  // match
    KwReturn, // return
    KwConst,  // const
    KwProof,  // proof
    KwType,   // type
    KwCap,    // cap

    // Modality & Categories Keywords
    KwUnity,      // unity
    KwPlurality,  // plurality
    KwTotality,   // totality
    KwReality,    // reality
    KwNegation,   // negation
    KwLimitation, // limitation
    KwSubstance,  // substance
    KwCausality,  // causality
    KwCommunity,  // community
    KwPossible,   // possible
    KwActual,     // actual
    KwNecessary,  // necessary
    KwNever,      // never
    KwSecret,     // secret

    // Hole Expression
    Hole, // ?hole

    // Identifiers & Literals
    Ident(String),
    DeBruijnSlot { type_tag: String, index: u32 }, // @T.0
    IntLit(i64),
    FloatLit(String),
    StringLit(String),
    BoolLit(bool),

    // Symbols & Punctuation
    Colon,        // :
    DoubleColon,  // ::
    Arrow,        // ->
    FatArrow,     // =>
    Bang,         // !
    LBrace,       // {
    RBrace,       // }
    LParen,       // (
    RParen,       // )
    LBracket,     // [
    RBracket,     // ]
    Comma,        // ,
    Semicolon,    // ;
    Dot,          // .
    Eq,           // =
    At,           // @
    Plus,         // +
    Minus,        // -
    Star,         // *
    Slash,        // /
    Percent,      // %
    EqEq,         // ==
    BangEq,       // !=
    Lt,           // <
    LtEq,         // <=
    Gt,           // >
    GtEq,         // >=
    AmpAmp,       // &&
    PipePipe,     // ||

    // End of File / Lexer Error
    Eof,
    Unknown(char),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Token {
    pub kind: TokenKind,
    pub span: ByteSpan,
}

impl Token {
    pub fn new(kind: TokenKind, span: ByteSpan) -> Self {
        Self { kind, span }
    }
}
