#!/usr/bin/env python3
"""Relève les choix d’horaires A4NE à 06:00 sur l’an 1 à partir d’états mGBA."""

import argparse
from collections import Counter
from hashlib import sha256
from pathlib import Path
from struct import pack, unpack_from
import sys
from tempfile import TemporaryDirectory
from zlib import error as ZlibError

from unicorn import (
    UC_ARCH_ARM, UC_HOOK_INTR, UC_MODE_THUMB, UC_PROT_EXEC, UC_PROT_READ,
    UC_PROT_WRITE, Uc, UcError,
)
from unicorn.arm_const import (
    UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R3, UC_ARM_REG_SP,
)

from exporter_horaires import BASE_GBA, PNJ, SAISONS, charger_rom, ecrire_csv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'mgba'))
from inspecter_etat import EWRAM, read_state
from preparer_karen import SAVE_IN_EWRAM


BASE_EWRAM = 0x02000000
BASE_IWRAM = 0x03000000
IWRAM = 0x19000
PARTIE = BASE_EWRAM + SAVE_IN_EWRAM
METEO = PARTIE + 0x08
CALENDRIER = PARTIE + 0x10
RETOUR = 0x01000000
PILE_VIDE = bytes(0x2000)
CODES_METEO = range(5)
ANNEE = 1
HEURE = 6


def entier_signe(valeur):
    return (valeur & 0x7FFFFFFF) - (valeur & 0x80000000)


def division_bios(cpu, interruption, _donnees):
    pc = cpu.reg_read(UC_ARM_REG_PC)
    if cpu.mem_read(pc - 2, 2) != b'\x06\xdf':
        raise ValueError(f'Interruption {interruption} inattendue à 0x{pc - 2:08X}')
    dividende = entier_signe(cpu.reg_read(UC_ARM_REG_R0))
    diviseur = entier_signe(cpu.reg_read(UC_ARM_REG_R1))
    if diviseur == 0:
        raise ValueError('Division BIOS par zéro')
    quotient = abs(dividende) // abs(diviseur)
    if (dividende < 0) != (diviseur < 0):
        quotient = -quotient
    reste = dividende - quotient * diviseur
    for registre, valeur in ((UC_ARM_REG_R0, quotient), (UC_ARM_REG_R1, reste),
                             (UC_ARM_REG_R3, abs(quotient))):
        cpu.reg_write(registre, valeur & 0xFFFFFFFF)


def preparer_cpu(rom, etat):
    cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    regions = (
        (BASE_GBA, rom, UC_PROT_READ | UC_PROT_EXEC),
        (BASE_EWRAM, etat[EWRAM:], UC_PROT_READ),
        (BASE_IWRAM, etat[IWRAM:EWRAM], UC_PROT_READ),
    )
    for adresse, contenu, droits in regions:
        cpu.mem_map(adresse, len(contenu), droits)
        cpu.mem_write(adresse, contenu)
    cpu.mem_map(RETOUR, len(PILE_VIDE), UC_PROT_READ | UC_PROT_WRITE)
    cpu.reg_write(UC_ARM_REG_SP, RETOUR + len(PILE_VIDE))
    cpu.reg_write(UC_ARM_REG_LR, RETOUR | 1)
    cpu.reg_write(UC_ARM_REG_R0, PARTIE)
    cpu.hook_add(UC_HOOK_INTR, division_bios)
    return cpu, cpu.context_save()


def relever(rom, chemins, dossier):
    contextes = []
    choix = []
    frequences = []
    for chemin in chemins:
        contenu = chemin.read_bytes()
        etat, code = read_state(contenu)
        if code != b'A4NE':
            raise ValueError(f'Un état A4NE est requis pour {chemin}')
        contexte = chemin.stem
        contextes.append((contexte, sha256(contenu).hexdigest(), ANNEE, f'{HEURE:02d}:00'))
        cpu, registres = preparer_cpu(rom, etat)
        for nom, identifiant, descripteur in PNJ:
            selecteur, nombre, table = unpack_from('<III', rom, descripteur)
            compte = Counter()
            for saison, libelle in enumerate(SAISONS):
                for jour in range(1, 31):
                    cpu.mem_write(CALENDRIER, pack('<BBH', ANNEE, ((jour - 1) << 2) | saison, HEURE))
                    variantes = []
                    for meteo in CODES_METEO:
                        cpu.mem_write(METEO, pack('<I', meteo))
                        cpu.mem_write(RETOUR, PILE_VIDE)
                        cpu.context_restore(registres)
                        try:
                            cpu.emu_start(selecteur, RETOUR, count=4096)
                            variante = cpu.reg_read(UC_ARM_REG_R0)
                            if cpu.reg_read(UC_ARM_REG_PC) != RETOUR or variante >= nombre:
                                raise ValueError(f'Retour invalide du sélecteur {selecteur:#010x}')
                        except (UcError, ValueError) as erreur:
                            raise ValueError(f'{contexte}, {nom}, {jour} {libelle}, météo {meteo} '
                                             f'({erreur})') from erreur
                        variantes.append(variante)
                    compte.update(variantes)
                    choix.append((contexte, identifiant, nom, libelle, jour, *variantes))
            for variante in range(nombre):
                pointeur, = unpack_from('<I', rom, table - BASE_GBA + variante * 4)
                frequences.append((contexte, identifiant, nom, variante, int(bool(pointeur)),
                                   compte[variante]))
    ecrire_csv(dossier / 'Contextes-A4NE.csv',
               ('contexte', 'sha256_etat', 'annee_mesuree', 'heure_mesuree'), contextes)
    ecrire_csv(dossier / 'Choix-horaires-An1-A4NE.csv',
               ('contexte', 'id_pnj', 'personnage', 'saison', 'jour',
                *(f'meteo_{code}' for code in CODES_METEO)), choix)
    ecrire_csv(dossier / 'Frequences-horaires-An1-A4NE.csv',
               ('contexte', 'id_pnj', 'personnage', 'variante', 'horaire_present', 'nombre_cas'), frequences)
    return len(choix) * len(CODES_METEO)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('destination', type=Path, help='Nouveau dossier pour les CSV')
    parser.add_argument('etats', type=Path, nargs='+', help='États instantanés A4NE de mGBA 0.10.5')
    args = parser.parse_args()
    try:
        rom, version = charger_rom(args.rom)
        if version != 'A4NE':
            raise ValueError('La ROM USA A4NE est requise.')
        if len({chemin.stem for chemin in args.etats}) != len(args.etats):
            raise ValueError('Chaque état doit avoir un nom de fichier distinct.')
        if args.destination.exists():
            raise ValueError(f'Le dossier de destination existe déjà ({args.destination}).')
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.selecteurs-', dir=args.destination.parent) as temporaire:
            lot = Path(temporaire) / 'selecteurs'
            lot.mkdir()
            total = relever(rom, args.etats, lot)
            lot.rename(args.destination)
    except (OSError, UcError, ValueError, ZlibError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print(f'A4NE · {total} choix relevés pour {len(PNJ)} sélecteurs et {len(args.etats)} états.')


if __name__ == '__main__':
    main()
