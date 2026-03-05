# 🎮 ScummVM Game Packer

Creates a **self-contained offline HTML page** from a directory of adventure game files using ScummVM WASM.

No server needed — works from `file://` protocol, just double-click to play!

## Engine

**ScummVM WASM** (Asyncify / mono-thread) from [scummvm.kuendig.io](https://scummvm.kuendig.io)

- ✅ No `SharedArrayBuffer` required
- ✅ No COOP/COEP headers required
- ✅ Works 100% offline from `file://`
- ✅ Everything embedded in a single HTML file
- ✅ 115 engine plugins — supports ~500 classic adventure games
- ✅ Auto-detects game engine from file contents

## Prerequisites

- Python 3.6+
- No pip dependencies (Python stdlib only)
- ScummVM WASM assets (downloaded once via `download_scummvm_assets.py`)

## Quick Start

### Step 1: Download ScummVM WASM Assets

```bash
cd packers/scummvm

# Download all ScummVM WASM assets (~200 MB total)
python3 download_scummvm_assets.py

# Check download status
python3 download_scummvm_assets.py --status

# Download only engine plugins (if core files already present)
python3 download_scummvm_assets.py --plugins-only
```

Assets are saved to `docs/data/scummvm/` and include:
- `scummvm.wasm` — Core engine (~37 MB)
- `scummvm.js` — JS glue code (~9 MB)
- `plugins/` — 115 engine plugin `.so` files
- `data/` — Engine-specific data files (.dat, .cpt, .tbl, .zip)

### Step 2: Pack a Game

```bash
# Auto-detect engine from game files
python3 pack_scummvm_game.py ./my_game/

# Specify engine explicitly
python3 pack_scummvm_game.py ./my_game/ --engine scumm --title "Monkey Island"

# Custom output path
python3 pack_scummvm_game.py ./my_game/ -o monkey_island.html

# List all available engines
python3 pack_scummvm_game.py --list-engines
```

**Output:** A single `.html` file — open it in any browser 🎮

## Usage

```bash
python3 pack_scummvm_game.py <game_dir> [options]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--engine`, `-e` | auto-detect | ScummVM engine ID |
| `--title`, `-t` | directory name | Game title shown on loading screen |
| `--output`, `-o` | `<title>.html` | Output HTML file path |
| `--list-engines` | — | List all available engine plugins and exit |
| `--scummvm-dir` | `docs/data/scummvm` | Path to ScummVM WASM assets |

### Examples

```bash
# SCUMM games (LucasArts)
python3 pack_scummvm_game.py ./monkey_island/ --engine scumm --title "Monkey Island"
python3 pack_scummvm_game.py ./day_of_tentacle/ --engine scumm --title "Day of the Tentacle"
python3 pack_scummvm_game.py ./full_throttle/ --engine scumm --title "Full Throttle"

# Sierra SCI games
python3 pack_scummvm_game.py ./kings_quest/ --engine sci --title "King's Quest"
python3 pack_scummvm_game.py ./space_quest/ --engine sci --title "Space Quest"

# Sierra AGI games
python3 pack_scummvm_game.py ./kings_quest1/ --engine agi --title "King's Quest I"

# Beneath a Steel Sky (Sky engine)
python3 pack_scummvm_game.py ./bass/ --engine sky --title "Beneath a Steel Sky"

# Broken Sword
python3 pack_scummvm_game.py ./broken_sword/ --engine sword1 --title "Broken Sword"

# Legend of Kyrandia
python3 pack_scummvm_game.py ./kyrandia/ --engine kyra --title "Legend of Kyrandia"

# Flight of the Amazon Queen
python3 pack_scummvm_game.py ./fotaq/ --engine queen --title "Flight of the Amazon Queen"
```

## Supported Engines

The packer supports **115 ScummVM engine plugins**, covering approximately 500 classic adventure games. Some notable engines:

| Engine | Games | Examples |
|--------|-------|---------|
| **SCUMM** | LucasArts adventures | Monkey Island, Day of the Tentacle, Full Throttle, The Dig, Sam & Max |
| **SCI** | Sierra On-Line | King's Quest, Space Quest, Leisure Suit Larry, Quest for Glory, Police Quest |
| **AGI** | Sierra AGI-era games | King's Quest I-III, Space Quest I-II, Leisure Suit Larry I |
| **Kyra** | Westwood Studios | Legend of Kyrandia series |
| **Sky** | Revolution Software | Beneath a Steel Sky |
| **Sword1/2** | Revolution Software | Broken Sword: Shadow of the Templars, Broken Sword II |
| **AGOS** | Adventure Soft | Simon the Sorcerer 1 & 2, Feeble Files |
| **Groovie** | Trilobyte | The 7th Guest, The 11th Hour |
| **Mohawk** | Cyan Worlds | Myst, Riven |
| **Queen** | Interactive Binary Illusions | Flight of the Amazon Queen |
| **Gob** | Coktel Vision | Gobliiins, Gobliins 2, Goblins Quest 3 |
| **Tinsel** | Psygnosis | Discworld, Discworld II |
| **Saga** | Wyrmkeep Entertainment | Inherit the Earth, I Have No Mouth |
| **Sherlock** | Electronic Arts | Sherlock Holmes: The Case of the Serrated Scalpel |
| **Wintermute** | Dead:Code | Various indie adventure games |
| **AGS** | Adventure Game Studio | Community-made adventure games |

Use `--list-engines` to see all 115 available engines with their plugin sizes and data file requirements.

## How It Works

The packer creates a single HTML file that contains everything needed to run the game:

1. **ScummVM WASM core** — The full ScummVM engine compiled to WebAssembly (~37 MB → ~13 MB gzip)
2. **ScummVM JS glue** — Emscripten JavaScript glue code (~9 MB → ~2 MB gzip)
3. **Engine plugin** — The specific `.so` plugin for the game's engine (variable size)
4. **Engine data files** — Required support data (themes, engine-specific .dat files)
5. **Game files** — All game data files (gzip+base64 compressed)
6. **Boot code** — JavaScript that orchestrates loading and launching

All binary data is gzip-compressed and base64-encoded inline in the HTML.

### Boot Sequence

At load time, the HTML file:

1. Decompresses the WASM core using the browser's `DecompressionStream` API
2. Decompresses the engine plugin and data files
3. Decompresses all game files
4. Sets ScummVM arguments via `window.location.hash`
5. Installs a `fetch()` interceptor to serve all assets from memory
6. Configures the Emscripten `Module` with `preRun` hooks
7. Writes game files and plugin to Emscripten MEMFS (`/game/` and `/data/plugins/`)
8. Injects the ScummVM JS to start the engine
9. ScummVM auto-detects the game and launches it fullscreen

### Typical Output Sizes

| Game Type | Typical Size |
|-----------|-------------|
| Small adventure (AGI, text-based) | ~20–25 MB |
| Medium adventure (early SCUMM, SCI) | ~25–40 MB |
| Large adventure (late SCUMM, talkie) | ~50–200+ MB |

> **Note:** The ScummVM WASM core alone is ~13 MB (gzip compressed, ~18 MB base64). Game files add on top of that.

## File Structure

```
portable-retro-games/
├── docs/data/scummvm/          # ScummVM WASM assets (served via GitHub Pages)
│   ├── scummvm.wasm            # Core engine (~37 MB)
│   ├── scummvm.js              # JS glue code (~9 MB)
│   ├── plugins/                # 115 engine plugins
│   │   ├── libscumm.so
│   │   ├── libsci.so
│   │   ├── libagi.so
│   │   └── ...
│   └── data/                   # Engine support data files
│       ├── scummmodern.zip     # Default theme
│       ├── scummremastered.zip # Remastered theme
│       ├── sky.cpt             # Beneath a Steel Sky data
│       ├── kyra.dat            # Kyrandia data
│       └── ...
└── packers/scummvm/
    ├── pack_scummvm_game.py        # Main packer script
    ├── download_scummvm_assets.py  # Asset downloader
    └── README.md                   # This file
```

## Architecture

This packer follows the same pattern as the other packers in portable-retro-games:

- **Self-contained Python script** — no pip dependencies
- **Downloads emulator assets** with skip-if-cached logic
- **Generates a single offline HTML file** — works from `file://`
- **CLI interface** with argparse
- **Auto-detection** of game engine from file patterns

### Key Technical Details

- **Gzip + Base64 encoding** — All binary data is gzip-compressed (level 9) then base64-encoded for embedding in HTML
- **Fetch interceptor** — Replaces `window.fetch()` to serve WASM, plugins, data files, and `scummvm.ini` from memory
- **MEMFS (Emscripten)** — Game files and engine plugin are written to the Emscripten virtual filesystem in `preRun`
- **Dynamic plugins** — ScummVM WASM uses `dlopen()` to load engine `.so` files at runtime from `/data/plugins/`
- **Asyncify** — Uses Emscripten's Asyncify transform (mono-thread), so `SharedArrayBuffer` is NOT required
- **DecompressionStream API** — Uses the browser's native gzip decompression for fast unpacking

## Troubleshooting

### "Plugins directory not found"

Run `download_scummvm_assets.py` first to download the ScummVM WASM assets:

```bash
python3 download_scummvm_assets.py
```

### "Engine plugin not found"

The specified engine ID doesn't match any available plugin. Use `--list-engines` to see available engines:

```bash
python3 pack_scummvm_game.py --list-engines
```

### "Could not auto-detect engine"

The packer couldn't determine which engine to use from the game files. Specify the engine manually:

```bash
python3 pack_scummvm_game.py ./my_game/ --engine scumm
```

### Game doesn't start in browser

- Check the browser console (F12) for error messages
- Ensure all game files are present in the game directory
- Some games require specific data files — check the engine's requirements
- Try a modern browser (Chrome 80+, Firefox 78+, Safari 14+) — `DecompressionStream` API is required

### Large HTML file sizes

The WASM core alone is ~18 MB (base64). For games with large data files (talkies, CD-ROM games), the HTML can be 100+ MB. This is expected — everything is embedded for offline use.

## Source Credit

ScummVM WASM build from **[scummvm.kuendig.io](https://scummvm.kuendig.io)** by kuendig.io.

ScummVM is an open-source project: [scummvm.org](https://www.scummvm.org/)
