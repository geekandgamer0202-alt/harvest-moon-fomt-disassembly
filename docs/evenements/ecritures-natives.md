# Écritures natives et notifications de `VarSet`

**30 146 couples `VarSet`–`VarGet`** ont terminé sur trois états mGBA 0.10.5 des éditions USA A4NE et Europe A4NP. Le sondage couvre les **590 ID** et répète dans chaque état les **911 couples ID–valeur littérale** distincts retrouvés dans le bytecode. Il relève séparément les écritures directes et celles du bloc qui relit la valeur et traite la notification. [CSV des essais](../../ressources/donnees/ecritures-natives/) · [Arguments du bytecode](ecritures-variables.md)

| Observation dans les trois états d’origine | ID concernés |
| --- | ---: |
| Au moins un essai change un octet de l’image pendant l’écriture directe | 527 |
| Au moins un essai change un octet hors de l’image pendant l’écriture directe | 3 |
| Au moins un essai change un octet de l’image pendant la notification | 309 |
| Au moins un essai change un octet hors de l’image pendant la notification | 309 |

Le sondage couvre une partie neuve en USA, la scène d’annonce de Karen en USA et le début jouable en Europe. Les écritures modifient une copie privée de l’EWRAM et de l’IWRAM. Chaque appel repart de l’état d’origine, sauf dans les séquences qui suivent le registre. Les 17 arguments communs couvrent zéro, des valeurs négatives et plusieurs limites en puissance de deux. L’outil ajoute les littéraux des scripts et la valeur courante. Les valeurs calculées par les scripts dépendent de leurs propres conditions d’exécution. [Empreintes des états](../../ressources/donnees/ecritures-natives/Contextes-VarSet-FoMT.csv) · [Entrées et tables Thumb](routines-natives.md#variables-lues-écrites-et-notifiées)

## Écritures directes

| ID | Variable | Écriture observée |
| ---: | --- | --- |
| 40 | Réserve de bois | Les dix bits de poids faible à `0x0024` changent. Les arguments `1023` et `65535` donnent `999`, et `-1` donne `0` dans les trois états. |
| 76 | État du mariage avec Karen | Dans les parties neuves, `1` écrit l’ID à `0x2158` et `2` modifie `0x1ECE`. L’écriture de `1` provoque en plus une inscription dans le registre. |
| 198 | État de grossesse de Karen | Stocke `argument & 3` dans les bits 5 et 6 de `0x2168`. L’écriture directe préserve les autres bits. |
| 199 | État de grossesse de Mary | Les deux bits à `0x2168` et `0x2169` changent indépendamment. La valeur `1` change le bit 7 du premier octet et la valeur `2` le bit 0 du second. |
| 580 | Argument partagé entre scripts | Stocke `argument & 3` dans les bits 0 et 1 de `0x21CA`. |

Les trois ID qui changent aussi des octets hors de l’image pendant l’écriture directe sont `30` et `31`, liés à la chaussette, et `403`, lié à l’inscription du chien au concours de frisbee. Les adresses dans l’image se convertissent en offsets `.sav` en ajoutant `0x002C` ou `0x4018`. [Branches pour Karen et l’argument partagé](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L21753-L21768) · [Branche `580`](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L27614-L27630) · [Format SRAM](../sauvegarde.md)

### Drapeau de marche de l’enfant

Parmi les 528 ID dotés d’une branche d’écriture dédiée, seul l’ID `47` laisse l’image intacte dans tout le sondage principal. Les trois états d’origine n’ont pas d’enfant. Dans **18 essais ciblés**, la présence a été préparée au bit 1 de `0x1CD7` et la marche au bit 0 de `0x1CFE`. Avec l’enfant présent et le drapeau à zéro, `VarSet(47, 1)` et `VarSet(47, -1)` mettent ce bit à `1`. L’argument `0` laisse le bit tel quel, y compris quand il vaut déjà `1`. [Essais ciblés](../../ressources/donnees/ecritures-natives/Marche-enfant-VarSet-FoMT.csv) · [Branche native](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L19606-L19633) · [Accès à la présence](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/npc_collection.cc#L2080-L2083)

## Registre des événements actifs

Le bloc de notification relit `VarGet`. Pour les ID pris en charge, il compare la valeur précédente à la valeur relue. Si elles diffèrent, la valeur `1` peut réinitialiser le dialogue de la scène et ajouter l’ID au registre, tandis que `0` et `2` le retirent s’il est présent. Le registre commence à `0x214C` avec un compteur `u32`, puis trois ID `u16` à `0x2150`. Il contient des ID de variable. Le premier `u16` après la structure alignée, à `0x2158`, contient l’événement romantique actif. [Bloc de notification](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L28171-L28227) · [Structure du registre](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/event_state.hh#L9-L52)

Pour Karen, le passage `0 → 1` inscrit `198`. Réécrire `1` laisse le registre intact, et `1 → 2` retire l’ID. L’essai réalisé à partir de l’annonce `0657` confirme la transition de fin de scène. Dans les deux états de partie neuve, inscrire successivement `198`, `197` et `199` remplit les trois places. L’écriture suivante passe `196` à l’état `1` alors que la liste reste pleine. Après libération d’une place et transition `196` de `1` à `2` puis de `2` à `1`, `196` entre dans le registre. Un retrait décale les ID suivants et peut laisser une valeur dans une case inactive. [Séquences mesurées](../../ressources/donnees/ecritures-natives/Registre-evenements-VarSet-FoMT.csv) · [Insertion et retrait natifs](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/event_state.cc#L21-L49)

## Lire les résultats et les reproduire

- `Essais-VarSet-FoMT.csv` donne l’argument et les retours `VarGet` avant et après chaque appel. Les colonnes `bits_image_modifies` contiennent des couples `offset/masque` séparés par `|`. Chaque masque est le XOR entre les octets au début et à la fin de la phase. Le nombre d’octets touchés inclut les écritures qui laissent la valeur identique.
- `Variables-ecrites-FoMT.csv` résume les essais et les changements par ID. Les types des branches viennent de l’index statique. `bloc_notification_atteint` dans le détail désigne l’entrée du bloc de relecture, y compris quand la branche retourne immédiatement.
- `Octets-ecrits-VarSet-FoMT.csv` regroupe les essais par ID, phase et octet de l’image. Son masque cumule les bits qui ont changé sur au moins un essai. Il dépend des états testés et complète les masques de lecture.
- `Registre-evenements-VarSet-FoMT.csv` conserve les ID logiquement actifs et les trois cases brutes après chaque écriture. `Marche-enfant-VarSet-FoMT.csv` donne les transitions préparées de l’ID `47`. Ces séquences sont indépendantes des 30 146 essais du sondage principal.

Les deux états de partie neuve ont **10 047** couples ID–argument en commun. Pour chacun de ceux dont `VarGet` renvoyait la même valeur au départ, sa valeur finale est identique. Les trois ID dont les valeurs initiales diffèrent gardent ces valeurs dans les essais comparables. Les traces décrivent les branches rencontrées sur les états et arguments testés. [Essais détaillés](../../ressources/donnees/ecritures-natives/Essais-VarSet-FoMT.csv)

```sh
python3 -m pip install unicorn==2.1.4
python3 outils/jeu/relever_ecritures.py \
  roms/A4NE.gba roms/A4NP.gba exports/ecritures-natives \
  etats/after-sleep-steady.state etats/karen-announcement.state etats/Harvest-Moon-Europe.ss1
```
