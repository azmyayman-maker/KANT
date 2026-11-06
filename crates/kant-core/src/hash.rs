use std::fmt;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// Represents the 32-byte SHA-256 content address of a Kant canonical definition (A Priori Space).
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct DefHash(pub [u8; 32]);

impl DefHash {
    pub const ZERO: Self = Self([0u8; 32]);

    pub fn from_bytes(bytes: &[u8]) -> Self {
        let mut hasher = Sha256::new();
        hasher.update(bytes);
        let result = hasher.finalize();
        let mut arr = [0u8; 32];
        arr.copy_from_slice(&result);
        Self(arr)
    }

    pub fn from_hex(hex_str: &str) -> Result<Self, String> {
        let clean = hex_str.strip_prefix("0x").unwrap_or(hex_str);
        if clean.len() != 64 {
            return Err(format!("Expected 64 hex characters, got {}", clean.len()));
        }
        let mut arr = [0u8; 32];
        for i in 0..32 {
            arr[i] = u8::from_str_radix(&clean[i * 2..i * 2 + 2], 16)
                .map_err(|e| format!("Invalid hex byte at index {}: {}", i, e))?;
        }
        Ok(Self(arr))
    }

    pub fn to_hex(&self) -> String {
        self.0.iter().map(|b| format!("{:02x}", b)).collect()
    }
}

impl fmt::Debug for DefHash {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "DefHash(0x{}...{})", &self.to_hex()[..8], &self.to_hex()[56..])
    }
}

impl fmt::Display for DefHash {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "0x{}", self.to_hex())
    }
}
