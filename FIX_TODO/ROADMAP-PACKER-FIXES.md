# 🗺️ Packer Fix Roadmap — Universal HTML Packer

**Baseline:** 25/40 working (62.5%) → **Target: 34/40 (85%)**  
**Last updated:** March 1, 2026

---

## Issue Type 1: BASIC Auto-Load Failure
**Impact:** 3 systems broken | **Difficulty:** 🟢 Easy  
**Pattern:** Emulator boots to BASIC prompt instead of running the ROM

### Affected Files
- [ ] `cpc-stars.html` — Amstrad CPC → boots to "Amstrad 128K Microcomputer" BASIC 1.1
- [ ] `vic20-afterparty.html` — VIC-20 → boots to "READY." prompt
- [ ] `zx81-maze.html` — ZX81 → boots to white screen with cursor

### Root Cause
The packer loads the ROM file but doesn't configure the emulator core to auto-execute it. These 8-bit home computers boot to BASIC by default — they need an explicit "run this program" command.

### Solution Leads
1. **RetroArch core options** — Each core has `autostart` or `autoload` options:
   - **CPC (cap32):** Set `cap32_autorun = enabled` in core options, or use `RUN"` command injection
   - **VIC-20 (vice_xvic):** Set `vice_xvic_autostart = enabled` or pass `-autostart` flag
   - **ZX81 (81):** Set `81_auto_load = enabled` or inject `LOAD ""` then `RUN`
2. **Packer script change:** In the universal packer, add per-system core option overrides in the generated HTML's RetroArch config block
3. **Alternative:** Use a system-specific `retroarch.cfg` snippet embedded in the HTML with the correct autostart settings

### Validation
After fix: each game should reach its title screen or gameplay without manual BASIC commands.

---

## Issue Type 2: Arcade ROM Packaging
**Impact:** 4 systems broken | **Difficulty:** 🟡 Medium  
**Pattern:** RetroArch loads to main menu or core reports "romset unknown"

### Affected Files
- [ ] `cps1-romtest.html` — CPS-1, FB Alpha 2012 CPS-1 core → stuck at RetroArch menu
- [ ] `cps2-romtest.html` — CPS-2, FB Alpha 2012 CPS-2 core → stuck at RetroArch menu
- [ ] `fbneo-gridlee.html` — FBNeo core → "Romset is unknown"
- [ ] `mame-gridlee.html` — MAME 2003-Plus core → stuck at RetroArch menu

### Root Cause
Arcade emulator cores (FB Alpha, FBNeo, MAME) expect ROMs as **named ZIP files** matching their internal romset database. The packer likely:
- Extracts or renames the ROM files, breaking the expected naming
- Doesn't place the ZIP in the correct virtual filesystem path
- Doesn't pass the correct content path to the core on launch

### Solution Leads
1. **Keep ROMs as ZIP** — Don't extract arcade ROM ZIPs. Pass them as-is to the core
2. **Correct naming** — The ZIP filename MUST match the romset name (e.g., `gridlee.zip` for Gridlee)
3. **Virtual filesystem path** — Arcade cores look for ROMs in specific directories. Ensure the packer mounts the ZIP at `/home/web_user/retroarch/userdata/content/` or the equivalent path
4. **Content loading** — Use RetroArch's `--content` flag pointing to the ZIP, not extracted files
5. **FBNeo vs MAME** — Gridlee might only work on specific core versions. Check which romset version each core expects:
   - MAME 2003-Plus: MAME 0.78 romset
   - FBNeo: latest FBNeo romset
   - FB Alpha 2012: MAME 0.139 romset

### Validation
After fix: game should auto-boot past the RetroArch menu directly to gameplay.

---

## Issue Type 3: Missing BIOS (Legal Limitation)
**Impact:** 4 systems broken | **Difficulty:** 🔴 Hard (legal constraint)  
**Pattern:** "NO BIOS", black screen, or boot screen waiting for media

### Affected Files
- [ ] `coleco-bejeweled.html` — ColecoVision → "NO BIOS"
- [ ] `coleco-bombjack.html` — ColecoVision → "NO BIOS"
- [ ] `atari5200-castleblast.html` — Atari 5200 → black screen
- [ ] `segacd-240p.html` — Sega CD → black screen

### Root Cause
These systems require proprietary BIOS files to boot. The cores cannot run any ROM without them. The packer cannot legally bundle these BIOS files.

### Solution Leads
1. **Open-source BIOS replacements:**
   - **ColecoVision:** There's an open-source BIOS alternative — check if the core accepts it. Some projects have HLE (High-Level Emulation) BIOS
   - **Atari 5200:** Look into `Altirra` open-source BIOS replacement (Altirra OS). Check if the a5200 core supports it
   - **Sega CD:** No known open-source replacement. May need to document as unsupported
2. **User-supplied BIOS:** Add a "drop your BIOS here" feature in the HTML player so users can provide their own legally-dumped BIOS
3. **Core-level HLE:** Some cores have built-in HLE BIOS options — check core settings for `use_bios = hle` or similar
4. **Documentation:** If no fix is possible, clearly mark these systems as "requires user BIOS" in the packer output

### Validation
After fix: ColecoVision games should reach title screen. Atari 5200 and Sega CD at minimum should not black-screen.

---

## Issue Type 4: WASM/Core Crashes
**Impact:** 2 files broken | **Difficulty:** 🟡 Medium  
**Pattern:** JavaScript/WASM runtime errors prevent game from starting

### Affected Files
- [ ] `doom-freedoom.html` — PrBoom core → `RuntimeError: memory access out of bounds`
- [ ] `plus4-petsrescue.html` — VICE Plus/4 core → `?FILE NOT FOUND ERROR`

### Root Cause
- **DOOM:** The Freedoom WAD (27.5 MB) likely exceeds the default WASM memory allocation. The PrBoom core runs out of memory during initialization.
- **Plus/4:** The VICE core can't find the ROM file — the packer likely places it at a path the core doesn't search, or the filename doesn't match what VICE expects.

### Solution Leads
#### DOOM
1. **Increase WASM memory** — In the generated HTML, set `Module.INITIAL_MEMORY` or equivalent to 128MB+ (default may be 16MB)
2. **Use smaller WAD** — Try Freedoom Phase 1 only instead of the full package
3. **Core swap** — Try a different DOOM core if PrBoom can't handle the memory
4. **Check packer memory settings** — The universal packer may have a configurable memory limit

#### Plus/4
1. **Check filename mapping** — VICE expects specific file extensions (.prg, .d64, .t64). Ensure the ROM file keeps its original extension
2. **VICE autostart** — Set `vice_plus4_autostart = enabled` in core options
3. **Virtual filesystem** — Ensure the ROM file is mounted where VICE looks for it

### Validation
- DOOM: Freedoom title screen with menu should appear
- Plus/4: Game should auto-load and reach title/gameplay

---

## Issue Type 5: Emulator Core Compatibility
**Impact:** 2 files broken | **Difficulty:** 🟠 Medium-Hard  
**Pattern:** Core loads but can't handle the specific ROM/format

### Affected Files
- [ ] `amiga-goodasnew.html` — Amiga (PUAE core) → "Unsupported file format", boots to AROS
- [ ] `nds-hbmenu.html` — NDS (DeSmuME/melonDS) → black screen

### Root Cause
- **Amiga:** The PUAE core may not support the ROM file format, or it needs a Kickstart BIOS (proprietary). The fallback AROS replacement BIOS doesn't support all software.
- **NDS:** The homebrew menu (hbmenu.nds) may require specific NDS firmware/BIOS or use features the web core doesn't support.

### Solution Leads
#### Amiga
1. **Check ROM format** — Ensure it's an ADF or HDF file. IPF and other formats may not be supported
2. **AROS limitations** — AROS is not 100% compatible. Some games won't work without official Kickstart
3. **Try different ROM** — Test with a known-working Amiga homebrew in ADF format
4. **Document** — Amiga emulation on web is limited; may need to mark as "partial support"

#### NDS
1. **Try different homebrew** — hbmenu is a launcher, not a game. Try a standalone NDS homebrew game instead
2. **Core settings** — Check if the NDS core needs specific boot settings or firmware
3. **BIOS files** — NDS cores often need `bios7.bin`, `bios9.bin`, and `firmware.bin`

### Validation
- Amiga: Game should load past AROS screen to actual gameplay
- NDS: Visual output should appear on the canvas

---

## 📈 Progress Tracker

### By Priority

| Priority | Issues | Files | Estimated Fix |
|----------|--------|-------|---------------|
| 🟢 P1 — Easy wins | BASIC auto-load | 3 | Core config tweak |
| 🟡 P2 — Medium effort | Arcade ROM format | 4 | Packer logic change |
| 🟡 P2 — Medium effort | WASM crashes | 2 | Memory config + path fix |
| 🟠 P3 — Hard | Core compatibility | 2 | ROM format / alt ROM |
| 🔴 P4 — Legal blocker | Missing BIOS | 4 | Open-source BIOS or user-supplied |

### Quick Wins (fix these first)
1. ✨ CPC, VIC-20, ZX81 auto-load → just add core options in packer
2. ✨ Plus/4 file not found → fix ROM path/naming in packer
3. ✨ DOOM memory → increase WASM initial memory

### Scorecard

| Milestone | Score | Status |
|-----------|-------|--------|
| Current baseline | 25/40 (62.5%) | ✅ Tested |
| After auto-load fixes | 28/40 (70%) | ⬜ TODO |
| After arcade fixes | 32/40 (80%) | ⬜ TODO |
| After crash fixes | 34/40 (85%) | ⬜ TODO |
| After BIOS solutions | 36-38/40 (90-95%) | ⬜ Stretch goal |

---

## 🧪 Test Environment Notes

- **VM:** Ubuntu, Chrome, no GPU → WebGL via SwiftShader (software)
- **N64 artifacts** are VM-only, not a packer bug (will look fine with real GPU)
- All tests done with DevTools Console open to catch errors
- 40 HTML files generated by universal packer from legal test ROMs (homebrews, 240p Test Suite, open-source)
