use kant_canonical::{Canonicalizer, Lockfile, LockfileEngine, ReconciliationAction};
use kant_core::SymbolId;
use kant_parser::parse;
use std::collections::BTreeMap;

#[test]
fn test_alpha_equivalence_invariant() {
    let src1 = r#"
fn add(x: Int64, y: Int64) -> Int64 {
    effects pure
} = {
    x + y
}
"#;
    let src2 = r#"
fn add(first: Int64, second: Int64) -> Int64 {
    effects pure
} = {
    first + second
}
"#;
    let ast1 = parse(src1);
    let ast2 = parse(src2);

    let canon1 = Canonicalizer::canonicalize_source(&ast1);
    let canon2 = Canonicalizer::canonicalize_source(&ast2);

    let def1 = canon1.definitions.get(&SymbolId::new("add")).unwrap();
    let def2 = canon2.definitions.get(&SymbolId::new("add")).unwrap();

    assert_eq!(
        def1.def_hash(),
        def2.def_hash(),
        "Renaming parameters must produce identical SHA-256 DefHash"
    );
}

#[test]
fn test_type_field_order_invariance() {
    let src1 = r#"
afhoum Point {
    x: Int64;
    y: Int64;
}
"#;
    let src2 = r#"
afhoum Point {
    y: Int64;
    x: Int64;
}
"#;
    let ast1 = parse(src1);
    let ast2 = parse(src2);

    let canon1 = Canonicalizer::canonicalize_source(&ast1);
    let canon2 = Canonicalizer::canonicalize_source(&ast2);

    let def1 = canon1.definitions.get(&SymbolId::new("Point")).unwrap();
    let def2 = canon2.definitions.get(&SymbolId::new("Point")).unwrap();

    assert_eq!(
        def1.def_hash(),
        def2.def_hash(),
        "Reordering struct fields must produce identical canonical hash"
    );
}

#[test]
fn test_lockfile_reconciliation_r1_and_r4_mechanical_rename() {
    let mut lock = Lockfile::new();
    let src = r#"
fn compute_total(a: Int64, b: Int64) -> Int64 {
    effects pure
} = {
    a + b
}
"#;
    let ast = parse(src);
    let canon = Canonicalizer::canonicalize_source(&ast);
    let def = canon.definitions.get(&SymbolId::new("compute_total")).unwrap();
    let hash = def.def_hash();

    // Pin original name in lockfile
    lock.insert(SymbolId::new("compute_total"), hash);

    // Case 1: R1 Exact Match
    let mut current_defs = BTreeMap::new();
    current_defs.insert(SymbolId::new("compute_total"), hash);
    let (_, actions) = LockfileEngine::reconcile(&lock, &current_defs, false);
    assert_eq!(actions.len(), 1);
    assert!(matches!(actions[0], ReconciliationAction::AcceptMatch { .. }));

    // Case 2: R4 Mechanical Rename (function renamed to `sum_pair`, but body/hash identical)
    let mut renamed_defs = BTreeMap::new();
    renamed_defs.insert(SymbolId::new("sum_pair"), hash);
    let (updated_lock, actions_r4) = LockfileEngine::reconcile(&lock, &renamed_defs, false);
    assert_eq!(actions_r4.len(), 1);
    if let ReconciliationAction::MechanicalRename { old_name, new_name, .. } = &actions_r4[0] {
        assert_eq!(old_name.as_str(), "compute_total");
        assert_eq!(new_name.as_str(), "sum_pair");
    } else {
        panic!("Expected MechanicalRename");
    }
    assert!(updated_lock.pins.contains_key(&SymbolId::new("sum_pair")));
    assert!(!updated_lock.pins.contains_key(&SymbolId::new("compute_total")));
}
