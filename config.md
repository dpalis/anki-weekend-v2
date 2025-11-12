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
- GitHub Issues: https://github.com/yourusername/anki-weekend-addon
- AnkiWeb Reviews: Coming soon
