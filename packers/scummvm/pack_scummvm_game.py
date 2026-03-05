#!/usr/bin/env python3
"""
ScummVM Game Packer - Creates portable single-file HTML games.

Takes a directory of game files and produces a self-contained HTML file that
runs the game in the browser using ScummVM WASM. The HTML file works 100%
offline - no server or internet connection needed.

Usage:
    python pack_scummvm_game.py <game_dir> [options]

Examples:
    # Auto-detect engine from game files
    python pack_scummvm_game.py ./my_game/

    # Specify engine explicitly
    python pack_scummvm_game.py ./my_game/ --engine scumm --title "Monkey Island"

    # List available engines
    python pack_scummvm_game.py --list-engines

Prerequisites:
    Run download_scummvm_assets.py first to download ScummVM WASM files.

Architecture:
    The generated HTML contains:
    1. ScummVM WASM core (gzip+base64 compressed)
    2. ScummVM JS glue code (gzip+base64 compressed)
    3. The correct engine plugin .so (gzip+base64 compressed)
    4. Engine-specific data files (gzip+base64 compressed)
    5. All game files (gzip+base64 compressed)
    6. A theme file (scummmodern.zip)
    7. JavaScript boot code that:
       - Decompresses everything using browser DecompressionStream API
       - Writes game files + plugin to Emscripten MEMFS
       - Intercepts fetch() to serve scummvm.ini and data files locally
       - Sets ScummVM arguments via window.location.hash
       - Launches ScummVM

Key discoveries (from reverse-engineering scummvm.kuendig.io):
    - ScummVM WASM uses DYNAMIC plugins (.so files loaded via dlopen)
    - Plugins must exist in /data/plugins/ in MEMFS before ScummVM init
    - ScummVM reads CLI arguments from window.location.hash (not Module.arguments)
    - scummvm.ini is fetched at startup and can be intercepted
    - Engine data files (.cpt, .dat, .tbl) are fetched on demand from /data/
    - Uses Asyncify (mono-thread) - no SharedArrayBuffer needed ✓
"""

import os
import sys
import gzip
import json
import base64
import argparse
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
SCUMMVM_DIR = os.path.join(REPO_ROOT, 'docs', 'data', 'scummvm')
PLUGINS_DIR = os.path.join(SCUMMVM_DIR, 'plugins')
DATA_DIR = os.path.join(SCUMMVM_DIR, 'data')
WASM_FILE = os.path.join(SCUMMVM_DIR, 'scummvm.wasm')
JS_FILE = os.path.join(SCUMMVM_DIR, 'scummvm.js')

# ============================================================================
# Engine detection - maps game file patterns to engine IDs
# ============================================================================

# Exact filename matches (case-insensitive)
DETECTION_BY_FILENAME = {
    # Sky engine (Beneath a Steel Sky)
    'sky.dsk': 'sky',
    'sky.dnr': 'sky',
    
    # Queen engine (Flight of the Amazon Queen)
    'queen.1': 'queen',
    'queen.1c': 'queen',
    
    # GOT engine (God of Thunder)
    'godfat.dat': 'got',
    
    # Lure engine (Lure of the Temptress)
    'lure.exe': 'lure',
    
    # Touche engine (Touché: Adventures of the Fifth Musketeer)
    'touche.dat': 'touche',
    
    # Teenagent
    'teenagent.dat': 'teenagent',
    
    # Drascula
    'packet.001': 'drascula',
    
    # Broken Sword 1
    'swordres.rif': 'sword1',
    'bs1': 'sword1',
    
    # Broken Sword 2
    'sword2.clu': 'sword2',
    'sword2.clr': 'sword2',
    
    # Discworld (Tinsel engine)
    'dw.scn': 'tinsel',
    'dw2.scn': 'tinsel',
    
    # The 7th Guest (Groovie)
    'script.grv': 'groovie',
    
    # Simon the Sorcerer (AGOS engine)
    'simon.gme': 'agos',
    'simon2.gme': 'agos',
    'stripped.txt': 'agos',
    'feeble.cmp': 'agos',
    
    # Myst (Mohawk engine)
    'myst.dat': 'mohawk',
    'channel.mov': 'mohawk',
    
    # I Have No Mouth (SAGA engine)
    'ihnm.res': 'saga',
    'itedata.ite': 'saga',
    'ihnmdata.ihn': 'saga',
    
    # Tony Tough (Tony engine)
    'roasted.mpr': 'tony',
    'roasted.mpc': 'tony',
    
    # Toonstruck (Toon engine)
    'misc.pak': 'toon',
    
    # Hopkins FBI
    'res_vga.res': 'hopkins',
    'reslng.res': 'hopkins',
    
    # Neverhood
    'hd.blb': 'neverhood',
    'c.blb': 'neverhood',
    
    # Pegasus Prime
    'images.dir': 'pegasus',
    
    # Starship Titanic
    'st.exe': 'titanic',
    'y222.dat': 'titanic',
    
    # Sludge engine
    'gamedata.slg': 'sludge',
    
    # Dreamweb
    'dreamweb.r00': 'dreamweb',
    'dreamweb.ad1': 'dreamweb',
    
    # Hugo
    'hugo.dat': 'hugo',
    
    # Mortevielle (Mort)
    'menufr.mor': 'mortevielle',
    'menuen.mor': 'mortevielle',
    
    # Last Express
    'cd1.hpf': 'lastexpress',
    'hdheader.bin': 'lastexpress',
    
    # Gobliiins (Gob engine)
    'intro.stk': 'gob',
    'gob.lic': 'gob',
    
    # Cruise for a Corpse
    'vol.cnf': 'cruise',
    
    # Future Wars (Cine engine)
    'auto00.prc': 'cine',
    'procs00': 'cine',
    
    # Legend of Kyrandia (Kyra engine)
    'kyrandia.exe': 'kyra',
    'gemcut.pak': 'kyra',
    'insignia.pak': 'kyra',
    'westwood.001': 'kyra',
    
    # Indiana Jones / SCUMM LFL format
    '000.lfl': 'scumm',
    '990.lfl': 'scumm',
    '901.lfl': 'scumm',
    
    # Sherlock Holmes (Sherlock engine)
    'talk.lib': 'sherlock',
    'journal.txt': 'sherlock',
    
    # Griffon
    'allitems.gfx': 'griffon',
    
    # Access engine (Amazon, Martian Memorandum)
    'room.dat': 'access',
    
    # Chamber (Return to Ringworld)
    'academy.rl2': 'tsage',
    
    # Wintermute engine
    'data.dcp': 'wintermute',
    'default.game': 'wintermute',

    # AGS (Adventure Game Studio)
    'acsetup.cfg': 'ags',
}

# Pattern-based detection (check if filename matches pattern)
DETECTION_BY_PATTERN = [
    # SCUMM games - .000 + .001 resource pairs
    (lambda f: f.endswith('.000') and not f.startswith('resource'), 'scumm'),
    (lambda f: f.endswith('.la0'), 'scumm'),  # Full Throttle, The Dig, COMI
    (lambda f: f.endswith('.lfl'), 'scumm'),
    (lambda f: f.endswith('.he0'), 'scumm'),  # Humongous Entertainment
    
    # Sierra SCI games
    (lambda f: f == 'resource.map' or f == 'resource.000', 'sci'),
    (lambda f: f == 'ressci.000' or f == 'ressci.001', 'sci'),
    
    # Sierra AGI games
    (lambda f: f in ('logdir', 'viewdir', 'picdir', 'snddir'), 'agi'),
    (lambda f: f == 'words.tok', 'agi'),
    (lambda f: f == 'agidata.ovl', 'agi'),
    
    # ADL (Scott Adams adventures)
    (lambda f: f.startswith('advent') and f.endswith('.dat'), 'adl'),
    
    # Blade Runner
    (lambda f: f.endswith('.tlk') and 'blade' in f.lower(), 'bladerunner'),
    (lambda f: f == 'startup.mix', 'bladerunner'),
    
    # Director/Macromedia
    (lambda f: f.endswith('.dxr') or f.endswith('.dcr'), 'director'),
    (lambda f: f.endswith('.cxt'), 'director'),
]

# Engine-specific data files (downloaded from the demo server)
# These are engine support files, NOT game files
ENGINE_DATA_FILES = {
    'access':       ['access.dat'],
    'bagel':        ['bagel.dat'],
    'cryo':         ['cryo.dat'],
    'cryomni3d':    ['cryomni3d.dat'],
    'darkseed':     ['darkseed.dat'],
    'drascula':     ['drascula.dat'],
    'freescape':    ['freescape.dat'],
    'got':          ['got.gfx', 'got.aud'],
    'hugo':         ['hugo.dat'],
    'kyra':         ['kyra.dat'],
    'lure':         ['lure.dat'],
    'macventure':   ['macventure.dat'],
    'mm':           ['mm.dat'],
    'mohawk':       [],  # Myst/Riven - no extra data needed
    'mortevielle':  ['mort.dat'],
    'myst3':        ['myst3.dat'],
    'nancy':        ['nancy.dat'],
    'neverhood':    ['neverhood.dat'],
    'prince':       ['prince_translation.dat'],
    'queen':        ['queen.tbl'],
    'scumm':        [],  # SCUMM games are self-contained
    'sci':          [],  # SCI games are self-contained
    'sky':          ['sky.cpt'],
    'supernova':    ['supernova.dat'],
    'teenagent':    ['teenagent.dat'],
    'titanic':      ['titanic.dat'],
    'tony':         ['tony.dat'],
    'toon':         ['toon.dat'],
    'ultima':       ['ultima.dat'],
    'wintermute':   ['wintermute.zip'],
}

# Common data files always included
COMMON_DATA_FILES = [
    'scummmodern.zip',       # Default ScummVM theme (~64 KB) - REQUIRED
    'scummremastered.zip',   # Remastered theme (~90 KB) - nice to have
]

# ============================================================================
# Engine detection
# ============================================================================

def detect_engine(game_dir):
    """Auto-detect the ScummVM engine from game files.
    
    Returns (engine_id, confidence) or (None, 0).
    """
    files = []
    for root, dirs, filenames in os.walk(game_dir):
        for f in filenames:
            rel = os.path.relpath(os.path.join(root, f), game_dir)
            files.append(rel.replace('\\', '/'))
    
    # Score each engine
    scores = {}
    filenames_lower = [f.lower() for f in files]
    basenames_lower = [os.path.basename(f).lower() for f in files]
    
    # Check exact filename matches
    for fname in basenames_lower:
        if fname in DETECTION_BY_FILENAME:
            engine = DETECTION_BY_FILENAME[fname]
            scores[engine] = scores.get(engine, 0) + 10
    
    # Check pattern matches
    for fname in basenames_lower:
        for pattern_fn, engine in DETECTION_BY_PATTERN:
            try:
                if pattern_fn(fname):
                    scores[engine] = scores.get(engine, 0) + 5
            except:
                pass
    
    if not scores:
        return None, 0
    
    # Return highest scoring engine
    best = max(scores, key=scores.get)
    return best, scores[best]


def list_available_engines():
    """List all available engine plugins."""
    if not os.path.exists(PLUGINS_DIR):
        print("❌ Plugins directory not found!")
        print(f"   Expected: {PLUGINS_DIR}")
        print(f"   Run download_scummvm_assets.py first.")
        return
    
    plugins = sorted([f for f in os.listdir(PLUGINS_DIR) if f.endswith('.so')])
    print(f"\nAvailable ScummVM engines ({len(plugins)}):\n")
    
    for p in plugins:
        engine_id = p.replace('lib', '').replace('.so', '')
        size = os.path.getsize(os.path.join(PLUGINS_DIR, p))
        data_files = ENGINE_DATA_FILES.get(engine_id, [])
        data_info = f" (data: {', '.join(data_files)})" if data_files else ""
        print(f"  {engine_id:20s}  {size/1024:7.0f} KB  {p}{data_info}")


# ============================================================================
# Compression helpers
# ============================================================================

def compress_and_encode(data):
    """Gzip compress then base64 encode binary data."""
    compressed = gzip.compress(data, compresslevel=9)
    encoded = base64.b64encode(compressed).decode('ascii')
    ratio = len(compressed) / len(data) * 100 if data else 0
    return encoded, len(data), len(compressed), ratio


def read_and_compress(filepath):
    """Read a file and return gzip+base64 encoded content."""
    with open(filepath, 'rb') as f:
        data = f.read()
    return compress_and_encode(data)


# ============================================================================
# HTML template
# ============================================================================

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{{GAME_TITLE}}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { width: 100%; height: 100%; overflow: hidden; background: #000; }
        
        /* Loading screen */
        #loading {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            background: #1a1a2e; color: #e0e0e0; font-family: 'Courier New', monospace; z-index: 100;
        }
        #loading h1 { font-size: 1.5em; margin-bottom: 20px; color: #00d4ff; }
        #loading .progress-bar {
            width: 300px; height: 20px; background: #333; border-radius: 10px;
            overflow: hidden; margin: 10px 0;
        }
        #loading .progress-fill {
            height: 100%; background: linear-gradient(90deg, #00d4ff, #7b2ff7);
            width: 0%; transition: width 0.3s; border-radius: 10px;
        }
        #loading .status { font-size: 0.9em; color: #888; margin-top: 10px; }
        #loading .detail { font-size: 0.75em; color: #666; margin-top: 5px; }
        
        /* Canvas */
        #canvas {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            display: none; cursor: default;
        }
        
        /* Error screen */
        #error {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: #1a1a2e; color: #ff4444; font-family: 'Courier New', monospace;
            padding: 40px; z-index: 200; overflow: auto;
        }
        #error h1 { margin-bottom: 20px; }
        #error pre { color: #ccc; white-space: pre-wrap; font-size: 0.85em; }
    </style>
</head>
<body>
    <div id="loading">
        <h1>🎮 {{GAME_TITLE}}</h1>
        <div class="progress-bar"><div class="progress-fill" id="progress"></div></div>
        <div class="status" id="status">Initializing...</div>
        <div class="detail" id="detail"></div>
    </div>
    <div id="error"><h1>❌ Error</h1><pre id="error-text"></pre></div>
    <canvas id="canvas" oncontextmenu="event.preventDefault()" tabindex="-1"></canvas>
    
    <!-- Embedded compressed data -->
    <script id="wasm-data" type="application/gzip-base64">{{WASM_DATA}}</script>
    <script id="js-data" type="application/gzip-base64">{{JS_DATA}}</script>
    <script id="plugin-data" type="application/gzip-base64" data-name="{{PLUGIN_NAME}}">{{PLUGIN_DATA}}</script>
    <script id="engine-data-files" type="application/json">{{ENGINE_DATA_JSON}}</script>
    <script id="game-files" type="application/json">{{GAME_FILES_JSON}}</script>
    
    <script>
    // ====================================================================
    // ScummVM Portable Game Launcher
    // ====================================================================
    
    const GAME_ENGINE = '{{ENGINE_ID}}';
    const GAME_TITLE = '{{GAME_TITLE_JS}}';
    
    // --- UI helpers ---
    function setProgress(pct) {
        document.getElementById('progress').style.width = pct + '%';
    }
    function setStatus(msg) {
        document.getElementById('status').textContent = msg;
    }
    function setDetail(msg) {
        document.getElementById('detail').textContent = msg;
    }
    function showError(msg) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'block';
        document.getElementById('error-text').textContent = msg;
    }
    
    // --- Decompression (gzip+base64 → Uint8Array) ---
    async function decompressB64(b64String) {
        const binaryStr = atob(b64String);
        const bytes = new Uint8Array(binaryStr.length);
        for (let i = 0; i < binaryStr.length; i++) {
            bytes[i] = binaryStr.charCodeAt(i);
        }
        
        const ds = new DecompressionStream('gzip');
        const writer = ds.writable.getWriter();
        writer.write(bytes);
        writer.close();
        
        const reader = ds.readable.getReader();
        const chunks = [];
        let totalLen = 0;
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            chunks.push(value);
            totalLen += value.length;
        }
        
        const result = new Uint8Array(totalLen);
        let offset = 0;
        for (const chunk of chunks) {
            result.set(chunk, offset);
            offset += chunk.length;
        }
        return result;
    }
    
    // --- Main boot sequence ---
    async function boot() {
        try {
            // Step 1: Decompress WASM
            setStatus('Decompressing ScummVM core...');
            setProgress(5);
            const wasmB64 = document.getElementById('wasm-data').textContent.trim();
            const wasmData = await decompressB64(wasmB64);
            setDetail(`WASM: ${(wasmData.length / 1024 / 1024).toFixed(1)} MB`);
            setProgress(30);
            
            // Step 2: Decompress plugin
            setStatus('Loading engine plugin...');
            const pluginEl = document.getElementById('plugin-data');
            const pluginName = pluginEl.dataset.name;
            const pluginData = await decompressB64(pluginEl.textContent.trim());
            setDetail(`Plugin: ${pluginName} (${(pluginData.length / 1024).toFixed(0)} KB)`);
            setProgress(40);
            
            // Step 3: Decompress engine data files
            setStatus('Loading engine data...');
            const engineDataJson = JSON.parse(
                document.getElementById('engine-data-files').textContent
            );
            const engineDataFiles = {};
            for (const [name, b64] of Object.entries(engineDataJson)) {
                engineDataFiles[name] = await decompressB64(b64);
                setDetail(`Data: ${name}`);
            }
            setProgress(50);
            
            // Step 4: Decompress game files
            setStatus('Decompressing game files...');
            const gameFilesJson = JSON.parse(
                document.getElementById('game-files').textContent
            );
            const gameFileNames = Object.keys(gameFilesJson);
            const gameFiles = {};
            let gameIdx = 0;
            for (const [name, b64] of Object.entries(gameFilesJson)) {
                gameFiles[name] = await decompressB64(b64);
                gameIdx++;
                const pct = 50 + (gameIdx / gameFileNames.length) * 20;
                setProgress(Math.round(pct));
                setDetail(`${name} (${(gameFiles[name].length / 1024).toFixed(0)} KB)`);
            }
            setProgress(70);
            
            // Step 5: Set ScummVM arguments via hash
            // ScummVM WASM reads arguments from window.location.hash
            window.location.hash = '-p /game --auto-detect --fullscreen';
            
            // Step 6: Prepare scummvm.ini
            const scummvmIni = [
                '[scummvm]',
                'fullscreen=true',
                'gfx_mode=surfacesdl',
                'aspect_ratio=true',
                'filtering=true',
                'gui_theme=scummmodern',
                '',
            ].join('\n');
            
            // Step 7: Build index metadata (critical for ScummVM plugin discovery)
            // ScummVM fetches /data/index.json to discover data files and plugins
            // ScummVM fetches /data/plugins/index.json to discover available engine plugins
            const indexJson = {};
            for (const [filename, data] of Object.entries(engineDataFiles)) {
                indexJson[filename] = data.length;
            }
            indexJson['plugins'] = {};
            indexJson['plugins'][pluginName] = pluginData.length;
            
            const pluginIndex = {};
            pluginIndex[pluginName] = pluginData.length;
            
            console.log('[Packer] INDEX_JSON:', JSON.stringify(indexJson));
            console.log('[Packer] PLUGIN_INDEX:', JSON.stringify(pluginIndex));
            
            // Step 8: Install fetch interceptor
            // ScummVM fetches scummvm.wasm, scummvm.ini, index.json, plugins, and data files at runtime
            setStatus('Configuring ScummVM...');
            const originalFetch = window.fetch;
            window.fetch = function(url, options) {
                const urlStr = (typeof url === 'string') ? url : url.url || url.toString();
                console.log('[FETCH]', urlStr);
                
                // Serve /data/index.json (ScummVM uses this to discover available data files + plugins)
                if (urlStr.includes('/data/index.json')) {
                    console.log('[Packer] Serving /data/index.json');
                    return Promise.resolve(new Response(JSON.stringify(indexJson), {
                        status: 200,
                        headers: { 'Content-Type': 'application/json' }
                    }));
                }
                
                // Serve /data/plugins/index.json (ScummVM uses this to discover engine plugins)
                if (urlStr.includes('/data/plugins/index.json')) {
                    console.log('[Packer] Serving /data/plugins/index.json');
                    return Promise.resolve(new Response(JSON.stringify(pluginIndex), {
                        status: 200,
                        headers: { 'Content-Type': 'application/json' }
                    }));
                }
                
                // Serve engine plugin .so file (ScummVM dynamically loads this)
                if (urlStr.includes('/data/plugins/' + pluginName)) {
                    console.log('[Packer] Serving plugin: ' + pluginName);
                    return Promise.resolve(new Response(pluginData.buffer, {
                        status: 200,
                        headers: { 'Content-Type': 'application/octet-stream' }
                    }));
                }
                
                // Serve WASM binary
                if (urlStr.includes('scummvm.wasm')) {
                    console.log('[Packer] Serving scummvm.wasm from memory');
                    return Promise.resolve(new Response(wasmData.buffer, {
                        status: 200,
                        headers: { 'Content-Type': 'application/wasm' }
                    }));
                }
                
                // Serve scummvm.ini
                if (urlStr.includes('scummvm.ini')) {
                    console.log('[Packer] Serving scummvm.ini');
                    return Promise.resolve(new Response(scummvmIni, { status: 200 }));
                }
                
                // Serve engine data files
                for (const [filename, data] of Object.entries(engineDataFiles)) {
                    if (urlStr.endsWith('/' + filename) || urlStr.endsWith('/data/' + filename)) {
                        console.log(`[Packer] Serving data file: ${filename}`);
                        return Promise.resolve(new Response(data.buffer, { status: 200 }));
                    }
                }
                
                // Block other /data/ requests with empty response (we're offline)
                console.warn(`[FETCH BLOCKED]`, urlStr);
                return Promise.resolve(new Response('', { status: 200 }));
            };
            setProgress(75);
            
            // Step 9: Configure Emscripten Module
            setStatus('Setting up ScummVM...');
            window.Module = {
                canvas: document.getElementById('canvas'),
                wasmBinary: wasmData.buffer,
                
                preRun: [function() {
                    console.log('[Packer] preRun: setting up MEMFS...');
                    
                    // Create directories
                    FS.mkdir('/game');
                    try { FS.mkdir('/data'); } catch(e) {}
                    try { FS.mkdir('/data/plugins'); } catch(e) {}
                    
                    // Write engine plugin
                    console.log(`[Packer] Writing plugin: /data/plugins/${pluginName}`);
                    FS.writeFile('/data/plugins/' + pluginName, pluginData);
                    
                    // Write game files (preserving directory structure)
                    for (const [name, data] of Object.entries(gameFiles)) {
                        const fullPath = '/game/' + name;
                        
                        // Create parent directories
                        const parts = name.split('/');
                        if (parts.length > 1) {
                            let dir = '/game';
                            for (let i = 0; i < parts.length - 1; i++) {
                                dir += '/' + parts[i];
                                try { FS.mkdir(dir); } catch(e) {}
                            }
                        }
                        
                        console.log(`[Packer] Writing game file: ${fullPath} (${data.length} bytes)`);
                        FS.writeFile(fullPath, data);
                    }
                    
                    // Debug: list what we wrote
                    console.log('[Packer] /game/ contents:', FS.readdir('/game'));
                    console.log('[Packer] /data/plugins/ contents:', FS.readdir('/data/plugins'));
                    console.log('[Packer] MEMFS setup complete ✓');
                }],
                
                // Called when canvas starts rendering
                onRuntimeInitialized: function() {
                    console.log('[Packer] ScummVM runtime initialized');
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('canvas').style.display = 'block';
                    document.getElementById('canvas').focus();
                },
                
                // Print handlers
                print: function(text) { console.log('[ScummVM]', text); },
                printErr: function(text) { console.error('[ScummVM]', text); },
                
                // Don't run immediately - we inject JS manually
                noInitialRun: false,
            };
            
            setProgress(80);
            
            // Step 10: Decompress and inject ScummVM JS
            setStatus('Starting ScummVM...');
            const jsB64 = document.getElementById('js-data').textContent.trim();
            const jsBytes = await decompressB64(jsB64);
            const jsText = new TextDecoder().decode(jsBytes);
            setProgress(90);
            
            // Inject as inline script (NOT blob URL - scope issues)
            const script = document.createElement('script');
            script.textContent = jsText;
            document.body.appendChild(script);
            
            setProgress(100);
            setStatus('ScummVM is starting...');
            
            // Auto-hide loading screen after timeout
            setTimeout(function() {
                const loading = document.getElementById('loading');
                if (loading.style.display !== 'none') {
                    loading.style.display = 'none';
                    document.getElementById('canvas').style.display = 'block';
                    document.getElementById('canvas').focus();
                }
            }, 10000);
            
        } catch (err) {
            console.error('Boot error:', err);
            showError('Failed to start game:\n\n' + err.message + '\n\n' + err.stack);
        }
    }
    
    // Start boot when page loads
    window.addEventListener('DOMContentLoaded', boot);
    </script>
</body>
</html>"""

# ============================================================================
# Packer logic
# ============================================================================

def pack_game(game_dir, engine_id, title, output_path):
    """Pack a game directory into a self-contained HTML file."""
    
    # Validate inputs
    if not os.path.isdir(game_dir):
        print(f"❌ Game directory not found: {game_dir}")
        return False
    
    if not os.path.exists(WASM_FILE):
        print(f"❌ ScummVM WASM not found: {WASM_FILE}")
        print(f"   Run download_scummvm_assets.py first!")
        return False
    
    if not os.path.exists(JS_FILE):
        print(f"❌ ScummVM JS not found: {JS_FILE}")
        print(f"   Run download_scummvm_assets.py first!")
        return False
    
    plugin_name = f'lib{engine_id}.so'
    plugin_path = os.path.join(PLUGINS_DIR, plugin_name)
    if not os.path.exists(plugin_path):
        print(f"❌ Engine plugin not found: {plugin_path}")
        print(f"   Engine '{engine_id}' may not exist. Use --list-engines to see available engines.")
        return False
    
    print(f"=" * 60)
    print(f"ScummVM Game Packer")
    print(f"=" * 60)
    print(f"  Game:   {title}")
    print(f"  Engine: {engine_id}")
    print(f"  Plugin: {plugin_name}")
    print(f"  Source: {game_dir}")
    print(f"  Output: {output_path}")
    print()
    
    # ---- Step 1: Compress WASM ----
    print(f"[1/6] Compressing ScummVM WASM...")
    wasm_b64, wasm_orig, wasm_gz, wasm_ratio = read_and_compress(WASM_FILE)
    print(f"       {wasm_orig/1024/1024:.1f} MB → {wasm_gz/1024/1024:.1f} MB ({wasm_ratio:.0f}%)")
    
    # ---- Step 2: Compress JS ----
    print(f"[2/6] Compressing ScummVM JS...")
    js_b64, js_orig, js_gz, js_ratio = read_and_compress(JS_FILE)
    print(f"       {js_orig/1024/1024:.1f} MB → {js_gz/1024/1024:.1f} MB ({js_ratio:.0f}%)")
    
    # ---- Step 3: Compress plugin ----
    print(f"[3/6] Compressing engine plugin ({plugin_name})...")
    plugin_b64, plugin_orig, plugin_gz, plugin_ratio = read_and_compress(plugin_path)
    print(f"       {plugin_orig/1024:.0f} KB → {plugin_gz/1024:.0f} KB ({plugin_ratio:.0f}%)")
    
    # ---- Step 4: Engine data files ----
    print(f"[4/6] Preparing engine data files...")
    engine_data = {}
    
    # Always include common data files (themes)
    for df in COMMON_DATA_FILES:
        df_path = os.path.join(DATA_DIR, df)
        if os.path.exists(df_path):
            b64, orig, gz, ratio = read_and_compress(df_path)
            engine_data[df] = b64
            print(f"       ✓ {df} ({orig/1024:.0f} KB → {gz/1024:.0f} KB)")
        else:
            print(f"       ⚠ {df} not found (optional)")
    
    # Engine-specific data files
    specific_files = ENGINE_DATA_FILES.get(engine_id, [])
    for df in specific_files:
        df_path = os.path.join(DATA_DIR, df)
        if os.path.exists(df_path):
            b64, orig, gz, ratio = read_and_compress(df_path)
            engine_data[df] = b64
            print(f"       ✓ {df} ({orig/1024:.0f} KB → {gz/1024:.0f} KB)")
        else:
            print(f"       ⚠ {df} not found!")
            print(f"         Check {DATA_DIR}")
    
    engine_data_json = json.dumps(engine_data)
    
    # ---- Step 5: Game files ----
    print(f"[5/6] Compressing game files...")
    game_files = {}
    total_game_orig = 0
    total_game_gz = 0
    
    for root, dirs, files in os.walk(game_dir):
        for f in files:
            filepath = os.path.join(root, f)
            relpath = os.path.relpath(filepath, game_dir).replace('\\', '/')
            
            b64, orig, gz, ratio = read_and_compress(filepath)
            game_files[relpath] = b64
            total_game_orig += orig
            total_game_gz += gz
            print(f"       ✓ {relpath} ({orig/1024:.0f} KB → {gz/1024:.0f} KB)")
    
    if not game_files:
        print(f"❌ No game files found in {game_dir}")
        return False
    
    print(f"       Total: {total_game_orig/1024/1024:.1f} MB → {total_game_gz/1024/1024:.1f} MB")
    
    game_files_json = json.dumps(game_files)
    
    # ---- Step 6: Generate HTML ----
    print(f"[6/6] Generating HTML file...")
    
    # Escape title for JS string
    title_js = title.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
    
    html = HTML_TEMPLATE
    html = html.replace('{{GAME_TITLE}}', title)
    html = html.replace('{{GAME_TITLE_JS}}', title_js)
    html = html.replace('{{ENGINE_ID}}', engine_id)
    html = html.replace('{{PLUGIN_NAME}}', plugin_name)
    html = html.replace('{{WASM_DATA}}', wasm_b64)
    html = html.replace('{{JS_DATA}}', js_b64)
    html = html.replace('{{PLUGIN_DATA}}', plugin_b64)
    html = html.replace('{{ENGINE_DATA_JSON}}', engine_data_json)
    html = html.replace('{{GAME_FILES_JSON}}', game_files_json)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    output_size = os.path.getsize(output_path)
    
    print()
    print(f"=" * 60)
    print(f"✅ SUCCESS!")
    print(f"=" * 60)
    print(f"  Output:     {output_path}")
    print(f"  File size:  {output_size/1024/1024:.1f} MB")
    print(f"")
    print(f"  Breakdown:")
    print(f"    WASM core:    {wasm_gz/1024/1024:.1f} MB (base64: {len(wasm_b64)/1024/1024:.1f} MB)")
    print(f"    JS glue:      {js_gz/1024/1024:.1f} MB (base64: {len(js_b64)/1024/1024:.1f} MB)")
    print(f"    Plugin:       {plugin_gz/1024:.0f} KB")
    print(f"    Engine data:  {len(engine_data_json)/1024:.0f} KB")
    print(f"    Game files:   {total_game_gz/1024/1024:.1f} MB (base64: {len(game_files_json)/1024/1024:.1f} MB)")
    print(f"")
    print(f"  Open {output_path} in a browser to play!")
    print(f"  Works 100% offline - no server needed 🎮")
    
    return True


# ============================================================================
# Entry point
# ============================================================================

def main():
    global SCUMMVM_DIR, PLUGINS_DIR, DATA_DIR, WASM_FILE, JS_FILE
    parser = argparse.ArgumentParser(
        description='ScummVM Game Packer - Creates portable single-file HTML games',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ./my_game/
  %(prog)s ./my_game/ --engine scumm --title "Monkey Island"
  %(prog)s ./my_game/ -o my_game.html
  %(prog)s --list-engines
"""
    )
    parser.add_argument(
        'game_dir', nargs='?',
        help='Directory containing the game files'
    )
    parser.add_argument(
        '--engine', '-e',
        help='ScummVM engine ID (auto-detected if not specified)'
    )
    parser.add_argument(
        '--title', '-t',
        help='Game title (default: directory name)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output HTML file path (default: <title>.html)'
    )
    parser.add_argument(
        '--list-engines', action='store_true',
        help='List all available engine plugins and exit'
    )
    parser.add_argument(
        '--scummvm-dir',
        help=f'Path to ScummVM WASM assets (default: {SCUMMVM_DIR})'
    )
    
    args = parser.parse_args()
    
    # Override paths if specified
    if args.scummvm_dir:
        SCUMMVM_DIR = args.scummvm_dir
        PLUGINS_DIR = os.path.join(SCUMMVM_DIR, 'plugins')
        DATA_DIR = os.path.join(SCUMMVM_DIR, 'data')
        WASM_FILE = os.path.join(SCUMMVM_DIR, 'scummvm.wasm')
        JS_FILE = os.path.join(SCUMMVM_DIR, 'scummvm.js')
    
    if args.list_engines:
        list_available_engines()
        return
    
    if not args.game_dir:
        parser.print_help()
        return
    
    game_dir = os.path.abspath(args.game_dir)
    
    # Auto-detect or use specified engine
    if args.engine:
        engine_id = args.engine
        print(f"Using specified engine: {engine_id}")
    else:
        print(f"Scanning {game_dir} for game files...")
        engine_id, confidence = detect_engine(game_dir)
        if engine_id:
            print(f"  → Detected engine: {engine_id} (confidence: {confidence})")
            confirm = input(f"  Use engine '{engine_id}'? [Y/n] ").strip().lower()
            if confirm == 'n':
                engine_id = input("  Enter engine ID: ").strip()
        else:
            print(f"  → Could not auto-detect engine.")
            print(f"  Use --list-engines to see available engines.")
            engine_id = input("  Enter engine ID: ").strip()
    
    if not engine_id:
        print("❌ No engine specified. Aborting.")
        return
    
    # Determine title
    title = args.title or os.path.basename(game_dir.rstrip('/\\'))
    
    # Determine output path
    safe_title = "".join(c if c.isalnum() or c in ' -_' else '' for c in title)
    output_path = args.output or f"{safe_title}.html"
    
    # Pack!
    success = pack_game(game_dir, engine_id, title, output_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
