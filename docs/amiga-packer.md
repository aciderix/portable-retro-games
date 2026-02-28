# 🐱 Amiga Packer — Documentation

> `build_jimmy_willburne.py` / `build_short_grey.py` — Build self-contained, offline-playable Amiga game HTML files using the vAmigaWeb emulator.

---

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Build Scripts](#build-scripts)
- [vAmigaWeb Architecture](#vamigaweb-architecture)
- [Asset Inlining Strategy](#asset-inlining-strategy)
- [JavaScript Patching for Standalone Mode](#javascript-patching-for-standalone-mode)
- [IndexedDB Caching System](#indexeddb-caching-system)
- [Hardware Configuration](#hardware-configuration)
- [Loading Screen & Progress Bar](#loading-screen--progress-bar)
- [Virtual Joystick & Touch Controls](#virtual-joystick--touch-controls)
- [Generated HTML Structure](#generated-html-structure)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Amiga Packer is the most complex of the three packers. Unlike the Apple II and CPC packers which embed lightweight JavaScript emulators, the Amiga packer embeds a **full WebAssembly-compiled Amiga emulator** (vAmiga) along with:

- **Kickstart ROM** (512 KB)
- **Game ADF disk images** (880 KB each)
- **Full JS runtime** (emscripten-generated)
- **CSS, images, SVG sprites, sounds** (MP3 audio)
- **Custom patches** for standalone operation

The result is a large but completely self-contained HTML file that runs a real Amiga emulation in your browser — complete with custom hardware configuration, virtual joystick, and touch controls.

### Key Differences from Apple II / CPC Packers

| Aspect | Apple II / CPC | Amiga |
|---|---|---|
| Emulator type | Pure JavaScript | WebAssembly (WASM) |
| Emulator size | 150-400 KB | 2-5 MB |
| ROM requirements | Small (32 KB) | Kickstart ROM (512 KB) |
| Build approach | Automated CLI | Per-game build scripts |
| Asset count | 2-3 files | 20+ files (JS, CSS, images, sounds) |
| Patching needed | Minimal | Extensive JS patching |

---

## How It Works

### Build Process Overview

```
1. PREPARE SOURCE FILES
   └── Clone/checkout vAmigaWeb emulator source
   └── Gather game ADF disk images
   └── Gather Kickstart ROM

2. READ ALL ASSETS
   └── vAmiga WASM binary (~2-5 MB)
   └── vAmiga JavaScript glue code (~1 MB)
   └── Kickstart ROM binary (512 KB)
   └── Game ADF disks (880 KB each)
   └── UI JavaScript libraries
   └── CSS stylesheets
   └── SVG sprite sheets
   └── Image assets (PNG, JPEG)
   └── Sound effects (MP3)

3. ENCODE & INLINE EVERYTHING
   └── WASM → base64 string in <script>
   └── ROM → base64 string in <script>
   └── ADF → base64 string in <script>
   └── JS libraries → inline <script> blocks
   └── CSS → inline <style> blocks
   └── Images → base64 Data URIs
   └── SVG → inline <svg> elements
   └── Sounds → base64 Data URIs (audio/mpeg)

4. PATCH EMULATOR JAVASCRIPT
   └── Neutralize UI elements (menu bar, settings panel, etc.)
   └── Neutralize network fetch calls
   └── Redirect WASM loading to embedded data
   └── Redirect ROM loading to embedded data
   └── Auto-configure hardware settings
   └── Disable update checks and telemetry
   └── Inject Fetch/Worker interceptors

5. CONFIGURE HARDWARE
   └── Chipset: ECS Agnus
   └── Memory: 2 MB Chip RAM + 2 MB Fast RAM
   └── Floppy: DF0 loaded with game disk
   └── Joystick: Port 2 (mouse in Port 1)

6. ADD VIRTUAL CONTROLS
   └── Virtual joystick (left side)
   └── Fire buttons (right side)
   └── Touch-anywhere for fire
   └── Landscape orientation lock

7. ASSEMBLE FINAL HTML
   └── Single HTML file, all assets embedded
   └── Loading screen with progress bar
   └── Auto-boot on load
```

---

## Build Scripts

Unlike the Apple II and CPC packers which use a single generic script, the Amiga packer uses per-game build scripts. This is because each Amiga game may need specific patches, timing adjustments, or hardware configuration.

### Available Scripts

| Script | Game | Features |
|---|---|---|
| `build_jimmy_willburne.py` | Jimmy Willburne | Standard build, virtual joystick |
| `build_jimmy_willburne_cached.py` | Jimmy Willburne | + IndexedDB caching, loading screen |
| `build_short_grey.py` | Short Grey | Standard build |
| `build_short_grey_cached.py` | Short Grey | + IndexedDB caching, loading screen |

### Why Per-Game Scripts?

1. **JS patching specifics**: Different vAmigaWeb versions may need different patches
2. **Hardware tweaks**: Some games need specific timing or memory configurations
3. **Disk configurations**: Multi-disk games need custom swap logic
4. **Control mapping**: Different games use different joystick/keyboard combos
5. **Build complexity**: The build process has many game-specific decisions

---

## vAmigaWeb Architecture

### What is vAmigaWeb?

[vAmigaWeb](https://github.com/nicl83/vAmigaWeb) is a web port of the vAmiga emulator, compiled from C++ to WebAssembly using Emscripten. It provides accurate Amiga emulation in the browser.

### Technology Stack

```
┌──────────────────────────────────────────┐
│              Browser                      │
├──────────────────────────────────────────┤
│  JavaScript UI Layer                      │
│  ├── Canvas rendering (WebGL / 2D)       │
│  ├── Audio playback (Web Audio API)      │
│  ├── Input handling (keyboard/mouse)     │
│  └── File management (disks, ROMs)       │
├──────────────────────────────────────────┤
│  Emscripten Glue Code                    │
│  ├── Memory management                   │
│  ├── C++ ↔ JS bridge                    │
│  ├── File system emulation               │
│  └── Threading (Web Workers)             │
├──────────────────────────────────────────┤
│  vAmiga Core (WASM)                      │
│  ├── 68000 CPU emulation                 │
│  ├── Custom chips (Agnus, Denise, Paula) │
│  ├── CIA chips (timing, I/O)             │
│  ├── Blitter & Copper                    │
│  ├── Floppy disk controller              │
│  └── Audio (4-channel Paula)             │
└──────────────────────────────────────────┘
```

### WASM Compilation

The vAmiga C++ source is compiled to WebAssembly using Emscripten:

```bash
# Simplified compilation pipeline:
emcc vAmiga/*.cpp \
    -O3 \
    -s WASM=1 \
    -s ALLOW_MEMORY_GROWTH=1 \
    -s TOTAL_MEMORY=67108864 \     # 64 MB initial
    -s EXPORTED_FUNCTIONS=[...] \
    -o vAmiga.js                    # Produces vAmiga.js + vAmiga.wasm
```

The build outputs two critical files:
- **`vAmiga.js`** (~1 MB): Emscripten glue code + JavaScript API
- **`vAmiga.wasm`** (~2-5 MB): Compiled emulator core

Both are embedded directly into the output HTML.

---

## Asset Inlining Strategy

The Amiga packer must inline **every single asset** the emulator needs. Nothing can be loaded from external URLs.

### Asset Inventory

| Asset Type | Files | Encoding | Typical Size |
|---|---|---|---|
| WASM binary | `vAmiga.wasm` | Base64 in `<script>` | 2-5 MB |
| JS glue code | `vAmiga.js` | Inline `<script>` | ~1 MB |
| JS libraries | UI, controls, etc. | Inline `<script>` | ~200 KB |
| CSS | Stylesheets | Inline `<style>` | ~50 KB |
| Kickstart ROM | `kick.rom` | Base64 in `<script>` | 512 KB |
| Game disk(s) | `*.adf` | Base64 in `<script>` | 880 KB each |
| Images | PNG, JPEG | Base64 Data URI | ~100 KB |
| SVG sprites | Icons, UI elements | Inline `<svg>` | ~50 KB |
| Sound effects | MP3 files | Base64 Data URI | ~50-200 KB |

### Total File Size

A typical Amiga game HTML file is **5-10 MB** — much larger than Apple II (~500 KB) or CPC (~800 KB) outputs, but still reasonable for a complete Amiga emulation.

### Encoding Methods

#### WASM Binary

```javascript
// The WASM binary is stored as a base64 string
const WASM_BASE64 = "AGFzbQEAAAAB..."; // ~3-7 MB base64

// At runtime, decoded and instantiated:
const wasmBytes = Uint8Array.from(atob(WASM_BASE64), c => c.charCodeAt(0));
const wasmModule = await WebAssembly.compile(wasmBytes);
```

#### Kickstart ROM

```javascript
// ROM stored as base64
const KICKSTART_BASE64 = "AAAE8A..."; // ~680 KB base64

// Decoded and loaded into emulator memory:
const romData = Uint8Array.from(atob(KICKSTART_BASE64), c => c.charCodeAt(0));
emulator.loadROM(romData);
```

#### Game ADF Disks

```javascript
// ADF disk image(s) as base64
const DISK_DF0_BASE64 = "RE9TAA..."; // ~1.2 MB base64

// Decoded and inserted into virtual floppy drive:
const diskData = Uint8Array.from(atob(DISK_DF0_BASE64), c => c.charCodeAt(0));
emulator.insertDisk(0, diskData); // DF0:
```

#### Images and Sounds

```html
<!-- Images as Data URIs -->
<img src="data:image/png;base64,iVBORw0KGgo..." />

<!-- Sounds as Data URIs -->
<audio id="click-sound">
    <source src="data:audio/mpeg;base64,//uQxAAA..." type="audio/mpeg">
</audio>
```

#### Fetch/Worker Interceptors

To serve embedded data when the emulator tries to fetch external resources:

```javascript
// Override fetch() to intercept emulator resource requests
const originalFetch = window.fetch;
window.fetch = function(url, options) {
    // Intercept WASM file request
    if (url.endsWith('.wasm')) {
        const wasmBytes = base64ToBytes(WASM_BASE64);
        return Promise.resolve(new Response(wasmBytes, {
            headers: { 'Content-Type': 'application/wasm' }
        }));
    }

    // Intercept ROM file request
    if (url.endsWith('.rom') || url.endsWith('.bin')) {
        const romBytes = base64ToBytes(KICKSTART_BASE64);
        return Promise.resolve(new Response(romBytes));
    }

    // Pass through other requests (shouldn't happen in offline mode)
    return originalFetch(url, options);
};

// Override Web Worker creation for emulator threads
const originalWorker = window.Worker;
window.Worker = function(url) {
    // Create worker from inline script instead of external URL
    const workerCode = WORKER_JS_SOURCE; // Embedded worker code
    const blob = new Blob([workerCode], { type: 'application/javascript' });
    return new originalWorker(URL.createObjectURL(blob));
};
```

---

## JavaScript Patching for Standalone Mode

The vAmigaWeb emulator is designed to run as a full web application with menus, settings, file dialogs, etc. For standalone game packaging, we need to **patch the JavaScript** to:

### Patches Applied

#### 1. Neutralize UI Elements

```javascript
// Remove menu bar, settings panel, file dialogs
// Patch: Comment out or replace DOM creation code

// Before:
document.getElementById('menu-bar').style.display = 'block';
// After (patched):
// document.getElementById('menu-bar').style.display = 'block';
```

#### 2. Disable Network Requests

```javascript
// Prevent the emulator from fetching external resources
// All resources are already embedded

// Before:
fetch('/roms/kickstart.rom').then(...)
// After (patched):
Promise.resolve(new Response(base64ToBytes(KICKSTART_BASE64))).then(...)
```

#### 3. Auto-Configure Hardware

```javascript
// Instead of showing a configuration dialog, inject settings directly

// Patched into initialization:
emulator.configure({
    chipset: 'ECS',          // ECS Agnus
    chipRam: 2048,            // 2 MB Chip RAM
    fastRam: 2048,            // 2 MB Fast RAM
    floppyDrives: 1,          // DF0 only
    joystickPort2: 'joystick' // Joystick in port 2
});
```

#### 4. Redirect WASM Loading

```javascript
// The emulator normally loads WASM from a URL
// Patch to load from embedded base64

// Before:
WebAssembly.instantiateStreaming(fetch('vAmiga.wasm'), imports)
// After (patched):
const wasmBytes = base64ToBytes(WASM_BASE64);
WebAssembly.instantiate(wasmBytes, imports)
```

#### 5. Disable Update Checks

```javascript
// Remove any version checking or update notification code
// Not needed for standalone files
```

### Patching Strategy

The build script uses string replacement on the JavaScript source:

```python
# Simplified patching approach
js_source = open('vAmiga.js').read()

# Neutralize menu bar
js_source = js_source.replace(
    'document.getElementById("menu-bar")',
    'document.getElementById("__disabled_menu")'
)

# Redirect WASM loading
js_source = js_source.replace(
    'fetch(wasmUrl)',
    'Promise.resolve(new Response(wasmData))'
)

# Inject auto-configuration
js_source = js_source.replace(
    '// CONFIGURATION_HOOK',
    'emulator.configure({chipset:"ECS",chipRam:2048,fastRam:2048});'
)
```

---

## IndexedDB Caching System

The **cached** versions of the build scripts (`build_*_cached.py`) add an IndexedDB caching layer. This is important because Amiga HTML files can be 5-10 MB, and re-parsing all that base64 data on every page load is slow.

### How Caching Works

```
First Load:
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│   Open   │────▶│ Decode base64│────▶│ Store in     │────▶│  Boot    │
│   HTML   │     │ WASM, ROM,   │     │ IndexedDB    │     │ emulator │
│          │     │ Disks        │     │              │     │          │
└──────────┘     └──────────────┘     └──────────────┘     └──────────┘
                  (slow: 2-5 sec)      (one-time cost)

Subsequent Loads:
┌──────────┐     ┌──────────────┐     ┌──────────┐
│   Open   │────▶│ Load from    │────▶│  Boot    │
│   HTML   │     │ IndexedDB    │     │ emulator │
│          │     │ (fast!)      │     │          │
└──────────┘     └──────────────┘     └──────────┘
                  (fast: <1 sec)
```

### IndexedDB Schema

```javascript
const DB_NAME = 'vAmigaGameCache';
const DB_VERSION = 1;

// Object stores:
const stores = {
    'wasm':     // Compiled WebAssembly module
    'roms':     // Kickstart ROM binary
    'disks':    // ADF disk images
    'config':   // Hardware configuration
    'metadata': // Version info for cache invalidation
};
```

### Cache Invalidation

```javascript
// Each cached asset has a version hash
const CACHE_VERSION = 'v1.0.0-abc123';

// On load, check if cached version matches embedded version
const cachedVersion = await db.get('metadata', 'version');
if (cachedVersion !== CACHE_VERSION) {
    // Cache miss or version mismatch — rebuild cache
    await rebuildCache();
}
```

---

## Hardware Configuration

The Amiga packer configures the emulated hardware for maximum game compatibility:

### Default Configuration

| Component | Setting | Notes |
|---|---|---|
| **Chipset** | ECS Agnus | Enhanced Chip Set — compatible with 90%+ of games |
| **Chip RAM** | 2 MB | Maximum for ECS (many games need 1MB+) |
| **Fast RAM** | 2 MB | Additional memory for system overhead |
| **CPU** | 68000 @ 7.09 MHz | Standard Amiga 500 CPU (PAL) |
| **Floppy** | DF0: (game disk) | Single drive, ADF format |
| **Joystick** | Port 2 | Standard game port |
| **Mouse** | Port 1 | For Workbench / point-and-click games |
| **Video** | PAL 50Hz | European standard (most Amiga games are PAL) |
| **Audio** | 4-channel Paula | Full stereo sound |

### Why ECS + 2MB Chip RAM?

- **OCS (Original Chip Set)**: Too limited for many games
- **ECS (Enhanced Chip Set)**: Best balance of compatibility and features
- **AGA**: Not needed for classic games, higher emulation cost
- **2 MB Chip RAM**: Many demos and later games require it
- **2 MB Fast RAM**: Helps with system overhead and some games that check for it

---

## Loading Screen & Progress Bar

The cached versions include a custom loading screen that displays while the emulator initializes.

### Loading Sequence

```
┌─────────────────────────────────────────┐
│                                         │
│           🐱 Loading...                │
│                                         │
│   ████████████░░░░░░░░░  60%           │
│                                         │
│   Decoding WASM module...               │
│                                         │
└─────────────────────────────────────────┘
```

### Progress Stages

| Stage | Weight | Description |
|---|---|---|
| 1. Check cache | 5% | Query IndexedDB for cached data |
| 2. Decode WASM | 35% | Base64 decode → compile WASM module |
| 3. Decode ROM | 10% | Base64 decode Kickstart ROM |
| 4. Decode Disks | 15% | Base64 decode ADF disk images |
| 5. Initialize emulator | 20% | Boot WASM, configure hardware |
| 6. Insert disk & boot | 15% | Load disk, start Amiga boot |

### Implementation

```javascript
function updateProgress(stage, percent) {
    const progressBar = document.getElementById('progress-bar');
    const statusText = document.getElementById('status-text');

    const stages = [
        'Vérification du cache...',
        'Décodage du module WASM...',
        'Chargement de la ROM Kickstart...',
        'Chargement des disquettes...',
        'Initialisation de l\'émulateur...',
        'Démarrage du jeu...'
    ];

    progressBar.style.width = percent + '%';
    statusText.textContent = stages[stage];

    if (percent >= 100) {
        document.getElementById('loading-screen').style.display = 'none';
        document.getElementById('emulator-screen').style.display = 'block';
    }
}
```

---

## Virtual Joystick & Touch Controls

### Joystick Layout

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   ╭───────────╮                    ╭───────────╮    │
│   │           │                    │           │    │
│   │  VIRTUAL  │    [EMULATOR      │   FIRE    │    │
│   │ JOYSTICK  │     SCREEN]       │  BUTTON   │    │
│   │  (D-pad)  │                    │           │    │
│   │           │                    │           │    │
│   ╰───────────╯                    ╰───────────╯    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Touch Control Features

- **Virtual D-pad**: 8-directional joystick on the left side of screen
- **Fire button**: Large touch target on the right side
- **Touch-anywhere fire**: Tap the emulator screen to fire (configurable)
- **Multi-touch**: Move and fire simultaneously
- **Haptic feedback**: Vibration on button press (where supported)

### Implementation

```javascript
class VirtualJoystick {
    constructor(element) {
        this.element = element;
        this.centerX = 0;
        this.centerY = 0;
        this.active = false;

        element.addEventListener('touchstart', (e) => this.onStart(e));
        element.addEventListener('touchmove', (e) => this.onMove(e));
        element.addEventListener('touchend', (e) => this.onEnd(e));
    }

    onStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        this.centerX = touch.clientX;
        this.centerY = touch.clientY;
        this.active = true;
        this.resumeAudio(); // Chrome mobile audio fix
    }

    onMove(e) {
        if (!this.active) return;
        e.preventDefault();
        const touch = e.touches[0];
        const dx = touch.clientX - this.centerX;
        const dy = touch.clientY - this.centerY;

        // Convert to joystick directions
        const threshold = 20; // pixels
        emulator.setJoystick({
            up: dy < -threshold,
            down: dy > threshold,
            left: dx < -threshold,
            right: dx > threshold
        });
    }

    onEnd(e) {
        e.preventDefault();
        this.active = false;
        emulator.setJoystick({ up:false, down:false, left:false, right:false });
    }

    resumeAudio() {
        // Chrome requires AudioContext.resume() after user gesture
        if (audioContext && audioContext.state === 'suspended') {
            audioContext.resume();
        }
    }
}
```

---

## Generated HTML Structure

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1,
          maximum-scale=1, user-scalable=no">
    <title>Game Name — Amiga</title>

    <!-- All CSS inlined -->
    <style>
        /* Emulator display styles */
        /* Loading screen styles */
        /* Virtual joystick styles */
        /* Fullscreen & orientation handling */
    </style>
</head>
<body>
    <!-- Loading screen (cached version) -->
    <div id="loading-screen">
        <div class="logo">🐱</div>
        <div class="title">Loading Game Name...</div>
        <div class="progress-container">
            <div id="progress-bar"></div>
        </div>
        <div id="status-text">Initialisation...</div>
    </div>

    <!-- Emulator screen -->
    <div id="emulator-screen" style="display:none">
        <canvas id="amiga-canvas"></canvas>
    </div>

    <!-- Virtual joystick -->
    <div id="joystick-zone">
        <div id="joystick-base">
            <div id="joystick-knob"></div>
        </div>
    </div>

    <!-- Fire button -->
    <div id="fire-button">FIRE</div>

    <!-- SVG sprites (inlined) -->
    <svg style="display:none">
        <!-- UI icons, button graphics, etc. -->
    </svg>

    <!-- Embedded assets -->
    <script>
        const WASM_BASE64 = "...";        // ~3-7 MB
        const KICKSTART_BASE64 = "...";   // ~680 KB
        const DISK_DF0_BASE64 = "...";    // ~1.2 MB
        const WORKER_JS = "...";          // Worker source code
    </script>

    <!-- Sound effects (base64 Data URIs) -->
    <script>
        const SOUNDS = {
            click: "data:audio/mpeg;base64,...",
            insert: "data:audio/mpeg;base64,..."
        };
    </script>

    <!-- Patched vAmiga JavaScript -->
    <script>
        /* vAmiga.js — patched for standalone operation */
        /* All fetch() calls redirected to embedded data */
        /* UI elements neutralized */
        /* Hardware auto-configured */
    </script>

    <!-- UI JavaScript libraries (inlined) -->
    <script>/* UI library code */</script>

    <!-- Fetch/Worker interceptors -->
    <script>
        // Override fetch() for embedded resources
        // Override Worker() for inline workers
    </script>

    <!-- Boot logic -->
    <script>
        async function boot() {
            updateProgress(0, 0);

            // Check IndexedDB cache (cached version)
            const cached = await checkCache();

            if (cached) {
                // Fast path: load from cache
                await loadFromCache();
            } else {
                // Slow path: decode base64, store in cache
                await decodeAndCache();
            }

            // Initialize emulator
            updateProgress(4, 80);
            await initEmulator();

            // Insert disk and boot
            updateProgress(5, 90);
            emulator.insertDisk(0, diskData);
            emulator.powerOn();

            updateProgress(5, 100);
        }

        boot();
    </script>
</body>
</html>
```

---

## Troubleshooting

### Common Issues

#### Black screen / emulator doesn't start

- **WASM support**: Ensure the browser supports WebAssembly (all modern browsers do)
- **Memory**: The emulator needs ~64 MB of browser memory. Close other tabs if low on RAM.
- **Kickstart ROM**: Verify the ROM is correctly embedded (512 KB for Kickstart 1.3)

#### No sound

- **AudioContext**: Tap the screen or press a button to activate audio (Chrome/Safari requirement)
- **Volume**: Check browser tab isn't muted

#### Slow loading

- **First load**: Can take 2-5 seconds to decode base64 and compile WASM
- **Cached version**: Use `build_*_cached.py` for faster subsequent loads
- **Network**: No network is used — any slowness is purely local decoding

#### Virtual joystick not responding

- Ensure touch events are reaching the joystick zone
- Try fullscreen mode for better touch target areas
- Some games use mouse (Port 1) instead of joystick (Port 2)

#### Game crashes or shows Guru Meditation

- **Wrong Kickstart**: Some games require specific Kickstart versions (1.2, 1.3, 2.0)
- **Memory config**: Try adjusting Chip RAM / Fast RAM amounts
- **Disk issues**: Verify ADF disk image integrity

### File Size Estimates

| Component | Size |
|---|---|
| vAmiga WASM | 2-5 MB |
| vAmiga JS glue | ~1 MB |
| Kickstart ROM (base64) | ~680 KB |
| Game ADF (base64) | ~1.2 MB per disk |
| JS libraries | ~200 KB |
| CSS / HTML | ~50 KB |
| Images / SVG | ~100 KB |
| Sounds (MP3) | ~50-200 KB |
| **Total HTML file** | **5-10 MB** (typical) |

### Browser Compatibility

| Browser | Desktop | Mobile | Notes |
|---|---|---|---|
| Chrome | ✅ | ✅ | Best WASM performance |
| Firefox | ✅ | ✅ | Good performance |
| Safari | ✅ | ✅ | AudioContext gesture needed, WebGL may fallback to 2D |
| Edge | ✅ | ✅ | Chromium-based, same as Chrome |

---

*← Back to [README](../README.md)*
