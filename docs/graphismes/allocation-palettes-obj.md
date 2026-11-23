# Allocation des palettes OBJ du monde

`GameSceneWorld::vfunc_48` choisit une **ressource de palette OBJ** pour un type de sprite. Au mariage de la Déesse des récoltes (`0848`), le marqueur romantique `371` active une allocation spéciale à l’église. Dans les deux éditions, les sept lutins se répartissent sur les **ressources `6`, `7` et `8`**, associées aux banques matérielles OBJ `4`, `5` et `6` dans les captures. [Mesures de la cérémonie](../../ressources/donnees/palettes-obj/Palettes-ceremonie-OBJ-FoMT.csv) · [Routine de sélection](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world.cc#L6794-L7003)

## De la ressource à la banque GBA

Le contrôleur du sprite conserve l’index retourné par `vfunc_48`. Le cache du monde contient **22 ressources** de `0x84` octets et **13 places** dans le pool de banques OBJ. `GetSpritePaletteBank` résout l’index de ressource vers une banque GBA. Une banque contient 16 couleurs sur 32 octets. [Constructeur du sprite](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_sprite.cc#L10-L30) · [Structures du cache](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/world_runtime.hh#L21-L73) · [Résolution de la banque](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world_interface.cc#L109-L126)

Un index fixe peut être renvoyé même si le drapeau d’occupation de la ressource est déjà actif. Pour une recherche, la routine prend la première ressource libre à partir de l’index de départ et active son octet `+0x81`. Si toute la plage est occupée, elle renvoie `21` sans modifier de drapeau. Le pool matériel renvoie `-1` si ses 13 cases sont déjà affectées. [Essais de remplissage](../../ressources/donnees/palettes-obj/Cache-OBJ-FoMT.csv) · [Saturation du pool et transferts DMA](banques-obj.md)

## Cérémonie à l’église

Le planificateur `0983` sélectionne `0848` quand la demande à la Déesse est terminée, que le mariage reste à commencer et que la saison et le jour correspondent à la date prévue. La préparation a mis le compteur de la Déesse à `5` et la date du mariage au 3 printemps, an 1. Après confirmation du sommeil, le jeu a lancé `0848`, montré les sept lutins à l’église et atteint le premier dialogue de Carter au PC `0x243`. Le script fixe les positions des acteurs à son arrivée sur la carte. [Planificateur](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_SystemEvent_ScheduleDailyEvents.mary.c#L43-L55) · [Positions de la cérémonie](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_WeddingEvent_HarvestGoddess_CeremonyAndNicknameSelection.mary.c#L87-L112)

| Lutins | Types de palette | Ressource | Banque OBJ observée |
| --- | --- | ---: | ---: |
| Staid, Bold, Chef | `19`, `21`, `22` | `6` | `4` |
| Nappy, Aqua, Timid | `20`, `23`, `25` | `7` | `5` |
| Hoggy | `24` | `8` | `6` |

Le cœur mGBA 0.10.5 instrumenté a relevé les retours de `vfunc_48` sur la carte `0x000C`. Pour chaque lutin, l’index lu dans son contrôleur correspond au retour natif. Le cache donne la banque, également relevée dans les entrées OBJ visibles. Les CSV conservent les coordonnées et les empreintes des 32 octets de chaque banque. [Contrôleur des lutins](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/harvest_sprite_actor.cc#L14118-L14187) · [États et empreintes](../../ressources/donnees/palettes-obj/Contextes-ceremonie-OBJ-FoMT.csv)

## Sondage par carte

**39 176 sélections** ont été exécutées dans Unicorn sur la routine du monde des éditions USA et Europe. Le sondage couvre les **564 valeurs de carte de `0x0000` à `0x0233`**, les types `0` à `33`, les variantes de trois événements et quatre cas de remplissage. Chaque appel travaille sur une copie de la RAM d’un état mGBA. Les deux éditions donnent les mêmes retours et les mêmes changements d’occupation. [Index par carte](../../ressources/donnees/palettes-obj/Allocation-OBJ-FoMT.csv) · [Variantes](../../ressources/donnees/palettes-obj/Variantes-OBJ-FoMT.csv)

- À l’église, le marqueur `371` réserve les ressources `6` à `8` aux groupes ci-dessus. La recherche des autres types dynamiques commence à `9`. Inscrire `371` dans le registre avec un marqueur vide donne le résultat du témoin.
- Au restaurant de Kai (`0x0024`), l’état `1` de la variable `300` applique le même regroupement. Les états `0`, `2` et `3` suivent la règle habituelle de la carte.
- Au sommet de la colline (`0x0008`), l’état `1` de la variable `342` attribue la ressource `7` au type `28` et fait commencer la recherche à `8`. Le type `29` conserve la ressource fixe `6`.

## Reproduire les relevés

L’extracteur utilise la routine `0x0801B5C0` en USA et `0x0801B5D4` en Europe. Les bornes de carte du CSV sont inclusives. `premiere_ressource` donne l’index fixe ou le début de la recherche et `resultat_cache_vide` contient le retour avec les drapeaux d’occupation à zéro. [États de départ](../../ressources/donnees/palettes-obj/Contextes-OBJ-FoMT.csv)

```sh
python3 -m pip install unicorn==2.1.4
python3 outils/jeu/relever_palettes_obj.py roms/A4NE.gba roms/A4NP.gba exports/palettes-obj \
  etats/after-sleep-steady.state etats/Harvest-Moon-Europe.ss1
```

Pour la cérémonie, enregistrer un état de confirmation du sommeil (`0342`, PC `0x50`) au 2 printemps, an 1. L’outil prépare trois octets dans une copie de l’image de sauvegarde. Charger cette copie, confirmer le sommeil et avancer jusqu’à l’église. Le code de `0848` vaut `0x083750AC` pour USA et `0x08375104` pour Europe. [Repères du sommeil et inspection des états](../mgba/usa-a4ne.md)

```sh
python3 outils/mgba/preparer_mariage_deesse.py sommeil.state mariage-deesse.state
```
