# 🕹️ Étude de faisabilité — Nouveaux systèmes pour portable-retro-games

> **Objectif** : identifier tous les systèmes rétro supplémentaires qui pourraient être pris en charge, soit via EmulatorJS (cores non encore exploités), soit via des émulateurs JS/WASM autonomes permettant le même principe de fichier HTML unique et offline.

---

## Table des matières

- [Rappel : systèmes actuellement supportés (38)](#rappel--systèmes-actuellement-supportés-38)
- [PARTIE A — Cores EmulatorJS non encore exploités (5 systèmes)](#partie-a--cores-emulatorjs-non-encore-exploités-5-systèmes)
- [PARTIE B — Émulateurs JS/WASM autonomes (13+ systèmes)](#partie-b--émulateurs-jswasm-autonomes-13-systèmes)
- [PARTIE C — Systèmes NON faisables actuellement](#partie-c--systèmes-non-faisables-actuellement)
- [Synthèse et priorités](#synthèse-et-priorités)
- [Impact sur le code du packer universel](#impact-sur-le-code-du-packer-universel)

---

## Rappel : systèmes actuellement supportés (38)

| Catégorie | Systèmes dans `pack_game.py` |
|-----------|------------------------------|
| **Console Nintendo** | NES, SNES, GB, GBC, GBA, N64, NDS, Virtual Boy |
| **Console Sega** | Genesis/Mega Drive, Master System, Game Gear, 32X, Sega CD |
| **Console Atari** | 2600, 5200, 7800, Lynx, Jaguar |
| **Console Sony** | PlayStation |
| **Console NEC** | PC Engine, PC-FX |
| **Console Autre** | Neo Geo Pocket, WonderSwan, ColecoVision |
| **Ordinateur Commodore** | C64, C128, VIC-20, PET, Plus/4, Amiga |
| **Ordinateur Sinclair** | ZX Spectrum, ZX81 |
| **Ordinateur Amstrad** | CPC |
| **Arcade** | CPS1, CPS2, FBNeo, MAME 2003+ |
| **Autre** | DOOM (PrBoom) |

---

## PARTIE A — Cores EmulatorJS non encore exploités (5 systèmes)

Ces systèmes disposent déjà de cores WASM compilés et hébergés sur le CDN EmulatorJS. Ils peuvent être ajoutés au `pack_game.py` **avec un effort minimal** — essentiellement une nouvelle entrée dans le dictionnaire `SYSTEMS` et potentiellement quelques ajustements.

### A1. 🎮 3DO Interactive Multiplayer

| | |
|---|---|
| **Core** | `opera` (~834 KB WASM) |
| **System ID** | `3do` |
| **Extensions** | `.iso`, `.bin`, `.cue`, `.chd` |
| **Taille ROM** | 50–650 MB |
| **BIOS requis** | ⚠️ Oui — `panafz1.bin` (Panasonic FZ-1) |
| **Taille HTML estimée** | 70–900 MB |
| **Difficulté d'intégration** | ⭐⭐ Facile (mais fichiers lourds) |
| **Qualité émulation** | Bonne, la plupart des jeux fonctionnent |
| **Jeux notables** | Road Rash, Need for Speed, Gex, Return Fire, Star Control II |

**Verdict** : ✅ Faisable. Le core existe et fonctionne. Le principal obstacle est la **taille des ISOs** (souvent 300-650 MB) qui produit des fichiers HTML énormes une fois en base64 (+33%). Viable pour les jeux plus petits. L'obligation d'un BIOS propriétaire complique la distribution.

**Ajout au packer** :
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
| **Taille ROM** | 50–650 MB |
| **BIOS requis** | ⚠️ Oui — `saturn_bios.bin` |
| **Taille HTML estimée** | 70–900 MB |
| **Difficulté d'intégration** | ⭐⭐ Facile (code) / ⭐⭐⭐⭐ Difficile (performances) |
| **Qualité émulation** | ⚠️ Médiocre en WASM — Yabause est le moins précis des émulateurs Saturn |
| **Jeux notables** | Nights into Dreams, Panzer Dragoon Saga, Virtua Fighter 2, Radiant Silvergun |

**Verdict** : ⚠️ Faisable techniquement mais **résultats décevants**. L'émulation Saturn en WASM via Yabause est connue pour être instable. Beaucoup de jeux crashent ou ont des glitches graphiques sévères. Les fichiers sont aussi très lourds. À proposer avec un avertissement.

---

### A3. 📱 PlayStation Portable (PSP)

| | |
|---|---|
| **Core** | `ppsspp` (~4.3 MB WASM, thread-only + 10.3 MB assets) |
| **System ID** | `psp` |
| **Extensions** | `.iso`, `.cso`, `.pbp` |
| **Taille ROM** | 50 MB – 1.8 GB |
| **BIOS requis** | Non (émulateur HLE) |
| **Taille HTML estimée** | 80 MB – 2.5 GB (!) |
| **Difficulté d'intégration** | ⭐⭐⭐⭐ Difficile |
| **Qualité émulation** | Variable — bonne pour les jeux 2D, problématique pour les gros jeux 3D |
| **Jeux notables** | God of War, Crisis Core FF7, Persona 3 Portable, Monster Hunter |

**Verdict** : ⚠️ **Faisable mais problématique**. Le core `ppsspp` est **thread-only** (nécessite SharedArrayBuffer, donc des headers COOP/COEP spéciaux), nécessite un paquet d'assets de 10 MB en plus, et les ISOs PSP sont **énormes**. Le fichier HTML résultant serait souvent > 500 MB. Intérêt limité pour le concept "portable single file".

**Complexité supplémentaire** : Le core PPSSPP requiert des headers HTTP spécifiques (`Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Embedder-Policy: require-corp`) pour SharedArrayBuffer. Cela **ne fonctionne PAS** en ouvrant un fichier HTML local avec `file://` sur la plupart des navigateurs sans configuration spéciale.

---

### A4. 💻 DOS (PC)

| | |
|---|---|
| **Core** | `dosbox_pure` (~1.7 MB WASM, thread-only) |
| **System ID** | `dos` |
| **Extensions** | `.zip`, `.dosz`, `.exe`, `.com`, `.bat`, `.iso`, `.cue`, `.img`, `.ima`, `.vhd` |
| **Taille ROM** | 100 KB – 500+ MB |
| **BIOS requis** | Non |
| **Taille HTML estimée** | Variable, souvent < 20 MB pour les jeux classiques |
| **Difficulté d'intégration** | ⭐⭐⭐ Moyen |
| **Qualité émulation** | Excellente — DOSBox Pure est très mature |
| **Jeux notables** | Civilization, Oregon Trail, Prince of Persia, Commander Keen, Lemmings, Wolfenstein 3D, Duke Nukem |

**Verdict** : ✅ **Très intéressant !** Des milliers de jeux DOS classiques deviendraient portables. Le core est `thread-only` (même limitation SharedArrayBuffer que PSP), mais les jeux DOS sont généralement petits (< 20 MB). DOSBox Pure a l'avantage de supporter le chargement de ZIP directement et l'auto-configuration.

**Alternative standalone** : `js-dos` est un projet mature et bien documenté qui pourrait offrir une alternative si le mode thread-only pose problème. js-dos est conçu spécifiquement pour l'embedding web.

**⚠️ Limitation thread-only** : Comme pour PSP, les fichiers HTML locaux (`file://`) ne supportent pas SharedArrayBuffer. **Solutions** :
1. Servir via un petit serveur local (`python -m http.server`)
2. Utiliser js-dos comme alternative (pas thread-only)
3. Créer un packer spécialisé DOS basé sur js-dos plutôt qu'EmulatorJS

---

### A5. 📀 Philips CD-i

| | |
|---|---|
| **Core** | `same_cdi` (~3.3 MB WASM) |
| **System ID** | `cdi` |
| **Extensions** | `.chd`, `.iso` |
| **Taille ROM** | 100–650 MB |
| **BIOS requis** | ⚠️ Oui — fichiers BIOS CDi |
| **Taille HTML estimée** | 150–900 MB |
| **Difficulté d'intégration** | ⭐⭐⭐ Moyen |
| **Qualité émulation** | Limitée — SAME CDi est encore en développement |
| **Jeux notables** | Zelda: Wand of Gamelon, Hotel Mario (notoires), Burn:Cycle |

**Verdict** : ⚠️ **Faisable mais anecdotique**. Le CDi a une ludothèque très limitée et l'émulation est encore imparfaite. Intérêt principalement historique/curiosité.

---

### Résumé Partie A — Cores EmulatorJS manquants

| Système | Core | Priorité | Difficulté | Intérêt |
|---------|------|----------|------------|---------|
| **DOS** | `dosbox_pure` | 🔴 **Haute** | Moyen (thread-only) | 🌟🌟🌟🌟🌟 Milliers de jeux |
| **3DO** | `opera` | 🟡 Moyenne | Facile | 🌟🌟 Ludothèque correcte |
| **Sega Saturn** | `yabause` | 🟡 Moyenne | Facile (code) | 🌟🌟🌟 Bons jeux, mais émulation faible |
| **PSP** | `ppsspp` | 🟠 Basse | Difficile | 🌟🌟🌟 Bons jeux, mais trop lourd |
| **CD-i** | `same_cdi` | 🔵 Très basse | Moyen | 🌟 Curiosité historique |

---

## PARTIE B — Émulateurs JS/WASM autonomes (13+ systèmes)

Ces systèmes ne sont PAS couverts par EmulatorJS mais disposent d'émulateurs JavaScript ou WebAssembly autonomes qui pourraient être intégrés selon le même principe que les packers spécialisés existants (Apple II, CPC, Amiga).

### B1. 🖥️ MSX / MSX2 / MSX2+ / MSX turboR — WebMSX ⭐⭐⭐⭐⭐

| | |
|---|---|
| **Émulateur** | [WebMSX](https://github.com/ppeccin/WebMSX) (WMSX) |
| **Technologie** | JavaScript pur (pas de WASM nécessaire) |
| **Licence** | MIT-like / Open source |
| **Maturité** | 🟢 Très mature — versions multiples, support mobile |
| **Modèles** | MSX1, MSX2, MSX2+, MSX turboR |
| **Formats** | `.rom`, `.dsk`, `.cas` (cassette), `.mx1`, `.mx2` |
| **Taille ROM** | 8 KB – 2 MB (ROM), 360 KB – 720 KB (DSK) |
| **Taille HTML estimée** | 500 KB – 2 MB |
| **Intérêt ludothèque** | 🌟🌟🌟🌟🌟 Énorme (Metal Gear, Gradius, Vampire Killer, Space Manbow, Aleste, Snatcher…) |

**Pourquoi c'est excellent** :
- WebMSX est conçu dès le départ pour l'embedding web — le concept même du projet est de "lancer un émulateur MSX avec un simple lien"
- Support complet clavier + joystick
- JavaScript pur, pas besoin de WASM
- Auteur (Paulo Augusto Peccin) = même développeur que Javatari.js, qualité prouvée
- Le MSX a une ludothèque massive (~5000+ jeux) avec des titres Konami légendaires
- ROMs légères → fichiers HTML compacts
- Support MSX-MUSIC, MSX-AUDIO, SCC (puces sonores additionnelles)

**Approche d'intégration** : Packer spécialisé similaire à `pack_apple2_game_html.py`, embarquant WebMSX + ROM/DSK en base64.

---

### B2. 🇬🇧 BBC Micro — JSBeeb ⭐⭐⭐⭐

| | |
|---|---|
| **Émulateur** | [JSBeeb](https://github.com/mattgodbolt/jsbeeb) |
| **Technologie** | JavaScript/TypeScript |
| **Licence** | GPL v3 |
| **Maturité** | 🟢 Très mature — par Matt Godbolt (créateur de Compiler Explorer) |
| **Modèles** | BBC Micro Model B (32K), BBC Master (128K) |
| **Formats** | `.ssd`, `.dsd`, `.uef` (cassette) |
| **Taille ROM** | 40–200 KB |
| **Taille HTML estimée** | 300 KB – 1 MB |
| **Intérêt ludothèque** | 🌟🌟🌟 Elite, Repton, Citadel, Exile, Chuckie Egg |

**Pourquoi c'est bon** :
- Émulateur très fidèle et activement maintenu
- Le BBC Micro est l'ordinateur culte britannique (comme le CPC pour la France)
- Fichiers très légers
- Le projet a déjà un mode "embedded" facilité

**Approche** : Packer spécialisé. La structure JSBeeb se prête bien à l'embedding, similaire au packer Apple II.

---

### B3. 🖥️ Atari ST/STE — EstyJS ⭐⭐⭐

| | |
|---|---|
| **Émulateur** | [EstyJS](https://github.com/AntoniMS/estyjs) |
| **Technologie** | JavaScript pur |
| **Licence** | Open source |
| **Maturité** | 🟡 Moyenne — fonctionnel mais pas toujours parfait |
| **Modèles** | Atari ST (1040 ST principalement) |
| **Formats** | `.st`, `.stx`, `.msa` (disquettes) |
| **Taille ROM** | 360 KB – 720 KB par disquette |
| **BIOS requis** | ⚠️ Oui — TOS ROM |
| **Taille HTML estimée** | 1–3 MB |
| **Intérêt ludothèque** | 🌟🌟🌟🌟 Dungeon Master, Populous, Carrier Command, Speedball 2 |

**Pourquoi c'est intéressant** :
- L'Atari ST a une excellente ludothèque de jeux 16 bits
- Beaucoup de portages exclusifs ou supérieurs (Dungeon Master, Falcon)
- JavaScript pur = pas de problème de SharedArrayBuffer

**Limites** :
- EstyJS n'est pas aussi mature que vAmigaWeb ou WebMSX
- Nécessite une ROM TOS propriétaire
- Compatibilité variable selon les jeux

**Alternative possible** : Hatari (émulateur ST mature en C) a été compilé via Emscripten par certains projets, mais pas de version web officielle stable.

---

### B4. 🇫🇷 Thomson MO5/MO6/TO7 — DCMO5 / MO5 Emulator ⭐⭐⭐

| | |
|---|---|
| **Émulateur** | [DCMO5 Online](http://dcmo5.free.fr/online/) / [MO5 Emulator (roug.org)](https://www.roug.org/retrocomputing/emulators/mo5) |
| **Technologie** | JavaScript |
| **Licence** | Open source |
| **Maturité** | 🟡 Moyenne |
| **Modèles** | Thomson MO5, MO6 (DCMO5 couvre aussi TO7, TO8, TO9) |
| **Formats** | `.k7` (cassette), `.fd` (disquette) |
| **Taille ROM** | 10–100 KB |
| **Taille HTML estimée** | 200 KB – 1 MB |
| **Intérêt ludothèque** | 🌟🌟🌟 Patrimoine français — ordinateurs du Plan Informatique pour Tous |

**Pourquoi c'est pertinent** :
- 🇫🇷 **Héritage culturel français majeur** — les Thomson étaient dans toutes les écoles françaises des années 1980
- Complémentaire parfait avec le packer CPC (132 jeux français déjà convertis)
- ROMs minuscules → fichiers HTML très compacts
- Patrimoine en danger de disparition numérique

**Approche** : Packer spécialisé français. Pourrait réutiliser des patterns du packer CPC (même public cible).

---

### B5. 🇬🇧 Oric Atmos — Oricutron WASM / JOric ⭐⭐⭐

| | |
|---|---|
| **Émulateur** | [Oricutron](https://torguet.net/oric/Oricutron.html) (Emscripten) / [JOric](https://github.com/lanceewing/joric) (libGDX→HTML5) |
| **Technologie** | C→WebAssembly (Oricutron) / Java→HTML5 (JOric) |
| **Licence** | GPL v2 (Oricutron) |
| **Maturité** | 🟡 Moyenne — Oricutron WASM est un port en cours |
| **Modèles** | Oric-1, Oric Atmos, Telestrat |
| **Formats** | `.tap`, `.dsk` |
| **Taille ROM** | 10–48 KB |
| **Taille HTML estimée** | 300 KB – 1 MB |
| **Intérêt ludothèque** | 🌟🌟 Communauté active mais ludothèque modeste |

**Pourquoi c'est intéressant** :
- L'Oric est un ordinateur franco-britannique avec une communauté encore active
- Fichiers extrêmement légers
- Oricutron a un port WASM documenté (présentation PDF disponible)
- JOric cible directement HTML5

---

### B6. 🕹️ Vectrex — JSVecX ⭐⭐⭐

| | |
|---|---|
| **Émulateur** | [JSVecX](http://www.twitchasylum.com/jsvecx/) |
| **Technologie** | JavaScript (port de VecX) |
| **Licence** | Open source |
| **Maturité** | 🟡 Fonctionnel |
| **Formats** | `.vec`, `.bin` |
| **Taille ROM** | 4–32 KB |
| **Taille HTML estimée** | < 200 KB |
| **Intérêt ludothèque** | 🌟🌟 Unique — affichage vectoriel, console culte |

**Pourquoi c'est cool** :
- Le Vectrex est la seule console à écran vectoriel (comme Asteroids en arcade)
- ROMs **minuscules** → fichiers HTML les plus compacts possibles
- Visuellement unique et spectaculaire
- La ROM du BIOS/moniteur est libre (Milton Bradley ne l'a jamais protégée)
- Homebrew scene active

---

### B7. 🖥️ TI-99/4A — JS99'er ⭐⭐⭐

| | |
|---|---|
| **Émulateur** | [JS99'er](https://js99er.net/) ([Source](https://github.com/Rasmus-M/Js99er)) |
| **Technologie** | JavaScript/TypeScript |
| **Licence** | Open source |
| **Maturité** | 🟢 Mature |
| **Formats** | `.bin`, `.rpk`, `.dsk` |
| **Taille ROM** | 8–32 KB |
| **Taille HTML estimée** | < 500 KB |
| **Intérêt ludothèque** | 🌟🌟 Parsec, TI Invaders, Tunnels of Doom, Hunt the Wumpus |

**Pourquoi** : Ordinateur emblématique de Texas Instruments avec une communauté fidèle. ROMs très légères.

---

### B8. 💻 DOS (alternative) — js-dos ⭐⭐⭐⭐⭐

| | |
|---|---|
| **Émulateur** | [js-dos](https://js-dos.com/) ([Source](https://github.com/caiiiycuk/js-dos)) |
| **Technologie** | C→WebAssembly (DOSBox Emscripten) |
| **Licence** | GPL v2 |
| **Maturité** | 🟢 Très mature — projet actif depuis 2014 |
| **Formats** | `.zip`, `.exe`, `.com`, archives de jeux DOS |
| **Taille jeu** | 100 KB – 500 MB |
| **Taille HTML estimée** | 2–50 MB pour la majorité des classiques |
| **Intérêt ludothèque** | 🌟🌟🌟🌟🌟 Des milliers de jeux DOS (Civilization, C&C, DOOM, Wolfenstein…) |

**Pourquoi c'est prioritaire** :
- **Alternative au core `dosbox_pure` d'EmulatorJS** qui est thread-only
- js-dos est spécifiquement conçu pour l'embedding web
- Pas de restriction SharedArrayBuffer → **fonctionne en `file://`** !
- API JavaScript bien documentée pour l'auto-configuration
- Peut servir de base à un packer DOS spécialisé

**C'est potentiellement le meilleur candidat pour un nouveau packer spécialisé** car il résout le problème thread-only du core EmulatorJS.

---

### B9. 🗡️ ScummVM — Emscripten Port ⭐⭐⭐⭐

| | |
|---|---|
| **Émulateur** | [ScummVM](https://github.com/scummvm/scummvm) (port Emscripten officiel) |
| **Technologie** | C++→WebAssembly |
| **Licence** | GPL v3 |
| **Maturité** | 🟢 Mature — port officiel maintenu par l'équipe ScummVM |
| **Moteurs** | SCUMM, AGI, SCI, Wintermute, Glk, et 50+ autres |
| **Formats** | Fichiers de données spécifiques à chaque jeu |
| **Taille jeu** | 1–200 MB |
| **Taille HTML estimée** | 5–300 MB |
| **Intérêt ludothèque** | 🌟🌟🌟🌟🌟 Monkey Island, Day of the Tentacle, Sam & Max, King's Quest, Space Quest, Gabriel Knight, Myst… |

**Pourquoi c'est exceptionnel** :
- ScummVM supporte **des centaines de jeux d'aventure** de LucasArts, Sierra, Revolution, etc.
- C'est un **méta-émulateur** : un seul outil couvre un pan entier du jeu rétro (point-and-click)
- Port Emscripten officiel et maintenu
- Beaucoup de jeux freeware/démo disponibles légalement
- Cross-platform par nature

**Approche** : Un packer spécialisé ScummVM serait un ajout majeur au projet. Il nécessiterait d'embarquer le WASM ScummVM + les fichiers de données du jeu.

---

### B10. 🖥️ Macintosh Classic — PCE.js / MiniVMac ⭐⭐

| | |
|---|---|
| **Émulateur** | [PCE.js](https://jamesfriend.com.au/pce-js/) / [MiniVMac-Em](https://github.com/nickvdp/minivmac-3.5-emscripten) |
| **Technologie** | C→Emscripten |
| **Maturité** | 🟡 Fonctionnel |
| **Modèles** | Mac Plus, Mac SE, Mac Classic |
| **Formats** | `.dsk`, `.img` (disquette 800K/1.4M) |
| **BIOS requis** | ⚠️ Oui — ROM Mac |
| **Taille HTML estimée** | 2–5 MB |
| **Intérêt** | 🌟🌟🌟 HyperCard, Dark Castle, Lode Runner, Shufflepuck Cafe |

**Note** : Intéressant mais nécessite des ROMs Mac propriétaires. Le Mac classic a une interface souris-only qui se prête bien aux écrans tactiles.

---

### B11. 🖥️ TRS-80 — TRSjs ⭐⭐

| | |
|---|---|
| **Émulateur** | [TRSjs](http://trsjs.48k.ca/trs80.html) |
| **Technologie** | JavaScript |
| **Formats** | `.cas`, `.dsk` |
| **Intérêt** | 🌟🌟 Historique (premier ordinateur personnel grand public) |

---

### B12. 🇫🇷 Hector / Micronique — HectorJS ⭐

Très niche. Ordinateur français rare. Pas d'émulateur JS connu de qualité.

---

### B13. 🎮 Pokémon Mini ⭐

Pas d'émulateur JS dédié connu. Potentiellement émulable via un core MAME si disponible en WASM.

---

## PARTIE C — Systèmes NON faisables actuellement

| Système | Raison | Perspective |
|---------|--------|-------------|
| **Nintendo 3DS** | Citra nécessite rendu GPU hardware, WASM pas suffisant | ❌ Pas avant longtemps |
| **Nintendo Wii / GameCube** | Dolphin utilise cmake, performances impossibles en WASM | ❌ |
| **PlayStation 2** | Play! a un port JS expérimental mais quasi inutilisable | ❌ |
| **Xbox (original)** | Aucun émulateur JS/WASM | ❌ |
| **Sega Dreamcast** | Flycast WASM existe (nouveau ! 2024) mais très expérimental, nécessite BIOS + WebGL2, GDI de 500MB+ | ⚠️ Émergent — à surveiller |
| **Sharp X68000** | Pas de port WASM | ❌ |
| **NEC PC-88/PC-98** | Cores RetroArch existent mais pas compilés en WASM pour EmulatorJS | ⚠️ Possible si quelqu'un compile |
| **FM Towns** | Pas de port WASM | ❌ |
| **Neo Geo AES/MVS** | Couvert partiellement via FBNeo, mais pas d'entrée dédiée | ✅ Via FBNeo déjà |

### Note sur Dreamcast (Flycast WASM)
Le projet [flycast-wasm](https://github.com/nasomers/flycast-wasm) est le premier port public de Flycast en WASM (novembre 2024). Il fonctionne avec EmulatorJS, nécessite un BIOS réel, WebGL2 et produit des fichiers énormes (GDI = 500 MB+). C'est un signal que l'émulation Dreamcast en navigateur **progresse**, mais c'est encore trop expérimental et lourd pour le concept portable-retro-games. **À réévaluer en 2025-2026.**

---

## Synthèse et priorités

### 🏆 Top 5 — Ajouts recommandés (par ordre de priorité)

| # | Système | Méthode | Effort | Impact |
|---|---------|---------|--------|--------|
| 1 | **DOS (jeux PC)** | js-dos (packer spécialisé) + dosbox_pure (EmulatorJS) | Moyen | 🌟🌟🌟🌟🌟 Milliers de jeux |
| 2 | **MSX / MSX2** | WebMSX (packer spécialisé) | Moyen | 🌟🌟🌟🌟🌟 Ludothèque massive, Konami |
| 3 | **ScummVM** | ScummVM WASM (packer spécialisé) | Élevé | 🌟🌟🌟🌟🌟 Point-and-click légendaires |
| 4 | **3DO** | EmulatorJS core `opera` (ajout dans pack_game.py) | Faible | 🌟🌟 Ludothèque correcte |
| 5 | **BBC Micro** | JSBeeb (packer spécialisé) | Moyen | 🌟🌟🌟 Ordinateur culte UK |

### 🥈 Tier 2 — Ajouts intéressants

| # | Système | Méthode | Effort | Impact |
|---|---------|---------|--------|--------|
| 6 | **Thomson MO5/TO7** | DCMO5 (packer spécialisé) | Moyen | 🌟🌟🌟 Patrimoine français |
| 7 | **Atari ST** | EstyJS (packer spécialisé) | Moyen-Élevé | 🌟🌟🌟 Bons jeux 16-bit |
| 8 | **Vectrex** | JSVecX (packer spécialisé) | Faible | 🌟🌟 Unique/spectaculaire |
| 9 | **TI-99/4A** | JS99'er (packer spécialisé) | Moyen | 🌟🌟 Communauté fidèle |
| 10 | **Oric** | Oricutron WASM (packer spécialisé) | Moyen | 🌟🌟 Franco-britannique |

### 🥉 Tier 3 — Ajouts possibles mais moins prioritaires

| # | Système | Raison de la priorité basse |
|---|---------|----------------------------|
| 11 | **Sega Saturn** | Émulation WASM trop instable |
| 12 | **PSP** | Fichiers trop lourds, thread-only |
| 13 | **CD-i** | Ludothèque quasi inexistante |
| 14 | **Mac Classic** | BIOS requis, niche |
| 15 | **TRS-80** | Très niche |

---

## Impact sur le code du packer universel

### Ajouts EmulatorJS (Partie A) — Modifications minimales

Pour les 5 systèmes EmulatorJS manquants, il suffit d'ajouter des entrées au dictionnaire `SYSTEMS` dans `pack_game.py` :

```python
# Ajouts au dictionnaire SYSTEMS dans pack_game.py

# 3DO
'3do': {
    'core': 'opera',
    'label': '3DO Interactive Multiplayer',
    'extensions': ['.iso', '.bin', '.cue', '.chd'],
    'bios': 'panafz1.bin'   # À gérer
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
    'thread_only': True   # ⚠️ Nécessite SharedArrayBuffer
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

**Nouvelles fonctionnalités requises dans pack_game.py** :
1. **Gestion BIOS** : Permettre d'inclure un fichier BIOS en base64 dans le HTML et le servir via l'intercepteur fetch
2. **Flag `thread_only`** : Avertir l'utilisateur que le fichier ne fonctionnera pas en `file://` sans serveur
3. **Assets additionnels** : Pour PSP, inclure le zip d'assets supplémentaire

### Packers spécialisés (Partie B) — Nouveaux scripts

Chaque nouveau packer spécialisé suivrait le pattern existant :
1. **Télécharger et cacher** l'émulateur JS/WASM
2. **Encoder** la ROM/DSK en base64
3. **Analyser** le contenu si possible (détection genre, touches, etc.)
4. **Assembler** le HTML final avec émulateur + données + UI

Estimation d'effort par packer :

| Packer | Effort estimé | Complexité |
|--------|---------------|------------|
| WebMSX (MSX) | 2-3 jours | Moyenne — API bien documentée |
| js-dos (DOS) | 3-5 jours | Moyenne-haute — config par jeu |
| ScummVM | 5-7 jours | Haute — multi-moteurs, détection jeu |
| JSBeeb (BBC) | 2-3 jours | Moyenne |
| DCMO5 (Thomson) | 2-3 jours | Moyenne |
| EstyJS (Atari ST) | 3-4 jours | Moyenne-haute — TOS ROM |
| JSVecX (Vectrex) | 1-2 jours | Faible — très simple |
| JS99'er (TI-99) | 2-3 jours | Moyenne |
| Oricutron (Oric) | 3-4 jours | Moyenne-haute |

---

## Conclusion

Le projet portable-retro-games peut **doubler sa couverture** en ajoutant :
- **5 systèmes** via les cores EmulatorJS existants (effort minimal pour 3DO, Saturn, DOS, PSP, CDi)
- **9+ systèmes** via des émulateurs JS/WASM autonomes (effort moyen à élevé par packer spécialisé)

Les trois ajouts les plus impactants seraient **DOS** (via js-dos), **MSX** (via WebMSX), et **ScummVM** — qui à eux trois ouvriraient l'accès à **plusieurs milliers de jeux supplémentaires** tout en restant fidèle au concept de fichier HTML unique et offline.

Le projet Flycast WASM pour Dreamcast est à surveiller car il pourrait devenir viable dans 1-2 ans.

---

*Rapport généré le 28 février 2026*
