# Diagnostic de la mémoire vidéo

## Dans mGBA Qt

Mettre le jeu sur la scène voulue, attendre la fin du fondu, puis suspendre l’émulation avec `Ctrl+P`. Faire avancer une image avec `Ctrl+N` si nécessaire. Dans **Tools → Game state views**, les vues suivantes lisent la mémoire de la scène courante. [Menus Qt 0.10.5](https://github.com/mgba-emu/mgba/blob/0.10.5/src/platform/qt/Window.cpp#L1693)

| Vue | Vérification |
| --- | --- |
| **View palette…** | Parcourir les 256 entrées BG et les 256 entrées OBJ. Sélectionner une case pour relever l’index, le mot GBA et sa couleur. L’export de mGBA permet de choisir BG ou OBJ. |
| **View tiles…** | Voir les motifs 8 × 8 chargés. Choisir BG ou OBJ, 16 ou 256 couleurs, puis la banque appropriée en 4 bpp. |
| **View sprites…** | Contrôler les entrées OAM, leur taille, leurs coordonnées et la tuile de départ. |
| **View map…** | Parcourir BG0 à BG3 et relever la priorité, le défilement et les adresses de motifs et de cartes. |
| **Frame inspector…** | Isoler les couches ou masquer des sprites pour vérifier leur rôle dans la composition. Dans la maison A4NP testée, BG3 porte le sol et les murs. Masquer les entrées OBJ 0 à 3 retire l’horloge et les icônes. |
| **View memory…** et **View I/O registers…** | Confirmer les registres et adresses dans la mémoire GBA. |

Les mots de palette ont cinq bits par canal. Le rouge occupe les bits 0 à 4, le vert 5 à 9 et le bleu 10 à 14. Dans la maison A4NP testée, l’entrée BG `0x002` vaut `0x2F1A`, soit `#D6C65A` après extension standard sur huit bits. À l’extérieur, le miel en main correspond à l’entrée OAM 4 en `(111, 48)` au moment du relevé, en 16 × 16. Il utilise la banque OBJ 0 et la première tuile commence à `0x06010300`. [Palette mGBA](https://github.com/mgba-emu/mgba/blob/0.10.5/src/platform/qt/PaletteView.cpp#L113) · [Format vidéo GBA](https://problemkaputt.de/gbatek.htm#gbavideo)

## Relever un état local

Enregistrer chaque scène à comparer, puis lancer `inspecter_etat.py` avec Python 3. La ROM locale est facultative. Elle sert à résoudre l’identifiant du bloc `CODE` à partir du pointeur lu dans l’état. Le script produit du JSON avec les compteurs de palettes, registres vidéo, couches BG en mode 0, entrées OAM et empreintes des zones mémoire.

```sh
python3 outils/mgba/inspecter_etat.py --rom roms/jeu-a4ne.gba \
  exports/mgba/sommeil-a4ne.state exports/mgba/reveil-a4ne.state
```

| Zone | Adresse GBA | Position dans l’état décompressé | Taille relevée |
| --- | --- | --- | ---: |
| Registres vidéo | `0x04000000` | `0x00400` | 88 octets |
| Palette BG | `0x05000000` | `0x00800` | 512 octets |
| Palette OBJ | `0x05000200` | `0x00A00` | 512 octets |
| OAM | `0x07000000` | `0x00C00` | 1 024 octets |
| VRAM BG | `0x06000000` | `0x01000` | 65 536 octets |
| VRAM OBJ | `0x06010000` | `0x11000` | 32 768 octets |

Le bloc PNG `gbAs`, compressé par zlib, contient l’état de l’émulateur. Le script vérifie le code et le CRC32 de la ROM mémorisés dans l’état. Les adresses de VRAM et de PRAM décrivent les données chargées lorsqu’une scène joue. Les offsets des tables, cartes et archives contenus dans la ROM doivent être établis séparément depuis le fichier cartouche. [Structure de l’état GBA dans mGBA 0.10.5](https://github.com/mgba-emu/mgba/blob/0.10.5/include/mgba/internal/gba/serialize.h#L410-L418)

## Résultats de référence

Les deux scènes européennes sont obtenues par les [actions ordinaires](europe-a4np.md#premier-jour-à-la-ferme). Pour les deux dernières scènes américaines, suivre le [test préparé](usa-a4ne.md#test-ciblé-de-karen), jouer la scène et reprendre un état à chacune des étapes. Le CSV joint au dépôt conserve les SHA-256 des états effectivement mesurés. Les nouveaux états peuvent différer selon le nom du joueur et l’instant de capture.

| Version | Scène | Origine | Couleurs BG | Couleurs OBJ | Objets OAM dans le cadre |
| --- | --- | --- | ---: | ---: | ---: |
| A4NP | Intérieur de la ferme | Partie normale | 104 | 166 | 11 |
| A4NP | Extérieur, miel en main | Partie normale | 187 | 194 | 12 |
| A4NE | Ferme, choix de dormir | Partie normale | 104 | 166 | 29 |
| A4NE | Ferme, réveil le lendemain | Partie normale | 104 | 166 | 11 |
| A4NE | Ferme, dialogue de Karen | Copie d’état préparée en RAM | 149 | 182 | 46 |
| A4NE | Clinique, annonce du médecin | Copie d’état préparée en RAM | 154 | 178 | 48 |

Les six relevés utilisent le mode 0, quatre couches de tuiles BG à 4 bpp et un écran de 240 × 160 pixels. BG0 à BG3 ont leurs cartes respectivement à `0x0600F800`, `0x0600F000`, `0x0600E800` et `0x0600E000` dans les quatre relevés A4NE. BG0 référence neuf indices de tuiles distincts dans la fenêtre autorisée à chacun de ces points. La zone autorisée pour cette couche passe de 2 688 pixels au réveil à 13 440 pixels au choix de dormir et à 16 128 pixels dans les deux dialogues du test de Karen.

Les couleurs distinctes sont comptées sur la totalité des 256 entrées chargées par palette. Les entrées peuvent être inutilisées ou rester d’une scène précédente. Le comptage des cellules de BG tient compte du défilement et de WIN0/WIN1. Il se fait avant transparence, priorité et mélange des couches. Le comptage OAM utilise l’intersection géométrique du rectangle avec l’écran avant masquage. Les fenêtres OBJ et autres modes vidéo sortent du calcul de couverture de cet outil. [Relevés et SHA-256](preuves-video.csv)
