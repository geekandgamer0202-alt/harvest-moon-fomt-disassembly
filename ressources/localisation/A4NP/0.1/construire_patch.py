#!/usr/bin/env python3
"""Build the BPS localization patch for the European GBA release."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib


def checked_bytes(rom, offset, expected, label):
    actual = rom[offset:offset + len(expected)]
    if offset < 0 or actual != expected:
        raise ValueError(f'{label} à {offset:#08x} : octets d’origine différents')


def build_changes(rom, manifest):
    changes = [(int(glyph['offset'], 0), bytes.fromhex(glyph['hex']))
               for glyph in manifest['glyphes']]
    characters = {letter: bytes.fromhex(value)
                  for letter, value in manifest['caracteres'].items()}
    free = int(manifest['zone_libre'], 0)
    for entry in manifest['textes']:
        label = entry['id']
        offset = int(entry['offset'], 0)
        ending = bytes.fromhex(entry.get('fin_hex', '00'))
        size = entry['taille']
        original = entry['original'].encode('ascii') + ending
        translated = b''.join(characters[letter] if letter in characters
                              else letter.encode('ascii') for letter in entry['fr']) + ending
        if size < len(original):
            raise ValueError(f'{label} : emplacement original trop court')
        checked_bytes(rom, offset, original.ljust(size, b'\x00'), label)

        if len(translated) <= size:
            changes.append((offset, translated.ljust(size, b'\x00')))
            continue

        # Longer text is moved only when a verified ROM pointer can be updated.
        if 'pointeur' not in entry:
            raise ValueError(f'{label} : traduction trop longue ({len(translated)} > {size})')
        pointer = int(entry['pointeur'], 0)
        checked_bytes(rom, pointer, struct.pack('<I', 0x08000000 + offset), label)
        checked_bytes(rom, free, b'\xff' * len(translated), label)
        changes.append((pointer, struct.pack('<I', 0x08000000 + free)))
        changes.append((free, translated))
        free = (free + len(translated) + 3) & ~3

    return sorted(changes)


def bps_number(value):
    encoded = bytearray()
    while value >= 128:
        encoded.append(value & 127)
        value = (value >> 7) - 1
    encoded.append(value | 128)
    return encoded


def make_bps(source, changes):
    patch = bytearray(b'BPS1')
    patch.extend(bps_number(len(source)))
    patch.extend(bps_number(len(source)))
    patch.extend(bps_number(0))
    target = bytearray(source)
    cursor = 0
    for offset, replacement in changes:
        if offset < cursor or offset + len(replacement) > len(source):
            raise ValueError(f'Plage modifiée invalide ou en double à {offset:#08x}')
        if offset > cursor:
            patch.extend(bps_number((offset - cursor - 1) << 2))
        patch.extend(bps_number(((len(replacement) - 1) << 2) | 1))
        patch.extend(replacement)
        cursor = offset + len(replacement)
        target[offset:cursor] = replacement
    if cursor < len(source):
        patch.extend(bps_number((len(source) - cursor - 1) << 2))

    patch.extend(struct.pack('<II', zlib.crc32(source), zlib.crc32(target)))
    patch.extend(struct.pack('<I', zlib.crc32(patch)))
    return patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path, help='ROM européenne A4NP extraite de son ZIP')
    parser.add_argument('-o', '--output', type=Path, required=True, help='Fichier .bps à créer')
    parser.add_argument('--textes', type=Path, default=Path(__file__).with_name('textes.json'))
    args = parser.parse_args()
    if args.output.suffix.lower() != '.bps' or args.output.resolve() == args.rom.resolve():
        parser.error('Le fichier de sortie doit être un .bps distinct de la ROM.')

    try:
        source = args.rom.read_bytes()
        manifest = json.loads(args.textes.read_text(encoding='utf-8'))
        if hashlib.sha1(source).hexdigest() != manifest['sha1_rom']:
            raise ValueError('Empreinte ROM incorrecte. La version A4NP d’origine est requise.')
        changes = build_changes(source, manifest)
        patch = make_bps(source, changes)
        args.output.write_bytes(patch)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'{error}\n')
    print(f'{args.output} — {len(manifest["textes"])} libellés, {len(patch)} octets')


if __name__ == '__main__':
    main()
