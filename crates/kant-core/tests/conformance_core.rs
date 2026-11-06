use kant_core::{ByteSpan, DefHash, SymbolId, KANT_MAGIC_HEADER};

#[test]
fn test_span_merge_and_len() {
    let s1 = ByteSpan::new(10, 20);
    let s2 = ByteSpan::new(15, 30);
    let merged = s1.merge(s2);
    assert_eq!(merged.start, 10);
    assert_eq!(merged.end, 30);
    assert_eq!(merged.len(), 20);
}

#[test]
fn test_symbol_display_and_equality() {
    let sym1 = SymbolId::new("afhoum");
    let sym2 = SymbolId::from("afhoum");
    assert_eq!(sym1, sym2);
    assert_eq!(sym1.to_string(), "afhoum");
}

#[test]
fn test_defhash_from_bytes_and_hex() {
    let bytes = b"afhoum Point { x: Int64, y: Int64 }";
    let hash = DefHash::from_bytes(bytes);
    let hex = hash.to_hex();
    assert_eq!(hex.len(), 64);
    let recovered = DefHash::from_hex(&hex).expect("valid hex");
    assert_eq!(hash, recovered);
}

#[test]
fn test_magic_header_constant() {
    assert_eq!(KANT_MAGIC_HEADER, "#![kant(v0.1)]");
}
