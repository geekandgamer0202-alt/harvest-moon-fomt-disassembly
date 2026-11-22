# Europe A4NP · parcours de vérification

Le jeu a été vérifié en anglais dans mGBA Qt 0.10.5 sur [A4NP révision 0](README.md#préparation). Les essais ci-dessous partent d’une nouvelle partie. Les touches correspondent à la manette GBA.

## Premier jour à la ferme

| Essai | Procédure et résultat observé |
| --- | --- |
| Début jouable | Valider le nom, l’anniversaire, la ferme et le chien, puis avancer l’introduction. Le lundi 2 printemps, an 1, la partie commence à 6 h avec 500 G. Le sac a trois emplacements d’objet et trois d’outil. |
| Prendre et ranger un miel | Sortir et terminer les présentations de la ferme. Faire face à l’arbre et appuyer sur A. Le miel apparaît en main. B le range. Maintenir L et appuyer sur A pour le reprendre. |
| Donner le miel à Rick | Prendre la route du village et terminer sa présentation. Lui faire face avec le miel en main et appuyer sur A. À la fermeture du dialogue, la main est vide, le solde reste à 500 G et l’octet d’affinité de Rick passe de 50 à 59. |
| Expédier un autre miel | Repartir d’un état antérieur au don. Sur la case immédiatement au sud de la caisse, faire face à la caisse et appuyer sur A, miel en main. Attendre Zack vers 17 h. Le solde passe de 500 à 550 G. Dans un essai décentré, la main s’est vidée et le solde est resté à 500 G. |
| Labourer et arroser | Avec la houe équipée, appuyer sur B devant une case de terre vide. Sélectionner l’arrosoir avec L+B et utiliser B face à la mare. La réserve passe de 0 à 30. Arroser la case labourée assombrit celle-ci et ramène la réserve à 29. |
| Acheter et semer | Dans le supermarché, ouvert le lundi à 11 h 10 dans cet essai, acheter un sachet de graines de navet pour 120 G. Dans la partie de départ, le solde passe de 500 à 380 G. Sélectionner le sachet avec L+B puis B face à la case labourée. Les graines deviennent visibles et le sachet est consommé. |
| Sauvegarde du jeu | Ouvrir le journal avec Start, choisir la sauvegarde et le premier emplacement. Quitter mGBA, relancer la ROM sans charger d’état, puis choisir la reprise et le premier emplacement. La sauvegarde de test fait 32 Kio et revient dans la maison à 6 h. |

L’essai de culture s’arrête au semis. Pour contrôler les mesures d’or et d’inventaire, enregistrer un état local avant et après chaque action et les passer à `inspecter_etat.py`. L’or est à `0x02004080`, les quatre octets de la main à `0x02004204`, une partie du sac à `0x02004214` et l’octet d’affinité de Rick à `0x02004338`. Dans l’essai de collecte, la main est passée de `05 00 FF FF` à `00 00 29 00`, puis est revenue aux octets de départ après le rangement. [Cartographie mémoire A4NP](https://github.com/khumam/gba-duo-companions/blob/main/harvest-moon-fomt-companion/NOTES.md)

## Prototype français externe

Les vérifications ont utilisé les patchs BPS A4NP 0.1 et 0.2. Pour reproduire avec une copie du patch, le charger après la ROM dans **File → Load patch…**, ou lancer cette commande en remplaçant les chemins. [Chargement des patchs dans mGBA Qt](https://github.com/mgba-emu/mgba/blob/0.10.5/src/platform/qt/Window.cpp#L462)

```sh
mgba-qt -p exports/mgba/Harvest-Moon-A4NP-FR-0.2.bps roms/jeu-a4np.gba
```

- **0.1.** Vérifier le menu de pause, le journal, le sac et le mémo. Sauver dans la première case, redémarrer et reprendre depuis cette case. Examiner le panneau de la caisse, puis ramasser et expédier un miel.
- **0.2.** En nouvelle partie, contrôler le joueur, la ferme et le chien. Le texte, les soulignements et le curseur s’alignent à 112 pixels du bord gauche. Tester la saisie jusqu’à douze caractères, le bouton **Fini** et la reprise des noms dans le récapitulatif.

Les essais concernent les écrans et libellés décrits pour ces versions du prototype. Les codes de jeu, empreintes et offsets s’appliquent à A4NP. L’inspecteur d’états vise la ROM d’origine.

## Interactions ciblées

| Test | Préparation | Observation |
| --- | --- | --- |
| Bibliothèque chez Ellen | Depuis le village en partie normale, entrer chez Ellen par A face au nord. Se placer en `(160, 68)` sur la carte 14, face au nord, puis appuyer sur A. | L’entrée exécute `0371`. La bibliothèque sélectionne `0191`, `CODE 0x082CEC88`. L’entrée répond `0191.00`. Une chaîne identique existe en `0181.00`. L’action testée résout `0191`. |
| Escalier de la réserve Aja | Une copie a modifié uniquement X et Y au format Q16 pour approcher la porte sur la carte 5, de `(329, 220)` à `(314, 458)`. Entrer par A dans la carte 33 et rejoindre l’escalier en `(122, 80)`. | A au bord de l’escalier conserve le contexte `0380`. Marcher vers le bas lance `0416` et entre dans la cave, carte 34. A du côté cave conserve `0416`. Marcher vers le haut lance `0422` pour le retour. Le script `0340` reste sans déclencheur identifié. |
| Téléviseur à 4 h 44 et 16 h 44 | Depuis la ferme, se placer face à la télévision. Dans une copie distincte par heure, remplacer les onze bits horaires du mot `0x020025EA` par `heure \| minute << 5`. Après chargement, appuyer sur A. Comparer à 4 h 43 et 4 h 45 sur le même état. | Les deux heures spéciales donnent le programme sans signal dans A4NP. Le code japonais sélectionne `1032` à ces heures. [Répartiteur japonais](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/jp/EventScript_TV_ChannelDispatcher.mary.c#L71-L75) |

Le menu d’affinité `1031` a été observé après une demande de script ajoutée en RAM. Son accès par les commandes normales reste indéterminé. Pour `1300`, la preuve est statique. Le préfixe de mise en place des acteurs est commun avec `0016`, qui poursuit la rencontre de Karen, tandis que `1300` se termine après ce préfixe. [Événement complet de Karen dans A4NP](https://github.com/Wokann/fomt/blob/9f2f03c775d64270a95250b8c03e6742219fda21/data/scripts/eu/EventScript_LoveEvent_Karen_01_BlackHeart_ReceiveWelcomeSeedGift.mary.c#L85-L101)
