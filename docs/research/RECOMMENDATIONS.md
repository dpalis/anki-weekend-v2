# Implementation Recommendations for Weekend Addon v2.0

**Based on:** Cross-platform research completed 2025-01-11
**Status:** Ready for architecture planning

---

## Core Recommendation: Strategy 1 (Deck Configuration Modification)

### Why This Approach

After extensive research of existing addons and Anki's sync architecture, **modifying deck configuration (new cards limit)** is the optimal approach because:

1. ✅ **Syncs to mobile automatically** - solves the core cross-platform problem
2. ✅ **Non-invasive** - doesn't modify scheduling algorithm or card due dates
3. ✅ **Reversible** - can restore original state easily
4. ✅ **Simple** - easy to understand, debug, and maintain
5. ✅ **Safe** - graceful degradation if addon disabled
6. ✅ **Compatible** - won't conflict with other scheduling addons

### What Other Addons Do Wrong

**AnkiWeekendsAndHolidays:**
- Reschedules card due dates (Strategy 3)
- Works cross-platform BUT invasive to SRS algorithm
- Changes intervals, violates spaced repetition principles
- Difficult to undo, potential for permanent damage

**Free Weekend:**
- Reschedules within fuzz range (Strategy 3 limited)
- Less invasive but still modifies algorithm
- Doesn't work with v3 scheduler
- Only affects cards with 3+ day intervals
- Doesn't work on learning cards

**anki-limitnew:**
- Uses scheduler hooks (Strategy 2)
- Clean and non-invasive BUT desktop-only
- Doesn't affect mobile at all
- User sees new cards on mobile (fails core requirement)

### Our Approach (Best of All)

**Modify deck configuration + hooks for UX:**
- Primary: Set `config["new"]["perDay"] = 0` on weekends (syncs to mobile)
- Secondary: Use hooks for UI feedback on desktop
- Travel mode: Same mechanism, manual trigger
- Safe: Store original limits, restore on weekdays

---

## Technical Implementation Plan

### 1. Core Logic

```python
# Weekend detection
def is_weekend(date=None):
    """Check if date is Saturday or Sunday"""
    if date is None:
        date = datetime.now()
    return date.weekday() in [5, 6]  # Sat=5, Sun=6

# Config modification
def set_weekend_mode(enabled: bool):
    """Enable or disable weekend mode across all decks"""
    for deck_id in mw.col.decks.all_ids():
        config_id = mw.col.decks.get(deck_id)['conf']
        config = mw.col.decks.get_config(config_id)

        if enabled:
            # Store original if not already stored
            if not state_manager.has_original(deck_id):
                original_limit = config["new"]["perDay"]
                state_manager.store_original(deck_id, original_limit)

            # Set to 0
            config["new"]["perDay"] = 0
        else:
            # Restore original
            original_limit = state_manager.get_original(deck_id)
            if original_limit is not None:
                config["new"]["perDay"] = original_limit

        # Save (marks for sync)
        mw.col.decks.save(config)
```

### 2. State Management

**Store in addon config.json:**
```json
{
    "original_limits": {
        "1234567890": {
            "limit": 20,
            "stored_at": "2025-01-11T09:00:00Z"
        }
    },
    "travel_mode_active": false,
    "language": "auto"
}
```

**Why store original limits:**
- User may change deck settings while addon active
- Need to differentiate user changes from addon changes
- Required for proper restoration
- Enables audit trail

### 3. Trigger Points

**When to check and apply mode:**

1. **On Anki startup** (`profile_did_open` hook)
   - Check if today is weekend
   - Apply appropriate mode
   - Handles case where Anki closed Friday, opened Saturday

2. **On day change** (hourly timer checking)
   - Every hour, check if date changed
   - If Friday → Saturday: apply weekend mode
   - If Sunday → Monday: apply weekday mode
   - Acceptable latency: user might study at 12:01 AM with wrong mode for <1 hour

3. **On manual trigger** (travel mode button)
   - User clicks "Enable Travel Mode"
   - Apply weekend mode immediately
   - Set flag to prevent auto-restore

### 4. Module Structure

```
anki_weekend_addon_v2/
├── __init__.py              # Addon entry point, hook registration
├── config.json              # User configuration
├── meta.json                # Addon metadata
├── core/
│   ├── __init__.py
│   ├── weekend_detector.py  # is_weekend(), date logic
│   ├── config_manager.py    # Deck config modification
│   ├── state_manager.py     # Original limits storage
│   └── timer.py             # Day change detection
├── ui/
│   ├── __init__.py
│   ├── menu.py              # Tools menu integration
│   ├── dialog.py            # Settings/travel mode dialog
│   └── indicator.py         # Status indicator (optional)
├── utils/
│   ├── __init__.py
│   ├── i18n.py              # Internationalization
│   └── logger.py            # Logging
└── tests/
    ├── test_weekend_detector.py
    ├── test_config_manager.py
    └── test_state_manager.py
```

### 5. Key Hooks to Use

```python
from aqt import gui_hooks

# On profile load
gui_hooks.profile_did_open.append(on_profile_open)

# On profile unload (cleanup)
gui_hooks.profile_will_close.append(on_profile_close)

# On collection loaded
gui_hooks.collection_did_load.append(on_collection_load)

# Optional: On sync complete (verify state)
gui_hooks.sync_did_finish.append(on_sync_finish)
```

**Why not use scheduler hooks:**
- We're modifying config, not intercepting scheduling
- Hooks would be redundant
- Keep it simple

### 6. Error Handling

```python
def set_weekend_mode(enabled: bool):
    try:
        # Core logic here
        pass
    except Exception as e:
        # Log error
        logger.error(f"Failed to set weekend mode: {e}")

        # Show user-friendly message
        show_warning(
            "Weekend Addon: Failed to apply mode. "
            "Please check addon settings or report the issue."
        )

        # Don't crash Anki
        return False

    return True
```

**Never crash Anki:**
- Catch all exceptions in addon code
- Log errors for debugging
- Provide user feedback
- Degrade gracefully

---

## User Experience Design

### First Run

**On first addon enable:**
1. Detect current day (weekend or weekday)
2. Scan all decks, store current new card limits
3. If weekend: apply weekend mode immediately
4. If weekday: wait for next weekend
5. Show welcome dialog explaining behavior

### Settings Dialog

**Accessible from Tools menu:**
- Current mode indicator (Weekend Mode / Weekday Mode / Travel Mode)
- Travel mode toggle button
- Language selection (PT-BR / English / Auto)
- Advanced: Manual restore original limits (in case of issues)

### Status Indicator (Optional v2.1+)

**Subtle visual indicator:**
- Toolbar button showing current mode
- Tooltip: "Weekend Mode Active - No New Cards"
- Click to open settings dialog

### Sync Reminders

**Context-aware notifications:**
- If user studied on desktop, about to close Anki
- Reminder: "Don't forget to sync before studying on mobile"
- Option to disable reminder
- Only show on weekends or if travel mode active

---

## Travel Mode Implementation

### Behavior

**"Indefinite weekend":**
- Same mechanism as weekend mode
- Set new cards limit to 0
- BUT: Don't auto-restore on Monday
- Manual disable required

### UI

**Enable travel mode:**
1. User clicks "Enable Travel Mode" button
2. Addon applies weekend mode
3. Sets flag: `travel_mode_active = true`
4. Shows confirmation with instructions to disable

**Disable travel mode:**
1. User clicks "Disable Travel Mode" button
2. Addon restores original limits
3. Sets flag: `travel_mode_active = false`
4. Shows confirmation

### Edge Cases

**User enables travel mode on Saturday:**
- Already in weekend mode
- Just set travel flag
- Prevents auto-restore on Monday

**User disables travel mode on Sunday:**
- Will auto-restore on Monday (normal weekend behavior)
- OR: Restore immediately (more intuitive?)
- Recommendation: Restore immediately when user disables

---

## Language Detection

### Auto-Detection

```python
def detect_language():
    """Detect Anki's interface language"""
    try:
        lang = mw.pm.meta.get('defaultLang', 'en')
        if lang.startswith('pt'):
            return 'pt_BR'
        else:
            return 'en'
    except:
        return 'en'  # Fallback
```

### Strings

**Create `strings.py`:**
```python
STRINGS = {
    'en': {
        'weekend_mode_active': 'Weekend Mode Active',
        'new_cards_paused': 'New cards paused until Monday',
        'travel_mode_enabled': 'Travel Mode Enabled',
        # ... more strings
    },
    'pt_BR': {
        'weekend_mode_active': 'Modo Final de Semana Ativo',
        'new_cards_paused': 'Novos cards pausados até segunda',
        'travel_mode_enabled': 'Modo Viagem Ativado',
        # ... more strings
    }
}

def get_string(key, lang='auto'):
    if lang == 'auto':
        lang = detect_language()
    return STRINGS.get(lang, STRINGS['en']).get(key, key)
```

---

## Testing Plan

### Unit Tests (pytest)

```python
def test_is_weekend():
    # Saturday
    assert is_weekend(datetime(2025, 1, 11))  # Saturday
    assert is_weekend(datetime(2025, 1, 12))  # Sunday

    # Weekday
    assert not is_weekend(datetime(2025, 1, 13))  # Monday
    assert not is_weekend(datetime(2025, 1, 10))  # Friday

def test_config_modification():
    # Mock Anki collection
    mock_col = MockCollection()

    # Test weekend mode
    set_weekend_mode(True, mock_col)
    assert mock_col.get_new_limit(deck_id) == 0

    # Test restore
    set_weekend_mode(False, mock_col)
    assert mock_col.get_new_limit(deck_id) == 20  # Original

def test_travel_mode():
    # Enable travel mode
    enable_travel_mode()
    assert state.travel_mode_active == True
    assert get_new_limit(deck_id) == 0

    # Simulate Monday (should NOT restore)
    on_day_change(datetime(2025, 1, 13))  # Monday
    assert get_new_limit(deck_id) == 0  # Still 0

    # Disable travel mode
    disable_travel_mode()
    assert state.travel_mode_active == False
    assert get_new_limit(deck_id) == 20  # Restored
```

### Integration Tests (Manual)

**Test Matrix:**

| Scenario | Day | Action | Expected Behavior |
|----------|-----|--------|-------------------|
| Fresh install | Friday | Enable addon | Store limits, wait for Sat |
| Fresh install | Saturday | Enable addon | Apply weekend mode immediately |
| Day change | Friday 11:59 PM | Wait 2 min | Weekend mode at 12:00 AM Sat |
| Mobile sync | Saturday | Sync mobile | No new cards on mobile |
| Travel mode | Wednesday | Enable travel | Limits set to 0 |
| Travel persist | Monday | Check limits | Still 0 (don't restore) |
| Travel disable | Tuesday | Disable travel | Limits restored |
| Addon disable | Saturday | Disable addon | Limits stay at 0 (warning) |
| Addon re-enable | Sunday | Enable addon | Resume weekend mode |
| Addon uninstall | Any day | Uninstall | Limits restored (cleanup hook) |

### Mobile Testing Checklist

- [ ] Desktop: Enable addon, sync
- [ ] Mobile: Sync, verify 0 new cards
- [ ] Mobile: Study reviews (should work)
- [ ] Mobile: Check deck options shows limit=0
- [ ] Desktop: Monday, sync
- [ ] Mobile: Sync, verify new cards restored
- [ ] Travel mode: Desktop enable, mobile sync
- [ ] Mobile: Verify travel mode persists

---

## Risks and Mitigations

### Risk 1: User Changes Deck Settings While Addon Active

**Scenario:**
- Weekend mode active (limit=0)
- User manually changes deck options to 30 new cards/day
- Monday: Addon restores old original limit (20 new cards/day)
- User's change lost

**Mitigation:**
- Detect if config changed by user vs addon
- Timestamp each modification
- If user changed config, update stored original
- Or: Prompt user on restore if conflict detected

### Risk 2: Addon Disabled Permanently

**Scenario:**
- User disables addon mid-weekend
- Limits stuck at 0
- User doesn't realize, no new cards Monday

**Mitigation:**
- On addon disable, show dialog:
  - "Warning: Deck limits set to 0 by addon"
  - "Click 'Restore' to reset limits now"
  - "Or manage manually in deck options"
- Provide manual restore function in Tools menu

### Risk 3: Sync Conflicts

**Scenario:**
- Desktop and mobile both modify deck config
- Sync conflict

**Mitigation:**
- Encourage users to sync before studying
- Anki's sync system handles conflicts (last write wins)
- Not much we can do beyond user education

### Risk 4: Timezone Changes

**Scenario:**
- User travels from NYC (EST) to Tokyo (JST)
- Saturday in Tokyo, but Friday in NYC
- Addon confused about current day

**Mitigation:**
- Always use local system time
- Python's `datetime.now()` respects local timezone
- Should work automatically

### Risk 5: Multiple Deck Config Groups

**Scenario:**
- Deck A uses config group "Default" (20 new/day)
- Deck B uses config group "Default" (20 new/day)
- Deck C uses config group "Intensive" (50 new/day)
- Addon modifies all to 0, but only stored one "original"

**Mitigation:**
- Store original per deck, not per config group
- When restoring, use deck-specific original
- If deck shares config group, both get same restoration

**Better approach:**
- Store original per config group
- Key by config_id, not deck_id
- Multiple decks sharing config restored to same value

---

## Performance Optimization

### Batch Operations

**Instead of:**
```python
for deck_id in all_decks:
    config = get_config(deck_id)
    config["new"]["perDay"] = 0
    save_config(config)
    # Triggers sync check each time
```

**Do:**
```python
configs_to_save = []

for deck_id in all_decks:
    config = get_config(deck_id)
    config["new"]["perDay"] = 0
    configs_to_save.append(config)

# Batch save
for config in configs_to_save:
    save_config(config)
```

### Caching

**Cache deck IDs and config mappings:**
```python
# Don't query every time
_deck_cache = None

def get_all_decks():
    global _deck_cache
    if _deck_cache is None:
        _deck_cache = mw.col.decks.all()
    return _deck_cache

# Invalidate cache on deck change
def on_deck_change():
    global _deck_cache
    _deck_cache = None
```

### Timer Frequency

**Every hour is sufficient:**
- Catches day change within 1 hour
- Minimal CPU usage
- Acceptable latency for user

**Don't check every minute:**
- Unnecessary overhead
- Battery drain on laptops
- No user benefit

---

## Code Quality Standards

### Type Hints

```python
from typing import Optional, Dict, List
from datetime import datetime

def is_weekend(date: Optional[datetime] = None) -> bool:
    """Check if date is weekend"""
    pass

def get_deck_config(deck_id: int) -> Dict:
    """Get deck configuration"""
    pass

def store_original_limits(limits: Dict[int, int]) -> None:
    """Store original limits for all decks"""
    pass
```

### Docstrings

```python
def set_weekend_mode(enabled: bool) -> bool:
    """
    Enable or disable weekend mode for all decks.

    When enabled, sets new cards limit to 0 for all decks.
    When disabled, restores original limits from stored state.

    Args:
        enabled: True to enable weekend mode, False to disable

    Returns:
        True if successful, False if error occurred

    Raises:
        ConfigNotFoundError: If deck config cannot be retrieved
    """
    pass
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def set_weekend_mode(enabled: bool):
    logger.info(f"Setting weekend mode: enabled={enabled}")

    try:
        # Logic here
        logger.debug(f"Modified {len(decks)} decks")
    except Exception as e:
        logger.error(f"Failed to set weekend mode: {e}", exc_info=True)
```

### Error Messages

**User-facing:**
- Clear, non-technical language
- Actionable (what user should do)
- Polite tone

**Developer-facing (logs):**
- Technical details
- Stack traces
- Context (deck IDs, config values)

---

## Deployment Plan

### Version 2.0.0 Scope

**MVP Features:**
- ✅ Weekend detection (Saturday + Sunday)
- ✅ Deck config modification
- ✅ Original limits storage and restoration
- ✅ Travel mode (manual trigger)
- ✅ Language support (PT-BR + English)
- ✅ Settings dialog
- ✅ Error handling and logging

**Explicitly Out of Scope:**
- ❌ Custom weekend days (always Sat+Sun for v2.0)
- ❌ Holiday calendars
- ❌ Per-deck configuration
- ❌ Statistics/analytics
- ❌ UI indicator in main window
- ❌ Sync reminders

### Testing Before Release

1. **Code review** (self or peer)
2. **Unit tests** (all pass)
3. **Manual testing** (full test matrix)
4. **Mobile testing** (iOS and Android)
5. **Performance testing** (100+ decks)
6. **Language testing** (PT-BR and EN)
7. **Edge case testing** (midnight, timezone, etc.)

### Release Process

1. Tag version: `v2.0.0`
2. Package addon (zip with all files)
3. Upload to AnkiWeb
4. Update CLAUDE.md with architecture details
5. Write user documentation (README for AnkiWeb)
6. Announce on Anki forums (if desired)

---

## Documentation Requirements

### User Documentation (README.md)

**Sections:**
1. What it does
2. How to install
3. How to use (weekend mode automatic)
4. Travel mode instructions
5. Settings explanation
6. FAQ
7. Troubleshooting
8. Support contact

### Developer Documentation (ARCHITECTURE.md)

**Sections:**
1. System design
2. Module breakdown
3. Data flow
4. API reference
5. Extension points
6. Testing guide

### Code Documentation

- Docstrings on all public functions
- Inline comments for complex logic
- Type hints everywhere
- Examples in docstrings

---

## Success Metrics

**How we'll know v2.0 is successful:**

1. ✅ **Zero critical bugs** in first month
2. ✅ **Mobile compatibility** confirmed by users
3. ✅ **No data loss** (deck limits correctly restored)
4. ✅ **Positive user feedback** on simplicity
5. ✅ **Easy to maintain** (can fix bugs without major refactor)
6. ✅ **Clean code** (80%+ test coverage)
7. ✅ **Reliable** (doesn't crash Anki)

**Comparison to v1.0:**
- v1.0: Buggy, complex, hard to maintain
- v2.0: Stable, simple, mobile-compatible

---

## Next Steps

1. **Update CLAUDE.md** with:
   - Chosen approach (Strategy 1)
   - Architecture overview
   - Module structure
   - Technical decisions rationale

2. **Create architecture diagram** (optional):
   - Data flow
   - Component interaction
   - Hook lifecycle

3. **Run `/compounding-engineering:plan`**:
   - Generate detailed implementation plan
   - Break down into tasks
   - Estimate timeline

4. **Begin implementation**:
   - Start with core modules (weekend_detector, config_manager)
   - Add tests as you go
   - Iterate based on testing feedback

---

## Questions to Resolve Before Implementation

### 1. Config Storage Location

**Options:**
- A. Store original limits in addon config.json
- B. Store in Anki's database (collection.anki2)
- C. Store in separate SQLite database

**Recommendation:** Option A (config.json)
- Simple, standard for addons
- Easy to backup/restore
- Doesn't modify Anki's database

### 2. Restore Timing

**Options:**
- A. Restore on Monday at midnight
- B. Restore on Monday when Anki opens
- C. Restore on Sunday at midnight (proactive)

**Recommendation:** Option B (Monday on open)
- Most reliable (guaranteed to run)
- User likely opens Anki to study Monday
- If they study Sunday night, still in weekend mode (acceptable)

### 3. Travel Mode Auto-Disable

**Options:**
- A. Never auto-disable (user must do it)
- B. Auto-disable after X days
- C. Prompt user after X days

**Recommendation:** Option A (manual disable only)
- Simpler, predictable behavior
- User explicitly enabled, should explicitly disable
- Avoids confusion ("why did it turn off?")

### 4. Multiple Config Groups

**Options:**
- A. Store original per deck
- B. Store original per config group
- C. Store both

**Recommendation:** Option B (per config group)
- More correct (decks share config)
- Simpler to manage
- Covers more cases correctly

### 5. UI Integration Level

**Options:**
- A. Minimal (Tools menu only)
- B. Moderate (Tools menu + status indicator)
- C. Full (Tools menu + indicator + toolbar button)

**Recommendation:** Option A for v2.0 (minimal)
- Faster to implement
- Lower maintenance
- Can add UI in v2.1 if users request

---

## Conclusion

**We have a clear, research-backed path forward:**

1. ✅ **Approach validated:** Strategy 1 (deck config modification) is optimal
2. ✅ **Cross-platform confirmed:** Will work on desktop and mobile
3. ✅ **Technical details understood:** Know exactly how to implement
4. ✅ **Edge cases identified:** Can test and handle them
5. ✅ **Risks mitigated:** Have plans for common failure modes

**Ready to proceed with architecture planning and implementation.**

---

**Document Status:** Final recommendations
**Approved for:** v2.0 implementation
**Next Action:** Update CLAUDE.md with architectural decisions
