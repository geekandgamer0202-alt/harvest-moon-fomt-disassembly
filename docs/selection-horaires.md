# Sélection des horaires selon la date et la météo (A4NE)

Les 32 sélecteurs natifs ont été appelés pour les 120 jours de l’an 1, à 06:00, avec chacun des cinq codes météo et dans chacun de deux états mGBA 0.10.5. Le relevé compte **38 400 appels** et **122 cases de variante distinctes** sur les 254 stockées dans la ROM. Parmi les 122 cases renvoyées, 116 pointent vers un horaire. [CSV de sélection](../ressources/donnees/selecteurs/A4NE/) · [Horaires et trajets](horaires.md)

## États de départ

| Contexte | Origine |
| --- | --- |
| `after-sleep-steady` | Réveil dans la maison après le premier sommeil, le 3 printemps de l’an 1 à 06:00. [Partie normale](mgba/usa-a4ne.md#partie-normale) |
| `karen-announcement` | Annonce de la grossesse à la clinique, le 5 été de l’an 1 à 06:00, après avoir joué la scène depuis un état de sommeil préparé. [Essai Karen](mgba/usa-a4ne.md#test-ciblé-de-karen) |

L’outil charge une copie de la mémoire EWRAM et IWRAM de chaque état. Il balaie le champ météo à `0x020025E0` et le calendrier à `0x020025E8`, puis passe à chaque fonction Thumb le pointeur `0x020025D8` de la structure de partie. Le code exécuté vient de la ROM A4NE. La pile est réinitialisée à chaque appel. Unicorn exécute les instructions et l’outil fournit la division entière du BIOS (`SWI 0x06`). [Structure de la sauvegarde](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/game_state_types.hh#L214-L220) · [Calendrier compact](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/time_of_day_types.hh) · [Services arithmétiques du BIOS](https://mgba-emu.github.io/gbatek/#bios-arithmetic-functions)

Le balayage force les combinaisons de date et de météo, y compris celles que le jeu peut exclure. Les drapeaux et la progression familiale conservent les valeurs de l’état de départ pour toutes les dates. Les résultats décrivent le retour des sélecteurs. L’application de l’horaire, les changements de lieu et les interruptions dues aux événements se vérifient séparément en jeu. [Utilisation des horaires par le moteur](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/npc_entity.cc#L175-L370)

## Lire les fichiers

| Fichier | Lignes | Contenu |
| --- | ---: | --- |
| [Contextes](../ressources/donnees/selecteurs/A4NE/Contextes-A4NE.csv) | 2 | SHA‑256 du fichier d’état utilisé, année et heure du balayage |
| [Choix par jour](../ressources/donnees/selecteurs/A4NE/Choix-horaires-An1-A4NE.csv) | 7 680 | Un personnage et une date par ligne dans chaque contexte, avec cinq retours de variante |
| [Fréquences](../ressources/donnees/selecteurs/A4NE/Frequences-horaires-An1-A4NE.csv) | 508 | Nombre de retours pour chacune des 254 cases dans chaque contexte, y compris les cases jamais sélectionnées |

Les colonnes `meteo_0` à `meteo_4` correspondent dans l’ordre au soleil, à la pluie, à la neige, au typhon et à la tempête de neige. Joindre `id_pnj` et `variante` à la table des variantes pour retrouver l’offset de l’horaire. Dans le fichier de fréquences, `horaire_present = 0` signifie que le pointeur stocké dans la case est nul. `nombre_cas = 0` indique que le sélecteur n’a jamais renvoyé cette case dans le contexte balayé. [Enum météo](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/fomt_constants.mary.h#L7208-L7212) · [Table des variantes](../ressources/donnees/horaires/A4NE/Variantes-horaires-A4NE.csv)

## Résultats vérifiés

- Dans les deux contextes, **17 sélecteurs** changent de variante avec la météo au moins un jour. Par exemple, le 3 printemps, Rick choisit `3` par soleil et `2` sous les quatre autres codes.
- Zack prend la variante `2` aux **14 dates** de la liste partagée et `1` les 106 autres jours, pour les cinq codes et dans les deux contextes. Van et Lou renvoient `0` dans les deux états, antérieurs à leurs introductions. [Dates de la liste](../ressources/donnees/horaires/A4NE/Dates-selection-horaires-A4NE.csv) · [Conditions d’introduction](horaires.md#conditions-repérées)
- **Karen** est le seul personnage dont les retours changent entre les deux contextes à date et météo identiques. Le réveil normal donne les variantes `1`, `2`, `3`, `4`, `5` et `8`. L’état de l’annonce donne `14`, `19`, `21` et `22`. La routine vérifie explicitement si l’ID de la conjointe vaut `19`. Dans cette branche, les 9 et 13 automne donnent respectivement `21` et `22` avant les tests de météo, ce que confirme le relevé. [Routine native de Karen](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/npc_schedule_karen.cc#L24-L85)

## Refaire le relevé

Utiliser la ROM A4NE révision 0 et des états instantanés A4NE enregistrés dans mGBA 0.10.5. Les fichiers exacts du relevé sont identifiés par SHA‑256. Avec des captures locales réalisées selon le même parcours, les résultats dépendent des drapeaux et de la progression enregistrés. Le nom de fichier sans extension sert d’identifiant de contexte.

```sh
python3 -m pip install unicorn==2.1.4
python3 outils/jeu/relever_selecteurs.py roms/A4NE.gba exports/selecteurs-a4ne \
  exports/mgba/after-sleep-steady.state exports/mgba/karen-announcement.state
```
