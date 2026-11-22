#!/usr/bin/env python3
"""Vérifie les index graphiques sur une ROM A4NE, en lecture seule."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from hashlib import sha1, sha256
import json
from pathlib import Path
from struct import unpack_from


ROM_SHA1 = 'a2fc3574f0a65a4fcf7682fb274b9d7eebdef963'
ROM_BASE = 0x08000000
INDEX = Path(__file__).resolve().parents[2] / 'docs' / 'graphismes'
MAP_TABLE = 0x105EDC
OBJ_SECTIONS = (4, 16, 8, 32, 32, 8, 4)
GBA_OBJ_SIZES = (
    ((8, 8), (16, 16), (32, 32), (64, 64)),
    ((16, 8), (32, 8), (32, 16), (64, 32)),
    ((8, 16), (8, 32), (16, 32), (32, 64)),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    return int(value, 16) if value.lower().startswith('0x') else int(value)


def expect(row, **expected):
    for key, value in expected.items():
        recorded = row[key]
        if isinstance(value, int):
            matches = bool(recorded) and number(recorded) == value
        else:
            matches = recorded == value
        require(matches, f'{key} vaut {recorded!r} dans l’index, valeur ROM attendue {value!r}')


def index_rows(path, count):
    with (INDEX / path).open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == count, f'{path} doit contenir {count} entrées, trouvé {len(rows)}')
    for row in rows:
        for key, value in row.items():
            if key.startswith('export_local') and value:
                require(value.startswith('exports/graphismes-a4ne/') and '..' not in Path(value).parts,
                        f'Chemin d’export local invalide dans {path}')
    return rows


@dataclass(frozen=True)
class Section:
    start: int
    count: int
    stride: int

    def __getitem__(self, index):
        require(0 <= index < self.count, f'Indice {index} hors table ROM 0x{self.start:06X}')
        return self.start + index * self.stride


def read_archive(rom, start, end, trailer_size=0):
    sections = []
    cursor = start
    for stride in OBJ_SECTIONS:
        require(cursor + 4 <= end, f'Table OBJ tronquée à 0x{cursor:06X}')
        count, = unpack_from('<I', rom, cursor)
        section = Section(cursor + 4, count, stride)
        sections.append(section)
        cursor = section.start + count * stride
    require(cursor + trailer_size == end, f'Longueur d’archive incohérente à 0x{start:06X}')
    return sections


def rom_offset(address):
    return address - ROM_BASE if address else ''


def verify_maps(rom):
    plans = index_rows('cartes/Cartes.csv', 84)
    tilesets = index_rows('cartes/Tuiles.csv', 31)
    palettes = index_rows('cartes/Palettes.csv', 47)
    streams = index_rows('cartes/Flux.csv', 272)
    tile_offsets, color_offsets, layer_offsets = set(), set(), set()
    plan_periods = defaultdict(set)
    for row in plans:
        layout = number(row['id_plan'])
        require(0 <= layout < 66, f'Plan hors limites {layout}')
        record = MAP_TABLE + 40 * layout
        tiles, day, night, bg3, bg2, bg1, _, _, width, height, flags = unpack_from('<8IHHI', rom, record)
        period = row['periode']
        require(period not in plan_periods[layout], f'Période répétée pour le plan {layout}')
        plan_periods[layout].add(period)
        require((period == 'jour_et_nuit' and day == night) or (period in ('jour', 'nuit') and day != night),
                f'Variantes de palette incohérentes pour le plan {layout}')
        color = night if period == 'nuit' else day
        expect(row, offset_entree_rom=record, adresse_entree_gba=record + ROM_BASE, drapeaux=flags,
               largeur_tuiles=width, hauteur_tuiles=height, largeur_px=width*8, hauteur_px=height*8,
               offset_tuiles_rom=rom_offset(tiles), offset_palette_rom=rom_offset(color),
               offset_palette_jour_rom=rom_offset(day), offset_palette_nuit_rom=rom_offset(night),
               offset_bg3_rom=rom_offset(bg3), offset_bg2_rom=rom_offset(bg2), offset_bg1_rom=rom_offset(bg1))
        tile_offsets.add(rom_offset(tiles))
        color_offsets.update((rom_offset(day), rom_offset(night)))
        layer_offsets.update(rom_offset(address) for address in (bg3, bg2, bg1) if address)
    require(len(plan_periods) == 66, 'Les 66 plans doivent être présents')
    require(Counter(map(len, plan_periods.values())) == {1: 48, 2: 18}, 'Répartition jour/nuit incohérente')
    require({number(row['offset_rom']) for row in tilesets} == tile_offsets, 'Jeux de tuiles de carte incomplets')
    require({number(row['offset_rom']) for row in palettes} == color_offsets, 'Palettes de carte incomplètes')
    require({number(row['offset_rom']) for row in streams} == tile_offsets | color_offsets | layer_offsets,
            'Flux de carte incomplets')
    for row in streams:
        start, end = number(row['offset_rom']), number(row['offset_fin_lue_exclue_rom'])
        require(start < end <= len(rom), f'Bornes invalides pour le flux 0x{start:06X}')
        expect(row, adresse_gba=ROM_BASE + start, octets_lus_compresses=end-start)
    return len(plans), len(streams)


def group_metadata(rom, tables, group):
    _, descriptors, oam, tiles, palettes, auxiliary, _ = tables
    offset = descriptors[group]
    oam_count, oam_index, tile_count, tile_index, palettes_count, palette_index, aux_count, aux_index = unpack_from(
        '<8H', rom, offset)
    for section, first, count in ((oam, oam_index, oam_count), (tiles, tile_index, tile_count),
                                  (palettes, palette_index, palettes_count), (auxiliary, aux_index, aux_count)):
        if count:
            section[first + count - 1]
    return (offset, oam[oam_index] if oam_count else '', oam_count,
            tiles[tile_index] if tile_count else '', tile_count,
            palettes[palette_index] if palettes_count else '', palette_index, palettes_count)


def signed_offset(value, bits):
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign


def verify_image_rows(rom, tables, archive_start, rows, actor):
    selectors, _, _, tiles, _, _, timings = tables
    used_multibank = 0
    for index, row in enumerate(rows):
        group = index
        if not actor:
            count, first = unpack_from('<HH', rom, selectors[index])
            require(count == 1, f'Sélection du portrait {index} inattendue')
            group, _ = unpack_from('<HH', rom, timings[first])
        (descriptor, oam_offset, oam_count, tile_start, tile_count,
         palette_offset, first_palette, bank_count) = group_metadata(rom, tables, group)
        left, top, right, bottom = [], [], [], []
        banks = set()
        for i in range(oam_count):
            attr0, attr1, attr2, _ = unpack_from('<4H', rom, oam_offset + 8*i)
            require(attr0 & 0x3F00 == 0 and attr0 >> 14 < 3, f'Forme OAM inattendue à 0x{oam_offset:06X}')
            width, height = GBA_OBJ_SIZES[attr0 >> 14][attr1 >> 14]
            x, y = signed_offset(attr1 & 0x1FF, 9), signed_offset(attr0 & 0xFF, 8)
            left.append(x)
            top.append(y)
            right.append(x + width)
            bottom.append(y + height)
            local_bank = attr2 >> 12
            require(local_bank < bank_count and (attr2 & 0x3FF) + width*height//64 <= tile_count,
                    f'Tuiles ou banque OAM hors limites pour le groupe {group}')
            banks.add(first_palette + local_bank)
        origin_x, origin_y = min(left), min(top)
        expect(row, id=index, archive_offset_rom=archive_start, descripteur=group,
               selecteur_offset_rom='' if actor else selectors[index], descripteur_offset_rom=descriptor,
               oam_offset_rom=oam_offset, entrees_oam=oam_count, tuiles_offset_rom=tile_start,
               nombre_tuiles=tile_count, premiere_tuile=(tile_start-tiles.start)//32,
               palette_offset_rom=palette_offset, banque_initiale=first_palette, nombre_banques=bank_count,
               banques_oam='|'.join(map(str, sorted(banks))), origine_x=origin_x, origine_y=origin_y,
               largeur_px=max(right)-origin_x, hauteur_px=max(bottom)-origin_y)
        used_multibank += bank_count > 1
    return used_multibank


def verify_actors(rom):
    known = (
        ('portrait', 0x52D984, 0x5E0A4, 32, '34c23aced1a4f23ba80d1429a87f4c8a7ca11b0458c61a37a6eb48731440bbd2'),
        ('sprite', 0x58BA28, 0xDB638, 0, '19a8733e132573478713e9b6e48e9650a702e62516209159787d26f270933736'),
    )
    color_rows = iter(index_rows('personnages/Palettes-personnages-A4NE.csv', 3440))
    actor_tables = None
    sprite_rows = []
    for family, start, length, tail, digest in known:
        end = start + length
        require(sha256(rom[start:end]).hexdigest() == digest, f'Empreinte de l’archive {family} différente')
        tables = read_archive(rom, start, end, tail)
        actor = family == 'sprite'
        filename = 'Sprites-A4NE.csv' if actor else 'Portraits-A4NE.csv'
        rows = index_rows(f'personnages/{filename}', 3009 if actor else 184)
        multibank = verify_image_rows(rom, tables, start, rows, actor)
        require(multibank == (703 if actor else 0), f'Nombre d’images multibanques inattendu pour {family}')
        banks = tables[4]
        offsets = [banks[index] for index in range(banks.count)]
        if tail:
            offsets.append(end - tail)
        for bank, offset in enumerate(offsets):
            for index, word in enumerate(unpack_from('<16H', rom, offset)):
                rgb = tuple(((word >> shift) & 31)*255//31 for shift in (0, 5, 10))
                expect(next(color_rows), archive=family, banque=bank if bank < banks.count else 'hors index',
                       indice=index, offset_rom=offset+2*index, bgr555=word, rgb='#%02X%02X%02X' % rgb,
                       transparent_en_obj='oui' if index == 0 else 'non')
        if actor:
            actor_tables = tables
            sprite_rows = rows
    require(next(color_rows, None) is None, 'L’index des palettes contient des entrées supplémentaires')
    selectors, _, _, _, _, _, timings = actor_tables
    timed_rows = iter(index_rows('personnages/Animations-A4NE.csv', 5980))
    used_entries = defaultdict(set)
    for selector in range(selectors.count):
        count, first = unpack_from('<HH', rom, selectors[selector])
        for sequence_pos in range(count):
            offset = timings[first+sequence_pos]
            group, duration = unpack_from('<HH', rom, offset)
            expect(next(timed_rows), selecteur=selector, selecteur_hex=selector,
                   selecteur_offset_rom=selectors[selector], position_sequence=sequence_pos,
                   descripteur=group, duree_native=duration, timing_offset_rom=offset)
            used_entries[group].add(selector)
    require(next(timed_rows, None) is None and len(used_entries) == 2963, 'Index des animations incohérent')
    for group, row in enumerate(sprite_rows):
        expect(row, selecteurs_animation='|'.join(map(str, sorted(used_entries.get(group, ())))))
    return len(sprite_rows)


def verify_obj_archives(rom):
    rows = index_rows('archives-obj/Archives-OBJ.csv', 52)
    catalogs = {}
    for row in rows:
        start, size = number(row['offset_rom']), number(row['octets'])
        end = start + size
        require(end <= len(rom), f'Archive hors ROM à 0x{start:06X}')
        expect(row, sha256_brut=sha256(rom[start:end]).hexdigest())
        tables = read_archive(rom, start, end)
        expect(row, descripteurs=tables[1].count, unites_de_tuile_32_octets=tables[3].count,
               banques_de_16_couleurs=tables[4].count)
        catalogs[start] = tables
    require(len(catalogs) == len(rows), 'Archives OBJ dupliquées')
    groups = index_rows('archives-obj/Groupes-OBJ.csv', 947)
    seen = defaultdict(set)
    for row in groups:
        archive, group = number(row['archive_offset_rom']), number(row['groupe'])
        require(group not in seen[archive], f'Groupe {group} dupliqué dans l’archive 0x{archive:06X}')
        seen[archive].add(group)
        offset, oam, oam_count, tiles, tile_count, palettes, _, bank_count = group_metadata(
            rom, catalogs[archive], group)
        expect(row, descripteur_offset_rom=offset, objets_oam=oam_count, oam_offset_rom=oam,
               tuiles_offset_rom=tiles, octets_tuiles=tile_count*32,
               palettes_offset_rom=palettes, banques_palette=bank_count)
    for start, tables in catalogs.items():
        require(seen[start] == set(range(tables[1].count)), f'Groupes manquants dans l’archive 0x{start:06X}')
    return catalogs, len(groups)


def verify_items(rom, common):
    names = ('index', 'groupes', 'oam', 'tiles', 'palettes', 'sixième', 'entrées')
    summary_path = INDEX / 'objets' / 'Verification-icones-objets-A4NE.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    for section, name in zip(common, names, strict=True):
        item = summary['sections'][name]
        require((number(item['rom']), item['quantite'], item['taille_en_octets']) ==
                (section.start, section.count, section.stride), f'Section commune {name} différente')
    links = {}
    selections, _, _, _, _, _, entries = common
    for row in index_rows('objets/Index-archive-commune-A4NE.csv', 578):
        icon, entry = number(row['id_icone']), number(row['id_entree'])
        count, first = unpack_from('<HH', rom, selections[icon])
        require(first <= entry < first+count and (icon, entry) not in links, f'Liaison d’icône {icon} invalide')
        group, metric = unpack_from('<HH', rom, entries[entry])
        descriptor, oam, oam_count, tiles, tile_count, palette, _, palette_count = group_metadata(rom, common, group)
        expect(row, index_rom=selections[icon], entree_rom=entries[entry], metrique_entree=metric,
               id_groupe=group, descripteur_rom=descriptor, descripteurs_oam=oam_count,
               oam_rom=oam, unites_tuiles=tile_count, tuiles_rom=tiles, octets_tuiles=tile_count*32,
               banques_palette=palette_count, palette_rom=palette, octets_palette=palette_count*32)
        links[icon, entry] = row
    require(len({entry for _, entry in links}) == entries.count, 'Entrées de l’archive commune incomplètes')
    object_tables = {
        'outil': ('gToolInfo', 0x0EAB0C, 81, 12, 4),
        'aliment': ('gFoodInfo', 0x0EDCD8, 171, 16, 8),
        'article': ('gArticleInfo', 0x0EFED4, 95, 12, 4),
    }
    rows = index_rows('objets/Index-icones-objets-A4NE.csv', 347)
    listed_objects = set()
    for row in rows:
        category, item_id = row['categorie'], number(row['id_objet'])
        symbol, start, count, stride, icon_offset = object_tables[category]
        require(0 <= item_id < count and (category, item_id) not in listed_objects, f'Objet {category} {item_id} invalide')
        listed_objects.add((category, item_id))
        record = start + item_id*stride
        offset = record + icon_offset
        icon, = unpack_from('<H', rom, offset)
        name_pointer, = unpack_from('<I', rom, record)
        name_start = rom_offset(name_pointer)
        require(isinstance(name_start, int) and 0 <= name_start < len(rom), f'Nom ROM invalide pour {category} {item_id}')
        name = rom[name_start:rom.index(b'\0', name_start)].decode('shift_jis')
        expect(row, table_objet=symbol, objet_rom=record, champ_icone_rom=offset,
               nom_rom_offset=name_start, nom_rom=name, id_icone=icon, largeur_px=16, hauteur_px=16)
        link = links[icon, number(row['id_entree'])]
        require(link['catalogue_objets'] == 'oui', f'Icône {icon} sans marquage inventaire')
        for field, value in link.items():
            if field != 'catalogue_objets':
                expect(row, **{field: value})
    return len(rows)


def verify_interface(rom):
    rows = index_rows('interface/Interface.csv', 113)
    for row in rows:
        ranges = row['plages_rom'].split('|')
        digests = row['sha256_plages_rom'].split('|')
        require(len(ranges) == len(digests), f'Nombre de plages incorrect pour {row["export_local"]}')
        for interval, expected in zip(ranges, digests, strict=True):
            start, length = map(number, interval.split('+'))
            require(length > 0 and start+length <= len(rom), f'Plage d’interface hors ROM {interval}')
            require(sha256(rom[start:start+length]).hexdigest() == expected,
                    f'Empreinte différente pour la plage {interval}')
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path, help='copie locale de la ROM américaine A4NE révision 0')
    args = parser.parse_args()
    try:
        rom = args.rom.read_bytes()
        require(len(rom) == 8*1024*1024 and rom[0xAC:0xB0] == b'A4NE' and rom[0xBC] == 0
                and sha1(rom).hexdigest() == ROM_SHA1, 'ROM A4NE révision 0 exacte requise')
        plans, streams = verify_maps(rom)
        sprites = verify_actors(rom)
        obj_archives, groups = verify_obj_archives(rom)
        items = verify_items(rom, obj_archives[0x6678A0])
        interface = verify_interface(rom)
    except (OSError, ValueError, KeyError, StopIteration) as error:
        parser.exit(1, f'Vérification interrompue. {error}\n')
    print(f'A4NE vérifié. {plans} variantes de plans, {streams} flux, 184 portraits et {sprites} sprites.')
    print(f'{len(obj_archives)} archives OBJ, {groups} groupes, {items} icônes et {interface} références d’interface.')


if __name__ == '__main__':
    main()
