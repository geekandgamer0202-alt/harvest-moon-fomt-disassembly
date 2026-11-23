# Format des sauvegardes SRAM

Les éditions USA A4NE et Europe A4NP utilisent le même format `.sav` de **32 768 octets**. Chaque emplacement enregistré contient une copie de **13 556 octets** de `GameStateSaveImage`. Dans mGBA 0.10.5, les deux emplacements de chaque édition correspondent octet pour octet à l’image en RAM au moment de l’écriture. [Mesures d’écriture](../ressources/donnees/sauvegarde/Essais-ecriture-FoMT.csv) · [Structures SRAM](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/sram_image.hh#L10-L48)

## Organisation du fichier

Les tableaux donnent les offsets hexadécimaux à partir du début du fichier, sauf lorsque la colonne précise une autre base. Les valeurs de plusieurs octets sont stockées en *little-endian*.

| Offset fichier | Octets | Champ |
| --- | ---: | --- |
| `0x0000` | 32 | Signature fixe, commune à A4NE et A4NP |
| `0x0020` | 4 | Masque des emplacements présents. Les bits 0 et 1 correspondent aux emplacements 1 et 2. |
| `0x0024` | 4 | Index du dernier emplacement utilisé, de 0 à 1 |
| `0x0028` | `0x3FEC` | Emplacement 1 |
| `0x4014` | `0x3FEC` | Emplacement 2 |

La validation compare les 32 octets de la signature, exige un masque compris entre `0` et `3` et un dernier index entre `0` et `1`. La signature se trouve aussi aux offsets ROM `0x0E862C` en USA et `0x0E8678` en Europe. Elle ne contient aucun code de région. [Validation de l’en-tête](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/sram_image.cc#L7-L38) · [Implantation dans les ROM](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/TEXT_ROM_LAYOUT.md)

| Dans l’emplacement | Octets | Offset `.sav` 1 | Offset `.sav` 2 | Champ |
| --- | ---: | ---: | ---: | --- |
| `+0x0000` | 4 | `0x0028` | `0x4014` | Taille attendue `0x34F4` |
| `+0x0004` | `0x34F4` | `0x002C` | `0x4018` | Image du jeu telle qu’elle est en RAM, octets d’alignement compris |
| `+0x34F8` | 4 | `0x3520` | `0x750C` | Somme des `0x34F4` octets non signés de l’image |
| `+0x34FC` | `0x0AF0` | `0x3524` | `0x7510` | Espace restant dans l’emplacement, hors enregistrement |

Le moteur écrit la taille, l’image, puis la somme. Au chargement, il contrôle la taille puis compare la somme recalculée à celle du fichier. La routine Thumb de calcul a été exécutée avec l’image originale, une image modifiée et une image remplie de `0xFF`, dans les deux éditions. [Écriture et calcul](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_state.cc#L1384-L1431) · [Lecture et validation](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_state.cc#L2007-L2108)

| Routine ou donnée | Adresse ROM GBA USA | Adresse ROM GBA Europe |
| --- | ---: | ---: |
| Calcul de la somme | `0x08011588` | `0x0801159C` |
| Écriture de l’enregistrement | `0x080115B0` | `0x080115C4` |
| Lecture de l’enregistrement | `0x08011650` | `0x08011664` |
| Signature | `0x080E862C` | `0x080E8678` |

## Retrouver un champ dans le fichier

Ajouter `0x002C` ou `0x4018` à un offset dans `GameStateSaveImage`, selon l’emplacement. L’index projette **674 couples variable–lecture** pour **589 ID `VarGet`**. Les 485 masques appliqués aux quatre enregistrements ont reproduit les **1 940 valeurs** attendues d’après les traces en RAM. L’ID `401`, le plat du joueur au concours de cuisine, lit hors de l’image dans les trois états étudiés. Les lectures conditionnelles restent limitées aux chemins observés. [Index des emplacements](../ressources/donnees/sauvegarde/Emplacements-VarGet-FoMT.csv) · [Traces en RAM](evenements/lectures-variables.md)

| Champ | Offset dans l’image | Offset `.sav` 1 | Offset `.sav` 2 | Lecture |
| --- | ---: | ---: | ---: | --- |
| Année | `0x0010` | `0x003C` | `0x4028` | `min(200, 7 * (octet >> 3) + (octet & 7))` |
| Saison et jour | `0x0011` | `0x003D` | `0x4029` | Saison `octet & 3`, jour `((octet & 0x7C) >> 2) + 1` |
| Heure et minute | `0x0012` | `0x003E` | `0x402A` | Heure `mot & 0x1F`, minute `(mot & 0x07E0) >> 5` |
| Nom de la ferme | `0x0014` | `0x0040` | `0x402C` | Chaîne terminée par `00` |
| Solde en G | `0x1AA8` | `0x1AD4` | `0x5AC0` | Entier non signé de 32 bits |
| Nom du joueur | `0x1BD8` | `0x1C04` | `0x5BF0` | Chaîne terminée par `00` |
| Nom du chien | `0x1C78` | `0x1CA4` | `0x5C90` | Chaîne terminée par `00` |
| État de grossesse de Karen | `0x2168` | `0x2194` | `0x6180` | `(octet & 0x60) >> 5` |

Les trois noms sont des `FixedStr<12>` composés de 12 octets de texte au maximum et d’un `00` terminal. L’inspecteur affiche les octets avant le `00` en hexadécimal pour préserver l’encodage d’origine. [Structure de l’image](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/game_state_types.hh#L183-L214) · [Champs du chien](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/animal.hh#L33-L51) · [Chaînes de taille fixe](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/utility/fixed_str.hh#L33-L66)

## Essais dans mGBA 0.10.5

Le cœur Libretro de mGBA a démarré chaque ROM jusqu’à l’initialisation de la SRAM, puis chargé l’état du réveil du 3 printemps en USA ou du début jouable du 2 printemps en Europe. Le journal a servi à enregistrer l’emplacement 1 puis l’emplacement 2. La comparaison de chacun des quatre enregistrements avec la RAM à `0x020025D8`, juste avant et après chaque sauvegarde, donne zéro différence. [Empreintes et mesures](../ressources/donnees/sauvegarde/Essais-ecriture-FoMT.csv)

| Essai de relecture à froid | Résultat dans les deux éditions |
| --- | --- |
| Sauvegarde originale, emplacement 1 puis 2 | Copie complète de l’image retrouvée à `0x02004E0C` en RAM. |
| Solde modifié de 500 à 501 G | L’emplacement est refusé avec la somme d’origine. Après recalcul de la somme, le jeu recharge 501 G. |
| Taille déclarée changée à `0x34F3` | L’emplacement est refusé, même avec les octets et la somme d’origine. |
| Premier octet après la somme modifié | L’emplacement se recharge avec les 500 G d’origine. |
| Bit de présence effacé | L’emplacement apparaît vide malgré un enregistrement encore valide dans le fichier. |

Les 14 essais ont chacun démarré la ROM avec la copie `.sav` correspondante. Depuis l’écran titre, le chargement utilisait l’emplacement sélectionné par défaut. La comparaison a recherché l’image entière en EWRAM après confirmation. [Résultats par édition et empreintes](../ressources/donnees/sauvegarde/Essais-relecture-FoMT.csv)

## Inspecter un fichier ou régénérer l’index

L’inspecteur Python lit un fichier `.sav` et affiche l’en-tête, le statut de chaque emplacement, la date, le solde et les octets des noms. Les numéros `emplacement` vont de 1 à 2 et `dernier_index` conserve le champ brut de 0 à 1. L’indexation écrit un nouveau CSV à partir des traces `VarGet` du dépôt.

```sh
python3 outils/jeu/inspecter_sauvegarde.py inspecter partie.sav
python3 outils/jeu/inspecter_sauvegarde.py indexer Emplacements-VarGet-FoMT.csv
```
