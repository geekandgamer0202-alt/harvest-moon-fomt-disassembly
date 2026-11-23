#!/usr/bin/env python3
"""Observe les écritures et les notifications de VarSet sur des états mGBA."""

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
from pathlib import Path
from struct import unpack
from tempfile import TemporaryDirectory
from zlib import error as ZlibError

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE, UcError
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2

from relever_selecteurs import IWRAM
from relever_variables import (
    BASE_EWRAM, BASE_GBA, BASE_IWRAM, EWRAM, MOTEUR, NOMBRE_VARIABLES, PARTIE,
    PILE_VIDE, POINTEUR_PARTIE, RACINE, RETOUR, SYMBOLES, charger_rom, dans_image,
    ecrire_csv, entier_signe, lire_moteur, preparer_cpu, read_state,
)
from inspecter_sauvegarde import BASES_CASES


ARGUMENTS_COMMUNS = frozenset((-2147483648, -1, 0, 1, 2, 3, 4, 7, 15, 31, 63, 127,
                              255, 256, 1023, 65535, 2147483647))
LIMITE_INSTRUCTIONS = 50000
REGISTRE = PARTIE + 0x214C
PRESENCE_ENFANT = PARTIE + 0x1CD7
MARCHE_ENFANT = PARTIE + 0x1CFE
LITTERAUX = RACINE / 'ressources/donnees/ecritures-variables/Ecritures-decomposees-FoMT.csv'
PHASES = ('ecriture', 'notification')


class Traceur:
    def __init__(self, rom, tables, etat):
        _, get, set_, notification = tables
        self.lecture = BASE_GBA + get.fonction
        self.ecriture = BASE_GBA + set_.fonction
        self.notification = BASE_GBA + notification.fonction
        self.cpu, self.registres = preparer_cpu(rom, etat)
        if unpack('<I', self.cpu.mem_read(POINTEUR_PARTIE, 4))[0] != PARTIE:
            raise ValueError('Pointeur de l’image de sauvegarde inattendu')
        self.ram = ((BASE_EWRAM, etat[EWRAM:]), (BASE_IWRAM, etat[IWRAM:EWRAM]))
        self.anciens = {}
        self.avant_notification = None
        for base, contenu in self.ram:
            self.cpu.mem_protect(base, len(contenu), UC_PROT_READ | UC_PROT_WRITE)
            self.cpu.hook_add(UC_HOOK_MEM_WRITE, self.noter_ecriture, begin=base, end=base + len(contenu) - 1)
        self.cpu.hook_add(UC_HOOK_CODE, self.commencer_notification,
                          begin=self.notification, end=self.notification)

    def restaurer(self):
        for base, contenu in self.ram:
            self.cpu.mem_write(base, contenu)

    def noter_ecriture(self, cpu, _acces, adresse, taille, _valeur, _donnees):
        # Unicorn appelle ce crochet avant l’instruction de stockage.
        for i, octet in enumerate(cpu.mem_read(adresse, taille), adresse):
            self.anciens.setdefault(i, octet)

    def changements(self):
        return {adresse: avant ^ self.cpu.mem_read(adresse, 1)[0] for adresse, avant in self.anciens.items()}

    def commencer_notification(self, _cpu, _adresse, _taille, _donnees):
        self.avant_notification = self.changements()
        self.anciens.clear()

    def appeler(self, entree, identifiant, argument=0):
        self.cpu.context_restore(self.registres)
        self.cpu.mem_write(RETOUR, PILE_VIDE)
        self.cpu.reg_write(UC_ARM_REG_R0, MOTEUR)
        self.cpu.reg_write(UC_ARM_REG_R1, identifiant)
        self.cpu.reg_write(UC_ARM_REG_R2, argument & 0xFFFFFFFF)
        self.cpu.emu_start(entree | 1, RETOUR, count=LIMITE_INSTRUCTIONS)
        pc = self.cpu.reg_read(UC_ARM_REG_PC)
        if pc != RETOUR:
            raise ValueError(f'Limite d’instructions atteinte à {pc:#010x}')
        return entier_signe(self.cpu.reg_read(UC_ARM_REG_R0))

    def lire(self, identifiant):
        return self.appeler(self.lecture, identifiant)

    def ecrire(self, identifiant, argument):
        self.avant_notification = None
        self.anciens.clear()
        self.appeler(self.ecriture, identifiant, argument)
        derniers = self.changements()
        if self.avant_notification is None:
            return 0, (derniers, {})
        return 1, (self.avant_notification, derniers)

    def registre(self):
        total, *cases = unpack('<I3H', self.cpu.mem_read(REGISTRE, 10))
        if total > len(cases):
            raise ValueError('Taille du registre d’événements inattendue')
        return cases[:total], cases


def lire_entrants():
    with SYMBOLES.open(encoding='utf-8', newline='') as fichier:
        catalogue = {int(row['id_variable']): row for row in csv.DictReader(fichier)}
    if set(catalogue) != set(range(NOMBRE_VARIABLES)):
        raise ValueError('Index des variables natives incomplet')
    litteraux = defaultdict(set)
    with LITTERAUX.open(encoding='utf-8', newline='') as fichier:
        for ligne in csv.DictReader(fichier):
            if ligne['forme'] == 'litteral':
                litteraux[int(ligne['id_variable'])].add(int(ligne['expression']))
    return catalogue, litteraux


def decrire_phase(changements):
    image = {a - PARTIE: bits for a, bits in changements.items() if dans_image(a, 1)}
    modifies = '|'.join(f'0x{a:04X}/0x{bits:02X}' for a, bits in sorted(image.items()) if bits)
    hors_image = sum(bool(bits) for a, bits in changements.items() if not dans_image(a, 1))
    return len(image), modifies, len(changements) - len(image), hors_image


def relever_contexte(traceur, contexte, catalogue, litteraux):
    for identifiant in sorted(catalogue):
        traceur.restaurer()
        avant = traceur.lire(identifiant)
        args_scripts = litteraux[identifiant]
        for argument in sorted(ARGUMENTS_COMMUNS | args_scripts | {avant}):
            traceur.restaurer()
            prefixe = (contexte, identifiant, argument, int(argument in args_scripts), avant)
            try:
                notification, changements = traceur.ecrire(identifiant, argument)
                apres = traceur.lire(identifiant)
            except (UcError, ValueError) as erreur:
                yield (*prefixe, '', 'incomplet', str(erreur), *('',) * 9), None
                continue
            traces = tuple(valeur for phase in changements for valeur in decrire_phase(phase))
            yield (*prefixe, apres, 'ok', '', notification, *traces), changements


def lister_evenements(traceur, contexte):
    traceur.restaurer()
    actifs, _ = traceur.registre()
    if not actifs and all(traceur.lire(i) == 0 for i in (196, 197, 198, 199)):
        suite = ((198, 1), (198, 1), (197, 1), (199, 1), (196, 1),
                 (198, 2), (196, 2), (196, 1), (197, 0))
    elif actifs == [198] and traceur.lire(198) == 1:
        suite = ((198, 1), (198, 2))
    else:
        return
    for etape, (identifiant, argument) in enumerate(suite, 1):
        avant = traceur.lire(identifiant)
        actifs_avant, _ = traceur.registre()
        traceur.ecrire(identifiant, argument)
        apres = traceur.lire(identifiant)
        actifs_apres, cases = traceur.registre()
        yield (contexte, etape, identifiant, argument, avant, apres,
               '|'.join(map(str, actifs_avant)), '|'.join(map(str, actifs_apres)), *cases)


def tester_marche(traceur, contexte):
    for presence, marche, argument in ((0, 0, 1), (1, 0, 0), (1, 0, -1),
                                       (1, 0, 1), (1, 1, 0), (1, 1, 1)):
        traceur.restaurer()
        for adresse, masque, actif in ((PRESENCE_ENFANT, 0x02, presence), (MARCHE_ENFANT, 0x01, marche)):
            octet = traceur.cpu.mem_read(adresse, 1)[0]
            traceur.cpu.mem_write(adresse, bytes([(octet & ~masque) | (masque * actif)]))
        avant = traceur.lire(47)
        _, (ecriture, notification) = traceur.ecrire(47, argument)
        apres = traceur.lire(47)
        yield (contexte, presence, marche, argument, avant, apres,
               decrire_phase(ecriture)[1], decrire_phase(notification)[1])


def exporter(roms, chemins, destination):
    catalogue, litteraux = lire_entrants()
    contextes, essais, registre, marche = [], [], [], []
    touches, modifies, masques = Counter(), Counter(), defaultdict(int)
    resumes = defaultdict(Counter)
    tables = {edition: lire_moteur(rom, edition) for edition, rom in roms.items()}
    for chemin in chemins:
        brut = chemin.read_bytes()
        etat, code = read_state(brut)
        edition, nom = code.decode('ascii'), chemin.stem
        traceur = Traceur(roms[edition], tables[edition], etat)
        contextes.append((nom, edition, sha256(brut).hexdigest()))
        for ligne, changements in relever_contexte(traceur, nom, catalogue, litteraux):
            essais.append(ligne)
            identifiant = ligne[1]
            resume = resumes[identifiant]
            resume['essais'] += 1
            if changements is None:
                continue
            resume['termines'] += 1
            resume['valeur_changee'] += ligne[4] != ligne[5]
            for phase, octets in zip(PHASES, changements, strict=True):
                internes = False
                for adresse, bits in octets.items():
                    if dans_image(adresse, 1):
                        interne = identifiant, phase, adresse - PARTIE
                        touches[interne] += 1
                        modifies[interne] += bool(bits)
                        masques[interne] |= bits
                        internes |= bool(bits)
                resume[f'{phase}_image'] += internes
                resume[f'{phase}_hors_image'] += any(bits and not dans_image(a, 1) for a, bits in octets.items())
        registre.extend(lister_evenements(traceur, nom))
        marche.extend(tester_marche(traceur, nom))

    ecrire_csv(destination / 'Contextes-VarSet-FoMT.csv', ('contexte', 'edition', 'sha256_etat'), contextes)
    ecrire_csv(destination / 'Essais-VarSet-FoMT.csv',
               ('contexte', 'id_variable', 'argument', 'litteral_script', 'valeur_avant', 'valeur_apres',
                'statut', 'erreur', 'bloc_notification_atteint',
                *(f'{phase}_{colonne}' for phase in PHASES for colonne in (
                    'octets_image_touches', 'bits_image_modifies', 'octets_hors_image_touches',
                    'octets_hors_image_modifies'))), essais)
    cles_resume = ('essais', 'termines', 'valeur_changee', 'ecriture_image', 'ecriture_hors_image',
                   'notification_image', 'notification_hors_image')
    ecrire_csv(destination / 'Variables-ecrites-FoMT.csv',
               ('id_variable', 'symbole', 'type_branche_ecriture', 'type_branche_notification', *cles_resume),
               ((i, entree['symbole'], entree['type_branche_ecriture'], entree['type_branche_notification'],
                 *(resumes[i][cle] for cle in cles_resume)) for i, entree in sorted(catalogue.items())))
    ecrire_csv(destination / 'Octets-ecrits-VarSet-FoMT.csv',
               ('id_variable', 'symbole', 'phase', 'offset_image', 'offset_sav_1', 'offset_sav_2',
                'essais_octet_touche', 'essais_octet_modifie', 'masque_bits_modifies'),
               ((i, catalogue[i]['symbole'], phase, f'0x{offset:04X}',
                 *(f'0x{base + 4 + offset:04X}' for base in BASES_CASES),
                 touches[i, phase, offset], modifies[i, phase, offset], f'0x{masques[i, phase, offset]:02X}')
                for i, phase, offset in sorted(touches)))
    ecrire_csv(destination / 'Registre-evenements-VarSet-FoMT.csv',
               ('contexte', 'etape', 'id_variable', 'argument', 'valeur_avant', 'valeur_apres',
                'actifs_avant', 'actifs_apres', 'case_brute_0', 'case_brute_1', 'case_brute_2'), registre)
    ecrire_csv(destination / 'Marche-enfant-VarSet-FoMT.csv',
               ('contexte', 'presence_preparee', 'marche_preparee', 'argument', 'valeur_avant', 'valeur_apres',
                'ecriture_bits_image_modifies', 'notification_bits_image_modifies'), marche)
    return len(essais), sum(resume['termines'] for resume in resumes.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('roms', type=Path, nargs=2, metavar='ROM', help='Une ROM A4NE et une ROM A4NP')
    parser.add_argument('destination', type=Path, help='Nouveau dossier pour les CSV')
    parser.add_argument('etats', type=Path, nargs='+', help='États instantanés mGBA 0.10.5')
    args = parser.parse_args()
    try:
        roms = {edition: rom for rom, edition in map(charger_rom, args.roms)}
        if set(roms) != {'A4NE', 'A4NP'}:
            raise ValueError('Les deux ROM de référence A4NE et A4NP sont requises.')
        if len({path.stem for path in args.etats}) != len(args.etats):
            raise ValueError('Chaque état doit avoir un nom de fichier distinct.')
        if args.destination.exists():
            raise ValueError(f'Le dossier de destination existe déjà ({args.destination}).')
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.varset-', dir=args.destination.parent) as temporaire:
            dossier = Path(temporaire) / 'varset'
            dossier.mkdir()
            total, termines = exporter(roms, args.etats, dossier)
            dossier.rename(args.destination)
    except (OSError, UcError, ValueError, ZlibError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print(f'{termines}/{total} couples VarSet–VarGet terminés sur {len(args.etats)} états.')


if __name__ == '__main__':
    main()
