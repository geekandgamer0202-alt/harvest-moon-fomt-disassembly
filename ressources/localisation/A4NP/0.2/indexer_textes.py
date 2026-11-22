#!/usr/bin/env python3
"""Indexe les emplacements des textes des événements dans la ROM A4NP."""

import argparse
import csv
from hashlib import sha1
import json
from pathlib import Path
from struct import unpack_from


ROM_SHA1 = '7ba1ec1e46ce424e3c6fd72e4e8d5e9eb5ede247'
ROM_BASE = 0x08000000
SCRIPT_TABLE = 0x0F8A20
SCRIPT_COUNT = 1328


def read_u32(rom, offset):
    return unpack_from('<I', rom, offset)[0]


def read_chunks(rom, start, limit):
    end = start + read_u32(rom, start + 4)
    if rom[start:start + 4] != b'RIFF' or rom[start + 8:start + 12] != b'SCR ':
        raise ValueError(f'En-tête de script invalide à {start:#08x}')
    if not start + 12 <= end <= limit:
        raise ValueError(f'Taille de script invalide à {start:#08x}')

    chunks = {}
    offset = start + 12
    while offset < end:
        if offset + 8 > end:
            raise ValueError(f'En-tête de bloc incomplet à {offset:#08x}')
        tag = rom[offset:offset + 4]
        payload = offset + 8
        next_offset = payload + read_u32(rom, offset + 4)
        if next_offset > end or tag in chunks:
            raise ValueError(f'Bloc de script invalide à {offset:#08x}')
        chunks[tag] = (payload, next_offset)
        offset = next_offset

    if tuple(chunks) not in ((b'CODE', b'STR '), (b'CODE', b'JUMP', b'STR ')):
        raise ValueError(f'Blocs inattendus à {start:#08x}')
    return chunks


def index_texts(rom):
    pointers = unpack_from(f'<{SCRIPT_COUNT + 1}I', rom, SCRIPT_TABLE)
    if pointers[0] != 0:
        raise ValueError('Le premier pointeur doit être nul')
    offsets = [pointer - ROM_BASE for pointer in pointers[1:]]
    limits = offsets[1:] + [len(rom)]

    for script_id, (start, limit) in enumerate(zip(offsets, limits), 1):
        if start < SCRIPT_TABLE or start % 4 or start + 12 > limit or limit > len(rom):
            raise ValueError(f'Pointeur invalide pour le script {script_id}')
        chunks = read_chunks(rom, start, limit)
        index, end = chunks[b'STR ']
        if index + 4 > end:
            raise ValueError(f'Table STR incomplète pour le script {script_id}')
        count = read_u32(rom, index)
        pool = index + 4 * (count + 1)
        if pool > end:
            raise ValueError(f'Table STR invalide pour le script {script_id}')

        starts = [pool + read_u32(rom, index + 4 * (slot + 1)) for slot in range(count)]
        physical_order = sorted(starts)
        bounds = dict(zip(physical_order, physical_order[1:] + [end]))
        if len(bounds) != count or any(begin >= stop for begin, stop in bounds.items()):
            raise ValueError(f'Offsets STR invalides pour le script {script_id}')
        for slot, text_offset in enumerate(starts):
            stop = rom.find(b'\x00', text_offset, bounds[text_offset])
            if stop < 0:
                raise ValueError(f'Chaîne sans terminaison dans le script {script_id}, entrée {slot}')
            yield (f'{script_id:04d}.{slot:02d}', script_id, slot, f'0x{start:06X}',
                   f'0x{text_offset:06X}', stop - text_offset, '')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path, help='Fichier .gba européen A4NP d’origine')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('-o', '--output', type=Path, help='Catalogue CSV à créer')
    mode.add_argument('--entree', metavar='ID', help='Inspecter une chaîne, par exemple 0162.00')
    args = parser.parse_args()
    if args.output and (args.output.suffix.lower() != '.csv' or args.output.resolve() == args.rom.resolve()):
        parser.error('La sortie doit être un fichier .csv distinct de la ROM.')

    try:
        rom = args.rom.read_bytes()
        if sha1(rom).hexdigest() != ROM_SHA1:
            raise ValueError('Empreinte ROM incorrecte. La version A4NP d’origine est requise.')
        if args.entree is not None:
            entry = next((row for row in index_texts(rom) if row[0] == args.entree), None)
            if entry is None:
                raise ValueError(f'Entrée introuvable : {args.entree}')
            start = int(entry[4], 16)
            raw = rom[start:start + entry[5]]
            print(json.dumps({'id': entry[0], 'offset': entry[4], 'octets': entry[5],
                              'apercu': raw.decode('shift_jis', errors='backslashreplace')},
                             ensure_ascii=False, indent=2))
            return

        entries = list(index_texts(rom))
        with args.output.open('w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(('id', 'script', 'chaine', 'offset_bloc', 'offset_texte', 'octets', 'fr'))
            writer.writerows(entries)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(f'{SCRIPT_COUNT} scripts vérifiés, {len(entries)} chaînes indexées dans {args.output}')


if __name__ == '__main__':
    main()
