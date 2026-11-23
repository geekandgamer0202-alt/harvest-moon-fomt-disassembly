# Fichiers d’extraction et essais

Les fichiers sont conservés dans leurs formats d’origine, avec leurs noms et leurs chemins relatifs. Pour un gros CSV ou TXT, ouvrir le fichier puis choisir **Raw** ou **Download raw file** dans GitHub.

| Ressource | Contenu | Fichiers |
| --- | --- | --- |
| Textes A4NE USA | 8 368 chaînes d’événement, catalogue des scripts et scènes familiales. | [Dossier](textes/A4NE/) · [CSV](textes/A4NE/Dialogues-A4NE.csv) · [TXT](textes/A4NE/Dialogues-A4NE.txt) |
| Textes A4NP Europe | 8 651 chaînes, dont 283 textes natifs, avec les noms des objets et personnages. Le catalogue anglais conserve les mêmes chaînes du jeu et traduit les annotations. | [Catalogue français](textes/A4NP/fr/) · [Catalogue anglais](textes/A4NP/en/) · [Produits expédiables](textes/A4NP/Produits-expediables.csv) |
| Graphismes A4NE USA | 4 577 PNG et leurs index, portraits, sprites, cartes, palettes, polices et blocs graphiques natifs. | [Dossier](graphismes/A4NE/) · [Aperçu](graphismes/A4NE/Apercu.png) · [Guide](graphismes/A4NE/Lire-moi.md) |
| Terrain A4NE USA | 155 descripteurs, 143 grilles lues dans la ROM, attributs de terrain et cellules liées à un script. | [Dossier](donnees/terrain/A4NE/) · [Format](../docs/terrain.md) |
| Économie A4NE USA | Fiches d’objet, effets des aliments, prix d’expédition et catalogues de boutiques. | [Dossier](donnees/economie/A4NE/) · [Format](../docs/economie.md) |
| Activités A4NE USA | Croissance et repousse des cultures, recettes et ingrédients, zones et prises de pêche. | [Dossier](donnees/activites/A4NE/) · [Format](../docs/activites.md) |
| Horaires A4NE USA | Variantes de 32 personnages, 1 122 étapes, lieux et points des trajets. | [Dossier](donnees/horaires/A4NE/) · [Format](../docs/horaires.md) |
| Sélection des horaires A4NE USA | Choix des 32 sélecteurs par jour et par code météo dans deux états d’essai. | [Dossier](donnees/selecteurs/A4NE/) · [Protocole](../docs/selection-horaires.md) |
| Audio M4A USA et Europe | Catalogue des 211 cases, pistes et boucles, instruments, PCM et ondes CGB. | [A4NE](donnees/audio/A4NE/) · [A4NP](donnees/audio/A4NP/) · [Format et export](../docs/audio.md) |
| Routines natives USA et Europe | 327 ID d’appel, 75 522 sites VM et 590 identifiants de variable avec leurs branches Thumb. | [Dossier](donnees/routines-natives/) · [Format et export](../docs/evenements/routines-natives.md) |
| Écritures de variables USA et Europe | Expressions calculées ou littérales des 1 850 appels `VarSet` et origines des valeurs lues dans des locales. | [Dossier](donnees/ecritures-variables/) · [Décomposition](../docs/evenements/ecritures-variables.md) |
| Lectures de variables USA et Europe | 1 770 traces `VarGet`, offsets de l’image de sauvegarde en RAM et 485 formules de lecture par masque. | [Dossier](donnees/lectures-variables/) · [Protocole et champs partagés](../docs/evenements/lectures-variables.md) |
| Sauvegarde SRAM USA et Europe | 674 lectures projetées dans les deux emplacements `.sav`, mesures d’écriture et contrôles après redémarrage. | [Dossier](donnees/sauvegarde/) · [Format et inspecteur](../docs/sauvegarde.md) |
| Essais mGBA | Rapports de jeu, captures d’écran et palettes relevées. | [A4NP Europe](mgba/A4NP/Rapport.md) · [A4NE USA](graphismes/A4NE/mgba/LISEZ-MOI.md) |
| Localisation A4NP Europe | Essais historiques 0.1 et 0.2 avec manifestes de texte, scripts, BPS et captures. Le bouton **Fini** figure dans la 0.2. | [Essai 0.1](localisation/A4NP/0.1/LISEZMOI.md) · [Essai 0.2](localisation/A4NP/0.2/LISEZMOI.md) |
| Repères BFGE | Index des événements de *More Friends of Mineral Town* USA d’après le catalogue de symboles. | [Dossier](evenements/BFGE/) · [Guide](evenements/BFGE/Lire-moi.md) |

Les empreintes des ZIP source sont consignées dans [les archives de travail](../docs/archives-de-travail.md). Le [manifeste graphique](graphismes/A4NE/Manifest-graphismes.csv) donne les dimensions, tailles et SHA-256 des fichiers associés. La sauvegarde `Partie-test-initiale.sav` mentionnée dans le rapport Europe se trouve dans le ZIP historique. Les ROM complètes et les états mGBA restent dans l’espace de travail.
