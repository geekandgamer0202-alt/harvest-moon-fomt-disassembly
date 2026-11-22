#!/usr/bin/env python3
"""Exporte les objets, aliments, produits expédiables et boutiques de FoMT A4NE."""

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from struct import unpack_from
import sys
from tempfile import TemporaryDirectory

from boutiques import exporter_boutiques


OUTILS = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(OUTILS / 'evenements'), str(OUTILS / 'textes')]
from indexer_scripts import BASE_GBA, charger_rom, hex_rom
from indexer_textes import FAMILLES_OBJETS, TABLES_OBJETS


TABLE_PRODUITS = 0x0F0348
NOMBRE_PRODUITS = 103


@dataclass(frozen=True)
class Objet:
    famille: str
    identifiant: int
    nom: str
    fiche: int
    nom_rom: int
    description_rom: int
    icone: int
    donnees: bytes


def lire_objets(rom):
    for (famille, nombre, largeur), table in zip(FAMILLES_OBJETS, TABLES_OBJETS['A4NE']):
        for identifiant in range(nombre):
            fiche = table + identifiant * largeur
            donnees = rom[fiche:fiche + largeur]
            nom_rom = unpack_from('<I', donnees, 0)[0] - BASE_GBA
            description_rom = unpack_from('<I', donnees, largeur - 4)[0] - BASE_GBA
            if not 0 <= min(nom_rom, description_rom) <= max(nom_rom, description_rom) < table:
                raise ValueError(f'Pointeur de texte incohérent à {hex_rom(fiche)}')
            fin_nom = rom.index(b'\0', nom_rom, table)
            nom = rom[nom_rom:fin_nom].decode('ascii')
            icone = unpack_from('<H', donnees, largeur - 8)[0]
            yield Objet(famille, identifiant, nom, fiche, nom_rom, description_rom, icone, donnees)


def lire_produits(rom, objets):
    for identifiant in range(NOMBRE_PRODUITS):
        fiche = TABLE_PRODUITS + identifiant * 4
        mot, = unpack_from('<I', rom, fiche)
        prix = mot & 0x7FFF
        famille = 'article' if mot & 0x8000 else 'aliment'
        id_objet = (mot >> 16) & 0xFF
        objet = objets.get((famille, id_objet))
        if objet is None:
            raise ValueError(f'Objet expédiable inconnu à {hex_rom(fiche)}')
        yield (f'0x{identifiant:02X}', famille, f'0x{id_objet:02X}', objet.nom, prix, hex_rom(fiche),
               hex_rom(objet.fiche), f'0x{mot:08X}')


def ecrire_csv(path, entetes, lignes):
    with path.open('w', encoding='utf-8', newline='') as fichier:
        sortie = csv.writer(fichier, lineterminator='\n')
        sortie.writerow(entetes)
        sortie.writerows(lignes)


def exporter_objets(rom, dossier):
    objets = {(objet.famille, objet.identifiant): objet for objet in lire_objets(rom)}
    lignes_objets, aliments = [], []
    for objet in objets.values():
        reference = (objet.famille, f'0x{objet.identifiant:02X}', objet.nom, hex_rom(objet.fiche))
        lignes_objets.append((*reference, hex_rom(objet.nom_rom), hex_rom(objet.description_rom),
                             objet.icone, objet.donnees.hex(' ').upper()))
        if objet.famille == 'aliment':
            drapeaux, endurance, fatigue = unpack_from('<Bbb', objet.donnees, 4)
            aliments.append((*reference[1:], drapeaux & 1, endurance, fatigue, f'0x{drapeaux:02X}'))
    produits = list(lire_produits(rom, objets))

    ecrire_csv(dossier / 'Objets-A4NE.csv',
               ('famille', 'id_objet', 'nom_rom', 'fiche_rom', 'nom_offset_rom', 'description_offset_rom',
                'id_icone', 'fiche_hex'), lignes_objets)
    ecrire_csv(dossier / 'Aliments-A4NE.csv',
               ('id_objet', 'nom_rom', 'fiche_rom', 'boisson', 'endurance_base', 'fatigue_base',
                'drapeaux_hex'), aliments)
    ecrire_csv(dossier / 'Expedition-A4NE.csv',
               ('id_expedition', 'famille', 'id_objet', 'nom_rom', 'prix_base_g', 'produit_rom',
                'objet_rom', 'mot_hex'), produits)
    return objets, len(aliments), len(produits)


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
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.economie-', dir=args.destination.parent) as temporaire:
            staging = Path(temporaire) / 'economie'
            staging.mkdir()
            objets, aliments, produits = exporter_objets(rom, staging)
            noms_objets = {cle: objet.nom for cle, objet in objets.items()}
            catalogues, lignes = exporter_boutiques(rom, staging, noms_objets)
            staging.rename(args.destination)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(f'A4NE · {len(objets)} objets, {aliments} aliments et {produits} produits expédiables. '
          f'{catalogues} catalogues de boutiques, {lignes} lignes stockées.')


if __name__ == '__main__':
    main()
