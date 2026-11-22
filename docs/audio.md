# Audio M4A de Friends of Mineral Town

L’export suit les **211 cases** de `gSongTable` dans les ROM USA A4NE et Europe A4NP. Dans chaque édition, **144 cases** donnent une séquence et **67** pointent vers le même en-tête de zéro piste. Le relevé couvre **277 pistes**, **263 fiches de voix** dans deux banques, **106 échantillons PCM** et **32 ondes CGB**. Tous les offsets des CSV sont relatifs au fichier ROM. [Exports USA](../ressources/donnees/audio/A4NE/) · [Exports Europe](../ressources/donnees/audio/A4NP/)

## Tables et fichiers

| CSV | Lignes par édition | Offset A4NE ou origine |
| --- | ---: | --- |
| `Lecteurs` | 5 | `gMusicPlayerTable` à `0x13ABB4`. Adresses GBA de l’état et des pistes en RAM, capacité et champ `+0x0A`. |
| `Sequences` | 211 | `gSongTable` à `0x13ABF0`. ID, en-tête, champs `ms` et `me`, priorité, réverbération, banque et nombre de pistes en boucle. |
| `Pistes` | 277 | Pointeurs de chaque en-tête de séquence. Plage ROM, terminaison, durée en ticks, instruments et tempos rencontrés. |
| `Sauts-pistes` | 2 933 | Relations observées pendant le parcours. Sauts `GOTO`, appels `PATT` et retours `PEND` avec leurs adresses. |
| `Instruments` | 263 | Banque de musique à `0x139D60` (128 fiches) et banque d’effets à `0x13A360` (135 fiches). Types, paramètres et cibles PCM, CGB ou percussion. |
| `Echantillons` | 106 | Pointeurs des voix PCM. Taille, fréquence brute, position de boucle et SHA-256 des données PCM signées de 8 bits. |
| `Ondes-CGB` | 32 | `gM4aCgbWaveData` à `0x13A9B4`. Une onde de 16 octets contient 32 valeurs de 4 bits. |

Une case `SongEnt` fait huit octets. Son pointeur mène à l’en-tête `Song`, dont les quatre premiers octets contiennent le nombre de pistes, le nombre de blocs, la priorité et la réverbération. Le pointeur de banque vient à `+0x04`. Les pointeurs de piste suivent à `+0x08`. Le lecteur utilise `ms` comme index, tandis que l’export conserve les deux champs `ms` et `me`. Les séquences présentes utilisent les lecteurs `0` ou `3`. [Structures M4A](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/m4a.h#L254-L262) · [Table et lecteur](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/m4a.c#L813-L850)

Les symboles du catalogue attribuent **18 musiques**, **4 ambiances**, **15 disques** et **76 effets**. Les **31 séquences** à symbole générique conservent la famille `indeterminee`. Les ID `18` à `32` correspondent aux 15 emplacements de disques. Les cinq derniers portent des noms d’album numérotés dans le catalogue. [Domaines des identifiants audio](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/fomt_constants.mary.h#L3170-L3245)

## Pistes, instruments et boucles

Le parcours applique la table d’attente, le dernier opcode réutilisable et les appels de motif du lecteur. **128 pistes** atteignent `FINE`. **149 pistes**, réparties dans **31 séquences**, répètent un état de parcours. Pour celles-ci, `ticks_cycle` donne la période du cycle et `entree_cycle_rom` son adresse de détection. Cette adresse tient compte de la commande mémorisée, du programme et de la note courante. Elle peut se trouver après la cible du premier `GOTO`. Les mesures sont exprimées en ticks de séquence. La conversion en durée réelle dépend du tempo et de la lecture par le moteur. [Parcours de commandes](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/m4a_1.s#L1166-L1223) · [Table des attentes](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/m4a.c#L210-L218)

Par exemple, la musique du printemps (`1`) comporte cinq pistes qui reviennent toutes sur un cycle de **2 016 ticks**. L’ambiance de pluie (`10`) boucle sur quatre pistes. L’ouverture d’une porte (`156`) comporte une seule piste finie. [Pistes A4NE](../ressources/donnees/audio/A4NE/Pistes-A4NE.csv)

Les instruments se retrouvent par `banque_rom` et `programme`. `parametre_04` garde le mot d’origine. Selon le type de voix, ce mot désigne un échantillon PCM, une onde CGB, une sous-table de percussion ou un paramètre de synthèse. Pour une percussion, chaque paire de `percussions_programme_note` indique le programme `p` et la note `n`. L’entrée jouée est à `cible_rom + 12 × n`. L’entrée `10` de la banque de musique pointe vers le programme `92` de la banque d’effets. Le disque `26` utilise les notes `39` à `42`, qui sélectionnent donc les entrées `131` à `134`. La banque d’effets conserve ces entrées au-delà de ses 128 programmes directs. [Structure ToneData](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/m4a.h#L79-L101) · [Indexation par note](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/m4a_1.s#L1584-L1615)

Sur les 106 PCM, **27** portent un marqueur de boucle. Le moteur lit les échantillons depuis `donnees_rom` et revient de la fin à `position_boucle_rom`, qui est un indice dans le PCM. Les boucles d’échantillons et les cycles de pistes décrivent deux niveaux du lecteur. [Structure WaveData](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/m4a.h#L69-L75) · [Lecture et bouclage du PCM](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/m4a_1.s#L222-L242)

## Comparaison USA et Europe

La table A4NP est à `0x13AC48`. Les offsets audio homologues sont décalés de `0x58` en Europe. Le contrôle a comparé **1 516 368 octets**, de `0x139D60` à `0x2AC0B0` exclu dans A4NE et sur la plage correspondante d’A4NP. Les octets concordent après correction des **2 304 pointeurs ROM** des tables, en-têtes, instruments et commandes de pistes. Les empreintes des PCM et des ondes CGB concordent également par entrée. Un second contrôle a recoupé la partie entre la séquence vide et le dernier en-tête avec les sources assembleur. [Données PCM natives](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/sound_data.s) · [Séquences natives](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/sound/songs.inc)

## Reproduire l’export

Le script vérifie le code et le SHA-1 de la ROM, puis écrit sept CSV dans un nouveau dossier. Le fichier de constantes est facultatif. Le fournir permet de reproduire les noms et familles des CSV publiés. [Éditions et empreintes](versions.md)

```sh
mkdir -p exports
curl -fsSL https://raw.githubusercontent.com/Wokann/fomt/9f2f03c775d64270a95250b8c03e6742219fda21/include/fomt_constants.mary.h \
  -o exports/fomt_constants.mary.h
python3 outils/audio/exporter_audio.py roms/A4NE.gba exports/audio-a4ne \
  --constantes exports/fomt_constants.mary.h
python3 outils/audio/exporter_audio.py roms/A4NP.gba exports/audio-a4np \
  --constantes exports/fomt_constants.mary.h
```

Ajouter `--binaires` pour écrire les pistes, les PCM et les ondes CGB sous `binaires/`. Les fichiers de piste couvrent leur plage jusqu’au début de la piste suivante ou jusqu’à l’en-tête. Ils conservent le remplissage éventuel et les pointeurs GBA d’origine. Les fichiers PCM et CGB contiennent les données brutes. Le rendu de séquences complètes en audio écoutable et la validation du rendu dans mGBA restent à faire.
