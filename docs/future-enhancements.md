# 🚀 Future Enhancements & Roadmap

> Ideas, plans, and possibilities for the evolution of portable-retro-games.

---

## Table of Contents

- [State Save/Load](#-state-saveload)
- [Performance Optimizations](#-performance-optimizations)
- [Unified CLI](#-unified-cli)
- [Batch Processing](#-batch-processing)
- [Web Catalog](#-web-catalog)
- [PWA Support](#-pwa-support)
- [Multiplayer](#-multiplayer)
- [Accessibility](#-accessibility)
- [More Platforms](#-more-platforms)
- [Save State Sharing](#-save-state-sharing)
- [Game Metadata](#-game-metadata)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Compression](#-compression)
- [Thumbnail Generation](#-thumbnail-generation)
- [Priority Matrix](#priority-matrix)

---

## 💾 State Save/Load

### Overview

Allow players to save their game progress and restore it later — essential for long games (RPGs, adventures) that weren't designed for modern "pick up and play" sessions.

### Implementation Plan

#### Save to localStorage / IndexedDB

```javascript
// Save emulator state snapshot
async function saveState(slot = 0) {
    const state = emulator.getState();  // Serialized emulator state
    const db = await openDB('GameSaves', 1);
    await db.put('saves', {
        slot: slot,
        state: state,
        timestamp: Date.now(),
        screenshot: captureScreenshot(), // Thumbnail for save menu
        gameName: GAME_NAME
    });
    showNotification('État sauvegardé ! / State saved!');
}

// Restore emulator state
async function loadState(slot = 0) {
    const db = await openDB('GameSaves', 1);
    const save = await db.get('saves', slot);
    if (save) {
        emulator.setState(save.state);
        showNotification('État restauré ! / State restored!');
    }
}
```

#### Export / Import Save Files

```javascript
// Export save as downloadable file
function exportSave(slot) {
    const save = getSaveData(slot);
    const blob = new Blob([JSON.stringify(save)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${GAME_NAME}_save_${slot}.json`;
    a.click();
}

// Import save from file
function importSave(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const save = JSON.parse(e.target.result);
        storeSaveData(save);
        showNotification('Sauvegarde importée ! / Save imported!');
    };
    reader.readAsText(file);
}
```

#### UI: Save Menu

```
┌─────────────────────────────────────┐
│         💾 Sauvegardes / Saves      │
│                                     │
│  ┌──────┐  Slot 1                   │
│  │ 📷   │  "Level 3 — Boss fight"  │
│  │ thumb│  28 fév 2026, 10:34      │
│  └──────┘  [Charger] [Supprimer]   │
│                                     │
│  ┌──────┐  Slot 2                   │
│  │ 📷   │  "Town — before dungeon" │
│  │ thumb│  27 fév 2026, 18:22      │
│  └──────┘  [Charger] [Supprimer]   │
│                                     │
│  ┌──────┐  Slot 3 — Vide / Empty   │
│  │      │                           │
│  │      │  [Sauvegarder ici]       │
│  └──────┘                           │
│                                     │
│  [Exporter tout] [Importer]        │
│  [Fermer]                           │
└─────────────────────────────────────┘
```

### Challenges

- **State size**: Emulator state can be large (1-10 MB depending on platform)
- **localStorage limits**: ~5-10 MB per origin; IndexedDB is better for large saves
- **Cross-browser**: IndexedDB API varies slightly across browsers
- **Emulator support**: Each emulator needs to expose save/restore state API

---

## ⚡ Performance Optimizations

### Lazy Base64 Decoding

Instead of decoding all base64 data at load time, decode on demand:

```javascript
// Current: decode everything at startup (slow)
const wasmBytes = base64ToBytes(WASM_BASE64); // 2-5 MB decode

// Proposed: decode lazily or in chunks
class LazyDecoder {
    constructor(base64String) {
        this.source = base64String;
        this.decoded = null;
    }

    async decode() {
        if (!this.decoded) {
            // Decode in chunks via Web Worker to avoid blocking UI
            this.decoded = await this.workerDecode(this.source);
        }
        return this.decoded;
    }
}
```

### Web Workers for Base64 Decoding

Move heavy decoding off the main thread:

```javascript
// Main thread
const decoder = new Worker(decoderBlobUrl);
decoder.postMessage({ data: WASM_BASE64 });
decoder.onmessage = (e) => {
    const wasmBytes = e.data;
    initEmulator(wasmBytes);
};

// Worker thread
self.onmessage = (e) => {
    const binary = atob(e.data.data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    self.postMessage(bytes, [bytes.buffer]); // Transfer buffer (zero-copy)
};
```

### Streaming WASM Compilation

Use `WebAssembly.compileStreaming()` with a Response object for faster WASM init:

```javascript
// Current: compile from ArrayBuffer
const module = await WebAssembly.compile(wasmBytes);

// Proposed: compile from streaming Response (faster, uses less memory)
const wasmBlob = new Blob([wasmBytes], { type: 'application/wasm' });
const wasmResponse = new Response(wasmBlob);
const module = await WebAssembly.compileStreaming(wasmResponse);
```

### Content Compression

Reduce HTML file sizes with embedded compression:

```javascript
// Embed data as compressed (gzip/brotli), decompress at runtime
const WASM_COMPRESSED = "H4sIAAAA..."; // gzip-compressed base64

async function decompress(compressedBase64) {
    const compressed = base64ToBytes(compressedBase64);
    const ds = new DecompressionStream('gzip');
    const reader = new Response(
        new Blob([compressed]).stream().pipeThrough(ds)
    ).arrayBuffer();
    return new Uint8Array(await reader);
}
```

**Estimated savings:**

| Asset | Original | Compressed | Savings |
|---|---|---|---|
| WASM binary | 5 MB | ~2 MB | 60% |
| Disk image | 880 KB | ~400 KB | 55% |
| Kickstart ROM | 512 KB | ~300 KB | 40% |

---

## 🔧 Unified CLI

### Overview

Replace the three separate scripts with a single unified command-line tool:

```bash
# Instead of:
python pack_apple2_game_html.py Karateka.dsk
python pack_cpc_game_html.py Gryzor.dsk
python build_jimmy_willburne.py

# Use:
retro-pack apple2 Karateka.dsk
retro-pack cpc Gryzor.dsk
retro-pack amiga game.adf
```

### Proposed CLI Design

```bash
retro-pack <platform> <input> [options]

Platforms:
  apple2    Apple II (.dsk, .do, .po, .nib, .woz)
  cpc       Amstrad CPC (.dsk)
  amiga     Commodore Amiga (.adf)

Common options:
  -o, --output <file>     Output HTML file path
  -k, --keys <layout>     Force keyboard layout
  --no-keyboard           Disable virtual keyboard
  --lang <code>           Help overlay language (fr/en)
  -v, --verbose           Verbose output
  --no-cache              Re-download emulator assets

Platform-specific options:
  --model <model>         Apple II model (apple2/apple2plus/apple2e)
  --warp                  CPC warp-speed loading
  --warp-duration <sec>   CPC warp duration
  --run <command>         CPC boot command override
  --cached                Amiga: enable IndexedDB caching
```

### Architecture

```python
# retro_pack/
# ├── __init__.py
# ├── cli.py              # Unified CLI entry point
# ├── packers/
# │   ├── __init__.py
# │   ├── base.py          # BasePacker abstract class
# │   ├── apple2.py        # Apple II packer
# │   ├── cpc.py           # CPC packer
# │   └── amiga.py         # Amiga packer
# ├── analyzers/
# │   ├── __init__.py
# │   ├── dos33.py         # DOS 3.3 catalog parser
# │   ├── amsdos.py        # AMSDOS directory parser
# │   └── keyboard.py      # Key detection engine
# ├── generators/
# │   ├── __init__.py
# │   ├── keyboard.py      # Virtual keyboard HTML generator
# │   └── html.py          # HTML assembly engine
# └── assets/
#     ├── cache.py          # Asset download & cache manager
#     └── encoder.py        # Base64 encoding utilities
```

---

## 📦 Batch Processing

### Overview

Convert entire ROM libraries in one command:

```bash
# Convert all CPC games in a directory
retro-pack batch cpc ./cpc-games/ --output ./html-games/

# Convert with specific settings
retro-pack batch cpc ./cpc-games/ --warp --output ./html-games/

# Convert multiple platforms
retro-pack batch auto ./mixed-roms/ --output ./html-games/
# (auto-detect platform from file extension)
```

### Features

- **Parallel processing**: Convert multiple games simultaneously
- **Error handling**: Continue on failure, generate report
- **Progress tracking**: Show progress bar for large libraries
- **Deduplication**: Skip already-converted games (check modification time)
- **Summary report**: Generate `conversion-report.json` with results

### Example Report

```json
{
    "total": 132,
    "success": 130,
    "failed": 2,
    "skipped": 0,
    "totalSize": "98.5 MB",
    "duration": "3m 42s",
    "results": [
        { "game": "Gryzor.dsk", "status": "ok", "output": "Gryzor.html", "size": "780 KB" },
        { "game": "Corrupted.dsk", "status": "error", "error": "Invalid DSK format" }
    ]
}
```

---

## 🌐 Web Catalog

### Overview

Generate a static website that serves as a browsable catalog for your retro game collection.

### Concept

```
┌─────────────────────────────────────────────────────┐
│  🕹️ Ma Collection Rétro / My Retro Collection      │
│                                                     │
│  [🔍 Rechercher / Search...]  [Filtres ▼]          │
│                                                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ 📷      │  │ 📷      │  │ 📷      │            │
│  │ thumb   │  │ thumb   │  │ thumb   │            │
│  │         │  │         │  │         │            │
│  │Karateka │  │ Gryzor  │  │ R-Type  │            │
│  │Apple II │  │ CPC     │  │ CPC     │            │
│  │ [Jouer] │  │ [Jouer] │  │ [Jouer] │            │
│  └─────────┘  └─────────┘  └─────────┘            │
│                                                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ 📷      │  │ 📷      │  │ 📷      │            │
│  ...                                                │
└─────────────────────────────────────────────────────┘
```

### Features

- **Static site**: No server needed — just HTML/CSS/JS files
- **Search**: Full-text search across game names and metadata
- **Filters**: By platform, genre, year, publisher
- **Thumbnails**: Auto-generated screenshots (see Thumbnail Generation)
- **Inline player**: Open games in an iframe without leaving the catalog
- **Responsive**: Works on mobile and desktop
- **Offline**: Service Worker for offline catalog browsing (see PWA Support)

### Generation

```bash
retro-pack catalog generate \
    --games ./html-games/ \
    --output ./catalog/ \
    --title "Ma Collection Rétro" \
    --theme dark
```

---

## 📲 PWA Support

### Overview

Add Progressive Web App capabilities to make game collections installable on home screens.

### Service Worker

```javascript
// sw.js — cache game HTML files for offline access
const CACHE_NAME = 'retro-games-v1';

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll([
                '/',
                '/index.html',
                '/games/Karateka.html',
                '/games/Gryzor.html',
                // ... all game files
            ]);
        })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});
```

### Web App Manifest

```json
{
    "name": "Ma Collection Rétro",
    "short_name": "Rétro Games",
    "start_url": "/",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#000000",
    "theme_color": "#007AFF",
    "icons": [
        { "src": "/icon-192.png", "sizes": "192x192" },
        { "src": "/icon-512.png", "sizes": "512x512" }
    ]
}
```

### Benefits

- **Install to home screen**: Looks and feels like a native app
- **Offline access**: All games available without internet
- **Full-screen**: No browser chrome in standalone mode
- **Auto-updates**: Service Worker handles cache updates

---

## 🎮 Multiplayer

### Overview

Enable local network multiplayer using WebRTC for games that support two players.

### Architecture

```
┌──────────────┐    WebRTC     ┌──────────────┐
│   Player 1   │◀────────────▶│   Player 2   │
│              │   Data        │              │
│  Emulator    │   Channel     │  Emulator    │
│  (host)      │               │  (guest)     │
│              │               │              │
│  Joystick 1  │               │  Joystick 2  │
└──────────────┘               └──────────────┘
```

### How It Would Work

1. **Host** opens game and creates a room (generates room code)
2. **Guest** opens same game and enters room code
3. WebRTC peer connection established
4. Guest's joystick inputs are sent to host's emulator
5. Host's emulator renders both players
6. Host streams video/audio to guest (or guest runs own emulator synced via input)

### Challenges

- **Latency**: Real-time input over network needs low latency
- **Sync**: Keeping two emulators in sync is extremely difficult
- **Signaling**: Need a signaling server for WebRTC connection setup
- **NAT traversal**: STUN/TURN servers for firewalled users

---

## ♿ Accessibility

### Overview

Make retro games more accessible to players with disabilities.

### Planned Features

#### Screen Reader Support

```html
<!-- Live region for game state changes -->
<div id="game-status" role="status" aria-live="polite">
    Score: 1500 | Lives: 3 | Level: 2
</div>

<!-- Accessible virtual keyboard -->
<button class="vk-key" role="button" aria-label="Arrow Up" tabindex="0">▲</button>
```

#### Remappable Controls

```javascript
// Allow custom key bindings
const keyMap = {
    'ArrowUp':    'joystick_up',
    'ArrowDown':  'joystick_down',
    'ArrowLeft':  'joystick_left',
    'ArrowRight': 'joystick_right',
    'Space':      'fire',
    'KeyZ':       'fire',     // Alternative fire
    'KeyX':       'fire2',
};

// UI for remapping
function showRemapDialog() { /* ... */ }
```

#### High Contrast Mode

```css
/* High contrast theme for virtual keyboard */
.high-contrast .vk-key {
    background: #000;
    color: #fff;
    border: 3px solid #fff;
    font-size: 18px;
    font-weight: bold;
}

.high-contrast .vk-key.active {
    background: #fff;
    color: #000;
}
```

#### Additional Features

- **Slow motion**: Adjustable emulation speed for games that require fast reflexes
- **Large touch targets**: Option for extra-large keyboard buttons
- **Colorblind modes**: Palette adjustments for common forms of color blindness
- **Audio descriptions**: Optional narration of on-screen events (for supported games)

---

## 🖥️ More Platforms

### Planned Platform Support

| Platform | Emulator | Format | Priority | Notes |
|---|---|---|---|---|
| **Commodore 64** | [VICE.js](https://nicl83.github.io/nicl83-js/) | `.d64`, `.t64`, `.prg` | 🔴 High | Huge game library, active JS emulator |
| **ZX Spectrum** | [JSSpeccy](https://github.com/nicl83/nicl83) | `.tap`, `.tzx`, `.z80` | 🔴 High | Classic British micro, many games |
| **DOS** | [js-dos](https://js-dos.com/) | `.exe`, `.com`, `.zip` | 🟡 Medium | Massive library, complex config |
| **NES** | [JSNES](https://github.com/nicl83/nicl83) | `.nes` | 🟡 Medium | Simple format, huge library |
| **SNES** | [bsnes-web](https://nicl83.github.io/) | `.sfc`, `.smc` | 🟡 Medium | 16-bit classic |
| **Game Boy** | [GameBoy-Online](https://nicl83.github.io/) | `.gb`, `.gbc` | 🟢 Low | Portable games |
| **Atari 2600** | [Javatari](https://javatari.org/) | `.a26`, `.bin` | 🟢 Low | Simple ROMs |
| **MSX** | [WebMSX](https://webmsx.org/) | `.rom`, `.dsk` | 🟢 Low | Popular in Japan/Europe |
| **Atari ST** | [Hatari.js](https://nicl83.github.io/) | `.st`, `.stx` | 🟢 Low | Amiga's rival |
| **Thomson MO/TO** | [DCMOTO.js](https://dcmoto.free.fr/) | `.fd`, `.k7` | 🟢 Low | French computers! 🇫🇷 |

### Platform Addition Checklist

For each new platform, the packer needs:

1. [ ] Disk/ROM format parser
2. [ ] JavaScript or WASM emulator (MIT/GPL compatible)
3. [ ] Key detection algorithm (or joystick default)
4. [ ] Virtual keyboard layout
5. [ ] Boot command detection
6. [ ] Asset fetching and caching
7. [ ] HTML assembly template
8. [ ] Test suite with 10+ games

---

## 📤 Save State Sharing

### Overview

Share game states via QR codes for quick multiplayer or challenge sharing.

### How It Works

```
Player A saves state
        │
        ▼
Compress state data (LZMA)
        │
        ▼
Encode as URL-safe base64
        │
        ▼
Generate QR code
        │
        ▼
Player B scans QR code
        │
        ▼
Decode + decompress state
        │
        ▼
Load state in emulator
```

### Implementation

```javascript
// Generate QR code for save state
async function shareState() {
    const state = emulator.getState();
    const compressed = await compress(state);  // LZMA
    const encoded = base64UrlEncode(compressed);

    // If small enough for QR code (<3KB after compression)
    if (encoded.length < 3000) {
        const qrUrl = `${location.href}#state=${encoded}`;
        showQRCode(qrUrl);
    } else {
        // Too large for QR — offer file download instead
        offerDownload(compressed);
    }
}

// On page load, check for shared state in URL hash
if (location.hash.startsWith('#state=')) {
    const encoded = location.hash.slice(7);
    const compressed = base64UrlDecode(encoded);
    const state = await decompress(compressed);
    emulator.setState(state);
}
```

### Use Cases

- **Challenge sharing**: "Beat my high score starting from this point!"
- **Puzzle solutions**: Share specific game states for walkthroughs
- **Bug reports**: Reproduce exact game situations

---

## 📊 Game Metadata

### Overview

Automatically enrich game files with metadata from online databases.

### Data Sources

| Source | Data Provided | API |
|---|---|---|
| [MobyGames](https://www.mobygames.com/) | Title, year, publisher, genre, screenshots | REST API |
| [IGDB](https://www.igdb.com/) | Title, year, genre, rating, covers | REST API |
| [CPCWiki](https://www.cpcwiki.eu/) | CPC-specific: publisher, type, year | Scraping |
| [Asimov](https://mirrors.apple2.org.za/) | Apple II-specific: author, year, type | FTP listing |

### Metadata Schema

```json
{
    "title": "Gryzor",
    "alternateTitle": "Contra",
    "platform": "Amstrad CPC",
    "year": 1987,
    "publisher": "Ocean Software",
    "developer": "Ocean Software",
    "genre": ["Action", "Platformer", "Run and Gun"],
    "players": 1,
    "language": "en",
    "rating": 4.2,
    "description": "Side-scrolling action game...",
    "coverArt": "data:image/jpeg;base64,...",
    "screenshots": ["data:image/png;base64,..."],
    "controls": "joystick",
    "fileSize": "780 KB",
    "originalMedia": "3\" floppy disk",
    "preservationSource": "Original disk dump"
}
```

### Usage

```bash
# Enrich a game with metadata
retro-pack metadata enrich Gryzor.html --source mobygames

# Batch enrich all games
retro-pack metadata enrich-all ./html-games/ --source igdb,mobygames
```

---

## 🔄 CI/CD Pipeline

### Overview

Automate game library building with GitHub Actions.

### GitHub Actions Workflow

```yaml
# .github/workflows/build-games.yml
name: Build Game Library

on:
  push:
    paths:
      - 'games/**'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Build Apple II games
        run: |
          for disk in games/apple2/*.dsk; do
            python pack_apple2_game_html.py "$disk" -o "dist/apple2/$(basename "${disk%.dsk}.html")"
          done

      - name: Build CPC games
        run: |
          for disk in games/cpc/*.dsk; do
            python pack_cpc_game_html.py --warp "$disk" -o "dist/cpc/$(basename "${disk%.dsk}.html")"
          done

      - name: Generate catalog
        run: python generate_catalog.py dist/ -o dist/index.html

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
```

### Benefits

- **Automatic rebuilds**: Push a new ROM, get an updated HTML automatically
- **Consistent output**: Same build environment every time
- **GitHub Pages**: Free hosting for the game catalog
- **Version tracking**: Git history tracks all changes to the game library

---

## 🗜️ Compression

### Overview

Reduce generated HTML file sizes using modern compression algorithms.

### Approaches

#### 1. Built-in Browser Decompression (DecompressionStream API)

```javascript
// Use the browser's built-in gzip decompression
async function decompressGzip(compressedBytes) {
    const ds = new DecompressionStream('gzip');
    const blob = new Blob([compressedBytes]);
    const stream = blob.stream().pipeThrough(ds);
    return new Uint8Array(await new Response(stream).arrayBuffer());
}
```

**Browser support:** Chrome 80+, Firefox 113+, Safari 16.4+

#### 2. LZMA/LZMA2 (via JavaScript library)

```javascript
// Higher compression ratio than gzip
// ~5KB JS decoder library needed
const decompressed = LZMA.decompress(compressedData);
```

#### 3. Brotli (server-side only, or pre-decoded)

Brotli provides the best compression ratio but doesn't have a browser-native decompression API. Can be used server-side with `Content-Encoding: br`.

### Expected File Size Reductions

| Platform | Uncompressed | gzip | LZMA | Savings |
|---|---|---|---|---|
| Apple II | 500 KB | 320 KB | 280 KB | 36-44% |
| CPC | 800 KB | 500 KB | 420 KB | 38-48% |
| Amiga | 8 MB | 4.5 MB | 3.5 MB | 44-56% |

---

## 📸 Thumbnail Generation

### Overview

Automatically capture game screenshots for use in catalogs, save states, and metadata.

### Approach

Use headless browser (Puppeteer/Playwright) to:

1. Open the generated HTML file
2. Wait for the emulator to boot
3. Wait N seconds for the game to reach a recognizable screen
4. Capture a screenshot
5. Resize and optimize for thumbnails

### Implementation

```python
from playwright.sync_api import sync_playwright

def capture_thumbnail(html_path, output_path, wait_seconds=10):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 800, 'height': 600})

        # Open the game HTML
        page.goto(f'file://{html_path}')

        # Wait for emulator to boot and game to load
        page.wait_for_timeout(wait_seconds * 1000)

        # Capture screenshot of the emulator canvas
        canvas = page.locator('canvas').first
        canvas.screenshot(path=output_path)

        browser.close()

    # Resize to thumbnail (300x225)
    from PIL import Image
    img = Image.open(output_path)
    img.thumbnail((300, 225))
    img.save(output_path, optimize=True, quality=85)
```

### Usage

```bash
# Generate thumbnails for all games
retro-pack thumbnails generate ./html-games/ --output ./thumbnails/ --wait 15

# Generate thumbnail for a single game
retro-pack thumbnails generate Gryzor.html --output gryzor-thumb.png --wait 10
```

---

## Priority Matrix

### Impact vs Effort

```
                        HIGH IMPACT
                            │
        Unified CLI  ●      │      ● State Save/Load
                            │
        Compression  ●      │      ● More Platforms
                            │
   ─────────────────────────┼─────────────────────────
        LOW EFFORT          │              HIGH EFFORT
                            │
  Batch Processing  ●       │      ● Web Catalog
                            │
     Thumbnails  ●          │      ● PWA Support
                            │
                        LOW IMPACT
```

### Recommended Implementation Order

| Phase | Features | Rationale |
|---|---|---|
| **Phase 1** (v1.1) | Unified CLI, Batch Processing, Compression | Core usability improvements |
| **Phase 2** (v1.2) | State Save/Load, Thumbnails | Player experience enhancements |
| **Phase 3** (v2.0) | More Platforms (C64, Spectrum), Web Catalog | Expand platform coverage |
| **Phase 4** (v2.1) | PWA Support, Game Metadata, CI/CD | Distribution and automation |
| **Phase 5** (v3.0) | Accessibility, Multiplayer, Save Sharing | Advanced features |

---

*← Back to [README](../README.md)*
