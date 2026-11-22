# Événements de More Friends of Mineral Town USA

Les octets de l’indice identifient l’édition américaine `BFGE`. L’adresse GBA `0x080000A0` correspond à l’offset fichier `0xA0`. Elle contient le titre `HM MFOM USA` suivi d’un octet nul. Le code `BFGE` se trouve à `0x080000AC`, soit l’offset fichier `0xAC`. La ROM européenne de *Friends of Mineral Town* utilisée pour le catalogue précédent porte le code `A4NP`. [Format de l’en-tête GBA](https://mgba-emu.github.io/gbatek/#gba-cartridge-header) · [Détection des éditions dans Mary](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/src/rom_import.cc#L114-L143)

## De l’annonce aux premiers pas

Les identifiants du tableau sont décimaux. La colonne « Chute » désigne l’incident après lequel l’enfant commence à ramper. La case vide pour Kappa indique qu’aucun symbole descriptif ne permet d’attribuer cette scène. L’identifiant `0916` reste générique dans la source. [Kai à Gray](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/goodies/mfomt_scripts_text.mary.sym#L6082-L6465) · [Gourmet, Kappa et Won](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/goodies/mfomt_scripts_text.mary.sym#L8750-L8920)

| Conjoint | Annonce | Naissance | Chute | Premiers pas |
|---|---:|---:|---:|---:|
| Kai | 0663 | 0668 | 0693 | 0673 |
| Cliff | 0664 | 0669 | 0694 | 0676 |
| Doctor | 0665 | 0670 | 0695 | 0679 |
| Rick | 0666 | 0671 | 0696 | 0682 |
| Gray | 0667 | 0672 | 0697 | 0685 |
| Gourmet | 0901 | 0904 | 0915 | 0907 |
| Kappa | 0902 | 0905 |  | 0910 |
| Won | 0903 | 0906 | 0917 | 0912 |

- **Annonce.** Le guide situe la scène au réveil, environ une à deux saisons après le mariage. Le jour exact, les conditions d’affection et les éventuels reports restent à vérifier pour chaque conjoint. [Guide MFoMT](https://fogu.com/hm5/house/child.php)
- **Naissance.** Le compteur `VAR_DAYS_SINCE_PREGNANCY_EVENT` (variable 50) commence après l’annonce. Le seuil de naissance est de 60 jours. Le guide décrit la naissance d’une fille et le choix de son prénom. [Constantes de grossesse](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/goodies/mfomt_constants.mary.h#L6784-L6807) · [Guide MFoMT](https://fogu.com/hm5/house/child.php)
- **Enfant.** Le jeu compte l’âge par `VAR_CHILD_AGE_DAYS` (variable 46). La chute devient éligible à 60 jours d’âge et les premiers pas à 120 jours. Le guide décrit ces scènes au réveil. [Constantes d’âge](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/goodies/mfomt_constants.mary.h#L6809-L6828) · [Guide MFoMT](https://fogu.com/hm5/house/child.php)

Le script `0492` est l’examen à la clinique. Le catalogue y distingue plusieurs résultats liés à la grossesse. Le script `1051` porte le nom `ScheduleDailyEvents` et constitue un point de départ pour vérifier les conditions d’appel dans le code BFGE. [Examen](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/goodies/mfomt_scripts_text.mary.sym#L4484-L4501) · [Planificateur](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/goodies/mfomt_scripts_text.mary.sym#L10672-L10676)

Le dialogue habituel de l’enfant est `1064`. Les variantes de son anniversaire figurent dans `0618`, `0621`, `0624`, `0627`, `0630`, `0874`, `0877` et `0880`, dans l’ordre des conjoints du tableau. [Index des symboles](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/goodies/mfomt_scripts_text.mary.sym)

## Repères dans la ROM européenne fournie

Sur `A4NP`, le planificateur quotidien est `0983`. Il appelle les annonces de grossesse de Popuri (`0654`), Ann (`0655`), Elli (`0656`), Karen (`0657`), Mary (`0658`) et de la Déesse des récoltes (`0862`). Pour Popuri, le code exige notamment un mariage, la présence dans la maison de la ferme, 65 000 points d’affection et au moins 30 jours depuis le mariage. Ces conditions ont été vérifiées pour `A4NP`. [Planificateur européen](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/eu/EventScript_SystemEvent_ScheduleDailyEvents.mary.c#L149-L520)

## Lire les CSV

- `Evenements-BFGE.csv` recense les **1 415 emplacements** de scripts numérotés de `0001` à `1415`. Chaque ligne indique le symbole publié, le nombre de libellés de texte répertoriés et la case dans la table de pointeurs. Les symboles génériques tels que `EventScript_0916` signalent une fonction qui reste à identifier.
- `Grossesse-et-enfant-BFGE.csv` détaille **31 scènes principales**. Les variables d’état et les symboles des répliques d’annonce servent de repères. Les indices de réplique commencent à zéro et suivent l’ordre du catalogue de symboles.

La table de pointeurs BFGE commence à l’offset fichier `0x1014BC` (`0x081014BC` en mémoire GBA), avec une case zéro nulle. Chaque case occupe quatre octets. Pour `0663`, le calcul `0x1014BC + 4 × 663` donne l’offset `0x101F18`, soit `0x08101F18` en mémoire GBA. La valeur stockée dans cette case indique où commence le bloc du script. [Disposition BFGE dans Mary](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/src/rom_import.cc#L136-L143)

L’index repose sur les sources publiées et le guide de jeu. La ROM `BFGE` est nécessaire pour lire les pointeurs stockés, extraire les répliques et vérifier les appels exacts des événements. L’édition américaine répertoriée par No-Intro fait 16 777 216 octets et porte le SHA-1 `3AA4D46CBBF152E440942ACD5F5D37DDC7B05E1D`. [Référence No-Intro](https://github.com/libretro/libretro-database/blob/master/metadat/no-intro/Nintendo%20-%20Game%20Boy%20Advance.dat#L8357-L8360)
