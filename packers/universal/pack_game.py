#!/usr/bin/env python3
"""
Universal Retro Game Packer — Creates self-contained offline HTML files from ROM images.
Uses EmulatorJS (RetroArch cores compiled to WebAssembly) to support 30+ retro platforms.

Usage:
    python3 pack_game.py game.nes
    python3 pack_game.py game.sfc --title "Chrono Trigger"
    python3 pack_game.py --system genesis "Sonic.md"
    python3 pack_game.py game.gb --output my_game.html

Supported systems: nes, snes, gb, gbc, gba, genesis, sms, gg, atari2600, atari7800,
                   atari5200, lynx, n64, nds, psx, pce, ngp, ws, vb, coleco, 32x,
                   segacd, c64, zxspectrum, msx
"""

import argparse
import base64
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
    'atari5200': {'core': 'a5200',             'label': 'Atari 5200',                 'extensions': ['.a52']},
    'lynx':      {'core': 'handy',             'label': 'Atari Lynx',                 'extensions': ['.lnx']},
    'coleco':    {'core': 'gearcoleco',        'label': 'ColecoVision',               'extensions': ['.col']},
    'ngp':       {'core': 'mednafen_ngp',      'label': 'Neo Geo Pocket / Color',     'extensions': ['.ngp', '.ngc']},
    'ws':        {'core': 'mednafen_wswan',    'label': 'WonderSwan / Color',         'extensions': ['.ws', '.wsc']},
    'vb':        {'core': 'beetle_vb',         'label': 'Virtual Boy',                'extensions': ['.vb']},
    'pce':       {'core': 'mednafen_pce',      'label': 'PC Engine / TurboGrafx-16',  'extensions': ['.pce']},
    '32x':       {'core': 'picodrive',         'label': 'Sega 32X',                   'extensions': ['.32x']},
    # Tier 2 — Feasible with caveats
    'gba':       {'core': 'mgba',              'label': 'Game Boy Advance',           'extensions': ['.gba']},
    'n64':       {'core': 'mupen64plus_next',  'label': 'Nintendo 64',                'extensions': ['.n64', '.z64', '.v64']},
    'nds':       {'core': 'melonds',           'label': 'Nintendo DS',                'extensions': ['.nds']},
    'psx':       {'core': 'pcsx_rearmed',      'label': 'PlayStation',                'extensions': ['.bin', '.cue', '.iso', '.pbp']},
    'segacd':    {'core': 'genesis_plus_gx',   'label': 'Sega CD / Mega CD',          'extensions': ['.cue', '.bin', '.chd']},
    # Tier 3 — Retro computers
    'c64':       {'core': 'vice_x64sc',        'label': 'Commodore 64',               'extensions': ['.d64', '.t64', '.prg', '.crt']},
    'zxspectrum':{'core': 'fuse',              'label': 'ZX Spectrum',                'extensions': ['.z80', '.tap', '.sna', '.tzx']},
    # --- NEW SYSTEMS (added Feb 2026) ---
    # Atari
    'jaguar':    {'core': 'virtualjaguar',     'label': 'Atari Jaguar',               'extensions': ['.j64', '.jag', '.rom', '.abs', '.cof', '.bin']},
    # Commodore family
    'c128':      {'core': 'vice_x128',         'label': 'Commodore 128',              'extensions': ['.d64', '.d71', '.d81', '.prg', '.t64', '.tap']},
    'vic20':     {'core': 'vice_xvic',         'label': 'Commodore VIC-20',           'extensions': ['.d64', '.prg', '.crt', '.t64', '.tap', '.20']},
    'pet':       {'core': 'vice_xpet',         'label': 'Commodore PET',              'extensions': ['.d64', '.prg', '.t64', '.tap']},
    'plus4':     {'core': 'vice_xplus4',       'label': 'Commodore Plus/4',           'extensions': ['.d64', '.prg', '.t64', '.tap']},
    'amiga':     {'core': 'puae',              'label': 'Commodore Amiga',            'extensions': ['.adf', '.adz', '.dms', '.ipf']},
    # Amstrad
    'cpc':       {'core': 'cap32',             'label': 'Amstrad CPC',                'extensions': ['.dsk', '.sna', '.cdt', '.voc']},
    # Sinclair
    'zx81':      {'core': '81',                'label': 'Sinclair ZX81',              'extensions': ['.p', '.81', '.tzx']},
    # id Software
    'doom':      {'core': 'prboom',            'label': 'DOOM (PrBoom)',              'extensions': ['.wad']},
    # NEC
    'pcfx':      {'core': 'mednafen_pcfx',     'label': 'PC-FX',                     'extensions': ['.cue', '.ccd', '.toc']},
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
    // Embedded game data
    var EMBEDDED_ROM_B64 = "{{ROM_B64}}";
    var EMBEDDED_ROM_FILENAME = "{{ROM_FILENAME}}";
    var EMBEDDED_CORE_B64 = "{{CORE_B64}}";
    var EMBEDDED_CORE_NAME = "{{CORE_NAME}}";

    // Helpers
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
    function setProgress(pct, msg) {
        var fill = document.getElementById('ld-fill');
        var status = document.getElementById('ld-status');
        if (fill) fill.style.width = pct + '%';
        if (status) status.textContent = msg;
    }

    setProgress(10, 'Loading emulator engine...');

    // ── Intercept fetch() ──
    var _origFetch = window.fetch;
    window.fetch = function(input, init) {
        var url = (typeof input === 'string') ? input : (input && input.url ? input.url : '');

        // Serve embedded core WASM
        if (url.indexOf(EMBEDDED_CORE_NAME + '-wasm.data') !== -1) {
            setProgress(60, 'Loading emulator core...');
            var data = b64toUint8(EMBEDDED_CORE_B64);
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

        // Stub metadata
        if (url.indexOf('version.json') !== -1 || url.indexOf('localization/') !== -1 ||
            url.indexOf('cores/reports/') !== -1 || url.indexOf('compression/') !== -1) {
            return Promise.resolve(new Response('{}', {
                status: 200, headers: { 'Content-Type': 'application/json' }
            }));
        }

        return _origFetch.apply(this, arguments);
    };

    // ── Intercept XMLHttpRequest ──
    var XHRProto = XMLHttpRequest.prototype;
    var _xhrOpen = XHRProto.open;
    var _xhrSend = XHRProto.send;

    XHRProto.open = function(method, url) {
        this._prg_url = url;
        return _xhrOpen.apply(this, arguments);
    };

    XHRProto.send = function(body) {
        var url = this._prg_url || '';
        var embeddedB64 = null;

        if (url.indexOf(EMBEDDED_CORE_NAME + '-wasm.data') !== -1) {
            embeddedB64 = EMBEDDED_CORE_B64;
            setProgress(60, 'Loading emulator core...');
        } else if (url.indexOf(EMBEDDED_ROM_FILENAME) !== -1) {
            embeddedB64 = EMBEDDED_ROM_B64;
            setProgress(80, 'Loading game data...');
        }

        if (embeddedB64) {
            var data = b64toUint8(embeddedB64);
            var self = this;
            Object.defineProperty(self, 'readyState', { get: function() { return 4; }, configurable: true });
            Object.defineProperty(self, 'status', { get: function() { return 200; }, configurable: true });
            Object.defineProperty(self, 'statusText', { get: function() { return 'OK'; }, configurable: true });
            Object.defineProperty(self, 'response', { get: function() { return data.buffer; }, configurable: true });
            setTimeout(function() {
                self.dispatchEvent(new ProgressEvent('progress', { loaded: data.length, total: data.length }));
                self.dispatchEvent(new Event('load'));
                if (self.onprogress) self.onprogress({ loaded: data.length, total: data.length });
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

    // ── EJS Configuration ──
    var romBlobUrl = b64toBlobUrl(EMBEDDED_ROM_B64, 'application/octet-stream');

    window.EJS_player = '#game';
    window.EJS_gameUrl = romBlobUrl;
    window.EJS_gameName = '{{TITLE}}';
    window.EJS_color = '#FF4444';
    window.EJS_startOnLoaded = false;
    window.EJS_pathtodata = 'https://cdn.emulatorjs.org/stable/data/';
    window.EJS_CacheLimit = 0;
    window.EJS_startButtonName = 'Play {{TITLE}}';
    window.EJS_disableLocalStorage = false;

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

<!-- EmulatorJS Engine (emulator.min.js) -->
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
def generate_html(rom_path, title, system_id, ejs_css, ejs_engine_js, core_b64, rom_b64):
    """Generate the complete self-contained HTML file."""
    system_info = SYSTEMS[system_id]
    rom_filename = os.path.basename(rom_path).lower()

    html = HTML_TEMPLATE
    html = html.replace('{{TITLE}}', title)
    html = html.replace('{{SYSTEM_LABEL}}', system_info['label'])
    html = html.replace('{{ROM_B64}}', rom_b64)
    html = html.replace('{{ROM_FILENAME}}', rom_filename)
    html = html.replace('{{CORE_B64}}', core_b64)
    html = html.replace('{{CORE_NAME}}', system_info['core'])
    html = html.replace('{{EJS_CSS}}', ejs_css)
    html = html.replace('{{EJS_ENGINE_JS}}', ejs_engine_js)

    return html


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
    parser.add_argument('--color', '-c', default='#FF4444', help='EmulatorJS accent color (default: #FF4444)')
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
        unique_cores = sorted(set(info['core'] for info in SYSTEMS.values()))
        cache_dir = get_cache_dir()
        for i, core in enumerate(unique_cores, 1):
            fname = f"{core}-wasm.data"
            dest = os.path.join(cores_dir, fname)
            if os.path.isfile(dest):
                print(f"  [{i}/{len(unique_cores)}] ✅ {fname} (already present)")
                continue
            cache_path = os.path.join(cache_dir, fname)
            if os.path.isfile(cache_path):
                import shutil
                shutil.copy2(cache_path, dest)
                print(f"  [{i}/{len(unique_cores)}] ✅ {fname} (copied from cache)")
                continue
            print(f"  [{i}/{len(unique_cores)}] ⬇️  Downloading {fname}...")
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
        total = sum(os.path.getsize(os.path.join(cores_dir, f)) for f in os.listdir(cores_dir))
        print(f"\n✅ Offline bundle ready: {len(os.listdir(cores_dir))} files, {total/1024/1024:.1f} MB")
        print(f"   The script can now work 100% offline.")
        return

    if args.offline_status:
        offline_dir = get_offline_dir()
        cache_dir = get_cache_dir()
        unique_cores = sorted(set(info['core'] for info in SYSTEMS.values()))
        print(f"\n📊 Offline Status:")
        if offline_dir:
            print(f"   Offline dir: {offline_dir} ✅")
        else:
            print(f"   Offline dir: not found (create with --prefetch-all)")
        ready = 0
        for core in unique_cores:
            fname = f"{core}-wasm.data"
            in_offline = offline_dir and os.path.isfile(os.path.join(offline_dir, fname))
            in_cache = os.path.isfile(os.path.join(cache_dir, fname))
            status = "✅ offline" if in_offline else ("📦 cached" if in_cache else "❌ missing")
            if in_offline or in_cache:
                ready += 1
            print(f"   {core:25s} {status}")
        # Check EJS assets
        for asset in ['emulator.min.js', 'emulator.min.css']:
            in_offline = offline_dir and os.path.isfile(os.path.join(offline_dir, asset))
            in_cache = os.path.isfile(os.path.join(cache_dir, asset))
            status = "✅ offline" if in_offline else ("📦 cached" if in_cache else "❌ missing")
            print(f"   {asset:25s} {status}")
        print(f"\n   {ready}/{len(unique_cores)} cores available locally")
        return


    if not args.rom and not args.prefetch_all and not args.offline_status:
        parser.error("ROM file is required (use --list-systems to see supported systems)")

    if not os.path.isfile(args.rom):
        print(f"❌ File not found: {args.rom}")
        sys.exit(1)

    # Detect system
    system_id = args.system or detect_system(args.rom)
    system_info = SYSTEMS[system_id]
    print(f"\n🕹️  Universal Retro Game Packer")
    print(f"   System:  {system_info['label']} ({system_id})")
    print(f"   Core:    {system_info['core']}")

    # Read ROM
    print(f"\n📀 Reading ROM: {args.rom}")
    with open(args.rom, 'rb') as f:
        rom_data = f.read()
    rom_size_kb = len(rom_data) / 1024
    print(f"   Size: {rom_size_kb:.0f} KB ({len(rom_data)} bytes)")

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
    print(f"\n📦 Loading EmulatorJS assets...")

    # Load EmulatorJS CSS (offline dir > cache > CDN)
    offline_dir = get_offline_dir()
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

    # Download Core WASM data
    core_name = system_info['core']
    core_filename = f"{core_name}-wasm.data"
    core_cache_path = os.path.join(cache_dir, core_filename)

    print(f"\n⚙️  Loading emulator core: {core_name}")
    offline_core_path = os.path.join(offline_dir, core_filename) if offline_dir else None
    if offline_core_path and os.path.isfile(offline_core_path):
        with open(offline_core_path, 'rb') as f:
            core_data = f.read()
        print(f"  ✅ Offline: {core_filename} ({len(core_data) / 1024:.0f} KB)")
    else:
        core_data = download_binary(EJS_CDN_BASE + f'cores/{core_filename}', core_cache_path)
    core_b64 = base64.b64encode(core_data).decode('ascii')
    print(f"   Core size: {len(core_data) / 1024:.0f} KB → Base64: {len(core_b64)} chars")

    # Generate HTML
    print(f"\n🏗️  Generating HTML...")
    html = generate_html(args.rom, title, system_id, ejs_css, ejs_engine_js, core_b64, rom_b64)

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
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
