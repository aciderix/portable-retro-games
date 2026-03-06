#!/usr/bin/env python3
"""
MSX Game Packer — Creates self-contained offline HTML files from MSX game images.
Uses WebMSX (wmsx.js) to emulate MSX, MSX2, MSX2+, and turbo R machines in the browser.

Usage:
    python3 pack_msx_game.py game.rom
    python3 pack_msx_game.py game.dsk --machine MSX2P --preset SCCI
    python3 pack_msx_game.py game.cas --title "My Game" -o my_game.html
    python3 pack_msx_game.py game.mx2 --preset FMPAC

Supported file types:
    .rom, .mx1  → Cartridge slot 1    (default: MSX2+)
    .mx2        → Cartridge slot 1    (default: MSX2)
    .dsk        → Floppy disk drive A (default: MSX2+)
    .cas        → Cassette tape       (default: MSX1)
    .zip        → Auto-detect         (default: MSX2+)

Machine types:    MSX1, MSX2, MSX2P (MSX2+), MSXTR (turbo R)
Sound presets:    SCCI, SCC, FMPAC, MSXMUSIC, MEGARAM
"""

import argparse
import base64
import os
import sys

# ============================================================
#  File Type Definitions
# ============================================================
FILE_TYPES = {
    '.rom': {'media': 'CARTRIDGE1_URL', 'label': 'Cartridge',    'default_machine': 'MSX2P'},
    '.mx1': {'media': 'CARTRIDGE1_URL', 'label': 'Cartridge',    'default_machine': 'MSX2P'},
    '.mx2': {'media': 'CARTRIDGE1_URL', 'label': 'Cartridge',    'default_machine': 'MSX2'},
    '.dsk': {'media': 'DISKA_URL',      'label': 'Floppy Disk',  'default_machine': 'MSX2P'},
    '.cas': {'media': 'TAPE_URL',       'label': 'Cassette Tape', 'default_machine': 'MSX1'},
    '.zip': {'media': 'AUTODETECT_URL', 'label': 'Auto-detect',  'default_machine': 'MSX2P'},
}

VALID_MACHINES = ['MSX1', 'MSX2', 'MSX2P', 'MSXTR']

VALID_PRESETS = ['SCCI', 'SCC', 'FMPAC', 'MSXMUSIC', 'MEGARAM']

MACHINE_LABELS = {
    'MSX1':  'MSX',
    'MSX2':  'MSX2',
    'MSX2P': 'MSX2+',
    'MSXTR': 'MSX turbo R',
}

# ============================================================
#  HTML Template
# ============================================================
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>{TITLE} — MSX</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 100%; height: 100%; background: #000; overflow: hidden; }}
  #wmsx {{ text-align: center; margin: 0 auto; width: 100%; height: 100%; }}
  #wmsx-screen {{ box-shadow: 2px 2px 10px rgba(0,0,0,.7); }}
</style>
</head>
<body>
<div id="wmsx"><div id="wmsx-screen"></div></div>
<script>
{WMSX_JS_CONTENT}
</script>
<script>
WMSX.{MEDIA_PARAM} = "data:application/octet-stream;base64,{BASE64_DATA}";
WMSX.MACHINE = "{MACHINE}";
{PRESETS_LINE}WMSX.SCREEN_FULLSCREEN_MODE = -1;
WMSX.MEDIA_CHANGE_DISABLED = true;
WMSX.AUTO_START = true;
</script>
</body>
</html>'''

# Multi-disk template: disk swap bar + all disks embedded
HTML_TEMPLATE_MULTIDISK = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>{TITLE} — MSX</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 100%; height: 100%; background: #000; overflow: hidden; display: flex; flex-direction: column; }}
  #disk-bar {{ background: #222; padding: 6px 12px; display: flex; align-items: center; gap: 8px; flex-shrink: 0;
               font: 13px/1.4 system-ui, sans-serif; color: #ccc; overflow-x: auto; }}
  #disk-bar span {{ color: #33cc99; font-weight: bold; white-space: nowrap; }}
  #disk-bar button {{ background: #444; color: #fff; border: 1px solid #666; border-radius: 4px;
                      padding: 4px 10px; cursor: pointer; font-size: 12px; white-space: nowrap; }}
  #disk-bar button:hover {{ background: #555; }}
  #disk-bar button.active {{ background: #33cc99; color: #000; border-color: #33cc99; font-weight: bold; }}
  #wmsx {{ text-align: center; margin: 0 auto; width: 100%; flex: 1; min-height: 0; }}
  #wmsx-screen {{ box-shadow: 2px 2px 10px rgba(0,0,0,.7); }}
</style>
</head>
<body>
<div id="disk-bar">
  <span>💾 Drive A:</span>
  {DISK_BUTTONS}
</div>
<div id="wmsx"><div id="wmsx-screen"></div></div>
<script>
var DISK_IMAGES = [{DISK_ARRAY}];
var currentDisk = 0;
function swapDisk(idx) {{
  if (idx === currentDisk) return;
  currentDisk = idx;
  // Update button states
  document.querySelectorAll('#disk-bar button').forEach(function(b, i) {{
    b.classList.toggle('active', i === idx);
  }});
  // Convert base64 to binary and load via WMSX file loader
  var b64 = DISK_IMAGES[idx].data;
  var bin = atob(b64);
  var arr = new Uint8Array(bin.length);
  for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  var blob = new Blob([arr], {{type: 'application/octet-stream'}});
  var url = URL.createObjectURL(blob);
  WMSX.room.fileLoader.loadFromURL(url, {{media: 'diska'}});
  setTimeout(function() {{ URL.revokeObjectURL(url); }}, 3000);
}}
</script>
<script>
{WMSX_JS_CONTENT}
</script>
<script>
WMSX.DISKA_URL = "data:application/octet-stream;base64,{FIRST_DISK_B64}";
WMSX.MACHINE = "{MACHINE}";
{PRESETS_LINE}WMSX.SCREEN_FULLSCREEN_MODE = -1;
WMSX.MEDIA_CHANGE_DISABLED = true;
WMSX.AUTO_START = true;
</script>
</body>
</html>'''


# ============================================================
#  Engine Locator
# ============================================================
def find_engine(explicit_path=None):
    """Locate wmsx.js — checks explicit path, script dir, then repo layout."""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    candidates = []

    if explicit_path:
        candidates.append(explicit_path)

    candidates += [
        os.path.join(script_dir, 'wmsx.js'),
        os.path.join(script_dir, '..', 'docs', 'data', 'msx', 'wmsx.js'),
        os.path.join(os.getcwd(), 'wmsx.js'),
        os.path.join(os.getcwd(), 'data', 'msx', 'wmsx.js'),
        os.path.join(os.getcwd(), 'docs', 'data', 'msx', 'wmsx.js'),
    ]

    for path in candidates:
        resolved = os.path.abspath(path)
        if os.path.isfile(resolved):
            return resolved

    return None


# ============================================================
#  Title Derivation
# ============================================================
def derive_title(filepath):
    """Derive a human-friendly title from a filename.

    Strips common rom-scene metadata: (year)(publisher), [tags], etc.
    Keeps original casing to preserve acronyms like MSX, SCC, RPG.
    Examples:
        "Antarctic Adventure - Konami (1984) [RC-701].rom" → "Antarctic Adventure - Konami"
        "Mon Mon Monster (1989) GA-Yume - HOT-B [FRS Fix].rom" → "Mon Mon Monster"
        "Arkanoid (1986)(Taito).dsk" → "Arkanoid"
        "1789 - La Revolution (19xx)(Legend Software)(fr)(Disk 1 of 3).dsk" → "1789 - La Revolution"
    """
    import re
    name = os.path.splitext(os.path.basename(filepath))[0]
    # Cut at the first ( or [ — everything after is metadata
    match = re.match(r'^(.*?)\s*[\(\[]', name)
    if match:
        name = match.group(1)
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    # Remove trailing separator
    name = name.rstrip(' -')
    # Collapse multiple spaces
    name = re.sub(r'\s{2,}', ' ', name)
    return name.strip() or os.path.splitext(os.path.basename(filepath))[0]


# ============================================================
#  Packing Logic
# ============================================================
def pack_msx_game(game_path, output_path, machine, preset, title, engine_path):
    """Pack an MSX game file into a self-contained HTML file."""

    # ── Validate game file ──
    if not os.path.isfile(game_path):
        print(f"❌ Game file not found: {game_path}")
        sys.exit(1)

    ext = os.path.splitext(game_path)[1].lower()
    if ext not in FILE_TYPES:
        print(f"❌ Unsupported file type: '{ext}'")
        print(f"   Supported extensions: {', '.join(sorted(FILE_TYPES.keys()))}")
        sys.exit(1)

    file_info = FILE_TYPES[ext]
    media_param = file_info['media']
    media_label = file_info['label']

    # ── Determine machine ──
    if not machine:
        machine = file_info['default_machine']
    machine = machine.upper()

    if machine not in VALID_MACHINES:
        print(f"❌ Invalid machine: '{machine}'")
        print(f"   Valid machines: {', '.join(VALID_MACHINES)}")
        sys.exit(1)

    machine_label = MACHINE_LABELS[machine]

    # ── Validate preset ──
    if preset:
        preset = preset.upper()
        if preset not in VALID_PRESETS:
            print(f"❌ Invalid preset: '{preset}'")
            print(f"   Valid presets: {', '.join(VALID_PRESETS)}")
            sys.exit(1)

    # ── Derive title ──
    if not title:
        title = derive_title(game_path)

    # ── Find WebMSX engine ──
    engine_file = find_engine(engine_path)
    if not engine_file:
        print(f"❌ WebMSX engine (wmsx.js) not found!")
        print(f"   Searched in:")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"     • {os.path.join(script_dir, 'wmsx.js')}")
        print(f"     • {os.path.abspath(os.path.join(script_dir, '..', 'docs', 'data', 'msx', 'wmsx.js'))}")
        if engine_path:
            print(f"     • {os.path.abspath(engine_path)}")
        print(f"   Use --engine <path> to specify the location of wmsx.js")
        sys.exit(1)

    # ── Print summary ──
    print(f"\n{'='*60}")
    print(f"  🎮 MSX Game Packer")
    print(f"{'='*60}")
    print(f"  📄 Game file:  {os.path.basename(game_path)}")
    print(f"  🎯 Title:      {title}")
    print(f"  💾 Media type: {media_label} ({media_param})")
    print(f"  🖥️  Machine:    {machine_label} ({machine})")
    if preset:
        print(f"  🔊 Preset:     {preset}")
    print(f"  ⚙️  Engine:     {engine_file}")
    print()

    # ── Read and encode game file ──
    print(f"📦 Reading game file...")
    with open(game_path, 'rb') as f:
        game_data = f.read()
    game_b64 = base64.b64encode(game_data).decode('ascii')
    game_size_kb = len(game_data) / 1024
    print(f"   Game size: {game_size_kb:.0f} KB → Base64: {len(game_b64)} chars")

    # ── Read WebMSX engine ──
    print(f"📦 Reading WebMSX engine...")
    with open(engine_file, 'r', encoding='utf-8') as f:
        wmsx_js = f.read()
    engine_size_kb = len(wmsx_js) / 1024
    print(f"   Engine size: {engine_size_kb:.0f} KB")

    # ── Build presets line ──
    presets_line = ''
    if preset:
        presets_line = f'WMSX.PRESETS = "{preset}";\n'

    # ── Generate HTML ──
    print(f"\n🏗️  Generating HTML...")
    html = HTML_TEMPLATE.format(
        TITLE=title,
        MEDIA_PARAM=media_param,
        BASE64_DATA=game_b64,
        MACHINE=machine,
        PRESETS_LINE=presets_line,
        WMSX_JS_CONTENT=wmsx_js,
    )

    # ── Determine output path ──
    if not output_path:
        game_name = os.path.splitext(os.path.basename(game_path))[0]
        output_path = game_name + '_msx.html'

    # ── Write output ──
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(output_path) / 1024
    size_mb = size_kb / 1024

    print(f"\n{'='*60}")
    print(f"  ✅ Done! Output: {output_path}")
    print(f"  📦 Size: {size_mb:.1f} MB ({size_kb:.0f} KB)")
    print(f"  🖥️  Machine: {machine_label} ({machine})")
    if preset:
        print(f"  🔊 Preset: {preset}")
    print(f"  🎯 Title: {title}")
    print(f"  🔌 100% offline — no internet needed")
    print(f"  🌐 Open in any modern browser")
    print(f"{'='*60}\n")


def pack_msx_multidisk(disk_paths, output_path, machine, preset, title, engine_path):
    """Pack multiple DSK files into a multi-disk HTML file with disk swap UI."""

    # ── Validate all disk files ──
    for dp in disk_paths:
        if not os.path.isfile(dp):
            print(f"❌ Disk file not found: {dp}")
            sys.exit(1)
        ext = os.path.splitext(dp)[1].lower()
        if ext != '.dsk':
            print(f"❌ Multi-disk mode only supports .dsk files, got: '{ext}' ({dp})")
            sys.exit(1)

    # ── Determine machine ──
    if not machine:
        machine = 'MSX2P'
    machine = machine.upper()
    if machine not in VALID_MACHINES:
        print(f"❌ Invalid machine: '{machine}'")
        sys.exit(1)
    machine_label = MACHINE_LABELS[machine]

    # ── Validate preset ──
    if preset:
        preset = preset.upper()
        if preset not in VALID_PRESETS:
            print(f"❌ Invalid preset: '{preset}'")
            sys.exit(1)

    # ── Derive title ──
    if not title:
        title = derive_title(disk_paths[0])

    # ── Find WebMSX engine ──
    engine_file = find_engine(engine_path)
    if not engine_file:
        print(f"❌ WebMSX engine (wmsx.js) not found!")
        print(f"   Use --engine <path> to specify the location of wmsx.js")
        sys.exit(1)

    # ── Print summary ──
    print(f"\n{'='*60}")
    print(f"  🎮 MSX Multi-Disk Packer")
    print(f"{'='*60}")
    print(f"  🎯 Title:      {title}")
    print(f"  💾 Disks:      {len(disk_paths)}")
    for i, dp in enumerate(disk_paths):
        size_kb = os.path.getsize(dp) / 1024
        print(f"       Disk {i+1}: {os.path.basename(dp)} ({size_kb:.0f} KB)")
    print(f"  🖥️  Machine:    {machine_label} ({machine})")
    if preset:
        print(f"  🔊 Preset:     {preset}")
    print(f"  ⚙️  Engine:     {engine_file}")
    print()

    # ── Read and encode all disks ──
    print(f"📦 Reading {len(disk_paths)} disk images...")
    disks_b64 = []
    disk_labels = []
    for i, dp in enumerate(disk_paths):
        with open(dp, 'rb') as f:
            data = f.read()
        b64 = base64.b64encode(data).decode('ascii')
        disks_b64.append(b64)
        label = os.path.basename(dp)
        # Try to extract "Disk X of Y" from filename
        import re
        m = re.search(r'Disk\s*(\d+)', label, re.IGNORECASE)
        disk_labels.append(f"Disk {m.group(1)}" if m else f"Disk {i+1}")
        print(f"   Disk {i+1}: {len(data)/1024:.0f} KB → {len(b64)} b64 chars")

    # ── Read WebMSX engine ──
    print(f"📦 Reading WebMSX engine...")
    with open(engine_file, 'r', encoding='utf-8') as f:
        wmsx_js = f.read()
    print(f"   Engine size: {len(wmsx_js)/1024:.0f} KB")

    # ── Build presets line ──
    presets_line = ''
    if preset:
        presets_line = f'WMSX.PRESETS = "{preset}";\n'

    # ── Build disk buttons HTML ──
    buttons = []
    for i, label in enumerate(disk_labels):
        active = ' class="active"' if i == 0 else ''
        buttons.append(f'<button{active} onclick="swapDisk({i})">{label}</button>')
    disk_buttons = '\n  '.join(buttons)

    # ── Build disk array JSON ──
    disk_entries = []
    for i, (b64, label) in enumerate(zip(disks_b64, disk_labels)):
        disk_entries.append(f'{{"name":"{label}","data":"{b64}"}}')
    disk_array = ',\n'.join(disk_entries)

    # ── Generate HTML ──
    print(f"\n🏗️  Generating multi-disk HTML...")
    html = HTML_TEMPLATE_MULTIDISK.format(
        TITLE=title,
        FIRST_DISK_B64=disks_b64[0],
        DISK_BUTTONS=disk_buttons,
        DISK_ARRAY=disk_array,
        MACHINE=machine,
        PRESETS_LINE=presets_line,
        WMSX_JS_CONTENT=wmsx_js,
    )

    # ── Determine output path ──
    if not output_path:
        game_name = os.path.splitext(os.path.basename(disk_paths[0]))[0]
        output_path = game_name + '_msx.html'

    # ── Write output ──
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(output_path) / 1024
    size_mb = size_kb / 1024

    print(f"\n{'='*60}")
    print(f"  ✅ Done! Output: {output_path}")
    print(f"  📦 Size: {size_mb:.1f} MB ({size_kb:.0f} KB)")
    print(f"  💾 Disks: {len(disk_paths)} (swap via top bar)")
    print(f"  🖥️  Machine: {machine_label} ({machine})")
    if preset:
        print(f"  🔊 Preset: {preset}")
    print(f"  🎯 Title: {title}")
    print(f"  🔌 100% offline — no internet needed")
    print(f"  🌐 Open in any modern browser")
    print(f"{'='*60}\n")


# ============================================================
#  CLI Entry Point
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description='Pack MSX game files into self-contained offline HTML files using WebMSX.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported file types:
    .rom, .mx1  → Cartridge (MSX2+ default)
    .mx2        → Cartridge (MSX2 default)
    .dsk        → Floppy disk (MSX2+ default)
    .cas        → Cassette tape (MSX1 default)
    .zip        → Auto-detect (MSX2+ default)

Machine types:  MSX1, MSX2, MSX2P (MSX2+), MSXTR (turbo R)
Presets:        SCCI, SCC, FMPAC, MSXMUSIC, MEGARAM

Multi-disk:
    %(prog)s disk1.dsk disk2.dsk disk3.dsk -o game.html

Examples:
    %(prog)s game.rom
    %(prog)s game.dsk --machine MSX2P --preset SCCI
    %(prog)s game.cas --title "My Game" -o my_game.html
    %(prog)s disk1.dsk disk2.dsk disk3.dsk --title "1789"
        """,
    )

    parser.add_argument('game', nargs='+', help='Path to MSX game file(s). Multiple .dsk files for multi-disk.')
    parser.add_argument('--output', '-o', help='Output HTML file path (default: <game>_msx.html)')
    parser.add_argument('--machine', '-m', choices=VALID_MACHINES,
                        help='MSX machine type (default: auto from file type)')
    parser.add_argument('--preset', '-p', choices=VALID_PRESETS,
                        help='Sound/extension preset (e.g. SCCI, FMPAC)')
    parser.add_argument('--title', '-t', help='Game title (default: derived from filename)')
    parser.add_argument('--engine', '-e', help='Path to wmsx.js engine file')

    args = parser.parse_args()

    # Route: multi-disk or single file
    if len(args.game) > 1:
        pack_msx_multidisk(
            disk_paths=args.game,
            output_path=args.output,
            machine=args.machine,
            preset=args.preset,
            title=args.title,
            engine_path=args.engine,
        )
    else:
        pack_msx_game(
            game_path=args.game[0],
            output_path=args.output,
            machine=args.machine,
            preset=args.preset,
            title=args.title,
            engine_path=args.engine,
        )


if __name__ == '__main__':
    main()
