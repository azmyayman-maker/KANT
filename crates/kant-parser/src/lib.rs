pub mod ast;
pub mod parser;

pub use ast::*;
pub use parser::Parser;

/// Parse a Kant source string into a Surface AST SourceFile.
pub fn parse(source: &str) -> SourceFile {
    let tokens = kant_lexer::tokenize(source);
    let mut parser = Parser::new(tokens);
    parser.parse_source_file()
}
