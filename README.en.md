# Harvest Moon: Friends of Mineral Town Disassembly

[Français](README.md) · **English**

This project aims to catalog, extract, and document all data from *Harvest Moon: Friends of Mineral Town* for Game Boy Advance. The US release (**A4NE**) serves as the reference. The European release (**A4NP**) is used for comparison. The original French localization experiments are part of the project archives. [ROM coverage and extraction batches](docs/couverture-a4ne.md)

## Quick links

| To find… | Files to open |
| --- | --- |
| A line of dialogue and its location | [US dialogue in CSV](ressources/textes/A4NE/Dialogues-A4NE.csv) · [US dialogue in TXT](ressources/textes/A4NE/Dialogues-A4NE.txt) · [European catalog in French](ressources/textes/A4NP/fr/) · [European catalog in English](ressources/textes/A4NP/en/) |
| A character or item | [Character names](docs/textes/Personnages.csv) · [Items and descriptions](docs/textes/Libelles-objets-A4NE.csv) · [Named icons](docs/graphismes/objets/Index-icones-objets-A4NE.csv) |
| A price, food, or shop offer | [A4NE economy data](ressources/donnees/economie/A4NE/) · [Structures and conditions](docs/economie.md) |
| A crop, recipe, or fishing catch | [A4NE activity data](ressources/donnees/activites/A4NE/) · [Tables and conditions](docs/activites.md) |
| A character’s schedule, location, or route | [A4NE schedule data](ressources/donnees/horaires/A4NE/) · [Reading routes](docs/horaires.md) · [Selection by date and weather](docs/selection-horaires.md) |
| What triggers a scene | [Events and calls](docs/evenements/) · [Family events](docs/evenements/vie-de-famille.md) · [Audit of 14 triggers](docs/evenements/declencheurs-14.md) |
| A map, portrait, or sprite | [Graphics directory](ressources/graphismes/A4NE/) · [Preview](ressources/graphismes/A4NE/Apercu.png) · [Graphics indexes and offsets](docs/graphismes/) |
| A tile’s attributes and scripts | [Terrain grids](ressources/donnees/terrain/A4NE/) · [Interaction index](ressources/donnees/terrain/A4NE/Interactions-A4NE.csv) · [Data format](docs/terrain.md) |
| Music, ambience, or a sound effect | [US audio](ressources/donnees/audio/A4NE/) · [European audio](ressources/donnees/audio/A4NP/) · [Format and extraction](docs/audio.md) |
| An mGBA procedure or screenshot | [mGBA 0.10.5 guide](docs/mgba/) · [European screenshots](ressources/mgba/A4NP/captures/) · [US screenshots](ressources/graphismes/A4NE/mgba/) |
| The early localization experiments | [Prototype 0.1](ressources/localisation/A4NP/0.1/LISEZMOI.md) · [Prototype 0.2](ressources/localisation/A4NP/0.2/LISEZMOI.md) |

`ressources/` contains text, images, native graphics files, and reports. `docs/` contains technical indexes and verification results, most of them in French. `outils/` contains Python scripts. To view a large CSV or TXT file on GitHub, use **Raw** or **Download raw file**. [Resource inventory](ressources/README.md) · [Original ZIP checksums](docs/archives-de-travail.md) · [Python tools](outils/)

## Reference releases and addresses

| Code | Release | Revision | Reference SHA-1 |
| --- | --- | ---: | --- |
| `A4NE` | *Friends of Mineral Town*, USA | 0 | `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963` |
| `A4NP` | *Friends of Mineral Town*, Europe | 0 | `7ba1ec1e46ce424e3c6fd72e4e8d5e9eb5ede247` |
| `BFGE` | *More Friends of Mineral Town*, USA | — | `3aa4d46cbbf152e440942acd5f5d37ddc7b05e1d` |

The A4NE and A4NP ROMs analyzed are 8,388,608 bytes each. The game code is at offset `0xAC` and the revision is at `0xBC`. The indexes use file offsets. Add `0x08000000` to convert them into GBA ROM addresses. For example, the A4NE script table at `0x0F89D4` is at `0x080F89D4` in memory. [Checksums, headers, and comparison](docs/versions.md)

The community clue at `0x080000A0` points to the BFGE header of *More Friends of Mineral Town*. Its index of 1,415 script slots and 31 family-scene references comes from the symbol catalog and documentation. The A4NE scripts and offsets below are for *Friends of Mineral Town*. [BFGE files](ressources/evenements/BFGE/) · [Interpreting the clue](docs/versions.md#lindice-communautaire-bfge)

## Text and names

The A4NE and A4NP releases each contain **8,368 event strings**. The European catalog adds **283 native strings** read by menus and other parts of the game. Its French and English editions translate the annotations and preserve the original game text. [European catalog in French](ressources/textes/A4NP/fr/) · [European catalog in English](ressources/textes/A4NP/en/)

An identifier such as `0162.00` refers to the first string in script `0162`. It identifies the shipping bin sign at `0x2CC120` in A4NE or `0x2CC178` in A4NP. The exports give the string’s ID, offset, length, and context. The text includes engine commands such as `05` to wait for input, `0C` to start a new page, and `FF21` to insert the player’s name. [Index and control codes](docs/textes/)

The **52 character entries** cover displayed names, roles, and names stored in the save. The inventory tables contain **347 items**, comprising 81 tools, 171 foods, and 95 articles. Their names and descriptions were compared across the two releases. [Character catalog](docs/textes/Personnages.csv) · [A4NE item text](docs/textes/Libelles-objets-A4NE.csv) · [A4NP item text](docs/textes/Libelles-objets-A4NP.csv)

The early A4NP experiments documented the player, farm, and dog name fields, the label widths, and the pointers used by the engine. The two prototypes include BPS patches, build scripts, text manifests, and screenshots. Version **0.2** includes the **Fini** button. [Prototype 0.1](ressources/localisation/A4NP/0.1/LISEZMOI.md) · [Prototype 0.2](ressources/localisation/A4NP/0.2/LISEZMOI.md) · [Interface offsets](docs/textes/README.md#saisie-du-joueur-de-la-ferme-et-du-chien)

## Events and triggers

The tables for the **1,328 scripts** begin at `0x0F89D4` in A4NE and `0x0F8A20` in A4NP. Each `RIFF/SCR` block can contain `CODE` bytecode, a `JUMP` table, and `STR` strings. The ROM comparison confirms that `CODE` and `JUMP` match. The only differing event string is `1008.00` in Karen’s introduction. [Script structure](docs/evenements/README.md#structure-vérifiée) · [A4NE/A4NP comparison](docs/comparaison-a4ne-a4np.json)

- **Calls and dialogue.** The A4NE index records 696 `CallScript` calls and 459 `SetEntityEventScript` assignments. The assignments attach dialogue to an actor for a later interaction. Whether an assignment runs depends on the branch leading to the instruction. [Call sites](docs/evenements/appels-a4ne.csv)
- **Native routines.** The US and European index links 75,522 bytecode call sites to the 327-entry Thumb dispatcher. It locates the read, write, and notification branches for all 590 variable IDs. All 1,850 `VarSet` calls are annotated with their arguments. [Method and tables](docs/evenements/routines-natives.md) · [CSVs](ressources/donnees/routines-natives/) · [Variable writes](docs/evenements/ecritures-variables.md)
- **Game state in RAM.** All 590 `VarGet` IDs were run against three US and European mGBA states. The 1,770 traces locate the fields read, and the tests establish 485 bitmask formulas. [Method and examples](docs/evenements/lectures-variables.md) · [CSVs](ressources/donnees/lectures-variables/)
- **Writes and notifications.** 30,146 `VarSet` tests cover all 590 IDs. The index locates the bytes written and documents changes to the active event registry. [Method and examples](docs/evenements/ecritures-natives.md) · [CSVs](ressources/donnees/ecritures-natives/)
- **Scene music.** Four calls check the active event registry when updating music. Six tests across both editions verify its role when Karen arrives at the clinic. [Calls and tests](docs/evenements/registre-evenements.md) · [CSVs](ressources/donnees/registre-evenements/)
- **Romance progression.** The 63 variables that share the romance marker are linked to 230 script writes and their counters. Eight clinic tests verify the marker's effect on player sprite priority. [Marker and counters](docs/evenements/romance.md) · [CSVs](ressources/donnees/romance/)
- **SRAM saves.** The `.sav` format, its two slots, and its checksum were verified in both editions. The index gives the file offsets of 674 `VarGet` reads. [Format and inspector](docs/sauvegarde.md) · [CSVs](ressources/donnees/sauvegarde/)
- **Family events.** Sleeping follows `0342 → 0988 → 0980 → 0982 → 0983`. The scheduler `0983`, at A4NE offset `0x390C7C`, selects a branch based on marriage, affection, date, and family progression. Static analysis identified 24 scenes. The bed script `0342` was observed in mGBA in a new game. After sleeping in-game from a copy of a state prepared in RAM, the game selected Karen’s script `0657` and displayed the announcement `0657.03`. [Conditions and scenes](docs/evenements/vie-de-famille.md) · [Karen test procedure](docs/mgba/usa-a4ne.md#test-ciblé-de-karen)
- **Fourteen triggers.** The search covered the indexed calls and assignments and 214,667 terrain cells per release. It found zero references to the 14 IDs through those mechanisms. European tests confirmed related interactions such as Ellen’s bookshelf via `0191`. Normal in-game access to the blocks remains to be established where the audit found only clues. [Results by script](docs/evenements/declencheurs-14.md)

## Graphics and mGBA captures

![Preview of A4NE maps, portraits, items, and scenes](ressources/graphismes/A4NE/Apercu.png)

The A4NE graphics extraction includes **4,577 PNGs** and preserves indexes, palettes, and native graphics blocks. [File guide](ressources/graphismes/A4NE/Lire-moi.md) · [SHA-256 manifest](ressources/graphismes/A4NE/Manifest-graphismes.csv)

| Category | Contents | A4NE reference |
| --- | --- | --- |
| Maps | 66 base maps, 84 renders including night variants, 31 tilesets, and 47 palettes. | `gMapData` at `0x105EDC` · [Map index](docs/graphismes/cartes/Cartes.csv) |
| Portraits and sprites | 184 portraits, 3,009 sprite images, and 2,551 animation selectors. | Archives at `0x52D984` and `0x58BA28` · [Sheets](ressources/graphismes/A4NE/personnages/Planches/) |
| Icons and OBJ groups | 347 inventory icons and 52 additional OBJ archives, including 939 assembled graphics groups. | Shared archive at `0x6678A0` · [OBJ archives](docs/graphismes/archives-obj/Archives-OBJ.csv) |
| Interface | Title screen, menus, fonts, backgrounds, and intro screens. | [ROM ranges in the interface index](docs/graphismes/interface/Interface.csv) |

The maps show static scenery. Characters, weather, crops, and animations are added according to the game state. The **six mGBA 0.10.5 measurements** document background (BG) and sprite (OBJ) palettes, OAM entries, and active layers. Four came from normal play and two from the prepared Karen test. The measurements describe the loaded data and objects in the frame before the final image is composed. [Video measurements](docs/mgba/preuves-video.csv) · [mGBA diagnostic views](docs/mgba/graphismes.md)

The European tests also document shipping, planting, gift-giving, and saving and reloading. [European test report](ressources/mgba/A4NP/Rapport.md) · [European screenshots](ressources/mgba/A4NP/captures/)

## Terrain and interactions

The terrain export covers **155 descriptors**, including 66 base maps, and **214,667 cells** read from the ROM. The grids refer to **722 attribute words** that retain the two bits used for collision checks and the script IDs. An index locates the **9,383 cells with interactions** by map or overlay and local coordinates. [Terrain data](ressources/donnees/terrain/A4NE/) · [Format and scope](docs/terrain.md)

## Items and economy

The A4NE economy CSVs cover **347 item records**, base stamina and fatigue effects for **171 foods**, prices for **103 shippable products**, and **12 shop catalogs**. The tables retain IDs and ROM offsets. The catalogs distinguish stored prices from conditions applied by the game. [Economy files](ressources/donnees/economie/A4NE/) · [Documentation](docs/economie.md) · [Shop conditions](docs/economie-boutiques.md)

## Farming, cooking, and fishing

The A4NE exports cover **39 field plot types** with growth, regrowth, and weather tables. The cooking data includes **117 recipe definitions**, ingredient and utensil lists, and failed cooking outcomes. The fishing tables list **59 catches** with sizes, areas, seasons, and rod levels. [Activity files](ressources/donnees/activites/A4NE/) · [Formats and conditions](docs/activites.md)

## Character schedules and routes

The A4NE tables cover **32 characters**, **254 variant slots**, including 222 with schedules, **1,122 steps**, and **430 routes**. A separate survey records **38,400 calls** to the native selectors across the 120 days of Year 1, with five weather codes and two mGBA states, at 06:00. Those calls returned **122 distinct variant slots**. [Schedules and routes](ressources/donnees/horaires/A4NE/) · [Selector results](ressources/donnees/selecteurs/A4NE/) · [Method and findings](docs/selection-horaires.md)

## M4A audio

The catalog contains **211 slots**, including **144 sequences**, along with **277 tracks**, **263 instrument entries**, **106 PCM samples**, and **32 CGB waveforms**. It identifies **149 track cycles** and **27 PCM loops**. The US and European data match after adjusting the addresses. [US audio](ressources/donnees/audio/A4NE/) · [European audio](ressources/donnees/audio/A4NP/) · [Format and extraction](docs/audio.md)

## Reproduce the checks

The examples use **Python 3.10 or later** and local copies of the original ROMs. After cloning the repository, place the copies at `roms/A4NE.gba` and, for comparison, `roms/A4NP.gba`. Keep ROMs, game saves, and mGBA states in the local test environment.

```sh
git clone https://github.com/geekandgamer0202-alt/harvest-moon-fomt-disassembly.git
cd harvest-moon-fomt-disassembly
mkdir -p roms exports
```

Check the game code and checksum first. The ROM identifier also accepts a ZIP containing a single ROM. The script and text indexers use the `.gba` file and write their CSVs to standard output.

```sh
python3 outils/identifier_rom.py roms/A4NE.gba
python3 outils/evenements/indexer_scripts.py roms/A4NE.gba > exports/scripts-a4ne.csv
python3 outils/evenements/indexer_scripts.py roms/A4NE.gba --appels > exports/appels-a4ne.csv
python3 outils/textes/indexer_textes.py roms/A4NE.gba > exports/index-textes-a4ne.csv
python3 outils/graphismes/verifier_index_a4ne.py roms/A4NE.gba
python3 outils/evenements/exporter_terrain.py roms/A4NE.gba exports/terrain-a4ne
python3 outils/economie/exporter_economie.py roms/A4NE.gba exports/economie-a4ne
python3 outils/jeu/exporter_activites.py roms/A4NE.gba exports/activites-a4ne
python3 outils/jeu/exporter_horaires.py roms/A4NE.gba exports/horaires-a4ne
```

Use the following commands to repeat the regional comparison or look up script references. `auditer_terrain.py` also takes decimal script IDs to locate specific scripts.

```sh
python3 outils/evenements/indexer_scripts.py roms/A4NE.gba --comparer roms/A4NP.gba
python3 outils/evenements/indexer_scripts.py roms/A4NE.gba --audit-quatorze
python3 outils/evenements/auditer_terrain.py roms/A4NE.gba 0342
```

To inspect a scene’s script and video memory, use the guide to record an mGBA 0.10.5 state. For this example, save `exports/mgba/sommeil-a4ne.state` while the farmhouse bed dialogue is open. [mGBA guide](docs/mgba/) · [US walkthrough](docs/mgba/usa-a4ne.md) · [European walkthrough](docs/mgba/europe-a4np.md)

```sh
python3 outils/mgba/inspecter_etat.py --rom roms/A4NE.gba exports/mgba/sommeil-a4ne.state
```

The schedule selector survey uses Unicorn to run the ROM routines in isolation. It varies the date and weather and keeps the other state fields fixed. [Survey procedure](docs/selection-horaires.md#refaire-le-relevé)

The audio tool works on both releases and can generate the CSVs as well as raw tracks and sample data. [Audio export command](docs/audio.md#reproduire-lexport)

To add a reproducible result, specify the release, the ID or offset, the in-game situation, and the tool used. The reports distinguish normal gameplay observations, tests using prepared states, and static ROM analysis.

## Data still to document

Work in progress covers native A4NE text outside event scripts, unresolved triggers and schedule conditions, map transitions and overlay placement, the remaining interfaces and minigames, livestock data, and the cartridge save format. The remaining 31 audio sequences need to be identified and their playback checked in mGBA. The ROM byte ranges also need to be inventoried. [Detailed coverage status](docs/couverture-a4ne.md)

[Wokann’s FoMT disassembly](https://github.com/Wokann/fomt) · [Event script format](https://github.com/StanHash/FOMT-DOC/blob/master/EventScripts.txt) · [mGBA 0.10.5](https://github.com/mgba-emu/mgba/releases/tag/0.10.5)
