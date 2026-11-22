"""Créer une copie d’un état mGBA A4NE de confirmation du sommeil pour le test 0657."""

import argparse
from pathlib import Path
from struct import pack, unpack_from
from zlib import compress, crc32, error as ZlibError

from inspecter_etat import EWRAM, PNG, png_chunks, read_state


SAVE_IN_EWRAM = 0x25D8
SLEEP_CONTEXT = (1, 0x082DA91C, 0x50)
BEFORE_AFTER = {
    0x0011: (0x04, 0x0D),
    0x01F4: (0x00, 0x02),
    0x01F5: (0x80, 0x90),
    0x1D00: (0x00, 0x01),
    0x1D01: (0x00, 0x0C),
    0x1ECC: (0x00, 0xFF),
    0x1ECD: (0x00, 0xFF),
    0x1ECE: (0x08, 0x0E),
}


def prepare(input_bytes):
    if not input_bytes.startswith(PNG):
        raise ValueError("Un état mGBA enregistré au format PNG est requis")
    state, code = read_state(input_bytes)
    if code != b"A4NE" or unpack_from("<III", state, EWRAM + 0x207C) != SLEEP_CONTEXT:
        raise ValueError("État A4NE d’origine attendu au choix de confirmer le sommeil (0342)")
    if tuple(state[EWRAM + 0x25E8:EWRAM + 0x25EA]) != (1, 4):
        raise ValueError("La date de départ attendue est le 2 printemps, an 1")

    changed = bytearray(state)
    for field, (old, new) in BEFORE_AFTER.items():
        position = EWRAM + SAVE_IN_EWRAM + field
        if state[position] != old:
            raise ValueError(f"Valeur d’origine inattendue pour le champ 0x{field:04X}")
        changed[position] = new

    compressed = compress(changed)
    block = pack(">I4s", len(compressed), b"gbAs") + compressed + pack(">I", crc32(b"gbAs" + compressed))
    return PNG + b"".join(block if tag == b"gbAs" else original for tag, _, original in png_chunks(input_bytes))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path, help="Nouveau fichier à créer")
    args = parser.parse_args()
    try:
        prepared = prepare(args.source.read_bytes())
        with args.destination.open("xb") as output:
            output.write(prepared)
    except (OSError, ValueError, ZlibError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
