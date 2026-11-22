# Désassemblage de Harvest Moon: Friends of Mineral Town

Notes techniques et outils d’analyse pour l’édition américaine de *Harvest Moon: Friends of Mineral Town* sur Game Boy Advance. Le projet documente le texte, les événements et les ressources graphiques en vue d’une traduction française.

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
