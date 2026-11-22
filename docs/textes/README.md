# Textes et localisation

Les relevés portent sur *Harvest Moon: Friends of Mineral Town* GBA, révision 00. Les adresses désignent des offsets dans le fichier. Les pointeurs ROM GBA valent `0x08000000` plus cet offset. Les longueurs des index CSV comptent les octets avant le terminateur `00`, commandes de dialogue comprises. [Identification des éditions](../versions.md)

## Textes d’événement

Les textes complets sont disponibles avec les index de travail. [Dialogues USA](../../ressources/textes/A4NE/) · [Catalogue Europe en français](../../ressources/textes/A4NP/fr/) · [Catalogue Europe en anglais](../../ressources/textes/A4NP/en/)

| Édition | Table des scripts | Scripts | Chaînes `STR` | Index |
| --- | ---: | ---: | ---: | --- |
| A4NE USA | `0x0F89D4` | 1 328 | 8 368 | [Métadonnées A4NE](Evenements-A4NE.csv) |
| A4NP Europe | `0x0F8A20` | 1 328 | 8 368 | [Métadonnées A4NP](Evenements-A4NP.csv) |

La case `0000` est nulle. Chaque pointeur actif mène à un bloc `RIFF/SCR ` avec `CODE`, éventuellement `JUMP`, puis `STR `. La longueur indiquée à `RIFF + 4` couvre l’ensemble du bloc depuis `RIFF`. La charge `STR ` commence par un nombre de chaînes `u32`, suivi de leurs offsets `u32` relatifs au début des données textuelles. Les scripts, les cases de chaînes et les offsets restent identifiables séparément dans les CSV. [Format des scripts](https://github.com/StanHash/FOMT-DOC/blob/master/EventScripts.txt) · [Événements et déclencheurs](../evenements/)

La comparaison des deux ROM d’origine donne les mêmes blocs `CODE` et `JUMP`. Seul le contenu de `1008.00`, la présentation de Karen, diffère parmi les chaînes `STR`. Il occupe 92 octets à `0x3CAD70` en A4NE et 96 octets à `0x3CADC8` en A4NP. Les offsets de fichiers doivent être repris dans l’index de la bonne édition.

| Repère | ID | A4NE | A4NP |
| --- | --- | ---: | ---: |
| Panneau de la caisse d’expédition | `0162.00` | `0x2CC120` | `0x2CC178` |
| Première sortie du fermier de sa maison | `0737.00` | `0x35AC08` | `0x35AC60` |

`05` attend une action, `0C` change de page et `0D 0A` revient à gauche puis avance d’une ligne. Les codes `FF21` (joueur), `FF22` (cheval), `FF23` (chien), `FF29` (surnom), `FF2A` (enfant), `FF24` et `FF2B` (lieux), `FF25` à `FF28` (variables de script), `FF2C` et `FF2D` (passants) insèrent des valeurs à l’exécution. Une traduction doit préserver les commandes et vérifier le rendu des caractères auprès de la police GBA. [Table de caractères et de commandes](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/charmap.txt)

## Chaînes natives

Le relevé A4NP couvre 283 chaînes utilisées dans les menus, statuts et autres interfaces. Dans cet index, l’identifiant `Nxxxxxx` incorpore l’offset de la chaîne. Pour chacune, `lectures_thumb` énumère les couples adresse de l’instruction `LDR` et adresse de son littéral, dans l’ordre `instruction>littéral`. Les 415 couples ont été vérifiés dans la ROM. Le contexte repose sur le lecteur natif et ses branches documentées. La couverture est limitée aux chaînes recensées et à l’édition A4NP. [Index natif A4NP](Natifs-A4NP.csv) · [Sources EU épinglées](https://github.com/Wokann/fomt/tree/9f2f03c775d64270a95250b8c03e6742219fda21/data/text/eu)

## Saisie du joueur, de la ferme et du chien

Les trois champs utilisent douze places de saisie sur les deux éditions. La mémoire de saisie et de normalisation réserve treize octets pour les douze positions et le terminateur. La création passe par le nom du joueur, l’anniversaire, le nom de la ferme, le nom du chien et la confirmation du profil. En mGBA 0.10.5 avec la v0.2 française A4NP, la saisie au douzième caractère mène à **Fini** et les trois noms réapparaissent dans le récapitulatif. [Ordre des écrans](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/new_game_name_entry.cc) · [Saisie et limite de longueur](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/new_game_name_input.cc)

| Élément à l’écran | Taille réservée d’origine | Chaîne A4NE | Chaîne A4NP | Lecteur littéral A4NE | Lecteur littéral A4NP |
| --- | ---: | ---: | ---: | --- | --- |
| Préfixe joueur, **Ton nom** | 8 | `0x0E8934` | `0x0E8980` | `0x004EE8` | `0x004EFC` |
| Préfixe ferme, **Ta ferme** | 8 | `0x0E893C` | `0x0E8988` | `0x004EEC` | `0x004F00` |
| Préfixe chien, **Ton chien** | 8 | `0x0E8944` | `0x0E8990` | `0x004EF0` | `0x004F04` |
| Suffixe commun de saisie, vidé en v0.2 | 8 | `0x0E8BF4` | `0x0E8C40` | `0x005F18` | `0x005F2C` |
| **End**, rendu **Fini** en v0.2, espaces demi-largeur | 24 | `0x0E8BFC` | `0x0E8C48` | `0x0066F4` | `0x006708` |
| **End**, rendu **Fini** en v0.2, espaces pleine largeur | 24 | `0x0E8C14` | `0x0E8C60` | `0x006710`, `0x006770` | `0x006724`, `0x006784` |
| Confirmation du nom | 24 | `0x0E8C2C` | `0x0E8C78` | `0x007028` | `0x00703C` |

Les tailles réservées incluent le terminateur et le remplissage éventuel. Les deux variantes de **End** comportent chacune 20 octets d’espacement, suivis de trois caractères et du terminateur. La traduction **Fini** occupe 25 octets avec cet espacement. Le patch A4NP redirige les trois pointeurs vers `0x75D018` et `0x75D034`. Il redirige aussi la ferme vers `0x75D000` et le chien vers `0x75D00C`. Le libellé du joueur tient dans ses huit octets. Les libellés du profil final pour le nom, l’anniversaire, la ferme et le chien sont à `0x0E8958`, `0x0E8968`, `0x0E8978`, `0x0E8988` en A4NE et `0x0E89A4`, `0x0E89B4`, `0x0E89C4`, `0x0E89D4` en A4NP.

Le premier caractère et le curseur du nom commencent à `x = 144` dans la ROM d’origine et `x = 112` avec la v0.2 A4NP. Les deux littéraux de carte de tuiles modifiés sont à `0x005F10` et `0x005F14`, et les deux constantes du curseur à `0x0062B2` et `0x0068EC`. Les emplacements homologues vérifiés dans l’original A4NE sont `0x005EFC`, `0x005F00`, `0x00629E` et `0x0068D8`. [Données de saisie A4NE](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/text/us/new_game_menu_2.cc) · [Données de saisie A4NP](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/text/eu/new_game_menu_2.cc)

## Personnages et inventaire

La table `gCharacterNameEntries` contient 43 enregistrements de huit octets à `0x104258` en A4NE et `0x1042B0` en A4NP. Le premier mot contient le pointeur du nom. Les 41 entrées renseignées ont le même contenu dans les deux ROM. Les entrées `0` et `35` pointent vers une chaîne vide. L’enfant utilise son nom de sauvegarde quand il existe. Les noms du fermier et de l’enfant sont donc renseignés dans le catalogue comme valeurs dynamiques. [Index brut A4NE](Noms-personnages-A4NE.csv) · [Index brut A4NP](Noms-personnages-A4NP.csv) · [Table des personnages](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/npc_collection.cc)

Le catalogue des personnages donne 52 relevés avec leurs provenances. Il distingue les noms et titres de cette table, les plaques de rôle du prologue, les deux noms présentés en dialogue, les noms saisis et les substitutions. L’ID `33` affiche **Lou** depuis la table et se présente comme **Van** dans `0813.00`. L’ID `34` affiche **Lu** depuis la table et se présente comme **Lou** dans `0814.00`. Les graphies et les adresses des 50 entrées statiques du catalogue ont été relues dans les deux ROM. [Catalogue de noms et de rôles](Personnages.csv)

Les tables `gToolInfo`, `gFoodInfo` et `gArticleInfo` couvrent 81 outils, 171 aliments et 95 articles par édition. Le premier mot de chaque enregistrement pointe vers le nom et le dernier vers la description. Les 347 noms et les 347 descriptions concordent entre A4NE et A4NP. Deux adresses de noms sont partagées entre des entrées. Les index donnent l’offset et la longueur des deux champs. Les libellés de cuisine à largeur fixe, le libellé du panier et les secours hors plage constituent des données natives séparées. [Index A4NE](Libelles-objets-A4NE.csv) · [Index A4NP](Libelles-objets-A4NP.csv) · [Index des icônes avec noms anglais](../graphismes/objets/Index-icones-objets-A4NE.csv) · [Tables d’inventaire](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/item.cc)

## État de la localisation

La démonstration française 0.2 cible uniquement A4NP. Son manifeste couvre 31 entrées concernant la création de partie, le profil, le menu de pause, le journal, le sac et le panneau **Caisse →**. Les tests mGBA 0.10.5 ont parcouru la saisie jusqu’au profil sur la 0.2. La 0.1 a aussi été vérifiée en sauvegardant via **Journal → Sauver → Case 1**, en redémarrant mGBA puis en rechargeant via **Lire → Case 1**, et en activant le panneau de la caisse. [Inventaire des archives de travail](../archives-de-travail.md)

Le caractère **é** de l’essai occupe `C5` dans un emplacement de kana demi-chasse. Le glyphe redessiné est à `0x4FA07C` en A4NP. Les autres accents demandent un relevé de police et des essais. Les chaînes des événements de longueur variable, leur réinsertion et la localisation A4NE restent à valider. [Relevé de police](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/font.cc)

## Reproduire les index

Depuis la racine du dépôt, renseigner le chemin de la ROM d’origine. L’outil ne lit les offsets qu’après contrôle de l’édition et du SHA-1. La sortie CSV contient des adresses et des longueurs. Changer le nom du fichier de sortie en fonction de l’édition utilisée. [Indexeur de texte](../../outils/textes/indexer_textes.py)

```sh
mkdir -p exports
python3 -B outils/textes/indexer_textes.py roms/A4NE.gba > exports/Evenements-A4NE.csv
python3 -B outils/textes/indexer_textes.py roms/A4NE.gba --noms > exports/Noms-personnages-A4NE.csv
python3 -B outils/textes/indexer_textes.py roms/A4NE.gba --objets > exports/Libelles-objets-A4NE.csv
python3 -B outils/textes/indexer_textes.py roms/A4NP.gba --verifier-natifs
python3 -B outils/evenements/indexer_scripts.py roms/A4NE.gba --comparer roms/A4NP.gba
```
