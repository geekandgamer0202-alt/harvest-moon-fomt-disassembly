#!/usr/bin/env python3
"""Mesure les attributs OBJ et les pixels de Hoggy lorsque le pool est saturé."""

import argparse
import csv
import ctypes as c
from hashlib import sha256
from pathlib import Path
from struct import unpack_from
from zlib import error as ZlibError

from inspecter_etat import EWRAM, read_state, script_addresses, visible_objects
from preparer_mariage_deesse import preparer


ADRESSES = {b'A4NE': (0x083750AC, 0x0801FCB4), b'A4NP': (0x08375104, 0x0801FCC8)}
RETOUR_SPRITE = 0x030005FC
ATTRIBUT_SPRITE = 0x03000670
RETOUR_LABO = 0x0203FF00
CONTEXTE = EWRAM + 0x207C
PUINT = c.POINTER(c.c_uint32)
PINT = c.POINTER(c.c_int32)
ARRET = c.CFUNCTYPE(c.c_uint32, c.c_uint32, c.c_void_p, PINT, PINT)


class Jeu(c.Structure):
    _fields_ = [('path', c.c_char_p), ('data', c.c_void_p), ('size', c.c_size_t), ('meta', c.c_char_p)]


class MGBALibretro:
    def __init__(self, bibliotheque, rom):
        self.lib = c.CDLL(str(bibliotheque.resolve()))
        for nom, type_retour, types in (
            ('retro_load_game', c.c_bool, [c.POINTER(Jeu)]),
            ('retro_serialize_size', c.c_size_t, []),
            ('retro_unserialize', c.c_bool, [c.c_void_p, c.c_size_t]),
            ('retro_serialize', c.c_bool, [c.c_void_p, c.c_size_t]),
            ('fomt_breakpoints', None, [ARRET, PUINT, c.c_uint]),
            ('fomt_read8', c.c_uint32, [c.c_void_p, c.c_uint32]),
        ):
            fonction = getattr(self.lib, nom)
            fonction.restype, fonction.argtypes = type_retour, types
        self.touche = False
        self.pixels = b''
        self.format_video = None
        self.callbacks = []
        self.lier('environment', c.c_bool, (c.c_uint, c.c_void_p), self.environnement)
        self.lier('video_refresh', None, (c.c_void_p, c.c_uint, c.c_uint, c.c_size_t), self.video)
        self.lier('audio_sample_batch', c.c_size_t, (c.c_void_p, c.c_size_t), lambda _, n: n)
        self.lier('input_poll', None, (), lambda: None)
        self.lier('input_state', c.c_int16, (c.c_uint,) * 4, self.manette)
        self.lib.retro_init()
        self.rom = c.create_string_buffer(rom.read_bytes())
        info = Jeu(str(rom).encode(), c.addressof(self.rom), len(self.rom) - 1, None)
        if not self.lib.retro_load_game(c.byref(info)):
            self.lib.retro_deinit()
            raise ValueError('mGBA a refusé la ROM')

    def lier(self, nom, type_retour, types, fonction):
        callback = c.CFUNCTYPE(type_retour, *types)(fonction)
        self.callbacks.append(callback)
        getattr(self.lib, 'retro_set_' + nom)(callback)

    def environnement(self, commande, donnees):
        if commande == 10:
            self.format_video = c.cast(donnees, c.POINTER(c.c_int))[0]
            return self.format_video in (0, 2)
        return False

    def manette(self, port, appareil, _index, touche):
        return self.touche and (port, appareil, touche) == (0, 1, 8)

    def video(self, adresse, largeur, hauteur, pas):
        if adresse and (largeur, hauteur) == (240, 160) and self.format_video in (0, 2):
            image = c.string_at(adresse, pas * hauteur)
            self.pixels = b''.join(image[i:i + 480] for i in range(0, len(image), pas))

    def avancer(self, nombre, touche=False):
        self.touche = touche
        for _ in range(nombre):
            self.lib.retro_run()

    def charger(self, etat):
        if not self.lib.retro_unserialize(etat, len(etat)):
            raise ValueError('État refusé par mGBA')

    def etat(self):
        taille = self.lib.retro_serialize_size()
        etat = c.create_string_buffer(taille)
        if not self.lib.retro_serialize(etat, taille):
            raise ValueError('État indisponible')
        return read_state(etat.raw[:0x61000])[0]

    def fermer(self):
        self.lib.retro_unload_game()
        self.lib.retro_deinit()


def adresse_etat(gba):
    return EWRAM + gba - 0x02000000


def mot(etat, gba):
    return unpack_from('<I', etat, adresse_etat(gba))[0]


def rejoindre_ceremonie(core, sommeil, script):
    core.avancer(250)
    prepare, _ = read_state(preparer(sommeil))
    core.charger(prepare)
    core.avancer(3, touche=True)
    core.avancer(175)
    for _ in range(25):
        etat = core.etat()
        if unpack_from('<III', etat, CONTEXTE) == (1, script, 0x20B):
            core.avancer(4)
            return core.etat(), sha256(prepare).hexdigest()
        core.avancer(3, touche=True)
        core.avancer(70)
    raise ValueError('Point de départ de la cérémonie 0848 introuvable')


class Requetes:
    def __init__(self, core, indice_banque, monde, nombre):
        self.core, self.get, self.monde, self.nombre = core, indice_banque, monde, nombre
        self.cache = monde + 0x19C
        self.contexte = None
        self.reservations = []
        self.suivre = False
        self.sprite = None
        self.erreur = None
        self.callback = ARRET(self.observer)
        pc = (c.c_uint32 * 4)(self.get, RETOUR_LABO, RETOUR_SPRITE, ATTRIBUT_SPRITE)
        core.lib.fomt_breakpoints(self.callback, pc, len(pc))

    def observer(self, pc, cpu, regs, cpsr):
        try:
            return self.arret(pc, cpu, regs, cpsr)
        except Exception as erreur:
            self.erreur = erreur
            return 0

    def arret(self, pc, cpu, regs, cpsr):
        if pc == self.get and (regs[0], regs[1], regs[14]) == (self.monde, 8, RETOUR_SPRITE):
            self.suivre = True
            places = self.core.lib.fomt_read8(cpu, self.cache + 0xC14)
            if self.nombre and not self.reservations and places == 6:
                self.contexte = (regs[:16], cpsr[0])
                regs[1], regs[14] = 11, RETOUR_LABO | 1
                return self.get
        elif pc == RETOUR_LABO and self.contexte is not None:
            self.reservations.append(regs[0])
            if len(self.reservations) < self.nombre:
                regs[0], regs[1], regs[14] = self.monde, 11 + len(self.reservations), RETOUR_LABO | 1
            else:
                registres, drapeaux = self.contexte
                for index, valeur in enumerate(registres):
                    regs[index] = valeur
                cpsr[0] = drapeaux
                self.contexte = None
            return self.get
        elif pc == RETOUR_SPRITE and self.suivre and self.sprite is None:
            self.retour = regs[0]
        elif pc == ATTRIBUT_SPRITE and self.suivre and self.sprite is None:
            self.sprite = self.retour, regs[9], regs[10], regs[1] & 0xFFFF
            self.suivre = False
        return 0

    def fermer(self):
        self.core.lib.fomt_breakpoints(ARRET(), None, 0)
        if self.erreur:
            raise self.erreur


def empreinte(octets):
    return sha256(octets).hexdigest()


def comparer(avant, apres):
    if len(avant) != 76800 or len(apres) != len(avant):
        raise ValueError('Trame vidéo 240 × 160 sur 16 bits attendue')
    points = [(i % 240, i // 240) for i in range(240 * 160)
              if avant[2 * i:2 * i + 2] != apres[2 * i:2 * i + 2]]
    if not points:
        return 0, '', '', '', ''
    x, y = zip(*points)
    return len(points), min(x), min(y), max(x), max(y)


def mesurer(core, etat, script, get):
    scene = mot(etat, 0x020023D0)
    monde = mot(etat, mot(etat, scene + 4) + 0xA8)
    if mot(etat, mot(etat, monde + 4)) != 12:
        raise ValueError('Carte de l’église attendue')
    hoggy = mot(etat, monde + 8 + 4 * 41)
    controleur = mot(etat, hoggy + 0x10)
    if etat[adresse_etat(controleur + 0xA0)] != 8:
        raise ValueError('La ressource de palette de Hoggy doit être 8')
    cache = adresse_etat(monde + 0x19C)
    observations = {}
    for nombre in (0, 6, 7):
        core.charger(etat)
        images = []
        for image in range(7):
            requetes = Requetes(core, get, monde, nombre if image < 4 else 0)
            try:
                core.avancer(1)
            finally:
                requetes.fermer()
            pixels, precedent = core.pixels, core.etat()
            if unpack_from('<III', precedent, CONTEXTE) != (1, script, 0x20B) or requetes.sprite is None:
                raise ValueError('Rendu de Hoggy indisponible')
            retour, x, y, attr2_cpu = requetes.sprite
            oam = precedent[0xC00:0x1000]
            obj, = (o for o in visible_objects(oam) if (o['x'], o['y']) == (x, y) and o['bpp'] == 4)
            attr2_oam = int(obj['attributs'][2], 16)
            banque = attr2_oam >> 12
            palette = precedent[0xA00 + 32 * banque:0xA20 + 32 * banque]
            details = (len(requetes.reservations), precedent[cache + 0xC14], retour, precedent[cache + 8],
                       attr2_cpu, obj['index_oam'], x, y, attr2_oam, banque, empreinte(palette))
            images.append((details, pixels, oam, precedent[0x11000:0x19000], precedent[0xBE0:0xC00]))
        observations[nombre] = images

    for nombre, images in observations.items():
        for image, (details, pixels, oam, vram, palette15) in enumerate(images):
            reference, pixels_temoin, oam_temoin, vram_temoin, palette15_temoin = observations[0][image]
            reserves, places, retour, memo, cpu, index, x, y, attr, banque, palette = details
            actif = image < 4
            differences = comparer(pixels_temoin, pixels)
            retour_attendu = {0: 6, 6: 12, 7: -1}[nombre] if actif else 6
            attr_attendu = {0: 0x68D8, 6: 0xC8D8, 7: 0xF8D8}[nombre] if 0 < image <= 4 else 0x68D8
            visible_sature = nombre == 7 and 0 < image <= 4
            pos_attr = index * 8 + 4
            if not (
                reserves == (nombre if actif else 0) and places == (13 if reserves else 7)
                and retour == retour_attendu and memo == retour + 16
                and cpu == (0x08D8 | ((retour & 15) << 12)) and attr == attr_attendu
                and (index, x, y) == (6, 224, 51)
                and oam[:pos_attr] + oam[pos_attr + 2:] == oam_temoin[:pos_attr] + oam_temoin[pos_attr + 2:]
                and vram == vram_temoin and palette15 == palette15_temoin
                and ((palette != reference[-1]) == visible_sature)
                and differences[0] == (104 if visible_sature else 0)
            ):
                raise ValueError(f'Résultat vidéo inattendu pour {nombre} réservations à l’image {image}')
            yield (nombre, image, reserves, places, retour, memo, f'0x{cpu:04X}', index, x, y,
                   f'0x{attr:04X}', banque, palette, empreinte(palette15), empreinte(pixels), *differences)


def enregistrer(chemin, titre, lignes):
    with chemin.open('x', encoding='utf-8', newline='') as fichier:
        writer = csv.writer(fichier, lineterminator='\n')
        writer.writerow(titre.split(','))
        writer.writerows(lignes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('libretro', type=Path, help='Cœur mGBA 0.10.5 avec les points d’arrêt du dépôt')
    parser.add_argument('rom', type=Path)
    parser.add_argument('sommeil', type=Path, help='État de confirmation du sommeil au 2 printemps, an 1')
    parser.add_argument('destination', type=Path, help='Nouveau fichier CSV')
    args = parser.parse_args()
    try:
        edition, _ = script_addresses(args.rom)
        script, get = ADRESSES[edition]
        sommeil = args.sommeil.read_bytes()
        if read_state(sommeil)[1] != edition:
            raise ValueError('La ROM et l’état doivent relever de la même édition')
        core = MGBALibretro(args.libretro, args.rom)
        try:
            base, etat_prepare = rejoindre_ceremonie(core, sommeil, script)
            prefixe = (edition.decode(), empreinte(sommeil), etat_prepare)
            lignes = [(*prefixe, *ligne) for ligne in mesurer(core, base, script, get)]
        finally:
            core.fermer()
        enregistrer(
            args.destination,
            'edition,sha256_sommeil,sha256_prepare_decompresse,scenario_reservations,image,'
            'reservations_actives,places_utilisees,retour_get,octet_memo,attr2_cpu,index_oam,x_obj,y_obj,'
            'attr2_oam,banque_oam,sha256_palette_obj,sha256_banque_15,sha256_pixels_16bits,'
            'pixels_modifies,x_min,y_min,x_max,y_max',
            lignes,
        )
    except (AttributeError, OSError, ValueError, ZlibError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print(f'{edition.decode()} · {len(lignes)} images vérifiées')


if __name__ == '__main__':
    main()
