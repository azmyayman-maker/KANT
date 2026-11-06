use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum KantianCategory {
    // Quantity
    Unity,     // Primitives: Unit, Bool, Int64, Float64, String
    Plurality, // Collections: Slice<T>, Vec<T>
    Totality,  // Exhaustive Enums / Bounded Refinements

    // Quality
    Reality,    // Inhabited Types
    Negation,   // Never (!)
    Limitation, // Attenuated Capability / Refinement

    // Relation
    Substance, // Immutable value structs
    Causality, // Function arrows: A -> B ! E
    Community, // Stream channels: !Stream<T>

    // Modality
    Possibility, // Option<T>, Result<T, E>
    Actuality,   // Live Capability Token Handles (cap &Cap)
    Necessity,   // Proved constants / invariants
}
