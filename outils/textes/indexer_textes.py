#!/usr/bin/env python3
"""Indexe les adresses des textes FoMT GBA sans exporter leur contenu."""

import argparse
import csv
from pathlib import Path
from struct import unpack_from
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evenements'))
from indexer_scripts import BASE_GBA, charger_rom, hex_rom, indexer


TABLES_PERSONNAGES = {'A4NE': 0x104258, 'A4NP': 0x1042B0}
NOMBRE_PERSONNAGES = 43
TABLES_OBJETS = {
    'A4NE': (0x0EAB0C, 0x0EDCD8, 0x0EFED4),
    'A4NP': (0x0EAB58, 0x0EDD24, 0x0EFF20),
}
FAMILLES_OBJETS = (('outil', 81, 12), ('aliment', 171, 16), ('article', 95, 12))
INDEX_NATIFS = Path(__file__).resolve().parents[2] / 'docs/textes/Natifs-A4NP.csv'


def indexer_evenements(rom, version, sortie):
    scripts, _ = indexer(rom, version)
    sortie.writerow(('id', 'script', 'slot', 'case_script_rom', 'bloc_script_rom',
                     'table_str_rom', 'case_chaine_rom', 'offset_rom', 'octets'))
    for script in scripts:
        table = script.sections[b'STR '].debut
        for slot, chaine in enumerate(script.chaines):
            sortie.writerow((f'{script.identifiant:04d}.{slot:02d}', f'{script.identifiant:04d}',
                             slot, hex_rom(script.case), hex_rom(script.bloc.debut),
                             hex_rom(table), hex_rom(table + 4 * (slot + 1)),
                             hex_rom(chaine.debut), chaine.fin - chaine.debut))


def indexer_noms(rom, version, sortie):
    table = TABLES_PERSONNAGES[version]
    lignes = []
    for identifiant in range(NOMBRE_PERSONNAGES):
        case = table + identifiant * 8
        debut = unpack_from('<I', rom, case)[0] - BASE_GBA
        if not 0 <= debut < table:
            raise ValueError(f'Pointeur de nom invalide à {hex_rom(case)}')
        longueur = rom.index(b'\0', debut, table) - debut
        if not longueur and identifiant not in (0, 35):
            raise ValueError(f'Nom statique vide à {hex_rom(case)}')
        lignes.append((identifiant, hex_rom(case), hex_rom(debut), longueur))
    sortie.writerow(('id_personnage', 'case_rom', 'offset_rom', 'octets'))
    sortie.writerows(lignes)


def indexer_objets(rom, version, sortie):
    lignes = []
    for (famille, nombre, largeur), table in zip(FAMILLES_OBJETS, TABLES_OBJETS[version]):
        for identifiant in range(nombre):
            case = table + identifiant * largeur
            nom = unpack_from('<I', rom, case)[0] - BASE_GBA
            description = unpack_from('<I', rom, case + largeur - 4)[0] - BASE_GBA
            if not 0 <= min(nom, description) <= max(nom, description) < table:
                raise ValueError(f'Pointeur d’objet invalide à {hex_rom(case)}')
            lignes.append((famille, f'0x{identifiant:02X}', hex_rom(case),
                           hex_rom(nom), rom.index(b'\0', nom, table) - nom,
                           hex_rom(description), rom.index(b'\0', description, table) - description))
    sortie.writerow(('famille', 'id_objet', 'case_rom', 'offset_nom_rom', 'octets_nom',
                     'offset_description_rom', 'octets_description'))
    sortie.writerows(lignes)


def verifier_natifs(rom, version):
    if version != 'A4NP':
        raise ValueError('Le relevé des lecteurs natifs utilise la ROM A4NP.')
    lignes = lectures = 0
    with INDEX_NATIFS.open(encoding='utf-8', newline='') as fichier:
        for ligne in csv.DictReader(fichier):
            debut = int(ligne['offset_rom'], 16)
            longueur = int(ligne['octets'])
            fin = debut + longueur
            if ligne['id'] != f'N{debut:06X}' or rom.find(b'\0', debut, fin + 1) != fin:
                raise ValueError(f'Métadonnées natives incohérentes pour {ligne["id"]}')
            lignes += 1
            for paire in ligne['lectures_thumb'].split('|'):
                lecteur, litteral = (int(offset, 16) for offset in paire.split('>'))
                opcode = unpack_from('<H', rom, lecteur)[0]
                pointeur = unpack_from('<I', rom, litteral)[0]
                adresse_ldr = ((lecteur + 4) & ~3) + 4 * (opcode & 0xFF)
                if opcode & 0xF800 != 0x4800 or adresse_ldr != litteral or pointeur != BASE_GBA + debut:
                    raise ValueError(f'Lecture native incohérente à {hex_rom(lecteur)}')
                lectures += 1
    print(f'{lignes} chaînes et {lectures} références Thumb vérifiées dans A4NP.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--noms', action='store_true', help='Indexer les entrées de noms de personnages')
    mode.add_argument('--objets', action='store_true', help='Indexer les noms et descriptions d’inventaire')
    mode.add_argument('--verifier-natifs', action='store_true', help='Vérifier le relevé des lecteurs natifs A4NP')
    args = parser.parse_args()
    try:
        rom, version = charger_rom(args.rom)
        if args.verifier_natifs:
            verifier_natifs(rom, version)
            return
        sortie = csv.writer(sys.stdout, lineterminator='\n')
        if args.noms:
            indexer_noms(rom, version, sortie)
        elif args.objets:
            indexer_objets(rom, version, sortie)
        else:
            indexer_evenements(rom, version, sortie)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
