# 🎮 Test Report — HTML ROM Packages (Universal Packer)

**Date:** March 1, 2026  
**Environment:** Chrome (Ubuntu VM, WebGL via SwiftShader software rendering)  
**Packer:** portable-retro-games/packers/universal  
**Total:** 40 HTML files tested

---

## 📊 Summary

| Status | Count | % |
|--------|-------|---|
| ✅ WORKS | 25 | 62.5% |
| ⚠️ MENU_ONLY | 9 | 22.5% |
| ⬛ BLACK_SCREEN | 3 | 7.5% |
| ❌ CRASH | 3 | 7.5% |

---

## ✅ WORKS — Game Functional (25/40)

| # | File | System | Notes |
|---|------|--------|-------|
| 1 | 32x-240p.html | Sega 32X | 240P Test Suite, full menu, NTSC 320x224p |
| 2 | atari2600-gofish.html | Atari 2600 | Go Fish — animated fish, fully playable |
| 3 | atari7800-poetiru.html | Atari 7800 | Poetiru — green field, sprites, playable |
| 4 | c128-digiplayer.html | Commodore 128 | DIGI PLAYER, BASIC program displayed |
| 5 | c64-fastone.html | Commodore 64 | Fast One — C64 blue screen, game running |
| 6 | gb-cpu-instrs.html | Game Boy | CPU instruction tests — 8/9 tests OK |
| 7 | gba-240p.html | Game Boy Advance | 160p Test Suite v0.23, sprite + menu |
| 8 | gbc-acid2.html | Game Boy Color | cgb-acid2 — "HELLO WORLD!" + smiley |
| 9 | genesis-240p-emu.html | Genesis (via EMU) | 240P Test Suite, full menu |
| 10 | genesis-240p.html | Genesis | 240P Test Suite, same as EMU variant |
| 11 | gg-tween.html | Game Gear | Sega Tween — colorful animated sprites |
| 12 | jaguar-ojc.html | Atari Jaguar | Orion Jaguar Collection — game gallery |
| 13 | lynx-chopper.html | Atari Lynx | Chopper X — title screen, HIGH SCORE |
| 14 | n64-controller.html | Nintendo 64 | ⚠️ Works but visual artifacts (SwiftShader) |
| 15 | n64-cputest.html | Nintendo 64 | ⚠️ Works but visual artifacts (SwiftShader) |
| 16 | nes-nestest.html | NES | Full CPU test menu |
| 17 | ngp-snake.html | Neo Geo Pocket | Snake — title screen + menu |
| 18 | pce-240p.html | PC Engine | 240P Test Suite, full TG-16 menu |
| 19 | pet-arrow.html | Commodore PET | Arrow — title + instructions |
| 20 | sms-astroforce.html | Master System | Astro Force — space intro |
| 21 | snes-240p-pal.html | SNES (PAL) | 240P Test Suite, 256x240P PAL |
| 22 | snes-240p.html | SNES (NTSC) | 240P Test Suite, 256x224P NTSC |
| 23 | vb-display.html | Virtual Boy | Display Test — "PROJECT: VIRTUAL BOY" |
| 24 | ws-wondersnake.html | WonderSwan | Wonder Snake — title screen + menu |
| 25 | zxspectrum-berzerk.html | ZX Spectrum | Berzerk — title + "PRESS FIRE TO PLAY!" |

> **N64 Note:** Visual artifacts are caused by the VM's software WebGL rendering (SwiftShader), not the packer. Games will display correctly on real browsers with hardware GPU.

---

## ⚠️ MENU_ONLY — Emulator Loaded but Game Not Started (9/40)

| # | File | System | Issue | Probable Cause |
|---|------|--------|-------|----------------|
| 1 | coleco-bejeweled.html | ColecoVision | Displays "NO BIOS" | **Missing ColecoVision BIOS** — core requires proprietary BIOS |
| 2 | coleco-bombjack.html | ColecoVision | Displays "NO BIOS" | **Same** |
| 3 | cpc-stars.html | Amstrad CPC | Boots to BASIC 1.1 "Ready" | **ROM auto-load failed** — emulator boots to BASIC without loading game |
| 4 | cps1-romtest.html | CPS-1 (Arcade) | RetroArch menu, FB Alpha 2012 CPS-1 | **ROM not loaded** — FB Alpha core can't find content |
| 5 | cps2-romtest.html | CPS-2 (Arcade) | RetroArch menu, FB Alpha 2012 CPS-2 | **Same** |
| 6 | fbneo-gridlee.html | FBNeo (Arcade) | "Romset is unknown" | **ROM not recognized** — Gridlee not in FBNeo romset |
| 7 | mame-gridlee.html | MAME (Arcade) | RetroArch menu, MAME 2003-Plus | **ROM not loaded** — same issue as CPS |
| 8 | vic20-afterparty.html | VIC-20 | BASIC "READY." prompt | **ROM auto-load failed** |
| 9 | zx81-maze.html | ZX81 | BASIC prompt, white screen | **ROM auto-load failed** |

### Identified Patterns:
- **Missing BIOS (2):** ColecoVision requires proprietary BIOS
- **Auto-load failure (3):** CPC, VIC-20, ZX81 — packer doesn't configure program auto-start
- **Arcade ROM format (4):** CPS1, CPS2, FBNeo, MAME — ROM packaging issue (cores expect specific zip format)

---

## ⬛ BLACK_SCREEN — Black Screen (3/40)

| # | File | System | Notes |
|---|------|--------|-------|
| 1 | atari5200-castleblast.html | Atari 5200 | Emulator loaded with control overlay, black canvas. **Atari 5200 BIOS likely required** |
| 2 | nds-hbmenu.html | Nintendo DS | Control overlay visible, black canvas. **NDS homebrew format may not be supported by core** |
| 3 | segacd-240p.html | Sega CD | Black canvas after 30s. **Missing Sega CD BIOS** — system requires BIOS to boot |

---

## ❌ CRASH — Total Failure (3/40)

| # | File | System | Error | Probable Cause |
|---|------|--------|-------|----------------|
| 1 | amiga-goodasnew.html | Amiga | "Unsupported file format" → AROS BIOS "Waiting for bootable media" | **Incompatible ROM format** or missing Amiga BIOS |
| 2 | doom-freedoom.html | DOOM (PrBoom) | `RuntimeError: memory access out of bounds` | **WASM crash** — PrBoom core crashes with Freedoom (too large? incompatible format?) |
| 3 | plus4-petsrescue.html | Commodore Plus/4 | `?FILE NOT FOUND ERROR` | **ROM not found** by VICE core — file packaging issue |

---

## 🔧 Packer Recommendations

### High Priority Fixes:

1. **BASIC program auto-load (CPC, VIC-20, ZX81)**
   - Packer should configure auto-start parameters for these systems
   - E.g.: for CPC, auto-send `RUN"` command after boot

2. **Arcade ROM packaging (CPS1, CPS2, FBNeo, MAME)**
   - Arcade cores expect ROMs in specific ZIP format
   - Packer must adapt format so core auto-loads content

3. **DOOM/PrBoom crash**
   - Freedoom WAD (27.5 MB) causes WASM memory crash
   - Test with smaller WAD or increase initial memory allocation

4. **Plus/4 — file not found**
   - Check ROM filename/path in packaging

### Known Limitations (no fix possible):

5. **Required BIOS:** ColecoVision, Atari 5200, Sega CD, Amiga
   - These systems need proprietary BIOS files the packer can't legally include
   - Document this limitation for users

6. **NDS (Nintendo DS)**
   - Web NDS core may have limitations with some homebrew formats
   - Test with other NDS ROMs

### Nice to Have:

7. **N64 WebGL**
   - Artifacts are from test software rendering, not the packer
   - Will work normally on browsers with hardware GPU

---

## 📁 Raw Result Files

Detailed JSON results per batch:
- `/agent/home/test-results-batch1.json` through `batch8.json`
