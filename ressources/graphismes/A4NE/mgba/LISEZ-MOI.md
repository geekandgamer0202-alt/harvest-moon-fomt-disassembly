# Relevés graphiques mGBA · A4NE Rev 0

Les quatre relevés proviennent d’états créés par mGBA 0.10.5 pour la version américaine `A4NE` révision 0, dont le CRC32 est `8E923168`. Chaque relevé décrit la mémoire graphique de l’émulateur au moment de la capture. Les adresses dans les CSV sont des adresses GBA. Les colonnes `offset_gbAs` désignent des positions dans l’état mGBA décompressé. [Structure de l’état mGBA 0.10.5](https://github.com/mgba-emu/mgba/blob/0.10.5/include/mgba/internal/gba/serialize.h#L410-L418)

| Scène | Origine | Couleurs BG distinctes | Couleurs OBJ distinctes |
| --- | --- | ---: | ---: |
| Ferme au réveil | Partie normale après validation de « Go to sleep? » | 104 | 166 |
| Ferme, confirmation du sommeil | Partie normale avant validation | 104 | 166 |
| Ferme, dialogue avec Karen | Vérification de l’événement avec une copie d’état ajustée en RAM | 149 | 182 |
| Clinique, annonce du médecin | Suite de ce même test après validation du sommeil | 154 | 178 |

Le test de Karen part d’un état de la ROM USA. La date et les conditions familiales ont été préparées dans une copie de son état. Le jeu a choisi et joué lui-même l’événement après confirmation du sommeil. La ROM est restée intacte.

- `preuves.csv` identifie les quatre états source par leur SHA-256 et recense les registres d’affichage, les captures et leurs planches de lecture.
- `palettes.csv` donne les 2 048 mots de PRAM en BGR555 et leur équivalent RVB. Pour chaque scène, les deux fichiers `*-palette-*.bin` contiennent chacun 256 mots little-endian et occupent 512 octets. Les doublons et les entrées inutilisées restent présents.
- `couches.csv` détaille les 16 couches BG de mode 0. Les fenêtres limitent le nombre de pixels et de cellules admissibles. Le comptage précède la composition des couches, l’occultation et le rendu des pixels transparents.
- `objets-oam.csv` liste 134 entrées OAM dont le rectangle englobant coupe l’écran, après exclusion des objets désactivés et des objets de fenêtre. La position, la taille et la priorité ne suffisent pas à établir leur visibilité finale. [Documentation vidéo GBA](https://problemkaputt.de/gbatek.htm#gbavideo)
- `blocs-memoire.csv` indique la taille, l’emplacement et le SHA-256 de chaque zone mesurée. La VRAM est représentée par ses empreintes BG et OBJ.
- Les quatre `*-mGBA.png` conservent les pixels de la capture intégrée à chaque état, à leur résolution native de 240 × 160. Les quatre `*-releve.png` associent cette même capture agrandie ×2 aux nuanciers PRAM. Les nuanciers présentent les couleurs chargées, avant mélange et effets d’affichage.

Pour recalculer les relevés à partir des quatre états indiqués dans `preuves.csv`, utiliser Python 3 avec Pillow et la police DejaVu Sans.

```sh
python3 relever_etats.py /chemin/vers/les/etats /chemin/vers/la/sortie
```
