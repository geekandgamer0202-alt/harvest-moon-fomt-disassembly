# Lectures des variables dans l’image de sauvegarde

Les **590 ID de `VarGet`** ont été exécutés sur trois états de mGBA 0.10.5, soit **1 770 appels natifs**. Pour chaque ID, les adresses et largeurs observées sont identiques dans les trois états. **485 ID** suivent une même formule de lecture par masque sur tous les essais. Les champs associés occupent 145 octets distincts de l’image de sauvegarde en RAM. [CSV et empreintes des états](../../ressources/donnees/lectures-variables/) · [Adresses des routines natives](routines-natives.md)

| Résultat | ID | Vérification |
| --- | ---: | --- |
| Masque sur un octet | 436 | Les 256 valeurs possibles dans chacun des trois états. |
| Masque sur deux ou quatre octets | 49 | 98 mots pour chacun des 32 champs de deux octets et 130 pour chacun des 17 champs de quatre octets, dans chaque état. |
| Plusieurs lectures observées | 83 | Au moins deux couples adresse–largeur dans l’image. |
| Chemin qui varie | 17 | La modification du champ a changé les lectures de la routine. |
| Transformation | 4 | Les résultats ne suivent pas la formule du masque, par exemple l’année. |
| Lectures hors de l’image | 1 | Le plat du joueur au concours de cuisine (`401`) lit `0x020023DC` en EWRAM et `0x0300040C` en IWRAM. |

## Champs partagés

Le mot lu est interprété en *little-endian*. La formule est `((mot & masque) >> decalage) + biais`. Le résultat est ramené à un entier signé de 32 bits comme la valeur `r0` du moteur.

| ID | Variable | Offset dans l’image | Taille | Masque | Décalage | Biais |
| ---: | --- | --- | ---: | --- | ---: | ---: |
| 1 | Saison | `0x0011` | 1 | `0x03` | 0 | 0 |
| 2 | Jour du mois | `0x0011` | 1 | `0x7C` | 2 | 1 |
| 3 | Heure | `0x0012` | 1 | `0x1F` | 0 | 0 |
| 4 | Minute | `0x0012` | 2 | `0x07E0` | 5 | 0 |
| 197 | État de la grossesse d’Elli | `0x2168` | 1 | `0x18` | 3 | 0 |
| 198 | État de la grossesse de Karen | `0x2168` | 1 | `0x60` | 5 | 0 |
| 199 | État de la grossesse de Mary | `0x2168` | 2 | `0x0180` | 7 | 0 |
| 580 | Argument partagé entre scripts | `0x21CA` | 1 | `0x03` | 0 | 0 |

Dans la scène d’annonce de Karen (`0657`), `VarGet(198)` renvoie `1` alors que `VarGet(197)` et `VarGet(199)` renvoient `0`. Les trois ID partagent l’offset `0x2168`. Le masque de Mary couvre le dernier bit de cet octet et le premier bit du suivant. Le compteur de jours depuis l’annonce (`50`) vaut `0` dans les trois états. Le code lit aussi `0x2144` quand une branche trouve un état de grossesse égal à `2`. Ce chemin est visible dans le désassemblage. [Scène et état mGBA](../mgba/usa-a4ne.md#test-ciblé-de-karen) · [Lectures natives de la grossesse](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L15116-L15148) · [Branche du compteur](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L13841-L13888)

L’année (`0`) lit `0x0010` et renvoie `min(200, 7 * (octet >> 3) + (octet & 7))`. L’argument partagé (`580`) réserve deux bits aux valeurs de `0` à `3`. L’analyse des écritures remonte jusqu’aux résultats du menu de télévision qui alimentent cet argument. [Lecture du calendrier](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L13212-L13267) · [Branche de l’argument partagé](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L18777-L18791) · [Origine des écritures](ecritures-variables.md#origine-des-variables-locales)

## Format et méthode

- `Contextes-variables-FoMT.csv` donne l’édition, l’empreinte SHA-256 du fichier mGBA et les bases du moteur de scripts (`0x0200207C`) et de `GameStateSaveImage` (`0x020025D8`). Les trois contextes sont le réveil du 3 printemps en USA, la scène de Karen du 5 été en USA et le début jouable du 2 printemps en Europe. [Essais USA](../mgba/usa-a4ne.md) · [Essais Europe](../mgba/europe-a4np.md)
- `Lectures-variables-FoMT.csv` conserve la valeur renvoyée et les couples `offset/taille` séparés par `|`. Les offsets sont relatifs aux `0x34F4` octets de `GameStateSaveImage` en RAM. La colonne `lectures_hors_image` donne des adresses GBA absolues. Les deux lectures de pointeur à `ScriptEngine + 0x350` et `+ 0x354` sont omises. [Structure de l’image](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/game_state_types.hh#L185-L217) · [Structure du moteur](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/script_engine.hh#L18-L42)
- `Masques-variables-FoMT.csv` donne une ligne par ID. Un champ unique, lu avec la même largeur dans chaque état, est testé dans une copie privée de la mémoire. Le sondage des mots larges couvre zéro, tous les bits à un, chaque bit isolé et son complément, ainsi que 64 mots mixtes déterministes, avec dédoublonnage. `essais_par_contexte` compte les essais terminés avec la trace attendue, dans l’ordre du CSV des contextes. Les colonnes `masque`, `decalage` et `biais` sont renseignées quand les trois états donnent le même modèle.

Les traces couvrent les chemins parcourus durant ces essais. Les offsets décrivent la structure en RAM. L’analyse SRAM a vérifié la copie de cette structure dans les deux emplacements du fichier `.sav` pour les deux éditions. [Offsets dans le fichier `.sav`](../sauvegarde.md#retrouver-un-champ-dans-le-fichier)

## Reproduire le relevé

L’outil exécute directement le code Thumb des deux ROM dans Unicorn 2.1.4, avec la RAM issue des états mGBA. Il écrit les trois CSV dans un nouveau dossier.

```sh
python3 -m pip install unicorn==2.1.4
python3 outils/jeu/relever_variables.py \
  roms/A4NE.gba roms/A4NP.gba exports/lectures-variables \
  etats/after-sleep-steady.state etats/karen-announcement.state etats/Harvest-Moon-Europe.ss1
```
