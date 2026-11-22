# Cultures, cuisine et pêche A4NE

Les dix CSV sont lus dans la ROM USA A4NE de référence. Les valeurs exportées gardent leur offset et leur identifiant dans la table d’origine. Les noms d’objets proviennent des fiches natives déjà vérifiées. [Exports](../ressources/donnees/activites/A4NE/) · [Fiches des objets](economie.md) · [Empreinte de la ROM](versions.md)

## Cultures et météo

| Fichier | Table A4NE | Contenu |
| --- | --- | --- |
| [Parcelles](../ressources/donnees/activites/A4NE/Parcelles-A4NE.csv) | `0x0E93F8` | 39 types de parcelles, pointeurs de rendu, variantes, identifiants de semences et de récoltes |
| [Croissance](../ressources/donnees/activites/A4NE/Croissance-A4NE.csv) | `0x0E8D14` | 21 types avec 21 entrées de compteur de croissance chacun |
| [Météo des parcelles](../ressources/donnees/activites/A4NE/Meteo-parcelles-A4NE.csv) | `0x0E8CC4` | 8 lignes ordinaires par saison et code météo, puis les cas spéciaux `3` et `4` |

La matrice associe un compteur de croissance à un stade. Pour les cultures ordinaires, la mise à jour journalière avance le compteur lorsque la parcelle est arrosée. Le stade `5` correspond à la récolte. Le navet, issu de `Turnip Seeds` (`outil 0x32`), l’atteint au compteur `4`. Le concombre l’atteint à `9` et sa récolte remet le compteur à `4`, au stade `2`. Les valeurs de repousse et les liens vers les semences viennent des fonctions qui lisent ces tables. Les deux types de Magic Grass partagent le même sachet, et l’herbe suit sa propre branche de croissance hors hiver. [Mise à jour journalière et récolte](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/field.cc#L389-L475) · [Conversion des semences](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/player_actor.cc#L242-L273)

Les valeurs météo sont les huit octets de chaque règle du champ. Le moteur les compare à un tirage sur huit bits, selon l’état de la parcelle. Les règles de changement de saison et de mise à jour d’une parcelle sont distinctes de la matrice de croissance. [Règles du champ](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/field.cc#L580-L779) · [Définition des tables](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/field_data.cc)

## Cuisine

- [Recettes](../ressources/donnees/activites/A4NE/Recettes-A4NE.csv) contient **117 définitions** pour **108 codes de résultat** à partir de `0x10110C`. Un résultat de `1` à `0xAB` donne l’aliment `code − 1`. À partir de `0xAC`, il donne l’article `code − 0xAC`. Le jeu peut associer plusieurs définitions au même résultat et parcourt les lignes dans l’ordre ROM. La sentinelle de 20 octets à `0x101A30` a été vérifiée.
- [Listes des recettes](../ressources/donnees/activites/A4NE/Listes-recettes-A4NE.csv) contient **267 listes** identifiées par le champ pointeur et leur adresse, avec **1 992 entrées** dont les terminaisons nulles. `08` contient les ingrédients et leurs codes spéciaux. `0C` donne les ingrédients complémentaires et leurs ajustements signés. `10` donne les masques d’ustensiles et leurs ajustements signés. Plusieurs recettes peuvent référencer la même adresse, et certaines listes partagent une portion en ROM.
- [Cuisson échouée](../ressources/donnees/activites/A4NE/Cuisson-echouee-A4NE.csv) tire ses **9 règles** de `0x1010E8`. La scène prend la première ligne dont le masque correspond aux ustensiles ou la dernière ligne par défaut.

La liste `08` conserve les codes spéciaux et le bit `0x8000` utilisés par le moteur pour comparer des ingrédients. Par exemple `0x0200` désigne le groupe des œufs et `0x0203` celui des mayonnaises. Les colonnes `champ_02_u16`, `champ_04_i16` et `masque_06` gardent les valeurs physiques. La signification complète des champs scalaires et le calcul final pour chaque combinaison restent à établir. [Format natif](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/cooking_recipe.hh) · [Évaluation des listes](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/cooking_recipe.cc#L2816-L3250) · [Sélection du résultat d’échec](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_cooking.cc#L15833-L15882)

## Pêche

| Fichier | Table A4NE | Contenu |
| --- | --- | --- |
| [Zones](../ressources/donnees/activites/A4NE/Zones-peche-A4NE.csv) | `0x10563C` | 8 rectangles, 7 zones, coordonnées locales en tuiles et bornes incluses |
| [Paramètres](../ressources/donnees/activites/A4NE/Parametres-peche-A4NE.csv) | `0x104E74`, `0x104EAC` | 28 délais de touche et 35 poids de catégories |
| [Prises](../ressources/donnees/activites/A4NE/Prises-A4NE.csv) | `0x104ED0` | 59 prises, tailles limites, noms des records à `0x103A18` et identifiants d’article à `0x104E54` |
| [Conditions de prise](../ressources/donnees/activites/A4NE/Conditions-peche-A4NE.csv) | Configuration `+0x02` de chaque prise | 1 652 entrées, une par prise, saison et zone |

Le premier tirage répartit les prises entre aucune prise, message en bouteille, déchets, poissons ordinaires et prises rares. Les poids d’une zone totalisent 100. La sélection filtre ensuite la catégorie par saison, zone et charge de canne. Une valeur nulle exclut la prise. `abs(niveau) − 1` donne la charge indiquée. La valeur calculée `7` accepte toute charge. La charge mythique `6` accepte les niveaux non nuls. Si les deux groupes de signe sont disponibles, le moteur tire le groupe positif à 70 et le négatif à 30 sur 100. Ces poids décrivent les tirages successifs. Le moteur peut appliquer des conditions liées à la sauvegarde après le tirage. [Choix de la zone](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/fishing_area.cc) · [Sélecteur de prise](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/fishing.cc#L501-L1225)

Les noms affichés sont lus dans la ROM. Deux records partagent le libellé `Silver Carp`. La colonne `id_article_table` décrit la table physique. La prise `2` suit un traitement dédié de baie de puissance. Pour les poissons qui deviennent des aliments d’inventaire, le moteur choisit l’ID `0xA0`, `0xA1` ou `0xA2` selon la taille tirée, avec seuils `25` et `49`. [Table des libellés](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/fishing_results_data.cc#L77-L150) · [Traitement des récompenses](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/fishing.cc#L1117-L1228)

## Reproduire l’export

La commande vérifie la ROM de référence et écrit les dix CSV dans un nouveau dossier.

```sh
python3 outils/jeu/exporter_activites.py roms/A4NE.gba exports/activites-a4ne
```
