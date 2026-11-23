"""Créer une copie d’un état mGBA USA ou Europe pour le test 0657."""

import argparse
from pathlib import Path
from struct import pack, pack_into, unpack_from
from zlib import compress, crc32, error as ZlibError

from inspecter_etat import EWRAM, PNG, png_chunks, read_state


SAVE_IN_EWRAM = 0x25D8
SLEEP_CONTEXTS = {
    b"A4NE": (1, 0x082DA91C, 0x50),
    b"A4NP": (1, 0x082DA974, 0x50),
}
CLINIC_CONTEXTS = {
    b"A4NE": (1, 0x08345884, 0xFE),
    b"A4NP": (1, 0x083458DC, 0xFE),
}
REGISTRE = EWRAM + SAVE_IN_EWRAM + 0x214C
MARQUEUR = EWRAM + SAVE_IN_EWRAM + 0x2158
MALAISE = EWRAM + SAVE_IN_EWRAM + 0x2171
VARIANTES_PRIORITE = {
    "marqueur": ("<H", MARQUEUR, 74),
    "registre": ("<H", REGISTRE + 4, 74),
    "malaise": ("<B", MALAISE, 0x08),
}
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


def reconstruire(input_bytes, changed):
    if not input_bytes.startswith(PNG):
        return bytes(changed)
    compressed = compress(changed)
    block = pack(">I4s", len(compressed), b"gbAs") + compressed + pack(">I", crc32(b"gbAs" + compressed))
    return PNG + b"".join(block if tag == b"gbAs" else original for tag, _, original in png_chunks(input_bytes))


def prepare(input_bytes):
    state, code = read_state(input_bytes)
    if unpack_from("<III", state, EWRAM + 0x207C) != SLEEP_CONTEXTS[code]:
        raise ValueError("État d’origine attendu au choix de confirmer le sommeil (0342)")
    if tuple(state[EWRAM + 0x25E8:EWRAM + 0x25EA]) != (1, 4):
        raise ValueError("La date de départ attendue est le 2 printemps, an 1")

    changed = bytearray(state)
    for field, (old, new) in BEFORE_AFTER.items():
        position = EWRAM + SAVE_IN_EWRAM + field
        if state[position] != old:
            raise ValueError(f"Valeur d’origine inattendue pour le champ 0x{field:04X}")
        changed[position] = new

    return reconstruire(input_bytes, changed)


def lire_clinique(input_bytes):
    state, code = read_state(input_bytes)
    if unpack_from("<III", state, EWRAM + 0x207C) != CLINIC_CONTEXTS[code]:
        raise ValueError("État 0657 attendu au dernier dialogue à la ferme, avant la clinique (PC 0xFE)")
    if unpack_from("<IH", state, REGISTRE) != (1, 198):
        raise ValueError("Le registre doit contenir uniquement l’ID 198")
    return bytearray(state)


def preparer_registre(input_bytes, variante):
    changed = lire_clinique(input_bytes)
    if variante == "vide":
        pack_into("<I", changed, REGISTRE, 0)
    else:
        pack_into("<H", changed, REGISTRE + 4, 0xFFFF)
    return reconstruire(input_bytes, changed)


def preparer_priorite(input_bytes, variante):
    changed = lire_clinique(input_bytes)
    if unpack_from("<H", changed, MARQUEUR)[0] != 0xFFFF or changed[MALAISE] & 0x18:
        raise ValueError("Le marqueur doit être vide et l’état de malaise à zéro")
    format_, position, valeur = VARIANTES_PRIORITE[variante]
    if variante == "malaise":
        valeur |= changed[MALAISE]
    pack_into(format_, changed, position, valeur)
    return reconstruire(input_bytes, changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path, help="Nouveau fichier à créer")
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--registre", choices=("vide", "id-substitue"),
                         help="Prépare un état 0657 avant la clinique pour l’essai de musique")
    options.add_argument("--priorite-clinique", choices=VARIANTES_PRIORITE,
                         help="Prépare un état 0657 pour l’essai de priorité du sprite du joueur")
    args = parser.parse_args()
    try:
        input_bytes = args.source.read_bytes()
        if args.registre:
            prepared = preparer_registre(input_bytes, args.registre)
        elif args.priorite_clinique:
            prepared = preparer_priorite(input_bytes, args.priorite_clinique)
        else:
            prepared = prepare(input_bytes)
        with args.destination.open("xb") as output:
            output.write(prepared)
    except (OSError, ValueError, ZlibError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
