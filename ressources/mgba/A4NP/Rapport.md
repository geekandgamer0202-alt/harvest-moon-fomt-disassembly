# Harvest Moon: Friends of Mineral Town sur mGBA

Les essais ont été réalisés sur mGBA **0.10.5** avec la ROM européenne fournie. L’archive ZIP a passé son contrôle d’intégrité. La ROM fait 8 388 608 octets, porte le code **A4NP**, révision 00, et son SHA-1 correspond à la référence européenne `7ba1ec1e46ce424e3c6fd72e4e8d5e9eb5ede247`. [mGBA](https://mgba.io/downloads.html) · [Référence OpenRetro](https://openretro.org/game/0efd872f-47c5-4020-b01f-31437a25741e/edit)

## Tests de jeu

| Essai | Résultat observé |
| --- | --- |
| Nouvelle partie | An 1, lundi 2 du printemps, 6 h, soleil et 500 G. Sac vide avec trois emplacements pour les objets et trois pour les outils. Le chien affiche deux cœurs. |
| Prendre et ranger | **A** face au tronc récupère un miel. **B** le range. Maintenir **L**, puis appuyer sur **A** le ressort. La prise et la reprise sont visibles au-dessus du personnage. |
| Donner | Après la première présentation de Rick, se placer face à lui avec le miel en main et appuyer sur **A**. Rick remercie le personnage. Une fois le dialogue fermé, le miel a quitté la main, le solde reste à 500 G et l’octet d’affinité mesuré passe de **50 à 59**. |
| Expédier | Face à la caisse, depuis la case juste au sud, **A** dépose le miel. Au passage de Zack vers 17 h, le solde passe de **500 à 550 G**. Lors d’un essai décentré, la main se vide et le solde reste à 500 G. |
| Travailler la terre | **B** avec la houe équipée retourne une case vide. **L+B** sélectionne l’arrosoir rangé. **B** face à la mare fait passer l’arrosoir vide à 30 cases. Arroser la case labourée l’assombrit et ramène la réserve à 29 cases. |
| Acheter | Au supermarché, ouvert au moment du test le lundi à 11 h 10, un sachet de graines de navet coûte **120 G**. Le solde passe de **500 à 380 G**. |
| Semer | Sélectionner le sachet avec **L+B**, puis utiliser **B** face à la case labourée. À midi, le sachet est consommé et les graines sont visibles sur la case préparée. |
| Sauvegarder et reprendre | **Start → Diary → Save → Data 1** crée un fichier `.sav` de 32 Kio. Après fermeture et relance de mGBA, **Continue → Data 1** restaure la partie à l’intérieur de la maison à 6 h. |

Avec les commandes clavier Qt par défaut, **X** correspond à la touche GBA **A**, **Z** à **B**, **A** à **L**, **S** à **R**, **Entrée** à **Start** et **Retour arrière** à **Select**. Les flèches déplacent le personnage. [Correspondances de mGBA](https://github.com/mgba-emu/mgba/blob/0.10.5/src/platform/qt/InputController.cpp#L65)

Les essais couvrent le premier jour jouable. Le test de culture s’arrête au semis.

## Inspection graphique

Ouvrir **Tools → Game state views** dans mGBA Qt. **Ctrl+P** fige la scène, **Ctrl+N** avance d’une image et **F12** prend une capture du rendu.

| Fenêtre | Données à lire |
| --- | --- |
| **View palette…** | Couleurs chargées dans les 256 entrées des arrière-plans (**BG**) et les 256 entrées des objets (**OBJ**). Sélectionner une case pour lire l’index, la valeur GBA et la couleur RGB. |
| **View tiles…** | Motifs de 8 × 8 pixels chargés en VRAM. Choisir BG ou OBJ, puis le format 16 ou 256 couleurs. En 16 couleurs, choisir la banque de palette pour restituer les bonnes couleurs. |
| **View sprites…** | Entrées OAM, coordonnées, taille, palette, index de tuile et attributs de chaque sprite. |
| **View map…** | Cartes de tuiles de BG0 à BG3, avec leur défilement, priorité et adresses de base. |
| **Frame inspector…** | Composition d’une image, avec possibilité d’isoler des couches. |
| **View memory…** et **View I/O registers…** | Contrôle des octets et des registres vidéo. La palette commence à `0x05000000`, la VRAM à `0x06000000` et l’OAM à `0x07000000`. |

L’outil **View palette…** exporte BG et OBJ séparément en `.pal` ou `.act`. Le format GBA **BGR555** réserve cinq bits à chaque composante RGB. Les entrées chargées peuvent contenir des doublons et des couleurs de scènes précédentes. Chaque relevé décrit l’état vidéo au moment de la capture. Pour comparer d’autres zones, entrer dans chacune puis relever de nouveau les palettes, les tuiles et les couches visibles. [Menu mGBA](https://github.com/mgba-emu/mgba/blob/0.10.5/src/platform/qt/Window.cpp#L1693) · [Visionneuse de palettes](https://github.com/mgba-emu/mgba/blob/0.10.5/src/platform/qt/PaletteView.cpp#L113) · [Domaines mémoire GBA](https://mgba.io/docs/scripting.html#gba-2)

## Deux scènes mesurées

| Scène | Couleurs BG distinctes | Couleurs OBJ distinctes | Rectangles OAM dans l’écran |
| --- | ---: | ---: | ---: |
| Intérieur de la ferme | 104 | 166 | 11 |
| Extérieur avec le miel en main | 187 | 194 | 12 |

Les deux scènes utilisent le mode vidéo 0, quatre arrière-plans de tuiles 8 × 8 à 4 bits par pixel et un écran de 240 × 160 pixels. Les couleurs distinctes sont comptées parmi les entrées chargées. Les rectangles de sprites sont comptés avant masquage ou superposition. [Format des états mGBA](https://github.com/mgba-emu/mgba/blob/0.10.5/include/mgba/internal/gba/serialize.h) · [Format vidéo GBA](https://problemkaputt.de/gbatek.htm#gbavideo)

- Dans la maison, l’entrée BG `0x002` vaut `0x2F1A`, soit **`#D6C65A`**. La couche BG3 montre le sol et les murs. Dans **Frame inspector**, masquer les sprites 0 à 3 retire l’horloge et les icônes de l’image en laissant la pièce et le personnage visibles. [Palette](captures/31-palettes.png) · [Fond BG3](captures/34-carte-bg3.png) · [Image avec l’interface](captures/35-image-avec-interface.png) · [Image avec l’interface masquée](captures/36-image-interface-masquee.png)
- À l’extérieur, le miel tenu en main correspond à l’entrée **OAM 4**, en **16 × 16 pixels**, à l’écran en **(111, 48)** dans l’image étudiée. Il utilise la banque OBJ 0 et sa première tuile commence à `0x06010300`. Cette entrée disparaît quand l’objet est rangé. [Miel en main](captures/03-miel-ramasse.png)

## Fichiers du dossier

- `captures/` contient les preuves visuelles des essais et des visionneuses.
- `palettes-gba.csv` contient les **1 024 entrées de palette** relevées sur les deux scènes, avec leur adresse, leurs valeurs BGR555 et leurs codes RGB.
- `analyse-graphique.json` détaille les couches, les références de tuiles et les objets OAM des deux scènes.
- `observations.json` donne les relevés d’horloge, d’or, d’inventaire et de l’octet d’affinité de Rick. Certains champs sont conservés en octets pour distinguer la mesure de l’interprétation. [Cartographie de référence A4NP](https://github.com/khumam/gba-duo-companions/blob/main/harvest-moon-fomt-companion/NOTES.md)
- `Partie-test-initiale.sav` est la sauvegarde de test vérifiée après redémarrage. Pour l’ouvrir dans mGBA, lui donner le même nom de base que la ROM dans un dossier de test.
