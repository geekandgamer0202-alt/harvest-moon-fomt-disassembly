#!/usr/bin/env python3
"""Compte les cellules de terrain et relève les attributs qui ciblent des scripts."""

import argparse
import json
from pathlib import Path
from struct import unpack_from

from indexer_scripts import BASE_GBA, NOMBRE_SCRIPTS, QUATORZE_SCRIPTS, charger_rom, hex_rom, u32


TABLES = {
    'A4NE': (0x105EDC, 0x10692C, 0x106A7C, 0x107204),
    'A4NP': (0x105F34, 0x106984, 0x106AD4, 0x10725C),
}
TAILLES = ((0x28, 66), (0x18, 14), (0x18, 68), (0x2C, 7))


def profil(rom, descripteur, base):
    if base:
        return unpack_from('<IIHH', rom, descripteur + 0x18)
    valeurs, grille = unpack_from('<II', rom, descripteur + 0x10)
    largeur, hauteur = rom[descripteur:descripteur + 2]
    return valeurs, grille, largeur, hauteur


def auditer(rom, version, cibles):
    tables = []
    for famille, (debut, (taille, nombre)) in enumerate(zip(TABLES[version], TAILLES)):
        cellules = 0
        actifs = 0
        adresses = set()
        occurrences = []
        for numero in range(nombre):
            descripteur = debut + taille * numero
            valeurs, grille, largeur, hauteur = profil(rom, descripteur, famille == 0)
            if not (valeurs and largeur and hauteur) or (famille == 0 and not grille):
                continue
            compteur = largeur * hauteur
            coord = grille - BASE_GBA
            donnees = valeurs - BASE_GBA
            if donnees < 0 or donnees + 4 > len(rom) or (grille and not 0 <= coord <= len(rom) - compteur):
                raise ValueError(f'Pointeur de terrain invalide à {hex_rom(descripteur)}')
            indices = rom[coord:coord + compteur] if grille else range(compteur)
            attribut_max = donnees + 4 * max(indices)
            if attribut_max + 4 > len(rom):
                raise ValueError(f'Dictionnaire de terrain tronqué à {hex_rom(donnees)}')
            cellules += compteur
            actifs += 1
            for indice in sorted(set(indices)):
                adresse = donnees + 4 * indice
                adresses.add(adresse)
                mot = u32(rom, adresse)
                marche, bouton = (mot >> 2) & 0x7FFF, mot >> 17
                if {marche, bouton} & cibles:
                    positions = [[i % largeur, i // largeur] for i, v in enumerate(indices) if v == indice]
                    occurrences.append({'descripteur': hex_rom(descripteur), 'entree': numero,
                                        'attribut': hex_rom(adresse), 'marche': f'{marche:04d}',
                                        'bouton_a': f'{bouton:04d}', 'positions': positions})
        tables.append({'offset': hex_rom(debut), 'pas_octets': taille,
                       'descripteurs': nombre, 'descripteurs_actifs': actifs, 'cellules': cellules,
                       'attributs_distincts': len(adresses), 'occurrences': occurrences})
    return {'version': version, 'scripts_recherches': [f'{s:04d}' for s in sorted(cibles)],
            'cellules_total': sum(t['cellules'] for t in tables), 'tables': tables}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('script', type=int, nargs='*', help='Identifiants décimaux, ou les quatorze étudiés par défaut')
    args = parser.parse_args()
    cibles = set(args.script or QUATORZE_SCRIPTS)
    if any(not 1 <= cible <= NOMBRE_SCRIPTS for cible in cibles):
        parser.error('Un identifiant doit être compris entre 0001 et 1328.')
    try:
        rom, version = charger_rom(args.rom)
        print(json.dumps(auditer(rom, version, cibles), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
