"""Render static A4NE world maps. Dependencies: numpy, Pillow and Wokann's decompress.py."""
import argparse
import csv
import hashlib
from collections import Counter, defaultdict
from functools import cache
from pathlib import Path
from struct import unpack_from

import numpy as np
from PIL import Image

from decompress import unpack_with_consumed

ROM_SHA1 = 'a2fc3574f0a65a4fcf7682fb274b9d7eebdef963'
BASE = 0x08000000
TABLE = 0x105EDC
STRIDE = 0x28
NUM_MAPS = 66

NAMES = (
    'Ferme', 'Place des Roses', 'Nord de Mineral Town', 'Sud de Mineral Town',
    'Plage de Mineral Town', 'Derrière l’église', 'Forêt', 'Mont Mother’s Hill',
    'Sommet de Mother’s Hill',
)
NAMES = tuple(f'{name} ({season})' for name in NAMES for season in ('hors hiver', 'hiver')) + (
    'Domaine viticole Aja, rez-de-chaussée', 'Domaine viticole Aja, étage',
    'Réserve du domaine Aja, rez-de-chaussée', 'Cave du domaine Aja',
    'Auberge, rez-de-chaussée', 'Arrière-salle de l’auberge', 'Auberge, étage',
    'Supermarché', 'Arrière-salle du supermarché', 'Restaurant de Kai', 'Maison de Zack',
    'Clinique, rez-de-chaussée', 'Clinique, étage', 'Église', 'Bibliothèque, rez-de-chaussée',
    'Bibliothèque, étage', 'Maison de Basil, rez-de-chaussée', 'Maison de Basil, étage',
    'Poulailler', 'Poulailler agrandi', 'Étable', 'Étable agrandie', 'Écurie',
    'Maison de la ferme, sans agrandissement', 'Maison de la ferme, premier agrandissement',
    'Maison de la ferme, second agrandissement', 'Maison de Lillia, rez-de-chaussée',
    'Maison de Lillia, étage', 'Maison du ranch Yodel, rez-de-chaussée',
    'Maison du ranch Yodel, étage', 'Forge', 'Maison de Gotz', 'Maison du maire',
    'Maison d’Ellen', 'Cabane des lutins', 'Chalet de montagne', 'Maison de plage',
    'Maison de ville', 'Mine du printemps ou mine du lac, niveau 0',
    'Mines, plan de base des multiples de 5', 'Mines, plan de base des multiples de 3',
    'Mines, plan de base courant', 'Entrée de la mine du lac', 'Mine du lac, niveau 9',
    'Champ du tutoriel des animaux', 'Poulailler du tutoriel', 'Étable du tutoriel',
    'Entrée de la mine du printemps',
)


def file_offset(address):
    return f'0x{address - BASE:06X}' if address else ''


def bus_address(address):
    return f'0x{address:08X}' if address else ''


def map_row_id(map_id):
    return f'{map_id:02d}'


def tile_pixels(data):
    packed = np.frombuffer(data, dtype=np.uint8).reshape(1024, 8, 4)
    pixels = np.empty((1024, 8, 8), dtype=np.uint8)
    pixels[:, :, 0::2] = packed & 15
    pixels[:, :, 1::2] = packed >> 4
    return pixels


def color_table(data):
    words = np.frombuffer(data, dtype='<u2')
    rgb5 = (words[:, None] >> np.array([0, 5, 10], np.uint16)) & 31
    rgb = np.zeros((256, 3), dtype=np.uint8)
    rgb[16:] = (rgb5 << 3) | (rgb5 >> 2)
    # GameSceneWorldMap loads these streams into hardware BG banks 1–15.
    # Index 0 is BG transparency, and the resource has no colors for bank 0.
    return rgb


def render(data, width, height, atlas, palette):
    canvas = Image.new('RGBA', (width * 8, height * 8))
    unknown_visible = np.zeros((height, width, 8, 8), dtype=bool)
    missing_entries = 0
    for layer in data:
        words = np.frombuffer(layer, dtype='<u2').reshape(height, width)
        pixels = atlas[words & 1023]
        pixels = np.where((words & 0x0400)[..., None, None], pixels[..., ::-1], pixels)
        pixels = np.where((words & 0x0800)[..., None, None], pixels[..., ::-1, :], pixels)
        banks = (words >> 12).astype(np.uint8)
        has_color = (banks != 0)[..., None, None]
        nonzero = pixels != 0
        opaque_pixels = nonzero & has_color
        missing_entries += np.count_nonzero(np.any(nonzero, axis=(-2, -1)) & (banks == 0))
        unknown_visible = np.where(nonzero, ~has_color, unknown_visible)
        color_indices = (banks[..., None, None] << 4) | pixels
        rgba = np.empty((*pixels.shape, 4), dtype=np.uint8)
        rgba[..., :3] = palette[color_indices]
        rgba[..., 3] = opaque_pixels * 255
        rows = rgba.transpose(0, 2, 1, 3, 4).reshape(height * 8, width * 8, 4)
        canvas.alpha_composite(Image.fromarray(rows))
    return canvas, missing_entries, np.count_nonzero(unknown_visible)


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as output:
        writer = csv.writer(output)
        writer.writerow(fields)
        writer.writerows(rows)


def export(rom_path, output):
    rom = rom_path.read_bytes()
    sha1 = hashlib.sha1(rom).hexdigest()
    if rom[0xAC:0xB0] != b'A4NE' or sha1 != ROM_SHA1:
        raise ValueError(f'La ROM A4NE attendue a pour SHA-1 {ROM_SHA1}, obtenu {sha1}')
    for directory in ('plans', 'tuiles', 'tuiles_indices', 'palettes'):
        (output / directory).mkdir(parents=True, exist_ok=True)

    stream_info = defaultdict(set)

    @cache
    def decoded(address):
        offset = address - BASE
        if not 0 <= offset < len(rom):
            raise ValueError(f'Adresse ROM hors limites {bus_address(address)}')
        data, codec, _, consumed = unpack_with_consumed(rom, offset)
        if offset + consumed > len(rom):
            raise ValueError(f'Flux ROM hors limites {bus_address(address)}')
        return data, codec, consumed

    def load(address, length, role):
        data, _, _ = decoded(address)
        if len(data) != length:
            raise ValueError(f'Taille incorrecte pour {role} {bus_address(address)}: {len(data)} != {length}')
        stream_info[address].add(role)
        return data

    map_rows = []
    tile_references = defaultdict(list)
    palette_references = defaultdict(list)
    counts = defaultdict(Counter)
    for map_id, name in enumerate(NAMES):
        offset = TABLE + STRIDE * map_id
        tile_address, day, night, bg3, bg2, bg1, _, _, width, height, flags = unpack_from('<8IHHI', rom, offset)
        atlas = tile_pixels(load(tile_address, 32768, 'tuiles'))
        layer_addresses = (bg3, bg2, bg1)
        layers = [load(p, width * height * 2, name) for p, name in zip(layer_addresses, ('BG3', 'BG2', 'BG1')) if p]
        for data in layers:
            words = np.frombuffer(data, dtype='<u2')
            counts[tile_address, day].update((int(word & 1023), int(word >> 12)) for word in words if 0 < word >> 12)
        tile_references[tile_address].append((map_id, day))
        day_data = load(day, 480, 'palette_jour')
        night_data = load(night, 480, 'palette_nuit')
        palette_references[day].append((map_id, 'jour'))
        palette_references[night].append((map_id, 'nuit'))
        variants = [('jour_et_nuit' if day_data == night_data else 'jour', day, day_data)]
        if day_data != night_data:
            variants.append(('nuit', night, night_data))
        for variant, palette_address, data in variants:
            image, missing_entries, missing_pixels = render(layers, width, height, atlas, color_table(data))
            file = f'plans/{map_row_id(map_id)}_{variant}.png'
            image.save(output / file)
            map_rows.append((map_row_id(map_id), name, variant, file, width, height, width * 8, height * 8,
                             file_offset(BASE + offset), bus_address(BASE + offset), f'0x{flags:08X}',
                             file_offset(tile_address), file_offset(palette_address), file_offset(day), file_offset(night),
                             *(file_offset(p) for p in layer_addresses), missing_entries, missing_pixels))

    tile_rows = []
    for address, references in sorted(tile_references.items()):
        _, palette_address = references[0]
        atlas = tile_pixels(load(address, 32768, 'tuiles'))
        palette = color_table(load(palette_address, 480, 'palette_jour'))
        choices = defaultdict(dict)
        for (tile, bank), count in counts[address, palette_address].items():
            choices[tile][bank] = count
        banks = np.zeros(1024, dtype=np.uint8)
        for tile, freqs in choices.items():
            banks[tile] = max(freqs, key=lambda bank: (freqs[bank], -bank))
        selected = banks[:, None, None]
        rgb = palette[(selected << 4) | atlas]
        rgba = np.empty((1024, 8, 8, 4), np.uint8)
        rgba[..., :3] = np.where(selected[..., None] == 0, atlas[..., None] * 17, rgb)
        rgba[..., 3] = (atlas != 0) * 255
        image = Image.fromarray(rgba.reshape(64, 16, 8, 8, 4).transpose(0, 2, 1, 3, 4).reshape(512, 128, 4))
        file = f'tuiles/{address - BASE:06X}.png'
        image.save(output / file)
        index_file = f'tuiles_indices/{address - BASE:06X}.png'
        index_image = Image.fromarray(atlas.reshape(64, 16, 8, 8).transpose(0, 2, 1, 3).reshape(512, 128))
        index_image.putpalette([value for i in range(256) for value in [min(255, i * 17)] * 3])
        index_image.save(output / index_file, bits=4)
        tile_rows.append((file_offset(address), bus_address(address), file, index_file, 1024, 128, 512,
                          file_offset(palette_address), map_row_id(references[0][0]),
                          ' '.join(map_row_id(map_id) for map_id, _ in references), len(choices)))

    palette_rows = []
    for address, references in sorted(palette_references.items()):
        rgb = color_table(load(address, 480, 'palette'))[16:].reshape(15, 16, 3)
        image = Image.fromarray(rgb).resize((256, 240), Image.Resampling.NEAREST)
        file = f'palettes/{address - BASE:06X}.png'
        image.save(output / file)
        palette_rows.append((file_offset(address), bus_address(address), file, 240, 1, 15,
                             ' '.join(f'{map_row_id(map_id)}:{period}' for map_id, period in references)))

    stream_rows = []
    for address, roles in sorted(stream_info.items()):
        data, codec, consumed = decoded(address)
        stream_rows.append((file_offset(address), file_offset(address + consumed), bus_address(address),
                            ' '.join(sorted(roles)), consumed, len(data), codec, hashlib.sha256(data).hexdigest()))

    write_csv(output / 'Cartes.csv', ('id_plan', 'lieu', 'periode', 'fichier_png', 'largeur_tuiles', 'hauteur_tuiles',
                                     'largeur_px', 'hauteur_px', 'offset_entree_rom', 'adresse_entree_gba', 'drapeaux',
                                     'offset_tuiles_rom', 'offset_palette_rom', 'offset_palette_jour_rom', 'offset_palette_nuit_rom',
                                     'offset_bg3_rom', 'offset_bg2_rom', 'offset_bg1_rom', 'cellules_source_banque_zero',
                                     'pixels_banque_zero_visibles'), map_rows)
    write_csv(output / 'Tuiles.csv', ('offset_rom', 'adresse_gba', 'fichier_png', 'fichier_indices_4bpp_png', 'nombre_tuiles', 'largeur_px', 'hauteur_px',
                                     'offset_palette_apercu_rom', 'id_plan_palette_apercu', 'plans', 'tuiles_avec_banque'), tile_rows)
    write_csv(output / 'Palettes.csv', ('offset_rom', 'adresse_gba', 'fichier_png', 'couleurs', 'premiere_banque_bg',
                                      'derniere_banque_bg', 'plans_et_periodes'), palette_rows)
    write_csv(output / 'Flux.csv', ('offset_rom', 'offset_fin_lue_exclue_rom', 'adresse_gba', 'roles', 'octets_lus_compresses',
                                  'octets_decompresses', 'format_codec', 'sha256_decompresse'), stream_rows)
    print(f'{len(NAMES)} plans • {len(map_rows)} PNG cartes • {len(tile_rows)} planches de tuiles • '
          f'{len(palette_rows)} palettes • {len(stream_rows)} flux')
    print(f'{sum(int(row[-1]) for row in map_rows)} pixels visibles sans couleur source')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    export(args.rom, args.destination)
