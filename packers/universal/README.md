# 🎮 Universal Retro Game Packer

> Pack any ROM into a **single, self-contained, offline-playable HTML file** — supports **41 retro systems** via EmulatorJS.

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

## Supported Systems (41)

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
| Commodore 64 | `c64` | vice_x64sc | `.d64`, `.t64`, `.prg`, `.crt` | `.d64` auto-extracted (see below) |
| Commodore 128 | `c128` | vice_x128 | `.d64`, `.d71`, `.d81`, `.prg` | — |
| VIC-20 | `vic20` | vice_xvic | `.d64`, `.prg`, `.crt`, `.60`, `.a0` | — |
| PET | `pet` | vice_xpet | `.d64`, `.prg`, `.tap` | — |
| Plus/4 | `plus4` | vice_xplus4 | `.d64`, `.prg`, `.tap`, `.bin` | — |
| Amiga | `amiga` | puae | `.adf`, `.adz`, `.dms`, `.ipf` | Also available as dedicated packer |

#### Commodore 64 — Automatic D64→PRG Extraction

The VICE WASM core cannot reliably load `.d64` disk images (True Drive Emulation hangs during `LOAD"*",8,1`). The packer automatically handles this:

1. **Detects `.d64` files** for C64/C128/VIC-20/PET/Plus4 systems
2. **Parses the D64 directory** (track 18, sector chain)
3. **Extracts the first PRG** program from the disk image
4. **Packs the PRG** instead — which loads instantly via direct memory injection

This is fully transparent to the user:

```bash
# These both work — D64 is auto-converted
python3 pack_game.py game.d64 --system c64      # → extracts PRG, packs it
python3 pack_game.py game.prg --system c64      # → packs directly
```

Other C64 formats work natively: `.prg`, `.crt`, `.t64`, `.nib`, `.tap`.

> ⚠️ If the D64 contains no PRG file, packing will fail with a clear error message.

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

### 🎮 Consoles — Other (continued)

| System | Key | Core | Extensions | Notes |
|--------|-----|------|------------|-------|
| 3DO | `3do` | opera | `.iso`, `.bin`, `.cue`, `.chd` | CD-based |
| Philips CD-i | `cdi` | same_cdi | `.chd`, `.iso` | CD-based |
| Sega Saturn | `saturn` | yabause | `.bin`, `.cue`, `.iso`, `.chd` | CD-based |

> ⚠️ **Arcade systems** require the `--system` flag because their ROM files are `.zip` which can't be auto-detected.

#### Arcade ROM Naming — Important!

Arcade ROMs **must** use their correct MAME romset filename (e.g. `dino.zip`, `sf2.zip`, `ssf2t.zip`). The emulator core identifies the game by the filename — a renamed ROM (e.g. `Cadillacs and Dinosaurs.zip`) will **not** work.

The packer passes the ROM filename directly to EmulatorJS via `EJS_gameUrl`, and the fetch interceptor serves the embedded data when the core requests it. This is why the original filename matters.

**Common romset names:**
| Game | CPS1 | CPS2 |
|------|------|------|
| Street Fighter II | `sf2.zip` | — |
| Super SF2 Turbo | — | `ssf2t.zip` |
| Cadillacs & Dinosaurs | `dino.zip` | — |
| Marvel vs Capcom | — | `mvsc.zip` |
| Hyper SF2 Anniversary | — | `hsf2.zip` |
| 1944: The Loop Master | — | `1944.zip` |

> 💡 Find correct romset names on [Myrient MAME ROMs](https://myrient.erista.me/files/MAME/ROMs%20(merged)/) or the [FBAlpha compatibility list](https://www.fbalpha.com/compatibility/).

### 🔄 Alternative Cores

Some systems have alternative cores available via `--core`:

| Core | System | Notes |
|------|--------|-------|
| `nestopia` | NES | Alternative to fceumm |
| `desmume` | NDS | Alternative to melonDS |
| `desmume2015` | NDS | Lighter alternative |
| `mame2003` | Arcade | Alternative to mame2003_plus |
| `mednafen_psx_hw` | PSX | Hardware-accelerated |
| `parallel_n64` | N64 | Alternative to mupen64plus_next |
| `vice_x64` | C64 | Lighter alternative to vice_x64sc |
| `crocods` | CPC | Alternative to cap32 |

```bash
# Use nestopia instead of fceumm for NES
python3 pack_game.py mario.nes --core nestopia

# Use parallel_n64 instead of mupen64plus
python3 pack_game.py mario64.z64 --core parallel_n64
```

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
  --core CORE_NAME      Use an alternative core (e.g., nestopia, desmume, parallel_n64)
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
├── cores/                # 92 core files (46 cores × normal + legacy) + 12 assets (~137 MB)
│   ├── emulator.min.js
│   ├── emulator.min.css
│   ├── fceumm-wasm.data        # NES (normal)
│   ├── fceumm-legacy-wasm.data # NES (legacy/WebGL1 fallback)
│   ├── snes9x-wasm.data        # SNES
│   ├── gambatte-wasm.data      # GB / GBC
│   ├── mgba-wasm.data          # GBA
│   ├── mupen64plus_next-wasm.data  # N64
│   ├── genesis_plus_gx-wasm.data   # Genesis / SMS / GG / Sega CD
│   ├── opera-wasm.data          # 3DO
│   ├── same_cdi-wasm.data       # Philips CD-i
│   ├── yabause-wasm.data        # Sega Saturn
│   ├── vice_x64sc-wasm.data    # C64
│   ├── puae-wasm.data          # Amiga
│   ├── cap32-wasm.data         # CPC
│   ├── prboom-wasm.data        # DOOM
│   ├── GameManager.js           # EJS src/ asset
│   ├── gamepad.js               # EJS src/ asset
│   ├── nipplejs.js              # EJS src/ asset
│   ├── shaders.js               # EJS src/ asset
│   ├── socket.io.min.js         # EJS src/ asset
│   ├── storage.js               # EJS src/ asset
│   ├── extract7z.js             # Compression lib
│   ├── extractzip.js            # Compression lib
│   ├── libunrar.js              # Compression lib
│   ├── libunrar.wasm            # Compression lib
│   └── ... (92 cores + 12 assets = 104 files total)
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
# → ~137 MB, contains everything to generate HTML for 41 systems
```

## Architecture

### 3-Layer Offline Interception

The generated HTML uses a **3-layer interception strategy** to serve all assets offline:

1. **EJS_paths API** — Redirects EmulatorJS src/ scripts to embedded base64 blobs
2. **MutationObserver** — Intercepts dynamically injected `<script>` tags before they load from CDN
3. **Fetch/XHR override** — Catches all remaining network requests for cores, compression libs, and metadata

Additionally:
- **Dual core embedding**: Both normal and legacy WASM cores are embedded (browser selects based on WebGL2 support)
- **EJS_threads = false**: Disables threading (SharedArrayBuffer is unavailable in local `file://` contexts)
- **12 extra assets**: src/ scripts + compression libraries embedded as base64

This means EmulatorJS "thinks" it's fetching from the CDN, but all data is served locally from the embedded base64 strings. The HTML file works 100% offline, forever.

## Known Issues & Limitations

| Issue | Details | Workaround |
|-------|---------|------------|
| Arcade ROM naming | ROMs must use MAME romset filenames | Rename to correct romset name (e.g. `dino.zip`) |
| D64 with no PRG | Packer fails if the disk image has no loadable program | Use a different ROM format (`.prg`, `.tap`) |
| D64 multi-program | Only the first PRG is extracted from D64 | Extract the desired PRG manually |
| Amiga | Not fully tested with the universal packer | Use the dedicated Amiga packer as fallback |
| Some ROMs (32X, VB) | Knuckles' Chaotix (32X) and Mario's Tennis (VB) don't work | ROM-specific compatibility issue, try alternative dumps |

## Test Results

Tested with **26 games across 13 systems** — **23/26 working (88%)**:

| System | Games Tested | Status |
|--------|-------------|--------|
| Master System | 2 | ✅ All working |
| Game Gear | 2 | ✅ All working |
| Sega 32X | 2 | ⚠️ 1/2 (Knuckles' Chaotix fails) |
| Atari 7800 | 2 | ✅ All working |
| Neo Geo Pocket | 2 | ✅ All working |
| WonderSwan | 2 | ✅ All working |
| Virtual Boy | 2 | ⚠️ 1/2 (Mario's Tennis fails) |
| Atari 5200 | 2 | ✅ All working |
| Atari Lynx | 1 | ✅ Working |
| Atari Jaguar | 1 | ✅ Working |
| ZX Spectrum | 2 | ✅ Working |
| C64 | 2 | ✅ Working (.nib native + .d64→prg) |
| CPS1 | 2 | ✅ Working (dino.zip + sf2.zip) |
| CPS2 | 2 | ✅ Working (ssf2t.zip + mvsc.zip) |

## Dependencies

- **Python 3.10+** (no pip packages needed — uses only stdlib)
- **Internet connection** only for first download of each core (or use `cores/` / `cores.zip` for offline)

## Changelog

### v2.1 (March 2025)

**Bug Fixes:**
- 🎯 **Arcade (CPS1/CPS2/FBNeo/MAME) fix** — ROM filename is now passed directly as `EJS_gameUrl` instead of a blob URL. Arcade cores identify games by filename; blob URLs were causing "unknown romset" errors.
- 💾 **C64 D64→PRG extraction** — `.d64` disk images are automatically parsed and the first PRG is extracted before packing. The VICE WASM core's True Drive Emulation cannot complete disk loads, but PRG files load instantly via direct memory injection.

**Impact:** Test success rate improved from 81% to 88% (21/26 → 23/26 games).

### v2.0

- Initial universal packer with 41-system support
- 3-layer offline interception (EJS_paths, MutationObserver, Fetch/XHR)
- Dual core embedding (normal + legacy WebGL1 fallback)
- Core caching and prefetch system

---

*Part of the [portable-retro-games](https://github.com/aciderix/portable-retro-games) project.*
