# Anki Framework API Research Findings
## Weekend Addon v2.0 Implementation Guide

**Date:** 2025-01-11
**Anki Target Version:** 25.x
**Research Scope:** Deck configuration modification approach for pausing new cards on weekends

---

## Table of Contents

1. [Deck Configuration API](#1-deck-configuration-api)
2. [Collection API](#2-collection-api)
3. [Addon Configuration](#3-addon-configuration)
4. [Hooks & Lifecycle](#4-hooks--lifecycle)
5. [Version Compatibility](#5-version-compatibility)
6. [Implementation Approaches](#6-implementation-approaches)
7. [Code Examples](#7-code-examples)
8. [Common Pitfalls](#8-common-pitfalls)
9. [References](#9-references)

---

## 1. Deck Configuration API

### 1.1 Getting Deck Configuration

**Method:** `col.decks.get_config(config_id: DeckConfigId) -> DeckConfigDict | None`

Gets a deck configuration by its ID. Returns `None` if not found.

```python
from aqt import mw

# Get deck by ID first
deck = mw.col.decks.get_legacy(deck_id)
if deck:
    config_id = deck['conf']
    config = mw.col.decks.get_config(config_id)
```

### 1.2 Modifying New Cards Per Day

**Configuration Structure:**

```python
config = {
    "new": {
        "perDay": 20,  # Number of new cards per day
        # ... other new card settings
    },
    "rev": {
        "perDay": 100,  # Number of reviews per day
        # ... other review settings
    },
    # ... other config options
}
```

**Example Modification:**

```python
config = mw.col.decks.get_config(config_id)
if config:
    # Store original value before modifying
    original_limit = config["new"]["perDay"]

    # Set to 0 to disable new cards
    config["new"]["perDay"] = 0

    # Save changes
    mw.col.decks.save(config)
```

### 1.3 Saving Configuration

**Method:** `col.decks.save(deck_or_config: DeckDict | DeckConfigDict | None = None) -> None`

Saves changes to a deck or deck configuration. Automatically distinguishes between deck and config objects based on the presence of the `"maxTaken"` field.

**Alternative Method:** `col.decks.update_config(conf: DeckConfigDict, preserve_usn: bool = False) -> None`

**CRITICAL:** Using these methods automatically marks items as requiring a sync. This ensures changes propagate to AnkiWeb and other devices.

```python
# Save using save() method
mw.col.decks.save(config)

# OR using update_config()
mw.col.decks.update_config(config)
```

### 1.4 Important Notes

- **Always use API methods** (not direct database access) to ensure sync compatibility
- Changes made via `save()` or `update_config()` are automatically marked for sync
- Never modify the database directly using `execute()` - those changes won't sync
- The `preserve_usn` parameter in `update_config()` is currently ignored

---

## 2. Collection API

### 2.1 Accessing the Collection

**Main Window Collection:** `mw.col`

The currently-open Collection is accessible via `mw.col`, where `mw` is the main window.

**Availability:** Collection is only available after profile loads. Use appropriate hooks (see Section 4).

### 2.2 Iterating Through All Decks

**Method:** `col.decks.all_names_and_ids(skip_empty_default: bool = False, include_filtered: bool = True) -> Sequence[DeckNameId]`

Returns a sorted sequence of deck names and IDs.

```python
from aqt import mw

# Iterate through all decks
for deck_info in mw.col.decks.all_names_and_ids():
    deck_id = deck_info.id
    deck_name = deck_info.name

    # Get full deck object if needed
    deck = mw.col.decks.get_legacy(deck_id)
    if deck:
        config_id = deck['conf']
        # ... work with deck config
```

**Parameters:**
- `skip_empty_default`: Skip the default deck if empty
- `include_filtered`: Include filtered (dynamic) decks

### 2.3 Getting Specific Decks

**By ID:** `col.decks.get_legacy(did: DeckId) -> DeckDict | None`

```python
deck = mw.col.decks.get_legacy(deck_id)
if deck:
    deck_name = deck['name']
    config_id = deck['conf']  # Configuration ID for this deck
```

**By Name:** `col.decks.id_for_name(name: str) -> DeckId | None`

```python
deck_id = mw.col.decks.id_for_name("My Deck")
if deck_id:
    deck = mw.col.decks.get_legacy(deck_id)
```

### 2.4 Type Aliases

- `DeckId`: Integer representing a deck identifier
- `DeckConfigId`: Integer representing a configuration identifier
- `DeckDict`: Dictionary containing deck properties
- `DeckConfigDict`: Dictionary containing configuration options
- `DeckNameId`: Object with `id` and `name` attributes

---

## 3. Addon Configuration

### 3.1 Configuration Files

**config.json** - Default configuration values:

```json
{
    "weekend_mode_enabled": true,
    "travel_mode_enabled": false,
    "language": "auto",
    "stored_limits": {}
}
```

**config.md** - User documentation (markdown format)

Documents all configuration options for users.

### 3.2 Reading Configuration

**Method:** `mw.addonManager.getConfig(__name__)`

```python
from aqt import mw

config = mw.addonManager.getConfig(__name__)
if config:
    weekend_mode = config.get('weekend_mode_enabled', True)
    stored_limits = config.get('stored_limits', {})
```

**Important:**
- Returns `None` if no `config.json` exists
- Falls back to `config.json` defaults if user hasn't customized
- User customizations stored in `meta.json`
- Avoid key names starting with underscores (reserved for Anki)

### 3.3 Writing Configuration

**Method:** `mw.addonManager.writeConfig(__name__, config)`

```python
from aqt import mw

config = mw.addonManager.getConfig(__name__)
config['stored_limits']['12345'] = 20  # Store original limit for deck ID 12345
mw.addonManager.writeConfig(__name__, config)
```

**Important:**
- Changes are saved to `meta.json`
- Changing `config.json` won't update previously customized user values
- Users must click "restore defaults" to pick up `config.json` changes

### 3.4 Custom Configuration UI

**Method:** `mw.addonManager.setConfigAction(__name__, callback)`

```python
from aqt import mw
from aqt.qt import QDialog

def show_config_dialog():
    dialog = QDialog(mw)
    # ... setup dialog
    dialog.exec()

mw.addonManager.setConfigAction(__name__, show_config_dialog)
```

### 3.5 User Files Folder

For complex data, use a `user_files` folder in your addon's root directory. This folder is preserved during addon upgrades.

---

## 4. Hooks & Lifecycle

### 4.1 Hook System Overview

Anki provides two types of hooks:

1. **Regular hooks:** Functions without return values, executed for side effects
2. **Filters:** Functions that return their first argument (potentially modified)

**Modern Style (Anki 2.1.20+):**

```python
from aqt import gui_hooks

def my_function(arg):
    print("Hook fired!")

gui_hooks.profile_did_open.append(my_function)

# To remove:
gui_hooks.profile_did_open.remove(my_function)
```

**Legacy Style:**

```python
from anki.hooks import addHook

def my_function():
    print("Hook fired!")

addHook("profileLoaded", my_function)
```

### 4.2 Critical Lifecycle Hooks

#### profile_did_open

**Signature:** `Hook(name="profile_did_open", legacy_hook="profileLoaded")`

**When it fires:** Executed whenever a user profile has been opened

**Use case:** Initialize functionality when profile loads

**Important:** Fires on profile switches, not just once per session

```python
from aqt import gui_hooks

def on_profile_open():
    print("Profile opened!")
    # Initialize addon functionality

gui_hooks.profile_did_open.append(on_profile_open)
```

#### collection_did_load

**Signature:** `Hook(name="collection_did_load", args=["col: anki.collection.Collection"], legacy_hook="colLoading")`

**When it fires:** After the collection finishes loading and becomes accessible

**Use case:** Access collection data once it's fully initialized

```python
from aqt import gui_hooks

def on_collection_load(col):
    print("Collection loaded!")
    # Access col.decks, etc.

gui_hooks.collection_did_load.append(on_collection_load)
```

#### main_window_did_init

**Signature:** `Hook(name="main_window_did_init")`

**When it fires:** Executed after the main window is fully initialized

**Use case:** Single-shot initialization that should run once per session

**Important:** Unlike `profile_did_open`, this doesn't repeat on profile switches

```python
from aqt import gui_hooks

def on_main_window_init():
    print("Main window initialized!")
    # One-time setup

gui_hooks.main_window_did_init.append(on_main_window_init)
```

### 4.3 Initialization Sequence

Typical lifecycle order:

1. `main_window_did_init` - Main window ready
2. `profile_did_open` - Profile loaded
3. `collection_did_load` - Collection accessible

### 4.4 Hook Discovery

View all available hooks:

- IDE type completion (with proper setup)
- [pylib/tools/genhooks.py](https://github.com/ankitects/anki/blob/main/pylib/tools/genhooks.py) - Backend hooks
- [qt/tools/genhooks_gui.py](https://github.com/ankitects/anki/blob/main/qt/tools/genhooks_gui.py) - GUI hooks

### 4.5 Timer Mechanisms

For periodic checks (e.g., checking for midnight/date change):

```python
from aqt.qt import QTimer
from aqt import mw

def check_date_change():
    # Your logic here
    pass

# Create timer - IMPORTANT: Requires parent argument in Anki 2.1.50+
timer = QTimer(mw)
timer.timeout.connect(check_date_change)
timer.start(60000)  # Check every 60 seconds (milliseconds)

# To stop:
timer.stop()
```

**CRITICAL (Anki 2.1.50+):** `QTimer()` now requires an explicit parent argument to prevent memory leaks.

**Alternative using mw.progress.timer():**

```python
# Note: mw.progress.timer() also requires parent in 2.1.50+
# This is less commonly used for addon timers
```

---

## 5. Version Compatibility

### 5.1 Anki 2.1.50 Breaking Changes

**PyQt5 to PyQt6 Migration:**

```python
# OLD (PyQt5)
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt

# NEW (PyQt6)
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt
```

**Compatibility shims provided but temporary - should update to PyQt6**

**Enum Qualification:**

```python
# OLD
Qt.AlignCenter

# NEW (PyQt6)
Qt.AlignmentFlag.AlignCenter
```

**Timer Parent Requirement:**

```python
# OLD (works in older versions)
timer = QTimer()

# NEW (required in 2.1.50+)
timer = QTimer(mw)
```

**Minimum Python Version:** 3.9+

### 5.2 Anki 25.x Changes

**AnkiWebView Security (25.02.1):**

New security precautions affect webviews. If using `AnkiWebView`, must specify allowed enum:

```python
# Webviews default to AnkiWebViewKind.DEFAULT which isn't allowed
# Use whitelisted AnkiWebViewKind when initializing
```

**Addon Shortcuts Override (2.1.64+):**

Addon shortcuts now override Anki defaults (priority change).

### 5.3 V3 Scheduler Compatibility

**CRITICAL LIMITATION:**

The v3 scheduler is a ground-up rewrite. **Monkey patching scheduler methods no longer works.**

```python
# THIS NO LONGER WORKS with v3 scheduler:
from anki.hooks import wrap
Scheduler._fuzzedIvl = wrap(Scheduler._fuzzedIvl, myFunc, "around")
```

**Alternative Approach:**

V3 scheduler allows custom JavaScript scheduling code in deck options, but this doesn't help with pausing new cards approach.

**For Weekend Addon:** The deck configuration modification approach (not scheduler patching) is **compatible with v3 scheduler**.

### 5.4 Version Check Example

```python
from anki import version as anki_version

def check_version():
    # Version string like "2.1.54" or "25.01.2"
    version = anki_version

    # Parse version for compatibility checks
    parts = version.split('.')
    major = int(parts[0])

    if major >= 25:
        # Handle Anki 25.x specifics
        pass
    elif major == 2:
        minor = int(parts[1])
        if minor >= 50:
            # Handle 2.1.50+ specifics
            pass
```

---

## 6. Implementation Approaches

### 6.1 Deck Configuration Modification (RECOMMENDED)

**Approach:** Modify `config["new"]["perDay"]` to pause/resume new cards.

**Pros:**
- Clean and non-invasive
- Works with v3 scheduler
- Syncs automatically via AnkiWeb
- No monkey patching required
- Easy to restore original state

**Cons:**
- Need to store original limits
- Must iterate through all decks
- Changes visible to user in deck options UI

**Best for:** Weekend Addon v2.0 (our use case)

### 6.2 Scheduler Monkey Patching (NOT RECOMMENDED)

**Approach:** Wrap scheduler methods like `_getNewCard` to filter cards.

**Pros:**
- Transparent to user
- Fine-grained control

**Cons:**
- **Does not work with v3 scheduler**
- Invasive and fragile
- Can conflict with other addons
- Harder to maintain

**Example (v2 scheduler only):**

```python
from anki.hooks import wrap
from anki.sched import Scheduler

def my_get_new_card(self, _old):
    # Custom logic
    if is_weekend():
        return None  # No new cards
    return _old(self)

Scheduler._getNewCard = wrap(Scheduler._getNewCard, my_get_new_card, "around")
```

**Verdict:** Avoid this approach for new addons.

### 6.3 Card Rescheduling (ALTERNATIVE)

**Approach:** Reschedule cards away from weekends (like AnkiWeekendsAndHolidays addon).

**Pros:**
- Works with all schedulers
- More sophisticated (moves reviews too)

**Cons:**
- Complex implementation
- Modifies card intervals
- Different use case (moves all cards, not just new)

**Verdict:** Not suitable for our simple "pause new cards" use case.

---

## 7. Code Examples

### 7.1 Complete Weekend Pause Implementation

```python
from aqt import mw, gui_hooks
from datetime import datetime
from typing import Dict

class WeekendManager:
    """Manages pausing new cards on weekends."""

    WEEKEND_DAYS = [5, 6]  # Saturday=5, Sunday=6 (Python weekday())

    def __init__(self):
        self.original_limits: Dict[int, int] = {}
        self._load_stored_limits()

    def _load_stored_limits(self):
        """Load previously stored limits from addon config."""
        config = mw.addonManager.getConfig(__name__)
        if config:
            # Convert string keys back to int
            stored = config.get('stored_limits', {})
            self.original_limits = {int(k): v for k, v in stored.items()}

    def _save_stored_limits(self):
        """Save current limits to addon config."""
        config = mw.addonManager.getConfig(__name__)
        if config:
            # Convert int keys to string for JSON
            config['stored_limits'] = {str(k): v for k, v in self.original_limits.items()}
            mw.addonManager.writeConfig(__name__, config)

    def is_weekend(self) -> bool:
        """Check if today is a weekend."""
        today = datetime.now().weekday()
        return today in self.WEEKEND_DAYS

    def pause_new_cards(self):
        """Set new cards per day to 0 for all decks."""
        if not mw.col:
            return

        for deck_info in mw.col.decks.all_names_and_ids():
            deck = mw.col.decks.get_legacy(deck_info.id)
            if not deck:
                continue

            config_id = deck['conf']
            config = mw.col.decks.get_config(config_id)
            if not config:
                continue

            # Store original limit if not already stored
            if config_id not in self.original_limits:
                self.original_limits[config_id] = config["new"]["perDay"]

            # Pause new cards
            if config["new"]["perDay"] != 0:
                config["new"]["perDay"] = 0
                mw.col.decks.save(config)

        self._save_stored_limits()

    def resume_new_cards(self):
        """Restore original new cards per day limits."""
        if not mw.col:
            return

        for config_id, original_limit in self.original_limits.items():
            config = mw.col.decks.get_config(config_id)
            if config:
                config["new"]["perDay"] = original_limit
                mw.col.decks.save(config)

        # Don't clear original_limits - keep them for next weekend

    def check_and_update(self):
        """Check if we need to pause or resume based on current day."""
        if self.is_weekend():
            self.pause_new_cards()
        else:
            self.resume_new_cards()


# Initialize
weekend_manager = WeekendManager()

# Hook into profile opening
def on_profile_open():
    weekend_manager.check_and_update()

gui_hooks.profile_did_open.append(on_profile_open)

# Optional: Periodic check for midnight transitions
from aqt.qt import QTimer

def setup_midnight_check():
    timer = QTimer(mw)
    timer.timeout.connect(weekend_manager.check_and_update)
    timer.start(3600000)  # Check every hour

gui_hooks.main_window_did_init.append(setup_midnight_check)
```

### 7.2 Travel Mode (Indefinite Pause)

```python
def enable_travel_mode():
    """Disable new cards indefinitely."""
    config = mw.addonManager.getConfig(__name__)
    if config:
        config['travel_mode_enabled'] = True
        mw.addonManager.writeConfig(__name__, config)

    weekend_manager.pause_new_cards()

def disable_travel_mode():
    """Re-enable new cards."""
    config = mw.addonManager.getConfig(__name__)
    if config:
        config['travel_mode_enabled'] = False
        mw.addonManager.writeConfig(__name__, config)

    # Only resume if not weekend
    if not weekend_manager.is_weekend():
        weekend_manager.resume_new_cards()

def check_and_update_with_travel_mode():
    """Check both travel mode and weekend."""
    config = mw.addonManager.getConfig(__name__)
    if config and config.get('travel_mode_enabled', False):
        weekend_manager.pause_new_cards()
    else:
        weekend_manager.check_and_update()
```

### 7.3 Language Detection

```python
import locale

def detect_language() -> str:
    """
    Detect system language.
    Returns 'pt-BR' or 'en' (fallback).
    """
    try:
        lang, _ = locale.getdefaultlocale()
        if lang and lang.startswith('pt'):
            return 'pt-BR'
    except:
        pass

    return 'en'  # Fallback

def get_translation(key: str) -> str:
    """Get translated string."""
    config = mw.addonManager.getConfig(__name__)
    language = config.get('language', 'auto')

    if language == 'auto':
        language = detect_language()

    translations = {
        'pt-BR': {
            'weekend_mode': 'Modo Fim de Semana',
            'travel_mode': 'Modo Viagem',
        },
        'en': {
            'weekend_mode': 'Weekend Mode',
            'travel_mode': 'Travel Mode',
        }
    }

    return translations.get(language, translations['en']).get(key, key)
```

---

## 8. Common Pitfalls

### 8.1 Don't Modify Database Directly

**DON'T:**
```python
mw.col.db.execute("UPDATE decks SET conf = ?", ...)
```

**DO:**
```python
mw.col.decks.save(config)
```

**Why:** Direct database modifications don't trigger sync and can cause data corruption.

### 8.2 Check Collection Availability

**DON'T:**
```python
def my_func():
    decks = mw.col.decks.all_names_and_ids()  # May crash if col not loaded
```

**DO:**
```python
def my_func():
    if not mw.col:
        return
    decks = mw.col.decks.all_names_and_ids()
```

### 8.3 Store Config IDs, Not Deck IDs

Deck configurations are shared among multiple decks. Store limits by `config_id`, not `deck_id`:

**DON'T:**
```python
self.original_limits[deck_info.id] = config["new"]["perDay"]
```

**DO:**
```python
self.original_limits[config_id] = config["new"]["perDay"]
```

### 8.4 Handle Profile Switches

`profile_did_open` fires on profile switches. Ensure your addon handles multiple profiles:

```python
def on_profile_open():
    # Reload stored limits for this profile
    weekend_manager._load_stored_limits()
    weekend_manager.check_and_update()
```

### 8.5 JSON Key Restrictions

Addon config keys cannot start with underscores:

**DON'T:**
```json
{
    "_internal_state": {}
}
```

**DO:**
```json
{
    "internal_state": {}
}
```

### 8.6 Timer Parent Requirement (2.1.50+)

**DON'T:**
```python
timer = QTimer()  # Memory leak in 2.1.50+
```

**DO:**
```python
timer = QTimer(mw)  # Proper parent
```

---

## 9. References

### 9.1 Official Documentation

- [Anki Add-ons Documentation](https://addon-docs.ankiweb.net/)
- [The 'anki' Module](https://addon-docs.ankiweb.net/the-anki-module.html)
- [Hooks and Filters](https://addon-docs.ankiweb.net/hooks-and-filters.html)
- [Add-on Config](https://addon-docs.ankiweb.net/addon-config.html)
- [Anki Manual](https://docs.ankiweb.net/)
- [Deck Options Documentation](https://docs.ankiweb.net/deck-options.html)

### 9.2 Source Code References

- [Anki GitHub Repository](https://github.com/ankitects/anki)
- [GUI Hooks Definition](https://github.com/ankitects/anki/blob/main/qt/tools/genhooks_gui.py)
- [Backend Hooks Definition](https://github.com/ankitects/anki/blob/main/pylib/tools/genhooks.py)
- [Deck Management Code](https://github.com/ankitects/anki/blob/main/pylib/anki/decks.py)

### 9.3 Similar Addons (Study Material)

- [AnkiWeekendsAndHolidays](https://github.com/vasarmilan/AnkiWeekendsAndHolidays) - Card rescheduling approach
- [Free Weekend](https://github.com/cjdduarte/Free_Weekend) - Scheduler fuzzing approach (v2 only)
- [Anki Official Add-ons](https://github.com/ankitects/anki-addons) - Official examples

### 9.4 Version Changelogs

- [Changes 2.1.50-59](https://changes.ankiweb.net/changes/2.1.50-59.html)
- [Changes 2.1.60-66](https://changes.ankiweb.net/changes/2.1.60-66.html)
- [All Releases](https://github.com/ankitects/anki/releases)

### 9.5 Community Resources

- [Anki Forums - Add-ons](https://forums.ankiweb.net/c/add-ons/11)
- [Anki Forums - Development](https://forums.ankiweb.net/c/development/8)
- [r/Anki Subreddit](https://reddit.com/r/Anki)

---

## Summary & Recommendations

### Recommended Implementation Approach

**For Weekend Addon v2.0, use the Deck Configuration Modification approach:**

1. Store original `config["new"]["perDay"]` values in addon config
2. On weekends: Set to 0
3. On weekdays: Restore original values
4. Use `profile_did_open` hook for initialization
5. Optional: Use QTimer for midnight checks

**Why this approach:**
- Clean and simple
- Works with v3 scheduler
- Auto-syncs via AnkiWeb
- Easy to understand and maintain
- Non-invasive to Anki internals

### Version Support Strategy

**Target:** Anki 2.1.50+ and Anki 25.x

**Key requirements:**
- Use PyQt6 imports
- Provide QTimer parent argument
- Use modern gui_hooks
- Test with both v2 and v3 schedulers

### Critical Success Factors

1. **Always use API methods** for deck config (not direct DB access)
2. **Store limits by config_id** (not deck_id)
3. **Check `mw.col` availability** before accessing collection
4. **Handle profile switches** properly
5. **Test sync behavior** thoroughly

---

**End of Research Findings**

**Next Steps:**
1. Review this document with implementation team
2. Create detailed architecture plan based on findings
3. Begin implementation using recommended approach
4. Set up testing environment with v2 and v3 schedulers
