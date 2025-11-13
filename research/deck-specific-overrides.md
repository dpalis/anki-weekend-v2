# Deck-Specific Configuration Overrides in Anki 25.x

**Research Date:** 2025-01-13
**Target Version:** Anki 25.x (Qt6)
**Context:** Weekend Addon v2.0 - Need to modify deck-specific overrides, not just shared presets

---

## Executive Summary

Anki has **three tiers of daily limits** that control new cards per day:

1. **Preset** (shared config) - Applied to all decks using that preset
2. **This deck** (deck-specific override) - Permanent override for a specific deck
3. **Today only** (temporary override) - Resets at midnight

**Current Problem:** The addon only modifies tier 1 (shared presets), missing decks that use tier 2/3 overrides.

**Solution:** Must access and modify the deck object's `new_limit` and `new_limit_today` fields directly.

---

## Three-Tier Limit System

### Architecture Overview

```
Collection
├── DeckConfigs (Shared Presets)
│   └── config['new']['perDay'] = 20  ← Tier 1: CURRENTLY WORKING
│
└── Decks
    ├── Normal Deck
    │   ├── config_id → links to DeckConfig
    │   ├── new_limit → Option<i32>       ← Tier 2: PERMANENT OVERRIDE (NOT WORKING)
    │   └── new_limit_today → Option<DayLimit>  ← Tier 3: TEMPORARY OVERRIDE (NOT WORKING)
    │
    └── Filtered Deck (not relevant for this addon)
```

### How Limits Are Applied (Priority Order)

When Anki determines how many new cards to show:

1. **Check Tier 3 first:** If `new_limit_today` exists AND matches today's date → use it
2. **Else check Tier 2:** If `new_limit` exists → use it
3. **Else use Tier 1:** Fall back to `config['new']['perDay']` from shared preset

**Key Insight:** If a deck has a deck-specific override active, modifying the shared preset has NO EFFECT.

---

## Technical Details

### Data Structure (from Anki source code)

Based on research from `rslib/src/decks/mod.rs` and GitHub issue #3875:

```rust
// Simplified structure based on protobuf definitions
pub struct Deck {
    pub id: DeckId,
    pub name: String,
    pub common: DeckCommon,
    pub kind: DeckKind,  // Normal or Filtered
}

pub struct NormalDeck {
    pub config_id: i64,  // Links to shared DeckConfig
    pub new_limit: Option<i32>,  // Tier 2: Permanent deck override
    pub review_limit: Option<i32>,
    pub new_limit_today: Option<DayLimit>,  // Tier 3: Today-only override
    pub review_limit_today: Option<DayLimit>,
}

pub struct DayLimit {
    pub limit: i32,  // The actual limit value
    pub today: u32,  // Day identifier (collection age in days)
}
```

### How Today Limits Work

From GitHub issue #3875 analysis:

- `DayLimit.today` stores the collection age (days since collection created)
- Anki checks: `(limit.today == current_day).then_some(limit.limit)`
- If the stored day matches today → apply the limit
- If the stored day is in the past → ignore it (expired)
- **Bug found:** Setting `limit.today = 0` on collection creation day causes overflow

---

## Legacy Python API (Currently Used)

### What Works (Tier 1 - Shared Presets)

```python
# Current working code from __init__.py lines 286-310
deck = col.decks.get_legacy(deck_id.id)
config_id = deck['conf']  # Get shared config ID
config = col.decks.get_config(config_id)
config['new']['perDay'] = 0  # Modify shared preset
col.decks.save(config)
```

**Limitation:** Only affects decks using the shared preset WITHOUT overrides.

### What Doesn't Work (Tier 2/3 - Deck Overrides)

The deck dictionary returned by `get_legacy()` does NOT expose `new_limit` or `new_limit_today` fields.

```python
deck = col.decks.get_legacy(deck_id.id)
print(deck.keys())
# Output: dict_keys(['id', 'name', 'conf', 'mod', 'usn', ...])
# Missing: 'new_limit', 'new_limit_today'
```

**Why?** The legacy API was designed for Anki 2.1.x compatibility and doesn't expose newer fields.

---

## Modern API (Anki 25.x / Qt6)

### Detecting Deck Overrides

Since Anki 2.1.55+ (released 2022-11-01), deck overrides are stored in the protobuf `Deck` structure.

**Problem:** The Python API (`pylib/anki/decks.py`) doesn't directly expose methods to:
1. Check if a deck has overrides active
2. Modify deck-specific limits (only config limits)

### Available Python Methods (from research)

From `/pylib/anki/decks.py`:

```python
# These methods exist but don't help with deck-specific overrides:
col.decks.update(deck, preserve_usn=True)  # Updates entire deck object
col.decks.update_dict(deck)  # Updates from dict (legacy format)
col.decks.save(deck_or_config)  # Routes to update() or update_config()
```

**Key Finding:** No public Python API to directly manipulate `new_limit` or `new_limit_today`.

---

## Proposed Solutions

### Option 1: Backend Service Call (Recommended for Anki 25.x)

Access the protobuf-based backend directly via `col._backend`:

```python
# HYPOTHETICAL CODE - needs testing
from anki.decks_pb2 import Deck  # Import protobuf types

# Get deck as protobuf object
deck_proto = col._backend.get_deck(deck_id)

# Check if deck has overrides
if deck_proto.kind.HasField('normal'):
    normal = deck_proto.kind.normal

    # Check for permanent override (Tier 2)
    if normal.HasField('new_limit'):
        original_limit = normal.new_limit
        # Store original and set to 0
        normal.new_limit = 0

    # Check for today override (Tier 3)
    if normal.HasField('new_limit_today'):
        # Handle today limit
        pass

    # Update deck
    col._backend.add_or_update_deck(deck_proto)
```

**Status:** Needs verification - `_backend` API is internal and may change.

### Option 2: Database Direct Access (Not Recommended)

Directly query/modify the `decks` table in Anki's SQLite database:

```python
# DANGEROUS - bypasses Anki's validation and sync logic
deck_data = col.db.scalar("SELECT data FROM decks WHERE id = ?", deck_id)
deck_dict = json.loads(deck_data)

# Modify deck_dict['new_limit'] directly
# ... then write back

# DON'T DO THIS - will break sync and may corrupt data
```

**Why not recommended:**
- Bypasses sync marking (AnkiWeb won't know about changes)
- No validation (can corrupt data)
- May break with Anki updates
- Against addon best practices

### Option 3: Work Around with Config Presets (Acceptable)

If we can't modify deck overrides, document the limitation:

```python
def apply_weekend_mode():
    """
    LIMITATION: Only affects decks using shared presets.
    Decks with "This deck" overrides must be manually set to 0.
    """
    # ... existing code ...

    # Add user warning if override detected
    # (but we can't reliably detect this with current API)
```

**Trade-off:** Users must manually disable overrides during weekends.

---

## Detection Strategy

### How to Detect if Override is Active

Since we can't directly access `new_limit` fields, we can infer it:

```python
def has_deck_override(deck_id: int) -> bool:
    """
    Detect if a deck has a deck-specific override active.

    HEURISTIC (not 100% reliable):
    - Get the shared config limit
    - Get the deck's actual limit (from scheduler)
    - If they differ → override is active
    """
    deck = col.decks.get_legacy(deck_id)
    config = col.decks.get_config(deck['conf'])
    shared_limit = config['new']['perDay']

    # Get actual limit from scheduler (includes overrides)
    # TODO: Find API to get effective limit
    # actual_limit = ???

    # return actual_limit != shared_limit
    pass  # Not implementable with current research
```

**Problem:** No public API found to get "effective limit" (after overrides applied).

---

## Breaking Changes from Anki 2.1.50+ (Qt6 Migration)

### PyQt5 → PyQt6 Rename

```python
# Old (Anki 2.1.49 and earlier)
from PyQt5.QtWidgets import QDialog

# New (Anki 2.1.50+)
from PyQt6.QtWidgets import QDialog

# Compatibility shim (works for both)
from aqt.qt import QDialog  # RECOMMENDED FOR ADDONS
```

**Impact on this addon:** None - we don't use Qt widgets currently.

### Enum Qualification Required

```python
# Old
Qt.AlignCenter

# New
Qt.AlignmentFlag.AlignCenter
```

**Impact:** None for this addon.

### Scheduler V3 Changes

- Anki 25.x uses V3 scheduler by default
- Deck limit behavior with subdecks changed
- Custom scheduling is global (not per-preset)

**Impact:** Need to ensure addon works with V3 scheduler behavior.

---

## Recommended Approach for This Addon

### Short-Term (MVP for v2.0)

1. **Continue using current approach** (modify shared presets only)
2. **Document limitation** in README:
   ```
   LIMITATION: Decks with "This deck" or "Today only" overrides
   are NOT automatically paused. Users must manually set these to 0.
   ```
3. **Add detection** (if possible) and warn users:
   ```
   "Warning: Deck 'Japanese' may have deck-specific limits that
   won't be affected by Weekend Mode. Check deck options manually."
   ```

### Long-Term (Future Enhancement)

1. **Research `_backend` API** further - test protobuf access
2. **Submit addon API request** to Anki developers (via GitHub issue)
3. **Wait for official API** - Anki team may expose deck limit methods

---

## Code Examples for Implementation

### Current Working Code (Tier 1 Only)

From `/Users/dpalis/Coding/Anki Weekend Addon v2/__init__.py` lines 282-346:

```python
def apply_weekend_mode() -> None:
    col = mw.col
    if not col:
        return

    deck_ids = col.decks.all_names_and_ids()

    for deck_id in deck_ids:
        deck = col.decks.get_legacy(deck_id.id)
        if not deck or 'conf' not in deck:
            continue

        config = col.decks.get_config(deck['conf'])
        if not config or 'new' not in config:
            continue

        config_id_str = str(deck['conf'])

        # Store original limit
        if config_id_str not in stored_limits:
            original_limit = config['new']['perDay']
            store_original_limit(deck['conf'], original_limit)

        # Set to 0 (Tier 1 only)
        config['new']['perDay'] = 0
        col.decks.save(config)
```

**What this misses:** Decks with `new_limit` or `new_limit_today` set.

### Proposed Enhancement (Needs Testing)

```python
def apply_weekend_mode_with_overrides() -> None:
    """
    EXPERIMENTAL: Attempt to handle deck-specific overrides.
    May not work - requires testing with Anki 25.x backend.
    """
    col = mw.col
    if not col:
        return

    # Try to access backend directly
    try:
        deck_ids = col.decks.all_names_and_ids()

        for deck_id in deck_ids:
            # Attempt 1: Use backend protobuf API
            try:
                deck_proto = col._backend.get_deck(deck_id.id)

                # Check for normal deck with overrides
                if hasattr(deck_proto, 'normal'):
                    # Store and clear new_limit (Tier 2)
                    if hasattr(deck_proto.normal, 'new_limit'):
                        # Store original
                        original = deck_proto.normal.new_limit
                        store_original_limit(f"deck_{deck_id.id}", original)

                        # Set to 0
                        deck_proto.normal.new_limit = 0

                    # Store and clear new_limit_today (Tier 3)
                    if hasattr(deck_proto.normal, 'new_limit_today'):
                        # Clear today limit
                        deck_proto.normal.ClearField('new_limit_today')

                    # Save deck
                    col._backend.add_or_update_deck(deck_proto)

            except AttributeError:
                # Backend API not available - fall back to legacy
                pass

            # Attempt 2: Legacy API (Tier 1 only)
            deck = col.decks.get_legacy(deck_id.id)
            if deck and 'conf' in deck:
                config = col.decks.get_config(deck['conf'])
                if config:
                    config['new']['perDay'] = 0
                    col.decks.save(config)

    except Exception as e:
        print(f"[Weekend Addon] ERROR: {e}")
        # Fall back to current implementation
        apply_weekend_mode()  # Original function
```

**WARNING:** This code is UNTESTED and may not work. Use with caution.

---

## Testing Strategy

### Test Cases for Deck Override Handling

1. **Deck with shared preset only** (Tier 1)
   - Set preset to 20 new/day
   - Apply weekend mode
   - Expected: Limit → 0
   - Expected: Restore → 20
   - Status: ✅ WORKING

2. **Deck with "This deck" override** (Tier 2)
   - Set preset to 20, override to 30
   - Apply weekend mode
   - Expected: Limit → 0 (currently FAILS)
   - Expected: Restore → 30 (not 20)

3. **Deck with "Today only" override** (Tier 3)
   - Set preset to 20, today override to 5
   - Apply weekend mode
   - Expected: Limit → 0 (currently FAILS)
   - Expected: Restore → 20 (not 5, since today override should expire)

4. **Edge case: Deck override = 0 legitimately**
   - User intentionally sets "This deck" to 0
   - Apply weekend mode
   - Expected: Don't capture this as original (it's already 0)
   - Expected: Don't restore to 0 on weekday

### How to Test Manually

1. Create test deck in Anki
2. Open Deck Options
3. Click "This deck" tab
4. Set "New cards/day" to 30
5. Verify preset still shows 20
6. Run addon's `apply_weekend_mode()`
7. Check if deck limit is now 0 (inspect via deck options)
8. Run addon's `apply_weekday_mode()`
9. Check if deck limit restored to 30 (not 20)

**Current Status:** Steps 7-9 will FAIL with current implementation.

---

## References

### Anki Source Code

- **Deck structure:** `rslib/src/decks/mod.rs`
- **Python API:** `pylib/anki/decks.py`
- **Protobuf definitions:** `proto/anki/decks.proto` (not directly accessed)
- **UI strings:** `ftl/core/deck-config.ftl`

### GitHub Issues

- **#3875:** "[BUG] Daily Limits are broken"
  https://github.com/ankitects/anki/issues/3875
  - Reveals `new_limit_today`, `review_limit_today` fields
  - Shows `DayLimit` structure with `limit` and `today` fields
  - Bug: overflow when `today = 0` (collection creation day)

- **#2804:** "Allow im-/exporting with or without deck configs"
  https://github.com/ankitects/anki/pull/2804
  - Shows deck override fields exist in export/import

### Anki Releases

- **2.1.55 (2022-11-01):** Introduced deck-specific daily limits
  - "Preset", "This deck", "Today only" tabs added to UI
  - Backend storage in protobuf `Deck.normal.new_limit` fields

- **2.1.50 (2021-10-01):** Qt6 migration
  - PyQt5 → PyQt6 rename
  - Compatibility shims added (won't last forever)

- **25.x (2025+):** Current target version
  - V3 scheduler default
  - Qt6 fully adopted
  - Legacy APIs may be deprecated

### Documentation

- **Anki Manual - Deck Options:**
  https://docs.ankiweb.net/deck-options.html
  - Explains three-tier limit system
  - "Limits Start From Top" behavior with subdecks

- **Addon Docs - The anki Module:**
  https://addon-docs.ankiweb.net/the-anki-module.html
  - Shows `col.decks.get_config()` and `col.decks.save()` usage
  - Warns against direct database access

---

## Conclusion

### Current State

The addon successfully handles **Tier 1 (shared presets)** but completely misses **Tier 2/3 (deck overrides)**.

### Why This Happens

The Anki Python API (`pylib/anki/decks.py`) does not expose public methods to:
1. Detect if a deck has overrides active
2. Modify deck-specific limit fields (`new_limit`, `new_limit_today`)

### Recommended Action

**For v2.0 MVP:**
1. Ship with current implementation (Tier 1 only)
2. Document limitation clearly in README
3. Add note: "Decks with 'This deck' limits must be manually adjusted"

**For future versions:**
1. Test backend protobuf access (`col._backend`)
2. Submit feature request to Anki team for public API
3. Consider UI to warn users about unmanaged overrides

### Risk Assessment

**Low risk:** Addon will NOT break existing functionality
- Worst case: Some decks not paused (user expects pause)
- No data corruption or sync issues
- Graceful degradation

**Medium impact:** User experience diminished
- Power users with deck overrides won't benefit fully
- May require manual intervention on weekends

**High priority for fix:** If many users rely on deck overrides
- Monitor user feedback after v2.0 launch
- Prioritize based on real-world usage patterns

---

**Document Version:** 1.0
**Last Updated:** 2025-01-13
**Status:** Research complete, implementation pending testing
**Next Steps:** Test protobuf backend access in Anki 25.x environment
