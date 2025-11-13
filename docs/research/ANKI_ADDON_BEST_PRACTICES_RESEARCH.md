# Comprehensive Best Practices for Anki Addon Development
## Research Report: Focus on Simplicity and Maintainability

**Date**: 2025-11-11
**Target**: Anki 25.x
**Purpose**: Rewriting Weekend Card Pause addon from scratch with emphasis on avoiding complexity

---

## Executive Summary

### Key Takeaways

1. **Use the Modern Hook System**: Anki 2.1.20+ provides new-style hooks with better type safety and error checking
2. **Keep It Simple**: Favor functions over classes unless you need state management
3. **Avoid Scheduler Monkey-Patching**: V3 scheduler (default in Anki 23.10+) doesn't support selective code replacement
4. **Use Official Configuration API**: Built-in config.json and meta.json system handles user preferences
5. **Don't Modify Database Schema**: Use collection API methods instead of direct database access
6. **Single Responsibility**: Each addon should do one thing well
7. **Minimal File Structure**: Small addons can use just `__init__.py` and `config.json`

### Critical Architecture Decision for Your Addon

**DO NOT** try to modify the scheduler's card-gathering logic. The v3 scheduler is a ground-up rewrite that prevents monkey-patching.

**CROSS-PLATFORM REQUIREMENT**: Since this addon must work on both macOS (desktop) and iOS (AnkiMobile), the implementation MUST use data that syncs via AnkiWeb.

**RECOMMENDED APPROACH**: Temporarily modify deck configuration (new card limit = 0) on weekends. This is the ONLY approach that works cross-platform:
- ✅ Deck configuration syncs via AnkiWeb
- ✅ Works on desktop AND mobile
- ✅ Non-invasive to scheduler
- ❌ Hooks DON'T sync (desktop-only behavior)
- ❌ Rescheduling is too invasive to SRS algorithm

See `research_cross_platform_behavior.md` for detailed analysis.

---

## 1. Anki Integration Best Practices

### 1.1 Modern Hook System (Anki 2.1.20+)

**Use new-style hooks for better code completion and error checking:**

```python
from aqt import gui_hooks

def on_question_shown(card):
    print("Question shown, card question is:", card.q())

# Register hook
gui_hooks.reviewer_did_show_question.append(on_question_shown)

# Unregister when needed
gui_hooks.reviewer_did_show_question.remove(on_question_shown)
```

**Key Hooks for Your Weekend Addon:**
- `scheduler_will_get_queued_cards()` - Not yet available, check current docs
- `reviewer_will_show_question()` - Intercept before showing question
- `reviewer_will_answer_card()` - Intercept before answering
- `webview_will_set_content()` - Modify displayed content

**Critical Rule**: Never modify a hook from within its own execution - this breaks things.

**Hook Locations**:
- Backend hooks: `pylib/tools/genhooks.py`
- GUI hooks: `qt/tools/genhooks_gui.py`

### 1.2 Collection Access Patterns

**Access the current collection:**

```python
from aqt import mw

config = mw.addonManager.getConfig(__name__)
collection = mw.col  # Current loaded collection
```

**Threading Considerations:**

```python
# BAD - Freezes UI
result = mw.col.find_cards("deck:MyDeck")

# GOOD - Run in background thread for long operations
from aqt.operations import QueryOp

def search_cards():
    return mw.col.find_cards("deck:MyDeck")

def on_success(result):
    print(f"Found {len(result)} cards")

QueryOp(parent=mw, op=search_cards, success=on_success).run_in_background()
```

**Important Warnings:**
- Collection operations must NOT run during addon initialization (no collection loaded yet)
- Never modify database schema directly
- Use collection API methods (update_note, update_card, etc.)
- Long operations should run in background threads

### 1.3 V3 Scheduler Constraints

**The v3 scheduler (default since Anki 23.10) has these characteristics:**

1. **No monkey-patching**: You cannot selectively replace scheduler code
2. **Ground-up rewrite**: Old scheduler hooks don't work
3. **Card gathering order**: Interday learning cards → review cards → new cards
4. **Mobile sync**: Changes must sync to AnkiMobile/AnkiDroid

**What This Means for Weekend Card Filtering:**

You CANNOT intercept the scheduler's card-gathering logic directly. Given the CROSS-PLATFORM requirement (macOS + iOS):
- **Option A (Hooks)**: ❌ Desktop-only, won't work on AnkiMobile
- **Option B (Deck Config)**: ✅ RECOMMENDED - Syncs to iOS via AnkiWeb
- **Option C (Rescheduling)**: ⚠️ Works cross-platform but too invasive to SRS

---

## 2. Architectural Recommendations

### 2.1 Recommended Approach for Weekend Card Pause

Based on research, here are three implementation strategies ranked by simplicity:

#### Strategy 1: Deck Configuration Modification (RECOMMENDED FOR CROSS-PLATFORM)

**Concept**: Temporarily set new card limit to 0 on weekends

**✅ CRITICAL ADVANTAGE**: This approach syncs via AnkiWeb, making it work on iOS/Android!

```python
from aqt import gui_hooks, mw
from datetime import datetime

def is_weekend():
    return datetime.now().weekday() in [5, 6]  # Saturday=5, Sunday=6

def adjust_new_card_limit():
    if not mw.col:
        return

    config = mw.addonManager.getConfig(__name__)
    if not config.get('enabled', True):
        return

    # Get all deck configs
    for deck_id in mw.col.decks.all_ids():
        deck = mw.col.decks.get(deck_id)
        deck_config = mw.col.decks.config_dict_for_deck_id(deck_id)

        if is_weekend() and not config.get('travel_mode', False):
            # Save original limit and set to 0
            deck_config['new']['perDay'] = 0
        elif not is_weekend() and not config.get('travel_mode', False):
            # Restore original limit (stored in addon config)
            original_limit = config.get('original_limits', {}).get(str(deck_id), 20)
            deck_config['new']['perDay'] = original_limit

        mw.col.decks.save(deck)

# Run on profile load
gui_hooks.profile_did_open.append(adjust_new_card_limit)
```

**Pros**:
- ✅ Simple, doesn't fight the scheduler
- ✅ Works with v3 scheduler
- ✅ **Syncs across devices via AnkiWeb (iOS/Android support!)**
- ✅ Minimal code
- ✅ Non-invasive to SRS algorithm

**Cons**:
- ⚠️ Modifies user's deck configuration (reversible)
- ⚠️ Must track original limits carefully
- ⚠️ Doesn't hide "new cards available" indicator in UI

**Cross-Platform Behavior**:
- User sets weekend mode on macOS Friday → syncs → iOS Saturday shows 0 new cards ✅
- User disables on Monday → syncs → iOS shows new cards again ✅

#### Strategy 2: Card Display Interception (MODERATE)

**Concept**: Skip new cards when they're about to be shown

```python
from aqt import gui_hooks, mw
from datetime import datetime

def should_skip_new_cards():
    config = mw.addonManager.getConfig(__name__)
    if config.get('travel_mode', False):
        return True
    if datetime.now().weekday() in [5, 6]:
        return True
    return False

def before_show_question(card):
    # Check if card is new (type 0 = new, 1 = learning, 2 = review)
    if card.type == 0 and should_skip_new_cards():
        # Skip this card and get next one
        mw.reviewer.nextCard()
        return False  # Prevent showing this card

gui_hooks.reviewer_will_show_question.append(before_show_question)
```

**Pros**:
- ✅ Doesn't modify deck configuration
- ✅ Clear separation of concerns
- ✅ Easy to toggle on/off

**Cons**:
- ❌ **DESKTOP-ONLY: Hooks don't run on iOS/Android**
- ⚠️ Still counts as "card seen" in some statistics
- ⚠️ May need additional hooks to handle edge cases

**Cross-Platform Behavior**:
- macOS Friday: New cards skipped ✅
- iOS Saturday: **New cards WILL appear** ❌ (addon not running)
- **NOT SUITABLE for users who study on mobile**

#### Strategy 3: Card Rescheduling (MOST FLEXIBLE)

**Concept**: Move new cards' due dates to skip weekends (like AnkiWeekendsAndHolidays)

**Pros**:
- ✅ **Syncs to mobile** (scheduling data syncs via AnkiWeb)
- ✅ Most control over card scheduling
- ✅ Works retroactively

**Cons**:
- ❌ **TOO INVASIVE**: Permanently modifies card scheduling
- ❌ Violates SRS principles (changes intervals)
- ❌ Most complex implementation
- ❌ Difficult to undo once applied
- ❌ Can conflict with other addons

**Cross-Platform Behavior**:
- Works on both desktop and mobile ✅
- But at the cost of compromising SRS algorithm ❌

**Recommendation**:
- **For cross-platform users (macOS + iOS)**: Use Strategy 1 (deck configuration)
- **For desktop-only users**: Strategy 2 (hooks) is simpler
- **Avoid Strategy 3** unless you absolutely need retroactive rescheduling

### 2.2 Modular Design Pattern

For small addons like yours, keep it minimal:

```
weekend_pause/
├── __init__.py          # Main entry point (all logic here for simple addon)
├── config.json          # Default configuration
├── config.md            # Configuration documentation
└── meta.json            # Generated by Anki (don't create manually)
```

**Only split into multiple files if you have distinct concerns:**

```
weekend_pause/
├── __init__.py          # Entry point, hook registration
├── config.json
├── config.md
├── weekend_logic.py     # Weekend detection, travel mode
├── scheduler_adapter.py # Anki scheduler interaction
└── i18n.py             # Translation strings
```

**Rule of Thumb**: If your addon is under 200 lines, use a single `__init__.py`.

---

## 3. Code Organization Patterns

### 3.1 Minimal File Structure

**__init__.py** (Main entry point):

```python
"""
Weekend Card Pause - Pause new cards on weekends
"""
from aqt import mw, gui_hooks
from datetime import datetime

# Module-level constants
WEEKEND_DAYS = [5, 6]  # Saturday, Sunday
ADDON_NAME = "Weekend Card Pause"

def is_weekend():
    """Check if today is a weekend."""
    return datetime.now().weekday() in WEEKEND_DAYS

def get_config():
    """Get addon configuration with defaults."""
    config = mw.addonManager.getConfig(__name__)
    if config is None:
        config = {
            'enabled': True,
            'travel_mode': False,
            'pause_on_weekends': True
        }
    return config

def should_pause_new_cards():
    """Determine if new cards should be paused."""
    config = get_config()

    if not config.get('enabled', True):
        return False

    if config.get('travel_mode', False):
        return True

    if config.get('pause_on_weekends', True) and is_weekend():
        return True

    return False

def on_reviewer_will_show_question(card):
    """Hook: Before showing a question."""
    # Type 0 = new card
    if card.type == 0 and should_pause_new_cards():
        mw.reviewer.nextCard()

# Register hooks
gui_hooks.reviewer_will_show_question.append(on_reviewer_will_show_question)
```

**config.json** (Default configuration):

```json
{
  "enabled": true,
  "pause_on_weekends": true,
  "travel_mode": false,
  "language": "auto"
}
```

**config.md** (User documentation):

```markdown
# Weekend Card Pause Configuration

- **enabled**: Enable/disable the addon
- **pause_on_weekends**: Pause new cards on Saturday and Sunday
- **travel_mode**: Pause new cards indefinitely (useful for vacations)
- **language**: UI language (auto, en, pt-br)
```

### 3.2 Configuration Management

**Reading configuration:**

```python
from aqt import mw

config = mw.addonManager.getConfig(__name__)
enabled = config.get('enabled', True)  # Use .get() with defaults
```

**Writing configuration:**

```python
config = mw.addonManager.getConfig(__name__)
config['travel_mode'] = True
mw.addonManager.writeConfig(__name__, config)
```

**Custom configuration dialog:**

```python
def show_config_dialog():
    # Your custom Qt dialog here
    pass

mw.addonManager.setConfigAction(__name__, show_config_dialog)
```

**Important Notes:**
- User edits are stored in `meta.json`, not `config.json`
- If `config.json` doesn't exist, `getConfig()` returns `None`
- Avoid underscore-prefixed keys (reserved for Anki)
- Changes to default values don't update customized configs

### 3.3 Internationalization (i18n)

**Simple approach for PT-BR/ENG:**

```python
from anki.lang import currentLang

TRANSLATIONS = {
    'en': {
        'weekend_mode': 'Weekend Mode',
        'travel_mode': 'Travel Mode',
        'new_cards_paused': 'New cards paused',
    },
    'pt-br': {
        'weekend_mode': 'Modo Fim de Semana',
        'travel_mode': 'Modo Viagem',
        'new_cards_paused': 'Novos cartões pausados',
    }
}

def tr(key):
    """Translate string with fallback to English."""
    lang = currentLang.lower()
    if lang.startswith('pt'):
        lang = 'pt-br'

    # Fallback to English
    translations = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    return translations.get(key, TRANSLATIONS['en'].get(key, key))

# Usage
print(tr('weekend_mode'))  # "Weekend Mode" or "Modo Fim de Semana"
```

**Alternative: Use Anki's Fluent system (more complex):**

```python
from aqt.utils import tr as anki_tr

# Requires adding strings to Anki's translation system
# More complex, only for large addons
```

---

## 4. Simplicity Guidelines

### 4.1 YAGNI Principle (You Aren't Gonna Need It)

**What it means:**
- Only implement features you ACTUALLY need now
- Don't build for hypothetical future requirements
- Remove speculation from design

**For your addon:**

✅ **IMPLEMENT**:
- Weekend detection (Saturday/Sunday)
- Travel mode toggle
- Skip new cards only (not reviews)
- Basic configuration

❌ **DON'T IMPLEMENT** (unless explicitly needed):
- Custom weekend days (Monday-Tuesday, etc.)
- Timezone handling
- Per-deck configuration
- Scheduling history
- Statistics tracking
- Undo functionality
- Integration with other addons

### 4.2 Functions vs Classes

**Use functions when:**
- You're performing actions without maintaining state
- The code is procedural/event-driven
- Simpler is better (which is most of the time)

**Use classes only when:**
- You need to maintain internal state across multiple operations
- You have multiple related functions that share data
- You're modeling a real-world concept

**For your addon (recommended):**

```python
# GOOD - Simple functions
def is_weekend():
    return datetime.now().weekday() in [5, 6]

def should_pause_new_cards():
    config = get_config()
    return config.get('travel_mode') or (is_weekend() and config.get('pause_on_weekends'))

# BAD - Unnecessary class
class WeekendChecker:
    def __init__(self, config):
        self.config = config

    def is_weekend(self):
        return datetime.now().weekday() in [5, 6]

    def should_pause(self):
        return self.config.get('travel_mode') or (self.is_weekend() and self.config.get('pause_on_weekends'))
```

**Exception**: If you need to track state:

```python
# Justified class usage - maintains state
class CardPauseTracker:
    def __init__(self):
        self.paused_count = 0
        self.last_check = None

    def increment(self):
        self.paused_count += 1

    def reset(self):
        self.paused_count = 0
```

### 4.3 Composition Over Inheritance

**Avoid complex inheritance hierarchies:**

```python
# BAD - Complex inheritance
class BaseSchedulerModifier:
    def modify(self):
        pass

class WeekendModifier(BaseSchedulerModifier):
    def modify(self):
        # Complex override logic
        pass

# GOOD - Simple composition
def modify_for_weekend(card):
    if is_weekend():
        return skip_new_card(card)
    return show_card(card)
```

**Use composition when combining behavior:**

```python
# Multiple independent behaviors
def apply_weekend_filter(card):
    if is_weekend():
        return None
    return card

def apply_travel_filter(card):
    config = get_config()
    if config.get('travel_mode'):
        return None
    return card

def apply_all_filters(card):
    # Compose filters
    card = apply_weekend_filter(card)
    if card:
        card = apply_travel_filter(card)
    return card
```

### 4.4 Avoiding Over-Abstraction

**Don't create abstractions prematurely:**

```python
# BAD - Premature abstraction
class DateChecker:
    def check(self, date, conditions):
        pass

class WeekendCondition:
    def matches(self, date):
        pass

class ConfigProvider:
    def get_value(self, key):
        pass

# GOOD - Direct and simple
def is_weekend():
    return datetime.now().weekday() in [5, 6]

config = mw.addonManager.getConfig(__name__)
```

**Abstraction checklist:**
- ✅ Do I have 3+ similar pieces of code?
- ✅ Will this abstraction make code EASIER to understand?
- ✅ Am I abstracting over actual duplication, not hypothetical?
- ❌ Am I creating abstraction "just in case"?

---

## 5. Testing Strategy

### 5.1 Testing Anki Addons

**Recommended tool: pytest-anki**

```bash
pip install pytest pytest-anki pytest-mock
```

**Basic test structure:**

```python
# test_weekend_pause.py
import pytest
from datetime import datetime

def test_is_weekend_saturday(monkeypatch):
    # Mock datetime to return Saturday
    class MockDateTime:
        @staticmethod
        def now():
            class FakeNow:
                def weekday(self):
                    return 5  # Saturday
            return FakeNow()

    monkeypatch.setattr('your_addon.datetime', MockDateTime)

    from your_addon import is_weekend
    assert is_weekend() == True

def test_is_weekend_monday(monkeypatch):
    class MockDateTime:
        @staticmethod
        def now():
            class FakeNow:
                def weekday(self):
                    return 0  # Monday
            return FakeNow()

    monkeypatch.setattr('your_addon.datetime', MockDateTime)

    from your_addon import is_weekend
    assert is_weekend() == False

def test_should_pause_travel_mode():
    # Mock config
    config = {'travel_mode': True, 'pause_on_weekends': False}

    # Test logic without Anki dependencies
    from your_addon import should_pause_new_cards
    assert should_pause_new_cards(config) == True
```

### 5.2 Mocking Best Practices

**Key principles:**
1. **Mock at the boundary**: Mock external dependencies (Anki API), not internal logic
2. **Use autospec**: Prevents typos in mock specifications
3. **Test behavior, not implementation**: Focus on what the code does, not how

**Mocking Anki collection:**

```python
def test_card_filtering(mocker):
    # Mock mw.col
    mock_col = mocker.Mock()
    mock_col.find_cards.return_value = [1, 2, 3]

    mocker.patch('aqt.mw.col', mock_col)

    # Test your function
    result = your_function_that_uses_col()
    assert result == expected_value
```

**Mocking configuration:**

```python
def test_config_disabled(mocker):
    mock_config = {'enabled': False}
    mocker.patch('aqt.mw.addonManager.getConfig', return_value=mock_config)

    # Test that addon respects disabled state
    assert should_pause_new_cards() == False
```

### 5.3 Test Organization

**Simple project test structure:**

```
weekend_pause/
├── __init__.py
├── config.json
└── tests/
    ├── __init__.py
    ├── test_weekend_logic.py
    ├── test_configuration.py
    └── conftest.py  # Shared fixtures
```

**conftest.py** (shared test fixtures):

```python
import pytest

@pytest.fixture
def mock_config():
    return {
        'enabled': True,
        'pause_on_weekends': True,
        'travel_mode': False
    }

@pytest.fixture
def weekend_datetime(monkeypatch):
    """Mock datetime to return Saturday."""
    class MockDateTime:
        @staticmethod
        def now():
            class FakeNow:
                def weekday(self):
                    return 5
            return FakeNow()

    monkeypatch.setattr('weekend_pause.datetime', MockDateTime)
```

### 5.4 Testing Without Anki

**Separate pure logic from Anki dependencies:**

```python
# weekend_logic.py - Pure Python, no Anki imports
def is_weekend_day(day_of_week):
    """Check if day_of_week is weekend (5=Sat, 6=Sun)."""
    return day_of_week in [5, 6]

def should_pause(is_weekend, travel_mode, pause_on_weekends):
    """Pure function - easy to test."""
    if travel_mode:
        return True
    if pause_on_weekends and is_weekend:
        return True
    return False

# __init__.py - Anki integration
from aqt import mw, gui_hooks
from datetime import datetime
from .weekend_logic import is_weekend_day, should_pause

def on_card_show(card):
    config = mw.addonManager.getConfig(__name__)
    today = datetime.now().weekday()

    if should_pause(
        is_weekend=is_weekend_day(today),
        travel_mode=config.get('travel_mode', False),
        pause_on_weekends=config.get('pause_on_weekends', True)
    ):
        if card.type == 0:  # New card
            mw.reviewer.nextCard()
```

**Benefits:**
- Test pure logic without mocking Anki
- Faster tests
- Easier to reason about
- Better separation of concerns

---

## 6. Common Pitfalls and How to Avoid Them

### 6.1 State Management Issues

**Problem**: Addons maintain state that gets out of sync with Anki

**BAD**:
```python
# Global state that can become stale
original_limits = {}

def save_limits():
    global original_limits
    # Saved once, never updated when user changes settings
    original_limits = get_deck_limits()
```

**GOOD**:
```python
# Store in addon config, read fresh each time
def get_original_limit(deck_id):
    config = mw.addonManager.getConfig(__name__)
    limits = config.get('original_limits', {})
    return limits.get(str(deck_id))

def save_original_limit(deck_id, limit):
    config = mw.addonManager.getConfig(__name__)
    if 'original_limits' not in config:
        config['original_limits'] = {}
    config['original_limits'][str(deck_id)] = limit
    mw.addonManager.writeConfig(__name__, config)
```

### 6.2 Lifecycle and Timing Issues

**Problem**: Running code before collection is loaded

**BAD**:
```python
# __init__.py - runs on Anki startup
from aqt import mw

# CRASH! Collection not loaded yet
cards = mw.col.find_cards("deck:MyDeck")
```

**GOOD**:
```python
# __init__.py
from aqt import mw, gui_hooks

def on_profile_loaded():
    # Now it's safe to access collection
    cards = mw.col.find_cards("deck:MyDeck")

gui_hooks.profile_did_open.append(on_profile_loaded)
```

**Important hooks for lifecycle:**
- `profile_did_open` - Profile loaded, collection available
- `profile_will_close` - About to close, save state
- `collection_did_load` - Collection ready

### 6.3 Database Schema Modification

**Problem**: Modifying Anki's database schema breaks future updates

**NEVER DO THIS**:
```python
# DON'T - Breaks Anki updates
mw.col.db.execute("ALTER TABLE cards ADD COLUMN my_custom_field TEXT")
```

**DO THIS INSTEAD**:
```python
# Store addon data in config or separate database
config = mw.addonManager.getConfig(__name__)
config['card_data'] = {
    '12345': {'my_field': 'value'}
}
mw.addonManager.writeConfig(__name__, config)
```

### 6.4 Performance and UI Freezing

**Problem**: Long operations freeze the UI

**BAD**:
```python
def on_button_click():
    # Freezes UI for several seconds
    for card_id in all_cards:
        process_card(card_id)
    show_message("Done!")
```

**GOOD**:
```python
from aqt.operations import QueryOp

def process_all_cards():
    """Runs in background thread."""
    results = []
    for card_id in all_cards:
        results.append(process_card(card_id))
    return results

def on_success(results):
    """Runs in main thread."""
    show_message(f"Processed {len(results)} cards!")

def on_button_click():
    QueryOp(
        parent=mw,
        op=process_all_cards,
        success=on_success
    ).run_in_background()
```

### 6.5 Addon Conflicts

**Problem**: Multiple addons modifying the same hooks/functions

**Mitigation**:
1. Use hooks instead of monkey-patching when possible
2. Be conservative with what you modify
3. Check if other addons are installed
4. Document known conflicts

**Example**:
```python
def on_card_show(card):
    # Check if another addon already handled this
    if hasattr(card, '_processed_by_other_addon'):
        return

    # Your logic here
    your_processing(card)
```

### 6.6 Version Compatibility

**Problem**: Code breaks on Anki updates

**Best Practices**:
1. Test against multiple Anki versions
2. Use version checks for breaking changes
3. Prefer official APIs over internal implementation details
4. Subscribe to Anki developer announcements

**Example**:
```python
from anki import version as anki_version

def is_anki_25_or_later():
    major, minor = anki_version.split('.')[:2]
    return int(major) >= 25

if is_anki_25_or_later():
    # Use new API
    cards = mw.col.find_cards(query)
else:
    # Fallback for older versions
    cards = mw.col.findCards(query)
```

---

## 7. Reference Implementations

### 7.1 Well-Structured Addon Examples

**Official Anki Demos** (https://github.com/ankitects/anki-addons/tree/master/demos):

1. **card_did_render** - Simple lifecycle hook example
   - Single file structure
   - Clean hook registration
   - Minimal code

2. **field_filter** - Data manipulation pattern
   - Filter-based architecture
   - Text processing example

3. **av_player** - Media handling
   - Integration with Anki's media system

**Glutanimate's Addons** (https://github.com/glutanimate/anki-addons-misc):

- Well-organized multi-file structure
- Comprehensive build system (anki-addon-builder)
- Professional quality

**AnkiWeekendsAndHolidays** (https://github.com/vasarmilan/AnkiWeekendsAndHolidays):

- Similar functionality to your addon
- Reschedules cards to skip dates
- Configuration-driven
- Respects spaced repetition principles (max 10% interval change)

### 7.2 Code Patterns from Real Addons

**Pattern 1: Simple Card Filter (from sched_filter_dailydue.py)**

```python
def wrap_fillDyn(original_func, scheduler, deck_dict):
    """Wrap scheduler to add custom filtering."""
    search_term = deck_dict.get('terms', [[]])[0][0]

    if 'is:today' in search_term:
        # Custom card selection logic
        new_cards = scheduler.col.db.list(
            "select id from cards where did = ? and queue = 0 order by due limit ?",
            deck_id, new_limit
        )
        review_cards = scheduler.col.db.list(
            "select id from cards where (queue in (2,3) and due <= ?) or (queue = 1 and due <= ?)",
            today, day_cutoff
        )
        return new_cards + review_cards

    # Delegate to original function
    return original_func(scheduler, deck_dict)

# Register wrapper
Scheduler._fillDyn = wrap(Scheduler._fillDyn, wrap_fillDyn, "around")
```

**Pattern 2: Configuration Dialog**

```python
from aqt.qt import QDialog, QVBoxLayout, QCheckBox, QPushButton

def show_config_dialog():
    dialog = QDialog(mw)
    dialog.setWindowTitle("Weekend Pause Settings")

    layout = QVBoxLayout()

    config = mw.addonManager.getConfig(__name__)

    weekend_checkbox = QCheckBox("Pause on weekends")
    weekend_checkbox.setChecked(config.get('pause_on_weekends', True))
    layout.addWidget(weekend_checkbox)

    travel_checkbox = QCheckBox("Travel mode")
    travel_checkbox.setChecked(config.get('travel_mode', False))
    layout.addWidget(travel_checkbox)

    def save_config():
        config['pause_on_weekends'] = weekend_checkbox.isChecked()
        config['travel_mode'] = travel_checkbox.isChecked()
        mw.addonManager.writeConfig(__name__, config)
        dialog.close()

    save_button = QPushButton("Save")
    save_button.clicked.connect(save_config)
    layout.addWidget(save_button)

    dialog.setLayout(layout)
    dialog.exec()

mw.addonManager.setConfigAction(__name__, show_config_dialog)
```

**Pattern 3: Language Detection**

```python
from anki.lang import currentLang

def get_user_language():
    """Get current Anki language with fallback."""
    lang = currentLang.lower()

    # Map Anki language codes to addon languages
    if lang.startswith('pt'):
        return 'pt-br'
    else:
        return 'en'  # Default fallback

def tr(key, lang=None):
    """Translate key to user language."""
    if lang is None:
        lang = get_user_language()

    translations = {
        'en': {
            'paused': 'New cards paused',
            'weekend': 'Weekend mode active',
            'travel': 'Travel mode active',
        },
        'pt-br': {
            'paused': 'Novos cartões pausados',
            'weekend': 'Modo fim de semana ativo',
            'travel': 'Modo viagem ativo',
        }
    }

    return translations.get(lang, translations['en']).get(key, key)
```

---

## 8. Specific Recommendations for Weekend Card Filter

### 8.1 Recommended Implementation Strategy

Based on comprehensive research, here's the SIMPLEST approach for your addon:

**Architecture**: Hook-based card skipping
**Hook**: `reviewer_will_show_question`
**Logic**: Check if card is new + (weekend OR travel mode) → skip to next card

### 8.2 Complete Minimal Implementation

**File: __init__.py**

```python
"""
Weekend Card Pause v2.0
Pauses new cards on weekends, keeps reviews active.
"""

from aqt import mw, gui_hooks
from datetime import datetime
from anki.lang import currentLang

__version__ = "2.0.0"

# Constants
WEEKEND_DAYS = [5, 6]  # Saturday=5, Sunday=6

# Translations
TRANSLATIONS = {
    'en': {
        'weekend_mode': 'Weekend Mode',
        'travel_mode': 'Travel Mode',
        'config_title': 'Weekend Card Pause Settings',
    },
    'pt-br': {
        'weekend_mode': 'Modo Fim de Semana',
        'travel_mode': 'Modo Viagem',
        'config_title': 'Configurações Pausa de Fim de Semana',
    }
}

def tr(key):
    """Translate with fallback to English."""
    lang = currentLang.lower()
    if lang.startswith('pt'):
        lang = 'pt-br'
    else:
        lang = 'en'

    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

def is_weekend():
    """Check if today is Saturday or Sunday."""
    return datetime.now().weekday() in WEEKEND_DAYS

def should_skip_new_cards():
    """Determine if new cards should be skipped."""
    config = mw.addonManager.getConfig(__name__)

    # Addon disabled
    if not config.get('enabled', True):
        return False

    # Travel mode overrides weekend check
    if config.get('travel_mode', False):
        return True

    # Weekend mode
    if config.get('pause_on_weekends', True) and is_weekend():
        return True

    return False

def on_reviewer_will_show_question(card):
    """Hook: Called before showing a question card."""
    # Only process if collection is loaded
    if not mw.col:
        return

    # Check if card is new (type 0 = new, 1 = learning, 2 = review)
    if card.type == 0 and should_skip_new_cards():
        # Skip this new card and get next one
        mw.reviewer.nextCard()

# Register hooks
gui_hooks.reviewer_will_show_question.append(on_reviewer_will_show_question)
```

**File: config.json**

```json
{
  "enabled": true,
  "pause_on_weekends": true,
  "travel_mode": false
}
```

**File: config.md**

```markdown
# Weekend Card Pause Configuration

## Settings

- **enabled**: Enable or disable the addon entirely
  - Default: `true`

- **pause_on_weekends**: Pause new cards on Saturday and Sunday
  - Default: `true`
  - When enabled, only review cards will be shown on weekends

- **travel_mode**: Pause new cards indefinitely
  - Default: `false`
  - Useful for vacations or study breaks
  - Overrides weekend settings when enabled

## Notes

- Only NEW cards are paused, REVIEW cards always continue
- Changes take effect immediately (no Anki restart needed)
- Works with Anki 25.x and later
```

### 8.3 Testing Checklist

Before releasing your addon, verify:

**Functional Tests:**
- ✅ New cards skip on Saturday
- ✅ New cards skip on Sunday
- ✅ New cards show on Monday-Friday
- ✅ Review cards ALWAYS show (weekends + weekdays)
- ✅ Travel mode skips new cards on any day
- ✅ Disabled addon shows all cards
- ✅ Config changes apply immediately

**Edge Cases:**
- ✅ Works when no cards available
- ✅ Works with multiple decks
- ✅ Works with filtered decks
- ✅ Profile switches don't cause issues
- ✅ Collection close/reload handled gracefully

**Compatibility:**
- ✅ Works with Anki 25.x
- ✅ No conflicts with popular addons
- ✅ Syncs properly across devices

### 8.4 Potential Enhancements (YAGNI - Don't implement unless needed)

Things you might be tempted to add but SHOULDN'T unless explicitly required:

- ❌ Custom weekend days (e.g., Friday-Saturday)
- ❌ Per-deck settings
- ❌ Timezone customization
- ❌ Statistics tracking
- ❌ Scheduling history
- ❌ Smart rescheduling (moving due dates)
- ❌ Integration with calendar apps
- ❌ Notification system
- ❌ Advanced UI with charts

**Remember**: Keep it simple. Add features only when users actually request them.

---

## 9. Development Workflow

### 9.1 Initial Setup

```bash
# Create addon directory
cd ~/.local/share/Anki2/addons21/  # Linux
# or ~/Library/Application Support/Anki2/addons21/  # macOS
# or %APPDATA%/Anki2/addons21/  # Windows

mkdir weekend_pause
cd weekend_pause

# Create files
touch __init__.py config.json config.md

# (Optional) Initialize git
git init
```

### 9.2 Development Cycle

1. **Make changes** to `__init__.py`
2. **Reload addon** in Anki:
   - Tools → Add-ons → Select addon → Config
   - Or restart Anki
3. **Test functionality**
4. **Check Anki console** for errors (Tools → Add-ons → View Files → Show Console)

### 9.3 Debugging

**View Anki console:**
- Help → Toggle Debug Console (Ctrl+Shift+:)

**Add debug prints:**

```python
def on_reviewer_will_show_question(card):
    print(f"DEBUG: Card type={card.type}, should_skip={should_skip_new_cards()}")
    # Your logic
```

**Use Anki's showInfo for user-visible messages:**

```python
from aqt.utils import showInfo

showInfo(f"Card type: {card.type}")
```

### 9.4 Packaging for Distribution

**Create manifest.json:**

```json
{
  "package": "weekend_pause",
  "name": "Weekend Card Pause",
  "author": "Your Name",
  "version": "2.0.0",
  "homepage": "https://github.com/yourusername/weekend-pause",
  "conflicts": [],
  "min_point_version": 50,
  "max_point_version": 0
}
```

**Create .ankiaddon file:**

```bash
# Zip the addon folder
cd ~/.local/share/Anki2/addons21/
zip -r weekend_pause.ankiaddon weekend_pause/

# Upload to AnkiWeb or share directly
```

---

## 10. Cross-Platform Considerations (CRITICAL)

### 10.1 The Mobile Problem

**Addons only run on desktop** (Windows/Mac/Linux). They do NOT run on:
- AnkiMobile (iOS) ❌
- AnkiDroid (Android) ❌

**For users who study on multiple platforms**, addon behavior must work via synced data.

### 10.2 What Syncs via AnkiWeb

| Data Type | Syncs? | Use for Cross-Platform? |
|-----------|--------|-------------------------|
| Deck configuration (new card limits) | ✅ Yes | ✅ Recommended |
| Card scheduling (due dates, intervals) | ✅ Yes | ⚠️ Too invasive |
| Review history | ✅ Yes | N/A |
| Addon code (Python) | ❌ No | ❌ Desktop-only |
| Hook behavior | ❌ No | ❌ Desktop-only |
| Addon config files | ❌ No | ❌ Desktop-only |

### 10.3 Implementation Strategy for Cross-Platform

**MUST USE: Deck Configuration Modification (Strategy 1)**

This is the ONLY approach that:
1. Syncs behavior to mobile via AnkiWeb
2. Doesn't compromise SRS algorithm
3. Is reversible and safe

**User Flow Example**:
```
Friday night (macOS):
- Addon detects weekend approaching
- Saves original new_cards_per_day limits
- Sets all decks to new_cards_per_day = 0
- User syncs (automatic on close)
- Config uploaded to AnkiWeb

Saturday morning (iOS):
- User opens AnkiMobile
- Syncs, downloads deck config with limit=0
- No new cards appear ✅
- Reviews work normally ✅

Monday morning (macOS):
- Addon detects weekday
- Restores original limits
- Syncs to AnkiWeb

Monday evening (iOS):
- Syncs, downloads restored limits
- New cards reappear ✅
```

### 10.4 Critical API Requirements

**MUST use proper save method for sync**:
```python
# ✅ CORRECT - Marks for sync
config = mw.col.decks.get_config(config_id)
config["new"]["perDay"] = 0
mw.col.decks.save(config)  # This marks for sync!

# ❌ WRONG - Won't sync
mw.col.db.execute("UPDATE...")  # Direct DB writes don't sync
```

**MUST track original limits carefully**:
```python
# Store in addon config
addon_config = mw.addonManager.getConfig(__name__)
addon_config['original_limits'][str(deck_id)] = original_limit
mw.addonManager.writeConfig(__name__, addon_config)
```

### 10.5 Edge Cases to Handle

1. **User modifies deck settings while addon active**
   - Detect changes, update stored originals
   - Warn user if conflicts detected

2. **Sync timing issues**
   - Encourage auto-sync on all devices
   - Document sync requirements clearly

3. **Addon disabled mid-weekend**
   - Provide restore button to reset limits
   - Don't leave limits stuck at 0

4. **Multiple decks with different settings**
   - Track limits per deck, not globally
   - Handle deck creation/deletion

### 10.6 User Documentation Requirements

**MUST document**:
1. Addon requires desktop Anki to modify settings
2. Settings sync automatically to mobile via AnkiWeb
3. Users must sync regularly for consistent behavior
4. What to do if limits get stuck (restore function)

**Example warning**:
```
⚠️ This addon modifies your deck configuration to pause new cards.
Changes sync to AnkiMobile/AnkiDroid automatically.
Make sure to sync regularly on all devices for consistent behavior.
```

### 10.7 Further Reading

See detailed cross-platform research in:
- `research_cross_platform_behavior.md` - Complete technical analysis
- `RECOMMENDATIONS.md` - Implementation guidelines and code examples

---

## 11. Summary and Action Plan

### 11.1 Critical Success Factors

1. **✅ Cross-Platform First**: Use deck configuration modification (syncs via AnkiWeb)
2. **✅ Proper API Usage**: Use `mw.col.decks.save()` to mark for sync
3. **✅ Track State Carefully**: Store original limits per-deck in addon config
4. **✅ Work with v3 Scheduler**: Don't try to monkey-patch
5. **✅ Keep it Simple**: Clear, testable code focused on core functionality
6. **✅ Handle Edge Cases**: Sync timing, user modifications, restore functionality
7. **✅ Document Requirements**: Users must understand sync dependency

### 11.2 Implementation Checklist

**Phase 1: Core Functionality (Deck Config Approach)**
- [ ] Set up addon file structure
- [ ] Implement `is_weekend()` function
- [ ] Implement deck config modification logic
- [ ] Track original limits in addon config (per-deck)
- [ ] Use `mw.col.decks.save()` for sync
- [ ] Test on macOS desktop
- [ ] Test sync to iOS (critical!)

**Phase 2: Configuration**
- [ ] Add travel mode toggle
- [ ] Add enable/disable toggle
- [ ] Create `config.md` documentation
- [ ] Test config changes

**Phase 3: Localization**
- [ ] Add PT-BR translations
- [ ] Implement language detection
- [ ] Test language fallback

**Phase 4: Testing & Polish**
- [ ] Write unit tests for pure logic
- [ ] Test on Anki 25.x desktop
- [ ] **Test cross-platform sync (macOS ↔ iOS)**
- [ ] Test with multiple decks
- [ ] Test edge cases (sync timing, user modifications)
- [ ] Test restore functionality
- [ ] Review code for simplicity

**Phase 5: Distribution**
- [ ] Create manifest.json
- [ ] Write user documentation (emphasize sync requirement!)
- [ ] Add warnings about cross-platform behavior
- [ ] Package as .ankiaddon
- [ ] Upload to AnkiWeb (optional)

### 11.3 Key Resources

**Official Documentation:**
- Addon Docs: https://addon-docs.ankiweb.net/
- Hooks Reference: https://addon-docs.ankiweb.net/hooks-and-filters.html
- Anki Source: https://github.com/ankitects/anki

**Example Addons:**
- Official Demos: https://github.com/ankitects/anki-addons/tree/master/demos
- Glutanimate's Addons: https://github.com/glutanimate/anki-addons-misc
- Weekends/Holidays: https://github.com/vasarmilan/AnkiWeekendsAndHolidays

**Testing:**
- pytest-anki: https://github.com/glutanimate/pytest-anki
- Python mocking guide: https://realpython.com/python-mock-library/

**Community:**
- Anki Forums: https://forums.ankiweb.net/
- Development Section: https://forums.ankiweb.net/c/development/

**Cross-Platform Research:**
- `research_cross_platform_behavior.md` - Full technical deep-dive (50+ pages)
- `RECOMMENDATIONS.md` - Implementation plan with code examples

---

## 12. Conclusion

The path to a simple, maintainable addon is through restraint:

1. **✅ Cross-Platform First** - Deck config modification (NOT hooks) for iOS/Android support
2. **✅ Implement only what's needed now** - YAGNI principle
3. **✅ Prefer functions over classes** - Less abstraction
4. **✅ Work with Anki, not against it** - Use official APIs that sync properly
5. **✅ Test the important parts** - Weekend detection, config logic, **and cross-platform sync**
6. **✅ Keep it small** - Focused modules, clear responsibilities

Your v1.0 became complex through accumulation of fixes and features. v2.0 should be the opposite: minimal, focused, and maintainable.

**Final Recommendation for Cross-Platform Users**:
- ✅ Use Strategy 1 (Deck Configuration Modification)
- ✅ Store original limits carefully (per-deck in addon config)
- ✅ Use proper API (`mw.col.decks.save()`) to ensure sync
- ✅ Test thoroughly on BOTH macOS and iOS
- ✅ Document sync requirements clearly for users
- ❌ Do NOT use hooks (desktop-only)
- ❌ Do NOT reschedule cards (too invasive)

Good luck with your rewrite!
