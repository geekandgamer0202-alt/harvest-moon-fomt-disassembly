#!/usr/bin/env python3
"""Rejoue les opérations natives du pool de banques OBJ, des deux côtés d’une image."""

import argparse
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from zlib import error as ZlibError

from unicorn import UC_HOOK_CODE, UcError
from unicorn.arm_const import (
    UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R8, UC_ARM_REG_R9,
    UC_ARM_REG_R10, UC_ARM_REG_SP,
)

from relever_palettes_obj import NOMBRE_RESSOURCES, TAILLE_RESSOURCE, PaletteMonde
from relever_variables import BASE_GBA, PILE_VIDE, RETOUR, charger_rom, ecrire_csv, entier_signe, read_state
from exporter_routines_natives import cible_bl


TAILLE_CACHE = 0xC18
DEBUT_POOL = 0xB78
TAILLE_CASE = 12
NOMBRE_CASES = 13
UTILISEES = 0xC14
PRECEDENTES = 0xC15
PREMIERE_CASE_RESSOURCE = 0x20 + 0x80


class CycleBanques:
    def __init__(self, monde, rom, edition):
        self.cpu, self.monde, self.registres = monde.cpu, monde.monde, monde.registres
        self.cache = monde.ressources - 0x20
        vtable = monde.mot(self.monde)
        self.lire = monde.mot(vtable + 0x50) & ~1
        draw = monde.mot(vtable + 0x10) & ~1
        self.decalage = draw - 0x080182C8
        if self.decalage != (0 if edition == 'A4NE' else 0x14):
            raise ValueError(f'Adresse Draw inattendue ({draw:#010x})')
        self.acquerir = BASE_GBA + cible_bl(rom, self.lire - BASE_GBA + 0x16)
        self.acquisitions = 0
        self.cpu.hook_add(UC_HOOK_CODE, self.noter_acquisition, begin=self.acquerir, end=self.acquerir)
        self.original = bytes(self.cpu.mem_read(self.cache, TAILLE_CACHE))

    def noter_acquisition(self, _cpu, _pc, _taille, _donnees):
        self.acquisitions += 1

    def initialiser(self):
        cache = bytearray(self.original)
        cache[:32] = bytes(32)
        cache[PREMIERE_CASE_RESSOURCE:DEBUT_POOL:TAILLE_RESSOURCE] = bytes([0xFF]) * NOMBRE_RESSOURCES
        cache[DEBUT_POOL + 9:UTILISEES:TAILLE_CASE] = bytes([0xFF]) * NOMBRE_CASES
        cache[DEBUT_POOL + 10:UTILISEES:TAILLE_CASE] = bytes(NOMBRE_CASES)
        cache[UTILISEES:PRECEDENTES + 1] = b'\0\0'
        self.cpu.mem_write(self.cache, bytes(cache))
        self.cpu.mem_write(RETOUR, PILE_VIDE)

    def executer(self, entree, fin, registres):
        self.cpu.context_restore(self.registres)
        self.acquisitions = 0
        for registre, valeur in registres:
            self.cpu.reg_write(registre, valeur)
        self.cpu.emu_start(entree | 1, fin, count=4096)
        if self.cpu.reg_read(UC_ARM_REG_PC) != fin:
            raise ValueError(f'Fin inattendue du code Thumb à {entree:#010x}')
        return entier_signe(self.cpu.reg_read(UC_ARM_REG_R0))

    def fragment(self, debut, fin, registres=()):
        cadre_draw = ((UC_ARM_REG_SP, RETOUR + 0x200), (UC_ARM_REG_R9, self.monde))
        self.executer(debut + self.decalage, fin + self.decalage, (*cadre_draw, *registres))

    def debut_image(self):
        self.fragment(0x080182DE, 0x080182FE)
        self.fragment(0x08018362, 0x080183C6)

    def fin_image(self):
        self.fragment(0x08019B10, 0x08019B56)

    def demander(self, ressource, direct=False):
        self.cpu.mem_write(RETOUR + 0x1000, bytes(0x1000))
        entree, objet = (self.acquerir, self.cache) if direct else (self.lire, self.monde)
        return self.executer(entree, RETOUR, ((UC_ARM_REG_R0, objet), (UC_ARM_REG_R1, ressource)))

    def valider_mise_en_file(self, ressource):
        adresse_case = self.cache + PREMIERE_CASE_RESSOURCE + ressource * TAILLE_RESSOURCE
        case = self.cpu.mem_read(adresse_case, 1)[0]
        if case >= NOMBRE_CASES:
            raise ValueError('La ressource doit avoir une banque avant la mise en file')
        self.fragment(0x08019ADE, 0x08019AF8,
                      ((UC_ARM_REG_R8, adresse_case + 2),
                       (UC_ARM_REG_R10, self.cache + DEBUT_POOL + case * TAILLE_CASE)))

    def relever(self, ressource):
        cache = self.cpu.mem_read(self.cache, TAILLE_CACHE)
        memo = case = ''
        if ressource is not None:
            memo = cache[ressource]
            case = signe_octet(cache[PREMIERE_CASE_RESSOURCE + ressource * TAILLE_RESSOURCE])
        ids = cache[DEBUT_POOL + 9:UTILISEES:TAILLE_CASE]
        valides = cache[DEBUT_POOL + 10:UTILISEES:TAILLE_CASE]
        banques = cache[DEBUT_POOL + 8:UTILISEES:TAILLE_CASE]
        return (cache[UTILISEES], cache[PRECEDENTES], memo, case,
                '|'.join(str(signe_octet(i)) for i in ids), '|'.join(map(str, valides)),
                '|'.join(map(str, banques)))


def signe_octet(valeur):
    return (valeur & 127) - (valeur & 128)


def essais(cycle):
    sequences = {
        'saturation': [('debut', None), *(('demander', r) for r in range(NOMBRE_CASES)),
                       ('demander', 13), ('demander', 13), ('demander', 0), ('acquerir', 0),
                       ('fin', None), ('debut', None), ('demander', 13)],
        'reutilisation': [('debut', None), ('demander', 4), ('valider_envoi', 4),
                          ('demander', 7), ('valider_envoi', 7), ('demander', 1), ('valider_envoi', 1),
                          ('fin', None), ('debut', None), ('demander', 4), ('demander', 1),
                          ('valider_envoi', 1), ('fin', None)],
    }
    for nom, operations in sequences.items():
        cycle.initialiser()
        for etape, (operation, ressource) in enumerate(operations, 1):
            avant = cycle.relever(ressource)
            retour = ''
            if operation in ('demander', 'acquerir'):
                retour = cycle.demander(ressource, direct=operation == 'acquerir')
            elif operation == 'valider_envoi':
                cycle.valider_mise_en_file(ressource)
            elif operation == 'debut':
                cycle.debut_image()
            else:
                cycle.fin_image()
            apres = cycle.relever(ressource)
            yield nom, etape, operation, ressource, retour, cycle.acquisitions, *avant, *apres


def exporter(roms, fichiers, dossier):
    contextes, lignes = [], []
    reference = None
    for fichier in fichiers:
        brut = fichier.read_bytes()
        etat, code = read_state(brut)
        edition = code.decode('ascii')
        rom = roms[edition]
        monde = PaletteMonde(rom, edition, etat)
        cycle = CycleBanques(monde, rom, edition)
        resultats = list(essais(cycle))
        if reference is not None and resultats != reference:
            raise ValueError('Le cycle du pool diffère entre les deux états')
        reference = resultats
        contextes.append((fichier.stem, edition, sha256(brut).hexdigest(), f'0x{cycle.cache:08X}',
                          f'0x{cycle.lire:08X}', f'0x{cycle.acquerir:08X}'))
        lignes.extend((edition, *resultat) for resultat in resultats)

    ecrire_csv(dossier / 'Contextes-pool-OBJ-FoMT.csv',
               ('contexte', 'edition', 'sha256_etat', 'cache_gba', 'get_bank_gba', 'acquire_bank_gba'), contextes)
    champs = ('utilisees', 'precedentes', 'memo', 'case_ressource', 'ressources_pool', 'validite_pool', 'banques_pool')
    ecrire_csv(dossier / 'Cycle-pool-OBJ-FoMT.csv',
               ('edition', 'scenario', 'etape', 'operation', 'ressource', 'banque_retour', 'appels_acquire',
                *(f'{champ}_{moment}' for moment in ('avant', 'apres') for champ in champs)), lignes)
    return len(lignes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('roms', nargs=2, type=Path, metavar='ROM')
    parser.add_argument('destination', type=Path)
    parser.add_argument('etats', nargs=2, type=Path, metavar='ÉTAT')
    args = parser.parse_args()
    try:
        roms = {ed: rom for rom, ed in map(charger_rom, args.roms)}
        editions = {read_state(p.read_bytes())[1].decode() for p in args.etats}
        if set(roms) != {'A4NE', 'A4NP'} or editions != set(roms):
            raise ValueError('Une ROM et un état de jeu de chaque édition A4NE et A4NP sont requis.')
        if args.destination.exists():
            raise ValueError(f'Le dossier de destination existe déjà ({args.destination}).')
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.banques-obj-', dir=args.destination.parent) as temporaire:
            dossier = Path(temporaire) / 'banques-obj'
            dossier.mkdir()
            total = exporter(roms, args.etats, dossier)
            dossier.rename(args.destination)
    except (OSError, UcError, ValueError, ZlibError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print(f'{total} opérations du pool OBJ vérifiées sur les deux éditions.')


if __name__ == '__main__':
    main()
