"""Read graphics diagnostics from A4NE mGBA 0.10.5 snapshot files."""

import argparse
import csv
from hashlib import sha256
from pathlib import Path
from struct import iter_unpack, unpack_from
from zlib import crc32, decompress

from PIL import Image, ImageDraw, ImageFont

SCENES = {
    "ferme-reveil": ("after-sleep-steady.state", "Ferme au réveil", "Partie normale"),
    "ferme-sommeil": ("sleep-prompt-orig.state", "Ferme, confirmation du sommeil", "Partie normale"),
    "ferme-karen": ("fixture-steady.state", "Ferme, dialogue avec Karen", "État de test préparé en RAM"),
    "clinique-annonce": ("karen-announcement.state", "Clinique, annonce du médecin", "État de test préparé en RAM"),
}
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
ROM_CRC32 = 0x8E923168
WIDTH, HEIGHT = 240, 160
REGIONS = (
    ("Registres graphiques", 0x400, 0x458, 0x04000000),
    ("Palette BG", 0x800, 0xA00, 0x05000000),
    ("Palette OBJ", 0xA00, 0xC00, 0x05000200),
    ("OAM", 0xC00, 0x1000, 0x07000000),
    ("VRAM BG", 0x1000, 0x11000, 0x06000000),
    ("VRAM OBJ", 0x11000, 0x19000, 0x06010000),
)
OBJ_SIZES = (
    ((8, 8), (16, 16), (32, 32), (64, 64)),
    ((16, 8), (32, 8), (32, 16), (64, 32)),
    ((8, 16), (8, 32), (16, 32), (32, 64)),
)


def read_snapshot(path):
    data = path.read_bytes()
    if data[:8] != PNG_MAGIC:
        raise ValueError(f"Conteneur PNG attendu dans {path}")
    offset = 8
    while offset + 12 <= len(data):
        size, tag = unpack_from(">I4s", data, offset)
        start = offset + 8
        stop = start + size
        if stop + 4 > len(data):
            raise ValueError(f"Bloc PNG tronqué dans {path}")
        if tag == b"gbAs":
            payload = data[start:stop]
            if crc32(tag + payload) != unpack_from(">I", data, stop)[0]:
                raise ValueError(f"CRC PNG incorrect dans {path}")
            state = decompress(payload)
            break
        offset = stop + 4
    else:
        raise ValueError(f"Bloc gbAs absent de {path}")
    if (len(state) != 0x61000
            or state[0x1C:0x20] != b"A4NE"
            or unpack_from("<I", state, 8)[0] != ROM_CRC32):
        raise ValueError(f"Enregistrement A4NE Rev 0 invalide dans {path}")
    return state, sha256(data).hexdigest()


def reg(state, offset):
    return unpack_from("<H", state, 0x400 + offset)[0]


def color_rgb(value):
    channels = (value & 31, value >> 5 & 31, value >> 10 & 31)
    return tuple((channel << 3) | (channel >> 2) for channel in channels)


def read_palettes(scene, state, destination):
    rows = []
    palettes = {}
    for name, offset, address in (("BG", 0x800, 0x05000000), ("OBJ", 0xA00, 0x05000200)):
        raw = state[offset:offset + 512]
        (destination / f"{scene}-palette-{name}.bin").write_bytes(raw)
        colors = []
        for index, (word,) in enumerate(iter_unpack("<H", raw)):
            color = color_rgb(word)
            colors.append(color)
            rows.append({
                "scene": scene, "palette": name, "index": index,
                "banque_4bpp": index // 16, "indice_dans_banque": index % 16,
                "adresse_gba": f"0x{address + 2 * index:08X}",
                "mot_brut": f"0x{word:04X}", "bgr555": f"0x{word & 0x7FFF:04X}",
                "rgb_hex": "#{:02X}{:02X}{:02X}".format(*color),
            })
        palettes[name] = colors
    return rows, palettes


def inside_axis(position, register):
    start, stop = register >> 8, register & 255
    return start <= position < stop if start <= stop else position >= start or position < stop


def screen_mask(state, control):
    if control & 0x8000:
        raise ValueError("Le calcul de masque ne couvre pas les fenêtres OBJ")
    inside, outside = reg(state, 0x48), reg(state, 0x4A)
    wins = [
        (reg(state, 0x40 + 2 * i), reg(state, 0x44 + 2 * i), inside >> (8 * i) & 63)
        for i in range(2)
        if control & (0x2000 << i)
    ]
    return [
        next((mask for h, v, mask in wins if inside_axis(x, h) and inside_axis(y, v)),
             outside & 63 if wins else 63)
        for y in range(HEIGHT) for x in range(WIDTH)
    ]


def inspect_backgrounds(scene, state, control):
    if control & 7:
        raise ValueError("La lecture des couches de cette étude exige le mode vidéo 0")
    masks = screen_mask(state, control)
    rows = []
    for layer in range(4):
        if not control & (0x100 << layer):
            continue
        settings = reg(state, 8 + layer * 2)
        bpp = 8 if (settings & 0x80) else 4
        charblock, screenblock = (settings >> 2) & 3, (settings >> 8) & 31
        width = 32 << (settings >> 14 & 1)
        height = 32 << (settings >> 15 & 1)
        hofs, vofs = reg(state, 0x10 + layer * 4) & 511, reg(state, 0x12 + layer * 4) & 511
        allowed = [i for i, mask in enumerate(masks) if mask & (1 << layer)]
        cells = {
            (((i % WIDTH + hofs) // 8) % width, ((i // WIDTH + vofs) // 8) % height)
            for i in allowed
        }
        references = []
        for x, y in sorted(cells):
            block = screenblock + (y // 32) * (width // 32) + x // 32
            address = (block * 0x800 + (y % 32) * 64 + (x % 32) * 2) % 0x10000
            references.append(unpack_from("<H", state, 0x1000 + address)[0])
        rows.append({
            "scene": scene, "couche": f"BG{layer}", "priorite": settings & 3,
            "bpp": bpp, "largeur_tuiles": width, "hauteur_tuiles": height,
            "base_motifs_gba": f"0x{0x06000000 + charblock * 0x4000:08X}",
            "base_carte_gba": f"0x{0x06000000 + screenblock * 0x800:08X}",
            "decalage_x": hofs, "decalage_y": vofs, "pixels_autorises_par_fenetre": len(allowed),
            "cellules_referencees": len(cells),
            "indices_tuiles_distincts": len({entry & 1023 for entry in references}),
            "banques_4bpp_referencees": (
                " | ".join(map(str, sorted({entry >> 12 for entry in references}))) if bpp == 4 else ""
            ),
        })
    return rows


def inspect_objects(scene, state):
    rows = []
    for index, (attr0, attr1, attr2, _) in enumerate(iter_unpack("<4H", state[0xC00:0x1000])):
        affine = bool(attr0 & 256)
        double_or_disabled = bool(attr0 & 512)
        shape, mode = attr0 >> 14, attr0 >> 10 & 3
        if (double_or_disabled and not affine) or shape == 3 or mode >= 2:
            continue
        x, y = attr1 & 511, attr0 & 255
        x -= 512 if x >= 256 else 0
        y -= 256 if y >= HEIGHT else 0
        width, height = OBJ_SIZES[shape][attr1 >> 14]
        scale = 2 if affine and double_or_disabled else 1
        if not (x < WIDTH and y < HEIGHT and x + width * scale > 0 and y + height * scale > 0):
            continue
        bpp = 8 if attr0 & 0x2000 else 4
        tile = attr2 & 1023
        first_tile = tile & ~1 if bpp == 8 else tile
        rows.append({
            "scene": scene, "entree_oam": index, "x": x, "y": y, "largeur": width, "hauteur": height,
            "bpp": bpp, "priorite": attr2 >> 10 & 3, "indice_motif": tile,
            "adresse_motif_gba": f"0x{0x06010000 + first_tile * 32:08X}",
            "banque_4bpp": attr2 >> 12 if bpp == 4 else "",
            "attr0": f"0x{attr0:04X}", "attr1": f"0x{attr1:04X}", "attr2": f"0x{attr2:04X}",
        })
    return rows


def evidence_picture(title, context, frame, palettes, destination):
    cell = 18
    im = Image.new("RGB", (850, 436), "#18252A")
    draw = ImageDraw.Draw(im)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    title_font = ImageFont.truetype(font_path, 23)
    label_font = ImageFont.truetype(font_path, 15)
    draw.text((24, 18), title, font=title_font, fill="#F3F5F5")
    draw.text((24, 60), "Capture mGBA · A4NE Rev 0", font=label_font, fill="#DEEAED")
    im.paste(frame.resize((WIDTH * 2, HEIGHT * 2), Image.Resampling.NEAREST), (24, 88))
    draw.text((532, 60), "Palette BG", font=label_font, fill="#DEEAED")
    for index, color in enumerate(palettes["BG"]):
        x, y = 532 + (index % 16) * 9, 88 + (index // 16) * cell
        draw.rectangle((x, y, x + 8, y + cell - 1), fill=color)
    draw.text((682, 60), "Palette OBJ", font=label_font, fill="#DEEAED")
    for index, color in enumerate(palettes["OBJ"]):
        x, y = 682 + (index % 16) * 9, 88 + (index // 16) * cell
        draw.rectangle((x, y, x + 8, y + cell - 1), fill=color)
    draw.text((532, 382), "16 banques × 16 entrées par palette", font=label_font, fill="#DEEAED")
    draw.text((24, 414), context, font=label_font, fill="#DEEAED")
    im.save(destination)


def save_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(source, destination):
    destination.mkdir(parents=True, exist_ok=True)
    palettes, backgrounds, objects, memory, evidence = [], [], [], [], []
    for scene, (filename, label, context) in SCENES.items():
        path = source / filename
        state, state_sha = read_snapshot(path)
        palette_rows, colors = read_palettes(scene, state, destination)
        palettes.extend(palette_rows)
        control = reg(state, 0)
        layers = inspect_backgrounds(scene, state, control)
        sprites = inspect_objects(scene, state) if control & 0x1000 else []
        backgrounds.extend(layers)
        objects.extend(sprites)
        for area, begin, end, address in REGIONS:
            memory.append({
                "scene": scene, "zone": area, "adresse_gba": f"0x{address:08X}",
                "offset_gbAs": f"0x{begin:05X}", "octets": end - begin,
                "sha256": sha256(state[begin:end]).hexdigest(),
            })
        with Image.open(path) as image:
            frame = image.convert("RGB")
        if frame.size != (WIDTH, HEIGHT):
            raise ValueError(f"Dimensions inattendues dans {path}")
        frame.save(destination / f"{scene}-mGBA.png")
        evidence_picture(label, context, frame, colors, destination / f"{scene}-releve.png")
        evidence.append({
            "scene": scene, "contexte": context, "etat_source": filename, "crc32_rom": f"{ROM_CRC32:08X}",
            "sha256_etat_source": state_sha, "mode_video": control & 7,
            "dispcnt": f"0x{control:04X}", "bldcnt": f"0x{reg(state, 0x50):04X}",
            "win0": int(bool(control & 0x2000)), "win1": int(bool(control & 0x4000)),
            "couches_BG_actives": len(layers), "objets_dans_le_cadre_avant_occlusion": len(sprites),
            "couleurs_BG_distinctes": len(set(colors["BG"])), "couleurs_OBJ_distinctes": len(set(colors["OBJ"])),
            "win0h": f"0x{reg(state, 0x40):04X}", "win1h": f"0x{reg(state, 0x42):04X}",
            "win0v": f"0x{reg(state, 0x44):04X}", "win1v": f"0x{reg(state, 0x46):04X}",
            "winin": f"0x{reg(state, 0x48):04X}", "winout": f"0x{reg(state, 0x4A):04X}",
            "capture_mgba_png": f"{scene}-mGBA.png", "releve_visuel": f"{scene}-releve.png",
        })
    for filename, rows in (
        ("preuves.csv", evidence), ("palettes.csv", palettes), ("couches.csv", backgrounds),
        ("objets-oam.csv", objects), ("blocs-memoire.csv", memory),
    ):
        save_csv(destination / filename, rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    run(args.source, args.destination)
