pub mod span;
pub mod symbol;
pub mod hash;

pub use span::ByteSpan;
pub use symbol::SymbolId;
pub use hash::DefHash;

/// The standard language identity constants
pub const KANT_MAGIC_HEADER: &str = "#![kant(v0.1)]";
pub const KANT_SOURCE_EXT: &str = ".kant";
pub const KANT_SIDECAR_EXT: &str = ".kantd";
pub const KANT_LOCKFILE_NAME: &str = "module.kant.lock";
pub const KANT_SPEC_EXT: &str = ".spec";
