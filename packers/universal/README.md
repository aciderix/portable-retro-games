# 🎮 Universal Retro Game Packer

> Pack any ROM into a **single, self-contained, offline-playable HTML file** — supports **38 retro systems** via EmulatorJS.

## Overview

`pack_game.py` is the universal packer for the [portable-retro-games](https://github.com/aciderix/portable-retro-games) project. It replaces the need for per-platform packer scripts by leveraging **EmulatorJS** (RetroArch cores compiled to WebAssembly) to support dozens of retro platforms with a single tool.

### How It Works

```
ROM file (.nes, .sfc, .gb, ...) ──→ pack_game.py ──→ game.html (offline, standalone)
```

The packer:
1. Reads the ROM file and base64-encodes it
2. Downloads (and caches) the EmulatorJS engine (CSS + JS)
3. Downloads (and caches) the WASM core for the target system
4. Assembles everything into a single HTML file with:
   - Fetch/XHR interceptors to serve embedded data offline
   - Custom loading overlay with progress bar
   - Full EmulatorJS UI (save states, controls, shaders, etc.)

## Quick Start

```bash
# Basic usage — system auto-detected from extension
python3 pack_game.py mario.nes

# Specify a title
python3 pack_game.py zelda.sfc --title "The Legend of Zelda"

# Force a specific system (required for arcade/DOOM)
python3 pack_game.py sonic.bin --system genesis
python3 pack_game.py streetfighter2.zip --system cps1
python3 pack_game.py DOOM1.WAD --system doom

# Custom output path
python3 pack_game.py tetris.gb --output "Tetris (Game Boy).html"

# List all supported systems
python3 pack_game.py --list-systems

# Check offline status
python3 pack_game.py --offline-status

# Pre-download all cores for full offline use
python3 pack_game.py --prefetch-all
```

## Supported Systems (38)

### 🎮 Consoles — Nintendo

| System | Key | Core | Extensions | Notes |
|--------|-----|------|------------|-------|
| NES / Famicom | `nes` | fceumm | `.nes` | < 2 MB HTML |
| Super Nintendo | `snes` | snes9x | `.smc`, `.sfc` | < 3 MB |
| Game Boy | `gb` | gambatte | `.gb` | < 2 MB |
| Game Boy Color | `gbc` | gambatte | `.gbc` | < 2 MB |
| Game Boy Advance | `gba` | mgba | `.gba` | Larger ROMs (up to ~40 MB) |
| Nintendo 64 | `n64` | mupen64plus_next | `.n64`, `.z64`, `.v64` | Variable performance |
| Nintendo DS | `nds` | melonds | `.nds` | Dual screen, large ROMs |
| Virtual Boy | `vb` | beetle_vb | `.vb` | < 3 MB |

### 🎮 Consoles — Sega

| System | Key | Core | Extensions | Notes |
|--------|-----|------|------------|-------|
| Genesis / Mega Drive | `genesis` | genesis_plus_gx | `.md`, `.bin`, `.gen` | < 6 MB |
| Master System | `sms` | smsplus | `.sms` | < 2 MB |
| Game Gear | `gg` | genesis_plus_gx | `.gg` | < 2 MB |
| Sega 32X | `32x` | picodrive | `.32x` | < 6 MB |
| Sega CD | `segacd` | genesis_plus_gx | `.cue`, `.bin`, `.chd` | CD-size games |

### 🎮 Consoles — Atari

| System | Key | Core | Extensions | Notes |
|--------|-----|------|------------|-------|
| Atari 2600 | `atari2600` | stella2014 | `.a26`, `.bin` | < 1 MB |
| Atari 5200 | `atari5200` | a5200 | `.a52` | < 1 MB |
| Atari 7800 | `atari7800` | prosystem | `.a78` | < 1 MB |
| Atari Lynx | `lynx` | handy | `.lnx` | < 2 MB |
| Atari Jaguar | `jaguar` | virtualjaguar | `.j64`, `.jag` | May need tuning |

### 🎮 Consoles — Sony

| System | Key | Core | Extensions | Notes |
|--------|-----|------|------------|-------|
| PlayStation | `psx` | pcsx_rearmed | `.bin`, `.cue`, `.iso`, `.pbp` | May need BIOS |

### 🎮 Consoles — Others

| System | Key | Core | Extensions | Notes |
|--------|-----|------|------------|-------|
| PC Engine / TurboGrafx-16 | `pce` | mednafen_pce | `.pce` | < 4 MB |
| PC-FX | `pcfx` | mednafen_pcfx | `.cue`, `.ccd`, `.chd` | CD-based |
| Neo Geo Pocket / Color | `ngp` | mednafen_ngp | `.ngp`, `.ngc` | < 5 MB |
| WonderSwan / Color | `ws` | mednafen_wswan | `.ws`, `.wsc` | < 5 MB |
| ColecoVision | `coleco` | gearcoleco | `.col` | < 1 MB |

### 💻 Computers — Commodore

| System | Key | Core | Extensions | Notes |
|--------|-----|------|------------|-------|
| Commodore 64 | `c64` | vice_x64sc | `.d64`, `.t64`, `.prg`, `.crt` | Fully tested |
| Commodore 128 | `c128` | vice_x128 | `.d64`, `.d71`, `.d81`, `.prg` | — |
| VIC-20 | `vic20` | vice_xvic | `.d64`, `.prg`, `.crt`, `.60`, `.a0` | — |
| PET | `pet` | vice_xpet | `.d64`, `.prg`, `.tap` | — |
| Plus/4 | `plus4` | vice_xplus4 | `.d64`, `.prg`, `.tap`, `.bin` | — |
| Amiga | `amiga` | puae | `.adf`, `.adz`, `.dms`, `.ipf` | Also available as dedicated packer |

### 💻 Computers — Others

| System | Key | Core | Extensions | Notes |
|--------|-----|------|------------|-------|
| ZX Spectrum | `zxspectrum` | fuse | `.z80`, `.tap`, `.sna`, `.tzx` | Fully tested |
| ZX81 | `zx81` | 81 | `.p`, `.81` | — |
| Amstrad CPC | `cpc` | cap32 | `.dsk`, `.sna`, `.tap` | Also available as dedicated packer |

### 🕹️ Arcade & DOOM

| System | Key | Core | Extensions | Notes |
|--------|-----|------|------------|-------|
| CPS1 (Capcom) | `cps1` | fbalpha2012_cps1 | `.zip` | Requires `--system cps1` |
| CPS2 (Capcom) | `cps2` | fbalpha2012_cps2 | `.zip` | Requires `--system cps2` |
| FBNeo | `fbneo` | fbneo | `.zip` | Requires `--system fbneo` |
| MAME 2003+ | `mame` | mame2003_plus | `.zip` | Requires `--system mame` |
| DOOM | `doom` | prboom | `.wad` | Requires `--system doom` |

> ⚠️ **Arcade systems** require the `--system` flag because their ROM files are `.zip` which can't be auto-detected. Use the correct ROM set for each core (FBAlpha for CPS1/CPS2, FBNeo for FBNeo, MAME 2003 for MAME).

## CLI Reference

```
usage: pack_game.py [-h] [--system SYSTEM] [--title TITLE] [--output OUTPUT]
                    [--color COLOR] [--list-systems] [--offline-status]
                    [--prefetch-all]
                    [rom]

Universal Retro Game Packer — Pack any ROM into a standalone offline HTML file

positional arguments:
  rom                   Path to ROM or disk image file

options:
  -h, --help            Show this help message and exit
  --system, -s SYSTEM   Target system (auto-detected from extension if omitted)
  --title, -t TITLE     Game title (default: filename without extension)
  --output, -o OUTPUT   Output HTML file path (default: <rom_name>.html)
  --color, -c COLOR     EmulatorJS accent color (default: #FF4444)
  --list-systems        List all supported systems and exit
  --offline-status      Show which cores are cached locally
  --prefetch-all        Download all cores for full offline use
```

## Caching & Offline Mode

### Asset Resolution Priority

The packer resolves WASM cores and EmulatorJS assets in this order:

1. **`cores/` directory** — portable offline bundle next to the script (highest priority)
2. **`~/.emulatorjs_cache/`** — persistent local cache
3. **EmulatorJS CDN** — only if not cached (first use per system)

### Offline Bundle Structure

```
universal/
├── pack_game.py          # Main script (Python 3.10+, stdlib only)
├── cores/                # 31 WASM cores + EmulatorJS (~35 MB)
│   ├── emulator.min.js
│   ├── emulator.min.css
│   ├── fceumm-wasm.data        # NES
│   ├── snes9x-wasm.data        # SNES
│   ├── gambatte-wasm.data      # GB / GBC
│   ├── mgba-wasm.data          # GBA
│   ├── mupen64plus_next-wasm.data  # N64
│   ├── genesis_plus_gx-wasm.data   # Genesis / SMS / GG / Sega CD
│   ├── vice_x64sc-wasm.data    # C64
│   ├── puae-wasm.data          # Amiga
│   ├── cap32-wasm.data         # CPC
│   ├── prboom-wasm.data        # DOOM
│   └── ... (31 cores total)
├── cores.zip             # Pre-packaged bundle for easy distribution
└── README.md
```

### Quick Offline Setup

```bash
# Option 1: Unzip the included bundle
cd packers/universal/
unzip cores.zip
# ✅ Done! No internet needed from now on

# Option 2: Download all cores (requires internet once)
python3 pack_game.py --prefetch-all

# Check what's cached
python3 pack_game.py --offline-status
```

### Distributing the Offline Bundle

To share the packer as a fully offline tool:

```bash
zip -r packer_offline.zip universal/
# → ~35 MB, contains everything to generate HTML for 38 systems
```

## Architecture

The generated HTML uses the **fetch interceptor pattern** to serve all embedded data offline:

```
Browser requests core WASM  ──→  Intercepted ──→  Served from embedded base64
Browser requests ROM file   ──→  Intercepted ──→  Served from embedded base64
Browser requests metadata   ──→  Intercepted ──→  Served stub JSON `{}`
Other requests              ──→  Passed through to original fetch()
```

This means EmulatorJS "thinks" it's fetching from the CDN, but all data is served locally from the embedded base64 strings. The HTML file works 100% offline, forever.

## Dependencies

- **Python 3.10+** (no pip packages needed — uses only stdlib)
- **Internet connection** only for first download of each core (or use `cores/` / `cores.zip` for offline)

---

*Part of the [portable-retro-games](https://github.com/aciderix/portable-retro-games) project.*
