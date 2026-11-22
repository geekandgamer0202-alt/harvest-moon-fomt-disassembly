# Friends of Mineral Town USA — événements et dialogues

Les données viennent de la ROM jointe **A4NE, révision 0** de *Harvest Moon: Friends of Mineral Town*. L’en-tête à `0x080000A0` affiche `HARVESTMOGBA`, puis le code `A4NE` à `0x080000AC`. Le SHA-1 vaut `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963`. Le code `BFGE` correspond à *More Friends of Mineral Town* USA, avec sa propre table. [Identification des éditions](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/tools/mary/src/rom_import.cc#L114-L143)

## Fichiers

- `Vie-de-famille-A4NE.csv` donne les conditions de 24 scènes, les appels qui y mènent dans le planificateur et les scripts de suivi après les premiers pas. Il indique aussi l’identifiant et l’offset des six répliques qui annoncent la grossesse.
- `Evenements-A4NE.csv` répertorie les 1 328 scripts et leurs adresses dans le fichier fourni, ainsi que les appels et affectations de dialogues trouvés dans le bytecode. Un lien peut dépendre d’une branche ou d’une action préalable.
- `Dialogues-A4NE.csv` et `Dialogues-A4NE.txt` contiennent les 8 368 chaînes des scripts d’événement. Les identifiants entre crochets permettent de retrouver la réplique et ses suites possibles. La colonne `fr` est réservée à la traduction. Les balises `⟦PAUSE⟧`, `⟦PAGE⟧` et `⟦FF…⟧` rendent visibles les commandes du jeu.

## Déclenchement au réveil

Dans la maison de la ferme, se placer à gauche du lit, regarder à droite, appuyer sur A et choisir de dormir. Le jeu suit `0342 → 0988 → 0980 → 0982 → 0983`. Le dernier appel est à l’offset fichier `0x390BF5`. Le bloc du planificateur `0983` commence à `0x390C7C`. [Lit de la ferme](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_LocationInteraction_FarmhouseBedSleepForDayChoice.mary.c#L23) · [Planificateur des événements](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_SystemEvent_ScheduleDailyEvents.mary.c)

| Conjointe | Annonce | Naissance | Chute du lit | Premiers pas | Autres dates exclues pour la naissance |
|---|---:|---:|---:|---:|---|
| Popuri | 0654 | 0659 | 0684 | 0664 | 3 et 10 été |
| Ann | 0655 | 0660 | 0685 | 0667 | 17 et 22 été |
| Elli | 0656 | 0661 | 0686 | 0670 | 16 et 20 printemps |
| Karen | 0657 | 0662 | 0687 | 0673 | 15 et 23 automne |
| Mary | 0658 | 0663 | 0688 | 0676 | 20 et 23 hiver |
| Déesse des récoltes | 0862 | 0863 | 0866 | 0864 | 8 et 9 printemps |

- **Annonce.** La scène devient éligible avec un mariage conclu, 65 000 points d’affection et au moins 30 jours écoulés selon le calcul du calendrier. Le calcul utilise la saison et le jour sur un cycle de 120 jours. Si la scène est encore en attente au premier anniversaire du mariage, elle redevient éligible 30 jours après cet anniversaire. Pour les cinq villageoises, le Doctor fait l’annonce à la clinique. La Déesse l’annonce elle-même à la ferme, une fois son mariage et le choix du surnom terminés. [Branche Popuri](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_SystemEvent_ScheduleDailyEvents.mary.c#L215-L241) · [Branche Déesse](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_SystemEvent_ScheduleDailyEvents.mary.c#L471-L497)
- **Naissance.** Le compteur atteint 60 jours après la fin de l’annonce et reste à 60 en cas de report. La scène est reportée à l’anniversaire du joueur, aux dates propres à la conjointe et si une branche prioritaire prend la place. Le jeu demande le prénom du garçon, puis passe au lendemain. [Compteur de grossesse](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/npc_collection.cc#L2193-L2217)
- **Chute et premiers pas.** La chute devient éligible à 60 jours d’âge et les premiers pas à 120 jours. Les premiers pas activent des dialogues de suivi, accessibles jusqu’à la réinitialisation quotidienne suivante. [Âge de l’enfant](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/fomt_constants.mary.h#L6459-L6479) · [Nettoyage des dialogues temporaires](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_SystemEvent_ResetDailyWorldState.mary.c#L803-L968)

Le planificateur évalue les anniversaires de mariage avant ces quatre scènes. Il saute aussi cette branche aux dates suivantes. Printemps 1, 14, 18 et 22. Été 1, 7, 20 et 24. Automne 3, 9, 13, 18, 21 et 30. Hiver 14 et 30. [Garde du calendrier](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_SystemEvent_ScheduleDailyEvents.mary.c#L7-L14)

## Vérification de la version

Les adresses des scripts sont lues dans la table A4NE à `0x0F89D4`. Les blocs `CODE` et `JUMP` des 1 328 scripts correspondent octet par octet à ceux de l’édition européenne A4NP. Cette comparaison et le contrôle de la table américaine des 41 noms affichés permettent de reprendre les liens de dialogue et les cartouches déjà analysés. Les textes et leurs adresses ont été relus dans la ROM américaine. Seule la chaîne `1008.00`, l’introduction de Karen, diffère parmi les chaînes des scripts.

Dans mGBA 0.10.5, une partie neuve avec la ROM américaine a atteint la maison de la ferme et ouvert le choix de dormir par les commandes ordinaires. Le pointeur CODE lu pendant l’interaction (`0x082DA91C`) correspond au script `0342`. Les conditions des scènes familiales proviennent de l’analyse du bytecode A4NE.
