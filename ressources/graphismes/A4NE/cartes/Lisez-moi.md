# Cartes, tuiles et palettes A4NE

Les 66 plans de la table du monde ont été décodés depuis la ROM américaine `A4NE` fournie, SHA-1 `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963`. La table `gMapData` commence à l’offset ROM `0x105EDC`, à l’adresse GBA `0x08105EDC`. Chaque entrée mesure `0x28` octets. Un offset ROM compte à partir du début du fichier. Les adresses GBA de cette extraction valent `0x08000000` plus l’offset ROM.

- `Cartes.csv` référence 84 PNG dans `plans/`. Les 18 extérieurs disposent chacun d’une palette de jour et d’une palette de nuit distinctes. Les 48 autres plans utilisent une seule palette pour les deux périodes. Les plans sont rendus à la résolution native, par tuiles de 8 × 8 pixels. Les identifiants sont ceux des entrées de `gMapData`.
- `Tuiles.csv` référence 31 jeux de tuiles, chacun couvrant les 1 024 emplacements graphiques du flux. `tuiles_indices/` conserve les indices 4 bits exacts. `tuiles/` affiche une version en couleur avec la palette de jour indiquée dans le CSV, la banque la plus fréquente pour chaque tuile et des niveaux de gris pour les tuiles sans occurrence dans cette palette. Dans le jeu, chaque cellule du plan sélectionne sa propre banque.
- `Palettes.csv` référence 47 flux de palettes. Chaque PNG affiche les banques BG 1 à 15 de haut en bas, et leurs 16 entrées de gauche à droite. Une case mesure 16 × 16 pixels. La première couleur de chaque banque est présentée dans le nuancier. Le rendu des cartes traite l’index de couleur 0 comme transparent.
- `Flux.csv` inventorie les 272 flux distincts référencés par la table, leur taille décompressée, leur format de compression, la borne exclusive lue par le décodeur et le SHA-256 du contenu décompressé. Une colonne de calque vide indique un pointeur nul.

Le moteur affiche les calques dans l’ordre BG3, BG2, BG1, du fond au premier plan. Le flux de carte fournit les banques BG 1 à 15. Les plans d’hiver 11 et 15 référencent respectivement sept et deux cellules non vides de banque 0. Le calcul de composition confirme qu’un calque supérieur couvre tous leurs pixels. Les zones vides du plan sont transparentes. Les images montrent les décors statiques, sans simulation des personnages, des animations, des modifications de terrain ou des variations d’éclairage calculées image par image. Les plans de mine représentent les modèles qui précèdent la génération des étages.

## Reproduire l’extraction

`extraction_cartes.py` utilise Python, NumPy, Pillow et le décodeur Popuri du projet Wokann. Depuis le dossier qui contient le script, en ajustant le chemin de la ROM et le dossier de destination souhaité :

```sh
curl -fsSLo decompress.py https://raw.githubusercontent.com/Wokann/fomt/31411d1d5450adf37565ad9ef7b87dd823d7fe91/tools/scripts/decompress.py
python extraction_cartes.py /chemin/vers/harvest-moon-usa.gba ./extraction
```

Le projet Wokann documente [les ressources de cartes](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/graphics/maps/README.md), [la structure des entrées](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/map_data.hh), [la sélection des plans](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/map_selection.c) et [le rendu des calques et palettes](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/world_map.cc).
