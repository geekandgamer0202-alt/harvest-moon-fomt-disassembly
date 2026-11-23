"""Prépare une copie de l’état mGBA du coucher pour vérifier la cérémonie 0848."""

import argparse
from pathlib import Path
from struct import unpack_from
from zlib import error as ZlibError

from inspecter_etat import EWRAM, read_state
from preparer_karen import SAVE_IN_EWRAM, SLEEP_CONTEXTS, reconstruire


IMAGE = EWRAM + SAVE_IN_EWRAM


def preparer(brut):
    etat, edition = read_state(brut)
    if unpack_from('<III', etat, EWRAM + 0x207C) != SLEEP_CONTEXTS[edition]:
        raise ValueError('État 0342 attendu à la confirmation du sommeil (PC 0x50)')
    if etat[IMAGE + 0x10:IMAGE + 0x12] != b'\x01\x04':
        raise ValueError('L’état doit dater du 2 printemps, an 1')
    if etat[IMAGE + 0x1FCE] & 7 or etat[IMAGE + 0x1D00:IMAGE + 0x1D02] != b'\0\0':
        raise ValueError('Progression romantique de la Déesse ou date de mariage déjà renseignée')
    copie = bytearray(etat)
    copie[IMAGE + 0x1FCE] |= 5
    copie[IMAGE + 0x1D00:IMAGE + 0x1D02] = b'\x01\x08'
    return reconstruire(brut, copie)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path, help='Nouveau fichier à créer')
    args = parser.parse_args()
    try:
        resultat = preparer(args.source.read_bytes())
        with args.destination.open('xb') as fichier:
            fichier.write(resultat)
    except (OSError, ValueError, ZlibError) as erreur:
        parser.exit(1, f'{erreur}\n')


if __name__ == '__main__':
    main()
