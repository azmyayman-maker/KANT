pub mod token;
pub mod lexer;

pub use token::{Token, TokenKind};
pub use lexer::Lexer;

/// Tokenize a source string into a list of tokens.
pub fn tokenize(source: &str) -> Vec<Token> {
    Lexer::new(source).tokenize_all()
}
