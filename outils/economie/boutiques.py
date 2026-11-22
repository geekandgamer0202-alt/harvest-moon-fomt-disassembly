"""Extrait les catalogues natifs de boutiques de la ROM A4NE révision 0."""

import csv
from dataclasses import dataclass
from hashlib import sha256
from struct import Struct


BASE_GBA = 0x08000000
TAILLE_ROM = 0x800000
FICHIER_BOUTIQUES = 'Catalogues-boutiques-A4NE.csv'

PAIRE = Struct('<II')
COMMERCE = Struct('<5I')
RESTAURATION = Struct('<IIIIiiI')


@dataclass(frozen=True)
class Catalogue:
    boutique: str
    cle: str
    symbole: str
    debut: int
    nombre: int
    format: Struct
    empreinte: str


CATALOGUES = (
    Catalogue('Supermarché', 'semences', 'gSupermarketCropSeedCatalog', 0x0FDDD8, 13, PAIRE,
              'e49f050092b3c3ea60a094d8606186b8f89edc637e4b03d66daf251a0fb00f9b'),
    Catalogue('Supermarché', 'epicerie', 'gSupermarketFoodCatalog', 0x0FDFA4, 8, PAIRE,
              'cdfba515e1d95cbf8c8ab5ea62b5c1485d7967ce1e0160df3ec319e447607f59'),
    Catalogue('Clinique', 'medicaments', 'gClinicCatalog', 0x0FE050, 4, PAIRE,
              'abf253347220d5220e2591fc3507201ce20a51c5e4e24129ec573d35060ca6c5'),
    Catalogue('Won', 'etale', 'gWonShopCatalog', 0x0FE484, 10, PAIRE,
              '5fd0c59a81e994e6d8c21a605a744bf2c15185b62594428c30a5fab5f06305d3'),
    Catalogue('Domaine viticole Aja', 'vins', 'gWineryShopCatalog', 0x0FE740, 2, PAIRE,
              '916dada954239c3a3b0f1e8fec4ca475af59e2e1a6934ec11d927e5dcddb04ef'),
    Catalogue('Van', 'marchand_special', 'gSpecialMerchantShopCatalog', 0x0FE8FC, 15, PAIRE,
              'f4d1a86911210d25e9860852590d0e08d86b26cbebca9ccb1cf94594321625b4'),
    Catalogue('Ferme avicole', 'volailles', 'gPoultryShopCatalog', 0x0FD988, 5, COMMERCE,
              'ca4bb453b7243076822d92ebdcf0ba27291af9e18c0cbeb6c7c639a3bee25a1e'),
    Catalogue('Auberge', 'menu_auberge', 'gInnShopMenu', 0x0FE2D8, 9, RESTAURATION,
              'e1b637294dc4a844414a475d59aa1c6ef483a01d85946432cddfe06cc42b4226'),
    Catalogue('Café de la plage', 'menu_cafe', 'gBeachCafeShopMenu', 0x0FEB60, 5, RESTAURATION,
              '8b12400b90735a01f2a6416b493acfbdca9d2d13ad9fa184d0908d834ff9833b'),
    Catalogue('Forge', 'forge', 'gBlacksmithCatalog', 0x0FED8C, 11, COMMERCE,
              'a4d629434c64e8c7b37927745c4722b463c738f513208aa4143fd12bba092489'),
    Catalogue('Charpentier', 'charpente', 'gCarpenterCatalog', 0x0FF6A8, 20, COMMERCE,
              'de21958021ad1a4b25ff3aa05c0f7fb3762e3b7043f54e15b725ad7dd0037704'),
    Catalogue('Ranch Yodel', 'betail', 'gLivestockShopCatalog', 0x0FFB90, 11, COMMERCE,
              '414a469fcb4b099813d4cca11def907fe93f2512887265753be881626fba8351'),
)

CONDITIONS_SEMENCES = (
    'Printemps', 'Printemps', 'Printemps',
    'Printemps. Expédier au moins 100 navets, 100 pommes de terre et 100 concombres.',
    'Été', 'Été', 'Été',
    'Été. Expédier au moins 100 tomates, 100 maïs et 100 oignons.',
    'Automne', 'Automne', 'Automne',
    'Automne. Expédier au moins 100 aubergines, 100 carottes et 100 patates douces.',
    'Printemps, été et automne',
)

ENTETES = (
    'boutique', 'catalogue', 'symbole', 'index', 'offset_rom', 'taille_octets',
    'espace_identifiant', 'identifiant_local', 'famille_objet', 'id_objet', 'nom_objet',
    'operation', 'prix_or_rom', 'bois_rom', 'conditions_verifiees',
    'libelle_rom', 'offset_libelle_rom', 'offset_detail_rom',
    'mode_rom', 'drapeau_description_rom', 'endurance_rom', 'champ_14_rom',
    'champ_18_rom', 'octets_rom',
)

LIMITES_OBJETS = {'outil': 81, 'aliment': 171, 'article': 95}


def hex_rom(offset):
    return f'0x{offset:06X}'


def texte_rom(rom, adresse):
    if not adresse:
        return '', None
    offset = adresse - BASE_GBA
    if not 0 <= offset < len(rom):
        raise ValueError(f'Pointeur de texte hors ROM : 0x{adresse:08X}.')
    fin = rom.find(b'\0', offset, min(len(rom), offset + 0x400))
    if fin == -1:
        raise ValueError(f'Texte natif sans terminaison à {hex_rom(offset)}.')
    return hex_rom(offset), rom[offset:fin]


def lier_objet(ligne, famille, identifiant):
    if not 0 <= identifiant < LIMITES_OBJETS[famille]:
        raise ValueError(f'Identifiant {famille} hors table : 0x{identifiant:X}.')
    ligne['famille_objet'] = famille
    ligne['id_objet'] = f'0x{identifiant:02X}'


def decoder_paire(cle, index, valeurs, ligne):
    identifiant, prix = valeurs
    ligne.update(identifiant_local=f'0x{identifiant:02X}', prix_or_rom=prix, operation='achat')
    if cle == 'epicerie' and index == 7:
        if valeurs != (0, 0):
            raise ValueError('Sentinelle du supermarché non nulle.')
        ligne.update(espace_identifiant='sentinelle_catalogue', operation='sentinelle')
        return
    if cle == 'marchand_special':
        ligne['conditions_verifiees'] = ('Van à l’étage de l’auberge et joueur face à droite au comptoir. '
                                         'Certaines scènes en cours bloquent l’interaction.')
        if index == 10:
            ligne.update(espace_identifiant='code_marchand_special', operation='achat_tourne_disque')
            return
    if cle == 'semences':
        ligne['conditions_verifiees'] = CONDITIONS_SEMENCES[index]
    if cle == 'semences' or (cle == 'etale' and index >= 3):
        famille = 'outil'
    elif cle in ('etale', 'marchand_special'):
        famille = 'article'
    else:
        famille = 'aliment'
    ligne['espace_identifiant'] = f'item_{famille}'
    lier_objet(ligne, famille, identifiant)


def decoder_restaurant(cle, index, valeurs, rom, ligne):
    identifiant, prix, detail, description, endurance, champ_14, champ_18 = valeurs
    ligne.update(espace_identifiant='food_ui_id', identifiant_local=f'0x{identifiant:02X}',
                 operation='consommation', prix_or_rom=prix, offset_detail_rom=texte_rom(rom, detail)[0],
                 drapeau_description_rom=description, endurance_rom=endurance,
                 champ_14_rom=champ_14, champ_18_rom=champ_18)
    if cle == 'menu_auberge' and index == 1:
        ligne['conditions_verifiees'] = 'Le libellé du jeu indique une vente l’après-midi.'


def decoder_commerce(cle, index, valeurs, rom, ligne):
    if cle == 'charpente':
        libelle, prix, bois, identifiant, detail = valeurs
        operation = 'travaux'
        if index < 2:
            operation = 'achat_bois'
        elif 8 <= index <= 10:
            operation = 'sous_menu'
        ligne.update(espace_identifiant='option_charpentier', operation=operation, bois_rom=bois)
    elif cle == 'forge':
        identifiant, libelle, prix, mode, detail = valeurs
        ligne.update(espace_identifiant='selection_forge', mode_rom=mode,
                     operation={0: 'sous_menu_amelioration', 1: 'achat',
                                2: 'commande_bijou', 3: 'commande_machine'}[mode])
        if mode == 1:
            lier_objet(ligne, 'outil', identifiant)
        elif mode == 2:
            lier_objet(ligne, 'article', identifiant)
            ligne['conditions_verifiees'] = 'Requiert de l’Orichalc.'
        elif mode == 3:
            ligne['conditions_verifiees'] = 'Requiert de l’Adamantite.'
    else:
        identifiant, libelle, prix, detail, mode = valeurs
        ligne.update(espace_identifiant=f'code_{cle}', mode_rom=mode)
        if index == 0:
            ligne['operation'] = 'achat'
            lier_objet(ligne, 'article', identifiant)
        elif (cle == 'volailles' and index == 1) or (cle == 'betail' and mode == 2):
            ligne['operation'] = 'achat'
            lier_objet(ligne, 'outil', identifiant)
        elif mode in (1, 2):
            ligne['operation'] = 'achat_animal'
        elif mode == 3:
            ligne['operation'] = 'vente_animal_prix_variable'
        else:
            ligne['operation'] = 'fiche_animal'
    ligne.update(identifiant_local=f'0x{identifiant:02X}', prix_or_rom=prix)
    ligne['offset_libelle_rom'], libelle_brut = texte_rom(rom, libelle)
    if libelle_brut:
        ligne['libelle_rom'] = libelle_brut.decode('ascii')
    ligne['offset_detail_rom'] = texte_rom(rom, detail)[0]


def lignes_catalogue(rom, catalogue):
    largeur = catalogue.format.size
    fin = catalogue.debut + largeur * catalogue.nombre
    table = rom[catalogue.debut:fin]
    if sha256(table).hexdigest() != catalogue.empreinte:
        raise ValueError(f'Empreinte du catalogue {catalogue.symbole} différente à {hex_rom(catalogue.debut)}.')

    for index, valeurs in enumerate(catalogue.format.iter_unpack(table)):
        debut = catalogue.debut + index * largeur
        ligne = dict(boutique=catalogue.boutique, catalogue=catalogue.cle, symbole=catalogue.symbole,
                     index=index, offset_rom=hex_rom(debut), taille_octets=largeur,
                     octets_rom=rom[debut:debut + largeur].hex().upper())
        if catalogue.format is PAIRE:
            decoder_paire(catalogue.cle, index, valeurs, ligne)
        elif catalogue.format is RESTAURATION:
            decoder_restaurant(catalogue.cle, index, valeurs, rom, ligne)
        else:
            decoder_commerce(catalogue.cle, index, valeurs, rom, ligne)
        yield ligne


def exporter_boutiques(rom, dossier, noms_objets):
    """Écrit un CSV UTF-8 et renvoie (nombre de catalogues, nombre de lignes)."""
    if len(rom) != TAILLE_ROM or rom[0xAC:0xB0] != b'A4NE' or rom[0xBC] != 0:
        raise ValueError('Cette extraction requiert FoMT USA A4NE révision 0.')

    lignes = [ligne for catalogue in CATALOGUES for ligne in lignes_catalogue(rom, catalogue)]
    for ligne in lignes:
        famille = ligne.get('famille_objet')
        if famille:
            identifiant = int(ligne['id_objet'], 16)
            try:
                ligne['nom_objet'] = noms_objets[famille, identifiant]
            except KeyError as erreur:
                raise ValueError(f'Objet absent du catalogue des noms : {famille} 0x{identifiant:02X}.') from erreur
    with (dossier / FICHIER_BOUTIQUES).open('x', encoding='utf-8', newline='') as fichier:
        table = csv.DictWriter(fichier, ENTETES, lineterminator='\n')
        table.writeheader()
        table.writerows(lignes)
    return len(CATALOGUES), len(lignes)
