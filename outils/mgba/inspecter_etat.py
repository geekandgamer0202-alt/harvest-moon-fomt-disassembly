"""Inspecter un état GBA de mGBA 0.10.5 sans modifier son contenu."""

import argparse
from hashlib import sha1, sha256
import json
from pathlib import Path
from struct import iter_unpack, unpack_from
from zlib import crc32, decompress, error as ZlibError


PNG = b"\x89PNG\r\n\x1a\n"
EWRAM = 0x21000
GBA_ROM = 0x08000000
ROM_INFO = {
    b"A4NE": (0x8E923168, "a2fc3574f0a65a4fcf7682fb274b9d7eebdef963", 0x0F89D4),
    b"A4NP": (0xF50F82AD, "7ba1ec1e46ce424e3c6fd72e4e8d5e9eb5ede247", 0x0F8A20),
}
VIDEO_REGIONS = (
    ("IO", 0x04000000, 0x400, 0x458),
    ("BG_PRAM", 0x05000000, 0x800, 0xA00),
    ("OBJ_PRAM", 0x05000200, 0xA00, 0xC00),
    ("OAM", 0x07000000, 0xC00, 0x1000),
    ("BG_VRAM", 0x06000000, 0x1000, 0x11000),
    ("OBJ_VRAM", 0x06010000, 0x11000, 0x19000),
)
OBJ_SIZE = (
    ((8, 8), (16, 16), (32, 32), (64, 64)),
    ((16, 8), (32, 8), (32, 16), (64, 32)),
    ((8, 16), (8, 32), (16, 32), (32, 64)),
)


def word(data, offset):
    return unpack_from("<H", data, offset)[0]


def png_chunks(data):
    offset = len(PNG)
    while offset + 12 <= len(data):
        size, tag = unpack_from(">I4s", data, offset)
        start = offset + 8
        end = start + size
        if end + 4 > len(data) or crc32(tag + data[start:end]) != unpack_from(">I", data, end)[0]:
            raise ValueError(f"Bloc PNG {tag!r} tronqué ou CRC invalide")
        yield tag, data[start:end], data[offset:end + 4]
        offset = end + 4
        if tag == b"IEND" and offset == len(data):
            return
    raise ValueError("Fin du conteneur PNG invalide")


def read_state(data):
    if data.startswith(PNG):
        chunks = [payload for tag, payload, _ in png_chunks(data) if tag == b"gbAs"]
        if len(chunks) != 1:
            raise ValueError("Le PNG doit contenir un bloc d’état gbAs")
        data = decompress(chunks[0])
    if len(data) != 0x61000 or data[:4] != b"\x07\x00\x00\x01":
        raise ValueError("Format d’état GBA mGBA 0.10.5 inattendu")
    code = data[0x1C:0x20]
    variant = ROM_INFO.get(code)
    if variant is None or unpack_from("<I", data, 8)[0] != variant[0]:
        raise ValueError("État A4NE ou A4NP d’une ROM de référence requis")
    return data, code


def script_addresses(rom_path):
    rom = rom_path.read_bytes()
    code = rom[0xAC:0xB0]
    variant = ROM_INFO.get(code)
    if variant is None or sha1(rom).hexdigest() != variant[1]:
        raise ValueError("SHA-1 de ROM A4NE/A4NP inattendu")
    pointers = unpack_from("<1329I", rom, variant[2])
    addresses = {}
    for script, address in enumerate(pointers[1:], 1):
        offset = address - GBA_ROM
        if rom[offset:offset + 4] != b"RIFF" or rom[offset + 8:offset + 16] != b"SCR CODE":
            raise ValueError(f"En-tête CODE absent du script {script:04d}")
        addresses[address + 24] = f"{script:04d}"
    return code, addresses


def palette_colors(data):
    return len({color & 0x7FFF for color, in iter_unpack("<H", data)})


def in_window(position, bounds):
    begin, end = bounds >> 8, bounds & 255
    return begin <= position < end if begin <= end else position >= begin or position < end


def window_masks(state, control):
    if control & 0x8000:
        return None
    inside, outside = word(state, 0x448), word(state, 0x44A) & 63
    windows = [
        (word(state, 0x440 + i * 2), word(state, 0x444 + i * 2), inside >> (i * 8) & 63)
        for i in range(2) if control & (0x2000 << i)
    ]
    if not windows:
        return [63] * (240 * 160)
    return [
        next((mask for h, v, mask in windows if in_window(x, h) and in_window(y, v)), outside)
        for y in range(160) for x in range(240)
    ]


def text_layer(state, layer, masks):
    settings = word(state, 0x408 + layer * 2)
    screenblock, charblock = settings >> 8 & 31, settings >> 2 & 3
    bpp = 8 if settings & 0x80 else 4
    width, height = 32 << (settings >> 14 & 1), 32 << (settings >> 15 & 1)
    hofs, vofs = word(state, 0x410 + layer * 4) & 511, word(state, 0x412 + layer * 4) & 511
    result = {
        "couche": f"BG{layer}", "priorite": settings & 3, "bpp": bpp,
        "base_motifs": f"0x{0x06000000 + charblock * 0x4000:08X}",
        "base_carte": f"0x{0x06000000 + screenblock * 0x800:08X}",
        "largeur_tuiles": width, "hauteur_tuiles": height, "decalage_x": hofs, "decalage_y": vofs,
    }
    if masks is None:
        return result
    allowed = [i for i, mask in enumerate(masks) if mask & (1 << layer)]
    cells = {(((i % 240 + hofs) // 8) % width, ((i // 240 + vofs) // 8) % height) for i in allowed}
    entries = []
    for x, y in cells:
        block = screenblock + (y // 32) * (width // 32) + x // 32
        offset = (block * 0x800 + (y % 32) * 64 + (x % 32) * 2) % 0x10000
        entries.append(word(state, 0x1000 + offset))
    result.update({
        "pixels_autorises_par_fenetre": len(allowed), "cellules_referencees": len(cells),
        "indices_tuiles_distincts": len({entry & 1023 for entry in entries}),
        "banques_4bpp_referencees": sorted({entry >> 12 for entry in entries}) if bpp == 4 else None,
    })
    return result


def visible_objects(data):
    """Entrées OBJ admissibles dont le cadre intersecte l’écran avant composition."""
    visible = []
    for index, (a0, a1, a2, _) in enumerate(iter_unpack("<4H", data)):
        affine = bool(a0 & 0x100)
        double_or_disabled = bool(a0 & 0x200)
        shape = a0 >> 14
        if (double_or_disabled and not affine) or shape == 3 or (a0 >> 10 & 3) >= 2:
            continue
        width, height = OBJ_SIZE[shape][a1 >> 14]
        scale = 2 if affine and double_or_disabled else 1
        x, y = a1 & 511, a0 & 255
        x -= 512 if x >= 256 else 0
        y -= 256 if y >= 160 else 0
        if x < 240 and y < 160 and x + width * scale > 0 and y + height * scale > 0:
            visible.append({
                "index_oam": index, "x": x, "y": y,
                "largeur_cadre": width * scale, "hauteur_cadre": height * scale,
                "indice_tuile": a2 & 1023, "bpp": 8 if a0 & 0x2000 else 4,
                "attributs": [f"0x{value:04X}" for value in (a0, a1, a2)],
            })
    return visible


def inspect_state(path, rom=None):
    raw = path.read_bytes()
    state, code = read_state(raw)
    if rom is not None and code != rom[0]:
        raise ValueError(f"{path.name} et la ROM relèvent de versions différentes")
    year, date, clock = unpack_from("<BBH", state, EWRAM + 0x25E8)
    running, address, pc = unpack_from("<III", state, EWRAM + 0x207C)
    control = word(state, 0x400)
    mode = control & 7
    backgrounds = []
    if mode == 0:
        masks = window_masks(state, control)
        backgrounds = [
            text_layer(state, layer, masks)
            for layer in range(4) if control & (0x100 << layer)
        ]
    objects = visible_objects(state[0xC00:0x1000]) if control & 0x1000 else []
    registers = {
        name: f"0x{word(state, 0x400 + offset):04X}"
        for name, offset in (
            ("DISPCNT", 0), ("WIN0H", 0x40), ("WIN1H", 0x42), ("WIN0V", 0x44),
            ("WIN1V", 0x46), ("WININ", 0x48), ("WINOUT", 0x4A), ("BLDCNT", 0x50),
        )
    }
    return {
        "etat": path.name, "sha256_etat": sha256(raw).hexdigest(), "rom": code.decode("ascii"),
        "crc32_rom": f"{ROM_INFO[code][0]:08X}",
        "date": {"annee_brute": year, "saison_0_a_3": date & 3, "jour": (date >> 2 & 31) + 1,
                 "heure": f"{clock & 31:02d}:{clock >> 5 & 63:02d}"} if 1 <= year <= 99 else None,
        "contexte_script_principal": {
            "indicateur_brut": running, "code_gba": f"0x{address:08X}", "pc": f"0x{pc:X}",
            "script": rom[1].get(address) if rom is not None else None,
        },
        "mesures": {
            "or": unpack_from("<I", state, EWRAM + 0x4080)[0],
            "main_octets": list(state[EWRAM + 0x4204:EWRAM + 0x4208]),
            "sac_octets": list(state[EWRAM + 0x4214:EWRAM + 0x421C]),
            "affinite_rick_octet": state[EWRAM + 0x4338],
        } if 1 <= year <= 99 else None,
        "video": {
            "mode": mode, "registres": registers, "couches_bg_mode_0": backgrounds,
            "couleurs_bg_distinctes": palette_colors(state[0x800:0xA00]),
            "couleurs_obj_distinctes": palette_colors(state[0xA00:0xC00]),
            "objets_avant_occlusion": objects,
            "zones": {
                name: {"adresse_gba": f"0x{address:08X}", "offset_etat": f"0x{start:X}",
                       "octets": end - start, "sha256": sha256(state[start:end]).hexdigest()}
                for name, address, start, end in VIDEO_REGIONS
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("etats", nargs="+", type=Path)
    parser.add_argument("--rom", type=Path, help="ROM locale pour résoudre les identifiants de scripts")
    args = parser.parse_args()
    try:
        rom = script_addresses(args.rom) if args.rom else None
        reports = [inspect_state(path, rom) for path in args.etats]
    except (OSError, ValueError, ZlibError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(reports, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
