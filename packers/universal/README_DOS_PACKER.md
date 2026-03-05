# DOS Game Packer

Creates a **self-contained offline HTML page** from a DOS game ZIP file.

No server needed — works from `file://` protocol, just double-click to play!

## Engine

**js-dos 6.22** (asyncify / mono-thread DOSBox 0.74)

- ✅ No `SharedArrayBuffer` required
- ✅ No COOP/COEP headers required
- ✅ Works 100% offline from `file://`
- ✅ Everything embedded in a single HTML file
- 📱 Virtual keyboard for mobile/touch devices

## Usage

```bash
# Basic — auto-detects executable
python3 pack_dos_game.py game.zip

# With title and explicit executable
python3 pack_dos_game.py game.zip --title "Prince of Persia" --exe PRINCE.EXE

# Custom DOSBox settings
python3 pack_dos_game.py game.zip --cycles max --memory 32 --sound sb16

# Adventure game layout (full keyboard)
python3 pack_dos_game.py game.zip --keyboard adventure

# Analyze ZIP contents only
python3 pack_dos_game.py game.zip --analyze-only
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--title`, `-t` | filename | Game title shown on screen |
| `--exe`, `-e` | auto-detect | Main executable (EXE/COM/BAT) |
| `--output`, `-o` | `<name>.html` | Output file path |
| `--cycles` | `auto` | CPU cycles: `auto`, `max`, or number |
| `--memory` | `16` | DOS memory in MB |
| `--sound` | `sb16` | Sound: sb16, sb1, sb2, sbpro1, sbpro2, none |
| `--keyboard`, `-k` | `default` | Virtual keyboard: default, minimal, arrows, adventure |
| `--extra-conf` | — | Extra DOSBox config (string or `@file`) |
| `--cache-dir` | `.jsdos_cache` | Cache dir for downloaded js-dos assets |
| `--analyze-only`, `-a` | — | Only analyze the ZIP, don't build |

## Keyboard Layouts

| Layout | Keys | Best for |
|--------|------|----------|
| `default` | Full QWERTY + arrows + F-keys | General use |
| `minimal` | Arrows + Enter + Space + Y/N | Simple arcade games |
| `arrows` | Arrows + F-keys + numbers + Y/N | Action games |
| `adventure` | Full QWERTY + numbers + all modifiers | Text adventures, RPGs |

## Input Format

The input is a **ZIP file** containing the DOS game files. The ZIP should contain:
- The main executable (`.EXE`, `.COM`, or `.BAT`)
- All required data files, libraries, etc.

The packer auto-detects the main executable by priority:
1. Known game executables (DOOM.EXE, PRINCE.EXE, etc.)
2. Common launcher names (GAME.EXE, PLAY.BAT, etc.)
3. First .EXE found, then .COM, then .BAT

## Output

A single `.html` file (~2.7 MB engine + game size in base64).

Typical sizes:
- Small game (Digger): ~2.8 MB
- Medium game (Prince of Persia): ~3.2 MB
- Large game (Doom shareware): ~4.5 MB

## How It Works

The packer embeds everything inline in the HTML:

1. **js-dos.js** (105 KB) — js-dos API library
2. **wdosbox.wasm.js** (1.7 MB → 2.3 MB base64) — DOSBox WebAssembly binary
3. **wdosbox.js** (185 KB) — Emscripten glue code
4. **Game ZIP** (variable) — Complete game data
5. **dosbox.conf** — Custom DOSBox configuration

At boot time:
1. Decode WASM from base64 → `WebAssembly.compile()`
2. Pre-set `exports.instantiateWasm` hook
3. Eval wdosbox.js → sets `exports.WDOSBOX`
4. `Dos(canvas)` finds WDOSBOX pre-loaded → **skips all XHR**
5. Game ZIP served via Blob URL → `fs.extract()`
6. DOSBox launches with custom config

## Dependencies

- Python 3.6+
- Internet connection (first run only, to download js-dos assets — cached after)

## Architecture

This packer follows the same pattern as the Apple II, CPC, and Amiga packers:
- Self-contained Python script
- Downloads emulator assets with caching
- Generates a single offline HTML file
- Includes virtual keyboard for mobile
- CLI interface with argparse
