# 🍎 Apple II Packer — Documentation

> `pack_apple2_game_html.py` — Package Apple II disk images into self-contained, offline-playable HTML files.

---

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [CLI Usage](#cli-usage)
- [Command-Line Options](#command-line-options)
- [Supported Disk Formats](#supported-disk-formats)
- [DOS 3.3 Catalog Parsing](#dos-33-catalog-parsing)
- [Keyboard Auto-Detection](#keyboard-auto-detection)
- [Virtual Keyboard Layout](#virtual-keyboard-layout)
- [Supported Apple II Models](#supported-apple-ii-models)
- [Emulator Asset Management](#emulator-asset-management)
- [Generated HTML Structure](#generated-html-structure)
- [Example Games](#example-games)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Apple II Packer takes an Apple II disk image file and produces a single HTML file that:

1. Embeds the **[apple2js](https://github.com/whscullin/apple2js)** emulator (JavaScript)
2. Embeds the **game disk image** (base64-encoded)
3. Generates a **context-aware virtual keyboard** optimized for touch/mobile
4. **Auto-boots** the game using the `PR#6` command (slot 6 boot)
5. Includes a **French-localized help overlay** with keyboard shortcuts

The output file is completely self-contained — zero server dependency, zero internet requirement. Open it in any modern browser on any device.

---

## How It Works

### Step-by-Step Process

```
1. READ disk image
   └── Load .dsk / .do / .po / .nib / .woz file into memory

2. PARSE disk catalog
   └── Read DOS 3.3 catalog (Track 17, Sector 0)
   └── Extract file names, types, and sizes
   └── Identify game type from file list

3. DETECT keyboard needs
   └── Analyze file names for genre clues
   └── Text adventures → full letter grid
   └── Arcade games → arrow keys + action buttons
   └── Hybrid → combined layout

4. FETCH emulator assets
   └── Download apple2js JavaScript files (if not cached)
   └── Download Apple II ROM files (if not cached)
   └── Cache in ~/.apple2js_cache/

5. ENCODE game data
   └── Base64-encode the disk image
   └── Embed as JavaScript variable in HTML

6. GENERATE virtual keyboard
   └── Build HTML/CSS/JS for detected key layout
   └── Add touch event handlers
   └── Add AudioContext resume on first gesture

7. ASSEMBLE HTML
   └── Combine emulator + game data + keyboard + boot logic
   └── Add help overlay (French-localized)
   └── Write single .html file

8. OUTPUT
   └── GameName.html — ready to open in any browser
```

---

## CLI Usage

### Basic Usage

```bash
python pack_apple2_game_html.py <disk_image>
```

### Examples

```bash
# Pack a standard .dsk file
python pack_apple2_game_html.py Karateka.dsk

# Pack a nibble format image
python pack_apple2_game_html.py "Prince of Persia.nib"

# Specify the Apple II model
python pack_apple2_game_html.py --model apple2e "Oregon Trail.dsk"

# Specify output file name
python pack_apple2_game_html.py --output karateka_game.html Karateka.dsk
```

---

## Command-Line Options

| Option | Default | Description |
|---|---|---|
| `disk_image` | *(required)* | Path to the Apple II disk image file |
| `--model` | `apple2e` | Apple II model: `apple2`, `apple2plus`, `apple2e` |
| `--output` | `<game_name>.html` | Output HTML file path |
| `--no-keyboard` | `false` | Disable virtual keyboard generation |
| `--force-keys` | *(auto)* | Override key detection: `arrows`, `letters`, `full` |
| `--no-cache` | `false` | Re-download emulator assets (ignore cache) |
| `--lang` | `fr` | Help overlay language (`fr`, `en`) |

---

## Supported Disk Formats

### `.dsk` — Standard DOS 3.3 Disk Image

- **Size:** 143,360 bytes (140 KB)
- **Structure:** 35 tracks × 16 sectors × 256 bytes
- **Encoding:** Logical sector order (DOS 3.3)
- **Most common format** for Apple II software distribution

### `.do` — DOS-Ordered Disk Image

- Identical to `.dsk` in structure
- Explicit DOS 3.3 sector ordering
- Same 143,360-byte size

### `.po` — ProDOS-Ordered Disk Image

- **Size:** 143,360 bytes
- **Structure:** Same physical layout as `.dsk`
- **Encoding:** ProDOS sector interleaving
- Used for ProDOS-formatted disks

### `.nib` — Nibble Format

- **Size:** 232,960 bytes
- **Structure:** 35 tracks × 6,656 bytes per track
- **Encoding:** Raw disk nibble data (GCR-encoded)
- Preserves copy protection schemes
- Larger files, but more faithful to original media

### `.woz` — WOZ Format

- **Size:** Variable (typically 200-300 KB)
- **Structure:** Flux-level disk representation
- **Encoding:** Bit-stream with timing data
- **Most accurate** preservation format
- Supports quarter-track and cross-track sync
- Developed by the Apple II preservation community

---

## DOS 3.3 Catalog Parsing

The packer reads the DOS 3.3 disk catalog to understand what's on the disk. This information drives the keyboard auto-detection algorithm.

### Catalog Structure

```
Track 17, Sector 0 — VTOC (Volume Table of Contents)
├── Byte $01: Track of first catalog sector (usually $11 = Track 17)
├── Byte $02: Sector of first catalog sector
├── Byte $06: DOS release number
├── Byte $27: Number of sectors per track
├── Byte $34: Number of tracks per disk
└── Bytes $38-$3B: Sector bitmap

Track 17, Sectors 15→1 — Catalog Entries
├── Each sector contains 7 file entries (35 bytes each)
├── Byte $00: Track of first T/S list sector
├── Byte $01: Sector of first T/S list sector
├── Byte $02: File type and flags
│   ├── Bit 7: Locked flag
│   └── Bits 0-6: File type
│       ├── $00 = Text (T)
│       ├── $01 = Integer BASIC (I)
│       ├── $02 = Applesoft BASIC (A)
│       └── $04 = Binary (B)
├── Bytes $03-$20: File name (30 chars, high-ASCII, padded with $A0)
└── Bytes $21-$22: Sector count
```

### File Type Detection

The packer uses the catalog to classify games:

| File Types Found | Game Type | Keyboard Layout |
|---|---|---|
| Mostly Text (T) + Applesoft (A) | Text adventure | Full letter grid |
| Binary (B) only | Arcade / Action | Arrow keys + action |
| Mix of types | Hybrid | Combined layout |

---

## Keyboard Auto-Detection

The keyboard detection algorithm examines the disk contents to determine what virtual keyboard layout to generate.

### Detection Heuristics

```python
# Simplified detection logic:

1. Parse DOS 3.3 catalog → get file names and types

2. Check file names for genre keywords:
   - Text adventure indicators: "STORY", "TEXT", "ROOM", "NORTH",
     "SOUTH", "EAST", "WEST", "INVENTORY", "LOOK", "GET", "DROP"
   - Arcade indicators: "SHAPE", "SPRITE", "HIRES", "LORES",
     "PADDLE", "JOYSTICK", "SOUND"

3. Check file types:
   - High ratio of Text/Applesoft → text input expected
   - Mostly Binary → arcade controls expected

4. Final classification:
   - TEXT_ADVENTURE → letters + digits + common words
   - ARCADE → arrows + space + return + a few action keys
   - HYBRID → compact letter grid + arrow keys
```

### Override Detection

If auto-detection gets it wrong, override with:

```bash
python pack_apple2_game_html.py --force-keys full MyGame.dsk
```

---

## Virtual Keyboard Layout

The virtual keyboard is generated as inline HTML/CSS/JS within the output file. It's designed for mobile touch interaction.

### Layout Variants

#### Arrow Keys Layout (Arcade Games)

```
┌─────────────────────────────┐
│                             │
│         ┌─────┐             │
│         │  ▲  │             │
│    ┌────┼─────┼────┐       │
│    │ ◀  │     │ ▶  │       │
│    └────┼─────┼────┘       │
│         │  ▼  │             │
│         └─────┘             │
│                             │
│  [SPACE]  [RETURN]  [ESC]  │
│                             │
└─────────────────────────────┘
```

#### Letter Grid Layout (Text Adventures)

```
┌─────────────────────────────────────────┐
│  Q  W  E  R  T  Y  U  I  O  P         │
│   A  S  D  F  G  H  J  K  L           │
│    Z  X  C  V  B  N  M                 │
│                                         │
│  1  2  3  4  5  6  7  8  9  0          │
│                                         │
│  [SPACE]  [RETURN]  [DELETE]  [ESC]    │
└─────────────────────────────────────────┘
```

#### Full / Hybrid Layout

Combines arrow keys on the left with a compact letter grid on the right.

### Touch Handling

```javascript
// Key features of the touch system:
- touchstart → key down (with visual feedback)
- touchend → key up
- touchmove → track finger across keys (slide input)
- preventDefault() on all events → no scroll/zoom interference
- CSS touch-action: none → disable browser gestures
- AudioContext.resume() on first touch → Chrome mobile audio fix
```

---

## Supported Apple II Models

| Model | Flag | ROM | Notes |
|---|---|---|---|
| Apple II | `--model apple2` | Integer BASIC ROM | Original 1977 model, limited software compatibility |
| Apple II+ | `--model apple2plus` | Applesoft BASIC ROM | Most common early model, broad compatibility |
| Apple IIe | `--model apple2e` | Enhanced IIe ROM | **Default.** Best compatibility, 80-column support, full keyboard |

### Which Model to Choose?

- **Apple IIe** (default): Works with 95%+ of all Apple II software. Start here.
- **Apple II+**: For early software (pre-1983) that expects Integer BASIC or has II+ specific code.
- **Apple II**: Only for very early software or specific compatibility testing.

---

## Emulator Asset Management

### Cache Directory

The packer downloads apple2js emulator files on first run and caches them locally:

```
~/.apple2js_cache/
├── apple2js.js              # Main emulator JavaScript
├── apple2js-worker.js       # Web Worker for CPU emulation
├── apple2e.rom              # Apple IIe ROM
├── apple2plus.rom           # Apple II+ ROM
├── apple2.rom               # Original Apple II ROM
├── disk2.rom                # Disk II controller ROM
└── slot6_boot.rom           # Slot 6 boot ROM
```

### Cache Behavior

- **First run:** Downloads all required files from the apple2js project
- **Subsequent runs:** Uses cached files (fast, offline-capable)
- **Force refresh:** Use `--no-cache` to re-download everything
- **Cache location:** `~/.apple2js_cache/` (configurable via environment variable)

---

## Generated HTML Structure

The output HTML file has this internal structure:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1,
          maximum-scale=1, user-scalable=no">
    <title>Game Name — Apple II</title>
    <style>
        /* Emulator display styles */
        /* Virtual keyboard styles */
        /* Help overlay styles */
        /* Anti-zoom protections */
    </style>
</head>
<body>
    <!-- Emulator canvas -->
    <canvas id="screen"></canvas>

    <!-- Virtual keyboard (generated based on detection) -->
    <div id="virtual-keyboard">...</div>

    <!-- Help overlay (French-localized) -->
    <div id="help-overlay">
        <h2>Aide — Contrôles</h2>
        ...
    </div>

    <!-- Emulator JavaScript (apple2js) -->
    <script>/* apple2js engine inlined */</script>

    <!-- Game disk data -->
    <script>
        const DISK_IMAGE = "/* base64-encoded disk image */";
    </script>

    <!-- Boot logic -->
    <script>
        // Initialize emulator
        // Load disk image from base64
        // Auto-boot with PR#6
        // Set up virtual keyboard handlers
        // Resume AudioContext on first gesture
    </script>
</body>
</html>
```

### Auto-Boot Sequence

The emulator is configured to automatically boot from the disk:

```javascript
// PR#6 equivalent — boot from Disk II in slot 6
emulator.reset();
emulator.loadDisk(0, diskData);  // Insert disk in drive 1
emulator.type("PR#6\r");         // Type boot command
// Game starts automatically!
```

---

## Example Games

### Tested and Working

| Game | Year | Type | Disk Format | Keyboard Layout | Notes |
|---|---|---|---|---|---|
| Karateka | 1984 | Arcade/Fighter | `.dsk` | Arrows + action | Classic martial arts game |
| Prince of Persia | 1989 | Platformer | `.dsk` | Arrows + action | Rotoscoped animation |
| Oregon Trail | 1985 | Educational | `.dsk` | Letters + digits | Text input for choices |
| Zork I | 1980 | Text Adventure | `.dsk` | Full letters | Complete letter grid needed |
| Ultima IV | 1985 | RPG | `.dsk` | Full layout | Letters for commands + arrows |
| Lode Runner | 1983 | Platformer | `.dsk` | Arrows + keys | I/J/K/M for movement |
| Choplifter | 1982 | Arcade | `.dsk` | Arrows + action | Joystick-style controls |
| Castle Wolfenstein | 1981 | Action | `.dsk` | Arrows + action | Early stealth game |
| Robot Odyssey | 1984 | Puzzle | `.dsk` | Full layout | Complex key commands |
| Colossal Cave | 1976 | Text Adventure | `.dsk` | Full letters | The original text adventure |

---

## Troubleshooting

### Common Issues

#### Game doesn't boot

- **Check disk format**: Ensure the disk image is a valid Apple II format
- **Try different model**: Some games require specific hardware (`--model apple2plus`)
- **Verify disk integrity**: Try the disk image in a standalone emulator first

#### No sound

- **Chrome/Safari**: Audio requires a user gesture before playing. Tap the screen or press a virtual key to activate audio.
- **AudioContext**: The packer includes an automatic `AudioContext.resume()` on first touch/click

#### Virtual keyboard too small/large

- The keyboard adapts to screen size automatically
- On very small screens, keys may be compact — try landscape orientation

#### Emulator assets fail to download

- Check internet connection for first run
- Use `--no-cache` to force re-download
- Manually download files to `~/.apple2js_cache/`

#### Black screen after boot

- Some games need time to load from disk — wait 10-15 seconds
- Try the `PR#6` auto-boot may not work for all disks (some use slot 5 or other boot methods)

---

## Technical Notes

### File Size Estimates

| Component | Size |
|---|---|
| apple2js emulator | ~150-200 KB |
| Apple II ROM files | ~32 KB |
| Disk image (base64) | ~190 KB (.dsk) to ~310 KB (.nib) |
| Virtual keyboard | ~15-25 KB |
| Help overlay | ~5 KB |
| **Total HTML file** | **~400-550 KB** (typical) |

### Browser Compatibility

| Browser | Desktop | Mobile | Notes |
|---|---|---|---|
| Chrome | ✅ | ✅ | Full support |
| Firefox | ✅ | ✅ | Full support |
| Safari | ✅ | ✅ | AudioContext needs gesture |
| Edge | ✅ | ✅ | Full support |
| Opera | ✅ | ✅ | Full support |

---

*← Back to [README](../README.md)*
