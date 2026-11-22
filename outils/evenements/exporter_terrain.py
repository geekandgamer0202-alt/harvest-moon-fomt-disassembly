#!/usr/bin/env python3
"""Exporte les grilles et attributs de terrain de FoMT GBA au format CSV."""

import argparse
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from auditer_terrain import FAMILLES, TABLES, TAILLES, decoder_attribut, lire_terrains
from indexer_scripts import charger_rom, hex_rom


def ecrire_csv(path, entetes, lignes):
    with path.open('w', encoding='utf-8', newline='') as fichier:
        writer = csv.writer(fichier, lineterminator='\n')
        writer.writerow(entetes)
        writer.writerows(lignes)


def ecrire_grille(path, terrain):
    lignes = ((y, *terrain.indices[y * terrain.largeur:(y + 1) * terrain.largeur])
              for y in range(terrain.hauteur))
    ecrire_csv(path, ('y', *range(terrain.largeur)), lignes)


def exporter(rom, version, dossier):
    dossier.mkdir()
    (dossier / 'grilles').mkdir()
    descripteurs, interactions = [], []
    attributs = {}
    cellules_rom = 0
    for famille, debut, (taille, nombre) in zip(FAMILLES, TABLES[version], TAILLES):
        base = famille == 'base'
        for terrain in lire_terrains(rom, debut, taille, nombre, base):
            mode = 'zero_initialise' if base else 'sans_attribut_rom'
            grille = ''
            if terrain.indices:
                mode = 'indexe'
                grille = f'grilles/{famille}-{terrain.numero:02d}.csv'
                ecrire_grille(dossier / grille, terrain)
                cellules_rom += len(terrain.indices)
                for indice in set(terrain.indices):
                    adresse = terrain.valeurs + 4 * indice
                    attributs[adresse] = decoder_attribut(rom, adresse)
                for position, indice in enumerate(terrain.indices):
                    adresse = terrain.valeurs + 4 * indice
                    _, marche, bouton = attributs[adresse]
                    if marche or bouton:
                        y, x = divmod(position, terrain.largeur)
                        interactions.append((famille, terrain.numero, x, y, indice, hex_rom(adresse),
                                             f'{marche:04d}' if marche else '', f'{bouton:04d}' if bouton else ''))
            descripteurs.append((famille, terrain.numero, hex_rom(terrain.descripteur), terrain.largeur,
                                 terrain.hauteur, mode, len(terrain.indices),
                                 hex_rom(terrain.valeurs) if terrain.valeurs is not None else '',
                                 hex_rom(terrain.grille) if terrain.grille is not None else '', grille))

    valeurs = ((hex_rom(adresse), f'0x{mot:08X}', mot & 1, (mot >> 1) & 1,
                f'{marche:04d}' if marche else '', f'{bouton:04d}' if bouton else '')
               for adresse, (mot, marche, bouton) in sorted(attributs.items()))
    ecrire_csv(dossier / f'Terrains-{version}.csv',
               ('famille', 'entree', 'descripteur_rom', 'largeur', 'hauteur', 'mode', 'cellules_rom',
                'attributs_rom', 'grille_rom', 'fichier_grille'), descripteurs)
    ecrire_csv(dossier / f'Attributs-{version}.csv',
               ('attribut_rom', 'mot_hex', 'bit_0', 'bit_1', 'script_marche', 'script_bouton_a'), valeurs)
    ecrire_csv(dossier / f'Interactions-{version}.csv',
               ('famille', 'entree', 'x_local', 'y_local', 'indice', 'attribut_rom', 'script_marche',
                'script_bouton_a'), interactions)
    return len(descripteurs), cellules_rom, len(attributs), len(interactions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('destination', type=Path, help='Nouveau dossier pour les CSV')
    args = parser.parse_args()
    try:
        rom, version = charger_rom(args.rom)
        if args.destination.exists():
            raise ValueError(f'Le dossier de destination existe déjà : {args.destination}')
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.terrain-', dir=args.destination.parent) as temporaire:
            staging = Path(temporaire) / 'terrain'
            descripteurs, cellules, attributs, interactions = exporter(rom, version, staging)
            staging.rename(args.destination)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(f'{version} · {descripteurs} descripteurs, {cellules} cellules ROM, '
          f'{attributs} mots d’attribut et {interactions} cellules avec script.')


if __name__ == '__main__':
    main()
