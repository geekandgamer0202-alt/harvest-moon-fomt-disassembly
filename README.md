# Désassemblage de Harvest Moon: Friends of Mineral Town

Notes techniques et outils d’analyse de *Harvest Moon: Friends of Mineral Town* sur Game Boy Advance pour préparer une traduction française. L’édition américaine `A4NE` sert de référence. Les essais et catalogues européens `A4NP` sont identifiés par leur version.

[Ouvrir les fichiers d’extraction](ressources/) pour consulter les dialogues complets, les images, les ressources graphiques natives, les captures mGBA et les essais de localisation.

## Résultats

| Sujet | Repères |
| --- | --- |
| [Textes et localisation](docs/textes/) | Index des répliques, noms, codes de contrôle et essais de saisie sur A4NP |
| [Événements et déclencheurs](docs/evenements/) | 1 328 scripts et leurs appels, scènes familiales et audit des 14 déclencheurs |
| [Graphismes](docs/graphismes/) | 66 plans, archives de portraits et sprites, objets, palettes et interface |
| [Tests mGBA](docs/mgba/) | Vérifications en jeu, états préparés et relevés vidéo par scène |
| [Versions et comparaison](docs/versions.md) | Empreintes A4NE et A4NP, comparaison du bytecode et édition BFGE |
| [Archives de travail](docs/archives-de-travail.md) | Noms et empreintes des ZIP produits pendant l’analyse |

## Version de référence

| Donnée | Valeur |
| --- | --- |
| Code de la ROM | `A4NE` |
| Révision | `0` |
| SHA-1 | `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963` |
| Émulateur de vérification | mGBA 0.10.5 |

## Repères de désassemblage

| Ressource | Offset dans le fichier ROM |
| --- | --- |
| Table des scripts d’événement | `0x0F89D4` |
| Table des plans du monde (`gMapData`) | `0x105EDC` |
| Archive des portraits | `0x52D984` |
| Archive des sprites du monde | `0x58BA28` |
| Archive commune des icônes | `0x6678A0` |

Ajouter `0x08000000` à un offset de fichier pour obtenir l’adresse GBA correspondante. Pour chaque repère, indiquer la version de la ROM, l’offset et la méthode de vérification. Conserver la ROM locale dans `roms/` et les fichiers extraits dans `exports/`.

Pour vérifier l’édition et l’empreinte d’une ROM ou du ZIP qui la contient, lancer l’identification depuis la racine du dépôt.

```sh
python3 outils/identifier_rom.py "roms/Harvest Moon - Friends of Mineral Town (USA).gba"
```
