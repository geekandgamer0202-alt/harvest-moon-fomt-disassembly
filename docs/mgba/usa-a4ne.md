# USA A4NE · démarrage et événement 0657

Les essais utilisent la [ROM de référence A4NE révision 0](README.md#préparation), sans patch. Le contexte de l’interpréteur principal est relevé dans un état enregistré par mGBA 0.10.5. Le pointeur à `0x02002080` est comparé à la première instruction de chaque bloc `CODE` depuis la table ROM `0x0F89D4`. L’indicateur brut à `0x0200207C` et le PC relatif à `0x02002084` permettent de distinguer un script en cours d’un contexte résiduel. [Structure des scripts d’événement](https://github.com/StanHash/FOMT-DOC/blob/master/EventScripts.txt)

## Partie normale

1. Partir du menu titre et créer une nouvelle partie. Saisir le nom du joueur, valider l’anniversaire, puis saisir les noms de la ferme et du chien. Faire avancer l’introduction jusqu’à pouvoir déplacer le joueur dans la maison.
2. Le 2 printemps à 6 h, se placer à gauche du lit, orienter le joueur vers la droite et appuyer sur A. Au choix de dormir, laisser l’écran ouvert et enregistrer `sommeil-a4ne.state`. Le relevé doit résoudre `0342` et `CODE 0x082DA91C`.
3. Confirmer le sommeil et attendre de reprendre le contrôle. Le jeu avance au 3 printemps à 6 h, an 1. Enregistrer `reveil-a4ne.state` dans la maison. La référence conserve dans ce relevé le pointeur de `0987` avec indicateur brut à `0`.

```sh
python3 outils/mgba/inspecter_etat.py --rom roms/jeu-a4ne.gba \
  exports/mgba/sommeil-a4ne.state exports/mgba/reveil-a4ne.state
```

## Test ciblé de Karen

Le test accélère la progression familiale à partir d’une **copie de l’état A4NE à la confirmation du sommeil**. Les huit modifications sont limitées à la structure de sauvegarde en EWRAM à `0x020025D8`. Les autres octets du bloc `gbAs` et les autres blocs du PNG sont conservés. Le programme vérifie les octets d’origine, la date et le contexte `0342` avant de créer un nouveau fichier. La copie conserve l’image de son écran de départ jusqu’à la première actualisation par mGBA.

```sh
python3 -B outils/mgba/preparer_karen.py exports/mgba/sommeil-a4ne.state \
  exports/mgba/karen-test.state
mgba-qt -t exports/mgba/karen-test.state roms/jeu-a4ne.gba
```

| Offset relatif à la sauvegarde en EWRAM | Avant | Après | Champ |
| --- | --- | --- | --- |
| `0x0011` | `04` | `0D` | Date courante, 2 printemps → 4 été |
| `0x01F4–0x01F5` | `00 80` | `02 90` | Agrandissement de la maison et aménagement du lit |
| `0x1D00–0x1D01` | `00 00` | `01 0C` | Date de mariage préparée, 4 printemps de l’an 1 |
| `0x1ECC–0x1ECE` | `00 00 08` | `FF FF 0E` | Affection et état de la relation de Karen |

Une fois la copie chargée, appuyer sur A pour confirmer le sommeil. Le jeu passe au **5 été, an 1, 6 h** et sélectionne `0657`. Faire avancer l’échange à la ferme, puis le diagnostic à la clinique. Le médecin annonce la grossesse. L’essai vérifie la sélection et l’exécution du script après l’action de dormir. Aucun identifiant de script n’est écrit par la préparation. La progression jusqu’au mariage et l’attente des jours requis ont été étudiées dans le bytecode.

| Point relevé | ID | Adresse `CODE` GBA | PC relatif | Indicateur brut |
| --- | --- | --- | --- | ---: |
| Confirmation du sommeil de départ | `0342` | `0x082DA91C` | `0x50` | 1 |
| Réveil normal | `0987` | `0x08393F08` | `0x1F7` | 0 |
| Dialogue avec Karen à la ferme, test préparé | `0657` | `0x08345884` | `0x92` | 1 |
| Diagnostic à la clinique, test préparé | `0657` | `0x08345884` | `0x1C0` | 1 |
| Annonce à la clinique, test préparé | `0657` | `0x08345884` | `0x1FC` | 1 |

L’annonce correspond à l’entrée `0657.03` à l’offset ROM `0x345CA4`. L’analyse du bytecode associe le sommeil à la chaîne `0342 → 0988 → 0980 → 0982 → 0983`. Le planificateur `0983` évalue entre autres le mariage conclu, au moins 65 000 points d’affection et le délai de 30 jours. Les autres conjointes, la naissance, la chute du lit et les premiers pas relèvent ici de l’analyse statique. [Script du lit](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_LocationInteraction_FarmhouseBedSleepForDayChoice.mary.c#L23) · [Planificateur journalier](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_SystemEvent_ScheduleDailyEvents.mary.c)
