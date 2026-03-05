#!/usr/bin/env python3
"""
DOS Game Packer — Creates a self-contained offline HTML page from a DOS game ZIP.
Embeds js-dos 6.22 (asyncify) emulator + game files + virtual mobile keyboard.

No server needed, works from file:// protocol.

Usage:
    python3 pack_dos_game.py game.zip
    python3 pack_dos_game.py game.zip --title "Prince of Persia"
    python3 pack_dos_game.py game.zip --exe PRINCE.EXE
    python3 pack_dos_game.py game.zip --cycles max --memory 32
    python3 pack_dos_game.py game.zip --analyze-only

Supported formats: .zip (containing DOS executables + data files)

Engine: js-dos 6.22 (asyncify / mono-thread)
  - No SharedArrayBuffer needed
  - No COOP/COEP headers needed
  - Works 100% offline from file:// protocol
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.request
import zipfile

# ============================================================
#  Constants
# ============================================================

JSDOS_VERSION = "6.22"
JSDOS_CDN_BASE = "https://js-dos.com/6.22/current/"
JSDOS_FILES = {
    "js-dos.js":         JSDOS_CDN_BASE + "js-dos.js",
    "wdosbox.js":        JSDOS_CDN_BASE + "wdosbox.js",
    "wdosbox.wasm.js":   JSDOS_CDN_BASE + "wdosbox.wasm.js",
}

# DOS executable extensions (priority order)
DOS_EXE_EXTENSIONS = ['.exe', '.com', '.bat']

# Common DOS game executables to auto-detect
KNOWN_GAME_EXES = [
    # Well-known games
    'DOOM.EXE', 'DOOM2.EXE', 'DUKE3D.EXE', 'WOLF3D.EXE',
    'PRINCE.EXE', 'DIGGER.COM', 'KEEN1.EXE', 'KEEN4.EXE',
    'MONKEY.EXE', 'MONKEY2.EXE', 'LOOM.EXE', 'INDY.EXE',
    'DOTT.EXE', 'SAMNMAX.EXE', 'TENTACLE.EXE',
    'SIMCITY.EXE', 'SC2000.EXE', 'LEMMINGS.EXE',
    'ALLEYCAT.EXE', 'DAVE.EXE', 'GORILLA.BAS',
    # Common launchers
    'GAME.EXE', 'PLAY.EXE', 'START.EXE', 'RUN.EXE',
    'MAIN.EXE', 'GO.BAT', 'PLAY.BAT', 'START.BAT', 'RUN.BAT',
    'INSTALL.EXE', 'SETUP.EXE',
]

# ============================================================
#  ZIP Analysis
# ============================================================

def analyze_zip(zip_path):
    """Analyze a DOS game ZIP and return metadata."""
    info = {
        'files': [],
        'executables': [],
        'total_size': 0,
        'file_count': 0,
        'has_subdirs': False,
        'root_dir': None,
    }

    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = zf.namelist()
        info['file_count'] = len(names)

        # Detect if all files are in a subdirectory
        dirs = set()
        for name in names:
            parts = name.replace('\\', '/').split('/')
            if len(parts) > 1 and parts[0]:
                dirs.add(parts[0])

        if len(dirs) == 1 and all(
            n.replace('\\', '/').startswith(list(dirs)[0] + '/') or n.replace('\\', '/') == list(dirs)[0] + '/'
            for n in names if n.strip('/')
        ):
            info['root_dir'] = list(dirs)[0]
            info['has_subdirs'] = True

        for zi in zf.infolist():
            if zi.is_dir():
                continue

            name = zi.filename.replace('\\', '/')
            basename = os.path.basename(name).upper()
            ext = os.path.splitext(basename)[1]
            size = zi.file_size
            info['total_size'] += size

            file_info = {
                'path': name,
                'basename': basename,
                'ext': ext,
                'size': size,
            }
            info['files'].append(file_info)

            if ext in [e.upper() for e in DOS_EXE_EXTENSIONS]:
                file_info['priority'] = _exe_priority(basename)
                info['executables'].append(file_info)

    # Sort executables by priority (lower = better)
    info['executables'].sort(key=lambda x: x.get('priority', 999))

    return info


def _exe_priority(basename):
    """Assign priority to an executable (lower = more likely the game)."""
    upper = basename.upper()

    # Known game executables get top priority
    if upper in [k.upper() for k in KNOWN_GAME_EXES]:
        return 10

    # Skip installers/setup
    if upper in ('INSTALL.EXE', 'SETUP.EXE', 'INSTALL.COM', 'SETUP.COM',
                 'SETSOUND.EXE', 'SNDSETUP.EXE', 'CONFIG.EXE'):
        return 900

    # GAME/PLAY/START/RUN/MAIN get high priority
    name = os.path.splitext(upper)[0]
    if name in ('GAME', 'PLAY', 'START', 'RUN', 'MAIN', 'GO'):
        return 20

    # .BAT files that are launchers
    if upper.endswith('.BAT'):
        return 50

    # .EXE files
    if upper.endswith('.EXE'):
        return 100

    # .COM files
    if upper.endswith('.COM'):
        return 150

    return 500


def detect_executable(zip_info):
    """Auto-detect the main game executable from ZIP analysis."""
    exes = zip_info['executables']
    if not exes:
        return None

    # Return highest priority
    return exes[0]['basename']


# ============================================================
#  Asset Downloading / Caching
# ============================================================

def download_asset(url, cache_path):
    """Download a file with caching."""
    if os.path.isfile(cache_path):
        with open(cache_path, 'rb') as f:
            data = f.read()
        if len(data) > 0:
            return data

    os.makedirs(os.path.dirname(cache_path) or '.', exist_ok=True)
    print(f"   Downloading {url}...")

    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (portable-retro-games packer)'
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()

    with open(cache_path, 'wb') as f:
        f.write(data)

    return data


def load_jsdos_assets(cache_dir):
    """Download/cache all js-dos 6.22 files."""
    assets = {}
    for filename, url in JSDOS_FILES.items():
        cache_path = os.path.join(cache_dir, filename)
        data = download_asset(url, cache_path)
        assets[filename] = data
        print(f"   {filename}: {len(data):,} bytes ({len(data)//1024} KB)")
    return assets


# ============================================================
#  DOSBox Configuration
# ============================================================

def generate_dosbox_conf(exe_name, cycles='auto', memory=16, sound='sb16',
                          fullscreen=False, mount_point='C', extra_conf=None,
                          root_dir=None):
    """Generate a dosbox.conf content string.
    
    IMPORTANT: No [autoexec] section! js-dos 6.22 unshifts 'mount c .' which
    mounts the Emscripten CWD (often /home/web_user) as C:, but fs.extract()
    puts files at '/'. To fix this, the launch commands are passed via -c args
    to main() in the JavaScript, which re-mounts C: to '/' explicitly.
    The config only contains settings sections.
    """
    conf = f"""[sdl]
fullscreen=false
autolock=true
sensitivity=100
waitonerror=true

[dosbox]
machine=svga_s3
memsize={memory}

[cpu]
core=auto
cputype=auto
cycles={cycles}

[mixer]
nosound=false
rate=44100
blocksize=1024
prebuffer=20

[sblaster]
sbtype={sound}
sbbase=220
irq=7
dma=1
hdma=5
sbmixer=true
oplmode=auto
oplemu=default
oplrate=44100

[gus]
gus=false

[speaker]
pcspeaker=true
pcrate=44100
tandy=auto
tandyrate=44100

[joystick]
joysticktype=auto
timed=true
autofire=false
swap34=false
buttonwrap=false

[serial]
serial1=dummy
serial2=dummy
serial3=disabled
serial4=disabled

[dos]
xms=true
ems=true
umb=true

[ipx]
ipx=false
"""
    if extra_conf:
        # Append extra config sections at the end
        conf += '\n' + extra_conf + '\n'

    return conf


# ============================================================
#  HTML Generation
# ============================================================

def generate_html(game_zip_path, title, exe_name, jsdos_assets, dosbox_conf,
                   keyboard_layout='default', root_dir=None):
    """Generate a single self-contained HTML file with embedded DOS emulator."""

    # Encode assets
    jsdos_js = jsdos_assets['js-dos.js'].decode('utf-8', errors='replace')
    wdosbox_js_text = jsdos_assets['wdosbox.js'].decode('utf-8', errors='replace')
    wdosbox_wasm_b64 = base64.b64encode(jsdos_assets['wdosbox.wasm.js']).decode('ascii')
    wdosbox_js_b64 = base64.b64encode(jsdos_assets['wdosbox.js']).decode('ascii')

    # Encode game ZIP
    with open(game_zip_path, 'rb') as f:
        game_data = f.read()
    game_b64 = base64.b64encode(game_data).decode('ascii')
    game_size_kb = len(game_data) // 1024

    # Encode dosbox.conf
    dosbox_conf_b64 = base64.b64encode(dosbox_conf.encode('utf-8')).decode('ascii')

    # Determine virtual keyboard layout
    vkb_html, vkb_js = _generate_virtual_keyboard(keyboard_layout)

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#000000">
<title>{_html_escape(title)} — DOS</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{
    width: 100%; height: 100%;
    background: #000;
    color: #ccc;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    overflow: hidden;
    touch-action: none;
    -webkit-user-select: none;
    user-select: none;
}}

/* Loading screen */
#loading {{
    position: fixed; inset: 0;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    background: #000;
    z-index: 9999;
    transition: opacity 0.5s;
}}
#loading.fade {{ opacity: 0; pointer-events: none; }}
#loading h1 {{
    font-size: 1.5rem; color: #fff;
    margin-bottom: 1rem;
    text-align: center;
    padding: 0 1rem;
}}
#loading .subtitle {{
    font-size: 0.85rem; color: #888;
    margin-bottom: 1.5rem;
}}
#progress-bar {{
    width: 280px; max-width: 80%;
    height: 6px; background: #222;
    border-radius: 3px; overflow: hidden;
}}
#progress-fill {{
    height: 100%; width: 0%;
    background: linear-gradient(90deg, #00aaff, #00ddff);
    border-radius: 3px;
    transition: width 0.3s;
}}
#loading-status {{
    margin-top: 0.8rem;
    font-size: 0.75rem; color: #666;
}}

/* Canvas container */
#canvas-wrap {{
    position: fixed; inset: 0;
    display: flex; align-items: center; justify-content: center;
    background: #000;
}}
#canvas-wrap canvas {{
    max-width: 100%; max-height: 100%;
    image-rendering: pixelated;
    image-rendering: crisp-edges;
    cursor: default;
}}

/* Controls overlay */
#controls {{
    position: fixed;
    bottom: 8px; left: 50%;
    transform: translateX(-50%);
    z-index: 100;
    display: flex; align-items: center; gap: 8px;
    background: rgba(0,0,0,0.75);
    padding: 6px 14px;
    border-radius: 20px;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    transition: opacity 0.3s;
}}
#controls.hidden {{ opacity: 0; pointer-events: none; }}
#controls button {{
    background: rgba(255,255,255,0.1);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 6px;
    font-size: 0.8rem;
    padding: 5px 10px;
    cursor: pointer;
    white-space: nowrap;
}}
#controls button:active {{ background: rgba(255,255,255,0.25); }}
#controls button.active {{ background: rgba(0,150,255,0.4); border-color: rgba(0,150,255,0.6); }}

#toggle-ctrl {{
    position: fixed; bottom: 8px; right: 8px;
    z-index: 101;
    background: rgba(0,0,0,0.5);
    color: rgba(255,255,255,0.6);
    border: none; border-radius: 50%;
    width: 36px; height: 36px;
    font-size: 1.1rem;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
}}

/* ======== GAMEPAD OVERLAY ======== */
#gamepad {{
    position: fixed; inset: 0; z-index: 99;
    pointer-events: none;
    display: none;
}}
#gamepad.show {{ display: block; }}

/* D-pad — left side, angle-based touch zone */
#gp-dpad {{
    position: absolute;
    bottom: 25px; left: 12px;
    width: clamp(120px, 28vw, 170px);
    height: clamp(120px, 28vw, 170px);
    pointer-events: auto;
    touch-action: none;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.08) 100%);
    border: 2px solid rgba(255,255,255,0.1);
}}
/* D-pad visual arrows */
.dp-arrow {{
    position: absolute; display: flex;
    align-items: center; justify-content: center;
    color: rgba(255,255,255,0.35);
    font-size: 1.6rem;
    transition: color 0.08s, transform 0.08s;
    pointer-events: none;
}}
.dp-arrow.active {{ color: rgba(0,170,255,0.9); transform: scale(1.2); }}
.dp-up    {{ top: 6px; left: 50%; transform: translateX(-50%); }}
.dp-down  {{ bottom: 6px; left: 50%; transform: translateX(-50%); }}
.dp-left  {{ left: 6px; top: 50%; transform: translateY(-50%); }}
.dp-right {{ right: 6px; top: 50%; transform: translateY(-50%); }}
.dp-up.active    {{ transform: translateX(-50%) scale(1.2); }}
.dp-down.active  {{ transform: translateX(-50%) scale(1.2); }}
.dp-left.active  {{ transform: translateY(-50%) scale(1.2); }}
.dp-right.active {{ transform: translateY(-50%) scale(1.2); }}
/* D-pad center dot */
.dp-center {{
    position: absolute; top: 50%; left: 50%;
    width: 18px; height: 18px;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.18);
    pointer-events: none;
}}

/* Action buttons — right side, diamond layout */
#gp-actions {{
    position: absolute;
    bottom: 25px; right: 12px;
    width: clamp(120px, 28vw, 160px);
    height: clamp(120px, 28vw, 160px);
    pointer-events: auto;
    touch-action: none;
}}
.gp-btn {{
    position: absolute;
    width: 52px; height: 52px;
    border-radius: 50%;
    background: rgba(255,255,255,0.10);
    color: rgba(255,255,255,0.55);
    border: 2px solid rgba(255,255,255,0.15);
    font-size: 0.75rem; font-weight: 700;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    display: flex; align-items: center; justify-content: center;
    pointer-events: auto; touch-action: none;
    transition: background 0.08s, border-color 0.08s, color 0.08s;
    -webkit-user-select: none; user-select: none;
}}
.gp-btn.active {{
    background: rgba(0,150,255,0.45);
    border-color: rgba(0,170,255,0.7);
    color: #fff;
}}
/* diamond positions (relative to container) */
.gp-btn.btn-a {{ bottom: 0; left: 50%; transform: translateX(-50%); }}
.gp-btn.btn-b {{ left: 0; top: 50%; transform: translateY(-50%); }}
.gp-btn.btn-x {{ right: 0; top: 50%; transform: translateY(-50%); }}
.gp-btn.btn-y {{ top: 0; left: 50%; transform: translateX(-50%); }}

/* System bar — bottom center */
#gp-sysbar {{
    position: absolute;
    bottom: 6px; left: 50%;
    transform: translateX(-50%);
    display: flex; gap: 5px;
    pointer-events: auto; touch-action: none;
    background: rgba(0,0,0,0.5);
    border-radius: 12px; padding: 3px 6px;
}}
#gp-sysbar button {{
    min-width: 32px; height: 28px;
    background: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.45);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 5px;
    font-size: 0.6rem; font-family: monospace;
    display: flex; align-items: center; justify-content: center;
    -webkit-user-select: none; user-select: none;
    touch-action: none;
}}
#gp-sysbar button:active,
#gp-sysbar button.active {{
    background: rgba(0,150,255,0.35);
    color: #fff;
}}

/* ======== KEYBOARD OVERLAY (fallback / adventure) ======== */
#vkb {{
    position: fixed;
    bottom: 50px; left: 50%;
    transform: translateX(-50%);
    z-index: 99;
    display: none;
    flex-wrap: wrap;
    justify-content: center;
    gap: 4px;
    padding: 8px;
    background: rgba(0,0,0,0.88);
    border-radius: 12px;
    backdrop-filter: blur(8px);
    max-width: 98vw;
}}
#vkb.show {{ display: flex; }}
#vkb button {{
    min-width: 40px; height: 40px;
    background: rgba(255,255,255,0.12);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 6px;
    font-size: 0.8rem;
    font-family: monospace;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    -webkit-user-select: none; user-select: none;
    touch-action: none;
}}
#vkb button:active {{ background: rgba(255,255,255,0.3); }}
#vkb button.wide {{ min-width: 64px; }}
#vkb button.space {{ min-width: 100px; }}

@media (max-width: 600px) {{
    .gp-btn {{ width: 48px; height: 48px; font-size: 0.7rem; }}
    #vkb button {{ min-width: 36px; height: 36px; font-size: 0.7rem; }}
    #vkb button.wide {{ min-width: 54px; }}
}}

/* Error screen */
#error-screen {{
    display: none;
    position: fixed; inset: 0;
    background: #1a0000;
    color: #ff6666;
    padding: 2rem;
    z-index: 10000;
    text-align: center;
    justify-content: center;
    align-items: center;
    flex-direction: column;
}}
#error-screen h2 {{ margin-bottom: 1rem; }}
#error-screen pre {{
    background: #220000;
    padding: 1rem;
    border-radius: 8px;
    max-width: 90%;
    overflow: auto;
    font-size: 0.8rem;
    text-align: left;
}}
</style>
</head>
<body>

<!-- Loading screen -->
<div id="loading">
    <h1>🖥️ {_html_escape(title)}</h1>
    <div class="subtitle">DOS • js-dos {JSDOS_VERSION}</div>
    <div id="progress-bar"><div id="progress-fill"></div></div>
    <div id="loading-status">Initializing...</div>
</div>

<!-- Error screen -->
<div id="error-screen">
    <h2>⚠️ Emulator Error</h2>
    <pre id="error-detail"></pre>
    <p style="margin-top:1rem;color:#999;font-size:0.8rem">
        Try refreshing the page or using a different browser (Chrome/Edge recommended).
    </p>
</div>

<!-- Canvas -->
<div id="canvas-wrap">
    <canvas id="jsdos" tabindex="0"></canvas>
</div>

<!-- Controls overlay -->
<div id="controls">
    <button id="btn-fs" onclick="toggleFullscreen()" title="Fullscreen">⛶</button>
    <button id="btn-vkb" onclick="toggleVKB()" title="Virtual Keyboard">⌨️</button>
    <button id="btn-mute" onclick="toggleMute()" title="Mute/Unmute">🔊</button>
    <button id="btn-pause" onclick="togglePause()" title="Pause/Resume">⏸️</button>
</div>
<button id="toggle-ctrl" onclick="document.getElementById('controls').classList.toggle('hidden')" title="Toggle Controls">🎮</button>

<!-- Virtual keyboard -->
{vkb_html}

<!-- js-dos 6.22 library (inline) -->
<script>
{jsdos_js}
</script>

<script>
// ============================================================
// BOOT SEQUENCE — Single-file DOS Emulation
// ============================================================

var GAME_TITLE = {json.dumps(title)};
var EXE_NAME = {json.dumps(exe_name)};
var ROOT_DIR = {json.dumps(root_dir or "")};

// Embedded assets (base64)
var WASM_B64 = "{wdosbox_wasm_b64}";
var WDOSBOX_JS_B64 = "{wdosbox_js_b64}";
var GAME_B64 = "{game_b64}";
var DOSBOX_CONF_B64 = "{dosbox_conf_b64}";

// --- UI Helpers ---
function setProgress(pct, msg) {{
    var fill = document.getElementById('progress-fill');
    var status = document.getElementById('loading-status');
    if (fill) fill.style.width = pct + '%';
    if (status) status.textContent = msg;
}}

function showError(msg) {{
    var screen = document.getElementById('error-screen');
    var detail = document.getElementById('error-detail');
    if (detail) detail.textContent = msg;
    if (screen) screen.style.display = 'flex';
    var loading = document.getElementById('loading');
    if (loading) loading.style.display = 'none';
}}

function hideLoading() {{
    var el = document.getElementById('loading');
    if (el) {{
        el.classList.add('fade');
        setTimeout(function() {{ el.style.display = 'none'; }}, 600);
    }}
}}

// --- Base64 Decoder ---
function b64toBytes(b64) {{
    var raw = atob(b64);
    var len = raw.length;
    var arr = new Uint8Array(len);
    for (var i = 0; i < len; i++) arr[i] = raw.charCodeAt(i);
    return arr;
}}

// --- Main Boot ---
(async function() {{
    try {{
        // Step 1: Decode WASM binary
        setProgress(10, 'Decoding WASM engine...');
        var wasmBytes = b64toBytes(WASM_B64);
        WASM_B64 = null; // free memory
        console.log('WASM decoded:', wasmBytes.length, 'bytes');

        // Step 2: Compile WebAssembly module
        setProgress(25, 'Compiling WebAssembly...');
        var wasmModule = await WebAssembly.compile(wasmBytes.buffer);
        wasmBytes = null;
        console.log('WASM compiled');

        // Step 3: Set up instantiateWasm hook
        setProgress(35, 'Setting up emulator...');
        window.exports = window.exports || {{}};
        window.exports.instantiateWasm = function(info, receiveInstance) {{
            WebAssembly.instantiate(wasmModule, info).then(function(instance) {{
                receiveInstance(instance, wasmModule);
            }});
        }};

        // Step 4: Eval wdosbox.js to set exports.WDOSBOX
        setProgress(45, 'Loading DOSBox engine...');
        var wdosboxJsCode = new TextDecoder().decode(b64toBytes(WDOSBOX_JS_B64));
        WDOSBOX_JS_B64 = null;
        eval.call(window, wdosboxJsCode);
        wdosboxJsCode = null;
        console.log('WDOSBOX loaded, exports.WDOSBOX:', typeof window.exports.WDOSBOX);

        // Step 5: Decode game ZIP → Blob URL
        setProgress(60, 'Decoding game data ({game_size_kb} KB)...');
        var gameBytes = b64toBytes(GAME_B64);
        GAME_B64 = null;
        var gameBlob = new Blob([gameBytes], {{ type: 'application/zip' }});
        var gameUrl = URL.createObjectURL(gameBlob);
        gameBytes = null;
        console.log('Game blob URL ready');

        // Step 6: Decode dosbox.conf
        var confText = new TextDecoder().decode(b64toBytes(DOSBOX_CONF_B64));
        DOSBOX_CONF_B64 = null;

        // Step 7: Start js-dos
        setProgress(75, 'Starting DOSBox...');
        var canvas = document.getElementById('jsdos');
        canvas.focus();

        Dos(canvas).ready(function(fs, main) {{
            setProgress(85, 'Extracting game files...');

            // Write dosbox.conf
            fs.createFile('/dosbox.conf', confText);
            console.log('dosbox.conf written');

            // Extract game ZIP to root /
            fs.extract(gameUrl).then(function() {{
                setProgress(95, 'Launching ' + EXE_NAME + '...');
                URL.revokeObjectURL(gameUrl);
                console.log('Game extracted, launching:', EXE_NAME);

                // Build launch args:
                // js-dos auto-prepends: -userconf -c "mount c ." -c "c:"
                // But "." is Emscripten CWD (often /home/web_user), not /
                // where files were extracted. So we re-mount c to / explicitly.
                var args = ['-conf', '/dosbox.conf',
                            '-c', 'mount c /',
                            '-c', 'c:'];
                if (ROOT_DIR) {{
                    args.push('-c', 'cd ' + ROOT_DIR);
                }}
                args.push('-c', 'cls');
                args.push('-c', EXE_NAME);
                console.log('DOSBox args:', args);

                main(args).then(function(ci) {{
                    hideLoading();
                    console.log('DOSBox running!');
                    window._ci = ci; // store command interface

                    // Auto-focus canvas
                    canvas.focus();
                    canvas.addEventListener('click', function() {{ canvas.focus(); }});
                }}).catch(function(err) {{
                    console.error('Main launch error:', err);
                    hideLoading();
                }});
            }}).catch(function(err) {{
                showError('Failed to extract game files:\\n' + err);
            }});
        }});

    }} catch(err) {{
        console.error('Boot error:', err);
        showError('Emulator initialization failed:\\n' + err.message + '\\n\\n' + err.stack);
    }}
}})();

// ============================================================
// CONTROLS
// ============================================================

var isMuted = false;
var isPaused = false;

function toggleFullscreen() {{
    if (!document.fullscreenElement) {{
        (document.documentElement.requestFullscreen ||
         document.documentElement.webkitRequestFullscreen ||
         function(){{}}).call(document.documentElement);
    }} else {{
        (document.exitFullscreen || document.webkitExitFullscreen || function(){{}}).call(document);
    }}
}}

function toggleMute() {{
    isMuted = !isMuted;
    var btn = document.getElementById('btn-mute');
    btn.textContent = isMuted ? '🔇' : '🔊';
    // js-dos 6.22 audio control via Emscripten
    if (window.Module && window.Module.SDL2 && window.Module.SDL2.audioContext) {{
        if (isMuted) window.Module.SDL2.audioContext.suspend();
        else window.Module.SDL2.audioContext.resume();
    }}
}}

function togglePause() {{
    isPaused = !isPaused;
    var btn = document.getElementById('btn-pause');
    btn.textContent = isPaused ? '▶️' : '⏸️';
    if (window._ci) {{
        if (isPaused) window._ci.exit();
        // Note: resume not directly supported in js-dos 6.22 command interface
    }}
}}

function toggleVKB() {{
    // Support both gamepad and keyboard overlays
    var gp = document.getElementById('gamepad');
    var vkb = document.getElementById('vkb');
    var target = gp || vkb;
    if (!target) return;
    target.classList.toggle('show');
    var btn = document.getElementById('btn-vkb');
    if (btn) btn.classList.toggle('active', target.classList.contains('show'));
}}

// Auto-show gamepad on touch devices
(function() {{
    var isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
    if (isTouchDevice) {{
        // Wait for loading to finish, then show gamepad
        var checkReady = setInterval(function() {{
            var loading = document.getElementById('loading');
            if (loading && loading.style.display === 'none') {{
                clearInterval(checkReady);
                toggleVKB();
            }}
        }}, 500);
        // Fallback: show after 10s regardless
        setTimeout(function() {{
            clearInterval(checkReady);
            var gp = document.getElementById('gamepad');
            var vkb = document.getElementById('vkb');
            var target = gp || vkb;
            if (target && !target.classList.contains('show')) toggleVKB();
        }}, 10000);
    }}
}})()

// Virtual keyboard key simulation
{vkb_js}

</script>
</body>
</html>"""

    return html


# ============================================================
#  Virtual Keyboard
# ============================================================

# js-dos 6.22 key codes (DOS scancodes mapped to JS keycodes)
JSDOS_KEYCODES = {
    'Esc': 27, 'F1': 112, 'F2': 113, 'F3': 114, 'F4': 115,
    'F5': 116, 'F6': 117, 'F7': 118, 'F8': 119, 'F9': 120, 'F10': 121,
    '1': 49, '2': 50, '3': 51, '4': 52, '5': 53,
    '6': 54, '7': 55, '8': 56, '9': 57, '0': 48,
    'Q': 81, 'W': 87, 'E': 69, 'R': 82, 'T': 84,
    'Y': 89, 'U': 85, 'I': 73, 'O': 79, 'P': 80,
    'A': 65, 'S': 83, 'D': 68, 'F': 70, 'G': 71,
    'H': 72, 'J': 74, 'K': 75, 'L': 76,
    'Z': 90, 'X': 88, 'C': 67, 'V': 86, 'B': 66,
    'N': 78, 'M': 77,
    'Enter': 13, 'Space': 32, 'Backspace': 8, 'Tab': 9,
    'Shift': 16, 'Ctrl': 17, 'Alt': 18,
    'Up': 38, 'Down': 40, 'Left': 37, 'Right': 39,
    'Y/N': None,  # Special: Y then N buttons
}


def _generate_virtual_keyboard(layout='default'):
    """Generate virtual keyboard/gamepad HTML and JS for DOS games.
    
    Layouts:
      - gamepad: D-pad + 4 action buttons + system bar (best for action games)
      - gamepad-prince: optimized for Prince of Persia (Shift=sword, Space=jump)
      - minimal, arrows: simple keyboard overlays
      - adventure, default: full keyboard overlays
    """

    # ---- GAMEPAD LAYOUTS ----
    if layout.startswith('gamepad'):
        # Button mappings: label → [keyCode, keyName]
        if layout == 'gamepad-prince':
            btn_map = {
                'A': [16, 'Shift'],     # Sword / careful step
                'B': [32, 'Space'],     # Jump
                'X': [38, 'Up'],        # Climb / run faster
                'Y': [27, 'Esc'],       # Menu
            }
            sys_keys = ['Ctrl', 'F1', 'F2', 'Space']
        else:
            # Default gamepad: good for most action games
            btn_map = {
                'A': [32, 'Space'],     # Jump / action
                'B': [13, 'Enter'],     # Confirm
                'X': [17, 'Ctrl'],      # Alt action / fire
                'Y': [27, 'Esc'],       # Menu / back
            }
            sys_keys = ['F1', 'F2', 'F3', 'Shift', 'Tab', '1', '2', '3']

        # -- D-pad + actions + sysbar HTML --
        sys_btns = ''
        for sk in sys_keys:
            kc = JSDOS_KEYCODES.get(sk, ord(sk[0]) if len(sk) == 1 else 0)
            label = sk
            if sk == 'Space': label = '␣'
            elif sk == 'Shift': label = '⇧'
            elif sk == 'Tab': label = '⇥'
            sys_btns += (
                f'<button data-kc="{kc}" data-key="{sk}" '
                f'ontouchstart="gpSysDown(this,event)" '
                f'ontouchend="gpSysUp(this,event)">{label}</button>\n        '
            )

        # Action button HTML
        act_btns = ''
        for pos in ['a', 'b', 'x', 'y']:
            label = pos.upper()
            info = btn_map[label]
            act_btns += (
                f'<div class="gp-btn btn-{pos}" data-kc="{info[0]}" '
                f'data-key="{info[1]}" data-label="{label}" '
                f'ontouchstart="gpBtnDown(this,event)" '
                f'ontouchend="gpBtnUp(this,event)">{label}</div>\n    '
            )

        vkb_html = f'''<div id="gamepad">
    <!-- D-pad (angle-based touch zone) -->
    <div id="gp-dpad"
         ontouchstart="gpDpadTouch(event)"
         ontouchmove="gpDpadTouch(event)"
         ontouchend="gpDpadRelease(event)"
         ontouchcancel="gpDpadRelease(event)">
        <div class="dp-arrow dp-up" id="dp-up">▲</div>
        <div class="dp-arrow dp-down" id="dp-down">▼</div>
        <div class="dp-arrow dp-left" id="dp-left">◄</div>
        <div class="dp-arrow dp-right" id="dp-right">►</div>
        <div class="dp-center"></div>
    </div>

    <!-- Action buttons (diamond) -->
    <div id="gp-actions">
    {act_btns}</div>

    <!-- System bar -->
    <div id="gp-sysbar">
        {sys_btns}</div>
</div>'''

        vkb_js = """
// ============ GAMEPAD TOUCH CONTROLLER ============

var _gpCanvas = null;
function _gpGetCanvas() {
    if (!_gpCanvas) _gpCanvas = document.getElementById('jsdos');
    return _gpCanvas;
}

// Send key events to the emulator canvas
function _gpKeyDown(kc, keyName) {
    var c = _gpGetCanvas(); if (!c) return;
    c.dispatchEvent(new KeyboardEvent('keydown', {
        keyCode: kc, which: kc, code: _keyToCode(keyName),
        key: _keyToEventKey(keyName), bubbles: true, cancelable: true
    }));
}
function _gpKeyUp(kc, keyName) {
    var c = _gpGetCanvas(); if (!c) return;
    c.dispatchEvent(new KeyboardEvent('keyup', {
        keyCode: kc, which: kc, code: _keyToCode(keyName),
        key: _keyToEventKey(keyName), bubbles: true, cancelable: true
    }));
}

// Optional haptic feedback
function _gpVibrate(ms) {
    if (navigator.vibrate) navigator.vibrate(ms || 12);
}

// ---- D-PAD (angle-based) ----
var _dpActive = { up: false, down: false, left: false, right: false };
var _dpKC = { up: [38, 'Up'], down: [40, 'Down'], left: [37, 'Left'], right: [39, 'Right'] };

function gpDpadTouch(e) {
    e.preventDefault();
    var dpad = document.getElementById('gp-dpad');
    var rect = dpad.getBoundingClientRect();
    var cx = rect.left + rect.width / 2;
    var cy = rect.top + rect.height / 2;

    // Use first touch on the dpad
    var touch = e.touches[0];
    var dx = touch.clientX - cx;
    var dy = touch.clientY - cy;
    var dist = Math.sqrt(dx * dx + dy * dy);
    var radius = rect.width / 2;

    // Dead zone: 15% of radius
    var newState = { up: false, down: false, left: false, right: false };
    if (dist > radius * 0.15) {
        var angle = Math.atan2(dy, dx) * (180 / Math.PI); // -180 to 180
        // 8-directional with 45° zones
        // Right: -22.5 to 22.5
        // Down-Right: 22.5 to 67.5
        // Down: 67.5 to 112.5
        // Down-Left: 112.5 to 157.5
        // Left: 157.5 to 180 or -180 to -157.5
        // Up-Left: -157.5 to -112.5
        // Up: -112.5 to -67.5
        // Up-Right: -67.5 to -22.5
        if (angle >= -67.5 && angle < -22.5)  { newState.up = true; newState.right = true; }
        else if (angle >= -112.5 && angle < -67.5) { newState.up = true; }
        else if (angle >= -157.5 && angle < -112.5) { newState.up = true; newState.left = true; }
        else if (angle >= 157.5 || angle < -157.5) { newState.left = true; }
        else if (angle >= 112.5 && angle < 157.5) { newState.down = true; newState.left = true; }
        else if (angle >= 67.5 && angle < 112.5) { newState.down = true; }
        else if (angle >= 22.5 && angle < 67.5) { newState.down = true; newState.right = true; }
        else { newState.right = true; }
    }

    // Update keys — only send events for changes
    var dirs = ['up', 'down', 'left', 'right'];
    var changed = false;
    for (var i = 0; i < dirs.length; i++) {
        var d = dirs[i];
        if (newState[d] && !_dpActive[d]) {
            _gpKeyDown(_dpKC[d][0], _dpKC[d][1]);
            document.getElementById('dp-' + d).classList.add('active');
            changed = true;
        } else if (!newState[d] && _dpActive[d]) {
            _gpKeyUp(_dpKC[d][0], _dpKC[d][1]);
            document.getElementById('dp-' + d).classList.remove('active');
            changed = true;
        }
    }
    if (changed) _gpVibrate(8);
    _dpActive = newState;
}

function gpDpadRelease(e) {
    e.preventDefault();
    var dirs = ['up', 'down', 'left', 'right'];
    for (var i = 0; i < dirs.length; i++) {
        var d = dirs[i];
        if (_dpActive[d]) {
            _gpKeyUp(_dpKC[d][0], _dpKC[d][1]);
            document.getElementById('dp-' + d).classList.remove('active');
        }
    }
    _dpActive = { up: false, down: false, left: false, right: false };
}

// ---- ACTION BUTTONS ----
function gpBtnDown(btn, e) {
    e.preventDefault();
    var kc = parseInt(btn.dataset.kc);
    var key = btn.dataset.key;
    btn.classList.add('active');
    _gpKeyDown(kc, key);
    _gpVibrate(15);
}
function gpBtnUp(btn, e) {
    e.preventDefault();
    var kc = parseInt(btn.dataset.kc);
    var key = btn.dataset.key;
    btn.classList.remove('active');
    _gpKeyUp(kc, key);
}

// ---- SYSTEM BAR BUTTONS ----
function gpSysDown(btn, e) {
    e.preventDefault();
    var kc = parseInt(btn.dataset.kc);
    var key = btn.dataset.key;
    btn.classList.add('active');
    _gpKeyDown(kc, key);
}
function gpSysUp(btn, e) {
    e.preventDefault();
    var kc = parseInt(btn.dataset.kc);
    var key = btn.dataset.key;
    btn.classList.remove('active');
    _gpKeyUp(kc, key);
}
"""

    # ---- KEYBOARD LAYOUTS ----
    else:
        if layout == 'minimal':
            rows = [
                ['Esc', 'Up', 'Enter', 'Space'],
                ['Left', 'Down', 'Right', 'Y', 'N'],
            ]
        elif layout == 'arrows':
            rows = [
                ['Esc', 'F1', 'F2', 'F3', 'F4', 'F5'],
                ['1', '2', '3', '4', '5', 'Enter'],
                ['Up', 'Y', 'N', 'Space'],
                ['Left', 'Down', 'Right', 'Ctrl', 'Alt'],
            ]
        elif layout == 'adventure':
            rows = [
                ['Esc', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6'],
                ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
                ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
                ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Enter'],
                ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Backspace'],
                ['Shift', 'Space', 'Ctrl', 'Alt', 'Tab'],
            ]
        else:  # default - balanced layout
            rows = [
                ['Esc', 'F1', 'F2', 'F3', 'F4', 'F5'],
                ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
                ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
                ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Enter'],
                ['Shift', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Backspace'],
                ['Ctrl', 'Alt', 'Left', 'Up', 'Down', 'Right', 'Space', 'Tab'],
            ]

        # Generate keyboard HTML
        buttons_html = []
        for row in rows:
            for key in row:
                kc = JSDOS_KEYCODES.get(key, ord(key[0]) if len(key) == 1 else 0)
                css_class = ''
                if key in ('Space',):
                    css_class = ' class="space"'
                elif key in ('Enter', 'Backspace', 'Shift', 'Ctrl', 'Alt', 'Tab'):
                    css_class = ' class="wide"'

                label = key
                if key == 'Space': label = '␣'
                elif key == 'Backspace': label = '⌫'
                elif key == 'Enter': label = '↵'
                elif key == 'Up': label = '▲'
                elif key == 'Down': label = '▼'
                elif key == 'Left': label = '◄'
                elif key == 'Right': label = '►'
                elif key == 'Tab': label = '⇥'
                elif key == 'Shift': label = '⇧'

                buttons_html.append(
                    f'<button{css_class} data-kc="{kc}" data-key="{key}" '
                    f'ontouchstart="vkbDown(this,event)" ontouchend="vkbUp(this,event)">'
                    f'{label}</button>'
                )

        vkb_inner = '\n    '.join(buttons_html)
        vkb_html = f'<div id="vkb">\n    {vkb_inner}\n</div>'

        vkb_js = """
function vkbDown(btn, e) {
    if (e) e.preventDefault();
    var kc = parseInt(btn.dataset.kc);
    var key = btn.dataset.key;
    if (!kc && !key) return;
    btn.style.background = 'rgba(0,150,255,0.4)';

    var canvas = document.getElementById('jsdos');
    if (!canvas) return;
    canvas.dispatchEvent(new KeyboardEvent('keydown', {
        keyCode: kc, which: kc, code: _keyToCode(key),
        key: _keyToEventKey(key), bubbles: true, cancelable: true
    }));
}

function vkbUp(btn, e) {
    if (e) e.preventDefault();
    var kc = parseInt(btn.dataset.kc);
    var key = btn.dataset.key;
    if (!kc && !key) return;
    btn.style.background = '';

    var canvas = document.getElementById('jsdos');
    if (!canvas) return;
    canvas.dispatchEvent(new KeyboardEvent('keyup', {
        keyCode: kc, which: kc, code: _keyToCode(key),
        key: _keyToEventKey(key), bubbles: true, cancelable: true
    }));
}
"""

    # Shared key helpers (used by both modes)
    shared_js = """
function _keyToCode(key) {
    var map = {
        'Esc':'Escape','Enter':'Enter','Space':'Space','Backspace':'Backspace',
        'Tab':'Tab','Shift':'ShiftLeft','Ctrl':'ControlLeft','Alt':'AltLeft',
        'Up':'ArrowUp','Down':'ArrowDown','Left':'ArrowLeft','Right':'ArrowRight',
        'F1':'F1','F2':'F2','F3':'F3','F4':'F4','F5':'F5','F6':'F6',
        'F7':'F7','F8':'F8','F9':'F9','F10':'F10'
    };
    if (map[key]) return map[key];
    if (key.length === 1 && key >= '0' && key <= '9') return 'Digit' + key;
    if (key.length === 1) return 'Key' + key.toUpperCase();
    return key;
}

function _keyToEventKey(key) {
    var map = {
        'Esc':'Escape','Enter':'Enter','Space':' ','Backspace':'Backspace',
        'Tab':'Tab','Shift':'Shift','Ctrl':'Control','Alt':'Alt',
        'Up':'ArrowUp','Down':'ArrowDown','Left':'ArrowLeft','Right':'ArrowRight'
    };
    if (map[key]) return map[key];
    return key;
}
"""

    return vkb_html, vkb_js + shared_js


# ============================================================
#  Utilities
# ============================================================

def _html_escape(text):
    """Basic HTML escaping."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


# ============================================================
#  Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Pack a DOS game ZIP into a self-contained offline HTML file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s game.zip
    %(prog)s game.zip --title "Prince of Persia" --exe PRINCE.EXE
    %(prog)s game.zip --cycles max --memory 32
    %(prog)s game.zip --keyboard adventure
    %(prog)s game.zip --analyze-only
        """
    )
    parser.add_argument('zip', help='Path to the DOS game ZIP file')
    parser.add_argument('--title', '-t', help='Game title (default: filename)')
    parser.add_argument('--exe', '-e', help='Main executable to launch (auto-detected if omitted)')
    parser.add_argument('--output', '-o', help='Output HTML file path')
    parser.add_argument('--cycles', default='auto',
                        help='DOSBox CPU cycles: auto, max, or number (default: auto)')
    parser.add_argument('--memory', type=int, default=16,
                        help='DOS memory in MB (default: 16)')
    parser.add_argument('--sound', default='sb16',
                        choices=['sb16', 'sb1', 'sb2', 'sbpro1', 'sbpro2', 'none'],
                        help='Sound card emulation (default: sb16)')
    parser.add_argument('--keyboard', '-k', default='gamepad',
                        choices=['gamepad', 'gamepad-prince', 'default', 'minimal', 'arrows', 'adventure'],
                        help='Touch controls layout: gamepad (D-pad+buttons), gamepad-prince, default, minimal, arrows, adventure')
    parser.add_argument('--extra-conf', help='Extra DOSBox config to inject (string or @file)')
    parser.add_argument('--cache-dir', default='.jsdos_cache',
                        help='Directory to cache downloaded js-dos assets')
    parser.add_argument('--analyze-only', '-a', action='store_true',
                        help='Only analyze the ZIP contents')

    args = parser.parse_args()

    # Validate input
    if not os.path.isfile(args.zip):
        print(f"Error: File not found: {args.zip}")
        sys.exit(1)

    if not zipfile.is_zipfile(args.zip):
        print(f"Error: Not a valid ZIP file: {args.zip}")
        sys.exit(1)

    # Analyze ZIP
    print(f"🖥️  Analyzing: {args.zip}")
    zip_info = analyze_zip(args.zip)
    print(f"   Files: {zip_info['file_count']}")
    print(f"   Total size: {zip_info['total_size']:,} bytes ({zip_info['total_size']//1024} KB)")

    if zip_info['root_dir']:
        print(f"   Root directory: {zip_info['root_dir']}/")

    if zip_info['executables']:
        print(f"   Executables found:")
        for exe in zip_info['executables'][:10]:
            marker = " ← auto-selected" if exe == zip_info['executables'][0] and not args.exe else ""
            print(f"     {exe['path']} ({exe['size']:,} bytes){marker}")
    else:
        print(f"   ⚠️  No DOS executables found!")

    if args.analyze_only:
        print(f"\n✅ Analysis complete.")
        return

    # Determine executable
    exe_name = args.exe
    if not exe_name:
        exe_name = detect_executable(zip_info)
        if not exe_name:
            print(f"\n❌ Error: No executable found in ZIP. Use --exe to specify one.")
            sys.exit(1)
        print(f"   Auto-detected executable: {exe_name}")
    else:
        exe_name = exe_name.upper()
        print(f"   Using specified executable: {exe_name}")

    # Title
    title = args.title or os.path.splitext(os.path.basename(args.zip))[0]
    print(f"   Title: {title}")

    # Extra config
    extra_conf = None
    if args.extra_conf:
        if args.extra_conf.startswith('@'):
            with open(args.extra_conf[1:], 'r') as f:
                extra_conf = f.read()
        else:
            extra_conf = args.extra_conf

    # Generate DOSBox config
    print(f"⚙️  DOSBox config: cycles={args.cycles}, memory={args.memory}MB, sound={args.sound}")
    dosbox_conf = generate_dosbox_conf(
        exe_name=exe_name,
        cycles=args.cycles,
        memory=args.memory,
        sound=args.sound,
        extra_conf=extra_conf,
        root_dir=zip_info.get('root_dir'),
    )

    # Download/cache js-dos assets
    print(f"📦 Loading js-dos {JSDOS_VERSION} assets...")
    jsdos_assets = load_jsdos_assets(args.cache_dir)

    # Generate HTML
    print(f"🏗️  Generating HTML...")
    html = generate_html(
        game_zip_path=args.zip,
        title=title,
        exe_name=exe_name,
        jsdos_assets=jsdos_assets,
        dosbox_conf=dosbox_conf,
        keyboard_layout=args.keyboard,
        root_dir=zip_info.get('root_dir'),
    )

    # Write output
    output_path = args.output or os.path.splitext(args.zip)[0] + '.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(output_path) / 1024
    size_mb = size_kb / 1024

    print(f"\n✅ Done! Output: {output_path}")
    print(f"   📦 Size: {size_mb:.1f} MB ({size_kb:.0f} KB)")
    print(f"   🔌 100% offline — no internet or server needed")
    print(f"   📱 Virtual keyboard included (layout: {args.keyboard})")
    print(f"   🖥️  Engine: js-dos {JSDOS_VERSION} (asyncify, no SharedArrayBuffer)")
    print(f"   🎮 Just double-click the HTML file to play!")


if __name__ == '__main__':
    main()
