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

Dans le scénario de réutilisation, un rendu demande `4`, `7`, `1` dans cet ordre et exécute le fragment qui valide chaque mise en file. Le rendu suivant demande `4`, `1`. La case 0 garde ses couleurs, la case 1 passe de la ressource `7` à la ressource `1` et doit être rechargée. En fin de rendu, la case 2 est libérée. Le test de saturation isole le code d’acquisition et les fragments de `Draw` qui gèrent le pool. Le rendu des sprites à saturation reste à observer dans une scène jouée. [Scénario de réutilisation](../../ressources/donnees/banques-obj/Cycle-pool-OBJ-FoMT.csv)

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
