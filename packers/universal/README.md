# 🎮 Universal Retro Game Packer

> Pack any ROM into a **single, self-contained, offline-playable HTML file** — supports 25+ retro systems via EmulatorJS.

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

# Force a specific system
python3 pack_game.py sonic.bin --system genesis

# Custom output path
python3 pack_game.py tetris.gb --output "Tetris (Game Boy).html"

# List all supported systems
python3 pack_game.py --list-systems
```

## Supported Systems (25+)

### Tier 1 — Excellent Feasibility (< 5 MB HTML)

| System | Core | Extensions | HTML Size |
|--------|------|------------|-----------|
| NES / Famicom | fceumm | `.nes` | < 2 MB |
| Super Nintendo | snes9x | `.smc`, `.sfc` | < 3 MB |
| Game Boy | gambatte | `.gb` | < 2 MB |
| Game Boy Color | gambatte | `.gbc` | < 2 MB |
| Sega Genesis / Mega Drive | genesis_plus_gx | `.md`, `.bin`, `.gen` | < 6 MB |
| Sega Master System | smsplus | `.sms` | < 2 MB |
| Sega Game Gear | genesis_plus_gx | `.gg` | < 2 MB |
| Atari 2600 | stella2014 | `.a26`, `.bin` | < 1 MB |
| Atari 7800 | prosystem | `.a78` | < 1 MB |
| Atari 5200 | a5200 | `.a52` | < 1 MB |
| Atari Lynx | handy | `.lnx` | < 2 MB |
| ColecoVision | gearcoleco | `.col` | < 1 MB |
| Neo Geo Pocket / Color | mednafen_ngp | `.ngp`, `.ngc` | < 5 MB |
| WonderSwan / Color | mednafen_wswan | `.ws`, `.wsc` | < 5 MB |
| Virtual Boy | beetle_vb | `.vb` | < 3 MB |
| PC Engine / TurboGrafx-16 | mednafen_pce | `.pce` | < 4 MB |
| Sega 32X | picodrive | `.32x` | < 6 MB |

### Tier 2 — Feasible with Caveats

| System | Core | Extensions | Notes |
|--------|------|------------|-------|
| Game Boy Advance | mgba | `.gba` | Larger ROMs (< 40 MB HTML) |
| Nintendo 64 | mupen64plus_next | `.n64`, `.z64`, `.v64` | Variable performance |
| Nintendo DS | melonds | `.nds` | Dual screen, large ROMs |
| PlayStation | pcsx_rearmed | `.bin`, `.cue`, `.iso`, `.pbp` | May need BIOS |
| Sega CD | genesis_plus_gx | `.cue`, `.bin`, `.chd` | CD-size games |

### Tier 3 — Retro Computers

| System | Core | Extensions |
|--------|------|------------|
| Commodore 64 | vice_x64sc | `.d64`, `.t64`, `.prg`, `.crt` |
| ZX Spectrum | fuse | `.z80`, `.tap`, `.sna`, `.tzx` |
| MSX / MSX2 | fmsx | `.rom`, `.dsk`, `.mx1`, `.mx2` |

## CLI Reference

```
usage: pack_game.py [-h] [--system SYSTEM] [--title TITLE] [--output OUTPUT]
                    [--color COLOR] [--list-systems]
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
```

## Caching

Downloaded EmulatorJS assets are cached in `.emulatorjs_cache/` next to the script:

```
packers/universal/
├── pack_game.py
└── .emulatorjs_cache/
    ├── emulator.min.css      # EmulatorJS styles (~25 KB)
    ├── emulator.min.js       # EmulatorJS engine (~416 KB)
    ├── fceumm-wasm.data      # NES core (~1 MB)
    ├── snes9x-wasm.data      # SNES core (~1 MB)
    ├── gambatte-wasm.data    # GB/GBC core (~944 KB)
    └── ...                   # Other cores cached on first use
```

First run for a new system requires internet to download the core (~1 MB). Subsequent runs are fully offline.

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
- **Internet connection** only for first download of each core

---

*Part of the [portable-retro-games](https://github.com/aciderix/portable-retro-games) project.*

## 🔌 Mode Offline

Le packer peut fonctionner **100% hors connexion** grâce au dossier `cores/` qui contient tous les émulateurs pré-téléchargés.

### Structure du bundle offline

```
universal/
├── pack_game.py          # Script principal (29 KB)
├── cores/                # 21 cores + EmulatorJS (~21 MB)
│   ├── emulator.min.js
│   ├── emulator.min.css
│   ├── fceumm-wasm.data     # NES
│   ├── snes9x-wasm.data     # SNES
│   ├── gambatte-wasm.data   # Game Boy / Color
│   ├── mgba-wasm.data       # GBA
│   └── ... (17 autres cores)
├── .emulatorjs_cache/    # Cache auto (même contenu, créé dynamiquement)
└── README.md
```

### Commandes offline

```bash
# Vérifier le statut offline
python3 pack_game.py --offline-status

# Pré-télécharger tous les cores (une seule fois, nécessite internet)
python3 pack_game.py --prefetch-all

# Ensuite, tout fonctionne sans internet
python3 pack_game.py mario.nes   # ✅ Utilise cores/ en local
```

### Priorité de résolution des assets

1. **`cores/`** (dossier à côté du script) — priorité maximale, mode offline garanti
2. **`.emulatorjs_cache/`** (cache auto) — rempli après le 1er téléchargement
3. **CDN EmulatorJS** (internet) — fallback si rien en local

### Distribuer le bundle offline

Pour partager le packer en mode 100% offline, il suffit de copier le dossier `universal/` complet :

```bash
zip -r packer_offline.zip universal/
# → ~21 MB, contient tout pour générer des HTML pour 24 systèmes
```
