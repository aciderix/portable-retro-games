# 🕹️ Supported Platforms & Roadmap

> **Which retro systems can be turned into portable, standalone HTML games?**
> This document maps every retro platform with a viable JavaScript/WebAssembly emulator and rates them by feasibility, impact, and priority.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Currently Supported](#-currently-supported)
- [Tier 1 — Excellent Feasibility](#-tier-1--excellent-feasibility-lightweight-roms-stable-emulation)
- [Tier 2 — Feasible with Caveats](#-tier-2--feasible-with-caveats-heavier-roms-bios-required)
- [Tier 3 — Retro Computers](#-tier-3--retro-computers)
- [Tier 4 — Not Yet Feasible](#-tier-4--not-yet-feasible)
- [Priority Roadmap](#-priority-roadmap)
- [Universal Packer Vision](#-universal-packer-vision)
- [Technical Considerations](#-technical-considerations)

---

## How It Works

Each packer script takes a ROM or disk image and produces a **single, self-contained HTML file** that:

- ✅ Embeds the emulator (JavaScript/WebAssembly)
- ✅ Embeds the game data (base64-encoded)
- ✅ Runs in any modern browser — desktop, tablet, phone
- ✅ Works offline — no server, no CDN, no internet required
- ✅ Can be shared as a single file — email, USB, cloud storage, messaging

The limiting factors are: **emulator maturity** (does a good JS/WASM emulator exist?) and **ROM size** (can it be reasonably embedded in base64 inside an HTML file?).

---

## ✅ Currently Supported

| Platform | Emulator | Status |
|---|---|---|
| 🍎 **Apple II** | apple2js | ✅ Production — packer available |
| 💾 **Amstrad CPC** | CPCBox (RVMPlayer) | ✅ Production — 132 French games packed |
| 🐱 **Commodore Amiga** | vAmigaWeb | ✅ Production — with IndexedDB caching |

---

## 🟢 Tier 1 — Excellent Feasibility (lightweight ROMs, stable emulation)

These platforms have tiny ROMs and rock-solid JavaScript/WebAssembly emulators. Single-file HTML games would be under 5 MB — perfect for the portable-retro-games concept.

| Platform | JS/WASM Emulator | ROM Format | Typical ROM Size | HTML Size Estimate | Difficulty |
|---|---|---|---|---|---|
| **NES / Famicom** | JSNES, FCEUmm (EmulatorJS) | `.nes` | 8–512 KB | **< 1 MB** | ⭐ Very easy |
| **Game Boy** | Gambatte (EmulatorJS) | `.gb` | 32 KB–1 MB | **< 1 MB** | ⭐ Very easy |
| **Game Boy Color** | Gambatte (EmulatorJS) | `.gbc` | 32 KB–2 MB | **< 2 MB** | ⭐ Very easy |
| **SNES / Super Famicom** | Snes9x (EmulatorJS) | `.smc`, `.sfc` | 256 KB–6 MB | **< 8 MB** | ⭐ Easy |
| **Sega Master System** | SMSPlus (EmulatorJS) | `.sms` | 32–512 KB | **< 1 MB** | ⭐ Very easy |
| **Sega Game Gear** | Genesis Plus GX (EmulatorJS) | `.gg` | 32–512 KB | **< 1 MB** | ⭐ Very easy |
| **Sega Mega Drive / Genesis** | Genesis Plus GX (EmulatorJS) | `.md`, `.bin` | 256 KB–4 MB | **< 6 MB** | ⭐ Easy |
| **Atari 2600** | Stella2014 (EmulatorJS) | `.a26`, `.bin` | 2–32 KB | **< 500 KB** | ⭐ Trivial |
| **Atari 7800** | ProSystem (EmulatorJS) | `.a78` | 16–128 KB | **< 500 KB** | ⭐ Very easy |
| **Atari 5200** | a5200 (EmulatorJS) | `.a52` | 8–32 KB | **< 500 KB** | ⭐ Very easy |
| **Atari Lynx** | Handy (EmulatorJS) | `.lnx` | 128–512 KB | **< 1 MB** | ⭐ Easy |
| **ColecoVision** | Gearcoleco (EmulatorJS) | `.col` | 8–32 KB | **< 500 KB** | ⭐ Very easy |
| **Neo Geo Pocket / Color** | Mednafen NGP (EmulatorJS) | `.ngp`, `.ngc` | 64 KB–4 MB | **< 5 MB** | ⭐ Easy |
| **WonderSwan / Color** | Mednafen WSwan (EmulatorJS) | `.ws`, `.wsc` | 64 KB–16 MB | **< 20 MB** | ⭐ Easy |
| **Virtual Boy** | Beetle VB (EmulatorJS) | `.vb` | 128 KB–1 MB | **< 2 MB** | ⭐ Easy |
| **PC Engine / TurboGrafx-16** | Mednafen PCE (EmulatorJS) | `.pce` | 256 KB–2 MB | **< 3 MB** | ⭐ Easy |
| **Sega 32X** | PicoDrive (EmulatorJS) | `.32x` | 1–3 MB | **< 5 MB** | ⭐ Easy |

> **17 platforms** ready to go with minimal effort. Combined with EmulatorJS, a single universal packer could handle all of them.

---

## 🟡 Tier 2 — Feasible with Caveats (heavier ROMs, BIOS required)

These platforms work in WASM but produce larger HTML files (50–500+ MB) or require BIOS files. Still viable for smaller games.

| Platform | JS/WASM Emulator | ROM Size | Challenge |
|---|---|---|---|
| **Game Boy Advance** | mGBA (EmulatorJS) | 1–32 MB | Larger files but manageable (< 40 MB HTML) |
| **Nintendo 64** | Mupen64Plus Next (EmulatorJS) | 4–64 MB | Variable performance in WASM, some games crash |
| **Nintendo DS** | melonDS, DeSmuME (EmulatorJS) | 8–256 MB | Dual screen layout, large ROMs |
| **PlayStation (PS1)** | PCSX ReARMed (EmulatorJS) | 50–700 MB | BIOS required (legal issue), CD-size games |
| **PSP** | PPSSPP (EmulatorJS) | 200 MB–1.8 GB | Way too large for single-file, needs streaming |
| **Sega Saturn** | Yabause (EmulatorJS) | 50–600 MB | Heavy emulation + large files |
| **Sega CD / Mega CD** | Genesis Plus GX (EmulatorJS) | 50–600 MB | CD-size games |
| **3DO** | Opera (EmulatorJS) | 50–700 MB | Obscure + large files |
| **Atari Jaguar** | Virtual Jaguar (EmulatorJS) | 1–6 MB | Unstable emulation in WASM |
| **PC-FX** | Mednafen PCFX (EmulatorJS) | 50–600 MB | Very niche, CD-size |

> **GBA is the sweet spot** in Tier 2 — still small enough for single-file, hugely popular catalog.

---

## 🟠 Tier 3 — Retro Computers

| Platform | JS/WASM Emulator | ROM Format | Difficulty |
|---|---|---|---|
| 🍎 **Apple II** | apple2js | `.dsk` | ✅ Already supported |
| 💾 **Amstrad CPC** | CPCBox / RVMPlayer | `.dsk` | ✅ Already supported |
| 🐱 **Commodore Amiga** | vAmigaWeb (PUAE via EmulatorJS) | `.adf` | ✅ Already supported |
| **Commodore 64** | VICE x64sc (EmulatorJS) | `.d64`, `.t64`, `.prg` | ⭐ Easy — huge game library |
| **Commodore 128** | VICE x128 (EmulatorJS) | `.d64`, `.d71` | ⭐ Easy |
| **Commodore VIC-20** | VICE xvic (EmulatorJS) | `.prg`, `.crt` | ⭐ Very easy — tiny ROMs |
| **Commodore PET** | VICE xpet (EmulatorJS) | `.prg` | ⭐ Very easy |
| **ZX Spectrum** | JSSpeccy, Fuse | `.z80`, `.tap`, `.sna` | ⭐ Very easy — huge UK scene |
| **MSX / MSX2** | WebMSX | `.rom`, `.dsk` | ⭐ Easy — Konami classics |
| **MS-DOS** | DOSBox Pure (EmulatorJS), js-dos | `.exe`, `.zip` | ⚠️ Variable — games vary wildly in size |
| **Atari ST** | Hatari (no stable WASM yet) | `.st` | ⚠️ Medium — emulator not ready |
| **Thomson MO5/TO7** | DCMOTO (partial JS port) | `.fd`, `.k7` | ⚠️ Very niche |

> **Commodore 64 and ZX Spectrum** are the top picks here — massive libraries, tiny ROMs, huge communities.

---

## 🔴 Tier 4 — Not Yet Feasible

| Platform | Why Not |
|---|---|
| **Nintendo 3DS** | Citra compiles to WASM but requires hardware rendering — no single-file possible |
| **Wii / GameCube** | Dolphin exists but performance is unplayable in WASM |
| **PlayStation 2** | No viable WASM emulator exists |
| **Xbox** | No WASM emulator |
| **Dreamcast** | Flycast exists in RetroArch but very unstable in WASM |

These may become feasible as WebGPU matures and browsers get faster.

---

## 🏆 Priority Roadmap

### Phase 1 — Quick Wins (1–2 weeks)
**Maximum impact, minimum effort.** These 4 consoles represent the most searched retro platforms globally.

| Priority | Platform | Why |
|---|---|---|
| 🥇 | **NES / Famicom** | Most iconic console ever. ROMs < 512 KB. HTML < 1 MB. Mario, Zelda, Mega Man, Castlevania. |
| 🥈 | **SNES / Super Famicom** | Best RPGs ever made. Chrono Trigger, FF6, EarthBound, Secret of Mana. Snes9x is bulletproof. |
| 🥉 | **Game Boy / GBC** | Pokémon alone justifies this. ROMs are tiny. Massive nostalgia factor. |
| 4 | **Mega Drive / Genesis** | Sonic, Streets of Rage, Golden Axe. The other 16-bit giant. |

### Phase 2 — Expansion (1 month)
**Cover portables and European 8-bit computers.**

| Priority | Platform | Why |
|---|---|---|
| 5 | **Game Boy Advance** | Best handheld library. Pokémon, Advance Wars, Metroid Fusion. |
| 6 | **Commodore 64** | Huge European community. Complements existing CPC + Amiga packers. |
| 7 | **ZX Spectrum** | UK retro scene staple. Ultra-light ROMs. Active community. |
| 8 | **MSX / MSX2** | Konami gems: Metal Gear, Vampire Killer, Nemesis. WebMSX is excellent. |

### Phase 3 — Differentiation (2–3 months)
**Niche platforms = less competition = better SEO.**

| Priority | Platform | Why |
|---|---|---|
| 9 | **Neo Geo Pocket Color** | Hidden gem console. SNK vs Capcom, Metal Slug. Almost no competition online. |
| 10 | **PC Engine / TurboGrafx-16** | Cult following, being rediscovered. R-Type, Bomberman '93. |
| 11 | **Atari 2600** | The grandmother of consoles. ROMs of 2–32 KB. Historical value. |
| 12 | **MS-DOS** | js-dos is incredible. Prince of Persia, Doom, Commander Keen. Complex but rewarding. |

### Phase 4 — The Final Boss
**CD-based systems.** Feasible for small games, requires compression strategies for larger ones.

| Priority | Platform | Challenge |
|---|---|---|
| 13 | **PlayStation 1** | Needs BIOS + 50–700 MB ROMs. Works for small games (< 100 MB). |
| 14 | **Nintendo 64** | Unstable emulation. Cherry-pick compatible titles. |
| 15 | **Nintendo DS** | Dual screen UX challenge. Interesting technical problem. |

---

## 🔧 Universal Packer Vision

Instead of one packer per platform, the project could evolve into a **universal packer** powered by [EmulatorJS](https://emulatorjs.org/) (RetroArch cores compiled to WebAssembly):

```bash
# One tool to rule them all
python pack_game.py --system nes "Super Mario Bros.nes"
python pack_game.py --system snes "Chrono Trigger.smc"
python pack_game.py --system genesis "Sonic The Hedgehog.md"
python pack_game.py --system gb "Pokemon Red.gb"
python pack_game.py --system gba "Advance Wars.gba"
python pack_game.py --system c64 "Maniac Mansion.d64"
python pack_game.py --system psx "Crash Bandicoot.bin"
```

### Architecture

```
pack_game.py
├── --system <platform>          # Target system (nes, snes, gb, gba, genesis, etc.)
├── --rom <file>                 # ROM or disk image path
├── --title <name>               # Game title (displayed in the HTML page)
├── --cache                      # Enable IndexedDB caching (for large files)
├── --touch-controls             # Add on-screen touch controls for mobile
├── --theme <dark|light|retro>   # Visual theme for the player UI
└── output: game.html            # Single standalone HTML file
```

### How it would work internally

1. **Read ROM file** and base64-encode it (or compress for large files)
2. **Fetch the correct EmulatorJS core** (WASM) for the target platform
3. **Inline everything** into a single HTML template:
   - Emulator core (WASM + JS loader)
   - ROM data (base64)
   - UI shell (controls, fullscreen, save states)
   - Touch controls (mobile)
4. **Output one HTML file** — portable, offline, permanent

This single tool would instantly support **30+ retro platforms** with consistent UX.

---

## 🔬 Technical Considerations

### File Size Management

| ROM Size | Strategy | Example |
|---|---|---|
| < 1 MB | Direct base64 embed | NES, Game Boy, Atari 2600 |
| 1–32 MB | Base64 + gzip compression | SNES, GBA, Mega Drive |
| 32–100 MB | Compressed embed + streaming decompression | N64, small PS1 games |
| > 100 MB | Split into chunks or use IndexedDB caching | Large PS1, PSP (not recommended for single-file) |

### BIOS Requirements

Some systems require BIOS files to boot:

| System | BIOS Required? | Notes |
|---|---|---|
| NES, SNES, GB, GBA, Genesis | ❌ No | Just ROM + emulator |
| PlayStation | ✅ Yes | Legal gray area — user must provide their own |
| Sega CD | ✅ Yes | Region-specific BIOS needed |
| Sega Saturn | ✅ Yes | BIOS required |
| Nintendo DS | ⚠️ Optional | melonDS can boot without BIOS for most games |

### Browser Compatibility

All EmulatorJS cores work in:
- ✅ Chrome / Chromium (desktop + mobile)
- ✅ Firefox (desktop + mobile)
- ✅ Safari (macOS + iOS 15+)
- ✅ Edge
- ⚠️ Older mobile browsers may struggle with N64/PS1 emulation

### Performance Expectations

| Tier | Platforms | Performance |
|---|---|---|
| Smooth (60 FPS) | NES, GB, GBC, SMS, Atari, ColecoVision | Any device |
| Good (50–60 FPS) | SNES, Genesis, GBA, PCE | Any modern device |
| Acceptable (30–60 FPS) | N64, PS1, DS | Desktop + recent phones |
| Variable | PSP, Saturn | Desktop only, not all games |

---

## 📚 Resources

- [EmulatorJS](https://emulatorjs.org/) — RetroArch cores compiled to WebAssembly
- [EmulatorJS GitHub](https://github.com/EmulatorJS/EmulatorJS) — Open source, self-hostable
- [js-dos](https://js-dos.com/) — DOS emulation in the browser
- [apple2js](https://github.com/nickg/apple2js) — Apple II emulator in JavaScript
- [vAmigaWeb](https://vamiganet.github.io/vAmiga/) — Amiga emulation in WebAssembly
- [WebMSX](https://webmsx.org/) — MSX emulator in JavaScript
- [JSSpeccy](https://jsspeccy.zxdemo.org/) — ZX Spectrum emulator in JavaScript

---

*This document is part of the [portable-retro-games](https://github.com/aciderix/portable-retro-games) project — turning retro game disk images into standalone, offline-playable HTML files.*
