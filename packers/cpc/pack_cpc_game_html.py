#!/usr/bin/env python3
"""
CPC Game Packer — Creates a self-contained offline HTML page from an Amstrad CPC DSK file.
Embeds RVMPlayer emulator + DSK file + virtual mobile keyboard.

Usage:
    python3 pack_cpc_game.py game.dsk
    python3 pack_cpc_game.py game.dsk --title "My Game" --run 'run"game'
    python3 pack_cpc_game.py game.dsk --extra-keys UP DOWN LEFT RIGHT
    python3 pack_cpc_game.py game.dsk --analyze-only
"""

import argparse, base64, os, re, struct, sys, urllib.request

# ============================================================
#  DSK Parser
# ============================================================
def parse_dsk(data):
    """Parse a DSK/EDSK file and return catalog entries and raw sectors."""
    header = data[:256]
    sig = header[:34].decode('ascii', errors='replace')
    is_extended = 'EXTENDED' in sig.upper()
    
    num_tracks = header[48]
    num_sides = header[49]
    
    entries = []
    sectors_data = {}
    
    offset = 256
    for t in range(num_tracks):
        for s in range(num_sides):
            if offset + 256 > len(data):
                break
            track_header = data[offset:offset+256]
            track_sig = track_header[:12].decode('ascii', errors='replace')
            if 'Track' not in track_sig:
                break
            
            num_sectors = track_header[21]
            sector_size_default = 128 << track_header[20] if track_header[20] > 0 else 512
            
            sect_offset = offset + 256
            for si in range(num_sectors):
                info_offset = 24 + si * 8
                sect_track = track_header[info_offset]
                sect_side = track_header[info_offset + 1]
                sect_id = track_header[info_offset + 2]
                sect_size_code = track_header[info_offset + 3]
                
                if is_extended:
                    actual_size = track_header[info_offset + 6] | (track_header[info_offset + 7] << 8)
                else:
                    actual_size = 128 << sect_size_code if sect_size_code > 0 else sector_size_default
                
                if sect_offset + actual_size <= len(data):
                    sectors_data[(t, s, sect_id)] = data[sect_offset:sect_offset + actual_size]
                sect_offset += actual_size
            
            if is_extended:
                track_size_entry = header[52 + t * num_sides + s]
                offset += track_size_entry * 256
            else:
                track_size = struct.unpack_from('<H', header, 50)[0]
                offset += track_size
    
    # Parse AMSDOS directory (track 0, sectors 0xC1-0xC4)
    dir_data = b''
    for sect_id in [0xC1, 0xC2, 0xC3, 0xC4]:
        key = (0, 0, sect_id)
        if key in sectors_data:
            dir_data += sectors_data[key]
    
    for i in range(0, len(dir_data), 32):
        entry = dir_data[i:i+32]
        if len(entry) < 32 or entry[0] == 0xE5:
            continue
        user = entry[0]
        name = entry[1:9].decode('ascii', errors='replace').strip()
        ext = bytes([b & 0x7F for b in entry[9:12]]).decode('ascii', errors='replace').strip()
        entries.append({'user': user, 'name': name, 'ext': ext, 'full': f"{name}.{ext}" if ext else name})
    
    return entries, sectors_data

# ============================================================
#  Key Detection from BASIC/Binary analysis
# ============================================================
CPC_FIRMWARE_KEY_CALLS = {
    0xBB09: 'KM_WAIT_CHAR',    # Wait for keypress
    0xBB06: 'KM_READ_CHAR',    # Read char (non-blocking)
    0xBB0C: 'KM_READ_KEY',     # Read key
    0xBB18: 'KM_WAIT_KEY',     # Wait for key
    0xBB1B: 'KM_TEST_KEY',     # Test specific key
}

BASIC_KEY_PATTERNS = {
    'INKEY$': ['any_key'],
    'INKEY(': ['specific_key'],
    'INPUT': ['alphanumeric', 'ENTER'],
    'INPUT$': ['any_key'],
}

def detect_keys_from_basic(text):
    """Detect keys used from BASIC text."""
    keys = set()
    
    # INKEY$ usage
    if 'INKEY$' in text:
        keys.add('FULL_KEYBOARD')
        # Look for comparisons: IF INKEY$="X"
        for m in re.finditer(r'INKEY\$\s*=\s*"(.)"', text):
            keys.add(m.group(1).upper())
    
    # INKEY(n) - specific key codes
    for m in re.finditer(r'INKEY\((\d+)\)', text):
        code = int(m.group(1))
        keys.add(f'INKEY_{code}')
    
    # INPUT - needs letters, numbers, enter
    if 'INPUT' in text:
        keys.add('ENTER')
        keys.add('ALPHANUMERIC')
    
    # JOY(0)/JOY(1) - joystick (arrow keys)
    if re.search(r'JOY\s*\(', text):
        keys.update(['UP', 'DOWN', 'LEFT', 'RIGHT', 'SPACE'])
    
    # Direct key references
    for m in re.finditer(r'CHR\$\((\d+)\)', text):
        code = int(m.group(1))
        if 32 <= code <= 126:
            keys.add(chr(code).upper())
    
    return keys

def detect_keys_from_binary(data):
    """Detect key usage from binary data by looking for firmware calls."""
    keys = set()
    has_key_scan = False
    
    for i in range(len(data) - 2):
        # CALL nn / JP nn / RST patterns
        if data[i] == 0xCD:  # CALL
            addr = data[i+1] | (data[i+2] << 8)
            if addr in CPC_FIRMWARE_KEY_CALLS:
                has_key_scan = True
                keys.add(CPC_FIRMWARE_KEY_CALLS[addr])
    
    if has_key_scan:
        keys.add('FULL_KEYBOARD')
    
    return keys

def determine_keyboard_layout(keys, extra_keys=None):
    """Determine the optimal virtual keyboard layout based on detected keys."""
    
    has_full = 'FULL_KEYBOARD' in keys or 'ALPHANUMERIC' in keys
    has_arrows = any(k in keys for k in ['UP', 'DOWN', 'LEFT', 'RIGHT'])
    specific_letters = {k for k in keys if len(k) == 1 and k.isalpha()}
    specific_digits = {k for k in keys if len(k) == 1 and k.isdigit()}
    
    # If nothing was detected (binary-only games), default to full keyboard
    # Most CPC games (especially French adventures) need text input
    nothing_detected = not has_full and not has_arrows and not specific_letters and not specific_digits and len(keys) == 0
    if nothing_detected:
        has_full = True
    
    layout = {
        'arrows': has_arrows or has_full,
        'letters': sorted(specific_letters) if specific_letters and not has_full else list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') if has_full else [],
        'digits': sorted(specific_digits) if specific_digits and not has_full else list('0123456789') if has_full else [],
        'special': [],
        'actions': ['SPACE', 'ENTER', 'BACKSPACE'],
    }
    
    if 'O' in keys or 'N' in keys:
        if not has_full:
            layout['letters'] = sorted(set(layout['letters']) | specific_letters)
    
    if extra_keys:
        for k in extra_keys:
            ku = k.upper()
            if ku in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                layout['arrows'] = True
            elif len(ku) == 1 and ku.isalpha():
                if ku not in layout['letters']:
                    layout['letters'].append(ku)
                    layout['letters'].sort()
            elif len(ku) == 1 and ku.isdigit():
                if ku not in layout['digits']:
                    layout['digits'].append(ku)
                    layout['digits'].sort()
    
    return layout

# ============================================================
#  RVMPlayer download
# ============================================================
RVM_CDN_URL = "https://cdn.rvmplayer.org/rvmplayer.cpc6128.0.1.1.min.js"

def download_rvmplayer():
    """Download RVMPlayer JS from CDN."""
    print(f"  Downloading RVMPlayer from {RVM_CDN_URL}...")
    req = urllib.request.Request(RVM_CDN_URL, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req).read().decode('utf-8')

# ============================================================
#  HTML Generation — Template matching hand-crafted quality
# ============================================================
# CPC key code mapping: label → data-c code (KeyboardEvent.code)
KEY_CODE_MAP = {
    'ArrowUp': 'ArrowUp', 'ArrowDown': 'ArrowDown',
    'ArrowLeft': 'ArrowLeft', 'ArrowRight': 'ArrowRight',
    'Space': 'Space', 'Enter': 'Enter', 'Backspace': 'Backspace',
    'Delete': 'Delete', 'Escape': 'Escape',
    # Letters — QWERTY codes (RVMPlayer maps internally)
    'A': 'KeyQ', 'B': 'KeyB', 'C': 'KeyC', 'D': 'KeyD',
    'E': 'KeyE', 'F': 'KeyF', 'G': 'KeyG', 'H': 'KeyH',
    'I': 'KeyI', 'J': 'KeyJ', 'K': 'KeyK', 'L': 'KeyL',
    'M': 'Semicolon', 'N': 'KeyN', 'O': 'KeyO', 'P': 'KeyP',
    'Q': 'KeyA', 'R': 'KeyR', 'S': 'KeyS', 'T': 'KeyT',
    'U': 'KeyU', 'V': 'KeyV', 'W': 'KeyZ', 'X': 'KeyX',
    'Y': 'KeyY', 'Z': 'KeyW',
    # Digits
    '0': 'Digit0', '1': 'Digit1', '2': 'Digit2', '3': 'Digit3',
    '4': 'Digit4', '5': 'Digit5', '6': 'Digit6', '7': 'Digit7',
    '8': 'Digit8', '9': 'Digit9',
}

def build_keyboard_html(layout):
    """Generate HTML for the virtual keyboard — matching hand-crafted quality.
    Uses data-c attribute, .r rows, .sp/.ent/.act classes."""
    rows = []
    
    # Row 1: Arrows + O/N/C (choice keys) + Space + Enter
    row1 = []
    if layout['arrows']:
        row1.extend([
            ('↑', 'ArrowUp', ''),
            ('↓', 'ArrowDown', ''),
            ('←', 'ArrowLeft', ''),
            ('→', 'ArrowRight', ''),
        ])
    
    # Add common choice/action letters in row 1 if they exist
    choice_keys = ['O', 'N', 'C']
    row1_letters = []
    remaining_letters = list(layout['letters'])
    for ck in choice_keys:
        if ck in remaining_letters:
            row1_letters.append((ck, ck, 'act'))
            remaining_letters.remove(ck)
    row1.extend(row1_letters)
    
    row1.append(('ESPACE', 'Space', 'sp'))
    row1.append(('ENTRÉE', 'Enter', 'ent'))
    rows.append(row1)
    
    # Row 2: Action letters (game commands)
    if remaining_letters:
        row2 = []
        for l in remaining_letters:
            row2.append((l, l, 'act'))
        rows.append(row2)
    
    # Row 3: Digits + Backspace
    if layout['digits']:
        row3 = [(d, d, '') for d in layout['digits']]
        row3.append(('⌫', 'Backspace', ''))
        rows.append(row3)
    else:
        # Always add backspace even without digits
        rows.append([('⌫', 'Backspace', '')])
    
    # Build HTML with .r rows and data-c attributes
    html_parts = []
    for row in rows:
        btns = ''
        for label, keyname, css_class in row:
            code = KEY_CODE_MAP.get(keyname, keyname)
            cls = f' class="{css_class}"' if css_class else ''
            btns += f'<button data-c="{code}"{cls}>{label}</button>'
        html_parts.append(f'  <div class="r">{btns}</div>')
    
    return '\n'.join(html_parts)

def generate_html(dsk_path, title, run_command, warp_seconds, layout, rvm_js):
    """Generate the complete self-contained HTML — matching hand-crafted quality.
    Identical CSS, HTML structure, JS event handling to the reference version."""
    
    # Read and encode DSK
    with open(dsk_path, 'rb') as f:
        dsk_data = f.read()
    dsk_b64 = base64.b64encode(dsk_data).decode()
    
    keyboard_html = build_keyboard_html(layout)
    
    # Build RVM command
    if run_command:
        rvm_command = run_command.replace("'", "\\'")
        if not rvm_command.endswith('\\n'):
            rvm_command += '\\n'
    else:
        rvm_command = ''
    
    warp_frames = warp_seconds * 50  # CPC runs at 50fps
    
    # Use placeholder-based template to avoid f-string escaping issues
    html_template = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>__TITLE__</title>
<style>
    *{margin:0;padding:0;box-sizing:border-box}
    html,body{width:100%;height:100%;background:#000;overflow:hidden;
      touch-action:manipulation;-webkit-user-select:none;user-select:none}

    #emu{position:absolute;top:0;left:0;width:100%;height:100%}

    /* Top-left floating buttons (small, discreet) */
    .float-btn{
      position:fixed;z-index:2000;
      width:32px;height:32px;border-radius:6px;
      background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);
      color:rgba(255,255,255,.45);font-size:16px;cursor:pointer;
      display:none;align-items:center;justify-content:center;
      -webkit-tap-highlight-color:transparent;
      transition:opacity .3s;
    }
    .float-btn:active{background:rgba(255,200,0,.3);color:#fc0}
    @media(pointer:coarse),(hover:none){.float-btn{display:flex}}
    #kb-btn{top:8px;left:8px}
    #help-btn{top:8px;left:48px}

    /* Virtual keyboard - compact game-specific */
    #vkb{
      display:none;position:fixed;bottom:0;left:0;right:0;z-index:1500;
      padding:4px 2px 6px;
      background:rgba(0,0,0,.85);
      backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);
      border-top:1px solid rgba(255,200,0,.2);
    }
    #vkb .r{display:flex;justify-content:center;gap:2px;margin-bottom:2px}
    #vkb .r:last-child{margin-bottom:0}
    #vkb button{
      font-family:system-ui,sans-serif;font-size:13px;font-weight:700;
      color:#ccc;background:rgba(255,255,255,.1);
      border:1px solid rgba(255,255,255,.15);border-radius:4px;
      min-width:26px;height:32px;padding:0 2px;
      cursor:pointer;-webkit-tap-highlight-color:transparent;
      flex:1;max-width:38px;
    }
    #vkb button:active,#vkb button.on{
      background:rgba(255,200,0,.4);border-color:#fc0;color:#fc0;
    }
    #vkb button.sp{max-width:120px;flex:3;font-size:11px}
    #vkb button.ent{max-width:72px;flex:2;background:rgba(255,200,0,.12);font-size:11px}
    #vkb button.act{color:#8cf;background:rgba(100,170,255,.12)}

    /* Help overlay */
    #help{
      display:none;position:fixed;top:0;left:0;right:0;bottom:0;z-index:3000;
      background:rgba(0,0,0,.92);
      backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
      overflow-y:auto;padding:16px;color:#ddd;
      font-family:system-ui,-apple-system,sans-serif;font-size:14px;line-height:1.5;
    }
    #help h2{color:#fc0;font-size:18px;margin:12px 0 6px;border-bottom:1px solid rgba(255,200,0,.3);padding-bottom:4px}
    #help h3{color:#8cf;font-size:15px;margin:10px 0 4px}
    #help .close-help{
      position:sticky;top:0;float:right;
      background:rgba(255,0,0,.2);border:1px solid rgba(255,0,0,.4);
      color:#f88;border-radius:6px;padding:4px 12px;cursor:pointer;font-size:14px;
      z-index:1;
    }
    #help kbd{
      background:rgba(255,200,0,.2);border:1px solid rgba(255,200,0,.4);
      border-radius:3px;padding:1px 5px;color:#fc0;font-family:monospace;font-size:13px;
    }
    #help table{border-collapse:collapse;width:100%;margin:6px 0}
    #help td,#help th{border:1px solid rgba(255,255,255,.15);padding:3px 8px;text-align:left}
    #help th{background:rgba(255,200,0,.1);color:#fc0}
    #help .tip{color:#8f8;font-style:italic}
</style>
</head>
<body>

<div id="emu"></div>
<button id="kb-btn" class="float-btn" aria-label="Clavier">⌨</button>
<button id="help-btn" class="float-btn" aria-label="Aide">?</button>

<!-- Help overlay -->
<div id="help">
  <button class="close-help" onclick="document.getElementById('help').style.display='none'">✕ Fermer</button>

  <h2>🎮 __TITLE__</h2>
  <p>Jeu Amstrad CPC émulé dans votre navigateur via RVMPlayer.</p>

  <h2>📋 Contrôles</h2>
  <p>Sur mobile, utilisez le clavier virtuel (bouton <kbd>⌨</kbd> en haut à gauche).<br>
  Sur ordinateur, utilisez votre clavier physique. Cliquez d'abord sur l'écran pour lui donner le focus.</p>

  <h3>Touches disponibles</h3>
  <table>
    <tr><th>Touche</th><th>Usage</th></tr>
__HELP_KEYS__
  </table>

  <p class="tip">💡 Si le jeu ne répond pas, cliquez sur l'écran de l'émulateur pour lui donner le focus.</p>
  <p style="margin-top:16px;color:#888;font-size:12px;text-align:center">Émulé via RVMPlayer — 100% hors-ligne</p>
</div>

<!-- Virtual Keyboard: compact, game-specific -->
<div id="vkb">
__KEYBOARD_HTML__
</div>

<script>__RVMPLAYER_JS__</script>
<script>
// Decode DSK from base64
const B=atob("__DSK_B64__");
const U=new Uint8Array(B.length);
for(let i=0;i<B.length;i++)U[i]=B.charCodeAt(i);
const dskUrl=URL.createObjectURL(new Blob([U],{type:"application/octet-stream"}));

// --- Emulator ---
const emu=document.getElementById("emu");
rvmPlayer_cpc6128(emu,{
  disk:{type:"dsk",url:dskUrl},
  command:'__RVM_COMMAND__',
  warpFrames:__WARP_FRAMES__,
  videoMode:"tv",
  pause:false,
  video:false
});

// --- Help toggle ---
document.getElementById("help-btn").onclick=function(e){
  e.stopPropagation();
  var h=document.getElementById("help");
  h.style.display=h.style.display==="block"?"none":"block";
};

// --- Virtual Keyboard Toggle ---
const vkb=document.getElementById("vkb");
const kbBtn=document.getElementById("kb-btn");
let kbOn=false;

kbBtn.onclick=function(e){
  e.stopPropagation();
  kbOn=!kbOn;
  vkb.style.display=kbOn?"block":"none";
};

// --- Send keys via window events (RVMPlayer listens on window) ---
function fireKey(code,type){
  const keyMap={
    Space:" ",Enter:"Enter",Backspace:"Backspace",
    ArrowUp:"ArrowUp",ArrowDown:"ArrowDown",
    ArrowLeft:"ArrowLeft",ArrowRight:"ArrowRight",
  };
  let key=keyMap[code]||"";
  if(code.startsWith("Key"))key=code[3].toLowerCase();
  if(code.startsWith("Digit"))key=code[5];
  if(code==="Semicolon")key="m";

  window.dispatchEvent(new KeyboardEvent(type,{
    code:code, key:key, bubbles:true, cancelable:true
  }));
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
</script>
</body>
</html>'''

    # Generate help keys table
    help_rows = []
    if layout['arrows']:
        help_rows.append('    <tr><td><kbd>↑</kbd><kbd>↓</kbd><kbd>←</kbd><kbd>→</kbd></td><td>Navigation / Déplacement</td></tr>')
    for l in layout['letters']:
        help_rows.append(f'    <tr><td><kbd>{l}</kbd></td><td>Commande {l}</td></tr>')
    if layout['digits']:
        help_rows.append(f'    <tr><td><kbd>0</kbd>-<kbd>9</kbd></td><td>Saisie numérique</td></tr>')
    help_rows.append('    <tr><td><kbd>ESPACE</kbd></td><td>Continuer / Action</td></tr>')
    help_rows.append('    <tr><td><kbd>ENTRÉE</kbd></td><td>Valider</td></tr>')
    help_rows.append('    <tr><td><kbd>⌫</kbd></td><td>Effacer</td></tr>')
    help_keys_html = '\n'.join(help_rows)

    # Replace all placeholders
    html = html_template
    html = html.replace('__TITLE__', title)
    html = html.replace('__KEYBOARD_HTML__', keyboard_html)
    html = html.replace('__HELP_KEYS__', help_keys_html)
    html = html.replace('__DSK_B64__', dsk_b64)
    html = html.replace('__RVM_COMMAND__', rvm_command)
    html = html.replace('__WARP_FRAMES__', str(warp_frames))
    html = html.replace('__RVMPLAYER_JS__', rvm_js)
    
    return html

# ============================================================
#  Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='Pack an Amstrad CPC DSK game into a self-contained HTML file')
    parser.add_argument('dsk', help='Path to the DSK file')
    parser.add_argument('--title', '-t', help='Game title (default: filename)')
    parser.add_argument('--run', '-r', help='RUN command (default: auto-detect from catalog)')
    parser.add_argument('--warp', '-w', type=int, default=20, help='Warp duration in seconds (default: 20)')
    parser.add_argument('--extra-keys', '-k', nargs='+', help='Additional keys to add to virtual keyboard')
    parser.add_argument('--output', '-o', help='Output HTML file path')
    parser.add_argument('--analyze-only', '-a', action='store_true', help='Only analyze the DSK, do not generate HTML')
    parser.add_argument('--rvm-js', help='Path to local RVMPlayer JS file (skip download)')
    args = parser.parse_args()
    
    if not os.path.isfile(args.dsk):
        print(f"Error: File not found: {args.dsk}")
        sys.exit(1)
    
    # Read DSK
    print(f"📀 Reading DSK: {args.dsk}")
    with open(args.dsk, 'rb') as f:
        dsk_data = f.read()
    print(f"   Size: {len(dsk_data)} bytes")
    
    # Parse DSK
    print(f"🔍 Parsing DSK...")
    entries, sectors = parse_dsk(dsk_data)
    print(f"   Found {len(entries)} catalog entries:")
    for e in entries:
        print(f"     {e['full']}")
    
    # Auto-detect RUN command
    run_cmd = args.run
    if not run_cmd:
        # Find the first entry that looks like a loader
        for e in entries:
            if e['ext'] in ['', 'BAS', 'bas', ' ']:
                run_cmd = f'run"{e["name"].lower()}'
                break
        if not run_cmd and entries:
            run_cmd = f'run"{entries[0]["name"].lower()}'
        if not run_cmd:
            run_cmd = 'cat'
        print(f"   Auto-detected RUN command: {run_cmd}")
    else:
        print(f"   RUN command: {run_cmd}")
    
    # Analyze keys
    print(f"🎹 Analyzing keyboard usage...")
    all_keys = set()
    
    for e in entries:
        if e['ext'] in ['BAS', 'bas', '', ' ']:
            # Try to find BASIC text in sectors
            pass
    
    # Scan all sector data for firmware calls and text patterns
    all_sector_data = b''
    for key, data in sectors.items():
        all_sector_data += data
    
    # Binary analysis
    bin_keys = detect_keys_from_binary(all_sector_data)
    all_keys.update(bin_keys)
    
    # Text pattern analysis
    try:
        text = all_sector_data.decode('ascii', errors='replace')
        basic_keys = detect_keys_from_basic(text)
        all_keys.update(basic_keys)
    except:
        pass
    
    print(f"   Detected key patterns: {sorted(all_keys)}")
    
    # Determine layout
    layout = determine_keyboard_layout(all_keys, args.extra_keys)
    print(f"   Keyboard layout:")
    print(f"     Arrows: {layout['arrows']}")
    print(f"     Letters: {' '.join(layout['letters'][:26])}{'...' if len(layout['letters'])>26 else ''}")
    print(f"     Digits: {' '.join(layout['digits'])}")
    
    if args.analyze_only:
        print(f"\n✅ Analysis complete.")
        return
    
    # Title
    title = args.title or os.path.splitext(os.path.basename(args.dsk))[0]
    
    # Download/load RVMPlayer
    print(f"📦 Loading RVMPlayer...")
    if args.rvm_js:
        with open(args.rvm_js, 'r') as f:
            rvm_js = f.read()
        print(f"   Loaded from {args.rvm_js}: {len(rvm_js)} chars")
    else:
        rvm_js = download_rvmplayer()
        print(f"   Downloaded: {len(rvm_js)} chars")
    
    # Generate HTML
    print(f"🏗️  Generating HTML...")
    html = generate_html(args.dsk, title, run_cmd, args.warp, layout, rvm_js)
    
    # Output
    output_path = args.output or os.path.splitext(args.dsk)[0] + '.html'
    with open(output_path, 'w') as f:
        f.write(html)
    
    size_kb = os.path.getsize(output_path) / 1024
    print(f"\n✅ Done! Output: {output_path} ({size_kb:.0f} KB)")
    print(f"   🔌 100% offline — no internet needed")
    print(f"   📱 Mobile virtual keyboard included")

if __name__ == '__main__':
    main()
