# Harvest Moon GBA en français

Le patch **0.2** s’applique à *Harvest Moon: Friends of Mineral Town (Europe)*, **A4NP**, révision 00. Les champs **Ton nom**, **Ta ferme** et **Ton chien** commencent désormais à 112 pixels du bord gauche. Le bouton **Fini** valide la saisie. Le manifeste couvre aussi les menus de pause, le journal, le sac, le récapitulatif du profil et le panneau de la caisse près de la ferme. [Écran de saisie](captures/01-ton-nom.png) · [Bouton Fini](captures/13-fini.png)

## Jouer dans mGBA

1. Extraire le fichier `.gba` de l’archive européenne. La ROM de référence fait 8 388 608 octets et son SHA-1 est `7ba1ec1e46ce424e3c6fd72e4e8d5e9eb5ede247`.
2. Dans mGBA Qt, ouvrir la ROM avec **File → Load ROM…**. Choisir ensuite **File → Load patch…** et charger `Harvest-Moon-A4NP-FR-0.2.bps`. mGBA charge le patch en mémoire. [Code de mGBA](https://github.com/mgba-emu/mgba/blob/0.10.5/src/platform/qt/Window.cpp#L462)
3. Vérifier **Ton nom** à la création de partie, puis **Journal**, **Sac** ou **Mémo** dans le menu de pause.

On peut aussi lancer le jeu et appliquer le patch en une commande.

```sh
mgba-qt -p Harvest-Moon-A4NP-FR-0.2.bps "/chemin/vers/Harvest Moon - Friends of Mineral Town (Europe).gba"
```

## Modifier les textes

Modifier les champs `fr` dans `textes.json`, puis reconstruire le patch avec Python 3.

```sh
python3 construire_patch.py "/chemin/vers/Harvest Moon - Friends of Mineral Town (Europe).gba" -o Harvest-Moon-A4NP-FR-essai.bps
```

Le générateur vérifie l’empreinte de la ROM, les octets de chaque entrée et les pointeurs de texte déplacés. Il déplace les textes plus longs lorsqu’un pointeur a été vérifié pour cette révision. Les suffixes binaires comme la flèche du panneau sont définis par `fin_hex`. Les libellés de la carte et du journal ont été raccourcis pour tenir dans leur zone d’affichage.

Le manifeste associe `é` à l’octet `C5` et installe un glyphe dessiné pour cet essai à `0x4FA07C`, dans un emplacement de kana demi-chasse. Les autres caractères accentués, les titres dessinés dans des tuiles et les scripts de dialogue demandent leurs propres relevés. Un prochain lot peut commencer par un événement court et vérifier les retours à la ligne, les noms insérés par le jeu et les choix de dialogue. [Travaux antérieurs sur la police et le texte](https://romhack.org/viewtopic.php?t=2680)

## Index des textes d’événement

L’indexeur lit directement la table A4NP à `0x0F8A20`, puis la section `STR` des **1 328 scripts**. Le CSV contient **8 368 chaînes** avec leur identifiant, leur adresse, leur longueur en octets et une colonne `fr` à compléter. Il couvre les textes d’événement. Les libellés de menus sont gérés dans `textes.json`. [Format des scripts](https://github.com/StanHash/FOMT-DOC/blob/master/EventScripts.txt)

```sh
python3 indexer_textes.py "/chemin/vers/le-jeu.gba" -o index_textes.csv
python3 indexer_textes.py "/chemin/vers/le-jeu.gba" --entree 0162.00
```

`0162.00` est le panneau de la caisse et `0737.00` correspond au premier dialogue de sortie de la maison. L’aperçu affiche les codes de contrôle sous forme échappée. La colonne `fr` sert à préparer les traductions. La réinsertion des chaînes d’événement de longueur variable reste à intégrer au générateur BPS.

## Vérifications

Dans mGBA 0.10.5, les trois écrans de saisie de la v0.2 affichent le curseur et les caractères au même emplacement. Le test à douze caractères se termine sur **Fini** et les noms apparaissent dans le récapitulatif. [Saisie complète](captures/13-fini.png) · [Récapitulatif](captures/05-profil.png)

Les essais de la v0.1 ont vérifié **Journal → Sauver → Case 1**, la reprise avec **Lire → Case 1** après redémarrage et l’affichage du panneau **Caisse →**. [Mémo](captures/07-memo.png) · [Journal](captures/09-journal.png) · [Panneau](captures/11-panneau-caisse.png)
