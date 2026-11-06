use kant_parser::{parse, BinaryOp, Expr, Literal, ToplevelItem};

#[test]
fn test_parse_full_function_with_contracts() {
    let src = r#"#![kant(v0.1)]
pub fn factorial(n: Int64) -> Int64 {
    intent "Compute factorial recursively"
    requires n >= 0
    decreases n
    effects pure
} = {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}"#;
    let ast = parse(src);
    assert!(ast.has_magic_header);
    assert_eq!(ast.items.len(), 1);

    if let ToplevelItem::Function(f) = &ast.items[0] {
        assert!(f.is_pub);
        assert_eq!(f.name.as_str(), "factorial");
        assert_eq!(f.params.len(), 1);
        let contracts = f.contracts.as_ref().expect("contracts present");
        assert_eq!(contracts.intent.as_deref(), Some("Compute factorial recursively"));
        assert_eq!(contracts.requires.len(), 1);
        assert!(contracts.decreases.is_some());
    } else {
        panic!("Expected Function");
    }
}

#[test]
fn test_parse_decision_block() {
    let src = r#"decision ADR001 {
    status: "Accepted";
    rationale: "Closed vocabulary prevents hallucination";
}"#;
    let ast = parse(src);
    assert_eq!(ast.items.len(), 1);
    if let ToplevelItem::Decision(d) = &ast.items[0] {
        assert_eq!(d.name.as_str(), "ADR001");
        assert_eq!(d.fields.len(), 2);
        assert_eq!(d.fields[0].0.as_str(), "status");
        assert_eq!(d.fields[0].1, "Accepted");
    } else {
        panic!("Expected Decision block");
    }
}

#[test]
fn test_parse_afhoum_and_cap() {
    let src = r#"
afhoum Point {
    x: Int64;
    y: Int64;
}

cap FsCap {
    read(String);
    write(String, String);
}
"#;
    let ast = parse(src);
    assert_eq!(ast.items.len(), 2);
    assert!(matches!(&ast.items[0], ToplevelItem::Type(_)));
    assert!(matches!(&ast.items[1], ToplevelItem::Capability(_)));
}

#[test]
fn test_parse_typed_hole_and_operator_precedence() {
    let src = r#"
fn calc() -> Int64 = {
    let x = ?hole;
    1 + 2 * 3
}
"#;
    let ast = parse(src);
    if let ToplevelItem::Function(f) = &ast.items[0] {
        assert_eq!(f.body.stmts.len(), 1);
        let trailing = f.body.trailing_expr.as_ref().expect("trailing expr");
        // Check 1 + (2 * 3) precedence
        if let Expr::Binary { op, rhs, .. } = trailing.as_ref() {
            assert_eq!(*op, BinaryOp::Add);
            assert!(matches!(rhs.as_ref(), Expr::Binary { op: BinaryOp::Mul, .. }));
        } else {
            panic!("Expected binary addition at root");
        }
    } else {
        panic!("Expected Function");
    }
}
