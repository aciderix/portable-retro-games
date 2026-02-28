#!/usr/bin/env python3
"""
Build script for standalone vAmigaWeb HTML with embedded game.
Produces a single HTML file with all assets (WASM, ROM, disks, JS, CSS, images, sounds) inlined.
"""

import base64
import os
import re
import sys

SRC = "/tmp/work/src"

def read_file(path):
    with open(os.path.join(SRC, path), 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def read_binary(path):
    with open(os.path.join(SRC, path), 'rb') as f:
        return f.read()

def to_b64(data):
    return base64.b64encode(data).decode('ascii')

def file_to_b64(path):
    return to_b64(read_binary(path))

def mime_type(path):
    ext = path.rsplit('.', 1)[-1].lower()
    return {
        'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
        'svg': 'image/svg+xml', 'ico': 'image/x-icon', 'gif': 'image/gif',
        'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'ogg': 'audio/ogg',
        'woff': 'font/woff', 'woff2': 'font/woff2',
    }.get(ext, 'application/octet-stream')

def img_to_data_uri(path):
    return f"data:{mime_type(path)};base64,{file_to_b64(path)}"

def sound_to_data_uri(path):
    return f"data:audio/mpeg;base64,{file_to_b64(path)}"

print("=== Building standalone vAmigaWeb HTML ===")

# ============================================================
# 1. Encode binary assets
# ============================================================
print("Encoding WASM...")
wasm_b64 = file_to_b64("vAmiga.wasm")
print(f"  WASM base64: {len(wasm_b64)} chars")

print("Encoding ROM...")
rom_b64 = file_to_b64("kick13.A500")

print("Encoding disks...")
disk1_b64 = file_to_b64("shortgrey_disk1.adf")
disk2_b64 = file_to_b64("shortgrey_disk2.adf")
disk3_b64 = file_to_b64("shortgrey_disk3.adf")
disk4_b64 = file_to_b64("shortgrey_disk4.adf")

print("Encoding images...")
icon_b64_uri = img_to_data_uri("img/icon_borderless_x413.png")
rom_empty_b64_uri = img_to_data_uri("img/rom_empty.png")
favicon_b64_uri = img_to_data_uri("img/favicon.ico")
aros_b64_uri = img_to_data_uri("img/aros_half.png")
emutos_b64_uri = img_to_data_uri("img/emutos_header_shadow.png")

# Read sprites.svg as inline SVG content
sprites_svg = read_file("img/sprites.svg")

print("Encoding sounds...")
sounds = {}
# Sound files map: JS path name -> actual filename on disk
sound_files = ['insert', 'eject', 'step', 'stephd', 'key_standard', 'key_backspace', 'key_space']
for snd in sound_files:
    sounds[snd] = sound_to_data_uri(f"sounds/{snd}.mp3")

# ============================================================
# 2. Read all JS files
# ============================================================
print("Reading JS files...")
js_files_order = [
    'js/jquery-3.7.1.min.js',
    'js/bootstrap.bundle.min.js',
    'js/vAmiga_browser.js',
    'js/ringbuffer.js',
    'js/vAmiga_canvas.js',
    'js/vAmiga_canvas_gl_fast.js',
    'js/vAmiga_ui.js',
    'js/vAmiga_storage.js',
    'js/vAmiga_keyboard.js',
    'js/vAmiga_action_script.js',
    'js/virtualjoystick.js',
    'js/jszip.min.js',
]

js_contents = {}
for jsf in js_files_order:
    js_contents[jsf] = read_file(jsf)
    print(f"  {jsf}: {len(js_contents[jsf])} chars")

# Read main emscripten JS
vamiga_js = read_file("vAmiga.js")
print(f"  vAmiga.js: {len(vamiga_js)} chars")

# ============================================================
# 3. Read CSS files
# ============================================================
print("Reading CSS files...")
bootstrap_css = read_file("css/bootstrap.min.css")
vamiga_css = read_file("css/vAmiga.css")

# Replace image URLs in CSS with data URIs
vamiga_css = vamiga_css.replace("../img/sprites.svg", "data:image/svg+xml;base64," + file_to_b64("img/sprites.svg"))

# ============================================================
# 4. Patch JS for standalone operation
# ============================================================
print("Patching JS for standalone operation...")

# Patch vAmiga_ui.js: Override the ROM loading and boot sequence
ui_js = js_contents['js/vAmiga_ui.js']

# CRITICAL PATCH 0: Neutralize fill_available_roms calls (called before its definition)
# We handle ROM ourselves, so these storage-based ROM pickers are not needed
ui_js = ui_js.replace(
    "fill_available_roms('rom', 'stored_roms');",
    "/* standalone: fill_available_roms removed */"
)
ui_js = ui_js.replace(
    "fill_available_roms('rom_ext', 'stored_exts');",
    "/* standalone: fill_available_roms removed */"
)

# CRITICAL PATCH 0b: Neutralize all navbar show/toggle calls
ui_js = ui_js.replace(
    '$("#navbar").collapse(\'show\')',
    '/* standalone: navbar show disabled */'
)
ui_js = ui_js.replace(
    "$(\"#navbar\").collapse('show')",
    "/* standalone: navbar show disabled */"
)
ui_js = ui_js.replace(
    "$('#navbar').collapse('toggle')",
    "/* standalone: navbar toggle disabled */"
)
ui_js = ui_js.replace(
    "$(\"#navbar\").collapse('toggle')",
    "/* standalone: navbar toggle disabled */"
)

# CRITICAL PATCH 0c: Wrap setup_browser_interface() in try-catch
# This function tries to access browser/search UI elements we don't have in standalone mode
# Without this, its crash kills all subsequent InitWrappers code (mouse, keyboard, ports)
ui_js = ui_js.replace(
    "setup_browser_interface();",
    "try { setup_browser_interface(); } catch(e) { console.log('standalone: setup_browser_interface skipped:', e.message); }"
)

# CRITICAL PATCH 1: Use Blob URL for ROM loading via NATIVE mechanism
# The boot script creates window._STANDALONE_ROM_URL before this JS loads
ui_js = ui_js.replace(
    'let call_param_kickstart_rom_url=null;',
    'let call_param_kickstart_rom_url=window._STANDALONE_ROM_URL || null;'
)

# CRITICAL PATCH 2: Don't show ROM dialog
ui_js = ui_js.replace(
    'let call_param_dialog_on_missing_roms=null;',
    'let call_param_dialog_on_missing_roms=false;'
)

# CRITICAL PATCH 3: Don't wait for injection - let native handler load ROM from URL
# (Leave call_param_wait_for_kickstart_injection as null = default)

# CRITICAL PATCH 4: Inject disk loading into MSG_READY_TO_RUN handler
# After ROM loads and MSG_READY_TO_RUN fires, we load both disks then let wasm_run proceed
ui_js = ui_js.replace(
    'try{on_ready_to_run()} catch(error){console.error(error)}',
    '''// STANDALONE: Configure HW + Load disks FIRST, then start emulator
        console.log("STANDALONE BOOT: Configuring hardware...");
        try {
            wasm_configure("AGNUS_REVISION", "ECS_2MB");
            wasm_configure("DENISE_REVISION", "OCS");
            wasm_configure("CHIP_RAM", "2048");
            wasm_configure("SLOW_RAM", "0");
            wasm_configure("FAST_RAM", "2048");
            wasm_configure("DRIVE_SPEED", "1");
            wasm_configure("floppy_drive_count", "4");
            wasm_configure("CLX_SPR_SPR", "true");
            wasm_configure("CLX_SPR_PLF", "true");
            wasm_configure("CLX_PLF_PLF", "true");
            console.log("Hardware configured OK");
        } catch(e) { console.warn("Config error:", e); }

        // Load disks BEFORE starting emulator so Amiga boots from df0
        if(window._DISK1_DATA) {
            console.log("Loading Disk 1 into df0:", window._DISK1_DATA.length, "bytes");
            wasm_loadfile("shortgrey_disk1.adf", window._DISK1_DATA, 0);
            window._DISK1_DATA = null;
        }
        if(window._DISK2_DATA) {
            console.log("Loading Disk 2 into df1:", window._DISK2_DATA.length, "bytes");
            wasm_loadfile("shortgrey_disk2.adf", window._DISK2_DATA, 1);
            window._DISK2_DATA = null;
        }
        if(window._DISK3_DATA) {
            console.log("Loading Disk 3 into df2:", window._DISK3_DATA.length, "bytes");
            wasm_loadfile("shortgrey_disk3.adf", window._DISK3_DATA, 2);
            window._DISK3_DATA = null;
        }
        if(window._DISK4_DATA) {
            console.log("Loading Disk 4 into df3:", window._DISK4_DATA.length, "bytes");
            wasm_loadfile("shortgrey_disk4.adf", window._DISK4_DATA, 3);
            window._DISK4_DATA = null;
        }
        console.log("STANDALONE BOOT: Disks loaded, starting emulator...");

        // NOW start the emulator (Amiga boots with disks already inserted)
        try{on_ready_to_run()} catch(error){console.error(error)}

        // Clean up UI overlays after a short delay
        setTimeout(function() {
            console.log("STANDALONE: Cleaning up UI overlays...");
            // Remove Bootstrap modal backdrops
            document.querySelectorAll(".modal-backdrop").forEach(function(el){ el.remove(); });
            // Hide any modals
            document.querySelectorAll(".modal.show").forEach(function(el){ el.style.display="none"; });
            // Remove modal-open class from body
            document.body.classList.remove("modal-open");
            document.body.style.overflow = "auto";
            document.body.style.paddingRight = "0";
            // Hide spinner and status
            var spinner = document.getElementById("spinner");
            if(spinner) spinner.style.display = "none";
            var status = document.getElementById("status");
            if(status) status.style.display = "none";
            // Make sure canvas and its parent are visible - NUCLEAR
            var divCanvas = document.getElementById("div_canvas");
            if(divCanvas) { divCanvas.style.display = "block"; divCanvas.style.visibility = "visible"; divCanvas.style.opacity = "1"; divCanvas.style.zIndex = "10"; }
            var canvas = document.getElementById("canvas");
            if(canvas) { canvas.style.display = "block"; canvas.style.visibility = "visible"; canvas.style.opacity = "1"; canvas.style.zIndex = "10"; }
            // Also remove the loaded class if it was added (it hides .emscripten elements!)
            document.body.classList.remove("loaded");
            console.log("STANDALONE: UI cleanup done");
        }, 2000);

        // Canvas guardian - periodically ensure canvas stays visible
        setInterval(function() {
            var c = document.getElementById("canvas");
            var d = document.getElementById("div_canvas");
            if(c && (c.style.display === "none" || c.style.visibility === "hidden")) {
                console.warn("GUARDIAN: Canvas was hidden! Forcing visible.");
                c.style.display = "block";
                c.style.visibility = "visible";
                c.style.opacity = "1";
            }
            if(d && (d.style.display === "none" || d.style.visibility === "hidden")) {
                console.warn("GUARDIAN: div_canvas was hidden! Forcing visible.");
                d.style.display = "block";
                d.style.visibility = "visible";
                d.style.opacity = "1";
            }
            // Remove loaded class from body if present (it kills .emscripten elements)
            if(document.body.classList.contains("loaded")) {
                document.body.classList.remove("loaded");
            }
        }, 500);'''
)

# Patch sound file paths to use data URIs
# The JS uses paths like 'sounds/insert.mp3', 'sounds/eject.mp3', etc.
for snd_name, snd_uri in sounds.items():
    ui_js = ui_js.replace(f"'sounds/{snd_name}.mp3'", f"'{snd_uri}'")
    ui_js = ui_js.replace(f'"sounds/{snd_name}.mp3"', f'"{snd_uri}"')

# CRITICAL PATCH: Inline AudioWorklet processor as Blob URL
# AudioWorklet.addModule() requires a URL, can't use inline code directly
# Solution: embed the processor code as a string, create a Blob URL at runtime
print("Inlining AudioWorklet processor...")
worklet_code = read_file("js/vAmiga_audioprocessor.js")
# Escape for embedding in JS string (backticks template literal)
worklet_code_escaped = worklet_code.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

# Replace the addModule call for the main audio processor
ui_js = ui_js.replace(
    "await audioContext.audioWorklet.addModule('js/vAmiga_audioprocessor.js');",
    f"""{{ const _workletCode = `{worklet_code_escaped}`;
        try {{
            const _workletDataUrl = 'data:application/javascript;base64,' + btoa(_workletCode);
            await audioContext.audioWorklet.addModule(_workletDataUrl);
            console.log('AudioWorklet loaded via data URL');
        }} catch(e1) {{
            try {{
                const _workletBlob = new Blob([_workletCode], {{type: 'application/javascript'}});
                const _workletUrl = URL.createObjectURL(_workletBlob);
                await audioContext.audioWorklet.addModule(_workletUrl);
                URL.revokeObjectURL(_workletUrl);
                console.log('AudioWorklet loaded via blob URL');
            }} catch(e2) {{
                console.warn('AudioWorklet failed, audio may not work:', e2.message);
            }}
        }} }}"""
)

# Also handle the SharedArrayBuffer variant (doesn't exist on server, but neutralize the call)
ui_js = ui_js.replace(
    "await audioContext.audioWorklet.addModule('js/vAmiga_audioprocessor_sharedarraybuffer.js');",
    "/* SharedArrayBuffer audio processor not available in standalone mode */ await Promise.resolve();"
)

# Patch vAmiga_browser.js to remove service worker and update checks
browser_js = js_contents['js/vAmiga_browser.js']
# Remove service worker registration attempts
browser_js = browser_js.replace('navigator.serviceWorker', '(false && navigator.serviceWorker)')
js_contents['js/vAmiga_browser.js'] = browser_js

# Patch storage.js to avoid IndexedDB errors on some mobile browsers
storage_js = js_contents['js/vAmiga_storage.js']
js_contents['js/vAmiga_storage.js'] = storage_js

js_contents['js/vAmiga_ui.js'] = ui_js

# ============================================================
# 5. Build HTML
# ============================================================
print("Building HTML...")

# Inline sprites SVG for xlink:href references
# We need to embed the SVG symbols in the page so <use xlink:href=img/sprites.svg#...> works
# Parse the sprites.svg and create an inline hidden SVG
sprites_inline = sprites_svg.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
# Wrap in a hidden div
sprites_inline_html = f'<div style="display:none">{sprites_inline}</div>'

# Read the original index.html to get the body content structure
index_html = read_file("index.html")

# Extract the body content (between <body...> and </body>)
body_match = re.search(r'<body[^>]*>(.*)</body>', index_html, re.DOTALL)
body_content = body_match.group(1) if body_match else ""

# Remove the inline script blocks from body (we'll add our own)
# Remove the Module init script and vAmiga.js async load
# Find the last <script> block that contains Module definition
script_pattern = r'<script>let light_mode.*?</script>'
body_content = re.sub(script_pattern, '', body_content, flags=re.DOTALL)
# Remove the async vAmiga.js script tag
body_content = body_content.replace('<script src=vAmiga.js async></script>', '')

# Replace image src references with data URIs
body_content = body_content.replace('src=img/icon_borderless_x413.png', f'src="{icon_b64_uri}"')
body_content = body_content.replace('src="img/icon_borderless_x413.png"', f'src="{icon_b64_uri}"')
body_content = body_content.replace('src=img/rom_empty.png', f'src="{rom_empty_b64_uri}"')
body_content = body_content.replace('src="img/rom_empty.png"', f'src="{rom_empty_b64_uri}"')
body_content = body_content.replace('src=img/aros_half.png', f'src="{aros_b64_uri}"')
body_content = body_content.replace('src=img/emutos_header_shadow.png', f'src="{emutos_b64_uri}"')

# Replace sprites.svg references: xlink:href=img/sprites.svg#xxx -> xlink:href=#xxx (using inline SVG)
body_content = body_content.replace('xlink:href=img/sprites.svg#', 'xlink:href=#')
body_content = body_content.replace('xlink:href="img/sprites.svg#', 'xlink:href="#')

# Now build the complete HTML
html = f'''<!DOCTYPE html>
<html lang="en-us">
<head>
<meta charset="utf-8">
<meta content="text/html; charset=utf-8" http-equiv="Content-Type">
<title>The Short Grey - Amiga</title>
<link rel="icon" href="{favicon_b64_uri}">
<meta content="width=device-width,initial-scale=1,user-scalable=no,viewport-fit=cover" name="viewport">
<meta content="yes" name="apple-mobile-web-app-capable">
<meta content="black-translucent" name="apple-mobile-web-app-status-bar">
<meta content="black" name="theme-color">

<style>
/* Bootstrap */
{bootstrap_css}
</style>

<style>
/* vAmiga CSS */
{vamiga_css}
</style>

<style>
/* Emscripten styles */
.emscripten{{padding-right:0;margin-left:auto;margin-right:auto;display:block}}
textarea.emscripten{{font-family:monospace;width:80%}}
div.emscripten{{text-align:center}}
div.emscripten_border{{border:0 solid #000}}
canvas.emscripten{{border:0 none}}
.spinner{{height:50px;width:50px;margin:0 auto;animation:rotation .8s linear infinite;border-left:10px solid #0096f0;border-right:10px solid #0096f0;border-bottom:10px solid #0096f0;border-top:10px solid #6400c8;border-radius:100%;background-color:#c864fa}}
@keyframes rotation{{from{{transform:rotate(0)}}to{{transform:rotate(360deg)}}}}
</style>

<style>
/* Standalone UI overrides - HIDE the original navbar completely */
#button_show_menu {{ display: none !important; }}
#navbar {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
}}
#navbar.collapse {{
    display: none !important;
}}
/* Hide other unwanted UI */
#button_reset, #button_run, #button_ff, #button_speed_toggle,
#button_take_snapshot, #button_snapshots, #button_custom_key,
#button_settings, #button_fullscreen, #btn_activity_monitor,
#theFileInput, #output_row {{ display: none !important; }}

/* Also kill any Bootstrap modal-backdrop */
.modal-backdrop {{ display: none !important; }}
.modal {{ display: none !important; }}

/* Port selectors styling */
.custom-select {{
    font-size: 0.75rem !important;
    padding: 2px 20px 2px 6px !important;
    height: auto !important;
    max-width: 180px;
}}

/* Virtual keyboard at bottom, above navbar */
#virtual_keyboard {{
    position: fixed !important;
    bottom: 40px;
    left: 0;
    right: 0;
    z-index: 999;
}}

/* Canvas fullscreen */
#div_canvas {{
    position: fixed !important;
    top: 0; left: 0; right: 0; bottom: 0;
    width: 100vw !important;
    height: 100vh !important;
}}
#canvas {{
    width: 100% !important;
    height: 100% !important;
    top: 0 !important;
    object-fit: contain;
}}

/* Hide loading elements after boot - BUT NOT the canvas! */
.loaded #spinner,
.loaded #status,
.loaded #progress {{ display: none !important; }}
.loaded div.emscripten {{ display: none !important; }}
/* NEVER hide the canvas or its parent! */
#div_canvas, #div_canvas.emscripten_border {{
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 10 !important;
}}
#canvas, canvas.emscripten {{
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 10 !important;
}}

/* Force-kill ALL modal overlays and backdrops */
.modal-backdrop {{ display: none !important; opacity: 0 !important; pointer-events: none !important; }}
.modal {{ display: none !important; }}
.modal.show {{ display: none !important; }}
.modal-open {{ overflow: auto !important; padding-right: 0 !important; }}
#modal_roms, #modal_settings, #snapshotModal,
#modal_file_slot, #modal_reset, #modal_take_snapshot,
#modal_custom_key {{ display: none !important; }}

/* Hide alerts */
#alert_reset, #alert_wait, #alert_import {{ display: none !important; }}

/* Hide toast/update */
#div_toast {{ display: none !important; }}

/* Mobile optimizations */
@media (max-width: 768px) {{
    .custom-select {{ max-width: 140px; font-size: 0.65rem !important; }}
    #navgrid {{ gap: 4px; }}
}}

/* Minimal control overlay */
#game-controls {{
    position: fixed;
    bottom: 6px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1001;
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(30,30,30,0.88);
    padding: 4px 12px;
    border-radius: 20px;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    transition: opacity 0.3s;
}}
#game-controls.hidden {{ opacity: 0; pointer-events: none; }}
#game-controls select {{
    background: rgba(60,60,60,0.9);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 6px;
    font-size: 0.7rem;
    padding: 3px 6px;
    max-width: 160px;
}}
#game-controls button {{
    background: rgba(60,60,60,0.9);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 6px;
    font-size: 0.8rem;
    padding: 4px 10px;
    cursor: pointer;
}}
#game-controls button:active {{ background: rgba(100,100,100,0.9); }}

/* Toggle button for controls */
#toggle-controls {{
    position: fixed;
    bottom: 6px;
    right: 6px;
    z-index: 1002;
    background: rgba(30,30,30,0.6);
    color: rgba(255,255,255,0.7);
    border: none;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    font-size: 1rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
}}
#toggle-controls:active {{ background: rgba(80,80,80,0.8); }}
</style>

'''

# CRITICAL: ROM Blob URL must be created BEFORE vAmiga_ui.js loads
# because call_param_kickstart_rom_url reads window._STANDALONE_ROM_URL at init time
html += f'''<script>
// === EARLY ROM DECODE (must run before vAmiga_ui.js) ===
console.log("Early ROM decode starting...");
function _b64decode(b64) {{
    var binary = atob(b64);
    var len = binary.length;
    var bytes = new Uint8Array(len);
    for (var i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);
    return bytes;
}}
var _romBytes = _b64decode("{rom_b64}");
console.log("ROM decoded:", _romBytes.length, "bytes");
var _romBlob = new Blob([_romBytes], {{type: 'application/octet-stream'}});
window._STANDALONE_ROM_URL = URL.createObjectURL(_romBlob);
_romBytes = null; _romBlob = null;
console.log("ROM Blob URL ready:", window._STANDALONE_ROM_URL);
</script>

'''

# Add all JS libraries inline
for jsf in js_files_order:
    html += f'<script>\n// === {jsf} ===\n{js_contents[jsf]}\n</script>\n\n'

html += '''
</head>
<body data-theme="dark" oncontextmenu="event.preventDefault()" warpstate="0">
'''

# Add inline SVG sprites
html += sprites_inline_html + '\n'

# Add loading spinner
html += f'''
<figure id="spinner" style="overflow:visible">
    <div class="spinner"></div>
    <center style="margin-top:.5em">
        <img src="{icon_b64_uri}" style="width:38px;height:38px;margin-right:10px">
        <strong>Loading The Short Grey...</strong>
    </center>
</figure>
<div class="emscripten" id="status">Initializing...</div>
<div class="emscripten"><progress hidden id="progress" max="100" value="0"></progress></div>
'''

# Add canvas
html += '''
<div class="emscripten_border" id="div_canvas" style="width:100vw;height:100vh">
    <canvas class="emscripten" height="568" id="canvas" oncontextmenu="event.preventDefault()" tabindex="-1" width="724"></canvas>
</div>
<div id="div_drive_select" ontouchstart="event.stopPropagation()"></div>
'''

# Add virtual keyboard
html += '''
<div class="collapse" id="virtual_keyboard" style="user-select:none">
    <div class="justify-content-center" id="vbk_scroll_area" style="display:flex;flex-wrap:nowrap;overflow-x:auto;overflow-y:hidden">
        <div style="display:flex;padding-top:2px;position:relative;min-width:0;max-width:100%">
            <div id="divKeyboardRows"></div>
        </div>
    </div>
</div>
'''

# Hidden elements needed by the JS (modals, etc.) - keep them but hidden
html += '''
<div id="navbar" style="display:none !important;position:absolute;width:0;height:0;overflow:hidden;pointer-events:none"></div>
<button style="display:none" id="button_show_menu"></button>
<div style="display:none" id="output_row"><div id="output"></div></div>
<div style="display:none" id="alert_reset"></div>
<div style="display:none" id="alert_wait"></div>
<div style="display:none" id="alert_import"></div>
<div style="display:none" id="div_toast"></div>

<!-- Hidden modals (needed by JS references) -->
<div style="display:none" id="modal_roms"></div>
<div style="display:none" id="modal_settings">
    <div id="hardware_settings"></div>
</div>
<div style="display:none" id="modal_file_slot">
    <div id="div_zip_content"></div>
</div>
<div style="display:none" id="snapshotModal">
    <div id="container_snapshots"></div>
</div>
<div style="display:none" id="modal_reset"></div>
<div style="display:none" id="modal_take_snapshot">
    <input id="input_app_title" value="">
</div>
<div style="display:none" id="modal_custom_key">
    <input id="input_button_text" value="">
    <input id="input_button_shortcut" value="">
    <input id="input_action_script" value="">
</div>

<!-- Hidden buttons/inputs needed by JS -->
<div style="display:none">
    <button id="button_reset"></button>
    <button id="button_run"></button>
    <button id="button_ff"></button>
    <button id="button_speed_toggle"></button>
    <button id="button_take_snapshot"></button>
    <button id="button_snapshots"></button>
    <button id="button_keyboard"></button>
    <button id="button_custom_key"></button>
    <button id="button_settings"></button>
    <button id="button_fullscreen"></button>
    <button id="btn_activity_monitor"></button>
    <button id="button_reset_confirmed"></button>
    <button id="button_save_snapshot"></button>
    <button id="button_save_workspace"></button>
    <button id="button_save_custom_button"></button>
    <button id="button_delete_custom_button"></button>
    <button id="button_rom_dialog"></button>
    <button id="button_eject_df0"></button>
    <button id="button_eject_df1"></button>
    <button id="button_eject_df2"></button>
    <button id="button_eject_df3"></button>
    <button id="button_eject_hd0"></button>
    <button id="button_eject_hd1"></button>
    <button id="button_eject_hd2"></button>
    <button id="button_eject_hd3"></button>
    <button id="button_export_df0"></button>
    <button id="button_export_df1"></button>
    <button id="button_export_df2"></button>
    <button id="button_export_df3"></button>
    <button id="button_export_hd0"></button>
    <button id="button_export_hd0_folder"></button>
    <button id="button_export_hd1"></button>
    <button id="button_export_hd1_folder"></button>
    <button id="button_export_hd2"></button>
    <button id="button_export_hd2_folder"></button>
    <button id="button_export_hd3"></button>
    <button id="button_export_hd3_folder"></button>
    <button id="button_insert_file"></button>
    <button id="button_insert_folder"></button>
    <button id="button_eject_zip"></button>
    <button id="button_delete_kickstart"></button>
    <button id="button_delete_kickstart_ext"></button>
    <button id="button_reset_position"></button>
    <button id="export_workspaces"></button>
    <button id="detail_back"></button>
    <select id="stored_roms"></select>
    <select id="stored_exts"></select>
    <input id="volume-slider" type="range" value="0.5" max="1" min="0" step="0.01">
    <input id="dark_switch" type="checkbox">
    <input id="pixel_art_switch" type="checkbox" checked>
    <input id="ntsc_pixel_ratio_switch" type="checkbox">
    <input id="wide_screen_switch" type="checkbox">
    <input id="wake_lock_switch" type="checkbox">
    <input id="warp_switch" type="checkbox">
    <input id="auto_snapshot_switch" type="checkbox">
    <input id="movable_action_buttons_in_settings_switch" type="checkbox" checked>
    <input id="auto_selecting_app_title_switch" type="checkbox" checked>
    <input id="activity_monitor_switch" type="checkbox">
    <input id="cb_debug_output" type="checkbox">
    <input id="key_haptic_feedback" type="checkbox" checked>
    <input id="touch_swap_move_button" type="checkbox">
    <input id="OPT_CLX_SPR_SPR" type="checkbox" checked>
    <input id="OPT_CLX_SPR_PLF" type="checkbox" checked>
    <input id="OPT_CLX_PLF_PLF" type="checkbox" checked>
    <input id="check_app_scope" type="checkbox">
    <input id="check_livecomplete" type="checkbox">
    <input id="move_action_buttons_switch" type="checkbox" checked>
    <input id="sprite0" type="checkbox" class="layer">
    <input id="sprite1" type="checkbox" class="layer">
    <input id="sprite2" type="checkbox" class="layer">
    <input id="sprite3" type="checkbox" class="layer">
    <input id="sprite4" type="checkbox" class="layer">
    <input id="sprite5" type="checkbox" class="layer">
    <input id="sprite6" type="checkbox" class="layer">
    <input id="sprite7" type="checkbox" class="layer">
    <input id="playfield1" type="checkbox" class="layer">
    <input id="playfield2" type="checkbox" class="layer">
    <form id="theFileInput">
        <div id="drop_zone">file slot</div>
        <input id="filedialog" type="file" name="theFileDialog" style="display:none">
    </form>
    <select id="port1"><option value="none">none</option><option value="keys">cursor keys</option><option value="touch" id="touch_joystick1">touch joystick</option><option value="mouse touchpad" id="touch_mouse1">mouse touchpad</option><option value="mouse">mouse</option></select>
    <select id="port2"><option value="none">none</option><option value="keys">cursor keys</option><option value="touch" id="touch_joystick2">touch joystick</option><option value="mouse touchpad" id="touch_mouse2">mouse touchpad</option><option value="mouse">mouse</option></select>
    <div id="button_renderer"></div>
    <div id="choose_renderer"><a href="#" class="dropdown-item">software</a><a href="#" class="dropdown-item">gpu shader</a></div>
    <div id="button_display"></div>
    <div id="choose_display"><a href="#" class="dropdown-item">standard</a></div>
    <div id="button_color_palette"></div>
    <div id="choose_color_palette"><a href="#" class="dropdown-item">color</a></div>
    <div id="button_speed"></div>
    <div id="choose_speed"><a href="#" class="dropdown-item">100%</a></div>
    <div id="button_run_ahead"></div>
    <div id="choose_run_ahead"><a href="#" class="dropdown-item">0 frame</a></div>
    <div id="button_vjoy_touch"></div>
    <div id="choose_vjoy_touch"><a href="#" class="dropdown-item">base moves</a></div>
    <div id="button_vjoy_dead_zone"></div>
    <div id="choose_vjoy_dead_zone"><a href="#" class="dropdown-item">14</a></div>
    <div id="button_vbk_touch"></div>
    <div id="choose_vbk_touch"><a href="#" class="dropdown-item">mix of both</a></div>
    <div id="button_keycap_size"></div>
    <div id="choose_keycap_size"><a href="#" class="dropdown-item">1.00</a></div>
    <div id="button_keyboard_bottom_margin"></div>
    <div id="choose_keyboard_bottom_margin"><a href="#" class="dropdown-item">auto</a></div>
    <div id="button_keyboard_transparency"></div>
    <div id="choose_keyboard_transparency"><a href="#" class="dropdown-item">0</a></div>
    <div id="button_keyboard_sound_volume"></div>
    <div id="choose_keyboard_sound_volume"><a href="#" class="dropdown-item">50</a></div>
    <div id="button_game_controller_type_choice"></div>
    <div id="choose_game_controller_type"><a href="#" class="dropdown-item">1</a></div>
    <div id="button_padding"></div>
    <div id="choose_padding"><a href="#" class="dropdown-item">default</a></div>
    <div id="button_opacity"></div>
    <div id="choose_opacity"><a href="#" class="dropdown-item">default</a></div>
    <div id="button_script_language"></div>
    <div id="choose_script_language"><a href="#" class="dropdown-item">actionscript</a></div>
    <div id="button_script_add"></div>
    <div id="predefined_actions"><div id="add_javascript"></div><div id="add_special_key"></div><div id="add_joystick1_action"></div><div id="add_joystick2_action"></div><div id="add_timer_action"></div><div id="add_system_action"></div></div>
    <div id="other_buttons"></div>
    <div id="sel_browser_workspace_db"></div>
    <div id="sel_browser_snapshots"></div>
    <input id="search" class="form-control">
    <div id="div_like"></div>
    <div id="view_detail"><div id="detail_content"></div></div>
    <div id="kickstart_title"></div>
    <div id="kickstart_ext_title"></div>
    <img id="rom_kickstart"><img id="rom_kickstart_ext">
    <div id="button_fetch_open_roms"></div>
    <div id="update_dialog"></div>
    <div id="version_display"></div>
    <span id="volumetext"></span>
    <span id="activity_help"></span>
    <span id="wake_lock_status"></span>
    <div id="speed_text"></div>
    <div id="run_ahead_text"></div>
    <div id="move_action_buttons_label_settings"></div>
    <div id="auto_select_on_help"></div>
    <div id="auto_select_off_help"></div>
    <div id="move_action_buttons_label"></div>
    <div id="file_slot_dialog_label"></div>
    <div id="input_button_text_error"></div>
    <div id="input_button_shortcut_error"></div>
    <div id="action_button_syntax_error"></div>
    <div id="check_app_scope_label"></div>
    <div id="check_livecomplete_label"></div>
    <div id="base_moves_text"></div>
    <div id="base_fixed_on_first_touch_text"></div>
    <div id="stationary_middle_text"></div>
    <div id="stationary_bottom_text"></div>
    <div id="exact_timing_text"></div>
    <div id="smartphone_like_text"></div>
    <div id="mix_of_both_text"></div>
    <div id="gc_buttons_1"></div>
    <div id="gc_buttons_2"></div>
    <div id="gc_buttons_3"></div>
    <div id="touch_swap_move_button_false"></div>
    <div id="touch_swap_move_button_true"></div>
    <div id="movable_button_label"></div>
    <span id="svg_fullscreen"></span>
    <div id="warping" style="display:none"></div>
    <div id="no_warping"></div>
</div>
'''

# Add our custom minimal controls overlay
html += '''
<!-- Custom game controls overlay -->
<div id="game-controls">
    <label style="color:#aaa;font-size:0.65rem;margin:0">P1:</label>
    <select id="ctrl-port1" onchange="document.getElementById('port1').value=this.value;document.getElementById('port1').dispatchEvent(new Event('change'))">
        <option value="none">None</option>
        <option value="keys">Keyboard</option>
        <option value="touch">Touch Joystick</option>
        <option value="mouse touchpad">Touch Mouse</option>
        <option value="mouse" selected>Mouse</option>
    </select>
    <label style="color:#aaa;font-size:0.65rem;margin:0">P2:</label>
    <select id="ctrl-port2" onchange="document.getElementById('port2').value=this.value;document.getElementById('port2').dispatchEvent(new Event('change'))">
        <option value="none" selected>None</option>
        <option value="keys">Keyboard</option>
        <option value="touch">Touch Joystick</option>
        <option value="mouse touchpad">Touch Mouse</option>
        <option value="mouse">Mouse</option>
    </select>
    <button id="btn-vkb" onclick="if(window.app&&window.app.button_keyboard_click){window.app.button_keyboard_click();}else{var b=document.getElementById('button_keyboard');if(b)b.dispatchEvent(new PointerEvent('pointerup',{bubbles:true}));}" title="Virtual Keyboard">⌨️</button>
</div>
<button id="toggle-controls" onclick="var c=document.getElementById('game-controls');c.classList.toggle('hidden');" title="Toggle Controls">🎮</button>
'''

# Now add the critical boot script
html += f'''
<script>
// ============================================================
// STANDALONE BOOT - NATIVE FLOW APPROACH
// ============================================================
// Strategy: Use vAmiga's NATIVE message system (MSG_ROM_MISSING / MSG_READY_TO_RUN)
// 1. ROM: Create Blob URL → set window._STANDALONE_ROM_URL → vAmiga_ui.js picks it up
//    via call_param_kickstart_rom_url and fetches it normally
// 2. Disks: Store as window._DISK1_DATA/_DISK2_DATA → loaded in MSG_READY_TO_RUN handler
// 3. WASM: Provide binary directly via Module.wasmBinary

// Embedded data (base64) - ROM already decoded in early script
var WASM_B64 = "{wasm_b64}";
var DISK1_B64 = "{disk1_b64}";
var DISK2_B64 = "{disk2_b64}";
var DISK3_B64 = "{disk3_b64}";
var DISK4_B64 = "{disk4_b64}";

// Reuse decode function from early script or define it
if(typeof _b64decode === 'undefined') {{
    window._b64decode = function(b64) {{
        var binary = atob(b64);
        var len = binary.length;
        var bytes = new Uint8Array(len);
        for (var i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);
        return bytes;
    }};
}}

// --- Step 1: ROM already loaded as Blob URL in early script ---
console.log("ROM Blob URL (from early decode):", window._STANDALONE_ROM_URL);

// --- Step 2: Prepare disk data as globals for MSG_READY_TO_RUN handler ---
console.log("Decoding embedded disks...");
window._DISK1_DATA = _b64decode(DISK1_B64);
DISK1_B64 = null;
console.log("Disk 1 decoded:", window._DISK1_DATA.length, "bytes");
window._DISK2_DATA = _b64decode(DISK2_B64);
DISK2_B64 = null;
console.log("Disk 2 decoded:", window._DISK2_DATA.length, "bytes");
window._DISK3_DATA = _b64decode(DISK3_B64);
DISK3_B64 = null;
console.log("Disk 3 decoded:", window._DISK3_DATA.length, "bytes");
window._DISK4_DATA = _b64decode(DISK4_B64);
DISK4_B64 = null;
console.log("Disk 4 decoded:", window._DISK4_DATA.length, "bytes");

// --- Step 3: Decode WASM binary ---
console.log("Decoding embedded WASM...");
var wasmBytes = _b64decode(WASM_B64);
WASM_B64 = null;
console.log("WASM decoded:", wasmBytes.length, "bytes");

// Suppress body touch scroll (Amiga emulator needs this)
document.body.addEventListener('touchmove', function(e) {{
    var t = e.target;
    while (t && t !== document.body) {{
        if (t.id === 'virtual_keyboard' || t.id === 'game-controls' ||
            (t.classList && (t.classList.contains('modal-body') || t.classList.contains('modal-dialog')))) {{
            return;
        }}
        t = t.parentNode;
    }}
    e.preventDefault();
}}, {{capture: false, passive: false}});

// --- Step 4: Module configuration ---
var statusElement = document.getElementById('status');
var progressElement = document.getElementById('progress');
var spinnerElement = document.getElementById('spinner');

var Module = {{
    preRun: [function() {{}}],
    postRun: [function() {{
        console.log("postRun: calling InitWrappers...");
        InitWrappers();
        console.log("InitWrappers complete - native message system active");
        // Hide loading UI after init
        setTimeout(function() {{
            document.body.classList.add('loaded');
            if (spinnerElement) spinnerElement.style.display = 'none';
            if (statusElement) statusElement.style.display = 'none';
        }}, 2000);
    }}],
    print: function() {{
        var element = document.getElementById('output');
        if (element) element.value = '';
        return function(text) {{ console.log(text); }};
    }}(),
    printErr: function(text) {{ console.error(text); }},
    canvas: (function() {{
        var canvas = document.getElementById('canvas');
        canvas.addEventListener('webglcontextlost', function(e) {{
            console.error('WebGL context lost');
            e.preventDefault();
        }}, false);
        return canvas;
    }})(),
    setStatus: function(text) {{
        if (statusElement) statusElement.innerHTML = text;
    }},
    totalDependencies: 0,
    monitorRunDependencies: function(left) {{
        this.totalDependencies = Math.max(this.totalDependencies, left);
        Module.setStatus(left ? 'Preparing... (' + (this.totalDependencies - left) + '/' + this.totalDependencies + ')' : 'All downloads complete.');
    }},
    wasmBinary: wasmBytes.buffer
}};

Module.setStatus('Initializing emulator...');

// Audio unlock on first user interaction (required by browsers)
(function() {{
    var audioUnlocked = false;
    function unlockAudio() {{
        if (audioUnlocked) return;
        audioUnlocked = true;
        try {{
            var AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {{
                var ctx = new AudioContext();
                if (ctx.state === 'suspended') ctx.resume();
            }}
        }} catch(e) {{}}
        document.removeEventListener('touchstart', unlockAudio);
        document.removeEventListener('click', unlockAudio);
        document.removeEventListener('keydown', unlockAudio);
    }}
    document.addEventListener('touchstart', unlockAudio, {{once: true}});
    document.addEventListener('click', unlockAudio, {{once: true}});
    document.addEventListener('keydown', unlockAudio, {{once: true}});
}})();

// Sync our custom controls with the hidden originals
document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(function() {{
        try {{
            var p1 = document.getElementById('port1');
            var p2 = document.getElementById('port2');
            if (p1) {{ p1.value = 'mouse'; p1.dispatchEvent(new Event('change')); }}
            if (p2) {{ p2.value = 'none'; p2.dispatchEvent(new Event('change')); }}
        }} catch(e) {{}}
    }}, 2000);
}});

window.onerror = function(msg, url, line, col, error) {{
    console.error("Error:", msg, "at", url, ":", line);
}};
</script>

<script>
// === vAmiga.js (Emscripten WASM loader) ===
{vamiga_js}
</script>

</body>
</html>
'''

# ============================================================
# 6. Write output
# ============================================================
output_path = "/tmp/work/short_grey.html"
print(f"Writing output to {output_path}...")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

file_size = os.path.getsize(output_path)
print(f"\n=== BUILD COMPLETE ===")
print(f"Output: {output_path}")
print(f"Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
print(f"  WASM: {len(wasm_b64):,} chars (base64)")
print(f"  ROM: {len(rom_b64):,} chars (base64)")
print(f"  Disk1: {len(disk1_b64):,} chars (base64)")
print(f"  Disk2: {len(disk2_b64):,} chars (base64)")
print(f"  Disk3: {len(disk3_b64):,} chars (base64)")
print(f"  Disk4: {len(disk4_b64):,} chars (base64)")
