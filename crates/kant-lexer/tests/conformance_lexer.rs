use kant_lexer::{tokenize, TokenKind};

#[test]
fn test_magic_header_tokenization() {
    let src = "#![kant(v0.1)]\nfn main() -> Unit = {}";
    let tokens = tokenize(src);
    assert_eq!(tokens[0].kind, TokenKind::MagicHeader);
    assert_eq!(tokens[1].kind, TokenKind::KwFn);
}

#[test]
fn test_typed_hole_tokenization() {
    let src = "let x = ?hole;";
    let tokens = tokenize(src);
    assert_eq!(tokens[0].kind, TokenKind::KwLet);
    assert_eq!(tokens[1].kind, TokenKind::Ident("x".to_string()));
    assert_eq!(tokens[2].kind, TokenKind::Eq);
    assert_eq!(tokens[3].kind, TokenKind::Hole);
}

#[test]
fn test_debruijn_slot_tokenization() {
    let src = "fn add(@Int64.0, @Int64.1) = @Int64.0 + @Int64.1";
    let tokens = tokenize(src);
    assert_eq!(
        tokens[2].kind,
        TokenKind::DeBruijnSlot {
            type_tag: "Int64".to_string(),
            index: 0
        }
    );
    assert_eq!(
        tokens[4].kind,
        TokenKind::DeBruijnSlot {
            type_tag: "Int64".to_string(),
            index: 1
        }
    );
}

#[test]
fn test_closed_epistemic_keywords() {
    let src = "afhoum shaym noumenon synthetic decision intent requires ensures decreases effects";
    let tokens = tokenize(src);
    let kinds: Vec<_> = tokens.into_iter().map(|t| t.kind).collect();
    assert_eq!(
        kinds,
        vec![
            TokenKind::KwAfhoum,
            TokenKind::KwShaym,
            TokenKind::KwNoumenon,
            TokenKind::KwSynthetic,
            TokenKind::KwDecision,
            TokenKind::KwIntent,
            TokenKind::KwRequires,
            TokenKind::KwEnsures,
            TokenKind::KwDecreases,
            TokenKind::KwEffects,
            TokenKind::Eof,
        ]
    );
}

#[test]
fn test_governance_and_effects_keywords() {
    let src = "handle with governor approval_gate dyn table of perform resume pure";
    let tokens = tokenize(src);
    let kinds: Vec<_> = tokens.into_iter().map(|t| t.kind).collect();
    assert_eq!(
        kinds,
        vec![
            TokenKind::KwHandle,
            TokenKind::KwWith,
            TokenKind::KwGovernor,
            TokenKind::KwApprovalGate,
            TokenKind::KwDyn,
            TokenKind::KwTable,
            TokenKind::KwOf,
            TokenKind::KwPerform,
            TokenKind::KwResume,
            TokenKind::KwPure,
            TokenKind::Eof,
        ]
    );
}

#[test]
fn test_string_escapes_and_comments() {
    let src = "// comment here\nlet s = \"hello\\nworld\";";
    let tokens = tokenize(src);
    assert_eq!(tokens[0].kind, TokenKind::KwLet);
    assert_eq!(tokens[3].kind, TokenKind::StringLit("hello\nworld".to_string()));
}
