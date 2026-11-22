# Audit de quatorze déclencheurs

Ces quatorze scripts ont été recherchés dans A4NP (Europe), puis recoupés dans A4NE (USA). Pour chacun, la case de la table principale est la seule occurrence du pointeur littéral vers son bloc. Aucun des 696 `CallScript` ni des 459 `SetEntityEventScript` indexés ne les cible. Les deux éditions possèdent le même bytecode pour ces scripts et pour leurs appelants potentiels en VM. Les adresses dans le tableau ci-dessous et dans le [relevé des pointeurs](references-14-a4ne.json) proviennent de la ROM A4NE.

L’audit statique A4NE couvre aussi 214 667 cellules de terrain. Les tables de base et de retouches recensées ne sélectionnent aucun des quatorze identifiants par une action A ou un déplacement. Les recherches de références et d’appels couvrent les mécanismes ci-dessous. La portée des conclusions suit les pistes effectivement décodées. Une interaction voisine vérifiée ne suffit pas à établir un accès au bloc recherché.

## Quatorze scripts

| Script | Bloc A4NE | Fonction et résultat de l’audit |
| --- | --- | --- |
| `0003` | `0x2AC1A8` | Message d’interaction sans effet. Accès normal à établir. |
| `0111` | `0x2C7C50` | Déplacement en `(220, 88)` si le joueur regarde vers le bas. Bloc identique à `0114`. La porte extérieure utilise `0170`, `0169` ou `0168` selon l’agrandissement. |
| `0112` | `0x2C7CC0` | Déplacement en `(160, 24)` si le joueur regarde vers le bas. Même alternative extérieure que `0111`. |
| `0113` | `0x2C7D30` | Déplacement en `(220, 104)` si le joueur regarde vers le haut. Bloc identique à `0115`. Même alternative extérieure que `0111`. |
| `0114` | `0x2C7DA0` | Même bloc que `0111`. Accès normal à établir. |
| `0115` | `0x2C7E10` | Même bloc que `0113`. Accès normal à établir. |
| `0158` | `0x2CBF78` | Message du panneau de réserve de nourriture pour poissons. Accès normal à établir. |
| `0181` | `0x2CE7C4` | Légende d’une bibliothèque. L’attribut actif de la bibliothèque d’Ellen sélectionne `0191` avec A. Les chaînes `0181.00` et `0191.00` sont identiques. L’essai de l’interaction européenne est détaillé ci-dessous. |
| `0340` | `0x2DA028` | Légende de l’escalier vers la cave. En marchant dans la réserve Aja, l’attribut actif sélectionne `0416` pour descendre. Au retour, le mouvement sélectionne `0422`. |
| `0544` | `0x32E744` | Légende d’un élément de sol. Accès normal à établir. |
| `0782` | `0x3698E0` | Scène de la photo de Cliff qui met fin à sa convalescence et ajoute 20 points d’amitié. Le lit de la clinique sélectionne `0229` avec A. Le dialogue de cadeau ordinaire de Cliff utilise `0996`. |
| `1031` | `0x40C9B4` | Menu de modification des affinités. Une mise en file forcée a confirmé son contenu sur A4NP. L’accès en jeu normal reste à établir. L’attribut du calendrier de la ferme sélectionne `0345`. |
| `1032` | `0x410360` | Émission cachée. Les répartiteurs `0356` et `0540` A4NE/A4NP sélectionnent le canal sans signal à 4 h 44 et 16 h 44. L’appel direct à `1032` à ces heures se trouve dans l’édition japonaise. [Répartiteur JP](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/jp/EventScript_TV_ChannelDispatcher.mary.c#L71-L75) · [Répartiteur US](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_TV_ChannelDispatcher.mary.c#L62-L73) |
| `1300` | `0x4F4324` | Mise en place au supermarché. Les 120 premiers octets des sections de code de `1300` à `0x4F433C` et `0016` à `0x2ADBDC` sont identiques. La porte `0372` appelle `0016` à `0x2E6125` pour la rencontre et `1304` à `0x2E5069` dans une autre branche. |

## Lecture du terrain A4NE

La table `gMapData` a 66 entrées de `0x28` octets à `0x105EDC`. À `+0x18`, chaque entrée donne le pointeur vers les mots d’attribut, puis le pointeur vers les indices, puis les dimensions 16 bits. Les tables de retouches ont leurs dimensions sous forme de deux octets au début du descripteur et les deux pointeurs à `+0x10`. Chaque cellule lit un indice sur un octet dans la grille. Le moteur applique les attributs d’une retouche lorsque les deux pointeurs sont renseignés. Un plan de base sans grille reçoit des attributs vides. Le mot 32 bits fournit l’identifiant d’action de marche avec `(mot >> 2) & 0x7FFF`, et l’identifiant du bouton A avec `mot >> 17`. [Données de terrain et lecture du moteur](../terrain.md)

| Table | Offset A4NE | Descripteurs | Cellules examinées |
| --- | --- | ---: | ---: |
| Plans de base | `0x105EDC` | 66 | 205 432 |
| Retouches de la ferme | `0x10692C` | 14 | 2 844 |
| Autres retouches | `0x106A7C` | 68 | 5 189 |
| Visuels de la maison | `0x107204` | 7 | 1 202 |

Le [script de vérification](../../outils/evenements/auditer_terrain.py) prend en option les identifiants à rechercher pour afficher leurs positions.

Repères A4NE des interactions voisines. Les coordonnées ci-dessous sont exprimées en tuiles d’attribut de 8 pixels.

| Script actif | Commande | Plan et cellules | Mot d’attribut A4NE |
| --- | --- | --- | --- |
| `0191` | A | 51, x18–21 y5–7 et 26, x10–13 y5–7 | `0x123F88` et `0x1242EC` |
| `0416` | Marche | 20, x13–16 y11 | `0x132C80` |
| `0422` | Marche | 21, x13–16 y16 | `0x132FE4` |
| `0229` | A | 29, x40–43 y30–35 | `0x125BD8` |
| `0170` | A | Descripteurs `0x10692C` et `0x106944` | `0x121CD8` |
| `0169` | A | Descripteurs `0x10695C` et `0x106974` | `0x121BFC` |
| `0168` | A | Descripteurs `0x10698C` et `0x1069A4` | `0x121AB8` |
| `0345` | A | 41, x21–22 y3–5 | `0x12A5DC` |
| `0372` | A | 4 et 5, x84–87 y17–18 | `0x12B5E0` |

## Chargeurs natifs et tutoriel

- Les références littérales A4NE à la base de la table se trouvent à `0x03F89C`, `0x0DFD20` et `0x0E0534`. Le chargeur par identifiant est à `0x03F878`, le chargeur RIFF à `0x03EEEC` et le lanceur de scènes par identifiant à `0x0DC294`.
- Les deux entrées A4NE du tutoriel à `0x0F19AE` sont `1063` et `1059`. Le script `1059` peut appeler `1061`, `1060` et `1062`, qui rappellent tous `1059`. Le script `1063` ne porte aucun appel `CallScript` indexé.
- Le pointeur Thumb de la mise en file A4NE, `0x0801D9A9`, figure dans la table virtuelle à `0x0E6004` (décalage `+0x140`). Le code correspondant a un appel direct à `0x017A82`. Les formes de sélection de ce décalage par `MOVS` suivi de `LSLS` et par littéral PC-relatif ont été recherchées dans le code natif. Les 43 sites du monde examinés ont un équivalent binaire A4NP. L’audit antérieur A4NP a suivi les producteurs de ces sites ainsi que des méthodes virtuelles d’acteurs, dont les entrées de PNJ, les acteurs errants et les lutins. Les producteurs A4NE à `0x024E76`, `0x02D6FC`, `0x02E90A` et `0x02FB2E` restent des entrées à valeur calculée dans le code natif.

## Essais antérieurs A4NP dans mGBA 0.10.5

| Sujet | État de départ et action | Observation européenne |
| --- | --- | --- |
| Bibliothèque d’Ellen | Partie normale, vers `(160, 68)` en pixels, orientée vers le nord. Appuyer sur A. | `0191`, `CODE` à `0x082CEC88`, texte `0191.00`. |
| Escalier Aja | Coordonnées du joueur préparées près de la réserve. Après l’entrée normale, descendre avec les commandes du jeu. | Le bouton A laisse `0380` courant. En marchant vers le bas, `0416` charge la cave à partir du `CODE` `0x082F1F00`. La remontée déclenche `0422`. |
| Photo de Cliff | Date, météo et état de convalescence préparés, photo en main. Entrée normale puis bouton A au nord ou à l’ouest du lit. | `0229`, `CODE` à `0x082D2D40`. La photo disparaît, l’amitié passe de 50 à 70 et la convalescence reste active dans l’essai terminé. |
| Menu d’affinités | État de test avec une demande `1031` ajoutée à la file en RAM. | Le menu s’ouvre. Ses branches appellent `0424` et `0423`. Le calendrier utilise `0345` dans les données de terrain. |
| Émission cachée | Horloge préparée à 4 h 44 et 16 h 44. Ouvrir le téléviseur. | Programme sans signal aux deux heures. Les essais à 4 h 43 et 4 h 45 montrent la réplique nocturne `0356.06`. |
