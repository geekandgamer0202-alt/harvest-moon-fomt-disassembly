# Harvest Moon · Friends of Mineral Town

Extraction graphique de la version USA `A4NE`, révision `0`. Le SHA-1 de la ROM fournie est `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963`. Ouvrir [Apercu.png](Apercu.png) pour voir quelques exports et une capture mGBA de l’annonce à la clinique.

| Dossier | Contenu | Index de départ |
| --- | --- | --- |
| `personnages/` | 184 portraits de dialogue et 3 009 images de sprites, dont des accessoires et des effets. Planches de consultation, tuiles indexées, palettes et séquences d’animation. | [Portraits](personnages/Portraits-A4NE.csv) · [Sprites](personnages/Sprites-A4NE.csv) · [Animations](personnages/Animations-A4NE.csv) |
| `cartes/` | 66 plans de base en 84 PNG, dont 18 variantes de nuit. 31 jeux de tuiles, chacun en aperçu coloré et en version indexée, et 47 nuanciers. | [Plans](cartes/Cartes.csv) · [Tuiles](cartes/Tuiles.csv) · [Palettes](cartes/Palettes.csv) |
| `objets/` | Correspondance de 347 objets à leurs icônes de 16 × 16 pixels. Les noms anglais et les ID d’origine servent de repères. Trois planches couvrent les outils, aliments et articles. | [Index des icônes](objets/Index-icones-objets-A4NE.csv) |
| `archives-obj/` | 52 archives OBJ supplémentaires couvrant notamment les icônes et effets. 939 groupes composés avec leurs couleurs, 8 groupes vides répertoriés et, selon l’archive, des nuanciers et des planches d’indices de tuiles. | [Archives](archives-obj/Archives-OBJ.csv) · [Groupes](archives-obj/Groupes-OBJ.csv) |
| `interface/` | 110 PNG pour le titre, l’ouverture, les menus, les polices, l’état de la ferme et divers fonds. Les deux polices 1bpp et l’archive décompressée du titre sont également disponibles. | [Index de l’interface](interface/Interface.csv) |
| `mgba/` | Quatre captures natives de mGBA 0.10.5 et leurs relevés de palettes, de couches BG et d’objets OAM. | [Scènes relevées](mgba/preuves.csv) · [Palette par scène](mgba/palettes.csv) |

## Retrouver un graphisme

- Pour une icône, filtrer `nom_rom` dans l’index des objets. `fichier_png` donne le PNG à l’intérieur du ZIP. Les colonnes `descripteur_rom`, `tuiles_rom` et `palette_rom` donnent les emplacements d’origine.
- Pour un portrait ou une animation, rechercher le nom symbolique ou l’ID dans `personnages/`. Dans l’index des animations, `descripteur` renvoie à l’ID de l’image dans `Sprites-A4NE.csv`. Les sélecteurs et durées proviennent de la ROM.
- Pour les éléments à localiser dans l’interface, commencer par `interface/ouverture/` pour le titre et ses libellés et par `interface/polices/` pour les planches de glyphes. Les CSV d’interface identifient les plages sources et leurs empreintes.

Les offsets se lisent en hexadécimal depuis le début du fichier ROM. Par exemple, le fichier `archives-obj/6678A0/archive.bin` commence à l’offset `0x6678A0`, soit l’adresse `0x086678A0` sur la GBA. Les chemins des index `archives-obj/` et de `objets/Index-icones-objets-A4NE.csv` partent de la racine du ZIP. Les index de personnages, des cartes, de l’interface et de mGBA utilisent des chemins relatifs à leur dossier.

## Rendu et vérification

Les PNG individuels gardent la taille native du graphisme. Les planches d’indices préservent les valeurs de tuiles, tandis que les compositions couleur utilisent les palettes BGR555 d’origine. `Apercu.png` et les planches de consultation agrandissent ou réduisent certaines images pour en faciliter la lecture.

Les cartes représentent le décor statique et ses palettes de jour et de nuit. En jeu, les personnages, la météo, les cultures, les bâtiments et les animations peuvent compléter ou modifier ce décor. Pour 24 images de sprites, certains modes du moteur peuvent modifier l’ordre de superposition des pièces. Les captures mGBA représentent quatre états précis. Deux d’entre eux ont été préparés pour atteindre la scène de Karen et celle de l’annonce à la clinique. [Méthode pour les cartes](cartes/Lisez-moi.md) · [Rendu des sprites](personnages/Lire-moi-personnages.md) · [Provenance des captures](mgba/LISEZ-MOI.md)

`Manifest-graphismes.csv` donne la taille et le SHA-256 des fichiers exportés, ainsi que les dimensions et le mode des PNG. Les archives OBJ sont des blocs graphiques repérés à leurs offsets. L’extraction s’appuie sur les formats et tables documentés par le projet de désassemblage FoMT de Wokann, vérifiés sur les octets A4NE fournis. [Documentation des ressources graphiques](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/graphics/README.md)
