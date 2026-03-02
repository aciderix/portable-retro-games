# 🎮 Rapport de Tests EmulatorJS — pack_game (5).py

> **Date** : 2 mars 2026
> **Jeux testés** : 64 (2 par système × 32 systèmes)
> **Méthode** : Test manuel sur Android (Chrome 145, ARM Mali-G57 MC2, WebGL 2.0)
> **Outil** : HTML autonomes générés par `pack_game (5).py` avec EmulatorJS + cores RetroArch

---

## 📊 Résumé Global

| Métrique | Valeur |
|:---|:---|
| **Jeux testés** | 64 |
| **✅ Fonctionnels** | **23** (35%) |
| **⚠️ Autorun Fail (Menu)** | 11 |
| **⚠️ Autorun Fail (Boot)** | 11 |
| **❌ Écran Noir** | 9 |
| **❌ Écran Corrompu** | 4 |
| **💥 Crash** | 4 |
| **🔧 BIOS Manquant** | 2 |

### Verdict par Système

| # | Système | Core | Verdict | Détails |
|:--|:---|:---|:---|:---|
| 01 | **NES / Famicom** | `fceumm` | ✅ FONCTIONNEL | ✅ 1200 in 1 (J) [p1], ✅ Super Mario Bros. 3 |
| 02 | **Super Nintendo** | `snes9x` | ✅ FONCTIONNEL | ✅ Donkey Kong Country (U) (, ✅ Super Mario World (U) [!] |
| 03 | **Game Boy** | `gambatte` | ✅ FONCTIONNEL | ✅ Pokemon: Blue Version, ✅ Pokemon: Red Version |
| 04 | **Game Boy Color** | `gambatte` | ✅ FONCTIONNEL | ✅ Pokemon: Crystal Version, ✅ Pokemon: Silver Version |
| 05 | **Game Boy Advance** | `mgba` | ✅ FONCTIONNEL | ✅ Pokemon: FireRed Version, ✅ Pokemon   Emerald Version |
| 06 | **Nintendo 64** | `mupen64plus_next` | ✅ FONCTIONNEL | ✅ Mario Kart 64, ✅ Super Mario 64 |
| 07 | **Virtual Boy** | `beetle_vb` | ❌ NON FONCTIONNEL | 💥 Mario, ⚠️ Virtual Boy Wario Land (J |
| 08 | **Sega Genesis / Mega Drive** | `genesis_plus_gx` | ✅ FONCTIONNEL | ✅ Sonic The Hedgehog 2 (Wor, ✅ Sonic The Hedgehog (USA,  |
| 09 | **Sega Master System** | `smsplus` | ❌ NON FONCTIONNEL | ❌ Alex Kidd in Miracle Worl, ❌ Sonic Chaos |
| 10 | **Sega Game Gear** | `genesis_plus_gx` | ❌ NON FONCTIONNEL | ❌ Shinobi II   The Silent F, ❌ Sonic The Hedgehog   Trip |
| 11 | **Sega 32X** | `picodrive` | ❌ NON FONCTIONNEL | ❌ Doom, 💥 Knuckles |
| 12 | **PC Engine / TurboGrafx-16** | `mednafen_pce` | ✅ FONCTIONNEL | ✅ Splatterhouse (U) [h1], ✅ Super Mario Bros (J) [p1] |
| 13 | **Atari 2600** | `stella2014` | ✅ FONCTIONNEL | ✅ Mario Bros (1983) (Atari), ✅ Pac Man (1981) (Atari) |
| 14 | **Atari 5200** | `a5200` | ❌ NON FONCTIONNEL | ⚠️ Frogger (USA), ⚠️ Mario Bros. (USA) |
| 15 | **Atari 7800** | `prosystem` | ❌ NON FONCTIONNEL | ❌ Asteroids (USA), ❌ Ms. Pac Man (USA) |
| 16 | **Atari Lynx** | `handy` | ❌ NON FONCTIONNEL | ❌ Ninja Gaiden (1990), ❌ Tetris (1996) |
| 17 | **Atari Jaguar** | `virtualjaguar` | ❌ NON FONCTIONNEL | ❌ Alien vs Predator (World), ❌ Rayman (World) |
| 18 | **Neo Geo Pocket / Color** | `mednafen_ngp` | ❌ NON FONCTIONNEL | ❌ Metal Slug   1st Mission , ❌ Sonic the Hedgehog   Pock |
| 19 | **WonderSwan / Color** | `mednafen_wswan` | ❌ NON FONCTIONNEL | ⚠️ Hunter X Hunter   Greed I, ⚠️ Saint Seiya   Ougon Dense |
| 20 | **ColecoVision** | `gearcoleco` | ❌ NON FONCTIONNEL | 🔧 Burgertime (1984)(Coleco), 🔧 Donkey Kong (1982)(Coleco |
| 21 | **Commodore 64** | `vice_x64sc` | ❌ NON FONCTIONNEL | ⚠️ Bruce Lee (USA, Europe), ⚠️ Sex Games |
| 22 | **Commodore VIC-20** | `vice_xvic` | ⚠️ PARTIEL | ⚠️ Donkey Kong (Japan, USA), ✅ Pac Man (World) |
| 23 | **Commodore PET** | `vice_xpet` | ⚠️ PARTIEL | ⚠️ Bomber (19xx)( )(de), ✅ Space Invaders (19xx)( ) |
| 24 | **Commodore Plus/4** | `vice_xplus4` | ✅ FONCTIONNEL | ✅ Atomic Mission (USA, Euro, ✅ Jack Attack (USA, Europe) |
| 25 | **Amiga** | `puae` | ❌ NON FONCTIONNEL | ⚠️ Sex Vixens from Space Dis, 💥 Teenage Mutant Hero Turtl |
| 26 | **Amstrad CPC** | `cap32` | ❌ NON FONCTIONNEL | ⚠️ Fallout (UK) (1987), ⚠️ SEX   Sex Entertains Xeno |
| 27 | **ZX Spectrum** | `fuse` | ⚠️ PARTIEL | ✅ Jetpac (1983)(Ultimate Pl, 💥 Out Run (1988)(U.S. Gold) |
| 28 | **Sinclair ZX81** | `81` | ❌ NON FONCTIONNEL | ⚠️ Pacman (19xx)( ), ⚠️ Tekenen (19xx)( ) |
| 29 | **CPS1 (Capcom)** | `fbalpha2012_cps1` | ❌ NON FONCTIONNEL | ⚠️ Cadillacs and Dinosaurs (, ⚠️ Sf2 |
| 30 | **CPS2 (Capcom)** | `fbalpha2012_cps2` | ❌ NON FONCTIONNEL | ⚠️ Hyper Street Fighter II  , ⚠️ Marvel vs Capcom   clash  |
| 31 | **Neo Geo (Arcade)** | `fbneo` | ❌ NON FONCTIONNEL | ⚠️ King of Fighters 98, ⚠️ Neobombe |
| 32 | **MAME (Arcade)** | `mame2003_plus` | ❌ NON FONCTIONNEL | ⚠️ Pepsiman, ⚠️ Tekken5D |

> **10 systèmes fonctionnels** / 3 partiels / 19 non fonctionnels sur 32 testés

---

## 📋 Détails par Catégorie

### 🎮 Nintendo

#### NES / Famicom — `fceumm` — ✅ FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| 1200 in 1 (J) [p1] | ✅ Fonctionnel | — |
| Super Mario Bros. 3 | ✅ Fonctionnel | — |

#### Super Nintendo — `snes9x` — ✅ FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Donkey Kong Country (U) (V1.2) [!] | ✅ Fonctionnel | — |
| Super Mario World (U) [!] | ✅ Fonctionnel | — |

#### Game Boy — `gambatte` — ✅ FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Pokemon: Blue Version | ✅ Fonctionnel | — |
| Pokemon: Red Version | ✅ Fonctionnel | — |

#### Game Boy Color — `gambatte` — ✅ FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Pokemon: Crystal Version | ✅ Fonctionnel | — |
| Pokemon: Silver Version | ✅ Fonctionnel | — |

#### Game Boy Advance — `mgba` — ✅ FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Pokemon: FireRed Version | ✅ Fonctionnel | — |
| Pokemon   Emerald Version (USA, Europe) | ✅ Fonctionnel | — |

#### Nintendo 64 — `mupen64plus_next` — ✅ FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Mario Kart 64 | ✅ Fonctionnel | Rame |
| Super Mario 64 | ✅ Fonctionnel | Rame |

#### Virtual Boy — `beetle_vb` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Mario | 💥 Crash / Erreur Fatale | Bloqué à loading emulator engine |
| Virtual Boy Wario Land (Japan, USA) | ⚠️ Autorun Fail (Menu RetroArch) | — |

**Erreurs console (Mario)** :
- `promise_rejection`: ReferenceError: EJS_player is not defined

> **Bilan 🎮 Nintendo** : 12/14 jeux fonctionnels


### 🔵 Sega & NEC

#### Sega Genesis / Mega Drive — `genesis_plus_gx` — ✅ FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Sonic The Hedgehog 2 (World) (Rev A) | ✅ Fonctionnel | — |
| Sonic The Hedgehog (USA, Europe) | ✅ Fonctionnel | — |

#### Sega Master System — `smsplus` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Alex Kidd in Miracle World | ❌ Écran Noir | Emulateur chargé écran reste noir |
| Sonic Chaos | ❌ Écran Noir | Emulateur chargé écran reste noir |

#### Sega Game Gear — `genesis_plus_gx` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Shinobi II   The Silent Fury (U) [!] | ❌ Écran Noir | Emulateur chargé écran reste noir |
| Sonic The Hedgehog   Triple Trouble (U) [!] | ❌ Écran Noir | Emulateur chargé écran reste noir |

#### Sega 32X — `picodrive` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Doom | ❌ Écran Noir | Emulateur chargé écran reste noir |
| Knuckles | 💥 Crash / Erreur Fatale | Bloqué à loading emulator engine |

**Erreurs console (Knuckles)** :
- `promise_rejection`: ReferenceError: EJS_player is not defined

#### PC Engine / TurboGrafx-16 — `mednafen_pce` — ✅ FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Splatterhouse (U) [h1] | ✅ Fonctionnel | — |
| Super Mario Bros (J) [p1] | ✅ Fonctionnel | — |

> **Bilan 🔵 Sega & NEC** : 4/10 jeux fonctionnels


### 🕹️ Atari

#### Atari 2600 — `stella2014` — ✅ FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Mario Bros (1983) (Atari) | ✅ Fonctionnel | — |
| Pac Man (1981) (Atari) | ✅ Fonctionnel | — |

#### Atari 5200 — `a5200` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Frogger (USA) | ⚠️ Autorun Fail (Menu RetroArch) | — |
| Mario Bros. (USA) | ⚠️ Autorun Fail (Menu RetroArch) | — |

#### Atari 7800 — `prosystem` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Asteroids (USA) | ❌ Écran Noir | Emulateur chargé écran reste noir |
| Ms. Pac Man (USA) | ❌ Écran Noir | Emulateur chargé écran reste noir |

#### Atari Lynx — `handy` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Ninja Gaiden (1990) | ❌ Écran Corrompu | Emulateur chargé écran reste noir avec glitch ligne verte partie supérieure |
| Tetris (1996) | ❌ Écran Corrompu | Emulateur chargé écran reste noir avec glitch ligne verte partie supérieure de l'écran |

#### Atari Jaguar — `virtualjaguar` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Alien vs Predator (World) | ❌ Écran Corrompu | Emulateur chargé écran reste noir avec glitch ligne bleue partie supérieur de l'écran |
| Rayman (World) | ❌ Écran Corrompu | Emulateur chargé écran reste noir avec glitch ligne bleue partie supérieur de l'écran |

> **Bilan 🕹️ Atari** : 2/10 jeux fonctionnels


### 📱 Portables Autres

#### Neo Geo Pocket / Color — `mednafen_ngp` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Metal Slug   1st Mission (World) (En,Ja) | ❌ Écran Noir | Écran blanc |
| Sonic the Hedgehog   Pocket Adventure (World) (Demo) | ❌ Écran Noir | Écran blanc |

#### WonderSwan / Color — `mednafen_wswan` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Hunter X Hunter   Greed Island (J)(Independent) | ⚠️ Autorun Fail (Menu RetroArch) | — |
| Saint Seiya   Ougon Densetsu Hen Perfect Edition (J) | ⚠️ Autorun Fail (Menu RetroArch) | — |

> **Bilan 📱 Portables Autres** : 0/4 jeux fonctionnels


### 🖥️ Ordinateurs

#### ColecoVision — `gearcoleco` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Burgertime (1984)(Coleco) | 🔧 BIOS Manquant | — |
| Donkey Kong (1982)(Coleco) | 🔧 BIOS Manquant | — |

#### Commodore 64 — `vice_x64sc` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Bruce Lee (USA, Europe) | ⚠️ Autorun Fail (Boot Console) | — |
| Sex Games | ⚠️ Autorun Fail (Boot Console) | Ready load * 8 1 searching for * loading |

#### Commodore VIC-20 — `vice_xvic` — ⚠️ PARTIEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Donkey Kong (Japan, USA) | ⚠️ Autorun Fail (Boot Console) | — |
| Pac Man (World) | ✅ Fonctionnel | — |

#### Commodore PET — `vice_xpet` — ⚠️ PARTIEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Bomber (19xx)( )(de) | ⚠️ Autorun Fail (Boot Console) | BOMBERANGRIFF  ZIEL IST ES MIT DEM FLUGZEUG ZU LANDEN, DAZU MUESSEN ZUERST ABER DIE GEBAEUDE MIT BORDWAFFEN ZERSTOERT WERDEN.  BITTE WAEHLEN SIE  SCHWIERIGKEIT:  1 315 3 |
| Space Invaders (19xx)( ) | ✅ Fonctionnel | — |

#### Commodore Plus/4 — `vice_xplus4` — ✅ FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Atomic Mission (USA, Europe) | ✅ Fonctionnel | — |
| Jack Attack (USA, Europe) | ✅ Fonctionnel | — |

#### Amiga — `puae` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Sex Vixens from Space Disk1 | ⚠️ Autorun Fail (Boot Console) | Waiting for boot able media |
| Teenage Mutant Hero Turtles | 💥 Crash / Erreur Fatale | — |

#### Amstrad CPC — `cap32` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Fallout (UK) (1987) | ⚠️ Autorun Fail (Boot Console) | — |
| SEX   Sex Entertains Xenomorph (UK) (19xx) (PD) | ⚠️ Autorun Fail (Boot Console) | — |

#### ZX Spectrum — `fuse` — ⚠️ PARTIEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Jetpac (1983)(Ultimate Play The Game)[16K] | ✅ Fonctionnel | — |
| Out Run (1988)(U.S. Gold)[48 128K][SpeedLock 4] | 💥 Crash / Erreur Fatale | Jeu se lance premier écran affiché puis stoppé |

#### Sinclair ZX81 — `81` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Pacman (19xx)( ) | ⚠️ Autorun Fail (Boot Console) | Écran blanc avec juste marque 0/0 |
| Tekenen (19xx)( ) | ⚠️ Autorun Fail (Boot Console) | Écran blanc avec juste marqué 0/0 |

> **Bilan 🖥️ Ordinateurs** : 5/18 jeux fonctionnels


### 🎰 Arcade

#### CPS1 (Capcom) — `fbalpha2012_cps1` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Cadillacs and Dinosaurs (World 930201) | ⚠️ Autorun Fail (Menu RetroArch) | — |
| Sf2 | ⚠️ Autorun Fail (Menu RetroArch) | — |

#### CPS2 (Capcom) — `fbalpha2012_cps2` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Hyper Street Fighter II  The Anniversary Edition (0402 | ⚠️ Autorun Fail (Menu RetroArch) | — |
| Marvel vs Capcom   clash of super heroes (980123 USA) | ⚠️ Autorun Fail (Menu RetroArch) | — |

#### Neo Geo (Arcade) — `fbneo` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| King of Fighters 98 | ⚠️ Autorun Fail (Boot Console) | Fb néo error romset is unknow |
| Neobombe | ⚠️ Autorun Fail (Boot Console) | Fb néo error romset is unknow |

#### MAME (Arcade) — `mame2003_plus` — ❌ NON FONCTIONNEL

| Jeu | Statut | Notes |
|:---|:---|:---|
| Pepsiman | ⚠️ Autorun Fail (Menu RetroArch) | — |
| Tekken5D | ⚠️ Autorun Fail (Menu RetroArch) | — |

> **Bilan 🎰 Arcade** : 0/8 jeux fonctionnels

---

## 🔍 Analyse des Problèmes

### Par type de problème

#### ⚠️ Autorun Fail — Menu RetroArch (11 jeux)

Le core RetroArch se charge mais affiche le menu au lieu de lancer le jeu automatiquement.
**Systèmes affectés** : Atari 5200, CPS1 (Capcom), CPS2 (Capcom), MAME (Arcade), Virtual Boy, WonderSwan / Color

**Cause probable** : Le paramètre d'autostart n'est pas correctement configuré pour ces cores, ou le format de ROM n'est pas reconnu automatiquement.

**Correctif possible** : Ajouter des arguments RetroArch supplémentaires dans le script de packing, ou utiliser un core alternatif.

#### ⚠️ Autorun Fail — Boot Console Bloqué (11 jeux)

L'émulateur démarre, le système de la console s'initialise, mais le jeu ne se lance pas automatiquement (reste sur l'écran de boot, le prompt BASIC, ou un écran d'attente).
**Systèmes affectés** : Amiga, Amstrad CPC, Commodore 64, Commodore PET, Commodore VIC-20, Neo Geo (Arcade), Sinclair ZX81

**Cause probable** : Ces systèmes (ordinateurs 8-bit, arcade) nécessitent souvent une commande manuelle (`LOAD`, `RUN`) ou un BIOS spécifique pour autorun. Le packing en standalone ne fournit pas ces instructions de démarrage.

#### ❌ Écran Noir (9 jeux)

L'émulateur se charge (barre EmulatorJS visible) mais l'écran reste noir.
**Systèmes affectés** : Atari 7800, Neo Geo Pocket / Color, Sega 32X, Sega Game Gear, Sega Master System

**Cause probable** : Problème de rendu du core avec le canvas HTML5. Certains cores (smsplus, picodrive, prosystem) ont des problèmes de compatibilité avec EmulatorJS en mode standalone. Un BIOS manquant peut aussi causer un écran noir (SMS, GG).

#### ❌ Écran Corrompu (4 jeux)

Le rendu est cassé : lignes de couleur, glitches visuels sur fond noir.
**Systèmes affectés** : Atari Jaguar, Atari Lynx

**Cause probable** : Les cores `handy` (Lynx) et `virtualjaguar` (Jaguar) sont connus pour être instables dans EmulatorJS. Ces systèmes avancés nécessitent un rendu graphique complexe que l'émulation WebAssembly ne supporte pas bien.

#### 💥 Crash / Erreur Fatale (4 jeux)

Le jeu ne démarre pas du tout, bloqué au chargement ou crash du core.
**Systèmes/jeux affectés** :
- **Mario** (Virtual Boy) — Bloqué à loading emulator engine
- **Knuckles** (Sega 32X) — Bloqué à loading emulator engine
- **Teenage Mutant Hero Turtles** (Amiga) — Pas de détail
- **Out Run (1988)(U.S. Gold)[48 128K][SpeedLock 4]** (ZX Spectrum) — Jeu se lance premier écran affiché puis stoppé

#### 🔧 BIOS Manquant (2 jeux)

**Système** : ColecoVision (`gearcoleco`)

Le core ColecoVision nécessite un BIOS (`colecovision.rom`) qui n'est pas inclus dans le packing. Sans ce fichier, le core ne peut pas démarrer.

---

## 🏆 Classement de Fiabilité des Cores

| Rang | Core | Système(s) | Taux de Succès | Verdict |
|:--|:---|:---|:---|:---|
| 1 | `fceumm` | NES / Famicom | 2/2 (100%) | ✅ Parfait |
| 2 | `gambatte` | Game Boy, Game Boy Color | 4/4 (100%) | ✅ Parfait |
| 3 | `mednafen_pce` | PC Engine / TurboGrafx-16 | 2/2 (100%) | ✅ Parfait |
| 4 | `mgba` | Game Boy Advance | 2/2 (100%) | ✅ Parfait |
| 5 | `mupen64plus_next` | Nintendo 64 | 2/2 (100%) | ✅ Parfait |
| 6 | `snes9x` | Super Nintendo | 2/2 (100%) | ✅ Parfait |
| 7 | `stella2014` | Atari 2600 | 2/2 (100%) | ✅ Parfait |
| 8 | `vice_xplus4` | Commodore Plus/4 | 2/2 (100%) | ✅ Parfait |
| 9 | `fuse` | ZX Spectrum | 1/2 (50%) | ⚠️ Partiel |
| 10 | `genesis_plus_gx` | Sega Game Gear, Sega Genesis / Mega Drive | 2/4 (50%) | ⚠️ Partiel |
| 11 | `vice_xpet` | Commodore PET | 1/2 (50%) | ⚠️ Partiel |
| 12 | `vice_xvic` | Commodore VIC-20 | 1/2 (50%) | ⚠️ Partiel |
| 13 | `81` | Sinclair ZX81 | 0/2 (0%) | ❌ Échec |
| 14 | `a5200` | Atari 5200 | 0/2 (0%) | ❌ Échec |
| 15 | `beetle_vb` | Virtual Boy | 0/2 (0%) | ❌ Échec |
| 16 | `cap32` | Amstrad CPC | 0/2 (0%) | ❌ Échec |
| 17 | `fbalpha2012_cps1` | CPS1 (Capcom) | 0/2 (0%) | ❌ Échec |
| 18 | `fbalpha2012_cps2` | CPS2 (Capcom) | 0/2 (0%) | ❌ Échec |
| 19 | `fbneo` | Neo Geo (Arcade) | 0/2 (0%) | ❌ Échec |
| 20 | `gearcoleco` | ColecoVision | 0/2 (0%) | ❌ Échec |
| 21 | `handy` | Atari Lynx | 0/2 (0%) | ❌ Échec |
| 22 | `mame2003_plus` | MAME (Arcade) | 0/2 (0%) | ❌ Échec |
| 23 | `mednafen_ngp` | Neo Geo Pocket / Color | 0/2 (0%) | ❌ Échec |
| 24 | `mednafen_wswan` | WonderSwan / Color | 0/2 (0%) | ❌ Échec |
| 25 | `picodrive` | Sega 32X | 0/2 (0%) | ❌ Échec |
| 26 | `prosystem` | Atari 7800 | 0/2 (0%) | ❌ Échec |
| 27 | `puae` | Amiga | 0/2 (0%) | ❌ Échec |
| 28 | `smsplus` | Sega Master System | 0/2 (0%) | ❌ Échec |
| 29 | `vice_x64sc` | Commodore 64 | 0/2 (0%) | ❌ Échec |
| 30 | `virtualjaguar` | Atari Jaguar | 0/2 (0%) | ❌ Échec |

---

## 💡 Recommandations

### Systèmes recommandés pour distribution (fiables)

Ces systèmes fonctionnent parfaitement en HTML standalone et sont prêts pour une distribution :

- ✅ **NES / Famicom** (`fceumm`)
- ✅ **Super Nintendo** (`snes9x`)
- ✅ **Game Boy** (`gambatte`)
- ✅ **Game Boy Color** (`gambatte`)
- ✅ **Game Boy Advance** (`mgba`)
- ✅ **Nintendo 64** (`mupen64plus_next`)
- ✅ **Sega Genesis / Mega Drive** (`genesis_plus_gx`)
- ✅ **PC Engine / TurboGrafx-16** (`mednafen_pce`)
- ✅ **Atari 2600** (`stella2014`)
- ✅ **Commodore Plus/4** (`vice_xplus4`)

### Systèmes à éviter ou nécessitant un correctif

- ❌ **Virtual Boy** (`beetle_vb`) — Crash / Erreur Fatale, Autorun Fail (Menu RetroArch)
- ❌ **Sega Master System** (`smsplus`) — Écran Noir
- ❌ **Sega Game Gear** (`genesis_plus_gx`) — Écran Noir
- ❌ **Sega 32X** (`picodrive`) — Crash / Erreur Fatale, Écran Noir
- ❌ **Atari 5200** (`a5200`) — Autorun Fail (Menu RetroArch)
- ❌ **Atari 7800** (`prosystem`) — Écran Noir
- ❌ **Atari Lynx** (`handy`) — Écran Corrompu
- ❌ **Atari Jaguar** (`virtualjaguar`) — Écran Corrompu
- ❌ **Neo Geo Pocket / Color** (`mednafen_ngp`) — Écran Noir
- ❌ **WonderSwan / Color** (`mednafen_wswan`) — Autorun Fail (Menu RetroArch)
- ❌ **ColecoVision** (`gearcoleco`) — BIOS Manquant
- ❌ **Commodore 64** (`vice_x64sc`) — Autorun Fail (Boot Console)
- ❌ **Amiga** (`puae`) — Crash / Erreur Fatale, Autorun Fail (Boot Console)
- ❌ **Amstrad CPC** (`cap32`) — Autorun Fail (Boot Console)
- ❌ **Sinclair ZX81** (`81`) — Autorun Fail (Boot Console)
- ❌ **CPS1 (Capcom)** (`fbalpha2012_cps1`) — Autorun Fail (Menu RetroArch)
- ❌ **CPS2 (Capcom)** (`fbalpha2012_cps2`) — Autorun Fail (Menu RetroArch)
- ❌ **Neo Geo (Arcade)** (`fbneo`) — Autorun Fail (Boot Console)
- ❌ **MAME (Arcade)** (`mame2003_plus`) — Autorun Fail (Menu RetroArch)

### Améliorations suggérées pour le script `pack_game (5).py`

1. **Autorun Arcade** : Les cores CPS1/CPS2/Neo Geo/MAME nécessitent une configuration d'autostart spécifique
2. **BIOS ColecoVision** : Intégrer le BIOS `colecovision.rom` dans le packing ou avertir l'utilisateur
3. **Commandes de démarrage ordinateurs** : Pour C64, VIC-20, PET, Amstrad CPC, ZX81, ajouter les commandes `LOAD"*",8,1` / `RUN` en automatique
4. **Core SMS** : Remplacer `smsplus` par `genesis_plus_gx` pour le Master System (le Genesis fonctionne avec ce core)
5. **Systèmes instables** : Documenter que Virtual Boy, Atari Jaguar, Atari Lynx, et 32X sont instables en émulation WebAssembly

---

## 🔧 Environnement de Test

| Paramètre | Valeur |
|:---|:---|
| **User Agent** | `Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36` |
| **Plateforme** | `Linux armv81` |
| **Écran** | 384x854 |
| **WebGL Vendor** | ARM |
| **WebGL Renderer** | Mali-G57 MC2 |
| **WebGL Version** | WebGL 2.0 (OpenGL ES 3.0 Chromium) |

### Logs Console Communs

Tous les jeux présentent ces deux messages non-bloquants :
- `TypeError: Cannot read properties of undefined (reading 'endsWith')` — Bug mineur EmulatorJS
- `Could not fetch core report JSON! Core caching will be disabled!` — Normal en mode standalone (pas de serveur)

---

*Rapport généré automatiquement à partir de 64 fichiers de test JSON — 2 mars 2026*