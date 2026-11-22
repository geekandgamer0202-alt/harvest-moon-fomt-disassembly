"""Vérifie l’en-tête et les empreintes d’une ROM GBA ou d’une archive ZIP locale."""

import argparse
from hashlib import sha1
import json
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from zlib import crc32


VERSIONS = {
    'A4NP': ('Friends of Mineral Town (Europe)', '7ba1ec1e46ce424e3c6fd72e4e8d5e9eb5ede247'),
    'A4NE': ('Friends of Mineral Town (USA)', 'a2fc3574f0a65a4fcf7682fb274b9d7eebdef963'),
    'BFGE': ('More Friends of Mineral Town (USA)', '3aa4d46cbbf152e440942acd5f5d37ddc7b05e1d'),
}


def lire_rom(source):
    if source.suffix.lower() != '.zip':
        return source.read_bytes(), None
    with ZipFile(source) as archive:
        membres = [fichier for fichier in archive.infolist() if fichier.filename.lower().endswith('.gba')]
        if len(membres) != 1:
            raise ValueError('Le ZIP doit contenir exactement un fichier .gba.')
        return archive.read(membres[0]), membres[0].filename


def identifier(rom):
    if len(rom) < 0xC0 or rom[0xB2] != 0x96:
        raise ValueError('En-tête GBA incomplet ou octet fixe 0x96 absent.')
    complement = (-sum(rom[0xA0:0xBD]) - 0x19) & 0xFF
    if rom[0xBD] != complement:
        raise ValueError('Somme de contrôle de l’en-tête GBA incorrecte.')

    titre = rom[0xA0:0xAC].rstrip(b'\0').decode('ascii', errors='replace')
    code = rom[0xAC:0xB0].decode('ascii', errors='replace')
    empreinte = sha1(rom).hexdigest()
    reference = VERSIONS.get(code)
    return {
        'titre_entete': titre,
        'code_rom': code,
        'revision_entete': rom[0xBC],
        'octets': len(rom),
        'crc32': f'{crc32(rom):08X}',
        'sha1': empreinte,
        'edition_reference': reference[0] if reference else None,
        'sha1_reference': reference[1] if reference else None,
        'sha1_confirme': empreinte == reference[1] if reference else False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='fichier .gba ou ZIP contenant une seule ROM GBA')
    args = parser.parse_args()
    try:
        rom, membre = lire_rom(args.source)
        resultat = identifier(rom)
    except (OSError, ValueError, BadZipFile, RuntimeError) as erreur:
        parser.error(str(erreur))
    if membre is not None:
        resultat['membre_zip'] = membre
    print(json.dumps(resultat, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
