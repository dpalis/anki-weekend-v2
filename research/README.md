# Research Documentation

This directory contains technical research findings for the Anki Weekend Addon v2.0.

## Documents

### 1. `deck-specific-overrides.md` (COMPREHENSIVE)

**16KB - Full deep-dive into deck override system**

**Read this if you need:**
- Complete understanding of Anki's three-tier limit system
- Detailed explanation of why current approach doesn't work for overrides
- Technical details about protobuf structures
- Historical context (Anki 2.1.50+ changes, Qt6 migration)
- Testing strategies and edge cases
- Long-term solution proposals

**Sections:**
- Executive Summary
- Three-Tier Limit System Architecture
- Technical Details (Rust structs, protobuf)
- Legacy vs Modern API comparison
- Proposed Solutions (with code examples)
- Breaking Changes from Qt6 migration
- Testing Strategy
- References (GitHub issues, Anki releases)

---

### 2. `quick-reference-api.md` (PRACTICAL)

**12KB - Quick reference for implementation**

**Read this if you need:**
- Code examples for current working API (Level 1 - shared presets)
- Config structure reference
- What doesn't work and why
- Experimental workarounds (untested)
- Recommended implementation for v2.0
- API reference summary
- Testing checklist

**Sections:**
- TL;DR - The Problem
- What Currently Works (code examples)
- What Doesn't Work (missing fields)
- Proposed Workarounds (experimental)
- Recommended Implementation
- API Reference Summary
- Testing Checklist

---

## Key Findings Summary

### The Problem

Anki has **3 levels** of "new cards per day" limits:

| Level | Name | Where | Addon Support |
|-------|------|-------|---------------|
| 1 | Preset (shared) | DeckConfig | ✅ WORKS |
| 2 | This deck (permanent) | Deck.new_limit | ❌ NO API |
| 3 | Today only (temporary) | Deck.new_limit_today | ❌ NO API |

**Current addon only handles Level 1** because Python API doesn't expose Level 2/3 fields.

### Impact

- Decks using shared presets: ✅ Will be paused correctly
- Decks with "This deck" override: ❌ Won't be paused (limitation)
- Decks with "Today only" override: ❌ Won't be paused (limitation)

### Recommendation for v2.0

**Ship with Level 1 support only** + clear documentation of limitation:

> **Note:** This addon only affects decks using shared presets (Deck Options → "Preset" tab).
> If you've set custom limits via "This deck" or "Today only" tabs, you must manually
> adjust those during weekends.

**Why this is acceptable:**
- Most users don't use deck overrides (shared presets are the default)
- Graceful degradation (addon doesn't break, just doesn't pause some decks)
- No data corruption or sync issues
- Can be enhanced in future versions when API becomes available

---

## Code Examples

### Current Working Code (Level 1)

```python
from aqt import mw

col = mw.col
deck_ids = col.decks.all_names_and_ids()

for deck_id in deck_ids:
    deck = col.decks.get_legacy(deck_id.id)
    config = col.decks.get_config(deck['conf'])

    # Store original
    original_limit = config['new']['perDay']

    # Set to 0
    config['new']['perDay'] = 0
    col.decks.save(config)  # Auto-syncs
```

### What We Can't Do (Level 2/3)

```python
# These fields exist but aren't accessible via Python API:
deck.new_limit  # ❌ AttributeError - not in get_legacy() response
deck.new_limit_today  # ❌ AttributeError - not exposed
```

---

## Next Steps

### For v2.0 Release (Now)
1. ✅ Use current working code (Level 1 only)
2. ✅ Document limitation in README
3. ✅ Ship MVP with known constraint

### For Future Versions (Post-launch)
1. Test `col._backend` protobuf API (experimental code in research docs)
2. Submit feature request to Anki team for public API
3. Monitor Anki releases for new deck override methods
4. Consider contributing to Anki codebase

---

## How to Test

### Verify Level 1 Works (Should Pass)

1. Create test deck
2. Set Deck Options → Preset → New cards/day = 20
3. Run addon's weekend mode
4. Check: Preset should now show 0
5. Run addon's weekday mode
6. Check: Preset should restore to 20

### Verify Level 2 Limitation (Expected to Fail)

1. Create test deck
2. Set Deck Options → Preset → New cards/day = 20
3. Set Deck Options → This deck → New cards/day = 30
4. Run addon's weekend mode
5. Check: "This deck" still shows 30 ❌ (NOT paused)
6. Expected: User must manually set to 0

---

## References

### Anki Source Code
- `pylib/anki/decks.py` - Python API for decks
- `rslib/src/decks/mod.rs` - Rust deck structure
- `proto/anki/decks.proto` - Protobuf definitions (not directly accessed)
- `ftl/core/deck-config.ftl` - UI strings for deck config

### Key GitHub Issues
- **#3875** - "[BUG] Daily Limits are broken"
  Reveals new_limit_today, review_limit_today structure

### Anki Releases
- **2.1.55 (2022-11-01)** - Introduced deck-specific limits (3-tier system)
- **2.1.50 (2021-10-01)** - Qt6 migration (PyQt5 → PyQt6)
- **25.x (2025)** - Current target (V3 scheduler default)

### Documentation
- https://docs.ankiweb.net/deck-options.html - Deck options manual
- https://addon-docs.ankiweb.net/ - Addon development docs

---

## Research Timeline

- **2025-01-13:** Initial research completed
  - Identified three-tier limit system
  - Discovered Python API limitation
  - Documented workarounds and recommendations

---

## Questions & Answers

### Q: Why can't we just access deck.new_limit?

**A:** The `get_legacy()` method returns a dictionary that doesn't include these fields. They exist in the database (protobuf format) but aren't exposed in the Python API.

### Q: Can we access the database directly?

**A:** Technically yes, but it's **strongly discouraged**:
- Bypasses sync marking (AnkiWeb won't sync changes)
- No validation (can corrupt data)
- May break with Anki updates
- Against Anki addon best practices

### Q: Will Anki add a public API for this?

**A:** Unknown. We can:
1. Submit a feature request
2. Contribute code to Anki project
3. Wait for community/maintainer interest

### Q: Should we delay v2.0 until this is solved?

**A:** No. Ship with Level 1 support and document limitation. Most users don't use deck overrides, and we can enhance later without breaking existing functionality.

### Q: What percentage of users are affected?

**A:** Unknown - needs user research. Deck overrides were introduced in 2.1.55 (2022), so:
- Power users: May use overrides frequently
- Casual users: Likely stick with shared presets
- **Assumption:** < 20% of users affected (needs validation)

---

**Last Updated:** 2025-01-13
**Status:** Research complete, ready for v2.0 implementation
**Maintainer:** @dpalis
