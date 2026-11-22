#!/usr/bin/env python3
"""Exporte les variantes d’horaires et trajets des PNJ de FoMT A4NE."""

import argparse
from pathlib import Path
from struct import unpack_from
import sys
from tempfile import TemporaryDirectory


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'economie'))
from exporter_economie import BASE_GBA, charger_rom, ecrire_csv, hex_rom


# Ordre des blocs dans fomt_us.lds, avec les ID de MaryCharacterId.
PNJ = (
    ('Rick', 2, 0x0F1A80), ('Popuri', 3, 0x0F1FC0), ('Lillia', 1, 0x0F280C),
    ('Enfant', 35, 0x0F29C0), ('Cliff', 23, 0x0F2AF8), ('Zack', 28, 0x0F2DC0),
    ('Doctor', 20, 0x0F3010), ('Ellen', 15, 0x0F33B8), ('Jeff', 17, 0x0F3408),
    ('Karen', 19, 0x0F35E4), ('Sasha', 18, 0x0F3FD8), ('Doug', 24, 0x0F42F0),
    ('Ann', 25, 0x0F43DC), ('Lou', 34, 0x0F4974), ('Basil', 10, 0x0F49C0),
    ('Mary', 12, 0x0F4D74), ('Anna', 11, 0x0F5540), ('Won', 29, 0x0F597C),
    ('Thomas', 13, 0x0F59CC), ('Elli', 21, 0x0F5D94), ('Stu', 16, 0x0F61FC),
    ('Duke', 8, 0x0F6370), ('Manna', 9, 0x0F66C4), ('Van', 33, 0x0F6B10),
    ('Harris', 14, 0x0F6B4C), ('Carter', 22, 0x0F6DE8), ('Kai', 26, 0x0F6FF8),
    ('Gray', 7, 0x0F7294), ('Saibara', 6, 0x0F77FC), ('Gotz', 27, 0x0F7B40),
    ('May', 5, 0x0F81BC), ('Barley', 4, 0x0F8678),
)
FIN_BLOCS = 0x0F89D4
DIRECTIONS = ('bas', 'haut', 'gauche', 'droite')
SAISONS = ('printemps', 'été', 'automne', 'hiver')
LIEUX = {
    0: 'MAP_MOTHERS_HILL_MIDDLE', 1: 'MAP_MINERAL_BEACH', 2: 'MAP_FARM', 3: 'MAP_FOREST',
    5: 'MAP_NORTH_SIDE_TOWN', 6: 'MAP_ROSE_SQUARE', 7: 'MAP_SOUTH_SIDE_TOWN',
    8: 'MAP_MOTHERS_HILL_SUMMIT', 10: 'MAP_POULTRY_FARM_HOUSE_1F', 11: 'MAP_POULTRY_FARM_HOUSE_2F',
    12: 'MAP_CHURCH', 13: 'MAP_ZACK_HOUSE', 14: 'MAP_ELLEN_HOUSE', 15: 'MAP_SUPERMARKET',
    16: 'MAP_SUPERMARKET_BACK_ROOM', 17: 'MAP_CHICKEN_COOP',
    19: 'MAP_MINERAL_CLINIC_1F', 20: 'MAP_MINERAL_CLINIC_2F',
    21: 'MAP_INN_1F', 22: 'MAP_INN_BACK_ROOM', 23: 'MAP_INN_2F',
    24: 'MAP_LIBRARY_1F', 25: 'MAP_LIBRARY_2F', 26: 'MAP_BASIL_HOUSE_1F', 27: 'MAP_BASIL_HOUSE_2F',
    29: 'MAP_FARMHOUSE', 30: 'MAP_MAYOR_HOUSE', 31: 'MAP_AJA_WINERY_1F', 32: 'MAP_AJA_WINERY_2F',
    34: 'MAP_AJA_WINERY_STORAGE_B1F', 36: 'MAP_KAI_RESTAURANT', 37: 'MAP_BARN', 38: 'MAP_BLACKSMITH',
    40: 'MAP_GOTZ_HOUSE', 41: 'MAP_YODEL_RANCH_HOUSE_1F', 42: 'MAP_YODEL_RANCH_HOUSE_2F', 564: 'MAP_NONE',
}


def offset_donnees(pointeur, taille, debut, fin):
    offset = pointeur - BASE_GBA
    if not debut <= offset <= fin - taille or offset % 4:
        raise ValueError(f'Pointeur de données inattendu 0x{pointeur:08X}')
    return offset


def lire_personnage(rom, nom, id_pnj, debut, fin, variantes, etapes, trajets):
    selecteur, nombre, choix = unpack_from('<III', rom, debut)
    if not (selecteur & 1 and BASE_GBA <= selecteur < BASE_GBA + PNJ[0][2] and nombre):
        raise ValueError(f'Descripteur de PNJ incohérent à {hex_rom(debut)}')
    table = offset_donnees(choix, 4 * nombre, debut, fin)
    for variante in range(nombre):
        case = table + 4 * variante
        pointeur, = unpack_from('<I', rom, case)
        if not pointeur:
            variantes.append((id_pnj, nom, variante, hex_rom(case), '', 0, ''))
            continue
        horaire = offset_donnees(pointeur, 8, debut, fin)
        n_etapes, entrees = unpack_from('<H2xI', rom, horaire)
        premiere = offset_donnees(entrees, n_etapes * 8, debut, fin)
        variantes.append((id_pnj, nom, variante, hex_rom(case), hex_rom(horaire), n_etapes,
                          hex_rom(premiere)))
        precedent = -1
        for index in range(n_etapes):
            entree = premiere + index * 8
            minute, destination = unpack_from('<H2xI', rom, entree)
            if not precedent <= minute < 1440:
                raise ValueError(f'Ordre des étapes incohérent à {hex_rom(entree)}')
            precedent = minute
            jour, minute_civile = divmod(minute + 360, 1440)
            heures, minutes = divmod(minute_civile, 60)
            trajet = offset_donnees(destination, 12, debut, fin)
            trajets[trajet] = (debut, fin)
            etapes.append((id_pnj, nom, variante, index, hex_rom(entree), minute,
                           f'{heures:02d}:{minutes:02d}', jour, hex_rom(trajet)))
    return (id_pnj, nom, hex_rom(debut), f'0x{selecteur:08X}', hex_rom(table), nombre)


def lire_trajet(rom, adresse, debut, fin, points):
    pointeur, nombre, x, y, drapeaux = unpack_from('<IHhhH', rom, adresse)
    if bool(pointeur) != bool(nombre):
        raise ValueError(f'Nombre de points incohérent à {hex_rom(adresse)}')
    type_b = bool(drapeaux & 0x1000)
    type_point = 'B' if type_b else 'A'
    table = offset_donnees(pointeur, 8 * nombre, debut, fin) if pointeur else None
    for index in range(nombre):
        point = table + 8 * index
        if type_b:
            coord, vitesse, champ_04, flags = unpack_from('<hHHH', rom, point)
            instant = ''
            axe = 'y' if flags & 4 else 'x'
            orientation = DIRECTIONS[flags & 3]
        else:
            instant, coord, flags = unpack_from('<HhI', rom, point)
            axe = 'y' if flags & 1 else 'x'
            vitesse = champ_04 = orientation = ''
        points.append((hex_rom(adresse), index, hex_rom(point), type_point, axe, coord, instant,
                       vitesse, champ_04, orientation, rom[point:point + 8].hex().upper()))
    lieu = drapeaux & 0x3FF
    return (hex_rom(adresse), lieu, LIEUX[lieu], x, y, DIRECTIONS[(drapeaux >> 10) & 3],
            type_point, nombre, hex_rom(table) if table is not None else '', f'0x{drapeaux:04X}')


def exporter(rom, dossier):
    variantes, etapes, points = [], [], []
    trajets = {}
    descripteurs = []
    for (nom, id_pnj, debut), fin in zip(PNJ, [ligne[2] for ligne in PNJ[1:]] + [FIN_BLOCS]):
        descripteurs.append(lire_personnage(rom, nom, id_pnj, debut, fin, variantes, etapes, trajets))

    chemins = [lire_trajet(rom, adresse, *trajets[adresse], points) for adresse in sorted(trajets)]
    ecrire_csv(dossier / 'Personnages-horaires-A4NE.csv',
               ('id_pnj', 'personnage', 'descripteur_rom', 'selecteur_thumb_gba', 'table_choix_rom',
                'nombre_variantes'), descripteurs)
    ecrire_csv(dossier / 'Variantes-horaires-A4NE.csv',
               ('id_pnj', 'personnage', 'variante', 'case_choix_rom', 'horaire_rom', 'nombre_etapes',
                'premiere_etape_rom'), variantes)
    ecrire_csv(dossier / 'Etapes-horaires-A4NE.csv',
               ('id_pnj', 'personnage', 'variante', 'etape', 'offset_rom', 'minutes_depuis_06h',
                'heure', 'decalage_jour_civil', 'trajet_rom'), etapes)
    ecrire_csv(dossier / 'Trajets-horaires-A4NE.csv',
               ('trajet_rom', 'id_lieu', 'symbole_lieu', 'depart_x', 'depart_y', 'orientation_depart',
                'format_points', 'nombre_points', 'points_rom', 'drapeaux_rom'), chemins)
    ecrire_csv(dossier / 'Points-trajets-A4NE.csv',
               ('trajet_rom', 'point', 'offset_rom', 'format', 'axe', 'coord_pixel',
                'minutes_depuis_etape', 'vitesse_rom', 'champ_04_rom', 'orientation_rom', 'octets_rom'), points)

    dates = []
    for index, valeur in enumerate(rom[0x0F1A66:0x0F1A74]):
        saison, jour = divmod(valeur, 30)
        dates.append((hex_rom(0x0F1A66 + index), valeur, SAISONS[saison], jour + 1))
    ecrire_csv(dossier / 'Dates-selection-horaires-A4NE.csv',
               ('offset_rom', 'valeur_rom', 'saison', 'jour'), dates)
    return len(descripteurs), len(variantes), len(etapes), len(chemins), len(points)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('destination', type=Path, help='Nouveau dossier pour les CSV')
    args = parser.parse_args()
    try:
        rom, version = charger_rom(args.rom)
        if version != 'A4NE':
            raise ValueError('Les descripteurs de ce relevé utilisent la ROM USA A4NE.')
        if args.destination.exists():
            raise ValueError(f'Le dossier de destination existe déjà : {args.destination}')
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.horaires-', dir=args.destination.parent) as temporaire:
            lot = Path(temporaire) / 'horaires'
            lot.mkdir()
            personnages, variantes, etapes, trajets, points = exporter(rom, lot)
            lot.rename(args.destination)
    except (OSError, ValueError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print(f'A4NE · {personnages} PNJ, {variantes} cases de variante, {etapes} étapes, '
          f'{trajets} trajets et {points} points.')


if __name__ == '__main__':
    main()
