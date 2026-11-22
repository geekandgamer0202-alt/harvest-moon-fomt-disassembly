# Objets et économie A4NE

L’export lit les tables économiques de *Friends of Mineral Town* USA, révision 0. Chaque ligne donne un offset dans le fichier ROM. Les objets se retrouvent par le couple **famille et ID**. La table d’expédition utilise ses propres identifiants et désigne l’objet correspondant. [Édition de référence](versions.md) · [Fichiers CSV](../ressources/donnees/economie/A4NE/)

| Table native | Offset A4NE | Entrées | Export |
| --- | --- | ---: | --- |
| `gToolInfo` | `0x0EAB0C` | 81 × 12 octets | [Objets](../ressources/donnees/economie/A4NE/Objets-A4NE.csv) |
| `gFoodInfo` | `0x0EDCD8` | 171 × 16 octets | [Objets](../ressources/donnees/economie/A4NE/Objets-A4NE.csv) · [Effets des aliments](../ressources/donnees/economie/A4NE/Aliments-A4NE.csv) |
| `gArticleInfo` | `0x0EFED4` | 95 × 12 octets | [Objets](../ressources/donnees/economie/A4NE/Objets-A4NE.csv) |
| `gProductInfo` | `0x0F0348` | 103 × 4 octets | [Prix d’expédition](../ressources/donnees/economie/A4NE/Expedition-A4NE.csv) |

## Objets et effets des aliments

Les 347 noms, pointeurs et identifiants d’icône ont été relus dans la ROM. La colonne `fiche_hex` conserve les octets de chaque fiche. Les pointeurs de nom et de description occupent le premier et le dernier mot de la fiche. L’identifiant d’icône est un entier de 16 bits à `+0x04` pour les outils et articles, à `+0x08` pour les aliments. Deux entrées peuvent partager un nom, comme `Fried Noodles` (`0x86` et `0x89` dans la famille `aliment`). [Structures natives](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/item.hh#L8-L48) · [Index des icônes](graphismes/objets/Index-icones-objets-A4NE.csv)

Pour chaque aliment, la fiche porte à `+0x04` le bit de boisson qui sélectionne l’animation. Il est actif pour 25 aliments. Les octets signés `+0x05` et `+0x06` donnent les variations de base d’endurance et de fatigue. Une fatigue négative la réduit. Par exemple, `Honey` vaut `+2 / −2`, `Poisonous Mushroom` vaut `−50 / +10` et `Elli Leaves` vaut `+100 / −50`. Les bonus propres aux aliments préparés s’ajoutent aux valeurs de la table. Le moteur applique ensuite les modificateurs et les bornes du personnage. [Lecture et bonus des aliments](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/item.cc#L162-L243) · [Application à l’endurance et à la fatigue](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/farmer.cc#L235-L298)

## Expédition

Le prix de base en G occupe les bits 0 à 14 du mot. Le bit 15 distingue un aliment (`0`) d’un article (`1`). Les bits 16 à 23 donnent l’ID de l’objet. Les bits 24 à 31 sont à zéro dans les 103 fiches observées. Le catalogue contient 64 aliments et 39 articles. On retrouve le navet à **60 G**, le miel à **50 G**, `Junk Ore` à **1 G** et `Mythic Stone` à **20 000 G**. [Calcul du prix et résolution du produit](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/item.cc#L444-L515)

La caisse accumule le revenu. L’arrivée de Zack au point de collecte règle le montant en attente et le jeu peut appliquer un bonus. Dans un essai historique A4NP, un miel correctement déposé a fait passer le solde de 500 à 550 G au passage de Zack. Les 103 mots d’expédition A4NP à `0x0F0394` concordent octet par octet avec A4NE. Les champs numériques des 347 fiches d’objet concordent également. Les pointeurs de texte suivent les offsets de chaque édition. [Calcul du revenu de la caisse](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/shipping_bin.cc#L150-L199) · [Règlement dans le moteur](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/game_state.cc#L1283-L1295) · [Essai A4NP](mgba/europe-a4np.md#premier-jour-à-la-ferme)

## Boutiques

Le relevé des **12 catalogues** donne 113 lignes stockées, dont une sentinelle de l’épicerie. Il conserve les prix, les codes propres à chaque vendeur et les conditions retrouvées dans le code. Certaines offres correspondent à un service, un animal, une amélioration ou une action de menu. Le jeu peut appliquer des conditions de stock et des frais à l’achat. Le sachet de graines de navet à **120 G** au supermarché correspond à l’achat observé dans l’essai A4NP. [Catalogues A4NE](../ressources/donnees/economie/A4NE/Catalogues-boutiques-A4NE.csv) · [Formats et conditions](economie-boutiques.md) · [Essai A4NP](mgba/europe-a4np.md#premier-jour-à-la-ferme)

## Reproduire l’export

L’outil vérifie le code et le SHA-1 de la ROM d’origine. Il produit les CSV avec leurs offsets dans un nouveau dossier.

```sh
python3 outils/economie/exporter_economie.py roms/A4NE.gba exports/economie-a4ne
```
