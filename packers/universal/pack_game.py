#!/usr/bin/env python3
"""
Universal Retro Game Packer — Creates self-contained offline HTML files from ROM images.
Uses EmulatorJS (RetroArch cores compiled to WebAssembly) to support 38 retro platforms.

Usage:
    python3 pack_game.py game.nes
    python3 pack_game.py game.sfc --title "Chrono Trigger"
    python3 pack_game.py --system genesis "Sonic.md"
    python3 pack_game.py game.gb --output my_game.html
    python3 pack_game.py streetfighter2.zip --system cps1
    python3 pack_game.py --prefetch-all   # Download all cores for 100% offline use

Supported systems (38):
  Console:  nes, snes, gb, gbc, gba, n64, nds, vb, genesis, sms, gg, 32x, segacd,
            atari2600, atari5200, atari7800, lynx, jaguar, psx, pce, pcfx, ngp, ws, coleco
  Computer: c64, c128, vic20, pet, plus4, amiga, cpc, zxspectrum, zx81
  Arcade:   cps1, cps2, fbneo, mame
  Other:    doom
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.request

# ============================================================
#  System Definitions
# ============================================================
SYSTEMS = {
    # Tier 1 — Excellent feasibility
    'nes':       {'core': 'fceumm',           'label': 'NES / Famicom',              'extensions': ['.nes']},
    'snes':      {'core': 'snes9x',           'label': 'Super Nintendo',             'extensions': ['.smc', '.sfc', '.snes']},
    'gb':        {'core': 'gambatte',          'label': 'Game Boy',                   'extensions': ['.gb']},
    'gbc':       {'core': 'gambatte',          'label': 'Game Boy Color',             'extensions': ['.gbc']},
    'genesis':   {'core': 'genesis_plus_gx',   'label': 'Sega Genesis / Mega Drive',  'extensions': ['.md', '.bin', '.gen']},
    'sms':       {'core': 'smsplus',           'label': 'Sega Master System',         'extensions': ['.sms']},
    'gg':        {'core': 'genesis_plus_gx',   'label': 'Sega Game Gear',             'extensions': ['.gg']},
    'atari2600': {'core': 'stella2014',        'label': 'Atari 2600',                 'extensions': ['.a26', '.bin']},
    'atari7800': {'core': 'prosystem',         'label': 'Atari 7800',                 'extensions': ['.a78']},
    'atari5200': {'core': 'a5200',             'label': 'Atari 5200',                 'extensions': ['.a52'], 'bios': '5200.rom'},
    'lynx':      {'core': 'handy',             'label': 'Atari Lynx',                 'extensions': ['.lnx'], 'bios': 'lynxboot.img'},
    'coleco':    {'core': 'gearcoleco',        'label': 'ColecoVision',               'extensions': ['.col'],          'bios': 'colecovision.rom'},
    'ngp':       {'core': 'mednafen_ngp',      'label': 'Neo Geo Pocket / Color',     'extensions': ['.ngp', '.ngc']},
    'ws':        {'core': 'mednafen_wswan',    'label': 'WonderSwan / Color',         'extensions': ['.ws', '.wsc']},
    'vb':        {'core': 'beetle_vb',         'label': 'Virtual Boy',                'extensions': ['.vb']},
    'pce':       {'core': 'mednafen_pce',      'label': 'PC Engine / TurboGrafx-16',  'extensions': ['.pce'], 'bios': 'syscard3.pce'},
    '32x':       {'core': 'picodrive',         'label': 'Sega 32X',                   'extensions': ['.32x']},
    # Tier 2 — Feasible with caveats
    'gba':       {'core': 'mgba',              'label': 'Game Boy Advance',           'extensions': ['.gba']},
    'n64':       {'core': 'mupen64plus_next',  'label': 'Nintendo 64',                'extensions': ['.n64', '.z64', '.v64']},
    'nds':       {'core': 'melonds',           'label': 'Nintendo DS',                'extensions': ['.nds']},
    'psx':       {'core': 'pcsx_rearmed',      'label': 'PlayStation',                'extensions': ['.bin', '.cue', '.iso', '.pbp'], 'bios': 'SCPH5501.BIN'},
    'segacd':    {'core': 'genesis_plus_gx',   'label': 'Sega CD / Mega CD',          'extensions': ['.cue', '.bin', '.chd'], 'bios': 'BIOS_CD_U.BIN'},
    # Tier 3 — Retro computers
    'c64':       {'core': 'vice_x64sc',        'label': 'Commodore 64',               'extensions': ['.d64', '.t64', '.prg', '.crt'],
                  'core_options': {'vice_autostart': 'warp', 'vice_drive_true_emulation': 'disabled'}},
    'zxspectrum':{'core': 'fuse',              'label': 'ZX Spectrum',                'extensions': ['.z80', '.tap', '.sna', '.tzx']},
    # --- NEW SYSTEMS (added Feb 2026) ---
    # Atari
    'jaguar':    {'core': 'virtualjaguar',     'label': 'Atari Jaguar',               'extensions': ['.j64', '.jag', '.rom', '.abs', '.cof', '.bin']},
    # Commodore family
    'c128':      {'core': 'vice_x128',         'label': 'Commodore 128',              'extensions': ['.d64', '.d71', '.d81', '.prg', '.t64', '.tap']},
    'vic20':     {'core': 'vice_xvic',         'label': 'Commodore VIC-20',           'extensions': ['.d64', '.prg', '.crt', '.t64', '.tap', '.20', '.60', '.a0'],
                  'core_options': {'vice_autostart': 'warp', 'vice_drive_true_emulation': 'disabled'}},
    'pet':       {'core': 'vice_xpet',         'label': 'Commodore PET',              'extensions': ['.d64', '.prg', '.t64', '.tap'],
                  'core_options': {'vice_autostart': 'warp', 'vice_drive_true_emulation': 'disabled'}},
    'plus4':     {'core': 'vice_xplus4',       'label': 'Commodore Plus/4',           'extensions': ['.d64', '.prg', '.t64', '.tap', '.bin', '.crt']},
    'amiga':     {'core': 'puae',              'label': 'Commodore Amiga',            'extensions': ['.adf', '.adz', '.dms', '.ipf']},
    # Amstrad
    'cpc':       {'core': 'crocods',            'label': 'Amstrad CPC',                'extensions': ['.dsk', '.sna', '.cdt', '.voc']},
    # Sinclair
    'zx81':      {'core': '81',                'label': 'Sinclair ZX81',              'extensions': ['.p', '.81', '.tzx']},
    # id Software
    'doom':      {'core': 'prboom',            'label': 'DOOM (PrBoom)',              'extensions': ['.wad']},
    # NEC
    'pcfx':      {'core': 'mednafen_pcfx',     'label': 'PC-FX',                     'extensions': ['.cue', '.ccd', '.toc'], 'bios': 'pcfx.rom'},
    'cps1':      {'core': 'fbalpha2012_cps1', 'label': 'Arcade (CPS1)',              'extensions': ['.zip']},
    'cps2':      {'core': 'fbalpha2012_cps2', 'label': 'Arcade (CPS2)',              'extensions': ['.zip']},
    'fbneo':     {'core': 'fbneo',            'label': 'Arcade (FBNeo)',             'extensions': ['.zip']},
    'mame':      {'core': 'mame2003_plus',    'label': 'Arcade (MAME 2003+)',        'extensions': ['.zip']},
    # --- NEW SYSTEMS (CDN cores not previously included) ---
    '3do':       {'core': 'opera',            'label': '3DO Interactive',            'extensions': ['.iso', '.bin', '.cue', '.chd']},
    'cdi':       {'core': 'same_cdi',         'label': 'Philips CD-i',              'extensions': ['.chd', '.cue']},
    'saturn':    {'core': 'yabause',          'label': 'Sega Saturn',               'extensions': ['.bin', '.cue', '.iso', '.chd'], 'bios': 'mpr-17933.bin'},
    # NOTE: dosbox_pure (DOS) and ppsspp (PSP) are listed in EmulatorJS docs
    # but their cores do NOT exist on any CDN version as of March 2026.
}

# Alternative cores: same system, different emulator backend.
# Use with: --core <core_name> to override the default.
ALT_CORES = {
    'nestopia':         {'for_system': 'nes',   'label': 'NES (Nestopia)'},
    'desmume':          {'for_system': 'nds',   'label': 'Nintendo DS (DeSmuME)'},
    'desmume2015':      {'for_system': 'nds',   'label': 'Nintendo DS (DeSmuME 2015)'},
    'mame2003':         {'for_system': 'mame',  'label': 'Arcade (MAME 2003)'},
    'mednafen_psx_hw':  {'for_system': 'psx',   'label': 'PlayStation (Mednafen HW)'},
    'parallel_n64':     {'for_system': 'n64',   'label': 'Nintendo 64 (Parallel)'},
    'vice_x64':         {'for_system': 'c64',   'label': 'Commodore 64 (VICE x64)'},
    'cap32':            {'for_system': 'cpc',   'label': 'Amstrad CPC (Cap32)'},
}

# Build reverse lookup: extension → system
EXT_TO_SYSTEM = {}
for sys_id, info in SYSTEMS.items():
    for ext in info['extensions']:
        if ext not in EXT_TO_SYSTEM:
            EXT_TO_SYSTEM[ext] = sys_id

# EmulatorJS CDN base URL
EJS_CDN_BASE = "https://cdn.emulatorjs.org/stable/data/"

# Offline cores directory (next to script). If present, no internet needed.
OFFLINE_DIR_NAME = "cores"

# ============================================================
#  Additional EmulatorJS assets to embed for 100% offline
# ============================================================
# These files are dynamically loaded by EmulatorJS at runtime.
# Without embedding them, games CANNOT work offline (Issue #11).

# Files loaded via <script> injection (EJS_paths can redirect these)
SRC_ASSETS = [
    'src/GameManager.js',
    'src/gamepad.js',
    'src/nipplejs.js',
    'src/shaders.js',
    'src/socket.io.min.js',
    'src/storage.js',
]

# Compression libraries (loaded for core WASM decompression)
COMPRESSION_ASSETS_TEXT = [
    'compression/extract7z.js',
    'compression/extractzip.js',
    'compression/libunrar.js',
]

COMPRESSION_ASSETS_BINARY = [
    'compression/libunrar.wasm',
]

ALL_EXTRA_ASSETS = SRC_ASSETS + COMPRESSION_ASSETS_TEXT + COMPRESSION_ASSETS_BINARY


def get_offline_dir():
    """Return the offline cores directory if it exists, else None."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    offline_dir = os.path.join(script_dir, OFFLINE_DIR_NAME)
    if os.path.isdir(offline_dir):
        return offline_dir
    return None

# ============================================================
#  Asset Downloading & Caching
# ============================================================
def get_cache_dir():
    """Return the cache directory path, creating it if needed."""
    # Check for .emulatorjs_cache next to this script first
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(script_dir, '.emulatorjs_cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def download_binary(url, cache_path=None):
    """Download a binary file, with optional local caching."""
    if cache_path and os.path.isfile(cache_path):
        size_kb = os.path.getsize(cache_path) / 1024
        print(f"  ✅ Cached: {os.path.basename(cache_path)} ({size_kb:.0f} KB)")
        with open(cache_path, 'rb') as f:
            return f.read()

    print(f"  ⬇️  Downloading: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 PortableRetroGames/1.0'})
    try:
        response = urllib.request.urlopen(req, timeout=60)
        data = response.read()
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        sys.exit(1)

    if cache_path:
        os.makedirs(os.path.dirname(cache_path) or '.', exist_ok=True)
        with open(cache_path, 'wb') as f:
            f.write(data)
        print(f"  ✅ Downloaded and cached: {len(data) / 1024:.0f} KB")

    return data


def download_text(url, cache_path=None):
    """Download a text file, with optional local caching."""
    if cache_path and os.path.isfile(cache_path):
        size_kb = os.path.getsize(cache_path) / 1024
        print(f"  ✅ Cached: {os.path.basename(cache_path)} ({size_kb:.0f} KB)")
        with open(cache_path, 'r', encoding='utf-8') as f:
            return f.read()

    print(f"  ⬇️  Downloading: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 PortableRetroGames/1.0'})
    try:
        response = urllib.request.urlopen(req, timeout=60)
        data = response.read().decode('utf-8')
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        sys.exit(1)

    if cache_path:
        os.makedirs(os.path.dirname(cache_path) or '.', exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(data)
        print(f"  ✅ Downloaded and cached: {len(data) / 1024:.0f} KB")

    return data


# ============================================================
#  System Auto-Detection
# ============================================================
def detect_system(rom_path):
    """Detect the system from the ROM file extension."""
    ext = os.path.splitext(rom_path)[1].lower()
    system = EXT_TO_SYSTEM.get(ext)
    if not system:
        print(f"❌ Cannot auto-detect system for extension '{ext}'")
        print(f"   Use --system to specify. Available systems:")
        for sid, info in sorted(SYSTEMS.items()):
            exts = ', '.join(info['extensions'])
            print(f"     {sid:12s}  {info['label']:35s}  ({exts})")
        sys.exit(1)
    return system


# ============================================================
#  HTML Template
# ============================================================
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<title>{{TITLE}} - {{SYSTEM_LABEL}} | Portable Retro Games</title>
<meta name="description" content="Play {{TITLE}} ({{SYSTEM_LABEL}}) directly in your browser. No download, no install - standalone offline HTML game.">
<meta name="keywords" content="{{TITLE}}, {{SYSTEM_LABEL}}, retro gaming, emulator, standalone, offline, browser game">
<meta property="og:title" content="{{TITLE}} - {{SYSTEM_LABEL}}">
<meta property="og:description" content="Play {{TITLE}} directly in your browser - standalone, offline, no install needed.">
<style>
{{EJS_CSS}}
</style>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    background: #0a0a0a;
    color: #fff;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    height: 100vh;
    height: 100dvh;
    width: 100vw;
    overflow: hidden;
    position: fixed;
    top: 0;
    left: 0;
    overscroll-behavior: none;
    -webkit-overflow-scrolling: none;
    touch-action: none;
    -webkit-tap-highlight-color: transparent;
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    user-select: none;
}
#game {
    width: 100vw;
    height: 100vh;
    height: 100dvh;
    max-width: 100%;
    max-height: 100%;
    overflow: hidden;
    touch-action: manipulation;
}
#loading-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    height: 100dvh;
    background: radial-gradient(ellipse at center, #1a1a2e 0%, #0a0a0a 100%);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    z-index: 9999;
    transition: opacity 0.5s ease;
    padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
    overflow: hidden;
}
#loading-overlay.hidden {
    opacity: 0;
    pointer-events: none;
}
.ld-title {
    font-size: clamp(1.5rem, 6vw, 2.5rem); font-weight: 700; margin-bottom: 0.25rem;
    background: linear-gradient(135deg, #FF4444, #ff8800);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    padding: 0 1rem;
    word-break: break-word;
    max-width: 90vw;
}
.ld-system {
    font-size: clamp(0.75rem, 3vw, 1rem); color: #888; margin-bottom: 2rem;
    text-align: center;
}
.ld-bar {
    width: min(300px, 80vw); height: 6px; background: #222; border-radius: 3px; overflow: hidden;
}
.ld-fill {
    height: 100%; width: 0%; border-radius: 3px;
    background: linear-gradient(90deg, #FF4444, #ff8800);
    transition: width 0.3s ease;
}
.ld-status {
    margin-top: 1rem; font-size: clamp(0.7rem, 2.5vw, 0.85rem); color: #aaa;
    text-align: center;
    padding: 0 1rem;
}
.ld-credits {
    position: absolute; bottom: max(1.5rem, env(safe-area-inset-bottom)); font-size: clamp(0.6rem, 2vw, 0.75rem); color: #555;
    text-align: center;
    padding: 0 1rem;
}
.ld-credits a { color: #777; text-decoration: none; }
</style>
</head>
<body>
<div id="loading-overlay">
    <div class="ld-title">{{TITLE}}</div>
    <div class="ld-system">{{SYSTEM_LABEL}}</div>
    <div class="ld-bar"><div class="ld-fill" id="ld-fill" style="width: 5%;"></div></div>
    <div class="ld-status" id="ld-status">Loading emulator engine...</div>
    <div class="ld-credits">
        Powered by <a href="https://emulatorjs.org">EmulatorJS</a> &amp;
        <a href="https://github.com/aciderix/portable-retro-games">Portable Retro Games</a>
    </div>
</div>

<div id="game"></div>

<script>
(function() {
    // ═══════════════════════════════════════════════════════════
    //  EMBEDDED GAME DATA
    // ═══════════════════════════════════════════════════════════
    var EMBEDDED_ROM_B64 = "{{ROM_B64}}";
    var EMBEDDED_ROM_FILENAME = "{{ROM_FILENAME}}";
    var EMBEDDED_CORE_B64 = "{{CORE_B64}}";
    var EMBEDDED_CORE_LEGACY_B64 = "{{CORE_LEGACY_B64}}";
    var EMBEDDED_CORE_NAME = "{{CORE_NAME}}";

    // ═══════════════════════════════════════════════════════════
    //  EMBEDDED EXTRA ASSETS (for 100% offline — Issue #11 fix)
    //  Contains: src/ scripts + compression/ libraries
    // ═══════════════════════════════════════════════════════════
    var EMBEDDED_EXTRA = {{EXTRA_ASSETS_JSON}};

    // ═══════════════════════════════════════════════════════════
    //  HELPERS
    // ═══════════════════════════════════════════════════════════
    function b64toUint8(b64) {
        var bin = atob(b64);
        var len = bin.length;
        var arr = new Uint8Array(len);
        for (var i = 0; i < len; i++) arr[i] = bin.charCodeAt(i);
        return arr;
    }
    function b64toBlobUrl(b64, mime) {
        return URL.createObjectURL(new Blob([b64toUint8(b64)], { type: mime || 'application/octet-stream' }));
    }
    function getMime(name) {
        if (name.endsWith('.wasm')) return 'application/wasm';
        if (name.endsWith('.js'))   return 'text/javascript';
        if (name.endsWith('.json')) return 'application/json';
        if (name.endsWith('.css'))  return 'text/css';
        return 'application/octet-stream';
    }
    function setProgress(pct, msg) {
        var fill = document.getElementById('ld-fill');
        var status = document.getElementById('ld-status');
        if (fill) fill.style.width = pct + '%';
        if (status) status.textContent = msg;
    }

    setProgress(10, 'Initializing offline engine...');

    // ═══════════════════════════════════════════════════════════
    //  CREATE BLOB URLs FOR ALL EXTRA ASSETS
    // ═══════════════════════════════════════════════════════════
    var extraBlobUrls = {};
    for (var key in EMBEDDED_EXTRA) {
        if (EMBEDDED_EXTRA[key]) {
            extraBlobUrls[key] = b64toBlobUrl(EMBEDDED_EXTRA[key], getMime(key));
        }
    }

    // ═══════════════════════════════════════════════════════════
    //  LAYER 1: EJS_paths — Official EmulatorJS path override
    //  Redirects src/ file loading to embedded blob URLs
    // ═══════════════════════════════════════════════════════════
    window.EJS_paths = {};
    var ejsPathFiles = ['GameManager.js', 'gamepad.js', 'nipplejs.js', 'shaders.js',
                        'socket.io.min.js', 'storage.js'];
    for (var i = 0; i < ejsPathFiles.length; i++) {
        if (extraBlobUrls[ejsPathFiles[i]]) {
            window.EJS_paths[ejsPathFiles[i]] = extraBlobUrls[ejsPathFiles[i]];
        }
    }
    // Stub version.json to prevent CDN fetch
    window.EJS_paths['version.json'] = b64toBlobUrl(btoa('{}'), 'application/json');

    // ═══════════════════════════════════════════════════════════
    //  LAYER 2: <script> tag interception
    //  Catches dynamically injected scripts (compression libs, etc.)
    // ═══════════════════════════════════════════════════════════
    var _origSrcDesc = Object.getOwnPropertyDescriptor(HTMLScriptElement.prototype, 'src');
    if (_origSrcDesc && _origSrcDesc.set) {
        Object.defineProperty(HTMLScriptElement.prototype, 'src', {
            set: function(val) {
                if (val && typeof val === 'string') {
                    for (var name in extraBlobUrls) {
                        if (val.indexOf(name) !== -1) {
                            return _origSrcDesc.set.call(this, extraBlobUrls[name]);
                        }
                    }
                }
                return _origSrcDesc.set.call(this, val);
            },
            get: _origSrcDesc.get,
            configurable: true
        });
    }
    // Also intercept setAttribute('src', ...) on script elements
    var _origSetAttr = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function(name, value) {
        if (this instanceof HTMLScriptElement && name.toLowerCase() === 'src' &&
            value && typeof value === 'string') {
            for (var key in extraBlobUrls) {
                if (value.indexOf(key) !== -1) {
                    return _origSetAttr.call(this, name, extraBlobUrls[key]);
                }
            }
        }
        return _origSetAttr.call(this, name, value);
    };

    // ═══════════════════════════════════════════════════════════
    //  LAYER 3: fetch() interception
    //  Catches core WASM, ROM, compression, and metadata requests
    // ═══════════════════════════════════════════════════════════
    var _origFetch = window.fetch;
    window.fetch = function(input, init) {
        var url = (typeof input === 'string') ? input : (input && input.url ? input.url : '');

        // Serve embedded core WASM (both normal and legacy variants)
        if (url.indexOf(EMBEDDED_CORE_NAME) !== -1 && url.indexOf('-wasm.data') !== -1) {
            setProgress(60, 'Loading emulator core (offline)...');
            var isLegacy = url.indexOf('-legacy-wasm.data') !== -1 || url.indexOf('legacy-wasm.data') !== -1;
            var coreB64 = (isLegacy && EMBEDDED_CORE_LEGACY_B64) ? EMBEDDED_CORE_LEGACY_B64 : EMBEDDED_CORE_B64;
            var data = b64toUint8(coreB64);
            return Promise.resolve(new Response(data.buffer, {
                status: 200,
                headers: { 'Content-Type': 'application/octet-stream', 'Content-Length': String(data.length) }
            }));
        }

        // Serve embedded ROM (match by blob URL or filename)
        if (url === window.EJS_gameUrl || url.indexOf(EMBEDDED_ROM_FILENAME) !== -1) {
            setProgress(80, 'Loading game data...');
            var data = b64toUint8(EMBEDDED_ROM_B64);
            return Promise.resolve(new Response(data.buffer, {
                status: 200,
                headers: { 'Content-Type': 'application/octet-stream', 'Content-Length': String(data.length) }
            }));
        }

        // Serve any embedded extra asset (compression libs, etc.)
        for (var fname in EMBEDDED_EXTRA) {
            if (url.indexOf(fname) !== -1 && EMBEDDED_EXTRA[fname]) {
                var data = b64toUint8(EMBEDDED_EXTRA[fname]);
                return Promise.resolve(new Response(data.buffer, {
                    status: 200,
                    headers: { 'Content-Type': getMime(fname), 'Content-Length': String(data.length) }
                }));
            }
        }

        // Stub metadata requests
        if (url.indexOf('version.json') !== -1 || url.indexOf('localization/') !== -1 ||
            url.indexOf('cores/reports/') !== -1) {
            return Promise.resolve(new Response('{}', {
                status: 200, headers: { 'Content-Type': 'application/json' }
            }));
        }

        return _origFetch.apply(this, arguments);
    };

    // ═══════════════════════════════════════════════════════════
    //  LAYER 3b: XMLHttpRequest interception (same logic)
    // ═══════════════════════════════════════════════════════════
    var XHRProto = XMLHttpRequest.prototype;
    var _xhrOpen = XHRProto.open;
    var _xhrSend = XHRProto.send;

    XHRProto.open = function(method, url) {
        this._prg_url = url;
        return _xhrOpen.apply(this, arguments);
    };

    XHRProto.send = function(body) {
        var url = this._prg_url || '';
        var embeddedData = null;

        // Check core WASM (both normal and legacy variants)
        if (url.indexOf(EMBEDDED_CORE_NAME) !== -1 && url.indexOf('-wasm.data') !== -1) {
            var isLegacy = url.indexOf('-legacy-wasm.data') !== -1 || url.indexOf('legacy-wasm.data') !== -1;
            embeddedData = b64toUint8((isLegacy && EMBEDDED_CORE_LEGACY_B64) ? EMBEDDED_CORE_LEGACY_B64 : EMBEDDED_CORE_B64);
            setProgress(60, 'Loading emulator core (offline)...');
        }
        // Check ROM
        else if (url.indexOf(EMBEDDED_ROM_FILENAME) !== -1) {
            embeddedData = b64toUint8(EMBEDDED_ROM_B64);
            setProgress(80, 'Loading game data...');
        }
        // Check extra assets
        else {
            for (var fname in EMBEDDED_EXTRA) {
                if (url.indexOf(fname) !== -1 && EMBEDDED_EXTRA[fname]) {
                    embeddedData = b64toUint8(EMBEDDED_EXTRA[fname]);
                    break;
                }
            }
        }

        if (embeddedData) {
            var self = this;
            Object.defineProperty(self, 'readyState', { get: function() { return 4; }, configurable: true });
            Object.defineProperty(self, 'status', { get: function() { return 200; }, configurable: true });
            Object.defineProperty(self, 'statusText', { get: function() { return 'OK'; }, configurable: true });
            Object.defineProperty(self, 'response', { get: function() { return embeddedData.buffer; }, configurable: true });
            Object.defineProperty(self, 'responseText', { get: function() {
                try { return new TextDecoder().decode(embeddedData); } catch(e) { return ''; }
            }, configurable: true });
            setTimeout(function() {
                self.dispatchEvent(new ProgressEvent('progress', { loaded: embeddedData.length, total: embeddedData.length }));
                self.dispatchEvent(new Event('load'));
                if (self.onprogress) self.onprogress({ loaded: embeddedData.length, total: embeddedData.length });
                if (self.onload) self.onload();
                if (self.onreadystatechange) self.onreadystatechange();
            }, 10);
            return;
        }

        // Stub metadata
        if (url.indexOf('version.json') !== -1 || url.indexOf('cores/reports/') !== -1 ||
            url.indexOf('localization/') !== -1) {
            var self = this;
            Object.defineProperty(self, 'readyState', { get: function() { return 4; }, configurable: true });
            Object.defineProperty(self, 'status', { get: function() { return 200; }, configurable: true });
            Object.defineProperty(self, 'response', { get: function() { return '{}'; }, configurable: true });
            Object.defineProperty(self, 'responseText', { get: function() { return '{}'; }, configurable: true });
            setTimeout(function() {
                self.dispatchEvent(new Event('load'));
                if (self.onload) self.onload();
                if (self.onreadystatechange) self.onreadystatechange();
            }, 10);
            return;
        }

        return _xhrSend.apply(this, arguments);
    };

    // ═══════════════════════════════════════════════════════════
    //  EJS CONFIGURATION
    // ═══════════════════════════════════════════════════════════
    window.EJS_player = '#game';
    // Use filename instead of blob URL — arcade cores (fbalpha, fbneo) identify
    // the romset by filename in the URL. Blob URLs have no filename → romset unknown.
    // The fetch interceptor already matches requests by EMBEDDED_ROM_FILENAME.
    window.EJS_gameUrl = EMBEDDED_ROM_FILENAME;
    window.EJS_gameName = '{{TITLE}}';
    window.EJS_color = '#FF4444';
    window.EJS_startOnLoaded = false;
    window.EJS_pathtodata = 'https://cdn.emulatorjs.org/stable/data/';
    window.EJS_threads = false;  // Force non-threaded cores (avoids needing SharedArrayBuffer/COOP/COEP headers)
    window.EJS_CacheLimit = 0;
    window.EJS_startButtonName = 'Play {{TITLE}}';
    window.EJS_disableLocalStorage = false;
    {{BIOS_SETUP}}

    window.EJS_ready = function() {
        setProgress(100, 'Ready!');
        setTimeout(function() {
            document.getElementById('loading-overlay').classList.add('hidden');
        }, 400);
    };
    window.EJS_onGameStart = function() {
        document.getElementById('loading-overlay').classList.add('hidden');
    };

    setProgress(30, 'Loading emulator engine...');
})();
window.EJS_core = '{{CORE_NAME}}';
</script>

<!-- Core options for autorun (injected by packer) -->
{{CORE_OPTIONS}}

<!-- EmulatorJS Engine (emulator.min.js) — embedded inline -->
<script>
{{EJS_ENGINE_JS}}
</script>

<!-- Initialize EmulatorJS -->
<script>
(async function() {
    var scriptPath = window.EJS_pathtodata;
    var config = {};
    config.gameUrl = window.EJS_gameUrl;
    config.dataPath = scriptPath;
    config.system = window.EJS_core;
    config.biosUrl = window.EJS_biosUrl;
    config.gameName = window.EJS_gameName;
    config.color = window.EJS_color;
    config.startOnLoad = window.EJS_startOnLoaded;
    config.fullscreenOnLoad = window.EJS_fullscreenOnLoaded;
    config.filePaths = window.EJS_paths;
    config.cacheLimit = window.EJS_CacheLimit;
    config.defaultOptions = window.EJS_defaultOptions;
    config.startBtnName = window.EJS_startButtonName;
    config.volume = window.EJS_volume;
    config.defaultControllers = window.EJS_defaultControls;
    config.disableDatabases = window.EJS_disableDatabases;
    config.disableLocalStorage = window.EJS_disableLocalStorage;
    config.threads = window.EJS_threads;
    config.shaders = Object.assign({}, window.EJS_SHADERS, window.EJS_shaders ? window.EJS_shaders : {});

    window.EJS_emulator = new EmulatorJS(EJS_player, config);

    if (typeof window.EJS_ready === 'function') {
        window.EJS_emulator.on('ready', window.EJS_ready);
    }
    if (typeof window.EJS_onGameStart === 'function') {
        window.EJS_emulator.on('start', window.EJS_onGameStart);
    }
})();
</script>

</body>
</html>'''


# ============================================================
#  HTML Generation
# ============================================================
# ============================================================
#  D64 → PRG Extraction (for C64/C128/VIC-20/PET/Plus4)
# ============================================================
# The VICE WASM core cannot reliably load .d64 disk images:
# True Drive Emulation hangs during LOAD"*",8,1.
# Extracting the first PRG program from the disk image and
# feeding it directly bypasses this issue entirely.

# D64 format: 35 tracks, 683 sectors of 256 bytes each
# Track numbering starts at 1, sector numbering at 0
# Directory is at track 18, sector 1

D64_TRACK_OFFSETS = []  # Will be populated at import time

def _build_d64_track_table():
    """Build a lookup table: track number → byte offset in the D64 file.
    D64 has variable sectors per track:
      Tracks  1-17: 21 sectors each
      Tracks 18-24: 19 sectors each
      Tracks 25-30: 18 sectors each
      Tracks 31-35: 17 sectors each
    """
    sectors_per_track = (
        [21] * 17 +   # tracks 1-17
        [19] * 7  +   # tracks 18-24
        [18] * 6  +   # tracks 25-30
        [17] * 5      # tracks 31-35
    )
    offset = 0
    D64_TRACK_OFFSETS.append(0)  # index 0 unused (tracks start at 1)
    for spt in sectors_per_track:
        D64_TRACK_OFFSETS.append(offset)
        offset += spt * 256
    return sectors_per_track

_D64_SECTORS_PER_TRACK = _build_d64_track_table()

def d64_read_sector(d64_data, track, sector):
    """Read a 256-byte sector from the D64 image."""
    if track < 1 or track > 35:
        return None
    offset = D64_TRACK_OFFSETS[track] + sector * 256
    if offset + 256 > len(d64_data):
        return None
    return d64_data[offset:offset + 256]

def extract_prg_from_d64(d64_data):
    """Extract the first PRG file from a D64 disk image.
    Returns (prg_data, filename) or (None, None) if no PRG found.
    
    Directory format (each entry = 32 bytes):
      Byte 0-1: Next dir sector (track, sector) — only in first entry of each sector
      Byte 2:   File type (0x82 = PRG with closed flag)
      Byte 3-4: First data sector (track, sector)
      Byte 5-20: Filename (16 bytes, padded with 0xA0)
      Byte 30-31: File size in sectors (little-endian)
    """
    # Read directory: starts at track 18, sector 1
    dir_track, dir_sector = 18, 1
    visited = set()
    
    while dir_track != 0:
        if (dir_track, dir_sector) in visited:
            break  # Avoid infinite loops
        visited.add((dir_track, dir_sector))
        
        sector_data = d64_read_sector(d64_data, dir_track, dir_sector)
        if not sector_data:
            break
        
        # Each directory sector has 8 entries of 32 bytes
        for i in range(8):
            entry = sector_data[i * 32:(i + 1) * 32]
            file_type = entry[2] & 0x0F  # Lower nibble = type (2 = PRG)
            closed = entry[2] & 0x80     # Bit 7 = closed flag
            
            if file_type == 2 and closed:  # PRG file, properly closed
                data_track = entry[3]
                data_sector = entry[4]
                # Extract filename (strip 0xA0 padding)
                raw_name = entry[5:21]
                name = raw_name.split(b'\xa0')[0].decode('ascii', errors='replace').strip()
                
                # Follow the sector chain to read the full PRG
                prg_data = bytearray()
                data_visited = set()
                while data_track != 0:
                    if (data_track, data_sector) in data_visited:
                        break
                    data_visited.add((data_track, data_sector))
                    
                    block = d64_read_sector(d64_data, data_track, data_sector)
                    if not block:
                        break
                    
                    next_track = block[0]
                    next_sector = block[1]
                    
                    if next_track == 0:
                        # Last sector: next_sector = number of bytes used (1-based)
                        prg_data.extend(block[2:2 + next_sector - 1])
                    else:
                        prg_data.extend(block[2:])
                    
                    data_track = next_track
                    data_sector = next_sector
                
                if prg_data:
                    return bytes(prg_data), name
        
        # Follow chain to next directory sector
        dir_track = sector_data[0]
        dir_sector = sector_data[1]
    
    return None, None


def generate_html(rom_path, title, system_id, ejs_css, ejs_engine_js, core_b64, core_legacy_b64, rom_b64, extra_assets_json):
    """Generate the complete self-contained HTML file."""
    system_info = SYSTEMS[system_id]
    rom_filename = os.path.basename(rom_path).lower()

    html = HTML_TEMPLATE
    html = html.replace('{{TITLE}}', title)
    html = html.replace('{{SYSTEM_LABEL}}', system_info['label'])
    html = html.replace('{{ROM_B64}}', rom_b64)
    html = html.replace('{{ROM_FILENAME}}', rom_filename)
    html = html.replace('{{CORE_B64}}', core_b64)
    html = html.replace('{{CORE_LEGACY_B64}}', core_legacy_b64)
    html = html.replace('{{CORE_NAME}}', system_info['core'])
    html = html.replace('{{EJS_CSS}}', ejs_css)
    html = html.replace('{{EJS_ENGINE_JS}}', ejs_engine_js)
    html = html.replace('{{EXTRA_ASSETS_JSON}}', extra_assets_json)

    # BIOS support: set EJS_biosUrl for systems that require a BIOS file
    if 'bios' in system_info:
        bios_filename = system_info['bios']
        html = html.replace('{{BIOS_SETUP}}', f"window.EJS_biosUrl = '{bios_filename}';")
    else:
        html = html.replace('{{BIOS_SETUP}}', '')

    # Core options injection (e.g. VICE autostart for VIC-20, PET, C64)
    if 'core_options' in system_info and system_info['core_options']:
        opts_js = json.dumps(system_info['core_options'])
        core_options_block = (
            '<script>\n'
            f'    window.EJS_defaultOptions = {opts_js};\n'
            '</script>'
        )
    else:
        core_options_block = ''
    html = html.replace('{{CORE_OPTIONS}}', core_options_block)

    return html


# ============================================================
#  Download Extra Assets
# ============================================================
def download_extra_assets(cache_dir, offline_dir):
    """Download all additional EmulatorJS assets needed for offline support.
    Returns a dict of {filename: base64_data}."""
    extra = {}
    for asset_path in ALL_EXTRA_ASSETS:
        filename = os.path.basename(asset_path)
        cache_path = os.path.join(cache_dir, filename)
        offline_path = os.path.join(offline_dir, filename) if offline_dir else None
        is_binary = asset_path in COMPRESSION_ASSETS_BINARY

        # Try offline dir first, then cache, then CDN
        if offline_path and os.path.isfile(offline_path):
            with open(offline_path, 'rb') as f:
                data = f.read()
            print(f"  ✅ Offline: {filename} ({len(data) // 1024} KB)")
        elif is_binary:
            data = download_binary(EJS_CDN_BASE + asset_path, cache_path)
        else:
            text = download_text(EJS_CDN_BASE + asset_path, cache_path)
            data = text.encode('utf-8')

        extra[filename] = base64.b64encode(data).decode('ascii')

    return extra


# ============================================================
#  Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description='Universal Retro Game Packer — Pack any ROM into a standalone offline HTML file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported systems:
""" + '\n'.join(f"  {sid:12s}  {info['label']:35s}  ({', '.join(info['extensions'])})"
                 for sid, info in sorted(SYSTEMS.items()))
    )
    parser.add_argument('rom', nargs='?', help='Path to ROM or disk image file')
    parser.add_argument('--system', '-s', choices=sorted(SYSTEMS.keys()),
                       help='Target system (auto-detected from extension if omitted)')
    parser.add_argument('--title', '-t', help='Game title (default: filename without extension)')
    parser.add_argument('--output', '-o', help='Output HTML file path (default: <rom_name>.html)')
    parser.add_argument('--core', help='Override default core (e.g. nestopia, desmume). See ALT_CORES in source.')
    parser.add_argument('--color', '-c', default='#FF4444', help='EmulatorJS accent color (default: #FF4444)')
    parser.add_argument('--bios', '-b', help='Path to BIOS file (auto-searched in ./bios/, ../bios/, script_dir/bios/ if omitted)')
    parser.add_argument('--list-systems', action='store_true', help='List all supported systems and exit')
    parser.add_argument('--prefetch-all', action='store_true', help='Download all cores to cores/ directory for offline use')
    parser.add_argument('--offline-status', action='store_true', help='Show offline readiness status')

    args = parser.parse_args()

    if args.list_systems:
        print("\n🕹️  Supported Systems:\n")
        print(f"  {'System':12s}  {'Label':35s}  {'Core':25s}  Extensions")
        print(f"  {'─'*12}  {'─'*35}  {'─'*25}  {'─'*20}")
        for sid, info in sorted(SYSTEMS.items()):
            exts = ', '.join(info['extensions'])
            print(f"  {sid:12s}  {info['label']:35s}  {info['core']:25s}  {exts}")
        return


    if args.prefetch_all:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cores_dir = os.path.join(script_dir, OFFLINE_DIR_NAME)
        os.makedirs(cores_dir, exist_ok=True)
        print(f"\n📥 Prefetching all cores to {cores_dir}/")
        # Collect all cores: default systems + alternative cores
        unique_cores = sorted(set(
            [info['core'] for info in SYSTEMS.values()] +
            list(ALT_CORES.keys())
        ))
        cache_dir = get_cache_dir()
        # Download both normal and legacy variants for each core
        variants = ['-wasm.data', '-legacy-wasm.data']
        total_variants = len(unique_cores) * len(variants)
        idx = 0
        for core in unique_cores:
            for variant_suffix in variants:
                idx += 1
                fname = f"{core}{variant_suffix}"
                dest = os.path.join(cores_dir, fname)
                if os.path.isfile(dest):
                    print(f"  [{idx}/{total_variants}] ✅ {fname} (already present)")
                    continue
                cache_path = os.path.join(cache_dir, fname)
                if os.path.isfile(cache_path):
                    import shutil
                    shutil.copy2(cache_path, dest)
                    print(f"  [{idx}/{total_variants}] ✅ {fname} (copied from cache)")
                    continue
                print(f"  [{idx}/{total_variants}] ⬇️  Downloading {fname}...")
                try:
                    data = download_binary(EJS_CDN_BASE + f'cores/{fname}')
                    with open(dest, 'wb') as f:
                        f.write(data)
                except Exception:
                    print(f"  ❌ Failed to download {fname}")
        for asset in ['emulator.min.js', 'emulator.min.css']:
            dest = os.path.join(cores_dir, asset)
            if os.path.isfile(dest):
                print(f"  ✅ {asset} (already present)")
                continue
            cache_path = os.path.join(cache_dir, asset)
            if os.path.isfile(cache_path):
                import shutil
                shutil.copy2(cache_path, dest)
                print(f"  ✅ {asset} (copied from cache)")
                continue
            print(f"  ⬇️  Downloading {asset}...")
            data_text = download_text(EJS_CDN_BASE + asset)
            with open(dest, 'w', encoding='utf-8') as f:
                f.write(data_text)

        # Also prefetch extra assets for offline packing
        print(f"\n📥 Prefetching extra EmulatorJS assets...")
        for asset_path in ALL_EXTRA_ASSETS:
            filename = os.path.basename(asset_path)
            dest = os.path.join(cores_dir, filename)
            if os.path.isfile(dest):
                print(f"  ✅ {filename} (already present)")
                continue
            cache_path = os.path.join(cache_dir, filename)
            if os.path.isfile(cache_path):
                import shutil
                shutil.copy2(cache_path, dest)
                print(f"  ✅ {filename} (copied from cache)")
                continue
            print(f"  ⬇️  Downloading {filename}...")
            try:
                if asset_path in COMPRESSION_ASSETS_BINARY:
                    data = download_binary(EJS_CDN_BASE + asset_path)
                    with open(dest, 'wb') as f:
                        f.write(data)
                else:
                    data = download_text(EJS_CDN_BASE + asset_path)
                    with open(dest, 'w', encoding='utf-8') as f:
                        f.write(data)
            except Exception:
                print(f"  ❌ Failed to download {filename}")

        total = sum(os.path.getsize(os.path.join(cores_dir, f)) for f in os.listdir(cores_dir))
        print(f"\n✅ Offline bundle ready: {len(os.listdir(cores_dir))} files, {total/1024/1024:.1f} MB")
        print(f"   The script can now work 100% offline.")
        return

    if args.offline_status:
        offline_dir = get_offline_dir()
        cache_dir = get_cache_dir()
        unique_cores = sorted(set(
            [info['core'] for info in SYSTEMS.values()] +
            list(ALT_CORES.keys())
        ))
        print(f"\n📊 Offline Status:")
        if offline_dir:
            print(f"   Offline dir: {offline_dir} ✅")
        else:
            print(f"   Offline dir: not found (create with --prefetch-all)")
        ready = 0
        total_needed = len(unique_cores) * 2  # normal + legacy for each
        for core in unique_cores:
            for variant_suffix, variant_label in [('-wasm.data', ''), ('-legacy-wasm.data', ' (legacy)')]:
                fname = f"{core}{variant_suffix}"
                in_offline = offline_dir and os.path.isfile(os.path.join(offline_dir, fname))
                in_cache = os.path.isfile(os.path.join(cache_dir, fname))
                status = "✅ offline" if in_offline else ("📦 cached" if in_cache else "❌ missing")
                if in_offline or in_cache:
                    ready += 1
                print(f"   {core + variant_label:35s} {status}")
        # Check EJS assets
        for asset in ['emulator.min.js', 'emulator.min.css']:
            in_offline = offline_dir and os.path.isfile(os.path.join(offline_dir, asset))
            in_cache = os.path.isfile(os.path.join(cache_dir, asset))
            status = "✅ offline" if in_offline else ("📦 cached" if in_cache else "❌ missing")
            print(f"   {asset:25s} {status}")
        # Check extra assets
        print(f"\n   Extra assets (offline embedding):")
        for asset_path in ALL_EXTRA_ASSETS:
            filename = os.path.basename(asset_path)
            in_offline = offline_dir and os.path.isfile(os.path.join(offline_dir, filename))
            in_cache = os.path.isfile(os.path.join(cache_dir, filename))
            status = "✅ offline" if in_offline else ("📦 cached" if in_cache else "❌ missing")
            print(f"   {filename:25s} {status}")
        print(f"\n   {ready}/{total_needed} core variants available locally (normal + legacy)")
        return


    if not args.rom and not args.prefetch_all and not args.offline_status:
        parser.error("ROM file is required (use --list-systems to see supported systems)")

    if not os.path.isfile(args.rom):
        print(f"❌ File not found: {args.rom}")
        sys.exit(1)

    # Detect system
    system_id = args.system or detect_system(args.rom)
    system_info = SYSTEMS[system_id].copy()  # copy so we don't mutate the global
    # Override core if --core is specified
    if args.core:
        if args.core in ALT_CORES:
            system_info['core'] = args.core
            print(f"\n🔄 Using alternative core: {args.core} ({ALT_CORES[args.core]['label']})")
        elif args.core in [info['core'] for info in SYSTEMS.values()]:
            system_info['core'] = args.core
            print(f"\n🔄 Using core override: {args.core}")
        else:
            all_cores = sorted(set(info['core'] for info in SYSTEMS.values()) | set(ALT_CORES.keys()))
            print(f"❌ Unknown core: {args.core}")
            print(f"   Available cores: {', '.join(all_cores)}")
            sys.exit(1)
    print(f"\n🕹️  Universal Retro Game Packer")
    print(f"   System:  {system_info['label']} ({system_id})")
    print(f"   Core:    {system_info['core']}")

    # Read ROM
    print(f"\n📀 Reading ROM: {args.rom}")
    with open(args.rom, 'rb') as f:
        rom_data = f.read()
    rom_size_kb = len(rom_data) / 1024
    print(f"   Size: {rom_size_kb:.0f} KB ({len(rom_data)} bytes)")

    # D64 → PRG extraction for Commodore systems
    # The VICE WASM core hangs when loading .d64 disk images via True Drive Emulation.
    # Extracting the PRG program and feeding it directly works perfectly.
    rom_ext = os.path.splitext(args.rom)[1].lower()
    if rom_ext == '.d64' and system_id in ('c64', 'c128', 'vic20', 'pet', 'plus4'):
        print(f"\n🔄 D64 disk image detected — extracting PRG program...")
        prg_data, prg_name = extract_prg_from_d64(rom_data)
        if prg_data:
            print(f"   ✅ Extracted: {prg_name}.prg ({len(prg_data)} bytes)")
            print(f"   (VICE WASM cannot load .d64 via True Drive Emulation)")
            rom_data = prg_data
            # Update the ROM path for filename generation (.prg extension)
            args.rom = os.path.splitext(args.rom)[0] + '.prg'
        else:
            print(f"   ⚠️  No PRG file found in D64 image — packing as-is")
            print(f"   (Game may hang at BASIC screen if True Drive Emulation fails)")

    rom_b64 = base64.b64encode(rom_data).decode('ascii')
    print(f"   Base64: {len(rom_b64)} chars")

    # Title
    title = args.title or os.path.splitext(os.path.basename(args.rom))[0]
    # Clean up title: replace underscores with spaces, title-case
    if not args.title:
        title = title.replace('_', ' ').replace('-', ' ')
        # Don't auto-titlecase if it contains uppercase already
        if title == title.lower():
            title = title.title()
    print(f"   Title: {title}")

    # Cache directory
    cache_dir = get_cache_dir()
    offline_dir = get_offline_dir()
    print(f"\n📦 Loading EmulatorJS assets...")

    # Load EmulatorJS CSS (offline dir > cache > CDN)
    ejs_css_path = os.path.join(cache_dir, 'emulator.min.css')
    offline_css_path = os.path.join(offline_dir, 'emulator.min.css') if offline_dir else None
    if offline_css_path and os.path.isfile(offline_css_path):
        with open(offline_css_path, 'r', encoding='utf-8') as f:
            ejs_css = f.read()
        print(f"  ✅ Offline: emulator.min.css ({len(ejs_css) // 1024} KB)")
    elif os.path.isfile(ejs_css_path):
        with open(ejs_css_path, 'r', encoding='utf-8') as f:
            ejs_css = f.read()
        print(f"  ✅ Cached: emulator.min.css ({len(ejs_css) // 1024} KB)")
    else:
        ejs_css = download_text(EJS_CDN_BASE + 'emulator.min.css', ejs_css_path)

    # Load EmulatorJS Engine JS (offline dir > cache > CDN)
    ejs_js_path = os.path.join(cache_dir, 'emulator.min.js')
    offline_js_path = os.path.join(offline_dir, 'emulator.min.js') if offline_dir else None
    if offline_js_path and os.path.isfile(offline_js_path):
        with open(offline_js_path, 'r', encoding='utf-8') as f:
            ejs_engine_js = f.read()
        print(f"  ✅ Offline: emulator.min.js ({len(ejs_engine_js) // 1024} KB)")
    elif os.path.isfile(ejs_js_path):
        with open(ejs_js_path, 'r', encoding='utf-8') as f:
            ejs_engine_js = f.read()
        print(f"  ✅ Cached: emulator.min.js ({len(ejs_engine_js) // 1024} KB)")
    else:
        ejs_engine_js = download_text(EJS_CDN_BASE + 'emulator.min.js', ejs_js_path)

    # Download Core WASM data (normal + legacy variants)
    core_name = system_info['core']
    print(f"\n⚙️  Loading emulator core: {core_name}")

    # Normal core
    core_filename = f"{core_name}-wasm.data"
    core_cache_path = os.path.join(cache_dir, core_filename)
    offline_core_path = os.path.join(offline_dir, core_filename) if offline_dir else None
    if offline_core_path and os.path.isfile(offline_core_path):
        with open(offline_core_path, 'rb') as f:
            core_data = f.read()
        print(f"  ✅ Offline: {core_filename} ({len(core_data) / 1024:.0f} KB)")
    else:
        core_data = download_binary(EJS_CDN_BASE + f'cores/{core_filename}', core_cache_path)
    core_b64 = base64.b64encode(core_data).decode('ascii')
    print(f"   Core size: {len(core_data) / 1024:.0f} KB → Base64: {len(core_b64)} chars")

    # Legacy core (for browsers without WebGL2 or when defaultWebGL2 is false)
    core_legacy_filename = f"{core_name}-legacy-wasm.data"
    core_legacy_cache_path = os.path.join(cache_dir, core_legacy_filename)
    offline_legacy_path = os.path.join(offline_dir, core_legacy_filename) if offline_dir else None
    if offline_legacy_path and os.path.isfile(offline_legacy_path):
        with open(offline_legacy_path, 'rb') as f:
            core_legacy_data = f.read()
        print(f"  ✅ Offline: {core_legacy_filename} ({len(core_legacy_data) / 1024:.0f} KB)")
    else:
        core_legacy_data = download_binary(EJS_CDN_BASE + f'cores/{core_legacy_filename}', core_legacy_cache_path)
    core_legacy_b64 = base64.b64encode(core_legacy_data).decode('ascii')
    print(f"   Legacy core size: {len(core_legacy_data) / 1024:.0f} KB → Base64: {len(core_legacy_b64)} chars")

    # ── NEW: Download extra assets for 100% offline support ──
    print(f"\n📦 Loading extra EmulatorJS assets (offline support)...")
    extra_assets = download_extra_assets(cache_dir, offline_dir)

    # ── BIOS embedding for systems that require it ──
    if 'bios' in system_info:
        bios_filename = system_info['bios']
        bios_path = None

        if args.bios:
            # Explicit --bios argument
            if os.path.isfile(args.bios):
                bios_path = args.bios
            else:
                print(f"❌ BIOS file not found: {args.bios}")
                sys.exit(1)
        else:
            # Auto-search in common locations
            script_dir = os.path.dirname(os.path.abspath(__file__))
            rom_dir = os.path.dirname(os.path.abspath(args.rom))
            search_dirs = [
                os.path.join(rom_dir, 'bios'),
                rom_dir,
                os.path.join(script_dir, 'bios'),
                os.path.join(script_dir, '..', '..', 'bios'),
                os.path.join(script_dir, '..', '..', 'docs', 'data', 'bios'),
                script_dir,
                '.',
                os.path.join('.', 'bios'),
            ]
            for search_dir in search_dirs:
                candidate = os.path.join(search_dir, bios_filename)
                if os.path.isfile(candidate):
                    bios_path = candidate
                    break

        if bios_path:
            with open(bios_path, 'rb') as f:
                bios_data = f.read()
            extra_assets[bios_filename] = base64.b64encode(bios_data).decode('ascii')
            print(f"\n🧬 BIOS: {bios_filename} ({len(bios_data)} bytes) — embedded from {bios_path}")
        else:
            print(f"\n⚠️  BIOS required: {bios_filename} (for {system_info['label']})")
            print(f"   Searched in: {', '.join(search_dirs)}")
            print(f"   Use --bios <path> to specify the BIOS file location.")
            print(f"   The game may not boot without it!")

    extra_assets_json = json.dumps(extra_assets)
    extra_size_kb = len(extra_assets_json) / 1024
    print(f"   Total extra assets: {len(extra_assets)} files, {extra_size_kb:.0f} KB (base64)")

    # Generate HTML
    print(f"\n🏗️  Generating HTML...")
    html = generate_html(args.rom, title, system_id, ejs_css, ejs_engine_js, core_b64, core_legacy_b64, rom_b64, extra_assets_json)

    # Output
    output_path = args.output or os.path.splitext(args.rom)[0] + '.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(output_path) / 1024
    size_mb = size_kb / 1024
    print(f"\n{'='*60}")
    print(f"  ✅ Done! Output: {output_path}")
    print(f"  📦 Size: {size_mb:.1f} MB ({size_kb:.0f} KB)")
    print(f"  🎮 System: {system_info['label']}")
    print(f"  🎯 Title: {title}")
    print(f"  🔌 100% offline — no internet needed")
    print(f"  📱 Mobile touch controls included (EmulatorJS)")
    print(f"  🌐 Open in any modern browser")
    print(f"  🛡️  3-layer offline: EJS_paths + fetch/XHR + script interception")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
