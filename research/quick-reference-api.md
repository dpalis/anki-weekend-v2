# Quick Reference: Anki Deck Limit APIs

**For:** Weekend Addon v2.0
**Target:** Anki 25.x (Qt6)
**Last Updated:** 2025-01-13

---

## TL;DR - The Problem

Anki has 3 levels of "new cards per day" limits:

| Level | Name | Storage Location | Current Addon |
|-------|------|------------------|---------------|
| 1 | Preset (shared) | `DeckConfig['new']['perDay']` | ✅ WORKS |
| 2 | This deck (permanent) | `Deck.normal.new_limit` | ❌ DOESN'T WORK |
| 3 | Today only (temporary) | `Deck.normal.new_limit_today` | ❌ DOESN'T WORK |

**Root cause:** Python API doesn't expose Level 2/3 fields.

---

## What Currently Works (Level 1: Shared Presets)

### Get Deck Config and Modify

```python
from aqt import mw

# Get collection
col = mw.col
if not col:
    return

# Get all decks
deck_ids = col.decks.all_names_and_ids()

for deck_id in deck_ids:
    # Get deck (legacy API)
    deck = col.decks.get_legacy(deck_id.id)

    # Get shared config ID
    config_id = deck['conf']  # Usually 1 for default

    # Get config object
    config = col.decks.get_config(config_id)

    # Read current limit
    current_limit = config['new']['perDay']  # e.g., 20

    # Modify limit
    config['new']['perDay'] = 0  # Set to 0 for weekend

    # Save (marks for sync automatically)
    col.decks.save(config)
```

### Config Structure

```python
config = {
    'id': 1,
    'name': 'Default',
    'new': {
        'perDay': 20,          # ← NEW CARDS PER DAY LIMIT
        'delays': [1, 10],
        'ints': [1, 4, 7],
        'initialFactor': 2500,
        'order': 1,
        'separate': True,
    },
    'rev': {
        'perDay': 200,         # Review cards per day
        'ease4': 1.3,
        'fuzz': 0.05,
        # ... more settings
    },
    'lapse': { ... },
    'dyn': False,
    'autoplay': True,
    'timer': 0,
    # ... more settings
}
```

**Key Fields:**
- `config['new']['perDay']` - New cards per day limit
- `config['rev']['perDay']` - Review cards per day limit
- `config['id']` - Config ID (referenced by decks)
- `config['name']` - Preset name (e.g., "Default")

---

## What Doesn't Work (Level 2/3: Deck Overrides)

### The Deck Structure (What We Can't Access)

```python
# This is what exists in the database but ISN'T exposed via API:
deck_object = {
    'id': 1234567890,
    'name': 'Japanese::Grammar',
    'conf': 1,  # ← Links to shared config (we CAN access this)

    # These fields exist but are NOT in get_legacy() response:
    'new_limit': 30,  # ← Level 2: Permanent override (HIDDEN)
    'new_limit_today': {  # ← Level 3: Today override (HIDDEN)
        'limit': 5,
        'today': 12345  # Days since collection created
    },
    'review_limit': None,
    'review_limit_today': None,
}
```

### What get_legacy() Actually Returns

```python
deck = col.decks.get_legacy(deck_id.id)
print(deck.keys())
# Output:
# dict_keys(['id', 'name', 'conf', 'mod', 'usn', 'collapsed',
#            'browserCollapsed', 'desc', 'dyn', 'newToday', 'revToday',
#            'lrnToday', 'timeToday'])

# MISSING: 'new_limit', 'new_limit_today', 'review_limit', 'review_limit_today'
```

**Problem:** Override fields are stored in protobuf but not exposed in legacy API.

---

## Proposed Workaround (EXPERIMENTAL - Needs Testing)

### Approach 1: Direct Backend Access

```python
from aqt import mw

def apply_weekend_mode_with_overrides():
    """
    EXPERIMENTAL: Try to access deck overrides via backend.
    May not work - requires Anki 25.x testing.
    """
    col = mw.col
    if not col:
        return

    deck_ids = col.decks.all_names_and_ids()

    for deck_id in deck_ids:
        try:
            # METHOD 1: Try to get deck as protobuf object
            # NOTE: _backend is INTERNAL API - may break in future versions
            deck_proto = col._backend.get_deck(deck_id.id)

            # Check if it's a normal deck (not filtered)
            if hasattr(deck_proto, 'kind') and hasattr(deck_proto.kind, 'normal'):
                normal = deck_proto.kind.normal

                # Check for Level 2 override (permanent)
                if hasattr(normal, 'new_limit'):
                    print(f"Deck {deck_id.name} has new_limit: {normal.new_limit}")
                    # TODO: Store original and set to 0

                # Check for Level 3 override (today only)
                if hasattr(normal, 'new_limit_today'):
                    print(f"Deck {deck_id.name} has new_limit_today")
                    # TODO: Store original and clear

        except AttributeError as e:
            print(f"Backend API not available: {e}")
            # Fall back to Level 1 only
            continue

        except Exception as e:
            print(f"Error accessing deck {deck_id.id}: {e}")
            continue

        # Always handle Level 1 (shared preset) as fallback
        deck = col.decks.get_legacy(deck_id.id)
        if deck and 'conf' in deck:
            config = col.decks.get_config(deck['conf'])
            if config:
                config['new']['perDay'] = 0
                col.decks.save(config)
```

**Status:** UNTESTED - may not work. The `_backend` API is internal and not documented.

### Approach 2: Database Direct Access (NOT RECOMMENDED)

```python
import json
from aqt import mw

def get_deck_with_overrides_DANGEROUS(deck_id):
    """
    WARNING: Direct database access bypasses Anki's sync and validation.
    DO NOT USE IN PRODUCTION. For research only.
    """
    col = mw.col
    deck_json = col.db.scalar("SELECT data FROM decks WHERE id = ?", deck_id)
    deck_dict = json.loads(deck_json)

    # Now we have access to all fields including overrides
    print(deck_dict.get('new_limit'))  # May exist
    print(deck_dict.get('new_limit_today'))  # May exist

    # DON'T MODIFY AND WRITE BACK - will break sync!
```

**Why not recommended:**
1. Bypasses sync marking (AnkiWeb won't sync changes)
2. No validation (can corrupt data)
3. May break with Anki updates
4. Against addon best practices (per Anki docs)

---

## Detection Strategy (Heuristic)

### How to Detect if Override is Active

Since we can't access override fields, we can try to infer:

```python
def might_have_override(deck_id: int) -> bool:
    """
    HEURISTIC: Try to detect if deck has override.
    Not 100% reliable but better than nothing.
    """
    col = mw.col
    deck = col.decks.get_legacy(deck_id)
    config = col.decks.get_config(deck['conf'])

    shared_limit = config['new']['perDay']

    # Check today's new card count
    new_today = deck.get('newToday', [0, 0])[1]  # [day, count]

    # HEURISTIC: If we've seen more new cards today than shared limit allows,
    # there might be an override active
    # (Not reliable - could be from yesterday, manual reviews, etc.)

    # TODO: No reliable way to detect without backend access
    return False  # Can't reliably detect
```

**Problem:** No public API to get "effective limit" after overrides applied.

---

## Recommended Implementation for v2.0

### Stick with Level 1, Document Limitation

```python
def apply_weekend_mode() -> None:
    """
    Set new cards per day = 0 for all decks.

    LIMITATION: Only affects decks using shared presets.
    Decks with "This deck" or "Today only" overrides are NOT modified.
    Users must manually adjust these decks in Deck Options.

    See: https://docs.ankiweb.net/deck-options.html
    """
    col = mw.col
    if not col:
        return

    deck_ids = col.decks.all_names_and_ids()

    for deck_id in deck_ids:
        try:
            deck = col.decks.get_legacy(deck_id.id)
            if not deck or 'conf' not in deck:
                continue

            config = col.decks.get_config(deck['conf'])
            if not config or 'new' not in config:
                continue

            # Store original (if not already stored)
            config_id_str = str(deck['conf'])
            if config_id_str not in stored_limits:
                store_original_limit(deck['conf'], config['new']['perDay'])

            # Set to 0 (Level 1 only)
            config['new']['perDay'] = 0
            col.decks.save(config)

        except Exception as e:
            print(f"Error processing deck {deck_id.id}: {e}")
            continue
```

### Add User Warning (Future Enhancement)

```python
def check_for_potential_overrides() -> list[str]:
    """
    FUTURE: Try to detect decks that might have overrides.
    Warn user to check manually.

    Returns:
        List of deck names that might need manual adjustment
    """
    # TODO: Implement heuristic detection
    # For now, return empty list
    return []

# In GUI/dialog:
potentially_overridden = check_for_potential_overrides()
if potentially_overridden:
    show_warning(
        "The following decks may have deck-specific limits:\n" +
        "\n".join(potentially_overridden) +
        "\n\nPlease check their Deck Options manually."
    )
```

---

## API Reference Summary

### Available Python Methods (from pylib/anki/decks.py)

#### Deck Access
```python
col.decks.all_names_and_ids() -> list[DeckNameId]
col.decks.get_legacy(deck_id: int) -> dict | None
col.decks.id(name: str) -> int | None
col.decks.name(deck_id: int) -> str
```

#### Config Access
```python
col.decks.get_config(config_id: int) -> DeckConfigDict | None
col.decks.all_config() -> list[DeckConfigDict]
col.decks.config_dict_for_deck_id(deck_id: int) -> DeckConfigDict
```

#### Modification
```python
col.decks.save(deck_or_config) -> None  # Routes to update() or update_config()
col.decks.update_config(conf, preserve_usn=False) -> None
col.decks.update(deck, preserve_usn=True) -> None
```

#### Config Management
```python
col.decks.add_config(name: str, clone_from=None) -> DeckConfigDict
col.decks.remove_config(config_id: int) -> None
col.decks.set_config_id_for_deck_dict(deck: dict, config_id: int) -> None
```

### What's Missing (No Public API)

```python
# These DON'T EXIST as public methods:
col.decks.get_deck_override(deck_id)  # ❌ Not available
col.decks.set_deck_override(deck_id, new_limit)  # ❌ Not available
col.decks.has_deck_override(deck_id)  # ❌ Not available
col.decks.clear_deck_override(deck_id)  # ❌ Not available
```

---

## Testing Checklist

### Manual Test Cases

1. **Shared preset only (Level 1)**
   - [ ] Create deck with default config (20 new/day)
   - [ ] Apply weekend mode
   - [ ] Verify: Config → Preset shows 0
   - [ ] Apply weekday mode
   - [ ] Verify: Config → Preset shows 20
   - Status: ✅ SHOULD WORK

2. **Deck override (Level 2)**
   - [ ] Create deck with default config (20 new/day)
   - [ ] Go to Deck Options → "This deck" tab
   - [ ] Set new cards/day to 30
   - [ ] Verify: Preset still shows 20, This deck shows 30
   - [ ] Apply weekend mode
   - [ ] Check: Does "This deck" change to 0? (Expected: NO ❌)
   - Status: ❌ KNOWN LIMITATION

3. **Today override (Level 3)**
   - [ ] Create deck with default config (20 new/day)
   - [ ] Go to Deck Options → "Today only" tab
   - [ ] Set new cards/day to 5
   - [ ] Apply weekend mode
   - [ ] Check: Does "Today only" clear? (Expected: NO ❌)
   - Status: ❌ KNOWN LIMITATION

### How to Verify Limits

```python
# In Anki's debug console (Tools → Debug → Debug Console):

# Get deck
deck = mw.col.decks.get_legacy(1234567890)  # Replace with deck ID

# Get config
config = mw.col.decks.get_config(deck['conf'])

# Check limit
print(f"Preset limit: {config['new']['perDay']}")

# Try to check override (will fail)
print(f"Deck override: {deck.get('new_limit', 'NOT ACCESSIBLE')}")
```

---

## Conclusion

### For v2.0 Release

**What works:**
✅ Modify shared preset limits (Level 1)
✅ Store and restore original limits
✅ Sync changes via AnkiWeb

**What doesn't work:**
❌ Modify deck-specific overrides (Level 2)
❌ Modify today-only overrides (Level 3)
❌ Detect if overrides are active

**Recommendation:**
Ship v2.0 with Level 1 support only. Document limitation clearly:

> **Note:** This addon only affects decks using shared presets (Deck Options → "Preset" tab).
> If you've set custom limits via "This deck" or "Today only" tabs, you must manually
> adjust those during weekends.

### For Future Versions

1. Test `col._backend` API access (may work in Anki 25.x)
2. Submit feature request to Anki team for public API
3. Monitor Anki releases for new deck override APIs
4. Consider contributing to Anki codebase to add these methods

---

**Document Version:** 1.0
**Status:** Complete
**Next Action:** Test protobuf backend access in live Anki 25.x environment
