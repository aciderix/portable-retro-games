# 🕹️ portable-retro-games

### Play retro games instantly — each game is a single standalone HTML file, no install, no server, works offline in any browser forever

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Offline Ready](https://img.shields.io/badge/Offline-Ready-brightgreen?logo=wifi-off)](#)
[![Mobile Friendly](https://img.shields.io/badge/Mobile-Friendly-orange?logo=smartphone)](#)
[![Platforms](https://img.shields.io/badge/Platforms-42%20Systems-purple)](#supported-platforms)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Play%20Now!-ff6600?logo=netlify&logoColor=white)](https://jimmy-willburne.netlify.app/)
[![Web Packer](https://img.shields.io/badge/Web%20Packer-Try%20Online!-blueviolet?logo=html5&logoColor=white)](https://aciderix.github.io/portable-retro-games/pack_game_en.html)

---

<p align="center">
  <strong>🇬🇧 English</strong> ·
  <a href="#-résumé-en-français">🇫🇷 Français</a>
</p>

---

## 🤔 What is this?

**portable-retro-games** is a collection of Python scripts that package retro game ROMs and disk images into **self-contained, offline-playable HTML files**.

Each generated HTML file embeds:
- ✅ A full **browser-based emulator** (JavaScript / WebAssembly)
- ✅ The **game ROM or disk image** (base64-encoded)
- ✅ **Touch-friendly controls** with virtual keyboard/gamepad support
- ✅ **Zero external dependencies** — works offline, forever

> **One file. One game. Any browser. Any device. No internet needed.**

This means you can take a retro game file — from NES to N64, from Game Boy to Amiga, from Arcade to DOOM — run a single command, and get an HTML file that plays the game in Chrome, Firefox, or Safari — on desktop or mobile — with no server, no installation, no plugins.

### Why does this matter?

Retro games are disappearing. Hardware fails. Websites go offline. Flash died. Java applets are gone. **portable-retro-games** creates permanent, portable, self-contained game archives that will work as long as web browsers exist.

---

## 🖥️ Supported Platforms

### 🌐 Universal Packer — 42 Console, Computer & Arcade Systems

The **Universal Packer** (`packers/universal/pack_game.py`) supports **42 retro systems** with a single script, zero pip dependencies:

| Category | Systems |
|----------|---------|
| 🎮 **Nintendo** | NES, SNES, Game Boy, Game Boy Color, GBA, N64, Nintendo DS, Virtual Boy |
| 🎮 **Sega** | Genesis/Mega Drive, Master System, Game Gear, Sega 32X, Sega CD |
| 🎮 **Atari** | 2600, 5200, 7800, Lynx, Jaguar |
| 🎮 **Sony** | PlayStation |
| 🎮 **NEC** | PC Engine / TurboGrafx-16, PC-FX |
| 🎮 **SNK** | Neo Geo Pocket / Color |
| 🎮 **Bandai** | WonderSwan / Color |
| 🎮 **Coleco** | ColecoVision |
| 💻 **Commodore** | C64, C128, VIC-20, PET, Plus/4, Amiga |
| 💻 **PC / DOS** | MS-DOS (DOSBox) |
| 💻 **Sinclair** | ZX Spectrum, ZX81 |
| 💻 **Amstrad** | CPC |
| 🕹️ **Arcade** | CPS1, CPS2, FBNeo, MAME 2003+ |
| 🔫 **id Software** | DOOM (PrBoom) |
| 🎮 **Other** | 3DO, Philips CD-i, Sega Saturn |

> Powered by [EmulatorJS](https://emulatorjs.org/) — cores are auto-downloaded and cached locally. A `cores.zip` bundle is included for full offline use.

### 🔧 Platform-Specific Packers — Advanced Features

For these platforms, dedicated packers provide enhanced features like keyboard auto-detection, firmware analysis, and custom virtual keyboards:

| Platform | Packer Script | Emulator | Input Formats | Key Features |
|---|---|---|---|---|
| 🍎 **Apple II** | `pack_apple2_game_html.py` | [apple2js](https://github.com/whscullin/apple2js) | `.dsk`, `.do`, `.po`, `.nib`, `.woz` | Auto keyboard detection, DOS 3.3 catalog parsing, model selection (II/II+/IIe) |
| 💾 **Amstrad CPC** | `pack_cpc_game_html.py` | [RVMPlayer](https://github.com/nicl83/RVMPlayer) | `.dsk` (DSK/EDSK) | Z80 firmware call analysis, AZERTY→QWERTY mapping, warp-speed loading |
| 🐱 **Commodore Amiga** | `build_jimmy_willburne.py` | [vAmigaWeb](https://github.com/nicl83/vAmigaWeb) | `.adf` | WASM emulation, IndexedDB caching, full asset inlining, virtual joystick |

> 💡 **Note:** Amstrad CPC and Commodore Amiga are available in *both* the universal packer (convenience, one script) and as dedicated packers (superior emulation quality, custom keyboards, firmware analysis). Use the dedicated packers for the best experience.

---

## ⚡ Quick Start

### 🌐 No Install? Use the Web Packer!

Don't want to install Python? Use the **Web GUI** directly in your browser:

- 🇬🇧 [**Web Packer (English)**](https://aciderix.github.io/portable-retro-games/pack_game_en.html)
- 🇫🇷 [**Web Packer (Français)**](https://aciderix.github.io/portable-retro-games/pack_game_fr.html)

> Drop a ROM, pick your system, click Generate — get a standalone HTML file. No Python, no terminal, no install.

> 💡 The Web Packer includes a local mirror of all cores, so it works even if the EmulatorJS CDN goes offline.


### Prerequisites

```bash
python --version   # Python 3.12+ (all packers)
```

### 🌐 Universal Packer — Any Console Game (41 Systems)

```bash
cd packers/universal

# Pack any ROM — system is auto-detected from file extension
python3 pack_game.py SuperMario.nes
python3 pack_game.py Sonic.gen
python3 pack_game.py Pokemon.gba
python3 pack_game.py Mario64.z64
python3 pack_game.py DOOM.wad

# Pack arcade ROM (system must be specified)
python3 pack_game.py streetfighter2.zip --system cps1

# Custom title & output
python3 pack_game.py Zelda.sfc --title "Zelda - A Link to the Past" --output zelda.html

# List all supported systems & file extensions
python3 pack_game.py --list-systems

# Use an alternative core
python3 pack_game.py game.nes --core nestopia

# Check which cores are cached locally
python3 pack_game.py --offline-status

# Download ALL cores at once for full offline use
python3 pack_game.py --prefetch-all
```

**Output:** A single `.html` file — open it in any browser 🎮

> 💡 The first time you pack a game for a given system, the WASM core is downloaded from the EmulatorJS CDN and cached locally (`~/.emulatorjs_cache/`). All subsequent games for that system work **100% offline**. You can also place cores in a `cores/` folder next to the script or unzip the included `cores.zip` for fully portable offline use.

### 🍎 Apple II — Pack a Game

```bash
cd packers/apple2
pip install beautifulsoup4 requests

# Pack a .dsk disk image into a playable HTML file
python pack_apple2_game_html.py Karateka.dsk

# Specify Apple II model
python pack_apple2_game_html.py --model apple2e "Oregon Trail.dsk"

# The packer auto-detects if the game needs arrow keys, letters, or both
# and generates the appropriate virtual keyboard
```

**Output:** `Karateka.html` — open it in any browser 🎮

### 💾 Amstrad CPC — Pack a Game

```bash
cd packers/cpc
pip install beautifulsoup4 requests

# Pack a CPC DSK file
python pack_cpc_game_html.py Gryzor.dsk

# Enable warp-speed loading (fast-forward through tape/disk loading)
python pack_cpc_game_html.py --warp Gryzor.dsk

# The packer reads the DSK catalog, finds the boot program,
# analyzes BASIC/Z80 code for keyboard usage, and generates
# the perfect virtual keyboard layout
```

**Output:** `Gryzor.html` — 132 French CPC games already converted! 🇫🇷

### 🐱 Amiga — Build a Game

```bash
cd packers/amiga

# Build a standalone HTML from an ADF disk image
python build_jimmy_willburne.py

# Build with IndexedDB caching (faster reload)
python build_jimmy_willburne_cached.py

# The builder inlines EVERYTHING: WASM emulator, Kickstart ROM,
# game disks, JS, CSS, images, SVG sprites, and sounds
```

**Output:** A complete Amiga experience in a single HTML file 🚀

---

## 🎮 Live Demos — Try It Now!

**No install needed — click and play directly in your browser:**

| Game | Platform | Link |
|---|---|---|
| 🐱 **Jimmy Willburne** | Amiga | [▶️ Play Now](https://jimmy-willburne.netlify.app/) |
| 🐱 **Short Grey** | Amiga | [▶️ Play Now](https://short-grey.netlify.app/) |
| 🍎 **Softporn Adventure VF** | Apple II | [▶️ Play Now](https://softporn-adventure-vf.netlify.app/) |
| 🍎 **Le Dragon Gardien** | Apple II | [▶️ Play Now](https://le-dragon-gardien.netlify.app/) |
| 🍎 **Mystery House VF** | Apple II | [▶️ Play Now](https://mystery-house-vf.netlify.app/) |
| 💾 **1815** | Amstrad CPC | [▶️ Play Now](https://1815-cpc.netlify.app/) |
| 🌐 **Web Packer** | All 41 systems | [🇬🇧 English](https://aciderix.github.io/portable-retro-games/pack_game_en.html) · [🇫🇷 Français](https://aciderix.github.io/portable-retro-games/pack_game_fr.html) |

> 💡 These are real examples generated by the packers in this repo — each is a single self-contained HTML file hosted on Netlify.

### 📱 Mobile Experience

Each packed game includes responsive controls optimized for touch:

| Packer | Virtual Controls |
|---|---|
| Universal (EmulatorJS) | Built-in virtual gamepad, D-pad, ABXY buttons, responsive viewport |
| Apple II | Arrow keys, letter grid, digit row, special keys (ESC, RETURN, SPACE) |
| Amstrad CPC | Context-detected keys, AZERTY layout, joystick option |
| Amiga | Virtual joystick with fire button, touch-anywhere controls |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     portable-retro-games                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐    ┌──────────────┐    ┌───────────────────┐    │
│   │ Game ROM  │───▶│ Packer Script│───▶│ Self-Contained    │    │
│   │ or Disk   │    │  (Python)    │    │  HTML File        │    │
│   │  Image    │    │              │    │                   │    │
│   │ .nes .sfc │    │ • Detect sys │    │ ┌───────────────┐│    │
│   │ .gb .gba  │    │ • Fetch core │    │ │  Emulator JS  ││    │
│   │ .gen .z64 │    │ • Embed all  │    │ │  + WASM Core  ││    │
│   │ .dsk .adf │    │ • Optimize   │    │ ├───────────────┤│    │
│   │ .woz .nib │    │ • Build HTML │    │ │  Game Data    ││    │
│   │ .wad .zip │    │              │    │ │  (base64)     ││    │
│   └──────────┘    └──────────────┘    │ ├───────────────┤│    │
│                                        │ │  Virtual      ││    │
│                                        │ │  Controls     ││    │
│                                        │ │  (HTML/CSS/JS)││    │
│                                        │ ├───────────────┤│    │
│                                        │ │  Boot Logic   ││    │
│                                        │ │  & Helpers    ││    │
│                                        │ └───────────────┘│    │
│                                        └───────────────────┘    │
│                                                                 │
│   Packers:                                                      │
│   ────────                                                      │
│   • Universal  → EmulatorJS + WASM cores (41 systems)           │
│   • Apple II   → apple2js (keyboard auto-detection)             │
│   • CPC        → RVMPlayer (Z80 firmware analysis)              │
│   • Amiga      → vAmigaWeb (full asset inlining)                │
│                                                                 │
│   Common Techniques:                                            │
│   ─────────────────                                             │
│   • Base64 encoding for binary data embedding                   │
│   • Blob URLs & Data URIs for asset serving                     │
│   • 3-layer interception (EJS_paths + MutationObserver + fetch)  │
│   • AudioContext resume on first gesture (Chrome mobile)        │
│   • Dynamic viewport (100dvh) with safe area insets             │
│   • Anti-zoom CSS for mobile viewport                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works (Step by Step)

#### Universal Packer (Console Games)

```
   ROM File                  pack_game.py                     Browser
  ┌──────────┐              ┌──────────────┐              ┌──────────────┐
  │          │   1. Read    │              │   4. Output  │              │
  │  .nes    │─────────────▶│  Auto-detect │─────────────▶│  Open HTML   │
  │  .sfc    │              │  system from │              │  in browser  │
  │  .gba    │              │  extension   │              │              │
  │  .z64    │              │              │              │  5. EmulatorJS│
  │  .wad    │              │  2. Load or  │              │  intercepts  │
  └──────────┘              │  download    │              │  fetch calls │
                            │  WASM core   │              │  → serves    │
  WASM Core                 │              │              │  embedded    │
  ┌──────────┐              │  3. Encode   │              │  data        │
  │          │   3. Embed   │  ROM + core  │              │              │
  │ cores/   │─────────────▶│  as base64   │              │  6. Game     │
  │ or cache │   (offline   │  in HTML     │              │  boots! 🎮   │
  │ or CDN   │    first)    │              │              │              │
  └──────────┘              └──────────────┘              └──────────────┘
```

#### Platform-Specific Packers (Apple II, CPC, Amiga)

```
   Disk Image                 Python Packer                    Browser
  ┌──────────┐              ┌──────────────┐              ┌──────────────┐
  │          │   1. Read    │              │   4. Output  │              │
  │  .dsk    │─────────────▶│  Parse disk  │─────────────▶│  Open HTML   │
  │  .adf    │              │  catalog     │              │  in browser  │
  │  .woz    │              │              │              │              │
  └──────────┘              │  2. Analyze  │              │  5. Emulator │
                            │  content for │              │  boots game  │
  Emulator                  │  keyboard    │              │  from        │
  ┌──────────┐              │  detection   │              │  embedded    │
  │          │   3. Fetch   │              │              │  data        │
  │  JS/WASM │─────────────▶│  Embed all   │              │              │
  │  assets  │   & cache    │  into single │              │  6. Virtual  │
  │          │              │  HTML file   │              │  keyboard    │
  └──────────┘              └──────────────┘              │  appears     │
                                                          └──────────────┘
```

---

## 🌟 Possibilities This Opens

### 🏛️ Digital Preservation
Package entire game libraries into portable HTML files. No more worrying about emulator websites going offline, plugin deprecation, or server shutdowns. **Your games survive forever.**

### 🎓 Education
Teachers can distribute retro computing experiences as simple HTML files. Students open them in any browser — no installation, no configuration, no IT department approval needed.

### 📚 Personal Collections
Build your own curated retro game library. Each game is a single file you can organize in folders, back up to cloud storage, or carry on a USB drive.

### 📱 Mobile Retro Gaming
Play NES, SNES, Game Boy, Genesis, N64, Arcade, Apple II, CPC, Amiga and more on your phone or tablet. Touch controls are built right in.

### 🏛️ Museums & Exhibitions
Interactive exhibits that run on any tablet or kiosk. No internet connection required. No maintenance. Just open the HTML file.

### 🌐 Offline Access
Perfect for situations with limited or no internet: airplanes, remote areas, schools with restricted networks, archival storage.

### 📤 Easy Sharing
Share a game with anyone by sending a single file. No instructions needed — just "open this in your browser." Works on Windows, Mac, Linux, iOS, Android, ChromeOS.

---

## 📖 Documentation

| Document | Description |
|---|---|
| [Universal Packer](packers/universal/README.md) | Complete guide to the Universal Packer: 41 systems, offline mode, all options |
| [Apple II Packer](docs/apple2-packer.md) | Complete guide to the Apple II packer: disk formats, key detection, virtual keyboard |
| [CPC Packer](docs/cpc-packer.md) | Complete guide to the Amstrad CPC packer: DSK parsing, Z80 analysis, AZERTY mapping |
| [Amiga Packer](docs/amiga-packer.md) | Complete guide to the Amiga packer: WASM embedding, asset inlining, caching |
| [Architecture](docs/architecture.md) | Technical deep-dive: embedding strategies, mobile patterns, emulator integration |
| [Future Enhancements](docs/future-enhancements.md) | Roadmap: save states, PWA support, more platforms, compression, batch processing |
| [Supported Platforms Roadmap](docs/supported-platforms-roadmap.md) | 🗺️ 40+ retro platforms feasibility analysis, priority ranking & universal packer vision |

---

## 🔧 Technical Highlights

### Universal System Detection 🔍

The universal packer auto-detects the target system from file extensions:

```
.nes → NES (FCEUmm)             .sfc/.smc → SNES (Snes9x)
.gb → Game Boy (Gambatte)        .gbc → Game Boy Color (Gambatte)
.gba → GBA (mGBA)               .gen/.md → Genesis (Genesis Plus GX)
.z64/.n64/.v64 → N64 (Mupen64)  .nds → Nintendo DS (melonDS)
.a26 → Atari 2600 (Stella)      .a52 → Atari 5200 (a5200)
.a78 → Atari 7800 (ProSystem)   .lnx → Atari Lynx (Handy)
.j64/.jag → Atari Jaguar        .gg → Game Gear (Genesis Plus GX)
.sms → Master System (SMSPlus)  .32x → Sega 32X (PicoDrive)
.pce → PC Engine (Mednafen)     .col → ColecoVision (GearColeco)
.ngp → Neo Geo Pocket (Mednafen) .ws/.wsc → WonderSwan (Mednafen)
.vb → Virtual Boy (Beetle VB)   .d64/.prg → C64 (VICE x64sc)
.adf → Amiga (PUAE)             .dsk → Amstrad CPC (cap32)
.wad → DOOM (PrBoom)            .zip → Arcade (CPS1/CPS2/FBNeo/MAME)
.iso/.bin/.cue/.chd → 3DO (Opera)  .chd/.iso → Philips CD-i (same_cdi)
.bin/.cue/.iso/.chd → Sega Saturn (Yabause)
...and more — run --list-systems for the full list
```

### Offline-First Architecture 📡

The universal packer resolves assets in this order:
1. **`cores/` directory** — portable offline bundle next to the script
2. **`~/.emulatorjs_cache/`** — persistent local cache
3. **EmulatorJS CDN** — only if not cached (first use per system)

```bash
# Pre-download everything for full offline use
python3 pack_game.py --prefetch-all    # All 41 systems, 92 core files (46 × 2: normal + legacy)

# Or unzip the included cores bundle
unzip cores.zip                        # Included in the repo

# Check what's cached
python3 pack_game.py --offline-status
```

### Keyboard Auto-Detection 🎹

Platform-specific packers analyze the game content to determine which keys the player will need:

- **Apple II**: Reads DOS 3.3 catalog entries — text adventures get a full letter grid; arcade games get arrow keys and a few action buttons
- **CPC**: Parses BASIC source for `INKEY$`, `JOY()` patterns and scans Z80 binaries for firmware calls (`BB09h`, `BB1Bh`) to detect keyboard vs. joystick input
- **Amiga**: Configures virtual joystick + fire button (most Amiga games are joystick-based)

### Emulator Asset Management 📦

Each packer manages its own cache:

```
~/.emulatorjs_cache/        # Universal packer — WASM cores + EmulatorJS
~/.apple2js_cache/          # Apple II emulator JS + ROM files
~/.cpc_emulator_cache/      # RVMPlayer emulator resources
./vAmigaWeb/                # vAmiga WASM + support files
```

### Mobile-First Design 📱

- **Dynamic viewport height** (`100dvh`) with safe area insets for notched devices
- **Touch event handling** with proper `preventDefault()` to avoid scroll/zoom
- **AudioContext resume** on first user gesture (required by Chrome/Safari)
- **Viewport locking** with `user-scalable=no` and `touch-action` CSS
- **Responsive layouts** that adapt to screen orientation
- **WebGL with 2D Canvas fallback** for older devices

### Single-File Philosophy 📄

Everything is embedded. The generated HTML files contain:

| Content | Encoding | Typical Size |
|---|---|---|
| Emulator engine (JS) | Inline `<script>` | 200KB – 2MB |
| Emulator engine (WASM) | Base64 in `<script>` | 1MB – 5MB |
| Game ROM / disk image | Base64 in `<script>` | 140KB – 50MB |
| Kickstart ROM (Amiga) | Base64 in `<script>` | 512KB |
| Virtual keyboard/controls | Inline HTML/CSS/JS | 10KB – 30KB |
| Fetch/XHR interceptors | Inline `<script>` | 2KB – 5KB |
| Help overlay | Inline HTML/CSS | 5KB |
| Images/SVG/sounds | Base64 Data URIs | Variable |

---

## 🎮 Game Library

### 🌐 Universal Packer — 41 Systems Supported

The universal packer supports **41 retro systems** with a single Python script. Most systems work out of the box; some may require specific ROM formats or BIOS files for optimal results.

| Status | Systems |
|--------|---------|
| ✅ **Fully tested** | NES, SNES, Game Boy, GBC, GBA, N64, NDS, Genesis, Master System, Game Gear, 32X, Atari 2600, 5200, 7800, Lynx, ColecoVision, Neo Geo Pocket, Virtual Boy, WonderSwan, PC Engine, C64, ZX Spectrum |
| 🟡 **Supported — may need tuning** | PSX *(needs BIOS)*, Sega CD *(large CD images)*, Jaguar, C128, VIC-20, PET, Plus/4, Amiga, CPC, ZX81, PC-FX |
| 🕹️ **Arcade / DOOM** | CPS1, CPS2, FBNeo, MAME 2003+, DOOM *(require `--system` flag + correct ROM sets)* |

> 💡 Systems marked "may need tuning" boot correctly via EmulatorJS but may require specific ROM formats, firmware files, or configuration depending on the game. Contributions and testing feedback are welcome!

### Amstrad CPC — 132 French Games Ready 🇫🇷

The CPC packer has been battle-tested with a library of **132 classic French CPC games**, all successfully converted to offline HTML. These include:

- Action/Arcade: *Gryzor*, *Rick Dangerous*, *Renegade*, *Barbarian*
- Adventure: *Sorcery*, *L'Aigle d'Or*, *Sapiens*
- Sports: *Kick Off*, *Match Day II*, *Track & Field*
- Puzzle: *Tetris*, *Boulder Dash*, *Sokoban*
- RPG: *Donjons et Dragons*, *Sram*, *L'Anneau de Doigts*

### Apple II — Classic Titles

- *Karateka*, *Prince of Persia*, *Oregon Trail*
- *Zork*, *Ultima*, *Lode Runner*, *Choplifter*

### Amiga — Custom Builds

- Individually crafted builds with game-specific optimizations
- Full Amiga experience: ECS Agnus, 2MB Chip RAM, 2MB Fast RAM

---

## 🤝 Credits & Acknowledgments

This project stands on the shoulders of incredible open-source emulator projects:

| Emulator | Author | Platform | Technology |
|---|---|---|---|
| [EmulatorJS](https://emulatorjs.org/) | EmulatorJS contributors | 41 console/computer/arcade systems | WebAssembly (RetroArch cores) |
| [apple2js](https://github.com/whscullin/apple2js) | Will Scullin | Apple II | JavaScript |
| [RVMPlayer](https://github.com/nicl83/RVMPlayer) | — | Amstrad CPC | JavaScript |
| [vAmigaWeb](https://github.com/nicl83/vAmigaWeb) | Dirk W. Hoffmann & contributors | Commodore Amiga | WebAssembly (Emscripten) |

Special thanks to all the retro computing communities keeping these platforms alive:
- [Archive.org](https://archive.org) for preserving software history
- [CPCWiki](https://www.cpcwiki.eu/) for Amstrad CPC documentation
- [Apple II Documentation Project](https://mirrors.apple2.org.za/)
- [English Amiga Board](https://eab.abime.net/) for Amiga preservation efforts
- [EmulatorJS](https://emulatorjs.org/) for making RetroArch cores accessible in the browser

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Game disk images and ROMs are NOT included in this repository. You must own or have legal access to the games you package. This tool is intended for personal archival and preservation purposes.

---

## 🛠️ Contributing

Contributions are welcome! Here are some ways you can help:

1. **Add support for new platforms** (DOS, MSX, more computers…)
2. **Improve key detection** algorithms for platform-specific packers
3. **Optimize file sizes** (compression, lazy loading)
4. **Test on more devices** and browsers
5. **Translate** the virtual keyboard overlays
6. **Add save state support** to the universal packer

Please open an issue first to discuss major changes.

---

## 📊 Project Stats

- **44 platforms** supported (41 universal + 3 platform-specific with advanced features)
- **132+ games** tested and converted (CPC library)
- **22 systems** fully validated with real ROM testing, 41 total supported
- **0 pip dependencies** for the universal packer (Python stdlib only)
- **0 runtime dependencies** in generated HTML files
- **100% offline** — no server, no CDN, no internet
- **Mobile-ready** with touch-optimized virtual controls

---

## 🏷️ Keywords

`retro gaming` · `emulator` · `offline` · `HTML5` · `NES` · `SNES` · `Game Boy` · `GBA` · `N64` · `Nintendo DS` · `Sega Genesis` · `Master System` · `PlayStation` · `Atari` · `Atari Jaguar` · `Apple II` · `Amstrad CPC` · `Commodore Amiga` · `Commodore 64` · `Commodore 128` · `VIC-20` · `ZX Spectrum` · `ZX81` · `Arcade` · `CPS1` · `CPS2` · `MAME` · `FBNeo` · `DOOM` · `game preservation` · `browser emulator` · `single-file` · `self-contained` · `EmulatorJS` · `RetroArch` · `WASM` · `WebAssembly` · `JavaScript emulator` · `ROM packer` · `offline gaming` · `preservation tools` · `mobile gaming`

---

---

## 🇫🇷 Résumé en Français

### portable-retro-games — Transformez vos jeux rétro en fichiers HTML jouables hors-ligne

**portable-retro-games** est un ensemble de scripts Python qui transforment des ROMs et images disque de jeux rétro en **fichiers HTML autonomes et jouables hors-ligne**.

Chaque fichier HTML généré embarque :
- ✅ Un **émulateur complet** en JavaScript ou WebAssembly
- ✅ La **ROM ou image disque du jeu** encodée en base64
- ✅ Des **contrôles tactiles** optimisés pour mobile
- ✅ **Zéro dépendance externe** — fonctionne hors-ligne, pour toujours

### Plateformes supportées

#### 🌐 Packer Universel — 41 systèmes consoles, ordinateurs & arcade

Un seul script Python, zéro dépendance pip, auto-détection du système :

| Catégorie | Systèmes |
|-----------|----------|
| 🎮 Nintendo | NES, SNES, Game Boy, GBC, GBA, N64, DS, Virtual Boy |
| 🎮 Sega | Genesis, Master System, Game Gear, 32X, Sega CD |
| 🎮 Atari | 2600, 5200, 7800, Lynx, Jaguar |
| 🎮 Sony | PlayStation |
| 🎮 NEC | PC Engine / TurboGrafx-16, PC-FX |
| 🎮 SNK | Neo Geo Pocket / Color |
| 🎮 Bandai | WonderSwan / Color |
| 🎮 Coleco | ColecoVision |
| 💻 Commodore | C64, C128, VIC-20, PET, Plus/4, Amiga |
| 💻 Sinclair | ZX Spectrum, ZX81 |
| 💻 Amstrad | CPC |
| 💻 **PC / DOS** | MS-DOS (DOSBox) |
| 🕹️ Arcade | CPS1, CPS2, FBNeo, MAME 2003+ |
| 🔫 id Software | DOOM (PrBoom) |
| 🎮 Autres | 3DO, Philips CD-i, Sega Saturn |

#### 🔧 Packers spécialisés — Fonctions avancées

| Plateforme | Script | Émulateur | Formats |
|---|---|---|---|
| 🍎 Apple II | `pack_apple2_game_html.py` | apple2js | `.dsk`, `.do`, `.po`, `.nib`, `.woz` |
| 💾 Amstrad CPC | `pack_cpc_game_html.py` | RVMPlayer | `.dsk` |
| 🐱 Amiga | `build_jimmy_willburne.py` | vAmigaWeb | `.adf` |

> 💡 **Note :** Amstrad CPC et Commodore Amiga sont disponibles à la fois dans le packer universel (pratique, un seul script) et en packers dédiés (qualité d'émulation supérieure, clavier personnalisé, analyse firmware).

### Fonctionnalités clés

- 🔍 **Détection automatique du système** par extension de fichier (packer universel)
- 🎹 **Détection automatique des touches** par analyse du contenu (packers spécialisés)
- 📱 **Contrôles tactiles** : gamepad virtuel (universel) ou clavier adapté (spécialisé)
- 📡 **Offline-first** : cores locaux → cache → CDN (téléchargement unique par système)
- 🚀 **Chargement turbo** (CPC) : option warp-speed pour accélérer le chargement
- 🔌 **100% hors-ligne** : aucun serveur, aucun CDN, aucune connexion internet
- 🇫🇷 **132 jeux CPC français** déjà convertis et testés
- 🕹️ **Arcade** : CPS1, CPS2, FBNeo et MAME 2003+ supportés

### Utilisation rapide

```bash
# Packer universel (41 systèmes)
python3 packers/universal/pack_game.py SuperMario.nes
python3 packers/universal/pack_game.py Sonic.gen
python3 packers/universal/pack_game.py DOOM.wad
python3 packers/universal/pack_game.py streetfighter2.zip --system cps1
python3 packers/universal/pack_game.py --prefetch-all   # Mode 100% offline

# Apple II
python packers/apple2/pack_apple2_game_html.py Karateka.dsk

# Amstrad CPC
python packers/cpc/pack_cpc_game_html.py Gryzor.dsk

# Amiga
python packers/amiga/build_jimmy_willburne.py
```

### 🌐 Packer Web — Sans installation

Pas envie d'utiliser Python ? Utilisez le **packer web** directement dans votre navigateur :

- 🇫🇷 [**Packer Web (Français)**](https://aciderix.github.io/portable-retro-games/pack_game_fr.html)
- 🇬🇧 [**Packer Web (English)**](https://aciderix.github.io/portable-retro-games/pack_game_en.html)

> Glissez une ROM, choisissez le système, cliquez Générer — vous obtenez un fichier HTML autonome. Sans Python, sans terminal.

### 🎮 Démos jouables en ligne

| Jeu | Plateforme | Lien |
|---|---|---|
| 🐱 **Jimmy Willburne** | Amiga | [▶️ Jouer](https://jimmy-willburne.netlify.app/) |
| 🐱 **Short Grey** | Amiga | [▶️ Jouer](https://short-grey.netlify.app/) |
| 🍎 **Softporn Adventure VF** | Apple II | [▶️ Jouer](https://softporn-adventure-vf.netlify.app/) |
| 🍎 **Le Dragon Gardien** | Apple II | [▶️ Jouer](https://le-dragon-gardien.netlify.app/) |
| 🍎 **Mystery House VF** | Apple II | [▶️ Jouer](https://mystery-house-vf.netlify.app/) |
| 💾 **1815** | Amstrad CPC | [▶️ Jouer](https://1815-cpc.netlify.app/) |
| 🌐 **Packer Web** | 41 systèmes | [🇫🇷 Français](https://aciderix.github.io/portable-retro-games/pack_game_fr.html) · [🇬🇧 English](https://aciderix.github.io/portable-retro-games/pack_game_en.html) |

### Documentation

- [Documentation Packer Universel](packers/universal/README.md) — 41 systèmes, mode offline, toutes les options
- [Documentation Apple II Packer](docs/apple2-packer.md)
- [Documentation CPC Packer](docs/cpc-packer.md)
- [Documentation Amiga Packer](docs/amiga-packer.md)
- [Architecture technique](docs/architecture.md)
- [Améliorations futures](docs/future-enhancements.md)
- [Roadmap des plateformes supportées](docs/supported-platforms-roadmap.md) — 🗺️ Analyse de 40+ plateformes rétro

---

<p align="center">
  Made with ❤️ for retro gaming preservation<br>
  <em>« Les jeux ne meurent jamais — ils changent de support. »</em>
</p>
