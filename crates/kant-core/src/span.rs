use serde::{Deserialize, Serialize};

/// Represents a source byte span [start, end) within a Kant source file.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct ByteSpan {
    pub start: usize,
    pub end: usize,
}

impl ByteSpan {
    pub const fn new(start: usize, end: usize) -> Self {
        Self { start, end }
    }

    pub const fn empty() -> Self {
        Self { start: 0, end: 0 }
    }

    pub const fn point(pos: usize) -> Self {
        Self { start: pos, end: pos }
    }

    pub fn len(&self) -> usize {
        self.end.saturating_sub(self.start)
    }

    pub fn is_empty(&self) -> bool {
        self.start >= self.end
    }

    pub fn merge(self, other: Self) -> Self {
        Self {
            start: self.start.min(other.start),
            end: self.end.max(other.end),
        }
    }

    pub fn to_array(&self) -> [usize; 2] {
        [self.start, self.end]
    }
}

impl From<[usize; 2]> for ByteSpan {
    fn from(arr: [usize; 2]) -> Self {
        Self::new(arr[0], arr[1])
    }
}
