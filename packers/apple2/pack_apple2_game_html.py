#!/usr/bin/env python3
"""
Apple II Game Packer — Creates a self-contained offline HTML page from an Apple II disk image.
Embeds apple2js emulator + disk image + virtual mobile keyboard.

Usage:
    python3 pack_apple2_game_html.py game.dsk
    python3 pack_apple2_game_html.py game.dsk --title "Mystery House VF"
    python3 pack_apple2_game_html.py game.dsk --model apple2plus
    python3 pack_apple2_game_html.py game.dsk --extra-keys UP DOWN LEFT RIGHT

Supported formats: .dsk, .do, .po, .nib, .woz
"""

import argparse, base64, os, re, sys, urllib.request, json

# ============================================================
#  Apple II Disk Parser (basic .dsk catalog reader)
# ============================================================
def parse_dsk_catalog(data):
    """Parse a DOS 3.3 .dsk file and return catalog entries."""
    entries = []
    
    if len(data) != 143360 and len(data) != 116480:
        return entries  # Not a standard .dsk
    
    # DOS 3.3: 16 sectors/track, 256 bytes/sector
    # Catalog starts at track 17, sector 15
    # DOS 3.1/3.2: 13 sectors/track
    sectors_per_track = 16 if len(data) == 143360 else 13
    bytes_per_sector = 256
    
    def read_sector(track, sector):
        offset = (track * sectors_per_track + sector) * bytes_per_sector
        if offset + bytes_per_sector <= len(data):
            return data[offset:offset + bytes_per_sector]
        return None
    
    # Read VTOC (Volume Table of Contents) at track 17, sector 0
    vtoc = read_sector(17, 0)
    if not vtoc:
        return entries
    
    cat_track = vtoc[1]
    cat_sector = vtoc[2]
    
    # Walk catalog chain
    visited = set()
    while cat_track != 0 and (cat_track, cat_sector) not in visited:
        visited.add((cat_track, cat_sector))
        sector_data = read_sector(cat_track, cat_sector)
        if not sector_data:
            break
        
        # Each catalog sector has 7 file entries starting at offset 11
        for i in range(7):
            entry_offset = 11 + i * 35
            entry = sector_data[entry_offset:entry_offset + 35]
            if len(entry) < 35:
                break
            
            first_ts_track = entry[0]
            if first_ts_track == 0 or first_ts_track == 0xFF:
                continue
            
            file_type = entry[2]
            name_bytes = entry[3:33]
            # Strip high bits and decode
            name = ''.join(chr(b & 0x7F) for b in name_bytes).strip()
            
            type_map = {0x00: 'T', 0x01: 'I', 0x02: 'A', 0x04: 'B',
                        0x08: 'S', 0x10: 'R', 0x20: 'A', 0x40: 'B'}
            ft = type_map.get(file_type & 0x7F, '?')
            locked = '*' if file_type & 0x80 else ' '
            
            entries.append({
                'name': name,
                'type': ft,
                'locked': locked,
                'full': f"{locked}{ft} {name}"
            })
        
        cat_track = sector_data[1]
        cat_sector = sector_data[2]
    
    return entries

# ============================================================
#  Key Detection
# ============================================================
def detect_keys_from_disk(data):
    """Detect likely key usage from disk content."""
    keys = set()
    
    # Try to find text content
    try:
        # Look for common adventure game keywords in the disk
        text = ''.join(chr(b & 0x7F) for b in data if 32 <= (b & 0x7F) <= 126)
        
        # Text adventure patterns (French/English)
        adventure_words = ['NORD', 'SUD', 'EST', 'OUEST', 'NORTH', 'SOUTH', 'EAST', 'WEST',
                          'PRENDRE', 'TAKE', 'GET', 'LOOK', 'REGARDER', 'OUVRIR', 'OPEN',
                          'INVENTAIRE', 'INVENTORY', 'ALLER', 'GO', 'ENTRER', 'ENTER',
                          'EXAMINER', 'EXAMINE', 'UTILISER', 'USE', 'DIRE', 'SAY']
        
        text_upper = text.upper()
        adventure_score = sum(1 for w in adventure_words if w in text_upper)
        
        if adventure_score >= 3:
            keys.add('FULL_KEYBOARD')
            keys.add('TEXT_ADVENTURE')
        
        # Look for INPUT or GET statements (Applesoft BASIC)
        if 'INPUT' in text_upper or 'GET ' in text_upper:
            keys.add('FULL_KEYBOARD')
        
        # Look for joystick/paddle references
        if 'PDL(' in text_upper or 'PADDLE' in text_upper:
            keys.update(['UP', 'DOWN', 'LEFT', 'RIGHT'])
            
    except:
        pass
    
    # If nothing detected, default to full keyboard (safe choice)
    if not keys:
        keys.add('FULL_KEYBOARD')
    
    return keys

def determine_keyboard_layout(keys, extra_keys=None):
    """Determine the virtual keyboard layout."""
    has_full = 'FULL_KEYBOARD' in keys
    has_arrows = any(k in keys for k in ['UP', 'DOWN', 'LEFT', 'RIGHT'])
    
    layout = {
        'arrows': has_arrows or has_full,
        'letters': list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') if has_full else [],
        'digits': list('0123456789') if has_full else [],
        'special': [],
        'actions': ['SPACE', 'RETURN', 'DELETE'],
    }
    
    if extra_keys:
        for k in extra_keys:
            ku = k.upper()
            if ku in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                layout['arrows'] = True
    
    return layout

# ============================================================
#  Apple2js Assets Download
# ============================================================
APPLE2JS_BUNDLE_URL = "https://www.scullinsteel.com/apple2/dist/main2.bundle.js"
APPLE2JS_CSS_URL = "https://www.scullinsteel.com/apple2/css/apple2.css"
APPLE2JS_WORKER_URL = "https://www.scullinsteel.com/apple2/dist/format_worker.bundle.js"

# ROM chunks — webpack lazy-loaded by apple2js, must be pre-embedded
# Each model needs a system ROM chunk + a character ROM chunk.
# These self-register via (self.webpackChunkApple2 = ...).push(...)
APPLE2JS_ROM_CHUNKS_URL = "https://www.scullinsteel.com/apple2/dist/"
ROM_CHUNKS_FOR_MODEL = {
    # model: (system_rom_chunk_id, character_rom_chunk_id)
    'apple2':      ('418', '298'),   # intbasic + apple2_char
    'apple2plus':  ('419', '298'),   # fpbasic + apple2_char  (default fallback)
    'apple2e':     ('90',  '327'),   # apple2e + apple2e_char
}

def download_asset(url, cache_path=None):
    """Download a web asset, with optional local caching."""
    if cache_path and os.path.isfile(cache_path):
        print(f"  Using cached: {cache_path}")
        with open(cache_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    print(f"  Downloading: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    content = urllib.request.urlopen(req).read().decode('utf-8')
    
    if cache_path:
        os.makedirs(os.path.dirname(cache_path) or '.', exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return content

# ============================================================
#  Virtual Keyboard
# ============================================================
# Apple II keyboard sends standard key codes
KEY_CODE_MAP = {
    'ArrowUp': 'ArrowUp', 'ArrowDown': 'ArrowDown',
    'ArrowLeft': 'ArrowLeft', 'ArrowRight': 'ArrowRight',
    'Space': 'Space', 'Return': 'Enter', 'Delete': 'Backspace',
    'Escape': 'Escape',
    # Letters
    'A': 'KeyA', 'B': 'KeyB', 'C': 'KeyC', 'D': 'KeyD',
    'E': 'KeyE', 'F': 'KeyF', 'G': 'KeyG', 'H': 'KeyH',
    'I': 'KeyI', 'J': 'KeyJ', 'K': 'KeyK', 'L': 'KeyL',
    'M': 'KeyM', 'N': 'KeyN', 'O': 'KeyO', 'P': 'KeyP',
    'Q': 'KeyQ', 'R': 'KeyR', 'S': 'KeyS', 'T': 'KeyT',
    'U': 'KeyU', 'V': 'KeyV', 'W': 'KeyW', 'X': 'KeyX',
    'Y': 'KeyY', 'Z': 'KeyZ',
    # Digits
    '0': 'Digit0', '1': 'Digit1', '2': 'Digit2', '3': 'Digit3',
    '4': 'Digit4', '5': 'Digit5', '6': 'Digit6', '7': 'Digit7',
    '8': 'Digit8', '9': 'Digit9',
}

def build_keyboard_html(layout):
    """Generate HTML for the virtual keyboard."""
    rows = []
    
    # Row 1: Arrows + Space + Return
    row1 = []
    if layout['arrows']:
        row1.extend([
            ('↑N', 'ArrowUp', 'dir'),
            ('↓S', 'ArrowDown', 'dir'),
            ('←W', 'ArrowLeft', 'dir'),
            ('→E', 'ArrowRight', 'dir'),
        ])
    row1.append(('ESPACE', 'Space', 'sp'))
    row1.append(('RETURN', 'Return', 'ent'))
    rows.append(row1)
    
    # Row 2-3: Letters (split into 2 rows)
    if layout['letters']:
        row2 = [(l, l, 'act') for l in layout['letters'][:13]]
        row3 = [(l, l, 'act') for l in layout['letters'][13:]]
        rows.append(row2)
        rows.append(row3)
    
    # Row 4: Digits + Backspace
    if layout['digits']:
        row4 = [(d, d, '') for d in layout['digits']]
        row4.append(('⌫', 'Delete', ''))
        rows.append(row4)
    
    # Build HTML
    html_parts = []
    for row in rows:
        btns = ''
        for label, keyname, css_class in row:
            code = KEY_CODE_MAP.get(keyname, keyname)
            cls = f' class="{css_class}"' if css_class else ''
            btns += f'<button data-c="{code}"{cls}>{label}</button>'
        html_parts.append(f'  <div class="r">{btns}</div>')
    
    return '\n'.join(html_parts)

# ============================================================
#  HTML Generation
# ============================================================
def clean_css_for_embed(css):
    """Clean apple2.css for embedding: replace image references with CSS alternatives."""
    # Replace disk light PNGs with simple CSS
    css = css.replace("url(red-off-16.png)", "none")
    css = css.replace("url(red-on-16.png)", "none")
    # Remove apple key images (not needed for gameplay)
    css = re.sub(r'url\(\.\./img/[^)]+\)', 'none', css)
    return css

def generate_html(dsk_path, title, layout, bundle_js, css, rom_chunks, worker_js, model='apple2plus'):
    """Generate the complete self-contained HTML file."""
    
    # Read and encode disk image
    with open(dsk_path, 'rb') as f:
        dsk_data = f.read()
    dsk_b64 = base64.b64encode(dsk_data).decode()
    
    # Detect extension
    ext = os.path.splitext(dsk_path)[1].lstrip('.').lower()
    if ext == 'dsk':
        ext = 'do'  # apple2js uses 'do' for DOS-order .dsk files
    
    keyboard_html = build_keyboard_html(layout)
    
    # Clean CSS for embedding
    clean_css = clean_css_for_embed(css)
    
    # Generate help keys table
    help_rows = []
    if layout['arrows']:
        help_rows.append('    <tr><td><kbd>↑N</kbd><kbd>↓S</kbd><kbd>←W</kbd><kbd>→E</kbd></td><td>Raccourcis : GO NORTH / SOUTH / WEST / EAST</td></tr>')
    if layout['letters']:
        help_rows.append('    <tr><td><kbd>A</kbd>-<kbd>Z</kbd></td><td>Saisie de texte / Commandes</td></tr>')
    if layout['digits']:
        help_rows.append(f'    <tr><td><kbd>0</kbd>-<kbd>9</kbd></td><td>Saisie numérique</td></tr>')
    help_rows.append('    <tr><td><kbd>ESPACE</kbd></td><td>Continuer / Action</td></tr>')
    help_rows.append('    <tr><td><kbd>RETURN</kbd></td><td>Valider la commande</td></tr>')
    help_rows.append('    <tr><td><kbd>⌫</kbd></td><td>Effacer</td></tr>')
    help_keys_html = '\n'.join(help_rows)
    
    html = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>__TITLE__</title>
<style>
__APPLE2_CSS__
</style>
<style>
    /* Override body for fullscreen game display */
    html,body{width:100%;height:100%;margin:0;padding:0;overflow:hidden;
      touch-action:manipulation;-webkit-user-select:none;user-select:none}
    
    /* Make canvas fill the screen */
    .outer{position:absolute;top:0;left:0;width:100%;height:100%;display:flex;
      align-items:center;justify-content:center;background:#000}
    .overscan{width:100%;height:100%;display:flex;align-items:center;justify-content:center}
    #screen{max-width:100%;max-height:100%;object-fit:contain;image-rendering:pixelated}
    
    /* Hide apple2js UI elements we don't need */
    .inset,#header,#exit-fullscreen,#keyboard,.modal{display:none!important}
    #display{display:flex;align-items:center;justify-content:center;width:100%;height:100%}
    
    /* Show loading modal only */
    #loading-modal{display:block!important;position:fixed;top:50%;left:50%;
      transform:translate(-50%,-50%);z-index:5000;color:#0f0;font-family:monospace;
      font-size:14px;text-align:center}
    #loading-modal.is-open{display:block!important}
    #loading-modal:not(.is-open){display:none!important}
    
    /* Top-left floating buttons */
    .float-btn{
      position:fixed;z-index:2000;
      width:32px;height:32px;border-radius:6px;
      background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);
      color:rgba(255,255,255,.45);font-size:16px;cursor:pointer;
      display:none;align-items:center;justify-content:center;
      -webkit-tap-highlight-color:transparent;
      transition:opacity .3s;
    }
    .float-btn:active{background:rgba(0,255,0,.3);color:#0f0}
    @media(pointer:coarse),(hover:none){.float-btn{display:flex}}
    #kb-btn{top:8px;left:8px}
    #help-btn{top:8px;left:48px}

    /* Virtual keyboard */
    #vkb{
      display:none;position:fixed;bottom:0;left:0;right:0;z-index:1500;
      padding:4px 2px 6px;
      background:rgba(0,0,0,.85);
      backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);
      border-top:1px solid rgba(0,255,0,.2);
    }
    #vkb .r{display:flex;justify-content:center;gap:2px;margin-bottom:2px}
    #vkb .r:last-child{margin-bottom:0}
    #vkb button{
      font-family:monospace,system-ui;font-size:13px;font-weight:700;
      color:#0f0;background:rgba(0,255,0,.08);
      border:1px solid rgba(0,255,0,.2);border-radius:4px;
      min-width:22px;height:32px;padding:0 2px;
      cursor:pointer;-webkit-tap-highlight-color:transparent;
      flex:1;max-width:34px;
    }
    #vkb button:active,#vkb button.on{
      background:rgba(0,255,0,.4);border-color:#0f0;color:#fff;
    }
    #vkb button.sp{max-width:100px;flex:3;font-size:10px}
    #vkb button.ent{max-width:72px;flex:2;background:rgba(0,255,0,.12);font-size:10px}
    #vkb button.act{color:#8f8}
    #vkb button.dir{background:rgba(0,128,255,.12);border-color:rgba(0,128,255,.3);color:#8cf;font-size:11px}

    /* Help overlay */
    #help{
      display:none;position:fixed;top:0;left:0;right:0;bottom:0;z-index:3000;
      background:rgba(0,0,0,.92);
      backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
      overflow-y:auto;padding:16px;color:#ddd;
      font-family:system-ui,-apple-system,sans-serif;font-size:14px;line-height:1.5;
    }
    #help h2{color:#0f0;font-size:18px;margin:12px 0 6px;border-bottom:1px solid rgba(0,255,0,.3);padding-bottom:4px}
    #help h3{color:#8cf;font-size:15px;margin:10px 0 4px}
    #help .close-help{
      position:sticky;top:0;float:right;
      background:rgba(255,0,0,.2);border:1px solid rgba(255,0,0,.4);
      color:#f88;border-radius:6px;padding:4px 12px;cursor:pointer;font-size:14px;
      z-index:1;
    }
    #help kbd{
      background:rgba(0,255,0,.2);border:1px solid rgba(0,255,0,.4);
      border-radius:3px;padding:1px 5px;color:#0f0;font-family:monospace;font-size:13px;
    }
    #help table{border-collapse:collapse;width:100%;margin:6px 0}
    #help td,#help th{border:1px solid rgba(255,255,255,.15);padding:3px 8px;text-align:left}
    #help th{background:rgba(0,255,0,.1);color:#0f0}
    #help .tip{color:#8f8;font-style:italic}
    
    /* Disk light indicator */
    .disk-light{display:none}
    .disk-light.on{display:block;position:fixed;top:8px;right:8px;width:8px;height:8px;
      border-radius:50%;background:#f00;box-shadow:0 0 6px #f00;z-index:2000}
</style>
</head>
<body class="apple2">

<!-- Apple2js required DOM structure -->
<div class="outer">
  <div id="display">
    <div class="overscan">
      <canvas id="screen" width="592" height="416" tabindex="-1"></canvas>
    </div>
  </div>
</div>

<!-- Hidden but required DOM stubs for apple2js -->
<div style="display:none">
  <div id="exit-fullscreen"><button>X</button></div>
  <div id="header"><div id="subtitle"></div></div>
  <div class="inset">
    <div class="disk"><div class="disk-light" id="disk1"></div><div id="disk-label1" class="disk-label"></div></div>
    <div class="disk"><div class="disk-light" id="disk2"></div><div id="disk-label2" class="disk-label"></div></div>
  </div>
  <div class="inset">
    <div id="khz">0 kHz</div>
    <button id="pause-run"><i class="fas fa-pause"></i></button>
    <button id="toggle-sound"><i class="fas fa-volume-off"></i></button>
    <button id="toggle-printer"></button>
  </div>
  <div class="inset"><div id="keyboard"></div></div>
  
  <!-- Modal stubs -->
  <div class="modal" id="loading-modal" aria-hidden="true">
    <div class="modal__overlay"><div class="modal__container">
      <header class="modal__header"><div class="modal__title" id="loading-modal-title">Loading...</div></header>
      <main class="modal__content" id="loading-modal-content"><div class="meter"><div class="progress"></div></div></main>
    </div></div>
  </div>
  <div class="modal" id="options-modal" aria-hidden="true">
    <div class="modal__overlay"><div class="modal__container">
      <header class="modal__header"><span class="modal__title" id="options-modal-title">Options</span></header>
      <main class="modal__content" id="options-modal-content"></main>
    </div></div>
  </div>
  <div class="modal" id="save-modal" aria-hidden="true">
    <div class="modal__overlay"><div class="modal__container">
      <header class="modal__header"><span class="modal__title" id="save-modal-title">Save</span></header>
      <main class="modal__content" id="save-modal-content">
        <input type="text" id="save_name"/><a id="local_save_link"></a>
      </main>
    </div></div>
  </div>
  <div class="modal" id="manage-modal" aria-hidden="true">
    <div class="modal__overlay"><div class="modal__container">
      <main class="modal__content" id="manage-modal-content"></main>
    </div></div>
  </div>
  <div class="modal" id="http-modal" aria-hidden="true">
    <div class="modal__overlay"><div class="modal__container">
      <main class="modal__content" id="http-modal-content"><input type="text" id="http_url"/></main>
    </div></div>
  </div>
  <div class="modal" id="load-modal" aria-hidden="true">
    <div class="modal__overlay"><div class="modal__container">
      <main class="modal__content" id="load-modal-content">
        <select id="category_select"></select><select id="disk_select"></select>
        <input type="file" id="local_file"/>
        <div id="local_file_address_input"><input id="local_file_address"/></div>
      </main>
    </div></div>
  </div>
  <div class="modal" id="printer-modal" aria-hidden="true">
    <div class="modal__overlay"><div class="modal__container">
      <main class="modal__content" id="printer-modal-content"><div class="paper"></div></main>
      <footer><a id="raw_printer_output"></a></footer>
    </div></div>
  </div>
  <div class="modal" id="alert-modal" aria-hidden="true">
    <div class="modal__overlay"><div class="modal__container">
      <header class="modal__header"><span class="modal__title" id="alert-modal-title">Alert</span></header>
      <main class="modal__content" id="alert-modal-content"><div class="message"></div></main>
    </div></div>
  </div>
</div>

<!-- SVG filter for green monitor -->
<svg width="0" height="0" xmlns="http://www.w3.org/2000/svg">
  <filter id="green">
    <feColorMatrix type="matrix"
      values="0.0 0.0 0.0 0.0 0
              0.0 1.0 0.0 0.0 0
              0.0 0.0 0.5 0.0 0
              0.0 0.0 0.0 1.0 0"/>
  </filter>
</svg>

<button id="kb-btn" class="float-btn" aria-label="Clavier">⌨</button>
<button id="help-btn" class="float-btn" aria-label="Aide">?</button>

<!-- Help overlay -->
<div id="help">
  <button class="close-help" onclick="document.getElementById('help').style.display='none'">✕ Fermer</button>
  <h2>🍎 __TITLE__</h2>
  <p>Jeu Apple II émulé dans votre navigateur via apple2js.</p>
  <h2>📋 Contrôles</h2>
  <p>Sur mobile, utilisez le clavier virtuel (bouton <kbd>⌨</kbd> en haut à gauche).<br>
  Sur ordinateur, utilisez votre clavier physique. Cliquez d'abord sur l'écran pour lui donner le focus.</p>
  <h3>Touches disponibles</h3>
  <table>
    <tr><th>Touche</th><th>Usage</th></tr>
__HELP_KEYS__
  </table>
  <p class="tip">💡 Si le jeu ne répond pas, cliquez sur l'écran de l'émulateur pour lui donner le focus.</p>
  <p style="margin-top:16px;color:#888;font-size:12px;text-align:center">Émulé via apple2js — 100% hors-ligne</p>
</div>

<!-- Virtual Keyboard -->
<div id="vkb">
__KEYBOARD_HTML__
</div>

<!-- Preferences: force 2D canvas (WebGL OES_texture_float not available on many devices) -->
<script>try{localStorage.setItem("gl_canvas","false")}catch(e){}</script>

<!-- Disk index (required by apple2js for catalog init) -->
<script>disk_index=[];</script>

<!-- Pre-loaded ROM chunks (self-register via webpackChunkApple2) -->
__ROM_CHUNKS__

<!-- Intercept fetch to serve embedded disk -->
<script>
(function(){
  var DSK_B64="__DSK_B64__";
  var DSK_EXT="__DSK_EXT__";
  var DSK_NAME="__DSK_NAME__";
  var origFetch=window.fetch;
  window.fetch=function(url,opts){
    if(typeof url==="string" && url.indexOf("embedded://")===0){
      var binary=atob(DSK_B64);
      var bytes=new Uint8Array(binary.length);
      for(var i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
      return Promise.resolve(new Response(bytes.buffer,{
        status:200,
        headers:{"Content-Type":"application/octet-stream","Content-Length":String(bytes.length)}
      }));
    }
    return origFetch.apply(this,arguments);
  };
  window.location.hash=encodeURIComponent("embedded://"+DSK_NAME+"."+DSK_EXT);
})();
</script>

<!-- Disable Worker to force synchronous disk loading (avoids race condition) -->
<script>window.Worker=undefined;</script>

<!-- Disable AudioWorklet to force ScriptProcessor fallback -->
<!-- (AudioWorklet.addModule needs external JS module not available in standalone HTML) -->
<script>
try{Object.defineProperty(window,'AudioWorklet',{value:undefined,writable:true,configurable:true})}
catch(e){try{window.AudioWorklet=undefined}catch(e2){}}
</script>

<!-- Audio fix: track AudioContexts and resume on first user gesture -->
<!-- (Chrome mobile suspends AudioContext until user interaction. Our virtual keyboard
     calls stopPropagation(), which blocks apple2js's own autoStart listener on window.
     Fix: use capture-phase listeners on document, which fire BEFORE stopPropagation.) -->
<script>
(function(){
  var contexts=[];
  var Orig=window.AudioContext||window.webkitAudioContext;
  if(!Orig)return;
  function Tracked(opts){var ctx=new Orig(opts);contexts.push(ctx);return ctx}
  Tracked.prototype=Orig.prototype;
  window.AudioContext=Tracked;
  if(window.webkitAudioContext)window.webkitAudioContext=Tracked;
  function resumeAll(){
    contexts.forEach(function(c){if(c.state==='suspended')c.resume()});
  }
  ['touchstart','mousedown','keydown'].forEach(function(evt){
    document.addEventListener(evt,function h(){
      resumeAll();setTimeout(resumeAll,100);setTimeout(resumeAll,500);
      document.removeEventListener(evt,h,true);
    },true);
  });
})();
</script>

<!-- Apple2js Bundle -->
<script>__APPLE2JS_BUNDLE__</script>

<script>
// --- Help toggle ---
document.getElementById("help-btn").onclick=function(e){
  e.stopPropagation();
  var h=document.getElementById("help");
  h.style.display=h.style.display==="block"?"none":"block";
};

// --- Virtual Keyboard Toggle ---
var vkb=document.getElementById("vkb");
var kbBtn=document.getElementById("kb-btn");
var kbOn=false;

kbBtn.onclick=function(e){
  e.stopPropagation();
  kbOn=!kbOn;
  vkb.style.display=kbOn?"block":"none";
};

// --- Send keys directly to Apple II I/O ---
// (Synthetic KeyboardEvents don't carry keyCode properly on mobile,
//  so we bypass the event system and talk to the emulator directly)

// Arrow keys send text adventure commands (type + RETURN) instead of raw cursor codes
// This makes arrows useful for text adventures like Mystery House, Softporn, etc.
var ARROW_COMMANDS={
  "ArrowUp":"GO NORTH","ArrowDown":"GO SOUTH",
  "ArrowLeft":"GO WEST","ArrowRight":"GO EAST"
};

function sendCommand(cmd){
  try{
    var a2=window.Apple2&&window.Apple2.apple2;if(!a2)return;
    var io=a2.getIO();if(!io)return;
    for(var i=0;i<cmd.length;i++){io.keyDown(cmd.charCodeAt(i));io.keyUp()}
    io.keyDown(13);io.keyUp(); // RETURN
  }catch(e){}
}

function codeToChar(code){
  // Letters → uppercase ASCII (Apple II standard)
  if(code.length===4&&code.startsWith("Key"))return code.charCodeAt(3);
  // Digits → ASCII 48-57
  if(code.length===6&&code.startsWith("Digit"))return code.charCodeAt(5);
  switch(code){
    case"Space":return 32;case"Enter":return 13;case"Backspace":return 127;
    case"Escape":return 27;
    default:return-1;
  }
}
function fireKey(code,type){
  try{
    // Arrow keys → send adventure commands
    if(type==="keydown"&&ARROW_COMMANDS[code]){sendCommand(ARROW_COMMANDS[code]);return}
    var a2=window.Apple2&&window.Apple2.apple2;if(!a2)return;
    var io=a2.getIO();if(!io)return;
    if(type==="keydown"){var c=codeToChar(code);if(c>=0)io.keyDown(c)}
    else io.keyUp();
  }catch(e){}
}

// --- Touch & mouse handling ---
vkb.querySelectorAll("button").forEach(function(btn){
  var code=btn.dataset.c;
  function down(e){e.preventDefault();e.stopPropagation();btn.classList.add("on");fireKey(code,"keydown")}
  function up(e){e.preventDefault();e.stopPropagation();btn.classList.remove("on");fireKey(code,"keyup")}
  btn.addEventListener("touchstart",down,{passive:false});
  btn.addEventListener("touchend",up,{passive:false});
  btn.addEventListener("touchcancel",up,{passive:false});
  btn.addEventListener("mousedown",down);
  btn.addEventListener("mouseup",up);
  btn.addEventListener("mouseleave",up);
});

// Prevent zoom
document.addEventListener("dblclick",function(e){e.preventDefault()});
document.addEventListener("gesturestart",function(e){e.preventDefault()});

// Auto-focus canvas
window.addEventListener("load",function(){
  setTimeout(function(){document.getElementById("screen").focus()},500);
});

// Auto-boot from disk: send PR#6 command after emulator starts
// (The embedded ROM doesn't auto-boot; we simulate typing PR#6 + RETURN)
(function autoBoot(){
  var bootInterval=setInterval(function(){
    try{
      var a2=window.Apple2&&window.Apple2.apple2;
      if(a2&&a2.isRunning()){
        var io=a2.getIO();
        var cmd="PR#6\\r";
        
        for(var i=0;i<cmd.length;i++){
          io.keyDown(cmd.charCodeAt(i));
          io.keyUp();
        }
        clearInterval(bootInterval);
      }
    }catch(e){console.error("[A2DBG] Auto-boot error:",e)}
  },200);
  // Safety timeout: stop trying after 10s
  setTimeout(function(){clearInterval(bootInterval)},10000);
})();
</script>
</body>
</html>'''
    
    # Build ROM chunks inline scripts
    rom_chunks_html = ''
    for chunk_id, chunk_js in rom_chunks:
        rom_chunks_html += f'<script>{chunk_js}</script>\n'
    
    # Replace placeholders
    html = html.replace('__TITLE__', title)
    html = html.replace('__APPLE2_CSS__', clean_css)
    html = html.replace('__KEYBOARD_HTML__', keyboard_html)
    html = html.replace('__HELP_KEYS__', help_keys_html)
    html = html.replace('__ROM_CHUNKS__', rom_chunks_html)
    html = html.replace('__DSK_B64__', dsk_b64)
    html = html.replace('__DSK_EXT__', ext)
    html = html.replace('__DSK_NAME__', title.replace('"', ''))
    html = html.replace('__APPLE2JS_BUNDLE__', bundle_js)
    
    return html

# ============================================================
#  Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='Pack an Apple II disk image into a self-contained HTML file')
    parser.add_argument('dsk', help='Path to disk image (.dsk, .do, .po, .nib, .woz)')
    parser.add_argument('--title', '-t', help='Game title (default: filename)')
    parser.add_argument('--model', '-m', default='apple2plus',
                       choices=['apple2', 'apple2plus', 'apple2e'],
                       help='Apple II model (default: apple2plus)')
    parser.add_argument('--extra-keys', '-k', nargs='+', help='Additional keys for virtual keyboard')
    parser.add_argument('--output', '-o', help='Output HTML file path')
    parser.add_argument('--bundle-js', help='Path to local apple2js bundle (skip download)')
    parser.add_argument('--css', help='Path to local apple2.css (skip download)')
    parser.add_argument('--analyze-only', '-a', action='store_true', help='Only analyze the disk')
    parser.add_argument('--cache-dir', default='.apple2js_cache', help='Directory to cache downloaded assets')
    args = parser.parse_args()
    
    if not os.path.isfile(args.dsk):
        print(f"Error: File not found: {args.dsk}")
        sys.exit(1)
    
    # Read disk
    print(f"🍎 Reading disk image: {args.dsk}")
    with open(args.dsk, 'rb') as f:
        dsk_data = f.read()
    print(f"   Size: {len(dsk_data)} bytes ({len(dsk_data)//1024} KB)")
    
    ext = os.path.splitext(args.dsk)[1].lstrip('.').lower()
    print(f"   Format: .{ext}")
    
    # Parse catalog (for .dsk files)
    if ext in ('dsk', 'do'):
        print(f"🔍 Parsing DOS 3.3 catalog...")
        entries = parse_dsk_catalog(dsk_data)
        if entries:
            print(f"   Found {len(entries)} files:")
            for e in entries:
                print(f"     {e['full']}")
        else:
            print("   No catalog entries found (may be ProDOS or copy-protected)")
    
    # Detect keys
    print(f"🎹 Analyzing keyboard usage...")
    keys = detect_keys_from_disk(dsk_data)
    print(f"   Detected patterns: {sorted(keys)}")
    
    layout = determine_keyboard_layout(keys, args.extra_keys)
    print(f"   Keyboard layout: arrows={layout['arrows']}, letters={len(layout['letters'])}, digits={len(layout['digits'])}")
    
    if args.analyze_only:
        print(f"\n✅ Analysis complete.")
        return
    
    # Title
    title = args.title or os.path.splitext(os.path.basename(args.dsk))[0]
    
    # Download/load assets
    print(f"📦 Loading apple2js assets...")
    
    if args.bundle_js:
        with open(args.bundle_js, 'r') as f:
            bundle_js = f.read()
        print(f"   Bundle: loaded from {args.bundle_js} ({len(bundle_js)//1024} KB)")
    else:
        cache_js = os.path.join(args.cache_dir, 'main2.bundle.js')
        bundle_js = download_asset(APPLE2JS_BUNDLE_URL, cache_js)
        print(f"   Bundle: {len(bundle_js)//1024} KB")
    
    if args.css:
        with open(args.css, 'r') as f:
            css = f.read()
        print(f"   CSS: loaded from {args.css}")
    else:
        cache_css = os.path.join(args.cache_dir, 'apple2.css')
        css = download_asset(APPLE2JS_CSS_URL, cache_css)
        print(f"   CSS: {len(css)//1024} KB")
    
    # Download format worker (for disk image parsing in a worker thread)
    cache_worker = os.path.join(args.cache_dir, 'format_worker.bundle.js')
    worker_js = download_asset(APPLE2JS_WORKER_URL, cache_worker)
    print(f"   Worker: {len(worker_js)//1024} KB")
    
    # Download ROM chunks for the selected model
    model = args.model
    sys_chunk_id, char_chunk_id = ROM_CHUNKS_FOR_MODEL.get(model, ROM_CHUNKS_FOR_MODEL['apple2plus'])
    print(f"📀 Loading ROM chunks for {model} (system={sys_chunk_id}, char={char_chunk_id})...")
    rom_chunks = []
    for chunk_id in [sys_chunk_id, char_chunk_id]:
        cache_chunk = os.path.join(args.cache_dir, f'{chunk_id}.bundle.js')
        chunk_js = download_asset(APPLE2JS_ROM_CHUNKS_URL + f'{chunk_id}.bundle.js', cache_chunk)
        rom_chunks.append((chunk_id, chunk_js))
        print(f"   Chunk {chunk_id}: {len(chunk_js)//1024} KB")
    
    # Generate HTML
    print(f"🏗️  Generating HTML...")
    html = generate_html(args.dsk, title, layout, bundle_js, css, rom_chunks, worker_js, args.model)
    
    # Output
    output_path = args.output or os.path.splitext(args.dsk)[0] + '.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    size_kb = os.path.getsize(output_path) / 1024
    print(f"\n✅ Done! Output: {output_path} ({size_kb:.0f} KB)")
    print(f"   🔌 100% offline — no internet needed")
    print(f"   📱 Mobile virtual keyboard included")
    print(f"   🍎 Emulated via apple2js (Apple ][+)")

if __name__ == '__main__':
    main()
