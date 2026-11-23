# Banques de palettes OBJ et transferts DMA

Le moteur du monde résout ses **22 ressources de palette** vers un pool de **13 banques OBJ** à chaque passage de `Draw`. Il garde les couleurs chargées d’une image à la suivante tant que la même ressource revient dans la même case et que ses couleurs restent valides. Les tests du code Thumb et les traces du mariage de la Déesse (`0848`) couvrent les éditions USA A4NE et Europe A4NP. [Sélection des ressources](allocation-palettes-obj.md) · [Données des essais](../../ressources/donnees/banques-obj/)

## Structure du cache

Le cache commence à `GameSceneWorld + 0x19C`. Les offsets ci-dessous se rapportent au cache, à une ressource ou à une case du pool selon la colonne de gauche. [Structures natives](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/world_runtime.hh#L21-L73)

| Base | Offset | Champ |
| --- | --- | --- |
| Cache | `+0x000` | 32 octets de mémo. Une résolution réussie est encodée sous la forme `banque + 16`. |
| Cache | `+0x020` | 22 ressources de `0x84` octets. |
| Ressource | `+0x80` | Indice signé de la case du pool. `-1` indique une ressource sans case. |
| Ressource | `+0x81` | Occupation logique suivie par `vfunc_48`. |
| Ressource | `+0x82` | Couleurs à remettre en file lorsqu’il est non nul. |
| Cache | `+0xB78` | 13 cases de `0x0C` octets, chacune avec sa banque réservée. |
| Case | `+0x08` | Numéro de banque matérielle. |
| Case | `+0x09` | ID signé de la ressource associée. `-1` indique une case libre. |
| Case | `+0x0A` | Validité des couleurs associées à cet ID après leur mise en file. |
| Cache | `+0xC14`, `+0xC15` | Nombre de cases utilisées pendant le rendu courant et le précédent. |

## Cycle d’un rendu

1. `Draw` vide le mémo, copie le nombre de cases utilisées vers le compteur précédent, remet à `-1` l’indice de case des ressources du rendu précédent et remet le compteur courant à zéro. Les cases gardent leur ID de ressource et leur validité à ce stade. [Début de `Draw`](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world.cc#L844-L861) · [Remise à zéro des associations](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world.cc#L909-L961)
2. `GetSpritePaletteBank` réutilise une valeur de mémo d’au moins `16`. En dessous, il appelle `AcquirePaletteBank`. Une ressource déjà associée reçoit sa banque sans consommer de place supplémentaire. Une nouvelle ressource prend la prochaine case dans l’ordre des demandes. Changer l’ID de la case invalide ses couleurs. [Lecture du mémo](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world_interface.cc#L109-L120) · [Acquisition de la banque](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/world_runtime.cc#L64-L135)
3. `Draw` met en file un transfert de **32 octets** si les couleurs de la ressource sont marquées à réécrire ou si la case est invalide. La source commence à `ressource + 0x00` quand `MapData.flags` vaut `1` et à `ressource + 0x60` pour les autres valeurs. La destination est `0x05000200 + 32 × banque`. Après la mise en file, le moteur efface le drapeau de réécriture et marque la case valide. Le moteur des sprites place la banque dans les bits 12 à 15 de l’attribut OBJ `ATTR2`. [Préparation du transfert](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world.cc#L3514-L3616) · [Validation et nettoyage](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world.cc#L3820-L3884) · [Écriture de `ATTR2`](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_sprite.cc#L149-L192)
4. Si le rendu a utilisé moins de cases que le précédent, `Draw` écrit `-1` dans l’ID de chaque case devenue libre, du compteur courant au compteur précédent exclu. L’octet de validité reste en place. La prochaine ressource qui occupe une de ces cases lui assigne son ID et invalide les anciennes couleurs. [Nettoyage des cases](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world.cc#L3846-L3884)

## Saturation et réutilisation dans le code natif

L’extracteur exécute **68 opérations** dans Unicorn sur des copies de la RAM mGBA, soit 34 par édition. Le scénario de saturation demande les ressources `0` à `12`, puis demande deux fois la ressource `13`. Les deux tentatives renvoient `-1` et laissent le mémo à `15`, ce qui autorise une nouvelle tentative. La ressource `0` reste accessible. Au rendu suivant, la ressource `13` obtient la première case devenue disponible. [Contextes](../../ressources/donnees/banques-obj/Contextes-pool-OBJ-FoMT.csv) · [Étapes et octets avant et après](../../ressources/donnees/banques-obj/Cycle-pool-OBJ-FoMT.csv)

Dans le scénario de réutilisation, un rendu demande `4`, `7`, `1` dans cet ordre et exécute le fragment qui valide chaque mise en file. Le rendu suivant demande `4`, `1`. La case 0 garde ses couleurs, la case 1 passe de la ressource `7` à la ressource `1` et doit être rechargée. En fin de rendu, la case 2 est libérée. Le test de saturation isole le code d’acquisition et les fragments de `Draw` qui gèrent le pool. [Scénario de réutilisation](../../ressources/donnees/banques-obj/Cycle-pool-OBJ-FoMT.csv)

## Copies observées dans mGBA

Dans l’église (`0x000C`), au PC `0x1F7` du script `0848`, le premier rendu relevé met en file sept transferts. L’image suivante exécute les sept copies sur le **canal DMA 3**. La banque 0 reçoit une seconde copie deux images plus tard, avec la même empreinte. Pour chacune des **16 copies** observées au total, les 32 octets en mémoire de palette OBJ correspondent aux 32 octets de la source en EWRAM. [Images et compteurs](../../ressources/donnees/banques-obj/Images-ceremonie-DMA-OBJ-FoMT.csv) · [Adresses, tailles et empreintes](../../ressources/donnees/banques-obj/Transferts-ceremonie-DMA-OBJ-FoMT.csv)

| Image relative | Mises en file | Copies DMA 3 | Banques utilisées |
| --- | ---: | ---: | ---: |
| 0 | 7 | 0 | 7 |
| 1 | 0 | 7 | 7 |
| 2 | 1 | 0 | 7 |
| 3 | 0 | 1 | 7 |
| 4 à 11 | 0 | 0 | 7 |

Les deux éditions donnent le même relevé de 20 demandes et 7 acquisitions par image. Les huit dernières images réutilisent les sept banques sans transfert. Les ressources `6`, `7` et `8` des lutins arrivent aux banques `4`, `5` et `6` à `0x05000280`, `0x050002A0` et `0x050002C0`. [Banques par lutin](../../ressources/donnees/palettes-obj/Palettes-ceremonie-OBJ-FoMT.csv)

## Rendu à la quatorzième demande

**Hoggy reste visible avec les couleurs de la banque OBJ 15** si la résolution de sa palette renvoie `-1`. L’essai force la saturation dans l’église au PC `0x20B` de `0848`. Avant que Hoggy demande la ressource `8`, six ressources de la scène ont déjà obtenu une banque. Un point d’arrêt fait passer six ou sept ressources de test supplémentaires par `GetSpritePaletteBank`, puis laisse reprendre l’appel de Hoggy. Les demandes supplémentaires passent par le code du jeu. La ROM, l’OAM et les couleurs de la banque 15 sont conservées telles quelles au moment de l’intervention. [42 images comparées](../../ressources/donnees/banques-obj/Saturation-rendu-OBJ-FoMT.csv) · [Banque associée à la ressource de Hoggy](../../ressources/donnees/palettes-obj/Palettes-ceremonie-OBJ-FoMT.csv)

| Demandes de test | Rang de la demande de Hoggy | Retour de `GetSpritePaletteBank` | `ATTR2` matériel après synchronisation | Pixels modifiés par rapport au témoin |
| ---: | ---: | ---: | --- | ---: |
| 0 | 7 | `6` | `0x68D8` | 0 |
| 6 | 13 | `12` | `0xC8D8` | 0 |
| 7 | 14 | `-1` | `0xF8D8` | 104 |

Dans la routine ARM de soumission du sprite, le retour arrive dans `r0` à `0x030005FC`, puis passe dans `r12`. À `0x03000658`, `orr r1, r1, r12, lsl #12` ajoute la valeur aux bits de palette. Le champ `ATTR2` conserve les 16 bits de poids faible. Les quatre bits issus de `-1` valent donc `0xF`. Le seul attribut OAM qui change est `ATTR2` de l’entrée 6, à la position écran `(224, 51)`. La tuile `0x0D8`, les autres attributs et les données graphiques OBJ en VRAM restent identiques. Les 104 pixels changés occupent le rectangle inclusif `(228, 58)` à `(237, 75)`. La banque 15 garde la même empreinte pendant tout l’essai. [Soumission du sprite ARM](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_sprite.cc#L149-L192) · [Attributs et empreintes par image](../../ressources/donnees/banques-obj/Saturation-rendu-OBJ-FoMT.csv)

L’image de la première demande à saturation contient encore l’`ATTR2` matériel du témoin. L’`ATTR2` préparé par le moteur apparaît dans l’OAM et les pixels à l’image suivante. À l’arrêt des réservations, le moteur renvoie de nouveau `6` et la vidéo retrouve l’empreinte du témoin une image plus tard. Le même résultat a été observé dans les deux éditions. L’essai établit l’effet d’une saturation provoquée dans cette scène. La fréquence du défaut en partie ordinaire reste à déterminer.

## Reproduire les essais

L’extracteur prend les deux ROM et deux états mGBA où le monde est actif. `valider_envoi` désigne l’exécution du fragment qui modifie les drapeaux après une mise en file dans `Draw`. Le relevé mGBA ci-dessus suit les copies réellement exécutées. [Extracteur du cycle natif](../../outils/jeu/relever_banques_obj.py)

```sh
python3 -m pip install unicorn==2.1.4
python3 outils/jeu/relever_banques_obj.py roms/A4NE.gba roms/A4NP.gba exports/banques-obj \
  etats/after-sleep-steady.state etats/Harvest-Moon-Europe.ss1
```

Pour suivre la cérémonie, préparer une copie de l’état de sommeil comme dans le relevé précédent, confirmer le sommeil et avancer jusqu’à l’église. Le relevé a utilisé mGBA 0.10.5. Une observation du service `GBADMAService` a enregistré le canal, la source, la destination et la longueur des copies dans la plage `0x05000200` à `0x050003FF`. Au site de construction du descripteur, `r1` et `r2` donnent la source et la destination. La première image à sept mises en file sert de repère commun. [Préparation de la cérémonie](allocation-palettes-obj.md#reproduire-les-relevés) · [Empreintes des états de départ](../../ressources/donnees/palettes-obj/Contextes-ceremonie-OBJ-FoMT.csv)

| Repère | USA A4NE | Europe A4NP |
| --- | --- | --- |
| `Draw` | `0x080182C8` | `0x080182DC` |
| Appel au constructeur du descripteur de palette | `0x08019932` | `0x08019946` |
| `GetSpritePaletteBank` | `0x0801FCB4` | `0x0801FCC8` |
| `AcquirePaletteBank` | `0x080AC96C` | `0x080AC99C` |

### Reproduire le rendu à saturation

Compiler le cœur Libretro de mGBA 0.10.5 avec les points d’arrêt fournis, puis lancer le script depuis la racine du dépôt. Il prépare une copie de l’état de sommeil, avance jusqu’à `0848`, rejoue trois variantes depuis le même point et exporte les 21 images de l’édition choisie. Le script n’utilise que la bibliothèque standard de Python. Les lignes des deux éditions sont réunies dans le CSV du dépôt. [Sources de mGBA 0.10.5](https://github.com/mgba-emu/mgba/releases/tag/0.10.5) · [Points d’arrêt](../../outils/mgba/instrumentation/mgba-0.10.5-points-arret.diff) · [Script de mesure](../../outils/mgba/relever_saturation_obj.py)

```sh
patch -d mgba-0.10.5 -p1 -i "$PWD/outils/mgba/instrumentation/mgba-0.10.5-points-arret.diff"
cmake -S mgba-0.10.5 -B mgba-build -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_LIBRETRO=ON -DBUILD_QT=OFF -DBUILD_SDL=OFF -DDISABLE_DEPS=ON
cmake --build mgba-build --target mgba_libretro
python3 outils/mgba/relever_saturation_obj.py mgba-build/mgba_libretro.so \
  roms/A4NE.gba etats/sommeil-usa.state saturation-usa.csv
python3 outils/mgba/relever_saturation_obj.py mgba-build/mgba_libretro.so \
  roms/A4NP.gba etats/sommeil-europe.state saturation-europe.csv
```
