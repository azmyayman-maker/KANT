use std::collections::BTreeMap;
use kant_core::{DefHash, SymbolId};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Lockfile {
    pub version: String,
    pub pins: BTreeMap<SymbolId, DefHash>,
}

impl Lockfile {
    pub fn new() -> Self {
        Self {
            version: "v0.1".to_string(),
            pins: BTreeMap::new(),
        }
    }

    pub fn insert(&mut self, symbol: SymbolId, hash: DefHash) {
        self.pins.insert(symbol, hash);
    }
}

impl Default for Lockfile {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReconciliationAction {
    AcceptMatch { symbol: SymbolId, hash: DefHash },
    ResolutionChangedError { symbol: SymbolId, got_hash: DefHash, existing_alias: SymbolId },
    ContentDrift { symbol: SymbolId, old_hash: DefHash, new_hash: DefHash },
    MechanicalRename { old_name: SymbolId, new_name: SymbolId, hash: DefHash },
    UnresolvedSymbol { symbol: SymbolId },
    NewPin { symbol: SymbolId, hash: DefHash },
}

pub struct LockfileEngine;

impl LockfileEngine {
    pub fn reconcile(
        current_lock: &Lockfile,
        new_definitions: &BTreeMap<SymbolId, DefHash>,
        is_frozen_ci: bool,
    ) -> (Lockfile, Vec<ReconciliationAction>) {
        let mut updated_lock = current_lock.clone();
        let mut actions = Vec::new();

        // Build inverted index of current lock: Hash -> SymbolId
        let mut hash_to_old_name: BTreeMap<DefHash, SymbolId> = BTreeMap::new();
        for (sym, hash) in &current_lock.pins {
            hash_to_old_name.insert(*hash, sym.clone());
        }

        // Process all newly extracted definitions
        for (new_sym, new_hash) in new_definitions {
            if let Some(old_hash) = current_lock.pins.get(new_sym) {
                if old_hash == new_hash {
                    // Rule R1: Exact Match
                    actions.push(ReconciliationAction::AcceptMatch {
                        symbol: new_sym.clone(),
                        hash: *new_hash,
                    });
                } else if let Some(alias) = hash_to_old_name.get(old_hash) {
                    if alias != new_sym {
                        // Rule R2: Resolution Changed Fatal Error
                        actions.push(ReconciliationAction::ResolutionChangedError {
                            symbol: new_sym.clone(),
                            got_hash: *new_hash,
                            existing_alias: alias.clone(),
                        });
                    } else {
                        // Rule R3: Content Drift
                        actions.push(ReconciliationAction::ContentDrift {
                            symbol: new_sym.clone(),
                            old_hash: *old_hash,
                            new_hash: *new_hash,
                        });
                        if !is_frozen_ci {
                            updated_lock.insert(new_sym.clone(), *new_hash);
                        }
                    }
                } else {
                    // Rule R3: Content Drift
                    actions.push(ReconciliationAction::ContentDrift {
                        symbol: new_sym.clone(),
                        old_hash: *old_hash,
                        new_hash: *new_hash,
                    });
                    if !is_frozen_ci {
                        updated_lock.insert(new_sym.clone(), *new_hash);
                    }
                }
            } else if let Some(old_name) = hash_to_old_name.get(new_hash) {
                // Rule R4: Mechanical Rename (old definition found under new name)
                actions.push(ReconciliationAction::MechanicalRename {
                    old_name: old_name.clone(),
                    new_name: new_sym.clone(),
                    hash: *new_hash,
                });
                if !is_frozen_ci {
                    updated_lock.pins.remove(old_name);
                    updated_lock.insert(new_sym.clone(), *new_hash);
                }
            } else {
                // Rule R6: New Pin
                actions.push(ReconciliationAction::NewPin {
                    symbol: new_sym.clone(),
                    hash: *new_hash,
                });
                if !is_frozen_ci {
                    updated_lock.insert(new_sym.clone(), *new_hash);
                }
            }
        }

        (updated_lock, actions)
    }
}
