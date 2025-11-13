"""
UI components for Weekend Addon v2.0
Simple menu for toggling travel mode and viewing status.
"""

from aqt import mw
from aqt.qt import QAction, QMenu
from aqt.utils import showInfo, tooltip
from .i18n import tr


# Global references for dynamic updates
_weekend_menu = None
_weekend_mode_action = None
_travel_mode_action = None


def create_menu() -> None:
    """
    Create the Weekend Addon menu in Anki's Tools menu.
    Updates dynamically to show weekend and travel mode status.
    """
    global _weekend_menu, _weekend_mode_action, _travel_mode_action

    if not mw:
        return

    # Get current mode status
    config = mw.addonManager.getConfig(__name__)
    weekend_mode = config.get('weekend_mode', True) if config else True
    travel_mode = config.get('travel_mode', False) if config else False

    # Create main menu (no icon in title)
    _weekend_menu = QMenu(tr('menu_title'), mw)

    # Update menu item text dynamically when shown
    def update_menu():
        config = mw.addonManager.getConfig(__name__)

        if _weekend_mode_action:
            weekend_mode = config.get('weekend_mode', True) if config else True
            icon = '✅' if weekend_mode else '❌'
            _weekend_mode_action.setText(f"{icon} {tr('menu_weekend_mode')}")

        if _travel_mode_action:
            travel_mode = config.get('travel_mode', False) if config else False
            icon = '✅' if travel_mode else '❌'
            _travel_mode_action.setText(f"{icon} {tr('menu_travel_mode')}")

    _weekend_menu.aboutToShow.connect(update_menu)

    # Add actions (weekend mode first, then travel mode)
    weekend_icon = '✅' if weekend_mode else '❌'
    _weekend_mode_action = add_action(_weekend_menu, f"{weekend_icon} {tr('menu_weekend_mode')}", toggle_weekend_mode)

    travel_icon = '✅' if travel_mode else '❌'
    _travel_mode_action = add_action(_weekend_menu, f"{travel_icon} {tr('menu_travel_mode')}", toggle_travel_mode)

    add_action(_weekend_menu, tr('menu_status'), show_status)

    # Add menu to Tools
    mw.form.menuTools.addMenu(_weekend_menu)


def add_action(menu: QMenu, text: str, callback) -> QAction:
    """
    Add an action to a menu.

    Args:
        menu: The menu to add the action to
        text: The action text
        callback: Function to call when action is triggered

    Returns:
        The created action
    """
    action = QAction(text, mw)
    action.triggered.connect(callback)
    menu.addAction(action)
    return action


def toggle_weekend_mode() -> None:
    """
    Toggle weekend mode on/off and apply changes immediately.
    """
    if not mw:
        return

    # Get current config
    config = mw.addonManager.getConfig(__name__)
    if not config:
        config = {}

    # Toggle weekend mode
    current = config.get('weekend_mode', True)
    config['weekend_mode'] = not current

    # Save config
    mw.addonManager.writeConfig(__name__, config)

    # Show feedback
    message = tr('weekend_enabled') if config['weekend_mode'] else tr('weekend_disabled')
    tooltip(message, period=4000)

    # Trigger immediate application by simulating profile open
    from . import on_profile_open
    on_profile_open()

    # Update menu item icon immediately
    if _weekend_mode_action:
        icon = '✅' if config['weekend_mode'] else '❌'
        _weekend_mode_action.setText(f"{icon} {tr('menu_weekend_mode')}")


def toggle_travel_mode() -> None:
    """
    Toggle travel mode on/off and apply changes immediately.
    """
    if not mw:
        return

    # Get current config
    config = mw.addonManager.getConfig(__name__)
    if not config:
        config = {}

    # Toggle travel mode
    current = config.get('travel_mode', False)
    config['travel_mode'] = not current

    # Save config
    mw.addonManager.writeConfig(__name__, config)

    # Show feedback
    message = tr('travel_enabled') if config['travel_mode'] else tr('travel_disabled')
    tooltip(message, period=4000)

    # Trigger immediate application by simulating profile open
    from . import on_profile_open
    on_profile_open()

    # Update menu item icon immediately
    if _travel_mode_action:
        icon = '✅' if config['travel_mode'] else '❌'
        _travel_mode_action.setText(f"{icon} {tr('menu_travel_mode')}")


def show_status() -> None:
    """
    Show current addon status in a dialog.
    """
    if not mw or not mw.col:
        showInfo(tr('please_open_profile'), title=tr('menu_title'))
        return

    # Get current config
    config = mw.addonManager.getConfig(__name__)
    if not config:
        config = {}

    weekend_mode = config.get('weekend_mode', True)
    travel_mode = config.get('travel_mode', False)
    last_mode = config.get('last_applied_mode', 'unknown')
    original_limits = config.get('original_limits', {})

    # Determine current day status
    from datetime import datetime
    weekday = datetime.now().weekday()
    day_keys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    current_day = tr(day_keys[weekday])
    is_weekend = weekday in [5, 6]  # Saturday or Sunday

    # Translate mode name
    mode_key = f'mode_{last_mode}' if last_mode else 'mode_unknown'
    mode_name = tr(mode_key)

    # Build status message
    status_lines = [
        f"<h3>{tr('status_title')}</h3>",
        tr('status_today').format(current_day),
        "",
        f"<b>Modo Fim de Semana:</b> {tr('status_enabled') if weekend_mode else tr('status_disabled')}",
        tr('status_travel_mode').format(tr('status_enabled') if travel_mode else tr('status_disabled')),
        tr('status_current_mode').format(mode_name),
        "",
        tr('status_behavior'),
    ]

    if not weekend_mode:
        status_lines.append('• Addon <b>desativado</b> - sem modificações automáticas')
    elif travel_mode:
        status_lines.append(tr('status_paused_travel'))
    elif is_weekend:
        status_lines.append(tr('status_paused_weekend'))
    else:
        status_lines.append(tr('status_active_weekday'))

    status_lines.extend([
        "",
        tr('status_stored_limits').format(len(original_limits)),
        "",
        tr('status_tip')
    ])

    message = "<br>".join(status_lines)
    showInfo(message, title=tr('menu_title'), textFormat="rich")


def reset_stored_limits() -> None:
    """
    Clear all stored original limits and force recapture on next mode change.
    Useful if limits were incorrectly captured during testing.
    """
    from aqt.utils import askUser

    if not mw or not mw.col:
        showInfo(tr('please_open_profile'), title=tr('menu_title'))
        return

    confirm = askUser(tr('reset_message'), title=tr('reset_title'))

    if not confirm:
        return

    # Clear addon config
    config = mw.addonManager.getConfig(__name__)
    if config:
        config['original_limits'] = {}
        config['last_applied_mode'] = None
        mw.addonManager.writeConfig(__name__, config)

    # Clear collection config
    try:
        mw.col.set_config("weekend_addon_original_limits", {})
        print("[Weekend Addon] Stored limits cleared successfully")
        tooltip(tr('reset_success'), period=4000)
    except Exception as e:
        print(f"[Weekend Addon] Error clearing collection config: {e}")
        showInfo(tr('reset_error').format(e), title=tr('menu_title'))
