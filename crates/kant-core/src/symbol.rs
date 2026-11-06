use std::fmt;
use serde::{Deserialize, Serialize};

/// Represents an identifier or symbol in the Kant language.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct SymbolId(pub String);

impl SymbolId {
    pub fn new(name: impl Into<String>) -> Self {
        Self(name.into())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Display for SymbolId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl From<&str> for SymbolId {
    fn from(s: &str) -> Self {
        Self::new(s)
    }
}

impl From<String> for SymbolId {
    fn from(s: String) -> Self {
        Self(s)
    }
}
