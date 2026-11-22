#!/usr/bin/env python3
"""Exporte les tables A4NE de culture, de cuisine et de pêche au format CSV."""

import argparse
from pathlib import Path
from struct import unpack_from
import sys
from tempfile import TemporaryDirectory


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'economie'))
from exporter_economie import BASE_GBA, charger_rom, ecrire_csv, hex_rom, lire_objets


SAISONS = ('printemps', 'été', 'automne', 'hiver')
SEMENCES = (*range(0x32, 0x41), 0x42, 0x43, 0x44, 0x44, 0x45, 0x41)
SAISON_CULTURE = (0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 0, 1, 2, 2, 0)
REPOUSSES = {2: (2, 4), 3: (3, 6), 5: (4, 6), 6: (4, 11), 9: (4, 15),
             10: (3, 6), 12: (2, 3), 14: (4, 5)}
GROUPES_INGREDIENTS = {0x200: 'œuf', 0x201: 'lait', 0x202: 'fromage', 0x203: 'mayonnaise'}


def code_objet(identifiant):
    return f'0x{identifiant:02X}'


def colonnes_objet(objet):
    if objet is None:
        return '', '', ''
    return objet.famille, code_objet(objet.identifiant), objet.nom


def exporter_cultures(rom, objets, dossier):
    croissance = []
    for culture in range(21):
        adresse = 0x0E8D14 + culture * 84
        croissance.append(unpack_from('<21I', rom, adresse))
    ecrire_csv(dossier / 'Croissance-A4NE.csv',
               ('type_parcelle', 'offset_rom', *(f'compteur_{i:02d}' for i in range(21))),
               ((i, hex_rom(0x0E8D14 + i * 84), *stades) for i, stades in enumerate(croissance)))

    parcelles = []
    for type_parcelle in range(39):
        adresse = 0x0E93F8 + type_parcelle * 12
        rendu, *variantes, resultat = unpack_from('<I6BH', rom, adresse)
        famille = 'aliment' if type_parcelle < 15 else 'article'
        produit = objets[famille, resultat] if resultat != 0xFF else None
        semence = objets['outil', SEMENCES[type_parcelle]] if type_parcelle < len(SEMENCES) else None
        saison = SAISONS[SAISON_CULTURE[type_parcelle]] if type_parcelle < 20 else ('hors hiver' if type_parcelle == 20 else '')
        maturite = croissance[type_parcelle].index(5) if type_parcelle < len(croissance) else ''
        stade_repousse, compteur_repousse = REPOUSSES.get(type_parcelle, ('', ''))
        parcelles.append((type_parcelle, hex_rom(adresse), hex_rom(rendu - BASE_GBA), *variantes,
                          code_objet(resultat), *colonnes_objet(produit),
                          code_objet(semence.identifiant) if semence else '', semence.nom if semence else '',
                          saison, maturite, stade_repousse, compteur_repousse))
    ecrire_csv(dossier / 'Parcelles-A4NE.csv',
               ('type_parcelle', 'offset_rom', 'rendu_offset_rom', 'variante_stade_2', 'variante_stade_3',
                'variante_stade_4', 'variante_stade_5', 'variante_stade_6', 'octet_reserve', 'resultat_brut',
                'famille_recolte', 'id_recolte', 'nom_recolte', 'id_semence', 'nom_semence',
                'saison_croissance', 'compteur_maturite', 'stade_repousse', 'compteur_repousse'), parcelles)

    meteo = []
    for i in range(10):
        adresse = 0x0E8CC4 + i * 8
        saison = SAISONS[i // 2] if i < 8 else ''
        code = ('autres codes ordinaires' if i % 2 == 0 else '0') if i < 8 else str(i - 5)
        meteo.append((i, hex_rom(adresse), saison, code, *rom[adresse:adresse + 8]))
    ecrire_csv(dossier / 'Meteo-parcelles-A4NE.csv',
               ('ligne', 'offset_rom', 'saison', 'code_meteo', *(f'octet_{i}' for i in range(8))), meteo)


def objet_cuisine(code, objets):
    if 1 <= code <= 0xAB:
        return objets['aliment', code - 1]
    if 0xAC <= code < 0xAC + 95:
        return objets['article', code - 0xAC]
    return None


def lire_liste_cuisine(rom, adresse, role, objets):
    taille = 2 if role == '08' else 4
    if not (0x101A44 <= adresse < 0x10363E and adresse % taille == 0):
        raise ValueError(f'Pointeur de liste de cuisine incohérent à {hex_rom(adresse)}')
    for index, courant in enumerate(range(adresse, 0x10363E - taille + 1, taille)):
        code, = unpack_from('<H', rom, courant)
        endurance, fatigue = unpack_from('<bb', rom, courant + 2) if taille == 4 else ('', '')
        groupe = GROUPES_INGREDIENTS.get(code, '') if role == '08' else ''
        objet = objet_cuisine(code & 0x0FFF, objets) if role in ('08', '0C') else None
        yield (role, hex_rom(adresse), index, hex_rom(courant), f'0x{code:04X}', groupe,
               *colonnes_objet(objet), endurance, fatigue)
        if not code:
            return
    raise ValueError(f'Liste de cuisine sans terminaison à {hex_rom(adresse)}')


def exporter_cuisine(rom, objets, dossier):
    definitions = []
    listes = set()
    for index in range(117):
        adresse = 0x10110C + index * 20
        resultat, champ_02, champ_04, masque, *pointeurs = unpack_from('<HHhHIII', rom, adresse)
        objet = objet_cuisine(resultat, objets)
        if objet is None:
            raise ValueError(f'Résultat de recette incohérent à {hex_rom(adresse)}')
        offsets = []
        for role, pointeur in zip(('08', '0C', '10'), pointeurs):
            if pointeur:
                listes.add((role, pointeur - BASE_GBA))
            offsets.append(hex_rom(pointeur - BASE_GBA) if pointeur else '')
        definitions.append((index, hex_rom(adresse), code_objet(resultat), *colonnes_objet(objet),
                            champ_02, champ_04, f'0x{masque:04X}', *offsets))
    if rom[0x101A30:0x101A44] != bytes(20):
        raise ValueError('Sentinelle des recettes incohérente.')
    ecrire_csv(dossier / 'Recettes-A4NE.csv',
               ('definition', 'offset_rom', 'code_resultat', 'famille_resultat', 'id_resultat', 'nom_resultat',
                'champ_02_u16', 'champ_04_i16', 'masque_06', 'liste_08_rom', 'liste_0c_rom', 'liste_10_rom'),
               definitions)
    ecrire_csv(dossier / 'Listes-recettes-A4NE.csv',
               ('champ_pointeur', 'liste_rom', 'position', 'offset_rom', 'code_brut', 'groupe_ingredient',
                'famille_ingredient', 'id_ingredient', 'nom_ingredient', 'ajustement_endurance',
                'ajustement_fatigue'),
               (ligne for role, adresse in sorted(listes) for ligne in lire_liste_cuisine(rom, adresse, role, objets)))

    echecs = []
    for i in range(9):
        adresse = 0x1010E8 + i * 4
        masque, code = unpack_from('<HH', rom, adresse)
        echecs.append((i, hex_rom(adresse), f'0x{masque:04X}', code_objet(code),
                       *colonnes_objet(objet_cuisine(code, objets))))
    ecrire_csv(dossier / 'Cuisson-echouee-A4NE.csv',
               ('priorite', 'offset_rom', 'masque', 'code_resultat', 'famille', 'id_objet', 'nom_objet'), echecs)


def exporter_peche(rom, objets, dossier):
    ecrire_csv(dossier / 'Zones-peche-A4NE.csv',
               ('ordre', 'offset_rom', 'id_lieu', 'x_min', 'y_min', 'x_max', 'y_max', 'zone'),
               ((i, hex_rom(adresse), *unpack_from('<I4iI', rom, adresse))
                for i, adresse in enumerate(range(0x10563C, 0x1056FC, 24))))
    ecrire_csv(dossier / 'Parametres-peche-A4NE.csv',
               ('zone', 'delais_rom', 'delai_06_08_s', 'delai_09_16_s', 'delai_17_19_s', 'delai_autres_s',
                'poids_rom', 'poids_sans_prise', 'poids_message_bouteille', 'poids_dechets',
                'poids_poissons', 'poids_prises_rares'),
               ((zone, hex_rom(0x104E74 + zone * 8), *unpack_from('<4H', rom, 0x104E74 + zone * 8),
                 hex_rom(0x104EAC + zone * 5), *unpack_from('<5B', rom, 0x104EAC + zone * 5))
                for zone in range(7)))

    prises, conditions = [], []
    for prise in range(59):
        adresse = 0x104ED0 + prise * 32
        pointeur = 0x103A18 + prise * 4
        nom_rom = unpack_from('<I', rom, pointeur)[0] - BASE_GBA
        if not 0x103788 <= nom_rom < 0x103A18:
            raise ValueError(f'Pointeur de nom de prise invalide à {hex_rom(pointeur)}')
        nom = rom[nom_rom:rom.index(b'\0', nom_rom, 0x103A18)].decode('ascii')
        minimum, maximum, *niveaux = unpack_from('<BB28b', rom, adresse)
        article = None
        if prise < 8:
            id_article = unpack_from('<I', rom, 0x104E54 + prise * 4)[0]
            article = objets['article', id_article]
        prises.append((prise, nom, hex_rom(pointeur), hex_rom(nom_rom), hex_rom(adresse), minimum,
                       maximum, *colonnes_objet(article), rom[adresse + 30:adresse + 32].hex().upper()))
        for position, niveau in enumerate(niveaux):
            saison, zone = divmod(position, 7)
            charge = abs(niveau) - 1 if niveau else ''
            conditions.append((prise, SAISONS[saison], zone, hex_rom(adresse + 2 + position), niveau, charge))
    ecrire_csv(dossier / 'Prises-A4NE.csv',
               ('id_prise', 'nom_rom', 'case_nom_rom', 'nom_offset_rom', 'configuration_rom', 'taille_min',
                'taille_max', 'famille_article_table', 'id_article_table', 'nom_article_table', 'alignement_hex'), prises)
    ecrire_csv(dossier / 'Conditions-peche-A4NE.csv',
               ('id_prise', 'saison', 'zone', 'offset_rom', 'niveau_signe', 'charge_indiquee'), conditions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('destination', type=Path, help='Nouveau dossier pour les CSV')
    args = parser.parse_args()
    try:
        rom, version = charger_rom(args.rom)
        if version != 'A4NE':
            raise ValueError('Les tables de ce relevé utilisent la ROM USA A4NE.')
        if args.destination.exists():
            raise ValueError(f'Le dossier de destination existe déjà : {args.destination}')
        objets = {(objet.famille, objet.identifiant): objet for objet in lire_objets(rom)}
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.activites-', dir=args.destination.parent) as temporaire:
            lot = Path(temporaire) / 'activites'
            lot.mkdir()
            exporter_cultures(rom, objets, lot)
            exporter_cuisine(rom, objets, lot)
            exporter_peche(rom, objets, lot)
            lot.rename(args.destination)
    except (OSError, ValueError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print('A4NE · dix CSV de culture, cuisine et pêche exportés.')


if __name__ == '__main__':
    main()
