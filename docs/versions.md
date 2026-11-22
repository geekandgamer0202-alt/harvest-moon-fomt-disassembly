# Versions de la ROM et comparaison

| Code | Édition | Révision | Octets | CRC32 | SHA-1 | Provenance |
| --- | --- | ---: | ---: | --- | --- | --- |
| `A4NE` | Friends of Mineral Town, USA | 0 | 8 388 608 | `8E923168` | `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963` | ROM fournie, empreinte recalculée |
| `A4NP` | Friends of Mineral Town, Europe | 0 | 8 388 608 | `F50F82AD` | `7ba1ec1e46ce424e3c6fd72e4e8d5e9eb5ede247` | ROM fournie, empreinte recalculée |
| `BFGE` | More Friends of Mineral Town, USA | — | 16 777 216 | — | `3aa4d46cbbf152e440942acd5f5d37ddc7b05e1d` | En-tête communiqué, empreinte de référence No-Intro |

Les deux ROMs analysées portent `HARVESTMOGBA` à `0xA0`. Le titre occupe 12 octets, le code de jeu commence à `0xAC` et la révision se lit à `0xBC`. Pour convertir un offset fichier dans la zone ROM principale en adresse GBA, ajouter `0x08000000`. L’outil accepte le fichier `.gba` ou le ZIP local qui contient une seule ROM. `sha1_confirme` compare les octets du fichier avec l’empreinte de référence, ce qui permet de distinguer une version modifiée qui conserve le même code. [Structure de l’en-tête GBA](https://mgba-emu.github.io/gbatek/#gba-cartridge-header)

```sh
python3 outils/identifier_rom.py "roms/Harvest Moon - Friends of Mineral Town (USA).gba"
```

## A4NE et A4NP

| Repère | USA A4NE | Europe A4NP |
| --- | --- | --- |
| Table des pointeurs de scripts | `0x0F89D4` | `0x0F8A20` |
| Répartiteur natif du bytecode | `0x03F8DC` | `0x03F8F0` |
| Table des 327 appels natifs | `0x03F904` | `0x03F918` |
| Scripts avec `CODE` et `STR` | 1 091 | 1 091 |
| Scripts avec `CODE`, `JUMP` et `STR` | 237 | 237 |
| Chaînes d’événement | 8 368 | 8 368 |

La comparaison des 1 328 scripts confirme l’égalité octet à octet des blocs `CODE` et `JUMP`, ainsi que de 1 327 blocs `STR`. La seule chaîne d’événement différente est `1008.00`, dans la présentation de Karen. Les blocs américains commencent 88 octets plus tôt pour 1 008 scripts et 92 octets plus tôt pour 320 scripts. Utiliser l’index de chaque version pour les adresses des répliques. Le dossier contient les tailles, opcodes, décalages et repères d’appels relevés lors de la comparaison. [Rapport de comparaison](comparaison-a4ne-a4np.json) · [Tables reconnues par Mary](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/src/rom_import.cc#L114-L143)

```sh
python3 outils/evenements/indexer_scripts.py roms/harvest-moon-usa.gba \
  --comparer roms/harvest-moon-europe.gba
```

## L’indice communautaire BFGE

Les octets `48 4D 20 4D 46 4F 4D 20 55 53 41 00 42 46 47 45` se lisent `HM MFOM USA`, un octet nul, puis `BFGE`. Ils identifient *More Friends of Mineral Town* USA. L’adresse `0x080000A0` pointe sur le titre de cette cartouche. Pour l’annonce de grossesse, les identifiants des événements utiles sont dans le catalogue ci-dessous. Les colonnes `case_table_*` localisent les pointeurs, dont la valeur doit être lue sur une ROM BFGE avant de donner l’adresse d’un script. [Détection BFGE par Mary](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/src/rom_import.cc#L136-L143) · [Empreinte de référence](https://github.com/libretro/libretro-database/blob/master/metadat/no-intro/Nintendo%20-%20Game%20Boy%20Advance.dat)

- La table BFGE commence à `0x1014BC`, avec une case zéro nulle et 1 415 emplacements numérotés. L’emplacement de `0663` est `0x1014BC + 4 × 663 = 0x101F18`. [Index des emplacements](versions/Evenements-BFGE.csv)
- Les annonces `0663` à `0667` couvrent Kai, Cliff, Doctor, Rick et Gray. `0901` à `0903` couvrent Gourmet, Kappa et Won. Le planificateur est `1051` et l’examen à la clinique est `0492`. Le test de la grossesse de Karen dans la ROM A4NE a, lui, utilisé le script `0657`. [31 scènes et leurs repères](versions/Grossesse-et-enfant-BFGE.csv) · [Symboles BFGE](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/goodies/mfomt_scripts_text.mary.sym)
- Le guide BFGE situe l’annonce au réveil environ une à deux saisons après le mariage. La naissance est associée au compteur de grossesse qui atteint 60 jours. La chute du lit et les premiers pas correspondent aux seuils de 60 et 120 jours d’âge de l’enfant. Les conditions propres à chaque conjoint restent à contrôler dans le bytecode BFGE. [Constantes documentées](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/goodies/mfomt_constants.mary.h#L6784-L6828) · [Guide MFoMT](https://fogu.com/hm5/house/child.php)
