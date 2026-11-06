//! # kant-core
//!
//! Epistemic Role: SA-01: Epistemic & Workspace Bootstrapper
//! Description: Core primitives, spans, interned symbols, and SHA-256 identity hashing
//!
//! Status: Zero-state scaffold. Implementation begins tomorrow.
//! Disambiguation Header: `#![kant(v0.1)]`

#![doc = "Kant programming language - kant-core pristine scaffold"]
#![allow(unused)]

/// Language specification version.
pub const KANT_VERSION: &str = "0.1.0";

/// Disambiguation header tag required in all .kant source units.
pub const KANT_MAGIC_HEADER: &str = "#![kant(v0.1)]";

/// Crate metadata description.
pub const CRATE_ROLE: &str = "SA-01: Epistemic & Workspace Bootstrapper";
