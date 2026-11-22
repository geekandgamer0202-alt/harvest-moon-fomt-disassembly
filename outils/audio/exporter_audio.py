#!/usr/bin/env python3
"""Inventorie les séquences, pistes et instruments M4A de FoMT A4NE ou A4NP."""

import argparse
from hashlib import sha256
from pathlib import Path
import re
from struct import unpack_from
import sys
from tempfile import TemporaryDirectory


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'economie'))
from exporter_economie import BASE_GBA, charger_rom, ecrire_csv, hex_rom


TABLES = {'A4NE': 0x13ABF0, 'A4NP': 0x13AC48}
NOMBRE_SEQUENCES = 211
NOMBRE_LECTEURS = 5
TAILLES_BANQUES = (128, 135)
ATTENTES = (*range(25), 28, 30, 32, 36, 40, 42, 44, 48, 52, 54, 56, 60,
            64, 66, 68, 72, 76, 78, 80, 84, 88, 90, 92, 96)
PARAMETRE_SIMPLE = {0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF, 0xC0, 0xC1, 0xC2,
                    0xC3, 0xC4, 0xC5, 0xC8}


def exiger(condition, message):
    if not condition:
        raise ValueError(message)


def offset_vers(rom, position):
    position_rom = unpack_from('<I', rom, position)[0] - BASE_GBA
    exiger(0 <= position_rom < len(rom), f'Pointeur ROM invalide à {hex_rom(position)}')
    return position_rom


def lire_symboles(chemin):
    if chemin is None:
        return {}
    texte = chemin.read_text(encoding='utf-8')
    motif = r'typedef enum MaryAudioSequenceId\s*\{(.*?)\}\s*MaryAudioSequenceId\s*;'
    enum = re.search(motif, texte, re.DOTALL)
    exiger(enum is not None, 'Enum MaryAudioSequenceId introuvable')
    entrees = re.findall(r'\b(AUDIO_\w+)\s*=\s*(\d+)\s*,', enum[1])
    exiger([int(index) for _, index in entrees] == list(range(NOMBRE_SEQUENCES)),
           'Les symboles doivent couvrir les 211 ID dans l’ordre')
    return {int(index): symbole for symbole, index in entrees}


def famille(symbole):
    return {'BGM': 'musique', 'AMBIENCE': 'ambiance', 'RECORD': 'disque',
            'SFX': 'effet'}.get(symbole.split('_')[1], 'indeterminee')


def lire_piste(rom, debut, fin, banque, nombre_instruments):
    pc = debut
    ticks = statut = repetition = note = notes = 0
    programme = None
    retours = ()
    visites = {}
    commandes = set()
    programmes = set()
    percussions = set()
    tempos = set()
    flux = set()
    while debut <= pc < fin:
        etat = (pc, statut, retours, repetition, programme, note)
        if etat in visites:
            entree, intro = pc, visites[etat]
            exiger(ticks > intro, f'Cycle sans attente à {hex_rom(pc)}')
            terminaison = 'boucle', hex_rom(entree), intro, ticks - intro
            break
        visites[etat] = ticks
        exiger(len(visites) <= 100_000, f'Piste trop complexe à {hex_rom(debut)}')
        adresse = pc
        commandes.add(adresse)
        opcode = rom[pc]
        if opcode >= 0x80:
            pc += 1
            if opcode >= 0xBD:
                statut = opcode
        else:
            opcode = statut

        if 0x80 <= opcode <= 0xB0:
            ticks += ATTENTES[opcode - 0x80]
        elif opcode == 0xB1:
            terminaison = 'fin', '', ticks, ''
            break
        elif opcode in (0xB2, 0xB3, 0xB5):
            exiger(pc + 4 + (opcode == 0xB5) <= fin, f'Cible tronquée à {hex_rom(adresse)}')
            quantite = rom[pc] if opcode == 0xB5 else 0
            pc += int(opcode == 0xB5)
            cible = offset_vers(rom, pc)
            exiger(debut <= cible < fin, f'Saut hors de la piste à {hex_rom(adresse)}')
            pc += 4
            operation = {0xB2: 'GOTO', 0xB3: 'PATT', 0xB5: 'REPT'}[opcode]
            flux.add((adresse, operation, cible))
            if opcode == 0xB3:
                exiger(len(retours) < 3, f'Pile de motifs pleine à {hex_rom(adresse)}')
                retours += (pc,)
            if quantite:
                repetition += 1
                if repetition >= quantite:
                    repetition = 0
                    continue
            pc = cible
        elif opcode == 0xB4:
            if retours:
                pc = retours[-1]
                retours = retours[:-1]
                flux.add((adresse, 'PEND', pc))
        elif opcode in PARAMETRE_SIMPLE:
            exiger(pc < fin, f'Paramètre absent à {hex_rom(adresse)}')
            valeur = rom[pc]
            pc += 1
            if opcode == 0xBB:
                tempos.add(2 * valeur)
            if opcode == 0xBD:
                exiger(valeur < nombre_instruments, f'Instrument invalide à {hex_rom(adresse)}')
                programme = valeur
                programmes.add(valeur)
        elif opcode >= 0xCE:
            if pc < fin and rom[pc] < 0x80:
                note = rom[pc]
                pc += 1
                if opcode >= 0xCF:
                    for _ in range(2):
                        if pc >= fin or rom[pc] >= 0x80:
                            break
                        pc += 1
            if opcode >= 0xCF:
                notes += 1
                if programme is not None and rom[banque + 12 * programme] & 0x80:
                    percussions.add((programme, note))
        else:
            raise ValueError(f'Commande M4A 0x{opcode:02X} non gérée à {hex_rom(adresse)}')
    else:
        raise ValueError(f'La piste de {hex_rom(debut)} sort de sa plage à {hex_rom(pc)}')

    return (terminaison, len(commandes), notes, programmes, percussions, tempos, flux)


def lire_instruments(rom, banques, debut_cgb, fin_cgb):
    instruments = []
    pcm = set()
    for banque, n in banques.items():
        for index in range(n):
            position = banque + 12 * index
            type_voix, note, duree, pan, donnees, *adsr = unpack_from('<4BI4B', rom, position)
            cible = None
            exiger(not type_voix & 0xC0 or type_voix == 0x80,
                   f'Type d’instrument inconnu à {hex_rom(position)}')
            if type_voix == 0x80:
                famille_voix = 'percussion'
                cible = offset_vers(rom, position + 4)
                exiger(any(b <= cible < b + 12 * taille and (cible - b) % 12 == 0
                            for b, taille in banques.items()), 'Sous-table de percussion invalide')
            elif type_voix & 7 == 0:
                famille_voix = 'pcm'
                cible = offset_vers(rom, position + 4)
                pcm.add(cible)
            elif type_voix & 7 == 3:
                famille_voix = 'onde_cgb'
                cible = offset_vers(rom, position + 4)
                exiger(debut_cgb <= cible < fin_cgb and (cible - debut_cgb) % 16 == 0,
                       f'Onde CGB invalide à {hex_rom(position)}')
            else:
                exiger(type_voix & 7 in (1, 2, 4),
                       f'Type d’instrument inconnu à {hex_rom(position)}')
                famille_voix = 'impulsion_cgb' if type_voix & 7 in (1, 2) else 'bruit_cgb'
            instruments.append((hex_rom(banque), index, hex_rom(position), f'0x{type_voix:02X}',
                                famille_voix, note, duree, pan, f'0x{donnees:08X}',
                                '' if cible is None else hex_rom(cible), *adsr))
    return instruments, sorted(pcm)


def ecrire_bloc(dossier, famille_bloc, position, bloc):
    sous_dossier = dossier / famille_bloc
    sous_dossier.mkdir(exist_ok=True, parents=True)
    (sous_dossier / f'{hex_rom(position)}.bin').write_bytes(bloc)


def exporter(rom, version, dossier, symboles, binaires):
    table = TABLES[version]
    fin_table = table + 8 * NOMBRE_SEQUENCES
    exiger(rom[fin_table:fin_table + 4] == bytes(4), 'En-tête de séquence vide inattendu')
    cases = [(offset_vers(rom, p), *unpack_from('<HH', rom, p + 4))
             for p in range(table, fin_table, 8)]
    en_tetes = sorted({entete for entete, _, _ in cases})
    exiger(en_tetes[0] == fin_table, 'Pointeur vers la séquence vide inattendu')
    pistes_par_sequence = {}
    banques_trouvees = set()
    for entete in en_tetes[1:]:
        nombre, blocs, priorite, reverb = unpack_from('<4B', rom, entete)
        exiger(1 <= nombre <= 8 and blocs == 0, f'En-tête M4A inattendu à {hex_rom(entete)}')
        banque = offset_vers(rom, entete + 4)
        pistes = [offset_vers(rom, entete + 8 + 4 * i) for i in range(nombre)]
        exiger(fin_table < pistes[0] and pistes == sorted(set(pistes)) and pistes[-1] < entete,
               f'Bornes de pistes inattendues pour {hex_rom(entete)}')
        pistes_par_sequence[entete] = (pistes, banque, priorite, reverb)
        banques_trouvees.add(banque)

    banques = dict(zip(sorted(banques_trouvees), TAILLES_BANQUES, strict=True))
    bgm, sfx = banques
    debut_cgb = sfx + 12 * banques[sfx]
    debut_lecteurs = table - NOMBRE_LECTEURS * 12
    exiger(bgm + 12 * banques[bgm] == sfx and debut_cgb + 32 * 16 == debut_lecteurs,
           'Bornes des banques et des ondes CGB inattendues')
    instruments, pcm = lire_instruments(rom, banques, debut_cgb, debut_lecteurs)
    lecteurs = []
    for i in range(NOMBRE_LECTEURS):
        position = debut_lecteurs + 12 * i
        etat, pistes, max_pistes, reserve = unpack_from('<IIBxH', rom, position)
        lecteurs.append((i, hex_rom(position), f'0x{etat:08X}', f'0x{pistes:08X}', max_pistes, reserve))

    echantillons = []
    premiere_piste = min(pistes[0] for pistes, _, _, _ in pistes_par_sequence.values())
    for i, (position, limite) in enumerate(zip(pcm, pcm[1:] + [premiere_piste])):
        type_pcm, flags, frequence, debut_boucle, taille = unpack_from('<HHIII', rom, position)
        boucle = bool(flags & 0xC000)
        debut = position + 16
        exiger(type_pcm == 0 and 0 < taille <= limite - debut and (not boucle or debut_boucle < taille),
               f'En-tête PCM inattendu à {hex_rom(position)}')
        bloc = rom[debut:debut + taille]
        echantillons.append((i, hex_rom(position), hex_rom(debut), taille, frequence,
                             f'0x{flags:04X}', int(boucle), debut_boucle, sha256(bloc).hexdigest()))
        if binaires:
            ecrire_bloc(dossier / 'binaires', 'pcm', debut, bloc)

    ondes = []
    for i, debut in enumerate(range(debut_cgb, debut_lecteurs, 16)):
        bloc = rom[debut:debut + 16]
        ondes.append((i, hex_rom(debut), len(bloc), sha256(bloc).hexdigest()))
        if binaires:
            ecrire_bloc(dossier / 'binaires', 'ondes-cgb', debut, bloc)

    sequences = []
    pistes_export = []
    sauts = []
    for i, (entete, ms, me) in enumerate(cases):
        symbole = symboles.get(i, '')
        nom_famille = famille(symbole) if symbole else 'indeterminee'
        position = table + 8 * i
        if entete == fin_table:
            sequences.append((i, symbole, 'case_vide', hex_rom(position), hex_rom(entete),
                              ms, me, 0, '', '', '', 0))
            continue
        pistes, banque, priorite, reverb = pistes_par_sequence[entete]
        exiger(ms < len(lecteurs) and len(pistes) <= lecteurs[ms][4], 'Index de lecteur invalide')
        boucles = 0
        for index, (debut, fin) in enumerate(zip(pistes, pistes[1:] + [entete]), 1):
            try:
                terminaison, commandes, notes, voix, percussions, tempos, flux = lire_piste(
                    rom, debut, fin, banque, banques[banque])
            except ValueError as erreur:
                raise ValueError(f'Séquence {i}, piste {index} ({erreur})') from erreur
            boucles += terminaison[0] == 'boucle'
            pistes_export.append((i, index, hex_rom(debut), hex_rom(fin), fin - debut,
                                  *terminaison, commandes, notes, ' '.join(map(str, sorted(voix))),
                                  ' '.join(f'{v}/{n}' for v, n in sorted(percussions)),
                                  ' '.join(map(str, sorted(tempos)))))
            for adresse, commande, cible in sorted(flux):
                sauts.append((i, index, hex_rom(adresse), commande, hex_rom(cible)))
            if binaires:
                ecrire_bloc(dossier / 'binaires', 'pistes', debut, rom[debut:fin])
        sequences.append((i, symbole, nom_famille, hex_rom(position), hex_rom(entete), ms, me,
                          len(pistes), priorite, reverb, hex_rom(banque), boucles))

    exports = (
        ('Sequences', ('id_audio', 'symbole', 'famille', 'case_rom', 'en_tete_rom', 'ms', 'me',
                       'pistes', 'priorite_rom', 'reverb_rom', 'banque_rom', 'pistes_en_boucle'), sequences),
        ('Lecteurs', ('id_lecteur', 'case_rom', 'etat_gba', 'pistes_gba', 'pistes_max', 'champ_0a'), lecteurs),
        ('Pistes', ('id_audio', 'piste', 'debut_rom', 'fin_rom_exclue', 'octets', 'sortie',
                    'entree_cycle_rom', 'ticks_avant_sortie_ou_cycle', 'ticks_cycle', 'positions_lues',
                    'commandes_note_parcourues', 'programmes', 'percussions_programme_note', 'tempos_definis'),
         pistes_export),
        ('Sauts-pistes', ('id_audio', 'piste', 'commande_rom', 'commande', 'cible_rom'), sauts),
        ('Instruments', ('banque_rom', 'programme', 'fiche_rom', 'type_rom', 'famille', 'note',
                         'duree', 'pan_sweep', 'parametre_04', 'cible_rom', 'attaque', 'decroissance',
                         'maintien', 'relachement'), instruments),
        ('Echantillons', ('id_pcm', 'en_tete_rom', 'donnees_rom', 'taille', 'frequence_rom',
                          'flags_rom', 'boucle_active', 'position_boucle_rom', 'sha256'), echantillons),
        ('Ondes-CGB', ('id_onde', 'donnees_rom', 'taille', 'sha256'), ondes),
    )
    for nom, colonnes, donnees in exports:
        ecrire_csv(dossier / f'{nom}-{version}.csv', colonnes, donnees)
    return len(pistes_export), len(instruments), len(echantillons), len(ondes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('destination', type=Path, help='Nouveau dossier pour les exports')
    parser.add_argument('--constantes', type=Path, help='Fichier fomt_constants.mary.h pour nommer les séquences')
    parser.add_argument('--binaires', action='store_true', help='Extrait aussi les pistes, PCM et ondes CGB')
    args = parser.parse_args()
    try:
        rom, version = charger_rom(args.rom)
        symboles = lire_symboles(args.constantes)
        exiger(not args.destination.exists(), f'Le dossier {args.destination} existe déjà')
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.audio-', dir=args.destination.parent) as temporaire:
            lot = Path(temporaire) / 'audio'
            lot.mkdir()
            pistes, instruments, pcm, ondes = exporter(rom, version, lot, symboles, args.binaires)
            lot.rename(args.destination)
    except (OSError, ValueError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print(f'{version} · {NOMBRE_SEQUENCES} cases, {pistes} pistes, {instruments} voix, '
          f'{pcm} échantillons PCM et {ondes} ondes CGB.')


if __name__ == '__main__':
    main()
