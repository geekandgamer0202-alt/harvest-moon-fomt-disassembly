# Désassemblage de Harvest Moon: Friends of Mineral Town

**Français** · [English](README.en.md)

Le projet vise à inventorier, extraire et documenter toutes les données de *Harvest Moon: Friends of Mineral Town* sur Game Boy Advance. L’édition américaine **A4NE** sert de référence. L’édition européenne **A4NP** sert à la comparaison. Les essais français d’origine font partie des archives du projet. [Couverture de la ROM et lots d’extraction](docs/couverture-a4ne.md)

## Accès rapide

| Pour trouver… | Fichiers à ouvrir |
| --- | --- |
| Une réplique et son emplacement | [Dialogues USA en CSV](ressources/textes/A4NE/Dialogues-A4NE.csv) · [Dialogues USA en TXT](ressources/textes/A4NE/Dialogues-A4NE.txt) · [Catalogue Europe en français](ressources/textes/A4NP/fr/) · [Catalogue Europe en anglais](ressources/textes/A4NP/en/) |
| Un personnage ou un objet | [Noms des personnages](docs/textes/Personnages.csv) · [Objets et descriptions](docs/textes/Libelles-objets-A4NE.csv) · [Icônes nommées](docs/graphismes/objets/Index-icones-objets-A4NE.csv) |
| Un prix, un aliment ou une offre de boutique | [Données économiques A4NE](ressources/donnees/economie/A4NE/) · [Structures et conditions](docs/economie.md) |
| Une culture, une recette ou une prise de pêche | [Données d’activités A4NE](ressources/donnees/activites/A4NE/) · [Tables et conditions](docs/activites.md) |
| Un horaire, un lieu ou un trajet de personnage | [Données d’horaires A4NE](ressources/donnees/horaires/A4NE/) · [Lecture des trajets](docs/horaires.md) · [Sélection par date et par météo](docs/selection-horaires.md) |
| Le déclencheur d’une scène | [Événements et appels](docs/evenements/) · [Vie de famille](docs/evenements/vie-de-famille.md) · [Audit des 14 déclencheurs](docs/evenements/declencheurs-14.md) |
| Une carte, un portrait ou un sprite | [Dossier des graphismes](ressources/graphismes/A4NE/) · [Aperçu](ressources/graphismes/A4NE/Apercu.png) · [Index et offsets graphiques](docs/graphismes/) |
| Les attributs et scripts d’une case | [Grilles de terrain](ressources/donnees/terrain/A4NE/) · [Index des interactions](ressources/donnees/terrain/A4NE/Interactions-A4NE.csv) · [Format des données](docs/terrain.md) |
| Une musique, une ambiance ou un effet sonore | [Audio USA](ressources/donnees/audio/A4NE/) · [Audio Europe](ressources/donnees/audio/A4NP/) · [Format et extraction](docs/audio.md) |
| Une procédure ou une capture mGBA | [Guide mGBA 0.10.5](docs/mgba/) · [Captures Europe](ressources/mgba/A4NP/captures/) · [Captures USA](ressources/graphismes/A4NE/mgba/) |
| Les premiers essais de traduction | [Prototype 0.1](ressources/localisation/A4NP/0.1/LISEZMOI.md) · [Prototype 0.2](ressources/localisation/A4NP/0.2/LISEZMOI.md) |

`ressources/` contient les textes, images, fichiers graphiques natifs et rapports. `docs/` contient les index techniques et les résultats de vérification, rédigés pour la plupart en français. `outils/` contient les scripts Python. Pour consulter un gros CSV ou TXT sur GitHub, utiliser **Raw** ou **Download raw file**. [Inventaire des ressources](ressources/README.md) · [Empreintes des ZIP d’origine](docs/archives-de-travail.md) · [Outils Python](outils/)

## Éditions et adresses de référence

| Code | Édition | Révision | SHA-1 de référence |
| --- | --- | ---: | --- |
| `A4NE` | *Friends of Mineral Town*, USA | 0 | `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963` |
| `A4NP` | *Friends of Mineral Town*, Europe | 0 | `7ba1ec1e46ce424e3c6fd72e4e8d5e9eb5ede247` |
| `BFGE` | *More Friends of Mineral Town*, USA | — | `3aa4d46cbbf152e440942acd5f5d37ddc7b05e1d` |

Les ROM A4NE et A4NP analysées font chacune 8 388 608 octets. Le code d’édition se lit à l’offset `0xAC`, et la révision à `0xBC`. Les adresses des index sont des offsets dans le fichier. Pour les convertir en adresses ROM GBA, ajouter `0x08000000`. Par exemple, la table de scripts A4NE à `0x0F89D4` correspond à `0x080F89D4` en mémoire. [Empreintes, en-têtes et comparaison](docs/versions.md)

L’indice communautaire à l’adresse `0x080000A0` correspond à l’en-tête BFGE de *More Friends of Mineral Town*. Son index de 1 415 emplacements et ses 31 repères familiaux proviennent du catalogue de symboles et de la documentation. Les scripts et offsets A4NE ci-dessous concernent *Friends of Mineral Town*. [Dossier BFGE](ressources/evenements/BFGE/) · [Lecture de l’indice](docs/versions.md#lindice-communautaire-bfge)

## Textes et noms

Les éditions A4NE et A4NP ont chacune **8 368 chaînes d’événement**. Le catalogue Europe ajoute **283 chaînes natives** issues des menus et autres lecteurs directs. Ses versions française et anglaise changent la langue des annotations et conservent le texte d’origine du jeu. [Catalogue Europe en français](ressources/textes/A4NP/fr/) · [Catalogue Europe en anglais](ressources/textes/A4NP/en/)

Un identifiant comme `0162.00` désigne la première chaîne du script `0162`. Il permet de retrouver le panneau de la caisse d’expédition à `0x2CC120` en A4NE ou à `0x2CC178` en A4NP. Les exports indiquent l’ID, l’offset, la longueur et le contexte de la chaîne. Le texte comprend des commandes du moteur, comme `05` pour attendre une action, `0C` pour changer de page et `FF21` pour insérer le nom du joueur. [Index et codes de contrôle](docs/textes/)

Les **52 entrées de personnages** couvrent les noms affichés, les rôles et les noms issus de la sauvegarde. Les tables d’inventaire comptent **347 objets** répartis en 81 outils, 171 aliments et 95 articles. Leurs noms et descriptions ont été comparés dans les deux éditions. [Catalogue des personnages](docs/textes/Personnages.csv) · [Libellés A4NE](docs/textes/Libelles-objets-A4NE.csv) · [Libellés A4NP](docs/textes/Libelles-objets-A4NP.csv)

Les essais historiques A4NP ont documenté les champs de saisie du joueur, de la ferme et du chien, la largeur des libellés et les pointeurs utilisés par le moteur. Les deux prototypes regroupent les patchs BPS, les scripts de construction, les manifestes de texte et les captures. La version **0.2** inclut le bouton **Fini**. [Essai 0.1](ressources/localisation/A4NP/0.1/LISEZMOI.md) · [Essai 0.2](ressources/localisation/A4NP/0.2/LISEZMOI.md) · [Offsets de l’interface](docs/textes/README.md#saisie-du-joueur-de-la-ferme-et-du-chien)

## Événements et déclencheurs

Les tables des **1 328 scripts** commencent à `0x0F89D4` en A4NE et à `0x0F8A20` en A4NP. Chaque bloc `RIFF/SCR` peut contenir le bytecode `CODE`, une table de sauts `JUMP` et les chaînes `STR`. La comparaison des ROM confirme l’égalité de `CODE` et `JUMP`. Seule `1008.00`, dans la présentation de Karen, diffère parmi les chaînes d’événement. [Structure des scripts](docs/evenements/README.md#structure-vérifiée) · [Comparaison A4NE/A4NP](docs/comparaison-a4ne-a4np.json)

- **Appels et dialogues.** L’index A4NE relève 696 appels `CallScript` et 459 affectations `SetEntityEventScript`. Les affectations associent un dialogue à un acteur pour une interaction ultérieure. Les conditions dépendent du branchement qui mène à l’instruction. [Sites d’appel](docs/evenements/appels-a4ne.csv)
- **Vie de famille.** Le sommeil passe par `0342 → 0988 → 0980 → 0982 → 0983`. Le planificateur `0983`, à l’offset A4NE `0x390C7C`, sélectionne les branches selon le mariage, l’affection, la date et la progression familiale. L’analyse statique situe 24 scènes. Dans mGBA, le lit `0342` a été observé en partie neuve. Le jeu a sélectionné le script `0657` de Karen et a affiché l’annonce `0657.03` après un sommeil ordinaire depuis une copie d’état préparée en RAM. [Conditions et scènes](docs/evenements/vie-de-famille.md) · [Procédure Karen](docs/mgba/usa-a4ne.md#test-ciblé-de-karen)
- **Quatorze déclencheurs.** La recherche a couvert les appels et affectations indexés ainsi que 214 667 cellules de terrain par édition, avec zéro référence vers les 14 identifiants dans ces mécanismes. Des essais Europe ont confirmé des interactions voisines, comme la bibliothèque d’Ellen via `0191`. L’accès en jeu normal aux blocs recherchés reste à établir là où l’audit n’a trouvé que des indices. [Résultats par script](docs/evenements/declencheurs-14.md)

## Graphismes et captures mGBA

![Aperçu des cartes, portraits, objets et scènes A4NE](ressources/graphismes/A4NE/Apercu.png)

L’extraction graphique A4NE compte **4 577 PNG** et conserve les index, les palettes et les blocs graphiques natifs. [Guide des fichiers](ressources/graphismes/A4NE/Lire-moi.md) · [Manifeste SHA-256](ressources/graphismes/A4NE/Manifest-graphismes.csv)

| Famille | Contenu | Repère A4NE |
| --- | --- | --- |
| Cartes | 66 plans de base, 84 compositions avec les variantes de nuit, 31 jeux de tuiles et 47 palettes. | `gMapData` à `0x105EDC` · [Index des plans](docs/graphismes/cartes/Cartes.csv) |
| Portraits et sprites | 184 portraits, 3 009 images de sprites et 2 551 sélecteurs d’animation. | Archives à `0x52D984` et `0x58BA28` · [Planches](ressources/graphismes/A4NE/personnages/Planches/) |
| Icônes et groupes OBJ | 347 icônes d’inventaire et 52 archives OBJ supplémentaires, dont 939 groupes graphiques composés. | Archive commune à `0x6678A0` · [Archives OBJ](docs/graphismes/archives-obj/Archives-OBJ.csv) |
| Interface | Titre, menus, polices, fonds et écrans d’introduction. | [Plages ROM dans l’index de l’interface](docs/graphismes/interface/Interface.csv) |

Les cartes représentent les décors statiques. Les personnages, la météo, les cultures et les animations s’ajoutent selon l’état du jeu. Les **six relevés mGBA 0.10.5** documentent les palettes de décor (BG), les palettes de sprites (OBJ), les entrées OAM et les couches actives. Quatre proviennent d’une partie normale et deux du test préparé de Karen. Les mesures décrivent les données chargées et les objets dans le cadre avant la composition de l’image finale. [Relevés vidéo](docs/mgba/preuves-video.csv) · [Vues de diagnostic mGBA](docs/mgba/graphismes.md)

Les essais Europe documentent aussi l’expédition, les semis, les cadeaux et la sauvegarde suivie d’un rechargement. [Rapport Europe](ressources/mgba/A4NP/Rapport.md) · [Captures Europe](ressources/mgba/A4NP/captures/)

## Terrain et interactions

L’export de terrain couvre **155 descripteurs**, dont 66 plans de base, et **214 667 cellules** lues dans la ROM. Les grilles renvoient à **722 mots d’attribut** qui conservent les deux bits utilisés par les tests de collision et les identifiants de scripts. Un index situe les **9 383 cellules avec interaction** par plan ou retouche et par coordonnées locales. [Données de terrain](ressources/donnees/terrain/A4NE/) · [Format et limites du relevé](docs/terrain.md)

## Objets et économie

Les CSV économiques A4NE couvrent **347 fiches d’objet**, les effets de base de **171 aliments** sur l’endurance et la fatigue, les prix de **103 produits expédiables** et **12 catalogues de boutiques**. Les tables conservent les identifiants et offsets ROM. Les catalogues distinguent les prix stockés des conditions appliquées par le jeu. [Fichiers économiques](ressources/donnees/economie/A4NE/) · [Documentation](docs/economie.md) · [Conditions des boutiques](docs/economie-boutiques.md)

## Ferme, cuisine et pêche

Les exports A4NE couvrent **39 types de parcelles** avec les tables de croissance, de repousse et de météo. La cuisine comprend **117 définitions de recettes**, les listes d’ingrédients et d’ustensiles et les résultats d’échec. Les tables de pêche recensent **59 prises**, avec leurs tailles, zones, saisons et niveaux de canne. [Fichiers d’activités](ressources/donnees/activites/A4NE/) · [Formats et conditions](docs/activites.md)

## Horaires et trajets des personnages

Les tables A4NE couvrent **32 personnages**, **254 cases de variante** dont 222 avec un horaire, **1 122 étapes** et **430 trajets**. Un relevé distinct compte **38 400 appels** aux sélecteurs natifs sur les 120 jours de l’an 1, pour cinq codes météo et deux états mGBA, à 06:00. Ces appels ont renvoyé **122 cases de variante distinctes**. [Horaires et trajets](ressources/donnees/horaires/A4NE/) · [Résultats des sélecteurs](ressources/donnees/selecteurs/A4NE/) · [Méthode et résultats](docs/selection-horaires.md)

## Audio M4A

Le catalogue contient **211 cases**, dont **144 séquences**, ainsi que **277 pistes**, **263 fiches d’instrument**, **106 échantillons PCM** et **32 ondes CGB**. Il relève **149 cycles de piste** et **27 boucles PCM**. Les données USA et Europe concordent après correction des adresses. [Audio USA](ressources/donnees/audio/A4NE/) · [Audio Europe](ressources/donnees/audio/A4NP/) · [Format et extraction](docs/audio.md)

## Reproduire les vérifications

Les exemples utilisent **Python 3.10 ou ultérieur** et des copies locales des ROM d’origine. Après avoir cloné le dépôt, placer les copies sous `roms/A4NE.gba` et, pour la comparaison, `roms/A4NP.gba`. Les ROM, sauvegardes et états mGBA restent dans l’environnement de test.

```sh
git clone https://github.com/geekandgamer0202-alt/harvest-moon-fomt-disassembly.git
cd harvest-moon-fomt-disassembly
mkdir -p roms exports
```

Vérifier d’abord le code et l’empreinte. L’identificateur accepte également un ZIP contenant une seule ROM. Les indexeurs de scripts et de textes utilisent le fichier `.gba` et produisent leurs CSV sur la sortie standard.

```sh
python3 outils/identifier_rom.py roms/A4NE.gba
python3 outils/evenements/indexer_scripts.py roms/A4NE.gba > exports/scripts-a4ne.csv
python3 outils/evenements/indexer_scripts.py roms/A4NE.gba --appels > exports/appels-a4ne.csv
python3 outils/textes/indexer_textes.py roms/A4NE.gba > exports/index-textes-a4ne.csv
python3 outils/graphismes/verifier_index_a4ne.py roms/A4NE.gba
python3 outils/evenements/exporter_terrain.py roms/A4NE.gba exports/terrain-a4ne
python3 outils/economie/exporter_economie.py roms/A4NE.gba exports/economie-a4ne
python3 outils/jeu/exporter_activites.py roms/A4NE.gba exports/activites-a4ne
python3 outils/jeu/exporter_horaires.py roms/A4NE.gba exports/horaires-a4ne
```

Pour refaire la comparaison régionale ou les recherches de références, utiliser les commandes suivantes. `auditer_terrain.py` accepte aussi des identifiants décimaux en arguments pour localiser un script précis.

```sh
python3 outils/evenements/indexer_scripts.py roms/A4NE.gba --comparer roms/A4NP.gba
python3 outils/evenements/indexer_scripts.py roms/A4NE.gba --audit-quatorze
python3 outils/evenements/auditer_terrain.py roms/A4NE.gba 0342
```

Pour examiner le script et la mémoire vidéo d’une scène, enregistrer un état mGBA 0.10.5 à l’aide du guide. Pour l’exemple, enregistrer `exports/mgba/sommeil-a4ne.state` pendant le dialogue du lit à la ferme. [Guide mGBA](docs/mgba/) · [Parcours USA](docs/mgba/usa-a4ne.md) · [Parcours Europe](docs/mgba/europe-a4np.md)

```sh
python3 outils/mgba/inspecter_etat.py --rom roms/A4NE.gba exports/mgba/sommeil-a4ne.state
```

Le relevé des sélecteurs d’horaires utilise Unicorn pour exécuter les routines ROM isolément. Il fait varier la date et la météo et garde les autres champs de l’état fixes. [Procédure de relevé](docs/selection-horaires.md#refaire-le-relevé)

L’outil audio fonctionne sur les deux éditions et peut générer les CSV ainsi que les pistes et échantillons bruts. [Commande d’export audio](docs/audio.md#reproduire-lexport)

Pour ajouter un relevé reproductible, préciser l’édition, l’ID ou l’offset, la situation en jeu et l’outil utilisé. Les rapports distinguent les observations en partie normale, les essais sur un état préparé et la lecture statique de la ROM.

## Données à documenter

Les travaux en cours couvrent les textes natifs A4NE hors scripts d’événement, les déclencheurs et conditions d’horaires encore inconnus, les transitions entre cartes et le placement des retouches, les interfaces et mini-jeux restants, les données d’élevage et le format des sauvegardes sur cartouche. Il reste à identifier 31 séquences audio et à vérifier leur rendu dans mGBA, ainsi qu’à inventorier les plages d’octets de la ROM. [État détaillé de la couverture](docs/couverture-a4ne.md)

[Désassemblage FoMT de Wokann](https://github.com/Wokann/fomt) · [Format des scripts d’événement](https://github.com/StanHash/FOMT-DOC/blob/master/EventScripts.txt) · [mGBA 0.10.5](https://github.com/mgba-emu/mgba/releases/tag/0.10.5)
