# Catalogues de boutiques A4NE

`Catalogues-boutiques-A4NE.csv` relève **113 entrées physiques dans 12 catalogues** de *Harvest Moon: Friends of Mineral Town* USA, `A4NE` révision 0. Les offsets du tableau sont relatifs au début du fichier `.gba`. La référence complète a pour SHA-1 `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963`. [Identification des éditions](versions.md)

| Boutique | Catalogue | Symbole | Offset ROM | Entrées × octets |
| --- | --- | --- | ---: | ---: |
| Supermarché | `semences` | `gSupermarketCropSeedCatalog` | `0x0FDDD8` | 13 × 8 |
| Supermarché | `epicerie` | `gSupermarketFoodCatalog` | `0x0FDFA4` | 8 × 8 |
| Clinique | `medicaments` | `gClinicCatalog` | `0x0FE050` | 4 × 8 |
| Won | `etale` | `gWonShopCatalog` | `0x0FE484` | 10 × 8 |
| Domaine viticole Aja | `vins` | `gWineryShopCatalog` | `0x0FE740` | 2 × 8 |
| Van | `marchand_special` | `gSpecialMerchantShopCatalog` | `0x0FE8FC` | 15 × 8 |
| Ferme avicole | `volailles` | `gPoultryShopCatalog` | `0x0FD988` | 5 × 20 |
| Auberge | `menu_auberge` | `gInnShopMenu` | `0x0FE2D8` | 9 × 28 |
| Café de la plage | `menu_cafe` | `gBeachCafeShopMenu` | `0x0FEB60` | 5 × 28 |
| Forge | `forge` | `gBlacksmithCatalog` | `0x0FED8C` | 11 × 20 |
| Charpentier | `charpente` | `gCarpenterCatalog` | `0x0FF6A8` | 20 × 20 |
| Ranch Yodel | `betail` | `gLivestockShopCatalog` | `0x0FFB90` | 11 × 20 |

Les blocs par commerce sont documentés dans la cartographie US. Les structures des scènes distinguent les champs des fiches de vente, de restauration et de service. Les entrées sont lues sous forme de mots de 32 bits en ordre petit-boutiste. Chaque plage du tableau est vérifiée par SHA-256 avant décodage. Les suites de prix, les modes et les pointeurs vers les libellés permettent de retrouver les tables à l’intérieur des blocs mêlant données et textes. [Cartographie ROM US](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/TEXT_ROM_LAYOUT.md#L5695-L5713) · [Format du supermarché](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/scene_supermarket.hh#L92-L101) · [Format de la charpente](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/scene_carpenter_shop.hh#L92-L101)

## Lire le CSV

- La clé `(catalogue, index)` identifie une ligne. `offset_rom`, `taille_octets` et `octets_rom` permettent de retrouver chaque enregistrement et de vérifier tous ses champs, y compris les octets dont le sens reste à établir.
- `espace_identifiant` désigne le rôle du nombre dans la scène qui le lit. `famille_objet` et `id_objet` donnent une jointure avec la table d’objets lorsque le consommateur confirme ce lien. `nom_objet` vient de cette table. Won utilise ainsi des articles pour les entrées 0 à 2, puis des outils pour les semences. Les restaurants conservent leur identifiant `food_ui_id`. Le tourne-disque de Van possède un code spécial dans son catalogue. [Routage du catalogue de Won](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_won_shop.cc#L51-L99) · [Catalogue de Van](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_special_merchant_shop.cc#L1516-L1533)
- `prix_or_rom` et `bois_rom` sont les valeurs stockées. `operation` indique le rôle de l’entrée. Les tarifs de revente des animaux dépendent de l’animal choisi. Les zéros des lignes de revente, des fiches d’animaux, des sous-menus et de la sentinelle gardent leur fonction native. [Calcul du prix à la ferme avicole](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_poultry_farm_shop.cc#L5632-L5682) · [Fiches du ranch Yodel](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_yodel_ranch_shop.cc#L1198-L1228)
- `offset_libelle_rom` et `offset_detail_rom` pointent vers les chaînes natives. `libelle_rom` reproduit la chaîne principale lorsqu’une entrée en contient une. En restauration, `drapeau_description_rom` sélectionne une description dédiée et `endurance_rom` conserve le champ signé. Les champs `champ_14_rom` et `champ_18_rom` gardent leur type natif sans supposer leur rôle. [Format des menus de restauration](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/include/scene_inn_shop.hh#L98-L109)

## Disponibilité

`conditions_verifiees` complète les valeurs du catalogue. Le jeu filtre les semences de la manière suivante. [Sélection des semences en jeu](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_supermarket.cc#L83-L475)

| Saison | Entrées de base | Déblocage supplémentaire |
| --- | --- | --- |
| Printemps | Navet, pomme de terre, concombre, herbe | Fraise après 100 expéditions de chacun des trois légumes de base |
| Été | Tomate, maïs, oignon, herbe | Citrouille après 100 expéditions de chacun des trois légumes de base |
| Automne | Aubergine, carotte, patate douce, herbe | Épinard après 100 expéditions de chacun des trois légumes de base |
| Hiver | Aucun sachet dans ce menu | |

Pour les trois déblocages, la scène vérifie aussi que chacun des produits est affiché dans le suivi des expéditions. Le bloc d’épicerie se termine par une entrée nulle conservée dans l’export. Le catalogue de Van entre en jeu lorsque son comptoir est accessible à l’étage de l’auberge. La fiche du panier-repas de l’auberge indique une vente l’après-midi. Les coûts en minerai de la forge viennent des libellés d’Adamantite et d’Orichalc. [Épicerie](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_supermarket.cc#L2426-L2438) · [Accès au comptoir de Van](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/us/EventScript_NPCEvent_Van_ShopCounter.mary.c#L15-L50) · [Commandes de la forge](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/src/scene_blacksmith_shop.cc#L3102-L3115)

Les conditions vides indiquent que la disponibilité n’est pas établie par cet export. Les horaires détaillés des comptoirs, les règles de vente des animaux, les menus d’amélioration, les commandes de Télé-Achat et les actions chiffrées dans les scripts font partie d’autres chemins d’exécution.

`exporter_boutiques(rom, dossier, noms_objets)` prend la ROM en octets, un `Path` vers un dossier existant et un dictionnaire de noms indexé par `(famille, id_entier)`. Il crée le CSV en UTF-8, conserve les autres fichiers et refuse d’écraser le CSV. Il renvoie `(nombre_catalogues, nombre_lignes)`. [Extracteur](../outils/economie/boutiques.py)
