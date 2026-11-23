#!/usr/bin/env python3
"""Relie les compteurs romantiques, leurs écritures de script et le marqueur actif."""

import argparse
from collections import Counter
import csv
from hashlib import sha256
from pathlib import Path
from struct import unpack
from tempfile import TemporaryDirectory
from zlib import error as ZlibError

from unicorn import UC_HOOK_CODE, UcError
from unicorn.arm_const import UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP

from relever_ecritures import Traceur, decrire_phase, lire_entrants, LITTERAUX
from relever_variables import (
    BASE_GBA, NOMBRE_VARIABLES, PARTIE, RACINE, charger_rom, ecrire_csv, lire_moteur, read_state,
)
from exporter_routines_natives import cible_bl, hex_rom


MARQUEUR = PARTIE + 0x2158
DATE_MARIAGE = PARTIE + 0x1D00
# GameStateSaveImage::npcs (+0x1CD4), puis le membre Bachelorette et ses bits à +0x16.
PERSONNAGES = {3: 0x1D82, 12: 0x1E3E, 19: 0x1ECE, 21: 0x1EFA, 25: 0x1F4E, 31: 0x1FCE}
COMPTEURS = (('joueur', 0x0007, 0), ('rival', 0x01C0, 6))


def lire_csv(path):
    with path.open(encoding='utf-8', newline='') as fichier:
        yield from csv.DictReader(fichier)


def detecter(traceur, rom, edition):
    pas = 0 if edition == 'A4NE' else 0x14
    lecture = BASE_GBA + 0x0455D8 + pas
    ecriture = BASE_GBA + cible_bl(rom, 0x04A1BA + pas)
    lectures, ecritures = {}, {}

    def relever(cpu, pc, _taille, _donnees):
        identifiant, personnage, r3 = (cpu.reg_read(reg) for reg in (UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        if identifiant != variable_sondee:
            raise ValueError(f'Variable {variable_sondee} transmise sous l’ID {identifiant}')
        pile = cpu.reg_read(UC_ARM_REG_SP)
        if pc == lecture:
            lectures[identifiant] = personnage, r3, cpu.mem_read(pile, 1)[0]
        else:
            seuil, compteur = unpack('<IB', cpu.mem_read(pile, 5))
            ecritures[identifiant] = personnage, seuil, compteur

    crochet_lecture = traceur.cpu.hook_add(UC_HOOK_CODE, relever, begin=lecture, end=lecture)
    crochet_ecriture = traceur.cpu.hook_add(UC_HOOK_CODE, relever, begin=ecriture, end=ecriture)
    for variable_sondee in range(NOMBRE_VARIABLES):
        traceur.lire(variable_sondee)
        traceur.restaurer()
        traceur.ecrire(variable_sondee, 1)
        traceur.restaurer()
    traceur.cpu.hook_del(crochet_lecture)
    traceur.cpu.hook_del(crochet_ecriture)
    if lectures != ecritures or not lectures:
        raise ValueError(f'Les paramètres romantiques diffèrent entre VarGet et VarSet en {edition}')
    return lectures, lecture - BASE_GBA, ecriture - BASE_GBA


def etat_romantique(traceur, identifiant, definition):
    personnage, _, compteur = definition
    _, masque, decalage = COMPTEURS[compteur]
    bits, = unpack('<H', traceur.cpu.mem_read(PARTIE + PERSONNAGES[personnage], 2))
    marqueur, = unpack('<H', traceur.cpu.mem_read(MARQUEUR, 2))
    return (traceur.lire(identifiant), (bits & masque) >> decalage, f'0x{marqueur:04X}',
            '|'.join(map(str, traceur.registre()[0])), bytes(traceur.cpu.mem_read(DATE_MARIAGE, 2)))


def sequences(definitions):
    for identifiant in sorted(definitions):
        yield 'cycle', tuple((identifiant, valeur) for valeur in (1, 1, 0, 1, 2, 1, 0, 2))
        yield 'fin_sans_ouverture', ((identifiant, 2),)
    if {70, 71} <= definitions.keys():
        yield 'deux_ouvertures', ((70, 1), (71, 1), (70, 0), (71, 2), (70, 2))
    if {117, 118, 119} <= definitions.keys():
        yield 'seuil_rival_partage', ((117, 1), (118, 1), (119, 2), (118, 2))


def tester(traceur, contexte, definitions):
    for sequence, etapes in sequences(definitions):
        traceur.restaurer()
        for etape, (identifiant, argument) in enumerate(etapes, 1):
            definition = definitions[identifiant]
            avant = etat_romantique(traceur, identifiant, definition)
            notification, phases = traceur.ecrire(identifiant, argument)
            apres = etat_romantique(traceur, identifiant, definition)
            yield (contexte, sequence, etape, identifiant, argument,
                   *avant[:4], *apres[:4], avant[4].hex(), apres[4].hex(), notification,
                   *(decrire_phase(phase)[1] for phase in phases))


def exporter(roms, fichiers, dossier):
    catalogue, _ = lire_entrants()
    personnels = {int(x['id_personnage']): x['nom_affiche'] for x in lire_csv(RACINE / 'docs/textes/Personnages.csv')
                  if x['id_personnage'].isdigit()}
    labels = {x['script']: x['symbole_us'] for x in lire_csv(RACINE / 'docs/evenements/catalogue-a4ne.csv')}
    tables = {ed: lire_moteur(rom, ed) for ed, rom in roms.items()}
    definitions = None
    contextes, transitions = [], []
    for fichier in fichiers:
        brut = fichier.read_bytes()
        etat, code = read_state(brut)
        edition = code.decode('ascii')
        traceur = Traceur(roms[edition], tables[edition], etat)
        mesure, entree_l, entree_e = detecter(traceur, roms[edition], edition)
        if definitions is not None and mesure != definitions:
            raise ValueError(f'Correspondance des variables romantiques différente dans {fichier.name}')
        definitions = mesure
        contextes.append((fichier.stem, edition, sha256(brut).hexdigest(), hex_rom(entree_l), hex_rom(entree_e)))
        transitions.extend(tester(traceur, fichier.stem, mesure))

    scripts = []
    compte = Counter()
    for row in lire_csv(LITTERAUX):
        identifiant = int(row['id_variable'])
        if identifiant in definitions:
            scripts.append((row['script'], labels[row['script']], identifiant, row['symbole_variable'],
                            row['forme'], row['expression'], row['pc_code'], row['site_a4ne_rom'], row['site_a4np_rom']))
            compte[identifiant] += 1

    variables = []
    for identifiant, (personnage, seuil, compteur) in sorted(definitions.items()):
        entree = catalogue[identifiant]
        mode, masque, decalage = COMPTEURS[compteur]
        variables.append((identifiant, entree['symbole'], personnage, personnels[personnage], mode, seuil,
                          f'0x{PERSONNAGES[personnage]:04X}', f'0x{masque:04X}', decalage,
                          entree['lecture_a4ne_rom'], entree['ecriture_a4ne_rom'],
                          entree['lecture_a4np_rom'], entree['ecriture_a4np_rom'], compte[identifiant]))

    ecrire_csv(dossier / 'Contextes-romance-FoMT.csv',
               ('contexte', 'edition', 'sha256_etat', 'aide_lecture_rom', 'aide_ecriture_rom'), contextes)
    ecrire_csv(dossier / 'Variables-romance-FoMT.csv',
               ('id_variable', 'symbole', 'id_personnage', 'personnage', 'compteur', 'seuil',
                'offset_compteur_image', 'masque_u16', 'decalage', 'lecture_a4ne_rom', 'ecriture_a4ne_rom',
                'lecture_a4np_rom', 'ecriture_a4np_rom', 'sites_varset'), variables)
    ecrire_csv(dossier / 'Scripts-romance-FoMT.csv',
               ('script', 'symbole_script', 'id_variable', 'symbole_variable', 'forme', 'argument',
                'pc_code', 'site_a4ne_rom', 'site_a4np_rom'), scripts)
    ecrire_csv(dossier / 'Transitions-romance-FoMT.csv',
               ('contexte', 'sequence', 'etape', 'id_variable', 'argument', 'varget_avant', 'compteur_avant',
                'marqueur_avant', 'registre_avant', 'varget_apres', 'compteur_apres', 'marqueur_apres',
                'registre_apres', 'date_mariage_avant_hex', 'date_mariage_apres_hex', 'notification_atteinte',
                'ecriture_bits_image_modifies', 'notification_bits_image_modifies'), transitions)
    return len(variables), len(scripts), len(transitions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('roms', nargs=2, type=Path, metavar='ROM')
    parser.add_argument('destination', type=Path, help='Nouveau dossier pour les CSV')
    parser.add_argument('etats', nargs='+', type=Path, help='États mGBA 0.10.5 A4NE et A4NP')
    args = parser.parse_args()
    try:
        roms = {ed: rom for rom, ed in map(charger_rom, args.roms)}
        if set(roms) != {'A4NE', 'A4NP'}:
            raise ValueError('Les deux ROM de référence A4NE et A4NP sont requises.')
        if len({path.stem for path in args.etats}) != len(args.etats):
            raise ValueError('Chaque état doit avoir un nom distinct.')
        if args.destination.exists():
            raise ValueError(f'Le dossier de destination existe déjà ({args.destination}).')
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.romance-', dir=args.destination.parent) as temporaire:
            dossier = Path(temporaire) / 'romance'
            dossier.mkdir()
            variables, scripts, transitions = exporter(roms, args.etats, dossier)
            dossier.rename(args.destination)
    except (OSError, UcError, ValueError, ZlibError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print(f'{variables} variables · {scripts} sites de script · {transitions} transitions relevées.')


if __name__ == '__main__':
    main()
