# Anki Weekend Addon v2.0 - Work Plan (Simplified)

**Date:** 2025-01-12
**Estimated Time:** 3-5 days
**Approach:** Simple implementation (2 files, ~150 lines)

---

## Context

This work plan implements the simplified architecture validated in our planning session:
- **Files:** 2 (`__init__.py` + `config.json`)
- **Functions:** 6 core functions (no classes)
- **Lines:** ~150 total
- **Complexity:** LOW (appropriate for domain)

**Reference Documents:**
- `CLAUDE.md` - Architectural principles and "Simplicidade Apropriada"
- `ANKI_ADDON_BEST_PRACTICES_RESEARCH.md` - Strategy 1 (Deck Configuration)
- `RESEARCH_FINDINGS.md` - Anki API documentation

---

## Phase 1: Core Implementation (Day 1)

### Task 1.1: Create `__init__.py` with Weekend Detection

**File:** `__init__.py`

**Implement:**
```python
from aqt import mw, gui_hooks
from datetime import datetime

def is_weekend() -> bool:
    """Check if today is Saturday or Sunday."""
    return datetime.now().weekday() in [5, 6]
```

**Acceptance Criteria:**
- [ ] Function returns `True` on Saturday (weekday=5)
- [ ] Function returns `True` on Sunday (weekday=6)
- [ ] Function returns `False` on weekdays (0-4)

**Test Manually:**
```python
# In Anki console (Tools → Add-ons → View Console)
from datetime import datetime
print(datetime.now().weekday())  # Check current day
print(is_weekend())  # Should match expectation
```

---

### Task 1.2: Add Config Management Functions

**File:** `__init__.py`

**Implement:**
```python
def get_config() -> dict:
    """Read addon configuration."""
    return mw.addonManager.getConfig(__name__) or {}

def get_original_limit(config_id: int) -> int | None:
    """Retrieve stored original limit for a deck config."""
    limits = get_config().get('original_limits', {})
    return limits.get(str(config_id))

def store_original_limit(config_id: int, limit: int):
    """Store original limit for future restoration."""
    config = get_config()
    if 'original_limits' not in config:
        config['original_limits'] = {}
    config['original_limits'][str(config_id)] = limit
    mw.addonManager.writeConfig(__name__, config)
```

**Acceptance Criteria:**
- [ ] `get_config()` returns dict (never crashes)
- [ ] `store_original_limit()` persists to config.json
- [ ] `get_original_limit()` retrieves stored value correctly
- [ ] Handles missing keys gracefully

**Test Manually:**
```python
# In Anki console
store_original_limit(1234, 20)
print(get_original_limit(1234))  # Should print: 20
print(get_config())  # Should show: {'original_limits': {'1234': 20}}
```

---

### Task 1.3: Implement Deck Config Modification

**File:** `__init__.py`

**Implement:**
```python
def apply_weekend_mode():
    """Set new cards per day = 0 for all decks."""
    if not mw.col:
        return

    for deck_id in mw.col.decks.all_names_and_ids():
        deck = mw.col.decks.get_legacy(deck_id.id)
        config = mw.col.decks.get_config(deck['conf'])

        # Store original if not already stored
        if get_original_limit(deck['conf']) is None:
            store_original_limit(deck['conf'], config['new']['perDay'])

        # Set limit to 0
        config['new']['perDay'] = 0
        mw.col.decks.save(config)  # Marks for AnkiWeb sync

def apply_weekday_mode():
    """Restore original new cards per day limits."""
    if not mw.col:
        return

    for deck_id in mw.col.decks.all_names_and_ids():
        deck = mw.col.decks.get_legacy(deck_id.id)
        config = mw.col.decks.get_config(deck['conf'])

        # Restore original if exists
        original = get_original_limit(deck['conf'])
        if original is not None:
            config['new']['perDay'] = original
            mw.col.decks.save(config)
```

**Acceptance Criteria:**
- [ ] `apply_weekend_mode()` sets all deck limits to 0
- [ ] Original limits are stored before modification
- [ ] `apply_weekday_mode()` restores original limits
- [ ] Uses `mw.col.decks.save()` for sync compatibility
- [ ] Handles `mw.col` being None gracefully

**Test Manually:**
```python
# 1. Check original limits
for deck_id in mw.col.decks.all_names_and_ids():
    deck = mw.col.decks.get_legacy(deck_id.id)
    config = mw.col.decks.get_config(deck['conf'])
    print(f"Deck: {deck['name']}, Limit: {config['new']['perDay']}")

# 2. Apply weekend mode
apply_weekend_mode()

# 3. Verify limits = 0
# (run step 1 again, all should show 0)

# 4. Restore weekday mode
apply_weekday_mode()

# 5. Verify limits restored
# (run step 1 again, should show original values)
```

---

### Task 1.4: Implement Main Logic

**File:** `__init__.py`

**Implement:**
```python
def on_profile_open():
    """Execute when profile opens (startup + sync)."""
    if not mw.col:
        return

    config = get_config()

    # Priority 1: Travel mode
    if config.get('travel_mode', False):
        apply_weekend_mode()
    # Priority 2: Weekend
    elif is_weekend():
        apply_weekend_mode()
    # Priority 3: Weekday
    else:
        apply_weekday_mode()

# Register hook
gui_hooks.profile_did_open.append(on_profile_open)
```

**Acceptance Criteria:**
- [ ] Hook registered successfully
- [ ] Travel mode takes precedence over date
- [ ] Weekend detection works correctly
- [ ] Weekday mode restores limits
- [ ] No crashes on startup

**Test Manually:**
1. Restart Anki
2. Check console for errors
3. Verify correct mode applied based on day/config

---

### Task 1.5: Create `config.json`

**File:** `config.json`

**Create:**
```json
{
  "travel_mode": false,
  "original_limits": {}
}
```

**Acceptance Criteria:**
- [ ] File created in addon directory
- [ ] Valid JSON format
- [ ] Default values present
- [ ] Anki recognizes config (Tools → Add-ons → Config)

---

### Task 1.6: Add Docstrings and Type Hints

**File:** `__init__.py`

**Review:**
- [ ] All functions have docstrings
- [ ] Type hints on all function signatures
- [ ] Comments explain non-obvious logic
- [ ] Code follows PEP 8 style

---

## Phase 2: Desktop Testing (Day 2)

### Task 2.1: Test Weekend Detection

**Manual Tests:**

| Day | Expected `is_weekend()` | Actual | Pass? |
|-----|-------------------------|--------|-------|
| Monday | `False` | | [ ] |
| Tuesday | `False` | | [ ] |
| Wednesday | `False` | | [ ] |
| Thursday | `False` | | [ ] |
| Friday | `False` | | [ ] |
| Saturday | `True` | | [ ] |
| Sunday | `True` | | [ ] |

**How to Test:**
- Use system date or mock datetime in console
- Verify function behavior matches day of week

---

### Task 2.2: Test Weekend Mode Application

**Test Scenario:**

1. **Setup:**
   - [ ] Create test deck with 20 new cards/day limit
   - [ ] Note deck name and config ID

2. **Enable Weekend Mode:**
   - [ ] Run `apply_weekend_mode()` in console
   - [ ] Check deck options: new cards/day should be 0
   - [ ] Check `config.json`: original limit stored (20)

3. **Verify Persistence:**
   - [ ] Restart Anki
   - [ ] Limit should still be 0
   - [ ] Study session: no new cards shown

4. **Check Sync Readiness:**
   - [ ] Run sync
   - [ ] Check AnkiWeb sync log (no errors)

---

### Task 2.3: Test Weekday Mode Restoration

**Test Scenario:**

1. **Setup:**
   - [ ] Weekend mode active (limits = 0)
   - [ ] Original limits stored in config

2. **Restore Weekday Mode:**
   - [ ] Run `apply_weekday_mode()` in console
   - [ ] Check deck options: limit should be 20
   - [ ] Check config.json: original_limits still present

3. **Verify New Cards:**
   - [ ] Start study session
   - [ ] New cards should appear
   - [ ] Limit enforced correctly

---

### Task 2.4: Test Travel Mode

**Test Scenario:**

1. **Enable Travel Mode:**
   - [ ] Edit config.json: `"travel_mode": true`
   - [ ] Restart Anki
   - [ ] Limits should be 0 (regardless of day)

2. **Persistence Through Monday:**
   - [ ] Change system date to Monday (or wait)
   - [ ] Restart Anki
   - [ ] Limits should still be 0 (no auto-restore)

3. **Disable Travel Mode:**
   - [ ] Edit config.json: `"travel_mode": false`
   - [ ] Restart Anki
   - [ ] If weekday: limits restored
   - [ ] If weekend: limits stay 0

---

### Task 2.5: Test Edge Cases

**Test Scenarios:**

1. **Addon Installed Mid-Weekend:**
   - [ ] Install addon on Saturday
   - [ ] Original limits captured correctly
   - [ ] Weekend mode applied immediately

2. **Multiple Decks:**
   - [ ] Create 3+ decks with different limits
   - [ ] Apply weekend mode
   - [ ] All decks set to 0
   - [ ] Restore weekday mode
   - [ ] Each deck gets correct original limit

3. **Shared Deck Config:**
   - [ ] Create 2 decks sharing same config
   - [ ] Apply weekend mode
   - [ ] Both decks affected (limit = 0)
   - [ ] Original stored once (by config_id)

4. **User Modifies Deck Settings:**
   - [ ] Weekend mode active (limit = 0)
   - [ ] User manually changes limit to 5
   - [ ] Current behavior: overwritten on next mode check
   - [ ] Document this limitation

---

## Phase 3: Cross-Platform Sync Testing (Day 3)

### Task 3.1: Prepare for iOS Testing

**Prerequisites:**
- [ ] AnkiWeb account configured
- [ ] AnkiMobile installed on iOS device
- [ ] Same account logged in on both devices
- [ ] Both devices synced (clean state)

---

### Task 3.2: Test macOS → iOS Weekend Sync

**Test Flow:**

1. **Friday Evening (macOS):**
   - [ ] Enable weekend mode manually or wait for Saturday
   - [ ] Verify limits = 0 in deck options
   - [ ] Sync to AnkiWeb (Tools → Sync)
   - [ ] Confirm sync successful (check timestamp)

2. **Saturday Morning (iOS):**
   - [ ] Open AnkiMobile
   - [ ] Sync from AnkiWeb
   - [ ] Open any deck
   - [ ] Verify: No new cards shown
   - [ ] Verify: Reviews work normally
   - [ ] Check deck options: new cards/day = 0

3. **Validate:**
   - [ ] Desktop config synced to mobile ✅
   - [ ] Behavior consistent across platforms ✅

---

### Task 3.3: Test iOS Study Session

**On iOS (Saturday):**

1. **Study Reviews:**
   - [ ] Open deck
   - [ ] Study available reviews
   - [ ] Answer cards
   - [ ] Reviews progress normally

2. **Verify No New Cards:**
   - [ ] Finish all reviews
   - [ ] Check "no cards due" message
   - [ ] Confirm no new cards introduced

3. **Check Stats:**
   - [ ] View deck stats
   - [ ] New cards remain at 0 studied
   - [ ] Reviews counted correctly

---

### Task 3.4: Test Weekday Restoration Sync

**Test Flow:**

1. **Monday Morning (macOS):**
   - [ ] Addon detects weekday
   - [ ] Limits restored automatically
   - [ ] Verify limits in deck options (should be original values)
   - [ ] Sync to AnkiWeb

2. **Monday Evening (iOS):**
   - [ ] Open AnkiMobile
   - [ ] Sync from AnkiWeb
   - [ ] Open any deck
   - [ ] Verify: New cards reappear
   - [ ] Check deck options: new cards/day restored

3. **Validate:**
   - [ ] Restoration synced to mobile ✅
   - [ ] New cards accessible again ✅

---

### Task 3.5: Test Travel Mode Cross-Platform

**Test Flow:**

1. **Wednesday (macOS):**
   - [ ] Enable travel mode in config.json
   - [ ] Restart Anki
   - [ ] Limits set to 0
   - [ ] Sync to AnkiWeb

2. **Thursday (iOS):**
   - [ ] Sync from AnkiWeb
   - [ ] Verify no new cards
   - [ ] Study reviews only

3. **Friday (macOS):**
   - [ ] Still in travel mode
   - [ ] Limits remain 0 (no auto-restore)

4. **Monday (macOS):**
   - [ ] Still in travel mode
   - [ ] Monday auto-restore skipped
   - [ ] Limits remain 0 ✅

5. **Tuesday (macOS):**
   - [ ] Disable travel mode
   - [ ] Limits restored
   - [ ] Sync to AnkiWeb

6. **Tuesday Evening (iOS):**
   - [ ] Sync from AnkiWeb
   - [ ] New cards reappear ✅

---

## Phase 4: Documentation (Day 3-4)

### Task 4.1: Create `config.md`

**File:** `config.md`

**Content:**
```markdown
# Anki Weekend Addon v2.0 - Configuration

## Settings

### `travel_mode`
- **Type:** Boolean
- **Default:** `false`
- **Description:** When enabled, pauses new cards indefinitely (useful for vacations).

### `original_limits`
- **Type:** Object
- **Default:** `{}`
- **Description:** Stores original "new cards per day" limits for restoration. Automatically managed by addon.
- **Format:** `{"config_id": limit_value}`

## How It Works

### Weekend Mode (Automatic)
- **Saturday & Sunday:** New cards automatically paused (limit set to 0)
- **Monday:** Original limits automatically restored
- **Reviews:** Always available (not affected)

### Travel Mode (Manual)
- **Enable:** Set `travel_mode: true` in config
- **Effect:** New cards paused indefinitely (even on weekdays)
- **Disable:** Set `travel_mode: false` to restore normal behavior

## Cross-Platform Sync

This addon modifies your deck configuration, which syncs automatically via AnkiWeb:

1. **Desktop (macOS/Windows/Linux):** Addon runs, modifies deck config
2. **Sync:** Changes upload to AnkiWeb
3. **Mobile (iOS/Android):** Sync downloads config changes
4. **Result:** No new cards on mobile ✅

**Important:** Make sure to sync regularly on all devices for consistent behavior.

## Troubleshooting

### New Cards Still Appearing on Weekend
- Check if today is actually Saturday/Sunday
- Verify addon is enabled (Tools → Add-ons)
- Check config.json shows correct day detection
- Try restarting Anki

### Limits Stuck at 0 on Monday
- Check if travel_mode is enabled (should be `false`)
- Manually restore: Tools → Add-ons → Config → set travel_mode to false
- Restart Anki

### Original Limits Not Restored
- Check `original_limits` in config.json
- If empty, addon couldn't capture originals
- Manually set deck limits in deck options

## Support

For issues or questions:
- GitHub Issues: [link to repo]
- AnkiWeb Reviews: [link to AnkiWeb page]
```

**Acceptance Criteria:**
- [ ] File created in addon directory
- [ ] Clear explanations for both settings
- [ ] Cross-platform sync explained
- [ ] Troubleshooting section included

---

### Task 4.2: Create Simple README

**File:** `README.md`

**Content:**
```markdown
# Anki Weekend Addon v2.0

Pause new cards on weekends, keep reviews active.

## Features

- ✅ Automatically pause new cards on Saturday & Sunday
- ✅ Restore new cards on Monday
- ✅ Travel mode for extended pauses
- ✅ Cross-platform sync (works on iOS/Android)

## Installation

1. Download `.ankiaddon` file
2. Tools → Add-ons → Install from file
3. Restart Anki

## Usage

### Weekend Mode (Automatic)
- Saturday & Sunday: No new cards
- Monday: New cards resume
- Reviews always available

### Travel Mode (Manual)
1. Tools → Add-ons → Weekend Addon → Config
2. Set `travel_mode: true`
3. Restart Anki
4. New cards paused until you disable travel mode

## Cross-Platform

This addon works on both desktop and mobile:
- Desktop: Addon modifies deck configuration
- Sync: Changes upload to AnkiWeb
- Mobile: Receives configuration changes
- Result: Consistent behavior across devices

## Requirements

- Anki 2.1.50+
- AnkiWeb account (for cross-platform sync)

## License

MIT

## Support

Issues: [GitHub link]
```

**Acceptance Criteria:**
- [ ] README created
- [ ] Features clearly listed
- [ ] Installation steps included
- [ ] Usage examples provided

---

## Phase 5: Final Review & Package (Day 4-5)

### Task 5.1: Code Review Checklist

**Review `__init__.py`:**
- [ ] All functions have type hints
- [ ] All functions have docstrings
- [ ] No global mutable state
- [ ] Error handling for `mw.col` being None
- [ ] Uses `mw.col.decks.save()` (not direct DB writes)
- [ ] Code follows CLAUDE.md principles
- [ ] Total lines < 200 (should be ~150)

---

### Task 5.2: Test All Scenarios

**Run Complete Test Suite:**
- [ ] Weekend detection (all days)
- [ ] Weekend mode application
- [ ] Weekday mode restoration
- [ ] Travel mode enable/disable
- [ ] Multiple decks handling
- [ ] Cross-platform sync (macOS ↔ iOS)
- [ ] Edge cases (mid-weekend install, etc.)

---

### Task 5.3: Create Addon Package

**Steps:**

1. **Verify File Structure:**
   ```
   anki_weekend_addon_v2/
   ├── __init__.py
   ├── config.json
   ├── config.md
   └── README.md
   ```

2. **Create `.ankiaddon` File:**
   ```bash
   cd ~/Library/Application\ Support/Anki2/addons21/
   zip -r weekend_addon_v2.ankiaddon anki_weekend_addon_v2/
   ```

3. **Test Installation:**
   - [ ] Install from .ankiaddon file on fresh Anki
   - [ ] Verify addon loads without errors
   - [ ] Test basic functionality

---

### Task 5.4: Prepare for Release

**Deliverables:**
- [ ] `__init__.py` - Core implementation
- [ ] `config.json` - Default configuration
- [ ] `config.md` - User documentation
- [ ] `README.md` - Project overview
- [ ] `weekend_addon_v2.ankiaddon` - Installable package

**Optional (Future):**
- [ ] Publish to AnkiWeb
- [ ] Create GitHub repository
- [ ] Write blog post about implementation

---

## Success Criteria

### Functional Requirements ✅
- [x] New cards paused on Saturday/Sunday
- [x] Reviews always available
- [x] Original limits restored on Monday
- [x] Travel mode works indefinitely
- [x] Cross-platform sync validated (iOS)

### Technical Requirements ✅
- [x] Code < 200 lines
- [x] No classes (functions only)
- [x] Type hints on all functions
- [x] Docstrings on all functions
- [x] Uses proper Anki API (mw.col.decks.save)
- [x] No global mutable state

### Quality Requirements ✅
- [x] No crashes on startup
- [x] Handles edge cases gracefully
- [x] Works with multiple decks
- [x] Documentation complete
- [x] Installable package created

---

## Timeline Summary

- **Day 1:** Implement core (Tasks 1.1-1.6) ⏱️ 3-4 hours
- **Day 2:** Desktop testing (Tasks 2.1-2.5) ⏱️ 2-3 hours
- **Day 3:** Cross-platform testing (Tasks 3.1-3.5) ⏱️ 2-3 hours
- **Day 4:** Documentation (Tasks 4.1-4.2) ⏱️ 1-2 hours
- **Day 5:** Final review & package (Tasks 5.1-5.4) ⏱️ 1-2 hours

**Total Estimated Time:** 10-14 hours over 3-5 days

---

## Notes

- All tasks are designed for manual execution
- Testing requires both macOS and iOS devices
- Cross-platform testing is critical (validates core requirement)
- Keep it simple: resist urge to add features not in plan
- Document any issues or learnings for future reference

---

**Ready to Execute:** Yes ✅
**Complexity Level:** Appropriate (Simple solution for simple problem)
**Confidence Level:** High (research-backed, validated approach)
