# Cross-Platform Anki Addon Research: Weekend Card Presentation

**Research Date:** 2025-01-11
**Purpose:** Understanding how Anki addons that modify card presentation behavior work across desktop and mobile platforms
**Status:** Complete

---

## Executive Summary

**Key Finding:** Addons only run on desktop, but their effects can sync to mobile through strategic use of synced data (deck configuration, card scheduling, or custom JavaScript scheduling).

**Recommended Approach for Weekend Addon:**
- **Primary Strategy:** Modify deck configuration (set new card limit to 0 on weekends) - syncs to mobile
- **Secondary Strategy:** Use scheduler hooks for desktop-only dynamic behavior
- **Avoid:** Pure hook-based interception without data modification (won't affect mobile)

---

## The Cross-Platform Problem

### Platform Limitations

1. **Desktop (Windows/Mac/Linux):**
   - Full Python addon support
   - Access to all hooks and APIs
   - Can modify UI, scheduling, deck configuration

2. **AnkiMobile (iOS):**
   - NO addon support
   - Supports v3 custom JavaScript scheduling (syncs from desktop)
   - Receives synced deck configurations, card due dates

3. **AnkiDroid (Android):**
   - NO traditional Python addon support
   - Some experimental addon work in progress (not production-ready)
   - Supports v3 custom JavaScript scheduling (as of 2.17+)
   - Receives synced deck configurations, card due dates

### What Data Syncs via AnkiWeb

**Data that DOES sync:**
- Card scheduling data (due dates, intervals, ease factors, card state)
- Deck configuration/options (including new card limits, review limits, deck settings)
- Review history
- Notes and cards
- Media files (sounds, images)
- Custom scheduling JavaScript code (v3 scheduler)

**Data that DOES NOT sync:**
- Addon code or settings (Python addons are desktop-only)
- Addon configuration files
- Hooks and Python-based behavior modifications

**Critical Database Insight:**
- Anki uses a single SQLite database (collection.anki2)
- The `dconf` field in the `col` table stores deck configuration as JSON
- Changes must use proper API methods (`col.decks.save()`) to mark for sync
- Direct database writes with `execute()` do NOT sync

---

## Three Implementation Strategies

### Strategy 1: Modify Deck Configuration (RECOMMENDED)

**Approach:** Dynamically change deck options (new card limit) based on date

**How it works:**
```python
# Pseudocode
if is_weekend():
    config["new"]["perDay"] = 0  # No new cards
else:
    config["new"]["perDay"] = original_limit  # Restore normal limit

mw.col.decks.save(config)  # Marks for sync
```

**Pros:**
- Syncs to mobile automatically
- Works consistently across all platforms
- User sees correct behavior on mobile without desktop
- Graceful degradation: if addon disabled, last-set limit persists

**Cons:**
- Modifies persistent deck state
- Need to restore original limits carefully
- Timing of sync matters (see "User Experience Scenarios" below)

**Examples:**
- Manual solution suggested in forum discussions
- Similar to how anki-limitnew dynamically adjusts limits

**Mobile Behavior:**
- When user syncs desktop → mobile, new card limit=0 is applied
- User on mobile won't see new cards (desired behavior)
- When they sync back desktop → changes merge normally

---

### Strategy 2: Scheduler Hooks (DESKTOP-ONLY)

**Approach:** Use `scheduler_new_limit_for_single_deck` hook to intercept card gathering

**How it works:**
```python
from anki import hooks

def modify_new_card_limit(count: int, deck_id: int) -> int:
    if is_weekend():
        return 0  # Override limit to 0
    return count  # Normal behavior

hooks.scheduler_new_limit_for_single_deck.append(modify_new_card_limit)
```

**Pros:**
- Clean, non-invasive
- Doesn't modify persistent state
- Works well with other addons
- Available since Anki 2.1.22

**Cons:**
- Desktop-only (hooks don't run on mobile)
- User on mobile will see new cards (undesired behavior)
- Requires desktop study session to prevent cards

**Examples:**
- anki-limitnew addon uses this hook (with fallback to monkey-patching for older versions)

**Mobile Behavior:**
- Hook doesn't run on mobile
- Mobile uses normal deck configuration
- User WILL see new cards on mobile (breaks intended behavior)

---

### Strategy 3: Reschedule Cards (SYNCS BUT INVASIVE)

**Approach:** Physically change card due dates to avoid weekends

**How it works:**
```python
# Move cards scheduled for Saturday/Sunday to Friday or Monday
card.due = new_due_date
mw.col.update_card(card)  # Proper API marks for sync
```

**Pros:**
- Syncs to mobile
- Works across all platforms
- User sees correct behavior everywhere

**Cons:**
- Highly invasive - permanently changes scheduling
- Violates spaced repetition algorithm integrity
- Intervals change by up to 10% (acceptable) or more (problematic)
- Conflicts with user's SRS progress
- Difficult to undo

**Examples:**
- AnkiWeekendsAndHolidays addon uses this approach
- Free Weekend addon uses "fuzz range" rescheduling

**Mobile Behavior:**
- Rescheduled due dates sync to mobile
- User won't see cards moved away from weekend
- BUT: algorithm integrity compromised

---

### Strategy 4: Custom JavaScript Scheduling (v3 ONLY - CROSS-PLATFORM)

**Approach:** Use v3 scheduler's custom JavaScript to modify scheduling algorithm

**How it works:**
- Enter JavaScript code in deck options → custom scheduling
- Code runs on all platforms (desktop + mobile)
- Can access card state, modify intervals

**Pros:**
- True cross-platform solution
- JavaScript syncs via deck configuration
- Works on desktop, AnkiMobile, AnkiDroid (2.17+)
- Non-invasive to Anki's core

**Cons:**
- Limited to v3 scheduler (default since Anki 2023)
- JavaScript has restricted access (can't change which cards are gathered)
- Can modify scheduling AFTER card selection, not prevent selection
- Cannot dynamically change new card limit based on date

**Critical Limitation:**
> "JavaScript can not be used to change which cards are gathered that day."

This means custom scheduling CANNOT prevent new cards from appearing - it can only adjust intervals/ease after a card is answered.

**Examples:**
- Low-key Anki (two-button review system)
- FSRS custom scheduling

**Mobile Behavior:**
- Code syncs and runs on AnkiMobile (fixed as of 2.0.84, April 2022)
- Confirmed working: "I'm using my custom scheduling code on iPad now"
- AnkiDroid support added in v2.17

**Verdict for Weekend Addon:** Not suitable - can't prevent new cards from appearing

---

## What Successful Addons Do

### AnkiWeekendsAndHolidays
- **Approach:** Strategy 3 (reschedule cards)
- **How:** Moves cards away from blocked days, within 10% interval or 7-day max
- **Trigger:** Manual (Ctrl+Shift+r) or automatic at startup
- **Mobile:** Works via sync (rescheduled dates propagate)
- **Limitation:** Modifies scheduling algorithm, can conflict with other addons

### Free Weekend
- **Approach:** Strategy 3 (reschedule within fuzz range)
- **How:** Uses Anki's natural "fuzz" randomization to shift reviews
- **Limitations:**
  - Only works for cards with >3 day intervals
  - Does NOT affect learning cards
  - Doesn't change past schedules
  - Conflicts with Load Balanced Scheduler
- **Mobile:** Works via sync (within fuzz limits)
- **Version:** Compatible with v2.1.50+, does NOT work with v3 scheduler

### anki-limitnew
- **Approach:** Strategy 2 (scheduler hook)
- **How:** Uses `scheduler_new_limit_for_single_deck` hook
- **Purpose:** Dynamically reduce new cards based on workload
- **Mobile:** Desktop-only, doesn't affect mobile study sessions
- **Fallback:** Monkey patches scheduler for older Anki versions

---

## Detailed Technical Specifications

### Deck Configuration API

**Get configuration:**
```python
config = mw.col.decks.get_config(config_id)
```

**Modify new card limit:**
```python
config["new"]["perDay"] = 0  # or any integer
```

**Save (marks for sync):**
```python
mw.col.decks.save(config)
```

**Structure of config["new"]:**
- `perDay`: new cards per day limit (integer)
- `delays`: learning steps (list of minutes)
- `ints`: intervals for graduating and easy (list)
- `initialFactor`: starting ease factor
- `order`: card order (0=random, 1=due date)
- `bury`: whether to bury related cards

### Scheduler Hooks

**Available hooks (Anki 2.1.22+):**
- `scheduler_new_limit_for_single_deck(count: int, deck_id: int) -> int`
  - Called when gathering new cards for a deck
  - Can reduce limit, cannot increase beyond deck config
  - Runs per-deck during study session

**Legacy approach (pre-2.1.22):**
- Monkey patch `Scheduler._new_for_deck()` or similar methods
- Not recommended, fragile across Anki updates

### Card Scheduling Data

**Cards table fields (collection.anki2):**
- `due`: Due date (integer day for review queue, timestamp for learning)
- `ivl`: Interval in days
- `factor`: Ease factor (2500 = 250%)
- `type`: 0=new, 1=learning, 2=review, 3=relearning
- `queue`: -3=user buried, -2=sched buried, -1=suspended, 0=new, 1=learning, 2=review, 3=day learning
- `reps`: Total reviews
- `lapses`: Number of lapses
- `usn`: Update sequence number (for sync)

**Proper API for card updates:**
```python
card = mw.col.get_card(card_id)
card.due = new_due
mw.col.update_card(card)  # Marks for sync
```

**DO NOT:**
```python
mw.col.db.execute("UPDATE cards SET due = ? WHERE id = ?", new_due, card_id)
# This won't sync!
```

---

## User Experience Scenarios

### Scenario 1: Desktop Friday → Mobile Saturday (Strategy 1: Deck Config)

**Friday night (desktop):**
1. User closes Anki, addon sets `new_cards_per_day = 0`
2. Anki auto-syncs on close
3. Config change uploads to AnkiWeb

**Saturday morning (mobile):**
1. User opens AnkiMobile
2. Syncs on open, downloads config with limit=0
3. No new cards appear (desired behavior)
4. Reviews still work normally

**Result:** ✅ Works perfectly

---

### Scenario 2: Desktop Friday → Mobile Saturday (Strategy 2: Hook Only)

**Friday night (desktop):**
1. User closes Anki
2. Deck config unchanged (still says 20 new cards/day)
3. Sync uploads normal config

**Saturday morning (mobile):**
1. User opens AnkiMobile
2. Syncs, gets normal config (20 new/day)
3. AnkiMobile shows 20 new cards (hook doesn't run on mobile)

**Result:** ❌ Fails - user sees new cards on mobile

---

### Scenario 3: Addon Disabled Mid-Weekend

**Saturday (addon enabled):**
- Deck config set to 0 new cards

**User disables addon:**
- Config stays at 0 (persists until manually changed)
- No automatic restoration

**Monday:**
- Addon should detect weekday and restore limit
- If addon never runs, limit stays at 0

**Risk:** Config can get "stuck" if addon disabled permanently

**Mitigation:**
- Store original limits in addon config
- Add reset function
- Monitor deck config modifications
- Warning dialog when disabling addon

---

### Scenario 4: Travel Mode (Extended Period)

**User enables "travel mode" on Wednesday:**
1. Addon sets `new_cards_per_day = 0`
2. Syncs to AnkiWeb

**User studies on mobile Thursday-Sunday:**
- No new cards on any day
- Reviews continue normally

**User returns, disables travel mode Monday:**
1. Desktop addon restores original limit
2. Syncs to AnkiWeb
3. New cards resume

**Result:** ✅ Works with Strategy 1

---

## Sync Timing Considerations

### Race Condition: Both Devices Modified Before Sync

**Scenario:**
- Desktop: User studies Friday, addon sets limit=0
- Mobile: User studies Saturday (before syncing), limit still =20
- Mobile: User syncs → pushes changes to AnkiWeb
- Desktop: User syncs → downloads changes

**Result:** Last sync wins - potential for incorrect state

**Mitigation:**
- Warn users to sync before studying
- Implement conflict detection
- Use timestamp checking

### Auto-Sync Behavior

**Desktop:**
- Auto-syncs on close (by default)
- Auto-syncs on open (by default)

**Mobile:**
- Manual sync (tap sync button)
- AnkiMobile: Can enable auto-sync in preferences
- AnkiDroid: Can enable auto-sync

**Recommendation:** Encourage users to enable auto-sync on all devices

---

## Best Practices from Research

### 1. Use Data That Syncs

**DO:**
- Modify deck configuration (syncs)
- Change card due dates (syncs, but invasive)
- Use custom JavaScript scheduling v3 (syncs, but limited)

**DON'T:**
- Rely only on hooks (desktop-only)
- Assume addon code runs on mobile
- Directly modify database without proper API

### 2. Graceful Degradation

**Principle:** If addon doesn't run, behavior should degrade gracefully

**Good example:**
- Deck config set to 0 new cards
- Even if addon disabled, user won't get new cards (safe default)

**Bad example:**
- Hook intercepts card gathering
- If addon disabled, user suddenly gets flood of new cards

### 3. State Management

**Track original state:**
```python
# Store in addon config
{
    "deck_1234567890": {
        "original_new_limit": 20,
        "modified_on": "2025-01-11T09:00:00Z"
    }
}
```

**Restore state:**
- On weekday morning
- On addon disable
- On addon uninstall hook

### 4. User Communication

**Inform users about:**
- Platform limitations (desktop vs mobile)
- Sync requirements (must sync to propagate changes)
- What happens if addon disabled
- Travel mode behavior

**UI elements:**
- Status indicator (weekend mode active)
- Manual override button
- Sync reminder

### 5. Conflict Prevention

**Avoid:**
- Modifying same data as other scheduler addons
- Permanent scheduling changes
- Assumptions about timing

**Be compatible with:**
- Load Balancer (popular addon)
- FSRS custom scheduling
- Other limit-based addons

### 6. Testing Edge Cases

**Must test:**
- Midnight rollover (Friday 11:59 PM → Saturday 12:00 AM)
- Timezone changes (traveling users)
- First install on weekend vs weekday
- Addon disabled mid-weekend
- Sync conflicts
- Multiple decks with different configs
- Subdecks inheriting parent configs

---

## Recommended Implementation for Weekend Addon

### Primary Strategy: Deck Configuration Modification

**Why:**
- Syncs to mobile (solves core problem)
- Non-invasive to scheduling algorithm
- Reversible
- Simple to understand and debug

**Architecture:**

1. **Background Timer**
   - Check every hour if day changed
   - On day change, evaluate weekend status

2. **Weekend Detection**
   ```python
   def is_weekend(date=None):
       if date is None:
           date = datetime.now()
       return date.weekday() in [5, 6]  # Saturday=5, Sunday=6
   ```

3. **Config Modification**
   ```python
   def apply_weekend_mode():
       for deck_id in get_all_deck_ids():
           config = get_deck_config(deck_id)

           # Store original if not stored
           if not is_stored(deck_id):
               store_original_limit(deck_id, config["new"]["perDay"])

           # Set to 0
           config["new"]["perDay"] = 0
           save_deck_config(config)

   def apply_weekday_mode():
       for deck_id in get_all_deck_ids():
           config = get_deck_config(deck_id)

           # Restore original
           original = get_stored_original_limit(deck_id)
           config["new"]["perDay"] = original
           save_deck_config(config)
   ```

4. **Travel Mode**
   - Same mechanism, but trigger is manual button press
   - Store "travel_mode_active" flag
   - Don't auto-restore on weekday if travel mode active

5. **Safety Mechanisms**
   - Validate config before modification
   - Catch and log exceptions
   - Fallback to safe defaults
   - Never crash Anki

### Secondary Strategy: Hook for Desktop UX

**Why:**
- Better user experience on desktop
- Can provide dynamic feedback
- Works alongside config modification

**Use hook to:**
- Update UI indicators
- Provide instant feedback
- Complement config changes

**Don't rely on hook alone:**
- Always modify config as primary mechanism
- Hook is enhancement only

---

## Alternative Approaches Considered and Rejected

### ❌ Pure Hook-Based (Strategy 2 Only)

**Rejected because:**
- Doesn't work on mobile (core requirement)
- User studies on mobile Saturday, sees new cards (bad UX)

### ❌ Card Rescheduling (Strategy 3)

**Rejected because:**
- Too invasive to scheduling algorithm
- Violates spaced repetition principles
- User SRS progress compromised
- Difficult to undo
- Potential for bugs causing permanent damage

**Acceptable for:**
- Vacation addons that reschedule large date ranges
- One-time adjustments

**Not acceptable for:**
- Recurring weekly behavior

### ❌ Custom JavaScript Scheduling (Strategy 4)

**Rejected because:**
- Cannot prevent new cards from appearing
- Can only modify scheduling after card answered
- Limitation quote: "JavaScript can not be used to change which cards are gathered that day"

**Works for:**
- Modifying intervals
- Changing ease factors
- Custom button behavior

**Doesn't work for:**
- Filtering which cards appear
- Controlling new card limits

### ❌ Filtered Decks

**Rejected because:**
- User would have to manually use filtered deck
- Can't automatically redirect study sessions
- Breaks normal workflow
- Not transparent to user

---

## Security and Privacy Considerations

### Data Stored Locally

**Addon config:**
- Original deck limits
- Travel mode state
- User preferences (language, etc.)

**No sensitive data:**
- No card content
- No study history
- No personal information

### Sync Safety

**Only modifies:**
- Deck configuration (standard Anki data)
- No direct card content changes

**Reversible:**
- All changes can be undone
- Original state stored

---

## Performance Considerations

### Timer Frequency

**Every hour check:**
- Minimal CPU usage
- Catches day change within 1 hour
- Acceptable latency

**Midnight check:**
- More precise, but can miss if Anki closed
- Users may study past midnight

**On Anki open:**
- Guaranteed to catch day change
- Instant weekend mode application

**Recommendation:** Check on open + hourly timer

### Number of Decks

**Scalability:**
- Modifying 100+ deck configs is fast (<100ms)
- Collection API is efficient
- SQLite handles it well

**Optimization:**
- Only modify decks with new cards
- Cache deck IDs
- Batch updates

---

## Internationalization

### Language Detection

**Use Anki's language setting:**
```python
from aqt import mw
lang = mw.pm.meta.get('defaultLang', 'en')
```

**Fallback to English:**
- If language not supported
- If detection fails

### Weekend Definition

**Cultural variations:**
- Most cultures: Saturday + Sunday
- Some Middle Eastern countries: Friday + Saturday
- Some countries: Sunday only

**Recommendation:**
- Default to Saturday + Sunday
- Allow user configuration in addon settings
- Future enhancement: Holiday calendars by country

---

## Testing Strategy

### Unit Tests

**Test functions:**
- `is_weekend()` with various dates
- Config modification logic
- Original state storage/retrieval
- Date calculations

**Mock Anki API:**
- `mw.col.decks.get_config()`
- `mw.col.decks.save()`

### Integration Tests

**Test scenarios:**
- Full weekend cycle (Fri → Sat → Sun → Mon)
- Travel mode activation/deactivation
- Multiple decks
- Addon disable/re-enable

### Manual Testing Checklist

- [ ] Install on Friday, verify limit changes Saturday
- [ ] Study on mobile after desktop sync
- [ ] Disable addon mid-weekend, verify recovery
- [ ] Travel mode for 1 week
- [ ] Midnight rollover
- [ ] Timezone change (travel simulation)
- [ ] First install on weekend
- [ ] First install on weekday
- [ ] 100+ decks (performance)
- [ ] Conflict with Load Balancer addon
- [ ] Anki restart during weekend

---

## Migration from v1.0

### Data Migration

**If v1.0 stored data:**
- Migrate to new config format
- Validate data integrity
- Provide fallback defaults

**Clean start:**
- v2.0 can be fresh install
- No data migration needed if v1 uninstalled

### User Communication

**Changelog:**
- Explain v2.0 is complete rewrite
- List improvements (mobile support!)
- Note any behavior changes

**Migration guide:**
- How to uninstall v1.0
- How to install v2.0
- Expected behavior differences

---

## Future Enhancements (Out of Scope for v2.0)

### Custom Weekend Days
- Let user choose which days to block
- Support for non-traditional weekends

### Holiday Calendars
- Integrate with calendar APIs
- Block specific dates (national holidays)

### Per-Deck Configuration
- Some decks always active
- Some decks weekend-only

### Smart Scheduling
- Detect upcoming gaps (long weekends)
- Adjust new card rate to compensate

### Statistics
- Track days skipped
- Show new cards avoided
- Estimate time saved

---

## Key Takeaways

### ✅ DO

1. **Modify deck configuration** to set new card limit to 0 on weekends
2. **Use proper API methods** (`col.decks.save()`) to ensure sync
3. **Store original state** to restore on weekdays
4. **Test on mobile** to verify sync behavior
5. **Communicate clearly** about platform behavior to users
6. **Implement graceful degradation** for addon disable scenarios

### ❌ DON'T

1. **Don't rely on hooks alone** - they don't work on mobile
2. **Don't reschedule cards** - too invasive to SRS algorithm
3. **Don't use custom JavaScript** - can't control card gathering
4. **Don't assume addon runs everywhere** - desktop only
5. **Don't modify database directly** - use API methods
6. **Don't ignore sync timing** - race conditions can occur

### 🎯 Success Criteria

- User enables addon on desktop
- User studies on desktop Friday: no new cards Saturday/Sunday
- User studies on mobile Saturday: no new cards (synced config)
- User disables addon: can restore to normal easily
- User travels: can pause indefinitely with travel mode

---

## References

### Official Documentation
- [Anki Add-ons Documentation](https://addon-docs.ankiweb.net/)
- [Anki Manual - Syncing](https://docs.ankiweb.net/syncing.html)
- [Anki Manual - Deck Options](https://docs.ankiweb.net/deck-options.html)
- [AnkiMobile Manual - Cloud Sync](https://docs.ankimobile.net/syncing.html)

### Database Schema
- [AnkiDroid Wiki - Database Structure](https://github.com/ankidroid/Anki-Android/wiki/Database-Structure)
- [Anki 2 Annotated Schema](https://gist.github.com/sartak/3921255)

### Hooks and API
- [Hooks and Filters Documentation](https://addon-docs.ankiweb.net/hooks-and-filters.html)
- [The 'anki' Module](https://addon-docs.ankiweb.net/the-anki-module.html)
- [Anki Source - genhooks.py](https://github.com/ankitects/anki/blob/main/pylib/tools/genhooks.py)

### Community Discussions
- [Forum: No new cards on the weekend, just reviews](https://forums.ankiweb.net/t/no-new-cards-on-the-weekend-just-reviews/32208)
- [Forum: V3 custom scheduling code ignored by AnkiMobile](https://forums.ankiweb.net/t/v3-custom-scheduling-code-ignored-by-ankimobile/15913)
- [Forum: Cross-platform JS addons for the reviewer](https://forums.ankiweb.net/t/cross-platform-js-addons-for-the-reviewer/46082)

### Example Addons
- [AnkiWeekendsAndHolidays](https://github.com/vasarmilan/AnkiWeekendsAndHolidays)
- [Free Weekend](https://github.com/cjdduarte/Free_Weekend)
- [anki-limitnew](https://github.com/ig3/anki-limitnew)
- [Low-key Anki](https://digitalwords.net/anki/low-key/)

### Scheduler Documentation
- [The Anki v3 scheduler](https://faqs.ankiweb.net/the-2021-scheduler.html)
- [The Anki 2.1 scheduler](https://faqs.ankiweb.net/the-anki-2.1-scheduler.html)

---

**Research completed by:** Claude (Anthropic)
**For project:** Anki Weekend Addon v2.0
**Next steps:** Use findings to complete architecture planning and implementation
