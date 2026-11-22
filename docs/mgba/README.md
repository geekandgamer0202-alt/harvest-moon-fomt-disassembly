# Vérifier le jeu dans mGBA

Les essais documentés ici ont été menés avec **mGBA Qt 0.10.5**. L’édition américaine A4NE est la référence du dépôt. Les essais européens A4NP datent de l’analyse du premier jour et du prototype français.

- [Préparation et commandes mGBA](#préparation)
- [USA A4NE · démarrage, sommeil et événement de Karen](usa-a4ne.md)
- [Europe A4NP · jeu, interface française et interactions](europe-a4np.md)
- [Palettes, tuiles et couches · méthode et six scènes mesurées](graphismes.md)

## Préparation

Installer l’édition Qt de mGBA 0.10.5 depuis la version officielle. Sous Linux x86-64, l’AppImage se lance après `chmod +x`. Si FUSE est indisponible, `--appimage-extract` fournit `squashfs-root/AppRun`. Pour un affichage X11 isolé, `xvfb-run` attribue un affichage temporaire. L’entrée clavier et l’enregistrement puis le rechargement d’un état ont été vérifiés dans l’AppImage avec Xvfb. [Version 0.10.5](https://github.com/mgba-emu/mgba/releases/tag/0.10.5)

```sh
chmod +x ./mGBA-0.10.5-appimage-x64.appimage
./mGBA-0.10.5-appimage-x64.appimage --appimage-extract
./squashfs-root/AppRun --version
xvfb-run -a -s '-screen 0 1024x768x24' \
  ./squashfs-root/AppRun "/chemin/vers/copie-locale.gba"
```

Pour jouer dans la fenêtre du bureau, lancer l’AppImage, `AppRun` ou `mgba-qt` sans Xvfb. Vérifier la taille et le SHA-1 avant chaque série. Le code de jeu est à l’offset fichier `0xAC` et la révision à `0xBC`. Les adresses équivalentes sur GBA sont `0x080000AC` et `0x080000BC`. Les deux ROM mesurent 8 388 608 octets.

| Édition | Code | Révision | SHA-1 | CRC32 |
| --- | --- | ---: | --- | --- |
| USA | `A4NE` | `0` | `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963` | `8E923168` |
| Europe | `A4NP` | `0` | `7ba1ec1e46ce424e3c6fd72e4e8d5e9eb5ede247` | `F50F82AD` |

```sh
sha1sum roms/jeu-local.gba
od -An -c -j 172 -N 4 roms/jeu-local.gba
od -An -tu1 -j 188 -N 1 roms/jeu-local.gba
mgba-qt roms/jeu-local.gba
```

Garder chaque édition et chaque essai dans un dossier de travail distinct afin que les fichiers `.sav` et les états associés à la ROM portent le bon nom. Une nouvelle partie sans sauvegarde existante fournit la référence pour les essais d’introduction.

## Commandes et états

| Action | Clavier Qt par défaut |
| --- | --- |
| Croix directionnelle | Flèches |
| A et B GBA | `X` et `Z` |
| L et R GBA | `A` et `S` |
| Start et Select | `Entrée` et `Retour arrière` |
| Pause et avance d’une image | `Ctrl+P` et `Ctrl+N` |
| Capturer l’écran | `F12` |
| Enregistrer l’état au premier emplacement | `Maj+F1` |
| Recharger le premier état | `F1` |

`Maj+F9` crée par exemple l’état `.ss9`, que l’on peut copier sous un nom de relevé. Les menus de fichier permettent aussi de choisir le chemin de l’état. Pour lancer directement un état créé avec la même ROM, utiliser `mgba-qt -t exports/mgba/etat.state roms/jeu-local.gba`. Pour vérifier la sauvegarde intégrée au jeu, enregistrer via le journal et redémarrer sans `-t` avant de charger la partie depuis son propre menu. Un état instantané contient aussi le processeur et la mémoire vidéo en cours d’exécution. [Touches GBA par défaut](https://github.com/mgba-emu/mgba/blob/0.10.5/src/platform/qt/InputController.cpp#L65) · [Format des états](https://github.com/mgba-emu/mgba/blob/0.10.5/include/mgba/internal/gba/serialize.h)

Les rapports et captures des premiers essais sont consultables dans les ressources. Les ROM, sauvegardes et états restent dans l’environnement de test. [Captures Europe](../../ressources/mgba/A4NP/captures/) · [Captures et relevés USA](../../ressources/graphismes/A4NE/mgba/)
