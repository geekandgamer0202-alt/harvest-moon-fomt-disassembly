# Grossesse, naissance et développement de l’enfant

Le [tableau des événements familiaux A4NE](vie-de-famille-a4ne.csv) situe les 24 blocs et la position de leur instruction d’appel dans le planificateur `0983`. Les six annonces portent aussi l’identifiant et l’offset de la réplique correspondante.

## Parcours depuis le lit

Dans la maison de la ferme, le joueur se place à gauche du lit, regarde vers la droite et appuie sur A. Le choix de passer au lendemain conduit à la chaîne suivante. L’appel `0982 → 0983` entre dans le planificateur au bloc `0x390C7C`, dont la première instruction se trouve à `0x390C94`.

| Script source | Script cible | Instruction A4NE |
| --- | --- | --- |
| `0342` | `0988` | `0x2DAD23` |
| `0988` | `0980` | `0x3944BE` |
| `0980` | `0982` | `0x38C6AF` |
| `0982` | `0983` | `0x390BF5` |

## Conditions relevées dans le bytecode

La branche familiale requiert une conjointe mariée et le joueur dans la maison de la ferme au moment du test. Pour la Déesse, la condition de mariage exige aussi l’achèvement de la scène de choix du surnom. Les mariages et anniversaires de mariage ont la priorité lorsque leur branche est sélectionnée. Un filtre en amont écarte les branches familiales aux dates suivantes. [Planificateur US, début et branche de Karen](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_SystemEvent_ScheduleDailyEvents.mary.c#L7-L201) · [Branche de la Déesse](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_SystemEvent_ScheduleDailyEvents.mary.c#L471-L519)

| Saison | Jours écartés en amont |
| --- | --- |
| Printemps | 1, 14, 18, 22 |
| Été | 1, 7, 20, 24 |
| Automne | 3, 9, 13, 18, 21, 30 |
| Hiver | 14, 30 |

- **Annonce.** La scène doit être à l’état « à venir » et l’affection doit atteindre 65 000 points. Le planificateur compare les jours de l’année, calculés par `saison × 30 + jour`, et ajoute 120 au jour courant lorsque celui-ci précède la date de mariage dans le cycle. Le résultat doit être au moins égal à 30 jours. La date se recalcule sur ce cycle à chaque anniversaire. Le Doctor annonce la grossesse à la clinique pour les cinq villageoises. La Déesse l’annonce à la ferme.
- **Naissance.** La scène devient éligible à 60 jours après la fin de l’annonce. Le code natif ne fait plus progresser le compteur lorsqu’il atteint 60 en jeu normal. Le planificateur peut reporter l’événement si une branche prioritaire est sélectionnée, à l’anniversaire du joueur ou aux dates propres à la conjointe. Le jeu ouvre le choix du prénom de l’enfant, puis passe au jour suivant. [Compteur natif](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/npc_collection.cc#L2193-L2217)
- **Chute du lit et premiers pas.** Les seuils sont respectivement 60 et 120 jours d’âge. Les premiers pas affectent des scripts de suivi aux acteurs, puis la réinitialisation quotidienne enlève ces affectations. Dans le cas de la Déesse, `0864` attribue `0865` à l’enfant, à l’instruction A4NE `0x3794AD`. [Constantes d’âge](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/fomt_constants.mary.h#L6459-L6479) · [Réinitialisation quotidienne](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_SystemEvent_ResetDailyWorldState.mary.c#L803-L969)

| Conjointe | Annonce | Naissance | Chute | Premiers pas | Autres jours de report de la naissance |
| --- | --- | --- | --- | --- | --- |
| Popuri | `0654` | `0659` | `0684` | `0664` | Été 3 et 10 |
| Ann | `0655` | `0660` | `0685` | `0667` | Été 17 et 22 |
| Elli | `0656` | `0661` | `0686` | `0670` | Printemps 16 et 20 |
| Karen | `0657` | `0662` | `0687` | `0673` | Automne 15 et 23 |
| Mary | `0658` | `0663` | `0688` | `0676` | Hiver 20 et 23 |
| Déesse des récoltes | `0862` | `0863` | `0866` | `0864` | Printemps 8 et 9 |

L’âge de l’enfant est stocké à `+0x25` dans sa structure et progresse jusqu’à 255 dans la routine native `0x09EAF8–0x09EB20` (test et incrément à `0x09EB0E–0x09EB18`). Le code natif du renouvellement quotidien des PNJ se trouve entre `0x0A0B18` et `0x0A1478` en A4NE. La séquence `0x0A1004–0x0A105A` teste l’achèvement des six annonces et incrémente le compteur de grossesse lorsque sa valeur diffère de 60, à `+0x470` dans la collection de PNJ. Dans la branche de Karen, les opérandes du bytecode servant aux comparaisons sont à `0x391A1C` (65 000), `0x391A3B` (30 jours), `0x391A8A` (60 jours de grossesse), `0x391B6F` (60 jours d’âge) et `0x391BBD` (120 jours d’âge).

## Observations dans mGBA 0.10.5

| Essai A4NE | État initial et action | Résultat |
| --- | --- | --- |
| Nuit ordinaire | Partie neuve, maison de la ferme, printemps 2 à 06 h. Dialogue du lit puis confirmation du sommeil. | Le pointeur de code identifie le script `0342`, avec `CODE` à l’adresse GBA `0x082DA91C` et le compteur du bytecode à `+0x50`. Après le sommeil, le printemps 3 à 06 h est affiché et le script courant est `0987` à `0x08393F08`. |
| Annonce de Karen | Copie de l’état mGBA à l’écran de confirmation. La date, le mariage, l’affection et l’agrandissement de la maison sont préparés dans cet état. Confirmation avec la commande ordinaire du jeu. | Été 5 à 06 h. Script `0657`, `CODE` à `0x08345884`, compteurs observés `+0x92`, `+0x1C0` et `+0x1FC`. Le Doctor affiche `0657.03` à la clinique (offset ROM `0x345CA4`). L’appel depuis `0983` est à `0x391A60`. |

L’essai de Karen valide la sélection de la scène depuis un état admissible préparé. Les seuils calendaires, les autres conjointes, la naissance et les étapes de l’enfance restent documentés par analyse statique.
