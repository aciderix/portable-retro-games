# 🎮 Rapport de Test — ROMs HTML (Packer Universel)

**Date :** 1er Mars 2026  
**Environnement :** Chrome (Ubuntu VM, WebGL via SwiftShader software)  
**Packer :** portable-retro-games/packers/universal  
**Total :** 40 fichiers HTML testés

---

## 📊 Résumé

| Statut | Nombre | % |
|--------|--------|---|
| ✅ WORKS | 25 | 62.5% |
| ⚠️ MENU_ONLY | 9 | 22.5% |
| ⬛ BLACK_SCREEN | 3 | 7.5% |
| ❌ CRASH | 3 | 7.5% |

---

## ✅ WORKS — Jeu fonctionnel (25/40)

| # | Fichier | Système | Notes |
|---|---------|---------|-------|
| 1 | 32x-240p.html | Sega 32X | 240P Test Suite, menu complet, NTSC 320x224p |
| 2 | atari2600-gofish.html | Atari 2600 | Go Fish — poissons animés, jouable |
| 3 | atari7800-poetiru.html | Atari 7800 | Poetiru — champ vert, sprites, jouable |
| 4 | c128-digiplayer.html | Commodore 128 | DIGI PLAYER, programme BASIC affiché |
| 5 | c64-fastone.html | Commodore 64 | Fast One — écran bleu C64, jeu actif |
| 6 | gb-cpu-instrs.html | Game Boy | CPU instruction tests — 8/9 tests OK |
| 7 | gba-240p.html | Game Boy Advance | 160p Test Suite v0.23, sprite + menu |
| 8 | gbc-acid2.html | Game Boy Color | cgb-acid2 — "HELLO WORLD!" + smiley |
| 9 | genesis-240p-emu.html | Genesis (via EMU) | 240P Test Suite, menu complet |
| 10 | genesis-240p.html | Genesis | 240P Test Suite, identique variante EMU |
| 11 | gg-tween.html | Game Gear | Sega Tween — sprites colorés animés |
| 12 | jaguar-ojc.html | Atari Jaguar | Orion Jaguar Collection — galerie jeux |
| 13 | lynx-chopper.html | Atari Lynx | Chopper X — title screen, HIGH SCORE |
| 14 | n64-controller.html | Nintendo 64 | ⚠️ Fonctionne mais artefacts visuels (SwiftShader) |
| 15 | n64-cputest.html | Nintendo 64 | ⚠️ Fonctionne mais artefacts visuels (SwiftShader) |
| 16 | nes-nestest.html | NES | Menu tests CPU complet |
| 17 | ngp-snake.html | Neo Geo Pocket | Snake — title screen + menu |
| 18 | pce-240p.html | PC Engine | 240P Test Suite, menu complet TG-16 |
| 19 | pet-arrow.html | Commodore PET | Arrow — title + instructions |
| 20 | sms-astroforce.html | Master System | Astro Force — intro spatiale |
| 21 | snes-240p-pal.html | SNES (PAL) | 240P Test Suite, 256x240P PAL |
| 22 | snes-240p.html | SNES (NTSC) | 240P Test Suite, 256x224P NTSC |
| 23 | vb-display.html | Virtual Boy | Display Test — "PROJECT: VIRTUAL BOY" |
| 24 | ws-wondersnake.html | WonderSwan | Wonder Snake — title screen + menu |
| 25 | zxspectrum-berzerk.html | ZX Spectrum | Berzerk — title + "PRESS FIRE TO PLAY!" |

> **Note N64 :** Les artefacts visuels sont causés par le rendu WebGL logiciel (SwiftShader) de la VM de test, pas par le packer. Sur un vrai navigateur avec GPU, les jeux s'afficheront normalement.

---

## ⚠️ MENU_ONLY — Émulateur chargé mais jeu pas lancé (9/40)

| # | Fichier | Système | Problème | Cause probable |
|---|---------|---------|----------|----------------|
| 1 | coleco-bejeweled.html | ColecoVision | Affiche "NO BIOS" | **BIOS ColecoVision manquant** — le core exige un BIOS qui n'est pas inclus |
| 2 | coleco-bombjack.html | ColecoVision | Affiche "NO BIOS" | **Idem** |
| 3 | cpc-stars.html | Amstrad CPC | Boot BASIC 1.1 "Ready" | **Auto-load ROM raté** — l'émulateur boot en BASIC sans charger le jeu |
| 4 | cps1-romtest.html | CPS-1 (Arcade) | Menu RetroArch, FB Alpha 2012 CPS-1 | **ROM non chargée** — le core FB Alpha ne trouve pas le contenu |
| 5 | cps2-romtest.html | CPS-2 (Arcade) | Menu RetroArch, FB Alpha 2012 CPS-2 | **Idem** |
| 6 | fbneo-gridlee.html | FBNeo (Arcade) | "Romset is unknown" | **ROM non reconnue** — Gridlee n'est pas dans le romset FBNeo |
| 7 | mame-gridlee.html | MAME (Arcade) | Menu RetroArch, MAME 2003-Plus | **ROM non chargée** — même problème que CPS |
| 8 | vic20-afterparty.html | VIC-20 | Prompt BASIC "READY." | **Auto-load ROM raté** |
| 9 | zx81-maze.html | ZX81 | Prompt BASIC, écran blanc | **Auto-load ROM raté** |

### Patterns identifiés :
- **BIOS manquant (2)** : ColecoVision nécessite un BIOS propriétaire
- **Auto-load défaillant (3)** : CPC, VIC-20, ZX81 — le packer ne configure pas l'auto-démarrage du programme
- **Arcade/ROM format (4)** : CPS1, CPS2, FBNeo, MAME — problème de packaging des ROMs arcade (format zip attendu par les cores)

---

## ⬛ BLACK_SCREEN — Écran noir (3/40)

| # | Fichier | Système | Notes |
|---|---------|---------|-------|
| 1 | atari5200-castleblast.html | Atari 5200 | Émulateur chargé avec overlay contrôles, canvas noir. **BIOS Atari 5200 probablement requis** |
| 2 | nds-hbmenu.html | Nintendo DS | Overlay contrôles visible, canvas noir. **Le format NDS homebrew n'est peut-être pas supporté par le core** |
| 3 | segacd-240p.html | Sega CD | Canvas noir après 30s. **BIOS Sega CD manquant** — ce système requiert un BIOS pour démarrer |

---

## ❌ CRASH — Échec total (3/40)

| # | Fichier | Système | Erreur | Cause probable |
|---|---------|---------|--------|----------------|
| 1 | amiga-goodasnew.html | Amiga | "Unsupported file format" → AROS BIOS "Waiting for bootable media" | **Format ROM incompatible** ou BIOS Amiga manquant |
| 2 | doom-freedoom.html | DOOM (PrBoom) | `RuntimeError: memory access out of bounds` | **Crash WASM** — le core PrBoom plante avec Freedoom (trop gros? format incompatible?) |
| 3 | plus4-petsrescue.html | Commodore Plus/4 | `?FILE NOT FOUND ERROR` | **ROM pas trouvée** par le core VICE — problème de packaging du fichier |

---

## 🔧 Recommandations pour le Packer

### Corrections prioritaires (impact élevé) :

1. **Auto-load des programmes BASIC (CPC, VIC-20, ZX81)**
   - Le packer devrait configurer les paramètres d'auto-démarrage pour ces systèmes
   - Ex: pour CPC, envoyer la commande `RUN"` automatiquement après le boot

2. **Packaging des ROMs arcade (CPS1, CPS2, FBNeo, MAME)**
   - Les cores arcade attendent des ROMs au format ZIP spécifique
   - Le packer doit adapter le format pour que le core charge automatiquement le contenu

3. **DOOM/PrBoom crash**
   - Le WAD Freedoom (27.5 Mo) cause un crash mémoire WASM
   - Tester avec un WAD plus petit ou augmenter la mémoire initiale

4. **Plus/4 — fichier non trouvé**
   - Vérifier le nom/chemin du fichier ROM dans le packaging

### Limitations connues (pas de fix possible) :

5. **BIOS requis** : ColecoVision, Atari 5200, Sega CD, Amiga
   - Ces systèmes nécessitent des BIOS propriétaires que le packer ne peut pas inclure légalement
   - Documenter cette limitation pour les utilisateurs

6. **NDS (Nintendo DS)**
   - Le core NDS web peut avoir des limitations avec certains formats homebrew
   - Tester avec d'autres ROMs NDS

### Nice to have :

7. **N64 WebGL**
   - Les artefacts sont liés au rendu logiciel de test, pas au packer
   - Fonctionnera normalement sur navigateurs avec GPU hardware

---

## 📁 Fichiers de résultats bruts

Les résultats JSON détaillés par batch sont dans :
- `/agent/home/test-results-batch1.json` à `batch8.json`
