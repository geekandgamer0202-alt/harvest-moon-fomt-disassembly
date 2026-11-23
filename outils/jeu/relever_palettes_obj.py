#!/usr/bin/env python3
"""Relève la sélection des ressources OBJ du monde FoMT dans les deux ROM."""

import argparse
from hashlib import sha256
from itertools import groupby
from pathlib import Path
from struct import pack, unpack
from tempfile import TemporaryDirectory
from zlib import error as ZlibError

from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_WRITE, UcError
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R5

from relever_variables import (
    BASE_EWRAM, BASE_GBA, MOTEUR, PARTIE, PILE_VIDE, RETOUR,
    charger_rom, ecrire_csv, preparer_cpu, read_state,
)


ENTREES = {'A4NE': 0x01B5C0, 'A4NP': 0x01B5D4}
CARTES = range(0x0234)
TYPES = range(34)
TAILLE_RESSOURCE = 0x84
NOMBRE_RESSOURCES = 22
FLAG_OCCUPE = 0x81


class PaletteMonde:
    def __init__(self, rom, edition, etat):
        self.cpu, self.registres = preparer_cpu(rom, etat)
        self.cpu.mem_protect(BASE_EWRAM, 0x40000, UC_PROT_READ | UC_PROT_WRITE)
        self.entree = BASE_GBA + ENTREES[edition]
        scene = self.mot(MOTEUR + 0x354)
        self.monde = self.mot(self.mot(scene + 4) + 0xA8)
        vtable = self.mot(self.monde)
        if self.mot(vtable + 0x48) & ~1 != self.entree or self.mot(self.monde + 0x1038) != PARTIE:
            raise ValueError('Un GameSceneWorld actif est requis dans l’état fourni')
        self.carte = self.mot(self.monde + 4)
        self.ressources = self.monde + 0x19C + 0x20
        self.cache = bytes(self.cpu.mem_read(self.ressources, TAILLE_RESSOURCE * NOMBRE_RESSOURCES))
        self.cache_vide = self.cache_prepare(())
        self.depart = None
        recherche = self.entree + (0x01B9BC - 0x01B5C0)
        self.cpu.hook_add(UC_HOOK_CODE, self.noter_depart, begin=recherche, end=recherche)

    def mot(self, adresse):
        return unpack('<I', self.cpu.mem_read(adresse, 4))[0]

    def cache_prepare(self, occupees):
        contenu = bytearray(self.cache)
        contenu[FLAG_OCCUPE::TAILLE_RESSOURCE] = bytes(i in occupees for i in range(NOMBRE_RESSOURCES))
        return bytes(contenu)

    def noter_depart(self, cpu, _adresse, _taille, _donnees):
        self.depart = cpu.reg_read(UC_ARM_REG_R5)

    def regler(self, carte, romance=0xFFFF, registre=None, cafe=0, etoiles=0):
        self.cpu.mem_write(self.carte, pack('<I', carte))
        self.cpu.mem_write(PARTIE + 0x2158, pack('<H', romance))
        self.cpu.mem_write(PARTIE + 0x214C, pack('<IH', int(registre is not None), registre or 0))
        mot, = unpack('<H', self.cpu.mem_read(PARTIE + 0x2182, 2))
        self.cpu.mem_write(PARTIE + 0x2182, pack('<H', (mot & ~0x0180) | cafe << 7))
        octet = self.cpu.mem_read(PARTIE + 0x218E, 1)[0]
        self.cpu.mem_write(PARTIE + 0x218E, bytes([(octet & ~0x18) | etoiles << 3]))

    def choisir(self, type_, cache=None):
        cache = self.cache_vide if cache is None else cache
        self.cpu.mem_write(self.ressources, cache)
        self.cpu.mem_write(RETOUR, PILE_VIDE)
        self.cpu.context_restore(self.registres)
        self.cpu.reg_write(UC_ARM_REG_R0, self.monde)
        self.cpu.reg_write(UC_ARM_REG_R1, type_ & 0xFFFFFFFF)
        self.depart = None
        self.cpu.emu_start(self.entree | 1, RETOUR, count=1024)
        resultat = self.cpu.reg_read(UC_ARM_REG_R0)
        if self.cpu.reg_read(UC_ARM_REG_PC) != RETOUR or not 0 <= resultat < NOMBRE_RESSOURCES:
            raise ValueError('Retour inattendu de la sélection OBJ')
        flags = self.cpu.mem_read(self.ressources, len(cache))[FLAG_OCCUPE::TAILLE_RESSOURCE]
        modifies = tuple(i for i, (avant, apres) in enumerate(zip(cache[FLAG_OCCUPE::TAILLE_RESSOURCE], flags,
                                                                strict=True)) if avant != apres)
        mode = 'fixe' if self.depart is None else 'recherche'
        debut = resultat if self.depart is None else self.depart
        return mode, debut, resultat, modifies


def mesurer(monde):
    regles = []
    for carte in CARTES:
        monde.regler(carte)
        regles.append(tuple(monde.choisir(type_) for type_ in TYPES))

    variantes = []
    for carte, scenarios in ((0x0C, (('temoin', {}), ('mariage_deesse', {'romance': 371}),
                                    ('registre_371', {'registre': 371}), ('romance_74', {'romance': 74}))),
                             (0x24, tuple((f'cafe_{v}', {'cafe': v}) for v in range(4))),
                             (8, tuple((f'etoiles_{v}', {'etoiles': v}) for v in range(4)))):
        for nom, reglages in scenarios:
            monde.regler(carte, **reglages)
            for type_ in TYPES:
                variations = monde.choisir(type_)
                variantes.append((carte, nom, type_, *variations))

    monde.regler(0x0C, romance=371)
    remplissage = [(nom, type_, presentes, monde.choisir(type_, monde.cache_prepare(presentes)))
                   for nom, type_, presentes in (
                       ('partage_fixe', 19, (6,)), ('trou', 33, (9, 10, 12)),
                       ('derniere_libre', 33, tuple(range(9, 21))),
                       ('sature', 33, tuple(range(9, 22))))]
    return regles, variantes, remplissage


def delimites(regles):
    for type_ in TYPES:
        debut = 0
        for mesure, groupe in groupby(regles, key=lambda cases: cases[type_]):
            nombre = sum(1 for _ in groupe)
            yield (f'0x{debut:04X}', f'0x{debut + nombre - 1:04X}', type_, *mesure[:3])
            debut += nombre


def exporter(roms, chemins, dossier):
    contextes, resultats = [], []
    for chemin in chemins:
        brut = chemin.read_bytes()
        etat, code = read_state(brut)
        edition = code.decode('ascii')
        monde = PaletteMonde(roms[edition], edition, etat)
        resultats.append(mesurer(monde))
        contextes.append((chemin.stem, edition, sha256(brut).hexdigest(), f'0x{monde.entree:08X}',
                          f'0x{monde.monde:08X}', f'0x{monde.carte:08X}'))
    if any(mesures != resultats[0] for mesures in resultats[1:]):
        raise ValueError('Allocation différente entre les contextes testés')
    regles, variantes, remplissage = resultats[0]
    ecrire_csv(dossier / 'Contextes-OBJ-FoMT.csv',
               ('contexte', 'edition', 'sha256_etat', 'routine_gba', 'monde_gba', 'carte_gba'), contextes)
    ecrire_csv(dossier / 'Allocation-OBJ-FoMT.csv',
               ('carte_debut', 'carte_fin', 'type_palette', 'mode', 'premiere_ressource', 'resultat_cache_vide'),
               delimites(regles))
    ecrire_csv(dossier / 'Variantes-OBJ-FoMT.csv',
               ('carte', 'variante', 'type_palette', 'mode', 'premiere_ressource', 'resultat_cache_vide'),
               ((f'0x{carte:04X}', nom, type_, mode, debut, resultat)
                for carte, nom, type_, mode, debut, resultat, _ in variantes))
    ecrire_csv(dossier / 'Cache-OBJ-FoMT.csv',
               ('variante', 'type_palette', 'ressources_occupees_avant', 'mode', 'premiere_ressource',
                'resultat', 'flags_modifies'),
               ((nom, type_, '|'.join(map(str, occupees)), mode, debut, resultat, '|'.join(map(str, modifies)))
                for nom, type_, occupees, (mode, debut, resultat, modifies) in remplissage))
    return len(resultats) * (len(CARTES) * len(TYPES) + len(variantes) + len(remplissage))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('roms', nargs=2, type=Path, metavar='ROM')
    parser.add_argument('destination', type=Path, help='Nouveau dossier pour les CSV')
    parser.add_argument('etats', type=Path, nargs=2, metavar='ÉTAT', help='Un état de jeu actif par édition')
    args = parser.parse_args()
    try:
        roms = {ed: rom for rom, ed in map(charger_rom, args.roms)}
        if set(roms) != set(ENTREES) or {read_state(p.read_bytes())[1].decode() for p in args.etats} != set(ENTREES):
            raise ValueError('Une ROM et un état de chaque édition A4NE et A4NP sont requis.')
        if args.destination.exists():
            raise ValueError(f'Le dossier de destination existe déjà ({args.destination}).')
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.palettes-obj-', dir=args.destination.parent) as temporaire:
            dossier = Path(temporaire) / 'palettes-obj'
            dossier.mkdir()
            total = exporter(roms, args.etats, dossier)
            dossier.rename(args.destination)
    except (OSError, UcError, ValueError, ZlibError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print(f'{total} sélections OBJ concordantes sur les deux éditions.')


if __name__ == '__main__':
    main()
