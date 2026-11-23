#!/usr/bin/env python3
"""Relève les lectures mémoire de VarGet sur des états mGBA USA et Europe."""

import argparse
from collections import Counter
import csv
from functools import cache
from hashlib import sha256
from pathlib import Path
import random
from struct import unpack_from
import sys
from tempfile import TemporaryDirectory
from zlib import error as ZlibError

from unicorn import UC_HOOK_MEM_READ, UcError
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1

from relever_selecteurs import (
    BASE_EWRAM, BASE_GBA, BASE_IWRAM, EWRAM, PARTIE, PILE_VIDE, RETOUR,
    entier_signe, preparer_cpu, read_state,
)

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / 'outils/evenements'))
from exporter_routines_natives import NOMBRE_VARIABLES, charger_rom, ecrire_csv, lire_moteur


MOTEUR = 0x0200207C
TAILLE_IMAGE = 0x34F4
POINTEUR_PARTIE = MOTEUR + 0x350
POINTEURS_MOTEUR = {(POINTEUR_PARTIE, 4), (MOTEUR + 0x354, 4)}
LIMITE_INSTRUCTIONS = 5000
SYMBOLES = RACINE / 'ressources/donnees/routines-natives/Variables-natives-FoMT.csv'


def dans_image(adresse, taille):
    return PARTIE <= adresse and adresse + taille <= PARTIE + TAILLE_IMAGE


class Observateur:
    def __init__(self, rom, table, etat):
        pointeur, = unpack_from('<I', etat, EWRAM + POINTEUR_PARTIE - BASE_EWRAM)
        if pointeur != PARTIE:
            raise ValueError(f'Pointeur de l’image de sauvegarde inattendu ({pointeur:#010x})')
        self.cpu, self.registres = preparer_cpu(rom, etat)
        self.entree = BASE_GBA + table.fonction + 1
        self.lectures = set()
        for base, taille in ((BASE_EWRAM, 0x40000), (BASE_IWRAM, 0x8000)):
            self.cpu.hook_add(UC_HOOK_MEM_READ, self.noter_lecture, begin=base, end=base + taille - 1)

    def noter_lecture(self, _cpu, _acces, adresse, taille, _valeur, _donnees):
        lecture = adresse, taille
        if lecture not in POINTEURS_MOTEUR:
            self.lectures.add(lecture)

    def lire(self, identifiant):
        self.lectures.clear()
        self.cpu.mem_write(RETOUR, PILE_VIDE)
        self.cpu.context_restore(self.registres)
        self.cpu.reg_write(UC_ARM_REG_R0, MOTEUR)
        self.cpu.reg_write(UC_ARM_REG_R1, identifiant)
        self.cpu.emu_start(self.entree, RETOUR, count=LIMITE_INSTRUCTIONS)
        if self.cpu.reg_read(UC_ARM_REG_PC) != RETOUR:
            raise ValueError('VarGet n’a pas terminé dans la limite d’instructions')
        return entier_signe(self.cpu.reg_read(UC_ARM_REG_R0)), tuple(sorted(self.lectures))


@cache
def valeurs_essai(taille):
    if taille == 1:
        return range(256)
    bits = 8 * taille
    maximum = (1 << bits) - 1
    isoles = {1 << i for i in range(bits)}
    aleatoire = random.Random(taille)
    melanges = {aleatoire.getrandbits(bits) for _ in range(64)}
    return tuple(sorted({0, maximum} | isoles | {maximum ^ bit for bit in isoles} | melanges))


def evaluer(mot, modele):
    masque, decalage, biais = modele
    return entier_signe(((mot & masque) >> decalage) + biais)


def tester(observateur, identifiant, champ, valeur_initiale):
    adresse, taille = champ
    original = bytes(observateur.cpu.mem_read(adresse, taille))
    sorties = {}
    try:
        for mot in valeurs_essai(taille):
            observateur.cpu.mem_write(adresse, mot.to_bytes(taille, 'little'))
            valeur, lectures = observateur.lire(identifiant)
            if lectures != (champ,):
                return 'chemin_variable', len(sorties), None
            sorties[mot] = valeur
    except (UcError, ValueError):
        return 'essai_interrompu', len(sorties), None
    finally:
        observateur.cpu.mem_write(adresse, original)

    biais = sorties[0]
    masque = sum(1 << bit for bit in range(8 * taille) if sorties[1 << bit] != biais)
    essais = len(sorties)
    if not masque:
        valeurs = set(sorties.values()) | {valeur_initiale}
        classe = 'constant_observe' if valeurs == {biais} else 'transformation'
        return classe, essais, None
    decalage = (masque & -masque).bit_length() - 1
    modele = masque, decalage, biais
    sorties[int.from_bytes(original, 'little')] = valeur_initiale
    if any(evaluer(mot, modele) != valeur for mot, valeur in sorties.items()):
        return 'transformation', essais, None
    return 'masque', essais, modele


def decrire_masque(identifiant, contextes):
    traces = [mesures[identifiant][1] for _, _, _, mesures in contextes]
    if any(not dans_image(*lecture) for trace in traces for lecture in trace):
        return ('hors_image',)
    if any(trace != traces[0] for trace in traces):
        return ('chemin_variable',)
    if len(traces[0]) != 1:
        return ('plusieurs_lectures' if traces[0] else 'sans_lecture',)

    champ, = traces[0]
    adresse, taille = champ
    resultats = [tester(obs, identifiant, champ, mesures[identifiant][0])
                 for _, _, obs, mesures in contextes]
    classes = {classe for classe, _, _ in resultats}
    valeurs = {modele for _, _, modele in resultats}
    classe = next(iter(classes)) if len(classes) == 1 and len(valeurs) == 1 else 'resultats_divergents'
    mode = 'exhaustif_8_bits' if taille == 1 else 'sondage'
    essais = '|'.join(str(nombre) for _, nombre, _ in resultats)
    colonnes = classe, f'0x{adresse - PARTIE:04X}', taille, mode, essais
    if classe == 'masque':
        (masque, decalage, biais), = valeurs
        return (*colonnes, f'0x{masque:0{taille * 2}X}', decalage, biais)
    return colonnes


def lire_contextes(roms, chemins):
    tables = {edition: lire_moteur(rom, edition)[1] for edition, rom in roms.items()}
    for chemin in chemins:
        brut = chemin.read_bytes()
        etat, code = read_state(brut)
        edition = code.decode('ascii')
        observateur = Observateur(roms[edition], tables[edition], etat)
        mesures = {}
        for identifiant in range(NOMBRE_VARIABLES):
            try:
                mesures[identifiant] = observateur.lire(identifiant)
            except (UcError, ValueError) as erreur:
                raise ValueError(f'{chemin.name}, VarGet({identifiant}) ({erreur})') from erreur
        yield chemin.stem, (edition, sha256(brut).hexdigest()), observateur, mesures


def serialiser_lectures(lectures):
    internes = [f'0x{a - PARTIE:04X}/{n}' for a, n in lectures if dans_image(a, n)]
    externes = [f'0x{a:08X}/{n}' for a, n in lectures if not dans_image(a, n)]
    return '|'.join(internes), '|'.join(externes)


def exporter(roms, chemins, dossier):
    with SYMBOLES.open(encoding='utf-8', newline='') as fichier:
        symboles = {int(row['id_variable']): row['symbole'] for row in csv.DictReader(fichier)}
    if set(symboles) != set(range(NOMBRE_VARIABLES)):
        raise ValueError('Index des symboles natifs incomplet')
    contextes = list(lire_contextes(roms, chemins))
    lignes = [(nom, edition, identifiant, symboles[identifiant], valeur, *serialiser_lectures(lectures))
              for nom, (edition, _), _, mesures in contextes
              for identifiant, (valeur, lectures) in mesures.items()]
    masques = []
    for identifiant, symbole in sorted(symboles.items()):
        champs = decrire_masque(identifiant, contextes)
        masques.append((identifiant, symbole, *champs, *('',) * (8 - len(champs))))

    ecrire_csv(dossier / 'Contextes-variables-FoMT.csv',
               ('contexte', 'edition', 'sha256_etat', 'script_engine_gba', 'save_image_gba'),
               ((nom, *meta, f'0x{MOTEUR:08X}', f'0x{PARTIE:08X}') for nom, meta, _, _ in contextes))
    ecrire_csv(dossier / 'Lectures-variables-FoMT.csv',
               ('contexte', 'edition', 'id_variable', 'symbole', 'valeur_r0_signee',
                'lectures_image', 'lectures_hors_image'), lignes)
    ecrire_csv(dossier / 'Masques-variables-FoMT.csv',
               ('id_variable', 'symbole', 'classe', 'offset_image', 'taille_octets', 'mode_essai',
                'essais_par_contexte', 'masque', 'decalage', 'biais'), masques)
    return len(lignes), Counter(ligne[2] for ligne in masques)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('roms', type=Path, nargs=2, metavar='ROM', help='Une ROM A4NE et une ROM A4NP')
    parser.add_argument('destination', type=Path, help='Nouveau dossier pour les CSV')
    parser.add_argument('etats', type=Path, nargs='+', help='États instantanés de mGBA 0.10.5')
    args = parser.parse_args()
    try:
        roms = {edition: rom for rom, edition in map(charger_rom, args.roms)}
        if set(roms) != {'A4NE', 'A4NP'}:
            raise ValueError('Les deux ROM de référence A4NE et A4NP sont requises.')
        if len({chemin.stem for chemin in args.etats}) != len(args.etats):
            raise ValueError('Chaque état doit avoir un nom de fichier distinct.')
        if args.destination.exists():
            raise ValueError(f'Le dossier de destination existe déjà ({args.destination}).')
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.variables-', dir=args.destination.parent) as temporaire:
            lot = Path(temporaire) / 'variables'
            lot.mkdir()
            lectures, classes = exporter(roms, args.etats, lot)
            lot.rename(args.destination)
    except (OSError, UcError, ValueError, ZlibError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print(f'{lectures} appels VarGet · {classes["masque"]} masques vérifiés sur {len(args.etats)} états.')


if __name__ == '__main__':
    main()
