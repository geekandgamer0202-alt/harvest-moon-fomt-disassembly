# Du bytecode aux routines natives FoMT

L’instruction VM `0x21` porte un identifiant 32 bits. Le répartiteur Thumb `ScriptEngine::OnCall` l’utilise comme index de table. Les **1 328 scripts** par édition contiennent **75 522 sites** pour **309 des 327 identifiants**. Chaque ligne indique le script, la position relative à sa première instruction et les offsets du site dans les deux ROM. Ces chiffres comptent les instructions stockées. Le déroulement du jeu décide lesquelles s’exécutent. [Exports USA et Europe](../../ressources/donnees/routines-natives/) · [Exécution de l’opcode](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_vm.cc#L540-L560)

| Table | Entrée A4NE | Table A4NE | Entrée A4NP | Table A4NP | Cases |
| --- | --- | --- | --- | --- | ---: |
| `OnCall` | `0x03F8DC` | `0x03F904` | `0x03F8F0` | `0x03F918` | 327 |
| `VarGet` | `0x04590C` | `0x045934` | `0x045920` | `0x045948` | 590 |
| `VarSet` | `0x048FFC` | `0x049034` | `0x049010` | `0x049048` | 562 |
| Bloc de notification après `VarSet` | `0x04DA2E` | `0x04DA5C` | `0x04DA42` | `0x04DA70` | 396 |

Les **1 875 pointeurs** des quatre tables concordent avec un décalage de `0x14` en Europe. Ils sont stockés avec le bit de poids faible à zéro. Le répartiteur exécute `mov pc, r0` en mode Thumb. Les CSV convertissent les pointeurs en offsets de fichier en soustrayant `0x08000000`. [Répartiteur OnCall](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L45-L70) · [Adresses et nombres de cases](../../ressources/donnees/routines-natives/Tables-natives-FoMT.json)

## Identifiants et symboles

Joindre `Sites-natifs-FoMT.csv` à `Liaisons-natives-FoMT.csv` par `id_natif`. Ce dernier contient l’offset de la case, la destination Thumb, le nombre de sites et les déclarations Mary. `symbole_natif` suit le code natif, dont chaque destination a été recoupée avec la table de branchements du désassemblage. `symbole_mary` conserve le libellé de l’en-tête Mary. Cinq ID d’initialisation partagent une destination. Les cases internes `0x000` et `0x001` portent le nom `NULL` dans l’en-tête. [Liaisons natives](../../ressources/donnees/routines-natives/Liaisons-natives-FoMT.csv) · [Déclarations Mary](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/eu/fomt_callables.mary.h)

Trois ID de menus de rangement ont des noms permutés entre ces sources. Le flux ROM et le `BL` dans chaque wrapper établissent la fonction appelée dans les deux éditions. [Wrappers des trois menus](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L4987-L5023)

| ID VM | Menu appelé dans la ROM | Nom dans l’en-tête Mary | Script | Cible du `BL` A4NE / A4NP |
| --- | --- | --- | --- | --- |
| `0x09C` | Coffre à outils (`OpenToolChest`) | `OpenShelf` | `0357` | `0x0135D8` / `0x0135EC` |
| `0x09D` | Réfrigérateur (`OpenRefrigerator`) | `OpenToolChest` | `0352` | `0x01366C` / `0x013680` |
| `0x09E` | Étagère (`OpenShelf`) | `OpenRefrigerator` | `0353` | `0x013700` / `0x013714` |

## Variables lues, écrites et notifiées

Les wrappers `0x03D` et `0x03E` appellent `VarGet` et `VarSet` par `BL`. La table de lecture couvre les ID `0` à `589`. La table d’écriture commence à `28`. Ses 562 cases comprennent 528 destinations dédiées et 34 entrées vers la branche générale après écriture. Les 28 ID plus bas vont également à cette branche, en dehors de la table d’écriture. L’accès à une branche dédiée peut dépendre de conditions du jeu. [Routines de lecture et d’écriture](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L2965-L3013) · [Index des variables](../../ressources/donnees/routines-natives/Variables-natives-FoMT.csv)

Le bloc après écriture relit la valeur. Il répartit les ID `70` à `465` dans la table de notification. Sur 396 cases, **309** mènent au traitement des changements d’état et **87** au retour direct. Le traitement compare les valeurs avant et après l’écriture. Après un changement, l’état `1` inscrit la variable dans la liste des événements actifs et peut réinitialiser le dialogue. Les états `0` ou `2` la retirent de la liste. Ce chemin explique pourquoi une réécriture d’état doit tenir compte de la notification en plus de la valeur stockée. [Notification et gestion des états](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L27752-L27776) · [Branches de notification](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/script_engine.cc#L28171-L28227)

L’index des variables recense **15 614 sites `VarGet`** et **1 850 sites `VarSet`**. Une lecture prend l’identifiant poussé juste avant l’appel. Une écriture à deux poussées littérales consécutives donne l’ID puis la valeur. Cette annotation locale couvre toutes les lectures et **1 636 écritures**. Les **214 autres écritures** gardent les champs littéraux vides. L’analyse se limite ici à la suite des instructions stockées, sans propagation de valeurs ni interprétation des branches. [Sites VarGet et VarSet](../../ressources/donnees/routines-natives/Acces-variables-FoMT.csv)

Dans `0657`, l’annonce de grossesse de Karen, les appels à `0x3458F0` et `0x345BAC` en A4NE demandent respectivement les valeurs `1` et `2` pour `VAR_KAREN_PREGNANCY_EVENT_STATE` (`198`). L’ID `198` mène à la destination d’écriture `0x04AA84`, puis au traitement de notification. [Contexte de la scène](vie-de-famille.md) · [Relevé des accès aux variables](../../ressources/donnees/routines-natives/Acces-variables-FoMT.csv)

## Reproduire l’export

L’outil vérifie les SHA-1 des deux ROM, compare les positions relatives des sites et leurs opérandes, puis recoupe les pointeurs d’`OnCall` avec les étiquettes du désassemblage de référence. Les sources Wokann fournissent les noms natifs, les noms et signatures Mary et l’énumération des variables. Les sorties comprennent quatre CSV et un résumé JSON.

```sh
mkdir -p references exports
git clone https://github.com/Wokann/fomt.git references/fomt
git -C references/fomt checkout --detach 9f2f03c775d64270a95250b8c03e6742219fda21
python3 outils/evenements/exporter_routines_natives.py \
  roms/A4NE.gba roms/A4NP.gba references/fomt exports/routines-natives
```
