# Marqueur romantique et compteurs de progression

Les ROM USA et Europe utilisent **63 variables** qui partagent le marqueur romantique `u16` à `GameStateSaveImage + 0x2158`. Le relevé retrouve leur personnage, leur compteur et le seuil transmis aux routines natives. Il relie ces variables à **230 appels `VarSet` dans 103 scripts**. Les paramètres observés dans les deux éditions concordent. [Variables](../../ressources/donnees/romance/Variables-romance-FoMT.csv) · [Sites dans le bytecode](../../ressources/donnees/romance/Scripts-romance-FoMT.csv)

## Interpréter les états `0`, `1` et `2`

Le moteur partage deux compteurs par personnage. **32 variables** utilisent la progression avec le joueur et **31** celle des couples rivaux. Chaque `VarGet` de ce groupe compare d’abord son ID au marqueur. Une correspondance renvoie `1`. Sans correspondance, le compteur donne `2` s’il atteint le seuil et `0` s’il est en dessous. `0xFFFF` est la valeur du marqueur vide. [Lecture native](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L11564-L11614) · [Structure des compteurs](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/bachelorette.hh#L31-L43)

| Argument `VarSet` | Effet dans la routine commune | Sites dans les scripts |
| ---: | --- | ---: |
| `0` | Efface le marqueur s’il contient l’ID écrit. Le compteur reste à sa valeur antérieure. | 6 |
| `1` | Inscrit l’ID dans le marqueur si le compteur est inférieur au seuil. Une inscription peut remplacer l’ID précédent. | 132 |
| `2` | Fait avancer le compteur jusqu’au seuil s’il est en dessous, puis efface le marqueur si l’ID correspond. L’appel peut faire avancer un événement même sans inscription préalable. | 92 |

Au passage à `2`, le moteur peut fixer une date de mariage quand le compteur du joueur vaut `5`. Il part de la date du jeu plus sept jours et écarte les anniversaires du couple et les dates indisponibles. Les six demandes en mariage testées fixent le 10 printemps dans le contexte USA du 3 printemps et le 9 printemps dans le contexte Europe du 2 printemps. Les seuils du mariage lui-même valent `6`. [Écriture et progression](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L12249-L12334) · [Calcul de la date](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L12335-L12578) · [1 152 transitions relevées](../../ressources/donnees/romance/Transitions-romance-FoMT.csv)

### Scripts et compteurs partagés

- La scène du cœur jaune de Karen (`0029`) demande `1` puis `2` pour la variable `74`, selon les branches. Le seuil est `4` sur le compteur du joueur à `+0x1ECE`. La demande en mariage (`0033`) écrit `2` pour la variable `75`, de seuil `5` sur le même compteur. [Catalogue des scènes](catalogue-a4ne.csv) · [Sites `VarSet`](../../ressources/donnees/romance/Scripts-romance-FoMT.csv)
- Les six écritures de `0` se trouvent dans la sortie de l’église (`0143`, cinq variables de mariage rival) et dans la réponse à la demande en mariage de la Déesse (`0847`, variable `370`). [Sortie de l’église](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_LocationTransition_ExitChurchWithEventStateCleanupAndMusicFestivalGuard.mary.c) · [Demande à la Déesse](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_LoveEvent_HarvestGoddess_ProposalResponse.mary.c)
- Les variables `117`, `118` et `119` de Rick et Karen partagent le seuil rival `5`. Dans l’essai, compléter `119` pendant que `118` est marqué fait passer `119` à `2`. `118` reste à `1` jusqu’à l’effacement de son marqueur. [Séquence `seuil_rival_partage`](../../ressources/donnees/romance/Transitions-romance-FoMT.csv)

Le registre d’événements à `+0x214C` est mis à jour par la notification quand la valeur relue de la variable écrite change. Dans une séquence d’essai, écrire `70 = 1` puis `71 = 1` remplace le marqueur `70` par `71` et laisse les deux ID inscrits dans le registre. `VarGet(70)` est alors déjà revenu à `0`. Écrire ensuite `70 = 0` laisse son inscription en place, car sa valeur relue reste `0`. Cette séquence vérifie un cas construit en laboratoire à partir d’un état de début de partie. [Séquence `deux_ouvertures`](../../ressources/donnees/romance/Transitions-romance-FoMT.csv) · [Notification après `VarSet`](ecritures-natives.md#registre-des-événements-actifs)

## Priorité du sprite à la clinique

Lors de la création du contrôleur visuel du joueur à la clinique (`0x0013`), le moteur choisit la priorité OBJ `1` si l’état de malaise (`227`) vaut `1` ou si le marqueur romantique vaut `74`. Sinon, il choisit `2`. Huit essais mGBA, quatre par édition, reproduisent la transition de `0657` vers la clinique. Chaque variante modifie un seul champ de l’état témoin. Les états atteignent tous le diagnostic au PC `0x1C0`. [Mesures](../../ressources/donnees/romance/Priorite-clinique-FoMT.csv) · [Branche du joueur](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/player_actor.cc#L1579-L1617) · [Champ de priorité](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/entity_actor.hh#L105-L121)

| Variante | Marqueur | ID au registre | État du malaise | Priorité OBJ |
| --- | ---: | ---: | ---: | ---: |
| Témoin | `0xFFFF` | `198` | `0` | `2` |
| ID `74` dans le marqueur | `74` | `198` | `0` | `1` |
| ID `74` dans le registre | `0xFFFF` | `74` | `0` | `2` |
| Malaise actif | `0xFFFF` | `198` | `1` | `1` |

Le cœur Libretro instrumenté relève l’instruction qui écrit l’octet `PlayerActor + 0x21`. La valeur est lue dans l’EWRAM au diagnostic. À l’église, le marqueur `371` sélectionne des ressources de palettes OBJ pour les lutins. Le script `0848` fixe leurs coordonnées. Les deux comportements ont été vérifiés pendant la cérémonie USA et Europe. [Appels ROM](../../ressources/donnees/registre-evenements/Appels-registre-FoMT.csv) · [Palettes de la cérémonie](../graphismes/allocation-palettes-obj.md#cérémonie-à-léglise)

## Reproduire les relevés

L’outil Python exécute les 590 lectures et écritures isolées dans Unicorn, repère les appels aux deux routines communes et relève leurs arguments dans les registres et sur la pile. Il rejoue ensuite les transitions sur une copie des états mGBA. Les offsets des compteurs sont relatifs à `GameStateSaveImage`. Les colonnes `lecture_*_rom`, `ecriture_*_rom` et `site_*_rom` sont des offsets ROM. [Empreintes des états](../../ressources/donnees/romance/Contextes-romance-FoMT.csv)

```sh
python3 -m pip install unicorn==2.1.4
python3 outils/jeu/relever_romance.py roms/A4NE.gba roms/A4NP.gba exports/romance \
  etats/after-sleep-steady.state etats/Harvest-Moon-Europe.ss1
```

Pour l’essai de priorité, partir du dernier dialogue à la ferme, `0657` au PC `0xFE`. Utiliser successivement `marqueur`, `registre` et `malaise` comme valeurs de `--priorite-clinique`, vers trois fichiers distincts. Dans mGBA, avancer avec A jusqu’au diagnostic. L’écriture de la priorité se trouve à `0x08024BCE` en USA et `0x08024BE2` en Europe. [Créer l’état de référence](registre-evenements.md#reproduire-le-relevé)

```sh
python3 outils/mgba/preparer_karen.py --priorite-clinique marqueur clinique-source.state clinique-marqueur.state
```
