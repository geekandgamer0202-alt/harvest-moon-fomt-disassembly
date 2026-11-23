#!/usr/bin/env python3
"""Vérifie dans les ROM les appels directs aux routines de GameEventState."""

import argparse
from array import array
from pathlib import Path
import sys

from exporter_routines_natives import cible_bl, charger_rom, ecrire_csv, hex_rom


BASES = {'A4NE': 0x09C5F4, 'A4NP': 0x09C624}
ROUTINES = {
    'HasRegisteredEvents': 0x00,
    'RegisterEventVariable': 0x0C,
    'RemoveEventVariable': 0x50,
    'IsActiveRomanceEvent': 0xA0,
    'SetActiveRomanceEvent': 0xB8,
    'ClearActiveRomanceEvent': 0xBC,
}

# Les appelants sont identifiés dans les sources Wokann. Chaque destination BL
# est contrôlée indépendamment dans les deux ROM avant l’export.
APPELS = (
    (0x01775E, 'HasRegisteredEvents', 'GameSceneWorld::GameSceneWorld', 'construction_monde'),
    (0x018292, 'HasRegisteredEvents', 'GameSceneWorld::Update', 'changement_fatigue'),
    (0x019ECC, 'HasRegisteredEvents', 'GameSceneWorld::ChangeMap', 'changement_carte'),
    (0x01B908, 'IsActiveRomanceEvent', 'GameSceneWorld::vfunc_48', 'selection_palette_obj_eglise'),
    (0x01EDC8, 'HasRegisteredEvents', 'func_0801EAA0', 'mise_a_jour_monde'),
    (0x024BBE, 'IsActiveRomanceEvent', 'func_08024B9C', 'etat_joueur_clinique'),
    (0x0455F2, 'IsActiveRomanceEvent', 'func_080455D8', 'etat_romance_ou_compteur'),
    (0x045696, 'IsActiveRomanceEvent', 'UpdateScriptRomanceEvent', 'test_avant_retrait_romance'),
    (0x0456A6, 'ClearActiveRomanceEvent', 'UpdateScriptRomanceEvent', 'retrait_romance'),
    (0x0456C8, 'SetActiveRomanceEvent', 'UpdateScriptRomanceEvent', 'inscription_romance'),
    (0x0456FA, 'IsActiveRomanceEvent', 'UpdateScriptRomanceEvent', 'test_apres_progression_romance'),
    (0x045708, 'ClearActiveRomanceEvent', 'UpdateScriptRomanceEvent', 'retrait_apres_progression_romance'),
    (0x04E0C6, 'RegisterEventVariable', 'VarSet', 'notification_etat_1'),
    (0x04E0E2, 'RemoveEventVariable', 'VarSet', 'notification_etat_0_ou_2'),
)


def trouver_appels(rom, cibles):
    mots = array('H', rom)
    if sys.byteorder == 'big':
        mots.byteswap()
    appels = {}
    for i, (haut, bas) in enumerate(zip(mots, mots[1:])):
        if haut & 0xF800 == 0xF000 and bas & 0xF800 == 0xF800:
            site = 2 * i
            cible = cible_bl(rom, site)
            if cible in cibles:
                appels[site] = cible
    return appels


def verifier(rom, edition):
    base = BASES[edition]
    pas = 0 if edition == 'A4NE' else 0x14
    attendu = {site + pas: base + ROUTINES[nom] for site, nom, _, _ in APPELS}
    mesures = trouver_appels(rom, set(attendu.values()))
    if mesures != attendu:
        raise ValueError(f'Appels Thumb inattendus pour {edition}')
    return mesures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('roms', type=Path, metavar='ROM', nargs=2)
    parser.add_argument('destination', type=Path, help='Nouveau fichier CSV')
    args = parser.parse_args()
    try:
        roms = {edition: rom for rom, edition in map(charger_rom, args.roms)}
        if set(roms) != set(BASES):
            raise ValueError('Les deux ROM A4NE et A4NP sont requises.')
        if args.destination.exists():
            raise ValueError(f'Le fichier de destination existe déjà ({args.destination}).')
        a4ne, a4np = (verifier(roms[edition], edition) for edition in BASES)
        ecrire_csv(args.destination,
                   ('appelant', 'routine', 'role', 'site_a4ne_rom', 'cible_a4ne_rom',
                    'site_a4np_rom', 'cible_a4np_rom'),
                   ((appelant, nom, role, hex_rom(site), hex_rom(a4ne[site]),
                     hex_rom(site + 0x14), hex_rom(a4np[site + 0x14]))
                    for site, nom, appelant, role in APPELS))
    except (OSError, ValueError) as erreur:
        parser.exit(1, f'{erreur}\n')


if __name__ == '__main__':
    main()
