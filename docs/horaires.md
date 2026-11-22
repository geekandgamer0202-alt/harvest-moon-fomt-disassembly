# Horaires et trajets des personnages A4NE

Le relevé suit les 32 descripteurs `ScheduleInfo` stockés entre `0x0F1A80` et `0x0F89D4` dans la ROM USA. Chaque descripteur lie un personnage à sa fonction de sélection et à ses horaires possibles. Les noms de personnage et de lieu suivent les identifiants de la décompilation FoMT. [CSV A4NE](../ressources/donnees/horaires/A4NE/) · [Ordre des objets dans la ROM USA](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/fomt_us.lds#L526-L558) · [Structures natives](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/npc_schedule.hh)

| CSV | Lignes | Données |
| --- | ---: | --- |
| [Personnages](../ressources/donnees/horaires/A4NE/Personnages-horaires-A4NE.csv) | 32 | ID du personnage, descripteur et adresse Thumb de son sélecteur |
| [Variantes](../ressources/donnees/horaires/A4NE/Variantes-horaires-A4NE.csv) | 254 | Cases du tableau de choix, dont 222 avec un horaire et 32 avec un pointeur nul |
| [Étapes des horaires](../ressources/donnees/horaires/A4NE/Etapes-horaires-A4NE.csv) | 1 122 | Minutes du jeu, heure affichée, jour civil et pointeur du trajet |
| [Trajets](../ressources/donnees/horaires/A4NE/Trajets-horaires-A4NE.csv) | 430 | Lieu logique, coordonnées et orientation de départ, format et nombre de points |
| [Points des trajets](../ressources/donnees/horaires/A4NE/Points-trajets-A4NE.csv) | 1 352 | Coordonnée sur un axe, instant ou vitesse, champs natifs et octets d’origine |
| [Dates de sélection](../ressources/donnees/horaires/A4NE/Dates-selection-horaires-A4NE.csv) | 14 | Dates de la liste partagée à `0x0F1A66` |

## Lire un trajet

1. Dans les étapes, filtrer le personnage et le numéro de variante. Le temps est compté depuis **06:00**. Une heure après minuit porte `decalage_jour_civil = 1` et appartient toujours à la journée de jeu en cours.
2. Joindre `trajet_rom` au tableau des trajets. Le lieu est le `MaryMapId` logique. `MAP_NONE` (`564`) est l’identifiant spécial d’absence de lieu. Les coordonnées de départ sont en pixels.
3. Pour un trajet qui se déplace, retrouver ses points par `trajet_rom`. En format A, `minutes_depuis_etape` fixe l’instant du point. En format B, les points utilisent une vitesse et une orientation. Le champ natif `+0x04` du format B est conservé sous `champ_04_rom`. `x` ou `y` indique la coordonnée visée par le point.

Plusieurs étapes peuvent partager le même trajet. Un trajet de zéro point fournit une position fixe. Le moteur lit la variante active selon l’état de la partie et choisit l’étape en fonction de l’heure. [Sélection et mise à jour du trajet](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/npc_entity.cc#L175-L370) · [Identifiants des lieux](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/fomt_constants.mary.h#L8103-L8156)

## Conditions repérées

| Personnage | Variante et règle confirmée dans le code |
| --- | --- |
| Zack | La variante `1` est la tournée ordinaire. À **17:03**, son horaire indique la ferme `MAP_FARM` à `(244, 171)`. Le règlement intervient lorsque Zack atteint ce point. La variante `2` le laisse chez lui aux dates renvoyées par `IsNpcScheduleDateListed`. |
| Van | La variante `1` s’active le mercredi lorsque l’état de son introduction vaut `2`. Son point fixe est à l’étage de l’auberge. |
| Lou | La variante `1` s’active le dimanche lorsque l’état de son introduction vaut `2`. Son trajet se situe à l’étage de l’auberge. |

Les 14 dates de la liste partagée sont encodées avec `saison × 30 + jour − 1`. Chaque sélecteur décide comment utiliser la liste. Les CSV donnent les branches et trajets stockés. L’interprétation complète des sélecteurs et des interruptions dues aux événements reste à établir. [Routine de calendrier](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/npc_schedule.cc#L755-L790) · [Zack](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/npc_schedule_zack.cc) · [Van](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/npc_schedule_van.cc) · [Lou](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/npc_schedule_lou.cc)

## Reproduire l’export

La commande contrôle le code et le SHA-1 de la ROM A4NE, puis suit les pointeurs dans les blocs d’horaires. Elle crée les six CSV dans un nouveau dossier.

```sh
python3 outils/jeu/exporter_horaires.py roms/A4NE.gba exports/horaires-a4ne
```
