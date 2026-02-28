# 🏗️ Technical Architecture

> Deep-dive into the common patterns, embedding strategies, and mobile techniques used across all portable-retro-games tools.

---

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Common Patterns Across Packers](#common-patterns-across-packers)
- [Embedding Strategy](#embedding-strategy)
- [Virtual Keyboard System](#virtual-keyboard-system)
- [Emulator Integration Patterns](#emulator-integration-patterns)
- [Mobile Compatibility Techniques](#mobile-compatibility-techniques)
- [Security Considerations](#security-considerations)
- [Performance Analysis](#performance-analysis)

---

## High-Level Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         portable-retro-games                                │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                        INPUT LAYER                                 │  │
│  │                                                                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │  │
│  │  │ Apple II  │  │ CPC DSK  │  │ Amiga    │  │ Emulator Assets  │  │  │
│  │  │ .dsk .woz │  │ .dsk     │  │ .adf     │  │ JS/WASM/ROM      │  │  │
│  │  │ .nib .do  │  │ .edsk    │  │          │  │                  │  │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │  │
│  └───────┼──────────────┼──────────────┼─────────────────┼────────────┘  │
│          ▼              ▼              ▼                 ▼                │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                     PROCESSING LAYER                               │  │
│  │                                                                    │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐    │  │
│  │  │ Disk Parser  │  │ Key Detector │  │ Asset Manager         │    │  │
│  │  │              │  │              │  │                       │    │  │
│  │  │ • DOS 3.3    │  │ • File name  │  │ • Download emulator   │    │  │
│  │  │ • AMSDOS     │  │   heuristics │  │ • Cache locally       │    │  │
│  │  │ • ADF        │  │ • BASIC scan │  │ • Base64 encode       │    │  │
│  │  │              │  │ • Z80 binary │  │ • Inline into HTML    │    │  │
│  │  │ Outputs:     │  │   analysis   │  │                       │    │  │
│  │  │ • File list  │  │ • Firmware   │  │ Outputs:              │    │  │
│  │  │ • Boot cmd   │  │   call scan  │  │ • Encoded assets      │    │  │
│  │  │ • Game type  │  │              │  │ • Fetch interceptors   │    │  │
│  │  └─────────────┘  │ Outputs:     │  └───────────────────────┘    │  │
│  │                    │ • Key layout │                                │  │
│  │                    │ • Key map    │                                │  │
│  │                    └──────────────┘                                │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│          │              │              │                 │                │
│          ▼              ▼              ▼                 ▼                │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                      OUTPUT LAYER                                  │  │
│  │                                                                    │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │                   SINGLE HTML FILE                           │  │  │
│  │  │                                                              │  │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │  │  │
│  │  │  │ Emulator │ │ Game     │ │ Virtual  │ │ Boot Logic   │  │  │  │
│  │  │  │ Engine   │ │ Data     │ │ Keyboard │ │ + Helpers    │  │  │  │
│  │  │  │ (JS/WASM)│ │ (base64) │ │ (HTML/   │ │ + Intercepts │  │  │  │
│  │  │  │          │ │          │ │  CSS/JS) │ │              │  │  │  │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
                    ┌─────────────┐
                    │  Disk Image │
                    │  (.dsk/.adf)│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Parse &   │
                    │   Analyze   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌──▼───┐ ┌─────▼─────┐
       │  Detect Key │ │ Find │ │  Encode   │
       │  Layout     │ │ Boot │ │  All Data │
       │             │ │ Cmd  │ │  base64   │
       └──────┬──────┘ └──┬───┘ └─────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │  Assemble   │
                    │  HTML File  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Output:    │
                    │  game.html  │
                    │  (offline)  │
                    └─────────────┘
```

---

## Common Patterns Across Packers

Despite targeting different platforms, all three packers share fundamental patterns:

### 1. Disk Image Parsing

Every packer starts by reading and understanding the disk format:

| Packer | Format | Key Information Extracted |
|---|---|---|
| Apple II | DOS 3.3 catalog | File names, types, sizes → genre detection |
| CPC | AMSDOS directory | File names, types, load addresses → boot command |
| Amiga | ADF structure | Filesystem → disk is treated as opaque blob |

### 2. Content Analysis for Key Detection

Each packer analyzes game content to determine input requirements:

```
Apple II:  File names in catalog → genre keywords → key layout
CPC:       BASIC tokens + Z80 firmware calls → input method detection
Amiga:     Assumed joystick (most Amiga games) → virtual joystick
```

### 3. Emulator Asset Fetching & Caching

```python
# Common pattern across all packers:

def get_emulator_assets(cache_dir, urls):
    """Download and cache emulator files."""
    os.makedirs(cache_dir, exist_ok=True)

    for filename, url in urls.items():
        cached_path = os.path.join(cache_dir, filename)
        if not os.path.exists(cached_path):
            print(f"Downloading {filename}...")
            response = requests.get(url)
            with open(cached_path, 'wb') as f:
                f.write(response.content)

    return cache_dir
```

### 4. Base64 Encoding & Embedding

All binary data is base64-encoded for embedding in HTML:

```python
import base64

def embed_binary(data: bytes, var_name: str) -> str:
    """Convert binary data to a JS variable with base64 content."""
    b64 = base64.b64encode(data).decode('ascii')
    return f'const {var_name} = "{b64}";'
```

### 5. Single-File Assembly

The final assembly follows the same pattern:

```python
html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1,
          maximum-scale=1, user-scalable=no">
    <title>{game_name} — {platform}</title>
    <style>{css}</style>
</head>
<body>
    {emulator_canvas}
    {virtual_keyboard}
    {help_overlay}
    <script>{emulator_js}</script>
    <script>{game_data_js}</script>
    <script>{boot_logic_js}</script>
</body>
</html>"""
```

---

## Embedding Strategy

### Binary Data Encoding

Three encoding methods are used depending on context:

#### 1. Base64 in JavaScript Variables

**Used for:** WASM binaries, ROMs, disk images

```javascript
// Stored as JS string constants
const DISK_DATA = "RDMzIERA...";  // base64-encoded

// Decoded at runtime:
function base64ToBytes(b64) {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
}
```

**Pros:** Simple, universal, works in all contexts
**Cons:** 33% size overhead (3 bytes → 4 chars)

#### 2. Data URIs

**Used for:** Images, sounds, small resources

```html
<img src="data:image/png;base64,iVBORw0KGgo..." />
<audio src="data:audio/mpeg;base64,//uQxAAA..." />
```

**Pros:** Direct browser rendering, no decode step
**Cons:** Same 33% overhead, not suitable for large files

#### 3. Blob URLs

**Used for:** Runtime-created resources, Worker scripts

```javascript
// Create a Blob from decoded data
const wasmBytes = base64ToBytes(WASM_BASE64);
const blob = new Blob([wasmBytes], { type: 'application/wasm' });
const blobUrl = URL.createObjectURL(blob);

// Use the Blob URL as if it were a regular URL
const response = await fetch(blobUrl);
```

**Pros:** Efficient for large binary data, streaming support
**Cons:** Requires explicit cleanup (`URL.revokeObjectURL`)

### Fetch Interceptor Pattern

The most critical pattern for making embedded emulators work offline:

```javascript
// Save original fetch
const _originalFetch = window.fetch;

// Resource map: URL patterns → embedded data
const EMBEDDED_RESOURCES = {
    'emulator.wasm': { data: WASM_BASE64, type: 'application/wasm' },
    'kickstart.rom': { data: ROM_BASE64, type: 'application/octet-stream' },
    'game.dsk':      { data: DISK_BASE64, type: 'application/octet-stream' },
};

// Override fetch
window.fetch = function(url, options) {
    // Check if this URL matches an embedded resource
    for (const [pattern, resource] of Object.entries(EMBEDDED_RESOURCES)) {
        if (url.includes(pattern) || url.endsWith(pattern)) {
            const bytes = base64ToBytes(resource.data);
            return Promise.resolve(new Response(bytes, {
                status: 200,
                headers: { 'Content-Type': resource.type }
            }));
        }
    }

    // For non-embedded URLs, use original fetch (will fail offline — that's OK)
    return _originalFetch(url, options);
};
```

### Worker Interceptor Pattern

Some emulators create Web Workers from external script URLs. We intercept this too:

```javascript
const _OriginalWorker = window.Worker;

window.Worker = function(scriptUrl) {
    if (typeof WORKER_SOURCE !== 'undefined') {
        // Create worker from inline source code
        const blob = new Blob([WORKER_SOURCE], { type: 'text/javascript' });
        const blobUrl = URL.createObjectURL(blob);
        return new _OriginalWorker(blobUrl);
    }
    return new _OriginalWorker(scriptUrl);
};
```

---

## Virtual Keyboard System

### Design Principles

1. **Context-aware**: Only show keys the game actually uses
2. **Touch-optimized**: Minimum 44×44px touch targets (Apple HIG)
3. **Non-intrusive**: Positioned below the emulator screen, not overlapping
4. **Responsive**: Adapts to screen size and orientation
5. **Accessible**: High contrast, clear labels, optional haptic feedback

### Architecture

```
┌─────────────────────────────────────────────┐
│               KeyboardManager               │
│                                             │
│  ┌──────────────┐  ┌─────────────────────┐  │
│  │ Layout Engine │  │ Input Mapper        │  │
│  │              │  │                     │  │
│  │ • Grid/Flex  │  │ • Key → scancode    │  │
│  │ • Responsive │  │ • AZERTY → QWERTY   │  │
│  │ • Themes     │  │ • Touch → keydown   │  │
│  └──────────────┘  └─────────────────────┘  │
│                                             │
│  ┌──────────────┐  ┌─────────────────────┐  │
│  │ Touch Handler │  │ Visual Feedback     │  │
│  │              │  │                     │  │
│  │ • touchstart │  │ • Highlight on      │  │
│  │ • touchmove  │  │   press             │  │
│  │ • touchend   │  │ • Scale animation   │  │
│  │ • multitouch │  │ • Haptic vibration  │  │
│  └──────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────┘
```

### Touch Event Flow

```
User touches screen
        │
        ▼
touchstart event
        │
        ├── Identify which key element was touched
        ├── Map key label → platform-specific scan code
        ├── Send keydown to emulator
        ├── Apply visual highlight (CSS class)
        ├── Trigger haptic feedback (if available)
        └── Call AudioContext.resume() (first touch only)
        
User moves finger (optional)
        │
        ▼
touchmove event
        │
        ├── Track finger position
        ├── If finger moves to new key:
        │   ├── Send keyup for previous key
        │   └── Send keydown for new key
        └── Update visual highlight

User lifts finger
        │
        ▼
touchend event
        │
        ├── Send keyup to emulator
        └── Remove visual highlight
```

### CSS Architecture

```css
/* Base keyboard container */
.virtual-keyboard {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 4px;
    padding: 8px;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(10px);
    z-index: 1000;
    touch-action: none;          /* Prevent browser gestures */
    -webkit-user-select: none;   /* Prevent text selection */
    user-select: none;
}

/* Individual key button */
.vk-key {
    min-width: 44px;            /* Apple HIG minimum touch target */
    min-height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #333;
    color: #fff;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
    transition: background 0.1s, transform 0.1s;
}

/* Key pressed state */
.vk-key.active {
    background: #007AFF;
    transform: scale(0.95);
}

/* Wide keys (Space, Enter, etc.) */
.vk-key.wide {
    flex: 2;
}

/* Responsive: landscape mode */
@media (orientation: landscape) {
    .virtual-keyboard {
        max-width: 60%;
        margin: 0 auto;
    }
}
```

---

## Emulator Integration Patterns

### Pattern 1: Direct JavaScript Emulator (Apple II, CPC)

```javascript
// The emulator is a JavaScript library that runs synchronously

// 1. Create emulator instance
const emulator = new Apple2Emulator({
    canvas: document.getElementById('screen'),
    model: 'apple2e'
});

// 2. Load ROM (embedded)
emulator.loadROM(romData);

// 3. Insert disk (decoded from base64)
const diskBytes = base64ToBytes(DISK_BASE64);
emulator.insertDisk(0, diskBytes);

// 4. Boot
emulator.reset();
emulator.type("PR#6\r");  // Boot from slot 6

// 5. Run emulation loop
function tick() {
    emulator.step();        // Execute one frame
    requestAnimationFrame(tick);
}
tick();

// 6. Handle input
document.addEventListener('keydown', (e) => {
    emulator.keyDown(e.keyCode);
});
```

### Pattern 2: WASM Emulator (Amiga)

```javascript
// The emulator is a WASM module with JS glue code

// 1. Decode and compile WASM
const wasmBytes = base64ToBytes(WASM_BASE64);
const wasmModule = await WebAssembly.compile(wasmBytes);

// 2. Instantiate with JS imports
const instance = await WebAssembly.instantiate(wasmModule, {
    env: {
        memory: new WebAssembly.Memory({ initial: 1024 }),
        // ... JS functions the WASM code can call
        renderFrame: (ptr, width, height) => {
            // Copy frame buffer to canvas
        },
        playAudio: (ptr, length) => {
            // Queue audio samples
        }
    }
});

// 3. Configure hardware
instance.exports.configure(/* chipset, RAM, etc. */);

// 4. Load ROM and disk
instance.exports.loadROM(romPtr, romSize);
instance.exports.insertDisk(0, diskPtr, diskSize);

// 5. Boot
instance.exports.powerOn();

// 6. Run emulation loop (WASM drives timing)
function tick() {
    instance.exports.runFrame();
    requestAnimationFrame(tick);
}
tick();
```

### Pattern 3: WebGL / Canvas Rendering

All packers support both WebGL and 2D Canvas rendering:

```javascript
// Try WebGL first for performance
let gl = canvas.getContext('webgl2') || canvas.getContext('webgl');

if (gl) {
    // WebGL rendering path
    // Create texture from frame buffer
    // Draw fullscreen quad
} else {
    // 2D Canvas fallback
    const ctx = canvas.getContext('2d');
    const imageData = ctx.createImageData(width, height);

    function renderFrame(frameBuffer) {
        // Copy emulator frame buffer to ImageData
        imageData.data.set(frameBuffer);
        ctx.putImageData(imageData, 0, 0);
    }
}
```

---

## Mobile Compatibility Techniques

### 1. Viewport Configuration

```html
<!-- Prevent zoom, ensure proper sizing -->
<meta name="viewport" content="width=device-width, initial-scale=1,
      maximum-scale=1, user-scalable=no, viewport-fit=cover">
```

### 2. Anti-Zoom CSS

```css
/* Prevent double-tap zoom */
* {
    touch-action: manipulation;
}

/* Prevent pinch zoom on the emulator area */
#emulator-screen {
    touch-action: none;
}

/* Prevent iOS rubber-band scrolling */
body {
    overflow: hidden;
    position: fixed;
    width: 100%;
    height: 100%;
}

/* Handle safe area (iPhone notch) */
body {
    padding-top: env(safe-area-inset-top);
    padding-bottom: env(safe-area-inset-bottom);
    padding-left: env(safe-area-inset-left);
    padding-right: env(safe-area-inset-right);
}
```

### 3. AudioContext Resume Pattern

```javascript
// Browsers (especially Chrome on mobile) require a user gesture
// before audio can play. This pattern handles it transparently.

let audioResumed = false;

function ensureAudio() {
    if (audioResumed) return;

    // Find the emulator's AudioContext
    const audioCtx = emulator.getAudioContext();
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume().then(() => {
            audioResumed = true;
            console.log('Audio context resumed');
        });
    }
}

// Attach to first user interaction
document.addEventListener('touchstart', ensureAudio, { once: true });
document.addEventListener('click', ensureAudio, { once: true });
document.addEventListener('keydown', ensureAudio, { once: true });
```

### 4. Orientation Handling

```javascript
// Detect orientation changes and resize emulator display

function handleOrientation() {
    const isLandscape = window.innerWidth > window.innerHeight;
    const canvas = document.getElementById('screen');

    if (isLandscape) {
        // Landscape: maximize screen, compact keyboard
        canvas.style.height = '60vh';
        document.getElementById('keyboard').classList.add('compact');
    } else {
        // Portrait: balanced split between screen and keyboard
        canvas.style.height = '40vh';
        document.getElementById('keyboard').classList.remove('compact');
    }
}

window.addEventListener('resize', handleOrientation);
screen.orientation?.addEventListener('change', handleOrientation);
handleOrientation(); // Initial call
```

### 5. Fullscreen API

```javascript
// Offer fullscreen for immersive experience

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {
            // Fullscreen not available — degrade gracefully
        });

        // Lock to landscape if possible
        screen.orientation?.lock('landscape').catch(() => {});
    } else {
        document.exitFullscreen();
    }
}
```

---

## Security Considerations

### Content Security Policy

Generated HTML files are designed to work with strict CSP:

- **No external scripts**: All JS is inline
- **No external styles**: All CSS is inline
- **No external images**: All images are Data URIs
- **No eval()**: No dynamic code execution
- **No external fonts**: System fonts only

### Data Safety

- Disk images are base64-encoded (no executable risk)
- WASM modules are compiled from known sources
- No localStorage/cookie usage (except cached version's IndexedDB)
- No network requests from generated files

---

## Performance Analysis

### File Size Breakdown

| Packer | Emulator | Game Data | Keyboard | Total |
|---|---|---|---|---|
| Apple II | ~200 KB | ~190 KB | ~20 KB | **~400-550 KB** |
| CPC | ~350 KB | ~300 KB | ~20 KB | **~600-800 KB** |
| Amiga | ~4 MB | ~2 MB | ~30 KB | **~5-10 MB** |

### Load Time Analysis

| Phase | Apple II | CPC | Amiga |
|---|---|---|---|
| Parse HTML | <100ms | <100ms | <500ms |
| Decode base64 | <100ms | <200ms | 1-3s |
| Init emulator | <200ms | <300ms | 1-2s |
| Boot game | <1s | 1-30s* | 5-15s |
| **Total** | **<1.5s** | **<2s*** | **<5s** |

\* CPC with warp-speed loading; without warp, loading can take 30-120s at real CPC speed.

### Memory Usage

| Platform | Emulator | Frame Buffer | Audio | Total |
|---|---|---|---|---|
| Apple II | ~10 MB | ~1 MB | <1 MB | **~12 MB** |
| CPC | ~15 MB | ~1 MB | <1 MB | **~17 MB** |
| Amiga | ~64 MB | ~2 MB | ~2 MB | **~68 MB** |

---

*← Back to [README](../README.md)*
