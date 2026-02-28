# 🕹️ Feasibility Study — New Systems for portable-retro-games

> **Goal**: Identify all additional retro systems that could be supported, either via EmulatorJS (unused cores) or via standalone JS/WASM emulators enabling the same single offline HTML file principle.

---

## Table of Contents

- [Recap: Currently Supported Systems (38)](#recap-currently-supported-systems-38)
- [PART A — Unused EmulatorJS Cores (5 systems)](#part-a--unused-emulatorjs-cores-5-systems)
- [PART B — Standalone JS/WASM Emulators (13+ systems)](#part-b--standalone-jswasm-emulators-13-systems)
- [PART C — Systems NOT Currently Feasible](#part-c--systems-not-currently-feasible)
- [Summary and Priorities](#summary-and-priorities)
- [Impact on the Universal Packer Code](#impact-on-the-universal-packer-code)

---

## Recap: Currently Supported Systems (38)

| Category | Systems in `pack_game.py` |
|----------|--------------------------|
| **Nintendo Consoles** | NES, SNES, GB, GBC, GBA, N64, NDS, Virtual Boy |
| **Sega Consoles** | Genesis/Mega Drive, Master System, Game Gear, 32X, Sega CD |
| **Atari Consoles** | 2600, 5200, 7800, Lynx, Jaguar |
| **Sony Consoles** | PlayStation |
| **NEC Consoles** | PC Engine, PC-FX |
| **Other Consoles** | Neo Geo Pocket, WonderSwan, ColecoVision |
| **Commodore Computers** | C64, C128, VIC-20, PET, Plus/4, Amiga |
| **Sinclair Computers** | ZX Spectrum, ZX81 |
| **Amstrad Computers** | CPC |
| **Arcade** | CPS1, CPS2, FBNeo, MAME 2003+ |
| **Other** | DOOM (PrBoom) |

---

## PART A — Unused EmulatorJS Cores (5 systems)

These systems already have compiled WASM cores hosted on the EmulatorJS CDN. They can be added to `pack_game.py` **with minimal effort** — essentially a new entry in the `SYSTEMS` dictionary and potentially a few adjustments.

### A1. 🎮 3DO Interactive Multiplayer

| | |
|---|---|
| **Core** | `opera` (~834 KB WASM) |
| **System ID** | `3do` |
| **Extensions** | `.iso`, `.bin`, `.cue`, `.chd` |
| **ROM Size** | 50–650 MB |
| **BIOS Required** | ⚠️ Yes — `panafz1.bin` (Panasonic FZ-1) |
| **Estimated HTML Size** | 70–900 MB |
| **Integration Difficulty** | ⭐⭐ Easy (but large files) |
| **Emulation Quality** | Good, most games work |
| **Notable Games** | Road Rash, Need for Speed, Gex, Return Fire, Star Control II |

**Verdict**: ✅ Feasible. The core exists and works. The main obstacle is the **size of ISOs** (often 300-650 MB) which produce enormous HTML files once base64-encoded (+33%). Viable for smaller games. The mandatory proprietary BIOS complicates distribution.

**Packer addition**:
```python
'3do': {'core': 'opera', 'label': '3DO Interactive Multiplayer', 'extensions': ['.iso', '.bin', '.cue', '.chd']}
```

---

### A2. 🪐 Sega Saturn

| | |
|---|---|
| **Core** | `yabause` (~967 KB WASM) |
| **System ID** | `segaSaturn` |
| **Extensions** | `.iso`, `.bin`, `.cue`, `.chd` |
| **ROM Size** | 50–650 MB |
| **BIOS Required** | ⚠️ Yes — `saturn_bios.bin` |
| **Estimated HTML Size** | 70–900 MB |
| **Integration Difficulty** | ⭐⭐ Easy (code) / ⭐⭐⭐⭐ Hard (performance) |
| **Emulation Quality** | ⚠️ Poor in WASM — Yabause is the least accurate Saturn emulator |
| **Notable Games** | Nights into Dreams, Panzer Dragoon Saga, Virtua Fighter 2, Radiant Silvergun |

**Verdict**: ⚠️ Technically feasible but **disappointing results**. Saturn emulation in WASM via Yabause is known to be unstable. Many games crash or have severe graphical glitches. Files are also very large. Should be offered with a warning.

---

### A3. 📱 PlayStation Portable (PSP)

| | |
|---|---|
| **Core** | `ppsspp` (~4.3 MB WASM, thread-only + 10.3 MB assets) |
| **System ID** | `psp` |
| **Extensions** | `.iso`, `.cso`, `.pbp` |
| **ROM Size** | 50 MB – 1.8 GB |
| **BIOS Required** | No (HLE emulator) |
| **Estimated HTML Size** | 80 MB – 2.5 GB (!) |
| **Integration Difficulty** | ⭐⭐⭐⭐ Hard |
| **Emulation Quality** | Variable — good for 2D games, problematic for large 3D games |
| **Notable Games** | God of War, Crisis Core FF7, Persona 3 Portable, Monster Hunter |

**Verdict**: ⚠️ **Feasible but problematic**. The `ppsspp` core is **thread-only** (requires SharedArrayBuffer, thus special COOP/COEP headers), requires a 10 MB asset package on top, and PSP ISOs are **massive**. The resulting HTML file would often be > 500 MB. Limited appeal for the "portable single file" concept.

**Additional complexity**: The PPSSPP core requires specific HTTP headers (`Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Embedder-Policy: require-corp`) for SharedArrayBuffer. This **does NOT work** when opening a local HTML file with `file://` on most browsers without special configuration.

---

### A4. 💻 DOS (PC)

| | |
|---|---|
| **Core** | `dosbox_pure` (~1.7 MB WASM, thread-only) |
| **System ID** | `dos` |
| **Extensions** | `.zip`, `.dosz`, `.exe`, `.com`, `.bat`, `.iso`, `.cue`, `.img`, `.ima`, `.vhd` |
| **ROM Size** | 100 KB – 500+ MB |
| **BIOS Required** | No |
| **Estimated HTML Size** | Variable, often < 20 MB for classic games |
| **Integration Difficulty** | ⭐⭐⭐ Medium |
| **Emulation Quality** | Excellent — DOSBox Pure is very mature |
| **Notable Games** | Civilization, Oregon Trail, Prince of Persia, Commander Keen, Lemmings, Wolfenstein 3D, Duke Nukem |

**Verdict**: ✅ **Very interesting!** Thousands of classic DOS games would become portable. The core is `thread-only` (same SharedArrayBuffer limitation as PSP), but DOS games are generally small (< 20 MB). DOSBox Pure has the advantage of supporting direct ZIP loading and auto-configuration.

**Standalone alternative**: `js-dos` is a mature and well-documented project that could offer an alternative if thread-only mode is a problem. js-dos is specifically designed for web embedding.

**⚠️ Thread-only limitation**: As with PSP, local HTML files (`file://`) don't support SharedArrayBuffer. **Solutions**:
1. Serve via a small local server (`python -m http.server`)
2. Use js-dos as an alternative (not thread-only)
3. Create a specialized DOS packer based on js-dos rather than EmulatorJS

---

### A5. 📀 Philips CD-i

| | |
|---|---|
| **Core** | `same_cdi` (~3.3 MB WASM) |
| **System ID** | `cdi` |
| **Extensions** | `.chd`, `.iso` |
| **ROM Size** | 100–650 MB |
| **BIOS Required** | ⚠️ Yes — CDi BIOS files |
| **Estimated HTML Size** | 150–900 MB |
| **Integration Difficulty** | ⭐⭐⭐ Medium |
| **Emulation Quality** | Limited — SAME CDi is still in development |
| **Notable Games** | Zelda: Wand of Gamelon, Hotel Mario (notorious), Burn:Cycle |

**Verdict**: ⚠️ **Feasible but anecdotal**. The CDi has a very limited game library and emulation is still imperfect. Primarily of historical/curiosity interest.

---

### Part A Summary — Missing EmulatorJS Cores

| System | Core | Priority | Difficulty | Interest |
|--------|------|----------|------------|----------|
| **DOS** | `dosbox_pure` | 🔴 **High** | Medium (thread-only) | 🌟🌟🌟🌟🌟 Thousands of games |
| **3DO** | `opera` | 🟡 Medium | Easy | 🌟🌟 Decent game library |
| **Sega Saturn** | `yabause` | 🟡 Medium | Easy (code) | 🌟🌟🌟 Great games, but weak emulation |
| **PSP** | `ppsspp` | 🟠 Low | Hard | 🌟🌟🌟 Great games, but too heavy |
| **CD-i** | `same_cdi` | 🔵 Very Low | Medium | 🌟 Historical curiosity |

---

## PART B — Standalone JS/WASM Emulators (13+ systems)

These systems are NOT covered by EmulatorJS but have standalone JavaScript or WebAssembly emulators that could be integrated using the same approach as the existing specialized packers (Apple II, CPC, Amiga).

### B1. 🖥️ MSX / MSX2 / MSX2+ / MSX turboR — WebMSX ⭐⭐⭐⭐⭐

| | |
|---|---|
| **Emulator** | [WebMSX](https://github.com/ppeccin/WebMSX) (WMSX) |
| **Technology** | Pure JavaScript (no WASM needed) |
| **License** | MIT-like / Open source |
| **Maturity** | 🟢 Very mature — multiple versions, mobile support |
| **Models** | MSX1, MSX2, MSX2+, MSX turboR |
| **Formats** | `.rom`, `.dsk`, `.cas` (cassette), `.mx1`, `.mx2` |
| **ROM Size** | 8 KB – 2 MB (ROM), 360 KB – 720 KB (DSK) |
| **Estimated HTML Size** | 500 KB – 2 MB |
| **Game Library Interest** | 🌟🌟🌟🌟🌟 Massive (Metal Gear, Gradius, Vampire Killer, Space Manbow, Aleste, Snatcher…) |

**Why it's excellent**:
- WebMSX was designed from the start for web embedding — the project's very concept is "launch an MSX emulator with a simple link"
- Full keyboard + joystick support
- Pure JavaScript, no WASM needed
- Author (Paulo Augusto Peccin) = same developer as Javatari.js, proven quality
- The MSX has a massive game library (~5000+ games) with legendary Konami titles
- Lightweight ROMs → compact HTML files
- MSX-MUSIC, MSX-AUDIO, SCC support (additional sound chips)

**Integration approach**: Specialized packer similar to `pack_apple2_game_html.py`, embedding WebMSX + ROM/DSK in base64.

---

### B2. 🇬🇧 BBC Micro — JSBeeb ⭐⭐⭐⭐

| | |
|---|---|
| **Emulator** | [JSBeeb](https://github.com/mattgodbolt/jsbeeb) |
| **Technology** | JavaScript/TypeScript |
| **License** | GPL v3 |
| **Maturity** | 🟢 Very mature — by Matt Godbolt (creator of Compiler Explorer) |
| **Models** | BBC Micro Model B (32K), BBC Master (128K) |
| **Formats** | `.ssd`, `.dsd`, `.uef` (cassette) |
| **ROM Size** | 40–200 KB |
| **Estimated HTML Size** | 300 KB – 1 MB |
| **Game Library Interest** | 🌟🌟🌟 Elite, Repton, Citadel, Exile, Chuckie Egg |

**Why it's good**:
- Very accurate and actively maintained emulator
- The BBC Micro is the iconic British home computer (like the CPC for France)
- Very lightweight files
- The project already has a facilitated "embedded" mode

**Approach**: Specialized packer. JSBeeb's structure lends itself well to embedding, similar to the Apple II packer.

---

### B3. 🖥️ Atari ST/STE — EstyJS ⭐⭐⭐

| | |
|---|---|
| **Emulator** | [EstyJS](https://github.com/AntoniMS/estyjs) |
| **Technology** | Pure JavaScript |
| **License** | Open source |
| **Maturity** | 🟡 Medium — functional but not always perfect |
| **Models** | Atari ST (primarily 1040 ST) |
| **Formats** | `.st`, `.stx`, `.msa` (floppy disks) |
| **ROM Size** | 360 KB – 720 KB per disk |
| **BIOS Required** | ⚠️ Yes — TOS ROM |
| **Estimated HTML Size** | 1–3 MB |
| **Game Library Interest** | 🌟🌟🌟🌟 Dungeon Master, Populous, Carrier Command, Speedball 2 |

**Why it's interesting**:
- The Atari ST has an excellent 16-bit game library
- Many exclusive or superior ports (Dungeon Master, Falcon)
- Pure JavaScript = no SharedArrayBuffer issues

**Limitations**:
- EstyJS isn't as mature as vAmigaWeb or WebMSX
- Requires a proprietary TOS ROM
- Variable compatibility depending on the game

**Possible alternative**: Hatari (a mature ST emulator in C) has been compiled via Emscripten by some projects, but there's no stable official web version.

---

### B4. 🇫🇷 Thomson MO5/MO6/TO7 — DCMO5 / MO5 Emulator ⭐⭐⭐

| | |
|---|---|
| **Emulator** | [DCMO5 Online](http://dcmo5.free.fr/online/) / [MO5 Emulator (roug.org)](https://www.roug.org/retrocomputing/emulators/mo5) |
| **Technology** | JavaScript |
| **License** | Open source |
| **Maturity** | 🟡 Medium |
| **Models** | Thomson MO5, MO6 (DCMO5 also covers TO7, TO8, TO9) |
| **Formats** | `.k7` (cassette), `.fd` (floppy disk) |
| **ROM Size** | 10–100 KB |
| **Estimated HTML Size** | 200 KB – 1 MB |
| **Game Library Interest** | 🌟🌟🌟 French heritage — computers from the "Plan Informatique pour Tous" national education program |

**Why it's relevant**:
- 🇫🇷 **Major French cultural heritage** — Thomson computers were in every French school in the 1980s
- Perfect complement to the CPC packer (132 French games already converted)
- Tiny ROMs → very compact HTML files
- Heritage at risk of digital disappearance

**Approach**: French-focused specialized packer. Could reuse patterns from the CPC packer (same target audience).

---

### B5. 🇬🇧 Oric Atmos — Oricutron WASM / JOric ⭐⭐⭐

| | |
|---|---|
| **Emulator** | [Oricutron](https://torguet.net/oric/Oricutron.html) (Emscripten) / [JOric](https://github.com/lanceewing/joric) (libGDX→HTML5) |
| **Technology** | C→WebAssembly (Oricutron) / Java→HTML5 (JOric) |
| **License** | GPL v2 (Oricutron) |
| **Maturity** | 🟡 Medium — Oricutron WASM is an ongoing port |
| **Models** | Oric-1, Oric Atmos, Telestrat |
| **Formats** | `.tap`, `.dsk` |
| **ROM Size** | 10–48 KB |
| **Estimated HTML Size** | 300 KB – 1 MB |
| **Game Library Interest** | 🌟🌟 Active community but modest game library |

**Why it's interesting**:
- The Oric is a Franco-British computer with a still-active community
- Extremely lightweight files
- Oricutron has a documented WASM port (PDF presentation available)
- JOric directly targets HTML5

---

### B6. 🕹️ Vectrex — JSVecX ⭐⭐⭐

| | |
|---|---|
| **Emulator** | [JSVecX](http://www.twitchasylum.com/jsvecx/) |
| **Technology** | JavaScript (port of VecX) |
| **License** | Open source |
| **Maturity** | 🟡 Functional |
| **Formats** | `.vec`, `.bin` |
| **ROM Size** | 4–32 KB |
| **Estimated HTML Size** | < 200 KB |
| **Game Library Interest** | 🌟🌟 Unique — vector display, cult console |

**Why it's cool**:
- The Vectrex is the only vector-display console (like Asteroids in the arcade)
- **Tiny** ROMs → most compact HTML files possible
- Visually unique and spectacular
- The BIOS/monitor ROM is free (Milton Bradley never protected it)
- Active homebrew scene

---

### B7. 🖥️ TI-99/4A — JS99'er ⭐⭐⭐

| | |
|---|---|
| **Emulator** | [JS99'er](https://js99er.net/) ([Source](https://github.com/Rasmus-M/Js99er)) |
| **Technology** | JavaScript/TypeScript |
| **License** | Open source |
| **Maturity** | 🟢 Mature |
| **Formats** | `.bin`, `.rpk`, `.dsk` |
| **ROM Size** | 8–32 KB |
| **Estimated HTML Size** | < 500 KB |
| **Game Library Interest** | 🌟🌟 Parsec, TI Invaders, Tunnels of Doom, Hunt the Wumpus |

**Why**: Iconic Texas Instruments home computer with a dedicated community. Very lightweight ROMs.

---

### B8. 💻 DOS (alternative) — js-dos ⭐⭐⭐⭐⭐

| | |
|---|---|
| **Emulator** | [js-dos](https://js-dos.com/) ([Source](https://github.com/caiiiycuk/js-dos)) |
| **Technology** | C→WebAssembly (DOSBox Emscripten) |
| **License** | GPL v2 |
| **Maturity** | 🟢 Very mature — active project since 2014 |
| **Formats** | `.zip`, `.exe`, `.com`, DOS game archives |
| **Game Size** | 100 KB – 500 MB |
| **Estimated HTML Size** | 2–50 MB for the majority of classics |
| **Game Library Interest** | 🌟🌟🌟🌟🌟 Thousands of DOS games (Civilization, C&C, DOOM, Wolfenstein…) |

**Why it's a priority**:
- **Alternative to EmulatorJS's `dosbox_pure` core** which is thread-only
- js-dos is specifically designed for web embedding
- No SharedArrayBuffer restriction → **works with `file://`**!
- Well-documented JavaScript API for auto-configuration
- Can serve as the foundation for a specialized DOS packer

**This is potentially the best candidate for a new specialized packer** because it solves the thread-only problem of the EmulatorJS core.

---

### B9. 🗡️ ScummVM — Emscripten Port ⭐⭐⭐⭐

| | |
|---|---|
| **Emulator** | [ScummVM](https://github.com/scummvm/scummvm) (official Emscripten port) |
| **Technology** | C++→WebAssembly |
| **License** | GPL v3 |
| **Maturity** | 🟢 Mature — official port maintained by the ScummVM team |
| **Engines** | SCUMM, AGI, SCI, Wintermute, Glk, and 50+ others |
| **Formats** | Data files specific to each game |
| **Game Size** | 1–200 MB |
| **Estimated HTML Size** | 5–300 MB |
| **Game Library Interest** | 🌟🌟🌟🌟🌟 Monkey Island, Day of the Tentacle, Sam & Max, King's Quest, Space Quest, Gabriel Knight, Myst… |

**Why it's exceptional**:
- ScummVM supports **hundreds of adventure games** from LucasArts, Sierra, Revolution, etc.
- It's a **meta-emulator**: a single tool covers an entire segment of retro gaming (point-and-click)
- Official and maintained Emscripten port
- Many freeware/demo games available legally
- Cross-platform by nature

**Approach**: A specialized ScummVM packer would be a major addition to the project. It would need to embed the ScummVM WASM + the game's data files.

---

### B10. 🖥️ Classic Macintosh — PCE.js / MiniVMac ⭐⭐

| | |
|---|---|
| **Emulator** | [PCE.js](https://jamesfriend.com.au/pce-js/) / [MiniVMac-Em](https://github.com/nickvdp/minivmac-3.5-emscripten) |
| **Technology** | C→Emscripten |
| **Maturity** | 🟡 Functional |
| **Models** | Mac Plus, Mac SE, Mac Classic |
| **Formats** | `.dsk`, `.img` (800K/1.4M floppy) |
| **BIOS Required** | ⚠️ Yes — Mac ROM |
| **Estimated HTML Size** | 2–5 MB |
| **Interest** | 🌟🌟🌟 HyperCard, Dark Castle, Lode Runner, Shufflepuck Cafe |

**Note**: Interesting but requires proprietary Mac ROMs. The classic Mac has a mouse-only interface that lends itself well to touchscreens.

---

### B11. 🖥️ TRS-80 — TRSjs ⭐⭐

| | |
|---|---|
| **Emulator** | [TRSjs](http://trsjs.48k.ca/trs80.html) |
| **Technology** | JavaScript |
| **Formats** | `.cas`, `.dsk` |
| **Interest** | 🌟🌟 Historical (first mass-market personal computer) |

---

### B12. 🇫🇷 Hector / Micronique — HectorJS ⭐

Very niche. Rare French computer. No known quality JS emulator.

---

### B13. 🎮 Pokémon Mini ⭐

No known dedicated JS emulator. Potentially emulable via a MAME core if available in WASM.

---

## PART C — Systems NOT Currently Feasible

| System | Reason | Outlook |
|--------|--------|---------|
| **Nintendo 3DS** | Citra requires hardware GPU rendering, WASM is insufficient | ❌ Not for a long time |
| **Nintendo Wii / GameCube** | Dolphin uses cmake, impossible performance in WASM | ❌ |
| **PlayStation 2** | Play! has an experimental JS port but nearly unusable | ❌ |
| **Xbox (original)** | No JS/WASM emulator | ❌ |
| **Sega Dreamcast** | Flycast WASM exists (new! 2024) but very experimental, requires BIOS + WebGL2, GDI files 500MB+ | ⚠️ Emerging — watch this space |
| **Sharp X68000** | No WASM port | ❌ |
| **NEC PC-88/PC-98** | RetroArch cores exist but not compiled to WASM for EmulatorJS | ⚠️ Possible if someone compiles them |
| **FM Towns** | No WASM port | ❌ |
| **Neo Geo AES/MVS** | Partially covered via FBNeo, but no dedicated entry | ✅ Already via FBNeo |

### Note on Dreamcast (Flycast WASM)
The [flycast-wasm](https://github.com/nasomers/flycast-wasm) project is the first public Flycast WASM port (November 2024). It works with EmulatorJS, requires a real BIOS, WebGL2, and produces enormous files (GDI = 500 MB+). This is a signal that browser-based Dreamcast emulation **is progressing**, but it's still too experimental and heavy for the portable-retro-games concept. **Reassess in 2025-2026.**

---

## Summary and Priorities

### 🏆 Top 5 — Recommended Additions (by priority)

| # | System | Method | Effort | Impact |
|---|--------|--------|--------|--------|
| 1 | **DOS (PC games)** | js-dos (specialized packer) + dosbox_pure (EmulatorJS) | Medium | 🌟🌟🌟🌟🌟 Thousands of games |
| 2 | **MSX / MSX2** | WebMSX (specialized packer) | Medium | 🌟🌟🌟🌟🌟 Massive library, Konami |
| 3 | **ScummVM** | ScummVM WASM (specialized packer) | High | 🌟🌟🌟🌟🌟 Legendary point-and-click games |
| 4 | **3DO** | EmulatorJS core `opera` (add to pack_game.py) | Low | 🌟🌟 Decent game library |
| 5 | **BBC Micro** | JSBeeb (specialized packer) | Medium | 🌟🌟🌟 Iconic UK computer |

### 🥈 Tier 2 — Interesting Additions

| # | System | Method | Effort | Impact |
|---|--------|--------|--------|--------|
| 6 | **Thomson MO5/TO7** | DCMO5 (specialized packer) | Medium | 🌟🌟🌟 French heritage |
| 7 | **Atari ST** | EstyJS (specialized packer) | Medium-High | 🌟🌟🌟 Great 16-bit games |
| 8 | **Vectrex** | JSVecX (specialized packer) | Low | 🌟🌟 Unique/spectacular |
| 9 | **TI-99/4A** | JS99'er (specialized packer) | Medium | 🌟🌟 Dedicated community |
| 10 | **Oric** | Oricutron WASM (specialized packer) | Medium | 🌟🌟 Franco-British |

### 🥉 Tier 3 — Possible but Lower Priority Additions

| # | System | Reason for Low Priority |
|---|--------|------------------------|
| 11 | **Sega Saturn** | WASM emulation too unstable |
| 12 | **PSP** | Files too heavy, thread-only |
| 13 | **CD-i** | Nearly nonexistent game library |
| 14 | **Classic Mac** | BIOS required, niche |
| 15 | **TRS-80** | Very niche |

---

## Impact on the Universal Packer Code

### EmulatorJS Additions (Part A) — Minimal Modifications

For the 5 missing EmulatorJS systems, it's simply a matter of adding entries to the `SYSTEMS` dictionary in `pack_game.py`:

```python
# Additions to the SYSTEMS dictionary in pack_game.py

# 3DO
'3do': {
    'core': 'opera',
    'label': '3DO Interactive Multiplayer',
    'extensions': ['.iso', '.bin', '.cue', '.chd'],
    'bios': 'panafz1.bin'   # Must be handled
},

# Sega Saturn
'saturn': {
    'core': 'yabause',
    'label': 'Sega Saturn',
    'extensions': ['.iso', '.bin', '.cue', '.chd'],
    'bios': 'saturn_bios.bin'
},

# DOS
'dos': {
    'core': 'dosbox_pure',
    'label': 'DOS (PC)',
    'extensions': ['.zip', '.dosz', '.exe', '.com', '.bat'],
    'thread_only': True   # ⚠️ Requires SharedArrayBuffer
},

# PSP
'psp': {
    'core': 'ppsspp',
    'label': 'PlayStation Portable',
    'extensions': ['.iso', '.cso', '.pbp'],
    'thread_only': True,
    'extra_assets': 'ppsspp-assets.zip'
},

# CD-i
'cdi': {
    'core': 'same_cdi',
    'label': 'Philips CD-i',
    'extensions': ['.chd', '.iso'],
    'bios': 'cdibios.zip'
},
```

**New features required in pack_game.py**:
1. **BIOS handling**: Allow inclusion of a base64-encoded BIOS file in the HTML and serve it via the fetch interceptor
2. **`thread_only` flag**: Warn the user that the file won't work with `file://` without a server
3. **Additional assets**: For PSP, include the additional assets zip

### Specialized Packers (Part B) — New Scripts

Each new specialized packer would follow the existing pattern:
1. **Download and cache** the JS/WASM emulator
2. **Encode** the ROM/DSK in base64
3. **Analyze** the content if possible (genre detection, keys, etc.)
4. **Assemble** the final HTML with emulator + data + UI

Effort estimate per packer:

| Packer | Estimated Effort | Complexity |
|--------|-----------------|------------|
| WebMSX (MSX) | 2-3 days | Medium — well-documented API |
| js-dos (DOS) | 3-5 days | Medium-High — per-game config |
| ScummVM | 5-7 days | High — multi-engine, game detection |
| JSBeeb (BBC) | 2-3 days | Medium |
| DCMO5 (Thomson) | 2-3 days | Medium |
| EstyJS (Atari ST) | 3-4 days | Medium-High — TOS ROM |
| JSVecX (Vectrex) | 1-2 days | Low — very simple |
| JS99'er (TI-99) | 2-3 days | Medium |
| Oricutron (Oric) | 3-4 days | Medium-High |

---

## Conclusion

The portable-retro-games project can **double its coverage** by adding:
- **5 systems** via existing EmulatorJS cores (minimal effort for 3DO, Saturn, DOS, PSP, CDi)
- **9+ systems** via standalone JS/WASM emulators (medium to high effort per specialized packer)

The three most impactful additions would be **DOS** (via js-dos), **MSX** (via WebMSX), and **ScummVM** — which together would open access to **several thousand additional games** while staying true to the single offline HTML file concept.

The Flycast WASM project for Dreamcast is worth monitoring as it could become viable in 1-2 years.

---

*Report generated on February 28, 2026*
