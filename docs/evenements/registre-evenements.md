# Registre des événements actifs et musique de scène

Dans les ROM USA et Europe, les **quatre appels directs** à `HasRegisteredEvents` servent à décider si le monde doit demander sa musique de fond. La routine teste si le compteur `u32` à `GameStateSaveImage + 0x214C` est non nul. Lors de l’annonce de grossesse de Karen (`0657`), vider le registre fait demander la musique de la ville à l’arrivée à la clinique. Le diagnostic et l’annonce s’affichent dans les mêmes conditions d’essai. [Appels ROM](../../ressources/donnees/registre-evenements/Appels-registre-FoMT.csv) · [Traces mGBA](../../ressources/donnees/registre-evenements/Trace-clinique-FoMT.csv)

## Appels dans le moteur

| Appelant | Offset du `BL` A4NE | Offset du `BL` A4NP | Condition observée dans le code |
| --- | ---: | ---: | --- |
| Construction de `GameSceneWorld` | `0x01775E` | `0x017772` | Si la mise à jour audio est demandée, garder la musique courante quand elle est active et que le registre est rempli. |
| `GameSceneWorld::Update` | `0x018292` | `0x0182A6` | Au changement du niveau de fatigue, actualiser la musique si elle est déjà active et si le registre est vide. |
| `GameSceneWorld::ChangeMap` | `0x019ECC` | `0x019EE0` | Si la mise à jour audio est demandée, garder la musique courante quand elle est active et que le registre est rempli. |
| `func_0801EAA0` | `0x01EDC8` | `0x01EDDC` | Actualiser la musique en fin de traitement si elle est active et si le registre est vide. |

`UpdateWorldBackgroundAudio` choisit la séquence par défaut de la carte avec les paramètres de fatigue et, dans les mines, de profondeur. Les quatre appels mènent à `HasRegisteredEvents` en `0x0809C5F4` (USA) ou `0x0809C624` (Europe). Le relevé vérifie aussi les deux appels d’inscription et de retrait depuis `VarSet`. [Construction](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world.cc#L373-L398) · [Mise à jour](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world.cc#L816-L823) · [Changement de carte](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world.cc#L4265-L4290) · [Mise à jour audio](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_world.cc#L13459-L13485)

Le champ `u16` à `+0x2158` est le marqueur romantique comparé à un ID précis par `IsActiveRomanceEvent`. Il fait l’objet de huit appels directs aux routines de comparaison, d’écriture et d’effacement. Le registre à `+0x214C` a son propre compteur et contient jusqu’à trois ID. [Structure](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/event_state.hh#L9-L52) · [Table des 14 appels](../../ressources/donnees/registre-evenements/Appels-registre-FoMT.csv)

## Passage de la ferme à la clinique

Les six essais partent du dernier dialogue à la ferme (`0657`, PC `0xFE`). Dans chaque édition, l’état témoin a été obtenu en confirmant le sommeil après la préparation de la progression. Les deux variantes modifient une copie de cet état. Le drapeau de grossesse à `+0x2168` reste à l’état `1` dans les trois cas. [Préparation du sommeil](../mgba/usa-a4ne.md#test-ciblé-de-karen) · [Script de la scène](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_FamilyEvent_Karen_PregnancyDiscovery.mary.c#L83-L125)

| Variante | Compteur | Première case brute | Séquences demandées, dans l’ordre | Diagnostic et annonce |
| --- | ---: | ---: | --- | --- |
| Témoin | 1 | `198` | `17` (musique de scène) | Atteints |
| Compteur mis à zéro | 0 | `198` | `13` (Mineral Town), puis `17` (musique de scène) | Atteints |
| ID remplacé | 1 | `0xFFFF` | `17` (musique de scène) | Atteints |

Le témoin et le remplacement de l’ID renvoient `1` dans `HasRegisteredEvents` et `IsBackgroundMusicActive`. Avec le compteur à zéro, `ChangeMap` appelle `UpdateWorldBackgroundAudio`, qui demande la séquence `13`. Le script demande la séquence `17` dans tous les cas. Le relevé observe les appels à `PlayBGM` et le numéro transmis dans `r2`. La sortie sonore reste à mesurer. Dans les six essais, l’interpréteur atteint le diagnostic à `0x1C0` et l’annonce à `0x1FC` sans changer d’ID de script. [Mesures](../../ressources/donnees/registre-evenements/Essais-clinique-FoMT.csv) · [Index audio](../../ressources/donnees/audio/A4NE/Sequences-A4NE.csv)

## Reproduire le relevé

L’index vérifie les SHA-1 des ROM et décode les `BL` Thumb qui ciblent les six routines. Ses colonnes `site_*_rom` et `cible_*_rom` sont des offsets dans les ROM. Les traces mGBA utilisent des adresses GBA.

```sh
python3 outils/evenements/exporter_registre.py roms/A4NE.gba roms/A4NP.gba Appels-registre-FoMT.csv
```

Pour tester la scène, partir de l’état du choix de dormir (`0342`, PC `0x50`) et utiliser `preparer_karen.py` sans option. L’outil accepte les états PNG et bruts des deux éditions. Après avoir confirmé le sommeil, avancer au dernier dialogue de Karen à la ferme et y enregistrer un état `clinique-source.state`. Son code doit être `0x08345884` en USA ou `0x083458DC` en Europe, avec le PC `0xFE`. [Vérifier le PC d’un état](../mgba/usa-a4ne.md)

```sh
python3 outils/mgba/preparer_karen.py --registre vide clinique-source.state clinique-vide.state
python3 outils/mgba/preparer_karen.py --registre id-substitue clinique-source.state clinique-id-substitue.state
```

Charger le témoin et les deux copies dans mGBA 0.10.5. Faire avancer le dialogue avec A jusqu’au diagnostic puis jusqu’à l’annonce. Les essais publiés utilisent le cœur Libretro instrumenté pour relever les PCs natifs et les registres CPU. Dans le débogueur mGBA, les points correspondants sont le retour du test de registre (`0x08019ED0` USA, `0x08019EE4` Europe) et l’entrée de `PlayBGM` (`0x080123CC` USA, `0x080123E0` Europe). [PC et registres relevés](../../ressources/donnees/registre-evenements/Trace-clinique-FoMT.csv)
