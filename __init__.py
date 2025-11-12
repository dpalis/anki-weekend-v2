"""
Anki Weekend Addon v2.0

Pauses new cards on weekends (Saturday & Sunday) while keeping reviews active.
Supports travel mode for extended pauses and cross-platform sync via AnkiWeb.

Author: [Your Name]
License: MIT
Version: 2.0.0
"""

from aqt import mw, gui_hooks
from datetime import datetime


# ==========================================
# Weekend Detection
# ==========================================

def is_weekend() -> bool:
    """
    Check if today is Saturday or Sunday.

    Returns:
        bool: True if today is Saturday (5) or Sunday (6), False otherwise
    """
    return datetime.now().weekday() in [5, 6]


# ==========================================
# Config Management
# ==========================================

def get_config() -> dict:
    """
    Read addon configuration from config.json.

    Returns:
        dict: Configuration dictionary with default empty dict if not found
    """
    return mw.addonManager.getConfig(__name__) or {}


def get_original_limit(config_id: int) -> int | None:
    """
    Retrieve stored original new cards per day limit for a deck config.

    Args:
        config_id: Deck configuration ID

    Returns:
        int | None: Original limit if stored, None otherwise
    """
    limits = get_config().get('original_limits', {})
    return limits.get(str(config_id))


def store_original_limit(config_id: int, limit: int) -> None:
    """
    Store original new cards per day limit for future restoration.

    Args:
        config_id: Deck configuration ID
        limit: Original new cards per day limit to store
    """
    config = get_config()
    if 'original_limits' not in config:
        config['original_limits'] = {}
    config['original_limits'][str(config_id)] = limit
    mw.addonManager.writeConfig(__name__, config)


# ==========================================
# Deck Config Modification
# ==========================================

def apply_weekend_mode() -> None:
    """
    Set new cards per day = 0 for all decks.
    Stores original limits before modification for later restoration.
    Changes are marked for AnkiWeb sync automatically.
    """
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


def apply_weekday_mode() -> None:
    """
    Restore original new cards per day limits for all decks.
    Only restores if original limit was previously stored.
    Changes are marked for AnkiWeb sync automatically.
    """
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


# ==========================================
# Main Logic
# ==========================================

def on_profile_open() -> None:
    """
    Execute when profile opens (startup + sync).
    Applies appropriate mode based on travel mode flag or current day.

    Priority:
        1. Travel mode (if enabled): Apply weekend mode
        2. Weekend (Sat/Sun): Apply weekend mode
        3. Weekday (Mon-Fri): Apply weekday mode (restore limits)
    """
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


# ==========================================
# Hook Registration
# ==========================================

# Register hook to run on profile open (startup + profile switch)
gui_hooks.profile_did_open.append(on_profile_open)
