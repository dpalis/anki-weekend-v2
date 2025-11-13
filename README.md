# Anki Weekend Addon v2.0

Pause new cards on weekends, keep reviews active.

## Features

- ✅ Automatically pause new cards on Saturday & Sunday
- ✅ Restore new cards on Monday
- ✅ Travel mode for extended pauses
- ✅ Cross-platform sync (works on iOS/Android)

## Installation

1. Download `.ankiaddon` file from releases
2. In Anki: Tools → Add-ons → Install from file
3. Select the downloaded `.ankiaddon` file
4. Restart Anki

## Usage

### Weekend Mode (Automatic)
- **Saturday & Sunday:** No new cards
- **Monday:** New cards resume automatically
- **Reviews:** Always available

### Travel Mode (Manual)
1. Tools → Add-ons → Weekend Addon → Config
2. Set `travel_mode: true`
3. Restart Anki
4. New cards paused until you manually disable travel mode

## Cross-Platform

This addon works seamlessly on both desktop and mobile:

1. **Desktop:** Addon modifies deck configuration
2. **Sync:** Changes upload to AnkiWeb automatically
3. **Mobile:** Receives configuration changes via sync
4. **Result:** Consistent behavior across all devices

**Requirement:** Make sure to sync regularly on all devices.

## Requirements

- Anki 2.1.50 or later
- AnkiWeb account (for cross-platform sync)

## Technical Details

- **Implementation:** Modifies deck configuration (`new cards per day` setting)
- **Sync Method:** Uses Anki's built-in sync via AnkiWeb
- **Storage:** Original limits stored in addon config for restoration
- **Code:** Simple, ~150 lines, well-documented

## Why v2.0?

Version 2.0 is a complete rewrite from scratch focused on:
- **Simplicity:** Single file, no over-engineering
- **Reliability:** Research-backed approach using deck configuration
- **Cross-platform:** Works on iOS/Android via sync (v1.0 was desktop-only)
- **Maintainability:** Clean code following best practices

## License

MIT

## Support

- **Issues:** https://github.com/yourusername/anki-weekend-addon/issues
- **Documentation:** See `config.md` for detailed configuration options
- **AnkiWeb:** Coming soon

## Contributing

Contributions welcome! Please open an issue first to discuss proposed changes.

## Acknowledgments

Built with research-backed best practices for Anki addon development.
