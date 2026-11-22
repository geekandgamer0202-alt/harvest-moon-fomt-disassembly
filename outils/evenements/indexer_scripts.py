#!/usr/bin/env python3
"""Indexe les structures des scripts FoMT GBA sans exporter les dialogues."""

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
from hashlib import sha1
import json
from pathlib import Path
from struct import pack, unpack_from
import sys


BASE_GBA = 0x08000000
NOMBRE_SCRIPTS = 1328
VERSIONS = {
    'A4NE': (0x0F89D4, 'a2fc3574f0a65a4fcf7682fb274b9d7eebdef963'),
    'A4NP': (0x0F8A20, '7ba1ec1e46ce424e3c6fd72e4e8d5e9eb5ede247'),
}
LARGEURS_OPERANDE = {
    0x13: 4, 0x14: 4, 0x17: 4, 0x18: 4, 0x19: 4, 0x1A: 4,
    0x1B: 4, 0x1C: 4, 0x1D: 4, 0x1E: 4, 0x21: 4, 0x22: 2,
    0x23: 1, 0x24: 4,
}
EMPILEMENT_IMMEDIAT = {0x17, 0x22, 0x23}
APPELS = {0x037: 'CallScript', 0x089: 'SetEntityEventScript'}
QUATORZE_SCRIPTS = (3, 111, 112, 113, 114, 115, 158, 181, 340, 544, 782, 1031, 1032, 1300)


@dataclass(frozen=True)
class Bloc:
    debut: int
    fin: int


@dataclass(frozen=True)
class Script:
    identifiant: int
    case: int
    bloc: Bloc
    sections: dict
    chaines: tuple
    sauts: int
    fin_immediate: bool


def hex_rom(offset):
    return f'0x{offset:06X}'


def u32(rom, offset):
    return unpack_from('<I', rom, offset)[0]


def charger_rom(chemin):
    rom = chemin.read_bytes()
    version = rom[0xAC:0xB0].decode('ascii', errors='replace')
    if version not in VERSIONS:
        raise ValueError('Une ROM FoMT A4NE ou A4NP est requise.')
    empreinte = sha1(rom).hexdigest()
    if len(rom) != 0x800000 or empreinte != VERSIONS[version][1]:
        raise ValueError(f'La taille ou le SHA-1 de la ROM {version} diffère de la référence.')
    return rom, version


def lire_sections(rom, bloc):
    sections = {}
    offset = bloc.debut + 12
    while offset < bloc.fin:
        if offset + 8 > bloc.fin:
            raise ValueError(f'En-tête de section tronqué à {hex_rom(offset)}')
        nom = rom[offset:offset + 4]
        debut = offset + 8
        fin = debut + u32(rom, offset + 4)
        if nom in sections or fin > bloc.fin:
            raise ValueError(f'Section invalide à {hex_rom(offset)}')
        sections[nom] = Bloc(debut, fin)
        offset = fin
    if tuple(sections) not in ((b'CODE', b'STR '), (b'CODE', b'JUMP', b'STR ')):
        raise ValueError(f'Ordre des sections inattendu à {hex_rom(bloc.debut)}')
    return sections


def lire_chaines(rom, section):
    if section.debut + 4 > section.fin:
        raise ValueError(f'En-tête STR tronqué à {hex_rom(section.debut)}')
    nombre = u32(rom, section.debut)
    table = section.debut + 4
    donnees = table + nombre * 4
    if donnees > section.fin:
        raise ValueError(f'Table STR tronquée à {hex_rom(table)}')
    debuts = [donnees + u32(rom, table + index * 4) for index in range(nombre)]
    ordre = sorted(debuts)
    fins = dict(zip(ordre, ordre[1:] + [section.fin]))
    if len(fins) != nombre or any(debut >= fin for debut, fin in fins.items()):
        raise ValueError(f'Adresses STR invalides à {hex_rom(table)}')
    chaines = []
    for debut in debuts:
        fin = rom.find(b'\0', debut, fins[debut])
        if fin < 0:
            raise ValueError(f'Chaîne sans terminateur à {hex_rom(debut)}')
        chaines.append(Bloc(debut, fin))
    return tuple(chaines)


def lire_sauts(rom, section):
    if section is None:
        return 0
    if section.debut + 4 > section.fin:
        raise ValueError(f'En-tête JUMP tronqué à {hex_rom(section.debut)}')
    nombre = u32(rom, section.debut)
    table = section.debut + 4
    offset = table + nombre * 4
    if offset > section.fin:
        raise ValueError(f'Table JUMP tronquée à {hex_rom(table)}')
    for index in range(nombre):
        if table + u32(rom, table + index * 4) != offset or offset + 8 > section.fin:
            raise ValueError(f'Entrée JUMP invalide à {hex_rom(offset)}')
        offset += 8 + 8 * u32(rom, offset)
        if offset > section.fin:
            raise ValueError(f'Cas JUMP tronqués à {hex_rom(offset)}')
    if offset != section.fin:
        raise ValueError(f'Taille JUMP incohérente à {hex_rom(table)}')
    return nombre


def lire_code(rom, code):
    offset = code.debut + 4
    if offset > code.fin or offset + u32(rom, code.debut) != code.fin:
        raise ValueError(f'Taille CODE incohérente à {hex_rom(code.debut)}')
    while offset < code.fin:
        opcode = rom[offset]
        suivant = offset + 1 + LARGEURS_OPERANDE.get(opcode, 0)
        if opcode > 0x24 or suivant > code.fin:
            raise ValueError(f'Instruction inconnue ou tronquée à {hex_rom(offset)}')
        operande = int.from_bytes(rom[offset + 1:suivant], 'little', signed=opcode == 0x17)
        yield offset, opcode, operande
        offset = suivant


def indexer(rom, version):
    table, _ = VERSIONS[version]
    pointeurs = unpack_from(f'<{NOMBRE_SCRIPTS + 1}I', rom, table)
    if pointeurs[0]:
        raise ValueError('La case réservée 0000 doit être nulle.')
    adresses = [adresse - BASE_GBA for adresse in pointeurs[1:]]
    scripts, liens = [], []
    for identifiant, (debut, limite) in enumerate(zip(adresses, adresses[1:] + [len(rom)]), 1):
        if not table + len(pointeurs) * 4 <= debut <= limite - 12 or debut % 4:
            raise ValueError(f'Adresse hors limites pour le script {identifiant:04d}')
        if rom[debut:debut + 4] != b'RIFF' or rom[debut + 8:debut + 12] != b'SCR ':
            raise ValueError(f'En-tête RIFF/SCR absent à {hex_rom(debut)}')
        bloc = Bloc(debut, debut + u32(rom, debut + 4))
        if not debut + 12 <= bloc.fin <= limite:
            raise ValueError(f'Taille RIFF incohérente à {hex_rom(debut)}')
        sections = lire_sections(rom, bloc)
        chaines = lire_chaines(rom, sections[b'STR '])
        sauts = lire_sauts(rom, sections.get(b'JUMP'))
        precedent = None
        for offset, opcode, operande in lire_code(rom, sections[b'CODE']):
            if opcode == 0x21 and operande in APPELS:
                if precedent is None or precedent[1] not in EMPILEMENT_IMMEDIAT or not 1 <= precedent[2] <= NOMBRE_SCRIPTS:
                    raise ValueError(f'Cible statique non reconnue à {hex_rom(offset)}')
                liens.append((identifiant, precedent[2], operande, offset))
            precedent = offset, opcode, operande
        if precedent is None:
            raise ValueError(f'Bloc CODE vide à {hex_rom(debut)}')
        fin_immediate = not chaines and rom[sections[b'CODE'].debut + 4] == 0x20
        scripts.append(Script(identifiant, table + identifiant * 4, bloc, sections, chaines, sauts, fin_immediate))
    return scripts, liens


def ecrire_scripts(scripts):
    output = csv.writer(sys.stdout, lineterminator='\n')
    output.writerow(('script', 'case_rom', 'bloc_rom', 'code_rom', 'octets_code',
                     'tables_saut', 'chaines_str', 'fin_immediate_sans_chaine'))
    for script in scripts:
        code = script.sections[b'CODE']
        output.writerow((f'{script.identifiant:04d}', hex_rom(script.case), hex_rom(script.bloc.debut),
                         hex_rom(code.debut + 4), code.fin - code.debut - 4,
                         script.sauts, len(script.chaines), int(script.fin_immediate)))


def ecrire_liens(liens):
    output = csv.writer(sys.stdout, lineterminator='\n')
    output.writerow(('origine', 'cible', 'appel_natif', 'id_appel_natif', 'instruction_rom'))
    for source, cible, appel, offset in liens:
        output.writerow((f'{source:04d}', f'{cible:04d}', APPELS[appel], f'0x{appel:03X}', hex_rom(offset)))


def occurrences_pointeur(rom, offset):
    motif = pack('<I', BASE_GBA + offset)
    position = rom.find(motif)
    while position >= 0:
        yield hex_rom(position)
        position = rom.find(motif, position + 1)


def audit_quatorze(rom, version, scripts, liens):
    audit = {}
    for identifiant in QUATORZE_SCRIPTS:
        script = scripts[identifiant - 1]
        audit[f'{identifiant:04d}'] = {
            'case_rom': hex_rom(script.case),
            'bloc_rom': hex_rom(script.bloc.debut),
            'code_rom': hex_rom(script.sections[b'CODE'].debut + 4),
            'pointeurs_litteraux_vers_bloc': list(occurrences_pointeur(rom, script.bloc.debut)),
            'pointeurs_litteraux_vers_case': list(occurrences_pointeur(rom, script.case)),
            'instructions_vm_entrantes': [hex_rom(offset) for _, cible, _, offset in liens if cible == identifiant],
        }
    return {'version': version, 'sha1': VERSIONS[version][1], 'scripts': audit}


def compare(rom, scripts, autre_rom, autres_scripts):
    changements_sections = {}
    changements_chaines = []
    for script, autre in zip(scripts, autres_scripts):
        sections = {nom: rom[bloc.debut:bloc.fin] for nom, bloc in script.sections.items()}
        autres_sections = {nom: autre_rom[bloc.debut:bloc.fin] for nom, bloc in autre.sections.items()}
        changement = sorted(nom.decode('ascii').strip() for nom in sections.keys() | autres_sections.keys()
                            if sections.get(nom) != autres_sections.get(nom))
        identifiant = f'{script.identifiant:04d}'
        if changement:
            changements_sections[identifiant] = changement
        for slot in range(max(len(script.chaines), len(autre.chaines))):
            if slot >= min(len(script.chaines), len(autre.chaines)):
                changements_chaines.append(f'{identifiant}.{slot:02d}')
                continue
            a, b = script.chaines[slot], autre.chaines[slot]
            if rom[a.debut:a.fin] != autre_rom[b.debut:b.fin]:
                changements_chaines.append(f'{identifiant}.{slot:02d}')
    deltas = Counter(a.bloc.debut - b.bloc.debut for a, b in zip(scripts, autres_scripts))
    return {'sections_differentes': changements_sections, 'chaines_differentes': changements_chaines,
            'deltas_offsets_blocs': deltas}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--appels', action='store_true', help='Émettre les sites d’appel au format CSV')
    action.add_argument('--audit-quatorze', action='store_true', help='Vérifier les références aux quatorze scripts étudiés')
    action.add_argument('--comparer', type=Path, help='Comparer les blocs à la ROM de l’autre région')
    args = parser.parse_args()
    try:
        rom, version = charger_rom(args.rom)
        scripts, liens = indexer(rom, version)
        if args.comparer:
            autre_rom, autre_version = charger_rom(args.comparer)
            if autre_version == version:
                raise ValueError('La comparaison requiert une ROM de chaque région.')
            autres_scripts, _ = indexer(autre_rom, autre_version)
            rapport = compare(rom, scripts, autre_rom, autres_scripts)
            print(json.dumps({'ordre': [version, autre_version], **rapport}, ensure_ascii=False, indent=2))
        elif args.audit_quatorze:
            print(json.dumps(audit_quatorze(rom, version, scripts, liens), ensure_ascii=False, indent=2))
        elif args.appels:
            ecrire_liens(liens)
        else:
            ecrire_scripts(scripts)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
