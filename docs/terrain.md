# Terrain et interactions A4NE

Ce relevé associe chaque cellule de terrain stockée par la ROM aux attributs que le moteur charge. Il complète les plans graphiques et le catalogue des scripts. Les offsets sont exprimés depuis le début de la ROM A4NE de référence. [Grilles et index](../ressources/donnees/terrain/A4NE/) · [Éditions et empreintes](versions.md)

| Famille | Table A4NE | Descripteurs | Grilles stockées | Cellules lues |
| --- | --- | ---: | ---: | ---: |
| Plans de base | `0x105EDC` | 66 | 63 | 205 432 |
| Retouches de la ferme | `0x10692C` | 14 | 14 | 2 844 |
| Autres retouches | `0x106A7C` | 68 | 59 | 5 189 |
| Visuels de la maison | `0x107204` | 7 | 7 | 1 202 |
| **Total** | | **155** | **143** | **214 667** |

- [Terrains-A4NE.csv](../ressources/donnees/terrain/A4NE/Terrains-A4NE.csv) donne les dimensions, les pointeurs, l’offset du descripteur et le chemin de sa grille. Les plans `63`, `64` et `65` portent le mode `zero_initialise`. Le moteur initialise leurs 1 800 cellules à zéro. Les neuf retouches sans terrain portent le mode `sans_attribut_rom`. Elles conservent les attributs déjà chargés sur les cellules concernées.
- Chaque fichier `grilles/*.csv` donne les indices d’attribut du terrain. La colonne `y` indique la ligne et les colonnes `0`, `1`, etc. indiquent `x`. Les indices sont des octets. La cellule `(x, y)` se lit à `grille_rom + y × largeur + x`. Les coordonnées sont locales au descripteur, en tuiles de 8 × 8 pixels. Le placement d’une retouche dans le plan dépend de l’appel qui l’applique.
- [Attributs-A4NE.csv](../ressources/donnees/terrain/A4NE/Attributs-A4NE.csv) conserve 722 mots de 32 bits distincts par adresse. Pour retrouver le mot d’une cellule, lire son indice puis calculer `attributs_rom + 4 × indice`. Les colonnes `bit_0` et `bit_1` servent aux tests de terrain. Le test de collision ordinaire tient compte des deux bits. Un second mode utilise le bit 0 seul. Le bit 1 intervient aussi dans un test d’emprise de 12 × 12 pixels. Sa signification de jeu reste à établir. [Tests de terrain](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/map_terrain.cc)
- [Interactions-A4NE.csv](../ressources/donnees/terrain/A4NE/Interactions-A4NE.csv) liste les 9 383 cellules concernées. Le script de marche correspond à `(mot >> 2) & 0x7FFF`. Celui du bouton A correspond à `mot >> 17`. Les cellules vides dans les colonnes de script représentent la valeur nulle. Les embranchements et les conditions s’étudient dans le script. [Catalogue des événements](evenements/catalogue-a4ne.csv)

Exemple vérifié sur le plan `41`. À `(25, 6)`, la grille du plan contient l’indice `3`. Le dictionnaire commence à `0x12A5C8`. Le mot `0x02AC0001` à `0x12A5D4` indique le script `0342` sur A. Le test mGBA au lit de la ferme a observé ce même script. [Grille du plan 41](../ressources/donnees/terrain/A4NE/grilles/base-41.csv) · [Vérification dans mGBA](mgba/usa-a4ne.md#partie-normale)

Les attributs décrivent le terrain au chargement des plans de base ou des retouches. Les cultures et d’autres actions du moteur peuvent modifier les attributs et les scripts en cours de jeu. Le plan graphique choisi et le lieu logique sont des identifiants distincts. [Chargement des plans](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/world_map.cc#L1012-L1026) · [Application des retouches](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/world_map.cc#L1135-L1158) · [Sélection des plans](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/map_selection.c)

## Reproduire l’export

La commande vérifie l’empreinte de la ROM d’origine et écrit les CSV dans un nouveau dossier. Le même outil lit la ROM A4NP de référence avec ses propres offsets.

```sh
python3 outils/evenements/exporter_terrain.py roms/A4NE.gba exports/terrain-a4ne
```
