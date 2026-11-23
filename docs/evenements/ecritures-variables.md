# Décomposition des écritures `VarSet`

L’export retrouve les deux arguments des **1 850 instructions `VarSet`** dans les ROM USA et Europe. Chaque écriture vise un ID de variable littéral. Les **214 sites** qui demandaient une analyse de pile fournissent maintenant une expression source. Les deux ROM produisent les mêmes expressions aux mêmes positions relatives dans `CODE`. [Écritures et origines](../../ressources/donnees/ecritures-variables/) · [Tables natives](routines-natives.md)

| Forme de la valeur | Sites | Exemple |
| --- | ---: | --- |
| Littéral | 1 636 | Le script `0657` transmet `1`, puis `2`, à l’état de grossesse de Karen (`198`). |
| Calcul | 139 | À `0x2C55F5` dans `0098`, le compteur des Joyaux de vérité (`340`) reçoit `VarGet(340) + 1`. Le relevé totalise 131 additions et 8 soustractions. |
| Lecture d’une locale | 69 | Un résultat d’écran de télévision passe par une locale avant d’être écrit dans l’argument partagé (`580`). |
| Retour direct d’une routine native | 6 | À `0x2C59F1` dans `0104`, le résultat `RunFrisbeeGame(1)` est transmis à `VAR_FRISBEE_TOURNAMENT_RESULT` (`405`). |

Les autres retours directs proviennent du choix du cadeau dans la chaussette (`SelectThomasStockingGift`), du tirage de la catégorie du concours de cuisine (`RandomIntInclusive(0, 4)`), du choix du partenaire de la fête de la lune (`SelectMoonViewingPartner`), de la note du plat (`GetCookingFestivalDishRating`) et du concours de poules (`RunChickenFestivalContest`). [Déclarations Mary des routines](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/eu/fomt_callables.mary.h)

## Origine des variables locales

Les **69 écritures d’une valeur locale** visent toutes `VAR_SHARED_CALLED_SCRIPT_ARGUMENT` (`580`). Le graphe mène à au moins une affectation de la locale par `ShowTelevisionMessage` pour chacune. Le CSV associe chaque écriture aux affectations qui peuvent l’atteindre selon les branches du bytecode. Il contient **1 013 paires écriture–affectation**. Pour **45** écritures, une seule affectation est trouvée. Pour les **24** autres, plusieurs affectations sont possibles et le graphe contient aussi un chemin qui remonte à la valeur initiale de la locale. Les locales commencent à zéro lors du chargement d’un script. L’analyse de graphe n’évalue pas les conditions. Un chemin vers la valeur initiale peut donc être exclu en jeu. [Initialisation de la VM](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_vm.cc#L18-L80) · [Affectations relevées](../../ressources/donnees/ecritures-variables/Origines-locales-VarSet-FoMT.csv)

Dans `1048`, *Mineral Town Friends*, l’écran d’introduction relève une entrée de télécommande, puis son retour est enregistré dans la locale `0`. Quand le joueur demande une autre chaîne, le script transmet la valeur au programme suivant par l’ID `580`. Cette première branche et les branches équivalentes expliquent les **40 sites** de ce type dans `1048`. L’argument de `ShowTelevisionMessage` désigne l’entrée `STR` du script courant. [Script de l’émission](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/eu/EventScript_TV_MineralTownFriends_CharacterProfiles.mary.c#L1213-L1235) · [Lecture de l’entrée STR](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L10416-L10453)

## Lire les CSV et réutiliser les expressions

- `Ecritures-decomposees-FoMT.csv` conserve les offsets A4NE/A4NP de l’appel et du début de sa préparation, l’ID de variable, une expression lisible et son équivalent JSON. `pc_code` est relatif au début des instructions de `CODE`.
- `Origines-locales-VarSet-FoMT.csv` relie `script` et `pc_varset` à l’offset d’une affectation possible. `pc_affectation` est également relatif à `CODE`. La colonne `expression_json` de cette table décrit la valeur produite à l’affectation.

| Forme JSON | Éléments, dans l’ordre |
| --- | --- |
| `litteral` | Valeur entière |
| `locale` | Index de la locale, PC de lecture |
| `binaire` | Opérateur, expression de gauche, expression de droite |
| `natif` | ID natif décimal, symbole, expressions des arguments |

Exemple structurel pour le tirage de la catégorie de cuisine dans `0982`.

```json
["natif",60,"RandomIntInclusive",["litteral",0],["litteral",4]]
```

La décomposition remonte les instructions de pile dans une suite de prédécesseurs adjacents. Les positions des sauts ordinaires et des cas `JUMP` délimitent les chemins analysés. Pour les valeurs passées directement par une locale, la recherche remonte les dernières affectations possibles depuis le point de lecture. Les expressions décrivent les arguments de `VarSet`. Les transformations au stockage et les notifications s’effectuent ensuite dans le moteur natif. [Instructions de la VM](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_vm.cc#L196-L590) · [Écriture et notification](routines-natives.md#variables-lues-écrites-et-notifiées)

Les 911 couples ID–valeur littérale distincts font partie des 30 146 essais qui suivent l’écriture jusqu’aux octets modifiés et à la relecture native. [Écritures natives et notifications](ecritures-natives.md)

## Reproduire l’export

L’outil vérifie les ROM et réutilise les signatures et ID déjà vérifiés dans les CSV des routines natives. Le dossier de destination reçoit deux CSV.

```sh
python3 outils/evenements/decomposer_ecritures.py \
  roms/A4NE.gba roms/A4NP.gba exports/ecritures-variables
```
