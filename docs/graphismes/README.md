# Ressources graphiques de l’édition USA A4NE

Les relevés portent sur la révision 0, code `A4NE`, SHA-1 `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963`. Les offsets comptent à partir du début du fichier ROM. Pour obtenir l’adresse GBA, ajouter `0x08000000`.

Les colonnes `export_local*` désignent les chemins d’origine sous `exports/graphismes-a4ne/`. Les fichiers ont la même arborescence dans le dépôt sous `ressources/graphismes/A4NE/`. [Fichiers graphiques](../../ressources/graphismes/A4NE/) · [Aperçu PNG](../../ressources/graphismes/A4NE/Apercu.png)

| Famille | Repère natif | Index |
| --- | --- | --- |
| Plans du monde | `gMapData` à `0x105EDC`, 66 entrées de `0x28` octets | [Plans](cartes/Cartes.csv) · [Flux](cartes/Flux.csv) · [Tuiles](cartes/Tuiles.csv) · [Palettes](cartes/Palettes.csv) |
| Portraits de dialogue | `gPortraitIndexedResourceArchive` à `0x52D984`, longueur `0x5E0A4` | [Portraits](personnages/Portraits-A4NE.csv) · [Palettes OBJ](personnages/Palettes-personnages-A4NE.csv) |
| Sprites du monde | `gActorIndexedResourceArchive` à `0x58BA28`, longueur `0xDB638` | [Images](personnages/Sprites-A4NE.csv) · [Séquences d’animation](personnages/Animations-A4NE.csv) |
| Allocation des palettes OBJ | `GameSceneWorld::vfunc_48` à `0x01B5C0` USA et `0x01B5D4` Europe | [Règles par carte et essai du mariage](allocation-palettes-obj.md) |
| Banques OBJ et DMA | `AcquirePaletteBank` à `0x0AC96C` USA et `0x0AC99C` Europe | [Cycle des 13 cases et copies vers la mémoire de palette](banques-obj.md) |
| Archives OBJ supplémentaires | 52 archives identifiées par leur adresse et leur taille | [Archives](archives-obj/Archives-OBJ.csv) · [Groupes](archives-obj/Groupes-OBJ.csv) |
| Icônes d’inventaire | Archive commune à `0x6678A0`, fin exclue `0x67A0E8` | [Icônes nommées](objets/Index-icones-objets-A4NE.csv) · [Résolution des entrées](objets/Index-archive-commune-A4NE.csv) · [Vérifications](objets/Verification-icones-objets-A4NE.json) |
| Titre, menus, polices et fonds | 113 références, avec plages sources et empreintes | [Index de l’interface](interface/Interface.csv) |

## Plans, tuiles et palettes BG

Les 66 plans se répartissent en 18 plans à palettes de jour et de nuit distinctes et 48 plans à palette commune, soit 84 compositions de référence. Une entrée `gMapData` contient les pointeurs vers les tuiles, les deux palettes, les trois calques et le terrain, puis les dimensions du plan. Les dimensions de l’image résultent de tuiles de 8 × 8 pixels. L’ordre de composition va de BG3 à BG1 et l’indice 0 des tuiles est transparent. [Définition de `MapData`](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/map_data.hh) · [Chargement dans le moteur](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/world_map.cc#L1012)

Les plans référencent 272 flux distincts, dont 31 jeux de tuiles de 1 024 emplacements et 47 palettes. Chaque flux de palette couvre les banques BG 1 à 15. Les plans d’hiver 11 et 15 contiennent respectivement sept et deux cellules non vides de banque 0, couvertes entièrement par des calques supérieurs dans les compositions. Un aperçu coloré de jeu de tuiles choisit une banque d’après les occurrences dans un plan de référence. En jeu, chaque cellule choisit sa propre banque. [Documentation des cartes](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/graphics/maps/README.md)

Les plans mettent en évidence le décor statique et les modèles de mine. Les ressources chargées en jeu peuvent y ajouter des cultures, des bâtiments, des animations, de la météo et les acteurs. La sélection d’un plan dépend notamment de la saison et des agrandissements de la ferme. [Sélection des plans](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/map_selection.c)

## Portraits, sprites et animations

Les deux archives suivent les sept tables d’`IndexedResourceArchive`. Dans l’ordre, elles contiennent des sélecteurs de 4 octets, des descripteurs de groupe de 16 octets, des entrées OAM de 8 octets, des unités de tuile de 32 octets, des banques de 16 couleurs BGR555 de 32 octets, des descripteurs auxiliaires de 8 octets et des entrées de 4 octets. Chaque table possède un en-tête de 4 octets. Le descripteur de groupe fixe les positions initiales et les tailles dans les tables OAM, tuiles, palettes et auxiliaires. [Lecteur natif](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/resource_archive.cc#L5)

| Table | Portraits | Sprites |
| --- | ---: | ---: |
| Sélecteurs | 184 à `0x52D988` | 2 551 à `0x58BA2C` |
| Descripteurs | 184 à `0x52DC6C` | 3 009 à `0x58E20C` |
| Entrées OAM | 1 037 à `0x52E7F0` | 4 795 à `0x599E20` |
| Tuiles 4bpp | 11 586 à `0x53085C` | 24 398 à `0x5A33FC` |
| Banques de couleurs | 52 à `0x58B0A0` | 162 à `0x661DC0` |
| Entrées finales | 184 à `0x58B728` | 3 990 à `0x663208` |

Les portraits possèdent en plus une banque de 32 octets après les tables. La conversion préserve les indices de palette, y compris les couleurs BGR555 identiques à des indices différents. Pour les 703 sprites à plusieurs banques, la palette de chaque pièce est celle indiquée par son entrée OAM, relative à la première banque du groupe. L’indice 0 est transparent. [Chargement des portraits](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/ui_portrait.cc#L4) · [Utilisation de la banque OAM](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_sprite.cc#L150)

Les séquences utilisent 2 963 des 3 009 images et peuvent partager des entrées physiques. L’index compte donc 5 980 positions de séquence pour 3 990 entrées finales physiques. Il couvre 281 sélecteurs munis d’un nom symbolique. Pour les groupes directionnels, l’acteur ajoute `0`, `1`, `2` ou `3` au sélecteur de base selon qu’il regarde vers le bas, le haut, la gauche ou la droite. [Symboles et directions](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/fomt_constants.mary.h#L44)

La composition de référence applique les retournements OAM et la priorité du mode habituel, dans lequel la première pièce reste au-dessus en cas de recouvrement. Les modes à priorité scindée peuvent modifier le recouvrement de 24 images. Les 46 descripteurs hors des séquences référencées restent documentés avec leur provenance. [Priorités des acteurs](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/entity_actor.cc#L587) · [Archives graphiques](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/graphics/README.md#L109)

## Archives OBJ et icônes d’inventaire

Les 52 archives OBJ supplémentaires donnent 947 groupes, dont 939 groupes 4bpp à une banque de couleurs et huit groupes vides. Les SHA-256 de 46 archives concordent avec les empreintes publiées par Wokann. Pour les six autres, l’index conserve la localisation, la structure et l’empreinte mesurées sur la ROM A4NE. [Inventaire des archives indexées](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/graphics/INDEXED_RESOURCE_ARCHIVE_INVENTORY.md)

Les tables d’inventaire `gToolInfo` à `0x0EAB0C`, `gFoodInfo` à `0x0EDCD8` et `gArticleInfo` à `0x0EFED4` indiquent les ID d’icône respectifs de 81 outils, 171 aliments et 95 articles. Dans l’archive commune, un ID d’icône résout un sélecteur, une entrée et un groupe OAM. Les 347 icônes cataloguées sont des images 16 × 16 en 4bpp composées de quatre tuiles et d’une banque de 16 couleurs. Le deuxième index décrit les 578 liaisons entre sélecteurs et entrées de cette archive, y compris les autres usages. [Tables des objets](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/item.cc) · [Lecteur d’icônes](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_gift_wrapping.cc) · [Archive commune](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/graphics/common_resource_archive/README.md)

## Titre, menus et polices

| Ressource | Offset ROM et encodage |
| --- | --- |
| Archive du titre | `0x747A74`, `0x2764` octets compressés en Huffman-8/LZ2 FoMT. La palette commence à `+0x4964` dans le flux décompressé. L’index identifie huit groupes OAM exportés en référence. |
| Menu principal | Huit icônes 4bpp à partir de l’archive `0x71E7A8`. Premier groupe de tuiles à `0x71E860`, palette à `0x71EC64`. |
| Police 8 × 12 | `0x4F90CC`, `0x16D4` octets, 487 glyphes 1bpp. |
| Police 16 × 12 | `0x4FA9A0`, `0x288F0` octets, 6 922 glyphes 1bpp. |
| Police de l’horloge | `0x75A440`, `0x1000` octets, 128 glyphes 4bpp de 8 × 8. |

Les glyphes 1bpp ont douze lignes actives dans une cellule de seize, avec les bits de poids fort à gauche. L’index relève également les calques du démarrage, les tableaux de l’histoire, l’état de la ferme et les fonds de scènes. Les colonnes `plages_rom` et `sha256_plages_rom` conservent l’ordre des intervalles et l’empreinte de chacun. Les variantes de menu et de décor assemblées à l’exécution peuvent mobiliser plusieurs ressources. [Ressources graphiques de référence](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/graphics/README.md)

## Vérifier les index sur une copie locale

```sh
python3 outils/graphismes/verifier_index_a4ne.py roms/harvest-moon-usa.gba
```

La vérification utilise Python 3.10 ou ultérieur. Elle contrôle la révision de la ROM, les pointeurs de plans, les limites des archives, les descripteurs, les palettes OBJ, les séquences, les chaînes d’ID d’icônes et les empreintes des plages de l’interface. Le contrôle des flux de carte porte sur leurs pointeurs et leurs intervalles. Les empreintes des données décompressées proviennent de l’analyse initiale avec le codec Popuri. [Décodeur Popuri consulté](https://github.com/Wokann/fomt/blob/31411d1d5450adf37565ad9ef7b87dd823d7fe91/tools/scripts/decompress.py)
