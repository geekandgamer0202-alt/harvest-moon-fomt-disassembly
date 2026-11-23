#!/usr/bin/env python3
"""Inspecte la SRAM FoMT et projette les lectures VarGet dans les deux emplacements."""

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack_from


TAILLE_SRAM = 0x8000
TAILLE_ENTETE = 0x28
TAILLE_IMAGE = 0x34F4
TAILLE_CASE = (TAILLE_SRAM - TAILLE_ENTETE) // 2
BASES_CASES = (TAILLE_ENTETE, TAILLE_ENTETE + TAILLE_CASE)
SIGNATURE = bytes.fromhex('47424196718fea95a88cea82cc5352414d83438381815b835720303030303000')
LECTURES = Path(__file__).resolve().parents[2] / 'ressources/donnees/lectures-variables'


def decrire_image(image):
    annee, jour, heure = unpack_from('<BBH', image, 0x10)
    noms = {cle: image[offset:offset + 13].split(b'\0', 1)[0].hex()
            for cle, offset in (('joueur', 0x1BD8), ('ferme', 0x14), ('chien', 0x1C78))}
    return {
        'date': {'annee': min(200, 7 * (annee >> 3) + (annee & 7)), 'saison': jour & 3,
                 'jour': ((jour & 0x7C) >> 2) + 1, 'heure': heure & 0x1F, 'minute': (heure & 0x7E0) >> 5},
        'argent_g': unpack_from('<I', image, 0x1AA8)[0],
        'noms_hex': noms,
    }


def lire_case(data, index, masque_cases):
    base = BASES_CASES[index]
    case = {'emplacement': index + 1, 'offset_enregistrement': f'0x{base:04X}'}
    if not masque_cases & (1 << index):
        return {**case, 'statut': 'vide'}

    taille, = unpack_from('<I', data, base)
    case['taille_declaree'] = taille
    if taille != TAILLE_IMAGE:
        return {**case, 'statut': 'taille_invalide'}

    debut = base + 4
    image = data[debut:debut + TAILLE_IMAGE]
    somme_lue, = unpack_from('<I', data, debut + TAILLE_IMAGE)
    somme_calculee = sum(image)
    case.update(offset_image=f'0x{debut:04X}', somme_lue=somme_lue, somme_calculee=somme_calculee)
    if somme_lue != somme_calculee:
        return {**case, 'statut': 'somme_invalide'}
    return {**case, 'statut': 'valide', **decrire_image(image)}


def lire_sram(data):
    if len(data) != TAILLE_SRAM:
        raise ValueError(f'Une image SRAM de {TAILLE_SRAM} octets est requise (reçu {len(data)}).')
    if data[:32] != SIGNATURE:
        raise ValueError('Signature de sauvegarde FoMT invalide.')
    masque, derniere = unpack_from('<II', data, 0x20)
    if masque & ~3 or derniere >= len(BASES_CASES):
        raise ValueError(f'En-tête SRAM invalide (masque {masque:#x}, dernier index {derniere}).')
    return {'sha256_sav': sha256(data).hexdigest(), 'masque_emplacements': masque,
            'dernier_index': derniere, 'emplacements': [lire_case(data, index, masque)
                                                        for index in range(len(BASES_CASES))]}


def lire_csv(nom):
    with (LECTURES / f'{nom}-variables-FoMT.csv').open(encoding='utf-8', newline='') as fichier:
        yield from csv.DictReader(fichier)


def emplacements_variables():
    champs = set()
    for ligne in lire_csv('Lectures'):
        for champ in filter(None, ligne['lectures_image'].split('|')):
            offset_hex, octets = champ.split('/')
            offset, taille = int(offset_hex, 16), int(octets)
            if not (taille in (1, 2, 4) and 0 <= offset <= TAILLE_IMAGE - taille):
                raise ValueError(f'Lecture hors image pour la variable {ligne["id_variable"]} ({champ}).')
            champs.add((int(ligne['id_variable']), offset, taille))

    modeles = {int(ligne['id_variable']): ligne for ligne in lire_csv('Masques')}
    for identifiant, offset, taille in sorted(champs):
        modele = modeles[identifiant]
        masque = decalage = biais = ''
        if (modele['classe'] == 'masque' and int(modele['offset_image'], 16) == offset
                and int(modele['taille_octets']) == taille):
            masque, decalage, biais = (modele[cle] for cle in ('masque', 'decalage', 'biais'))
        yield (identifiant, modele['symbole'], f'0x{offset:04X}', taille, modele['classe'],
               *(f'0x{base + 4 + offset:04X}' for base in BASES_CASES), masque, decalage, biais)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commandes = parser.add_subparsers(dest='commande', required=True)
    inspection = commandes.add_parser('inspecter', help='Vérifie une image SRAM et résume les emplacements en JSON')
    inspection.add_argument('sauvegarde', type=Path)
    indexation = commandes.add_parser('indexer', help='Écrit les offsets .sav des lectures déjà observées')
    indexation.add_argument('destination', type=Path, help='Nouveau fichier CSV')
    args = parser.parse_args()
    try:
        if args.commande == 'inspecter':
            resultats = lire_sram(args.sauvegarde.read_bytes())
            print(json.dumps(resultats, ensure_ascii=False, indent=2))
        else:
            lignes = list(emplacements_variables())
            with args.destination.open('x', encoding='utf-8', newline='') as fichier:
                sortie = csv.writer(fichier, lineterminator='\n')
                sortie.writerow(('id_variable', 'symbole', 'offset_image', 'taille_octets', 'classe',
                                  'offset_sav_1', 'offset_sav_2', 'masque', 'decalage', 'biais'))
                sortie.writerows(lignes)
    except (OSError, ValueError) as erreur:
        parser.exit(1, f'{erreur}\n')


if __name__ == '__main__':
    main()
