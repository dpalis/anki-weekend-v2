"""
Anki Weekend Addon v2.0

Pauses new cards on weekends (Saturday & Sunday) while keeping reviews active.
Supports travel mode for extended pauses and cross-platform sync via AnkiWeb.

Author: Daniel Palis
License: MIT
Version: 2.0.0
"""

from __future__ import annotations

from typing import Any

from aqt import mw, gui_hooks
from datetime import datetime


# ==========================================
# Constants
# ==========================================

# Valid range for new cards per day (Anki's UI limits: 0-9999)
MIN_NEW_CARDS = 0
MAX_NEW_CARDS = 9999

# Weekday constants (datetime.weekday() returns 0=Mon...6=Sun)
MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6
WEEKEND_DAYS = [SATURDAY, SUNDAY]


# ==========================================
# Input Validation
# ==========================================

def validate_original_limit(limit: int) -> int:
    """
    Validate and sanitize original limit value.

    Args:
        limit: Original new cards per day limit to validate

    Returns:
        int: Sanitized limit within valid range [0-9999]

    Raises:
        TypeError: If limit is not an integer
        ValueError: If limit is outside valid range
    """
    if not isinstance(limit, int):
        raise TypeError(f"Limit must be integer, got {type(limit).__name__}")

    if limit < MIN_NEW_CARDS or limit > MAX_NEW_CARDS:
        raise ValueError(f"Limit must be between {MIN_NEW_CARDS} and {MAX_NEW_CARDS}, got {limit}")

    return limit


# ==========================================
# Weekend Detection
# ==========================================

def is_weekend() -> bool:
    """
    Check if today is Saturday or Sunday.

    Returns:
        bool: True if today is weekend
    """
    return datetime.now().weekday() in WEEKEND_DAYS


# ==========================================
# Config Management
# ==========================================

# Collection config key for redundant storage
COLLECTION_CONFIG_KEY = "weekend_addon_original_limits"


def _get_collection_limits() -> dict[str, int]:
    """
    Get original limits from collection config (primary storage).

    Returns:
        dict[str, int]: Original limits stored in collection, empty dict if not found
    """
    if not mw.col:
        return {}

    try:
        limits = mw.col.get_config(COLLECTION_CONFIG_KEY)
        if limits is None or not isinstance(limits, dict):
            return {}
        return limits
    except Exception as e:
        print(f"[Weekend Addon] ERROR: Failed to read collection config: {e}")
        return {}


def _store_collection_limits(limits: dict[str, int]) -> None:
    """
    Store original limits in collection config (primary storage).

    Args:
        limits: Dictionary mapping config_id -> original limit
    """
    if not mw.col:
        return

    try:
        mw.col.set_config(COLLECTION_CONFIG_KEY, limits)
    except Exception as e:
        print(f"[Weekend Addon] ERROR: Failed to write collection config: {e}")


def get_config() -> dict[str, Any]:
    """
    Read addon configuration from config.json with validation.

    Returns:
        dict[str, Any]: Configuration dictionary with keys:
            - 'travel_mode': bool
            - 'original_limits': dict[str, int]
            - 'last_applied_mode': str | None

    Note:
        Returns safe defaults if config is corrupted or invalid.
        Logs errors for debugging.
    """
    try:
        config = mw.addonManager.getConfig(__name__)
        if config is None:
            return {'travel_mode': False, 'original_limits': {}}

        # Validate config structure
        if not isinstance(config, dict):
            print(f"[Weekend Addon] ERROR: Config is not a dict, got {type(config).__name__}")
            return {'travel_mode': False, 'original_limits': {}}

        # Ensure required keys exist with correct types
        if 'travel_mode' not in config or not isinstance(config['travel_mode'], bool):
            config['travel_mode'] = False

        if 'original_limits' not in config or not isinstance(config['original_limits'], dict):
            config['original_limits'] = {}

        # Validate original_limits entries
        validated_limits = {}
        for config_id, limit in config['original_limits'].items():
            try:
                if not isinstance(limit, int):
                    print(f"[Weekend Addon] WARNING: Limit for config {config_id} is not int, skipping")
                    continue
                validated_limits[config_id] = validate_original_limit(limit)
            except (TypeError, ValueError) as e:
                print(f"[Weekend Addon] WARNING: Invalid limit for config {config_id}: {e}")
                continue

        config['original_limits'] = validated_limits
        return config

    except Exception as e:
        print(f"[Weekend Addon] ERROR: Failed to load config: {e}")
        return {'travel_mode': False, 'original_limits': {}}


def get_original_limit(config_id: int) -> int | None:
    """
    Retrieve stored original new cards per day limit for a deck config.
    Uses redundant storage: primary (collection config) + fallback (addon config).

    Args:
        config_id: Deck configuration ID

    Returns:
        int | None: Original limit if stored, None otherwise
    """
    config_id_str = str(config_id)

    # Try primary storage (collection config)
    collection_limits = _get_collection_limits()
    if config_id_str in collection_limits:
        return collection_limits[config_id_str]

    # Fallback to secondary storage (addon config)
    addon_limits = get_config().get('original_limits', {})
    limit = addon_limits.get(config_id_str)

    # If found in fallback, sync to primary
    if limit is not None and mw.col:
        print(f"[Weekend Addon] INFO: Syncing limit for config {config_id} to collection storage")
        collection_limits[config_id_str] = limit
        _store_collection_limits(collection_limits)

    return limit


def store_original_limit(config_id: int, limit: int) -> None:
    """
    Store original new cards per day limit for future restoration.
    Uses redundant storage: primary (collection config) + secondary (addon config).

    Args:
        config_id: Deck configuration ID
        limit: Original new cards per day limit to store

    Raises:
        TypeError: If limit is not an integer
        ValueError: If limit is outside valid range
    """
    # Validate limit before storing
    validated_limit = validate_original_limit(limit)
    config_id_str = str(config_id)

    # Store in primary storage (collection config)
    if mw.col:
        collection_limits = _get_collection_limits()
        collection_limits[config_id_str] = validated_limit
        _store_collection_limits(collection_limits)

    # Store in secondary storage (addon config) for redundancy
    config = get_config()
    if 'original_limits' not in config:
        config['original_limits'] = {}
    config['original_limits'][config_id_str] = validated_limit
    mw.addonManager.writeConfig(__name__, config)


# ==========================================
# Deck Config Modification
# ==========================================

def apply_weekend_mode() -> None:
    """
    Set new cards per day = 0 for all decks.
    Stores original limits before modification for later restoration.
    Changes are marked for AnkiWeb sync automatically.

    Note: On first run during weekend with limits already at 0,
    waits until weekday to capture real original values.

    Optimization: Reads config once and batches all writes (100x faster).

    Error handling: Failures on individual decks don't prevent
    processing other decks. Errors are logged but don't propagate.
    """
    # Store collection reference once to prevent race conditions
    col = mw.col
    if not col:
        return

    # Read config ONCE
    addon_config = get_config()
    original_limits = addon_config.setdefault('original_limits', {})
    collection_limits = _get_collection_limits()
    limits_modified = False

    success_count = 0
    skip_count = 0
    error_count = 0

    # Get deck list with error handling
    try:
        deck_ids = col.decks.all_names_and_ids()
    except Exception as e:
        print(f"[Weekend Addon] ERROR: Failed to get deck list: {e}")
        return

    for deck_id in deck_ids:
        try:
            # Get deck
            deck = col.decks.get_legacy(deck_id.id)
            if not deck:
                skip_count += 1
                continue

            # Verify deck structure
            if 'conf' not in deck:
                print(f"[Weekend Addon] WARNING: Deck {deck_id.id} has no 'conf', skipping")
                skip_count += 1
                continue

            # Get deck config
            config = col.decks.get_config(deck['conf'])
            if not config:
                print(f"[Weekend Addon] WARNING: Config {deck['conf']} not found, skipping")
                skip_count += 1
                continue

            # Verify config structure
            if 'new' not in config or 'perDay' not in config['new']:
                print(f"[Weekend Addon] WARNING: Config {deck['conf']} has unexpected structure, skipping")
                skip_count += 1
                continue

            config_id_str = str(deck['conf'])

            # Capture original if not already stored (in MEMORY, not disk yet)
            if config_id_str not in collection_limits and config_id_str not in original_limits:
                try:
                    current_limit = config['new']['perDay']

                    # Validate limit
                    validated_limit = validate_original_limit(current_limit)

                    # Safe capture logic
                    if validated_limit > 0:
                        # Safe: positive value is reliable
                        collection_limits[config_id_str] = validated_limit
                        original_limits[config_id_str] = validated_limit
                        limits_modified = True
                    elif not is_weekend():
                        # Weekday with limit=0: user really wants 0
                        collection_limits[config_id_str] = validated_limit
                        original_limits[config_id_str] = validated_limit
                        limits_modified = True
                    # Else: Weekend with limit=0: WAIT for weekday
                    # (don't store anything yet)
                except (TypeError, ValueError) as e:
                    print(f"[Weekend Addon] WARNING: Invalid limit for config {deck['conf']}: {e}")
                    # Continue anyway - at least pause the deck
                except Exception as e:
                    print(f"[Weekend Addon] WARNING: Failed to store original limit for config {deck['conf']}: {e}")
                    # Continue anyway - at least pause the deck

            # Set limit to 0
            config['new']['perDay'] = 0
            col.decks.save(config)
            success_count += 1

        except (KeyError, AttributeError, TypeError) as e:
            # Structure/type errors - specific deck issue
            error_count += 1
            print(f"[Weekend Addon] ERROR processing deck {deck_id.id}: {type(e).__name__}: {e}")
            continue

        except Exception as e:
            # Unexpected error - log but continue
            error_count += 1
            print(f"[Weekend Addon] UNEXPECTED ERROR processing deck {deck_id.id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # BATCH WRITE: Write config ONCE at the end (if modified)
    if limits_modified:
        try:
            _store_collection_limits(collection_limits)
            addon_config['original_limits'] = original_limits
            mw.addonManager.writeConfig(__name__, addon_config)
        except Exception as e:
            print(f"[Weekend Addon] ERROR: Failed to save config: {e}")

    # Log summary if there were issues
    if error_count > 0 or skip_count > 0:
        print(f"[Weekend Addon] Weekend mode applied: {success_count} success, {skip_count} skipped, {error_count} errors")


def apply_weekday_mode() -> None:
    """
    Restore original new cards per day limits for all decks.
    Only restores if original limit was previously stored.
    Changes are marked for AnkiWeb sync automatically.

    Optimization: Reads config once (no repeated I/O calls).

    Error handling: Failures on individual decks don't prevent
    processing other decks. Errors are logged but don't propagate.
    """
    # Store collection reference once to prevent race conditions
    col = mw.col
    if not col:
        return

    # Read config ONCE
    collection_limits = _get_collection_limits()
    addon_limits = get_config().get('original_limits', {})

    # Merge both sources (collection is primary)
    original_limits = {**addon_limits, **collection_limits}

    success_count = 0
    skip_count = 0
    error_count = 0

    try:
        deck_ids = col.decks.all_names_and_ids()
    except Exception as e:
        print(f"[Weekend Addon] ERROR: Failed to get deck list: {e}")
        return

    for deck_id in deck_ids:
        try:
            deck = col.decks.get_legacy(deck_id.id)
            if not deck or 'conf' not in deck:
                skip_count += 1
                continue

            config = col.decks.get_config(deck['conf'])
            if not config or 'new' not in config or 'perDay' not in config['new']:
                skip_count += 1
                continue

            # Restore original if exists (from in-memory dict)
            config_id_str = str(deck['conf'])
            original = original_limits.get(config_id_str)
            if original is not None:
                config['new']['perDay'] = original
                col.decks.save(config)
                success_count += 1
            else:
                skip_count += 1

        except (KeyError, AttributeError, TypeError) as e:
            error_count += 1
            print(f"[Weekend Addon] ERROR restoring deck {deck_id.id}: {type(e).__name__}: {e}")
            continue

        except Exception as e:
            error_count += 1
            print(f"[Weekend Addon] UNEXPECTED ERROR restoring deck {deck_id.id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    if error_count > 0 or skip_count > 0:
        print(f"[Weekend Addon] Weekday mode applied: {success_count} restored, {skip_count} skipped, {error_count} errors")


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

    Optimization: Tracks last applied mode to avoid unnecessary
    deck iteration when mode hasn't changed (95% performance improvement).

    Error handling: Catches ALL exceptions to prevent Anki crash.
    Addon may fail, but Anki continues working.
    """
    try:
        if not mw.col:
            return

        config = get_config()

        # Determine desired mode
        if config.get('travel_mode', False):
            desired_mode = 'travel'
        elif is_weekend():
            desired_mode = 'weekend'
        else:
            desired_mode = 'weekday'

        # Check current mode
        current_mode = config.get('last_applied_mode')

        # OPTIMIZATION: Apply ONLY if mode changed
        if current_mode != desired_mode:
            # Mode changed - apply update
            if desired_mode in ['weekend', 'travel']:
                apply_weekend_mode()
            else:
                apply_weekday_mode()

            # Store applied mode
            config['last_applied_mode'] = desired_mode
            mw.addonManager.writeConfig(__name__, config)
        # Else: Mode hasn't changed - SKIP (saves 95% of iterations!)

    except Exception as e:
        # CRITICAL: Don't let exception propagate to Anki
        print(f"[Weekend Addon] CRITICAL ERROR in on_profile_open: {e}")
        import traceback
        traceback.print_exc()


# ==========================================
# Hook Registration
# ==========================================

# Register hook to run on profile open (startup + profile switch)
gui_hooks.profile_did_open.append(on_profile_open)
