# Événements et scripts A4NE

Cette analyse porte sur la révision 0 américaine de *Harvest Moon: Friends of Mineral Town* (SHA-1 `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963`). Les identifiants de script sont décimaux et les offsets de fichiers sont hexadécimaux. Pour obtenir une adresse GBA à partir d’un offset de fichier, ajouter `0x08000000`.

Les dialogues et catalogues d’origine accompagnent les index d’analyse. [Fichiers USA](../../ressources/textes/A4NE/) · [Fichiers Europe](../../ressources/textes/A4NP/) · [Catalogue BFGE](../../ressources/evenements/BFGE/)

- [Catalogue annoté A4NE](catalogue-a4ne.csv) et [catalogue annoté A4NP](catalogue-a4np.csv) réunissent les 1 328 événements par édition avec les fonctions, conditions, liens et preuves relevés au cours de l’analyse. Le catalogue A4NP conserve les observations européennes. Le catalogue A4NE indique les points d’entrée confirmés pour la ROM américaine ainsi que les appels et affectations du bytecode.
- [Scripts A4NE](scripts-a4ne.csv) situe les 1 328 blocs d’événement, leur bytecode et leurs tables. Le décompte des 8 368 chaînes correspond aux entrées des blocs `STR ` des scripts.
- [Sites d’appel A4NE](appels-a4ne.csv) donne l’adresse de chacune des 696 instructions `CallScript` et des 459 instructions `SetEntityEventScript`, ainsi que son script d’origine et sa cible. Une affectation fixe un dialogue pour un acteur. Elle peut prendre effet lors d’une interaction ultérieure.
- [Routines natives et variables](routines-natives.md) relie les 75 522 instructions d’appel natif aux destinations Thumb USA et Europe. Les index incluent les tables de lecture, d’écriture et de notification des variables.
- [Décomposition des écritures](ecritures-variables.md) donne l’ID de variable et l’expression transmise aux 1 850 appels `VarSet`.
- [Lectures de l’état du jeu](lectures-variables.md) situe les champs lus par les 590 ID `VarGet` et documente les 485 formules de lecture par masque testées.
- [Écritures natives et notifications](ecritures-natives.md) décrit les octets changés par `VarSet`, le registre de trois événements actifs et le drapeau de marche de l’enfant.
- [Registre des événements et musique de scène](registre-evenements.md) situe les appels qui consultent le registre et mesure son effet lors du passage de la ferme à la clinique.
- [Progression romantique](romance.md) relie le marqueur aux 63 variables, à leurs compteurs et aux 230 écritures dans les scripts.
- [Événements familiaux](vie-de-famille.md) décrit la chaîne du réveil, les conditions et les essais mGBA. Le [tableau des scènes](vie-de-famille-a4ne.csv) situe les 24 branches d’annonce, de naissance, de chute du lit et de premiers pas.
- [Audit de quatorze déclencheurs](declencheurs-14.md) documente les références vérifiées, les interactions voisines et les essais précédemment réalisés sur l’édition européenne. Les résultats des recherches de pointeurs A4NE sont aussi disponibles [en JSON](references-14-a4ne.json).

## Structure vérifiée

La table principale commence à `0x0F89D4`. La case `0000` est nulle. À partir de `0001`, les cases de quatre octets contiennent les adresses GBA des blocs `RIFF` de type `SCR `, en ordre croissant. La valeur 32 bits à `RIFF + 4` indique la taille totale du bloc. Les sections portent chacune une taille de données. La section suivante commence à la fin de la taille déclarée. Les 1 328 blocs ont une section `CODE` puis une section `STR `, avec `JUMP` entre les deux dans 237 blocs.

- Le contenu de `CODE` débute par une longueur 32 bits. Dans le CSV, `code_rom` pointe vers la première instruction. L’opcode VM `0x21` appelle la routine native désignée par son opérande 32 bits. Le répartiteur A4NE commence à `0x03F8DC`, sa table de 327 pointeurs est à `0x03F904`, et les entrées `0x037` et `0x089` pointent respectivement vers `0x08040FBC` et `0x08041F80`.
- `JUMP` contient les groupes utilisés par les sélections multiples. `tables_saut` compte ces groupes pour chaque script. `STR ` contient un nombre d’entrées, des offsets relatifs à la zone des chaînes, puis les chaînes terminées par un octet nul.
- Dans les deux familles d’appels indexées, la cible est empilée juste avant l’instruction. Les sites sont des références statiques à l’intérieur des scripts. Les circonstances d’exécution dépendent de la branche prise et de l’état du jeu.
- 29 scripts débutent par `END` (`0x20`) et ont zéro chaîne. Leur indicateur `fin_immediate_sans_chaine` vaut `1`.

La comparaison A4NE/A4NP a donné les mêmes blocs `CODE` et `JUMP` pour les 1 328 scripts. Le bloc `STR ` du script `1008` est le seul qui diffère. En comparant les contenus de chaque entrée, seule `1008.00` change. Le catalogue A4NE utilise les adresses lues dans la table américaine.

## Reproduire l’index

Depuis la racine du dépôt, utiliser Python 3 et une copie locale de la ROM. Le script vérifie le code de région et le SHA-1 puis envoie uniquement les métadonnées sur la sortie standard.

```sh
mkdir -p exports
python3 outils/evenements/indexer_scripts.py roms/fomt-a4ne.gba > exports/scripts-a4ne.csv
python3 outils/evenements/indexer_scripts.py roms/fomt-a4ne.gba --appels > exports/appels-a4ne.csv
python3 outils/evenements/indexer_scripts.py roms/fomt-a4ne.gba --audit-quatorze > exports/references-14-a4ne.json
python3 outils/evenements/indexer_scripts.py roms/fomt-a4ne.gba --comparer roms/fomt-a4np.gba
python3 outils/evenements/auditer_terrain.py roms/fomt-a4ne.gba
```

Les noms symboliques utilisés dans les notes suivent le [projet de désassemblage Wokann](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/fomt_scripts.mary.h).
