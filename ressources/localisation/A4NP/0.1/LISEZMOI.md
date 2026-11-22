# Harvest Moon GBA en français

Le patch **0.1** est la première version de travail pour *Harvest Moon: Friends of Mineral Town (Europe)*, **A4NP**, révision 00. Le manifeste réunit 31 entrées qui couvrent les menus de pause, le journal, le sac, la saisie des noms, le récapitulatif du profil et le panneau de la caisse près de la ferme.

## Jouer dans mGBA

1. Extraire le fichier `.gba` de l’archive européenne. La ROM de référence fait 8 388 608 octets et son SHA-1 est `7ba1ec1e46ce424e3c6fd72e4e8d5e9eb5ede247`.
2. Dans mGBA Qt, ouvrir la ROM avec **File → Load ROM…**. Choisir ensuite **File → Load patch…** et charger `Harvest-Moon-A4NP-FR-0.1.bps`. mGBA charge le patch en mémoire. [Code de mGBA](https://github.com/mgba-emu/mgba/blob/0.10.5/src/platform/qt/Window.cpp#L462)
3. Vérifier **Ton nom** à la création de partie, puis **Journal**, **Sac** ou **Mémo** dans le menu de pause.

On peut aussi lancer le jeu et appliquer le patch en une commande.

```sh
mgba-qt -p Harvest-Moon-A4NP-FR-0.1.bps "/chemin/vers/Harvest Moon - Friends of Mineral Town (Europe).gba"
```

## Modifier les textes

Modifier les champs `fr` dans `textes.json`, puis reconstruire le patch avec Python 3.

```sh
python3 construire_patch.py "/chemin/vers/Harvest Moon - Friends of Mineral Town (Europe).gba" -o Harvest-Moon-A4NP-FR-essai.bps
```

Le générateur vérifie l’empreinte de la ROM, les octets de chaque entrée et les pointeurs de texte déplacés. Il déplace les textes plus longs lorsqu’un pointeur a été vérifié pour cette révision. Les suffixes binaires comme la flèche du panneau sont définis par `fin_hex`. Les libellés de la carte et du journal ont été raccourcis pour tenir dans leur zone d’affichage.

Le manifeste associe `é` à l’octet `C5` et installe un glyphe dessiné pour cet essai à `0x4FA07C`, dans un emplacement de kana demi-chasse. Les autres caractères accentués, les titres dessinés dans des tuiles et les scripts de dialogue demandent leurs propres relevés. Un prochain lot peut commencer par un événement court et vérifier les retours à la ligne, les noms insérés par le jeu et les choix de dialogue. [Travaux antérieurs sur la police et le texte](https://romhack.org/viewtopic.php?t=2680)

## Vérifications

Dans mGBA 0.10.5, les trois écrans de saisie et le récapitulatif du profil rendent les libellés français. **Journal → Sauver → Case 1** crée une sauvegarde. Après redémarrage, **Lire → Case 1** reprend la partie. L’interaction avec le panneau affiche **Caisse →** et conserve la flèche. [Récapitulatif](captures/05-profil.png) · [Mémo](captures/07-memo.png) · [Journal](captures/09-journal.png) · [Panneau](captures/11-panneau-caisse.png)
