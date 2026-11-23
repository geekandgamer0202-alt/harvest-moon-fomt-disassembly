#!/usr/bin/env python3
"""Relie les instructions VM et les variables aux tables Thumb A4NE et A4NP."""

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import re
from struct import unpack_from
from tempfile import TemporaryDirectory

from exporter_terrain import ecrire_csv
from indexer_scripts import BASE_GBA, EMPILEMENT_IMMEDIAT, charger_rom, hex_rom, indexer, lire_code


REPARTITEUR = {'A4NE': 0x03F8DC, 'A4NP': 0x03F8F0}
NOMBRE_LIAISONS = 327
NOMBRE_VARIABLES = 590
PREMIERE_ECRITURE = 28
PREMIERE_NOTIFICATION = 70
NOMBRE_NOTIFICATIONS = 396
VAR_GET, VAR_SET = 0x03D, 0x03E


def exiger(condition, message):
    if not condition:
        raise ValueError(message)


def mot(rom, position):
    return unpack_from('<I', rom, position)[0]


def cible_bl(rom, position):
    haut, bas = unpack_from('<HH', rom, position)
    exiger(haut & 0xF800 == 0xF000 and bas & 0xF800 == 0xF800,
           f'Instruction BL Thumb attendue à {hex_rom(position)}')
    relatif = ((haut & 0x7FF) << 12) | ((bas & 0x7FF) << 1)
    if relatif & 0x400000:
        relatif -= 0x800000
    return position + 4 + relatif


def cible_b(rom, position):
    opcode, = unpack_from('<H', rom, position)
    exiger(opcode & 0xF800 == 0xE000, f'Instruction B Thumb attendue à {hex_rom(position)}')
    relatif = ((opcode & 0x7FF) ^ 0x400) - 0x400
    return position + 4 + 2 * relatif


@dataclass(frozen=True)
class TableThumb:
    fonction: int
    offset: int
    destinations: tuple
    defaut: int | None = None

    def case(self, indice):
        return self.offset + 4 * indice

    def resume(self):
        return {
            'fonction_rom': hex_rom(self.fonction),
            'table_rom': hex_rom(self.offset),
            'cases': len(self.destinations),
            'destinations_distinctes': len(set(self.destinations)),
            'branche_defaut_rom': hex_rom(self.defaut) if self.defaut is not None else None,
        }


def lire_table(rom, fonction, position_pointeur, nombre, defaut=None):
    offset = mot(rom, fonction + position_pointeur) - BASE_GBA
    exiger(offset == fonction + position_pointeur + 4, f'Table inattendue à {hex_rom(offset)}')
    fin = offset + 4 * nombre
    destinations = tuple(pointeur - BASE_GBA for pointeur in unpack_from(f'<{nombre}I', rom, offset))
    exiger(all(fin <= cible < len(rom) and cible % 2 == 0 for cible in destinations),
           f'Destination Thumb invalide dans la table à {hex_rom(offset)}')
    return TableThumb(fonction, offset, destinations, defaut)


def lire_moteur(rom, version):
    repartiteur = lire_table(rom, REPARTITEUR[version], 0x24, NOMBRE_LIAISONS)
    lecteur = cible_bl(rom, repartiteur.destinations[VAR_GET] + 0x1E)
    ecrivain = cible_bl(rom, repartiteur.destinations[VAR_SET] + 0x30)
    exiger(mot(rom, lecteur + 0x20) + 1 == NOMBRE_VARIABLES, 'Borne VarGet inattendue')
    exiger(mot(rom, ecrivain + 0x30) + 1 == NOMBRE_VARIABLES - PREMIERE_ECRITURE,
           'Borne VarSet inattendue')
    exiger(unpack_from('<H', rom, ecrivain + 0x18)[0] == 0x391C,
           'L’index VarSet doit soustraire 28 avant le saut')
    lectures = lire_table(rom, lecteur, 0x24, NOMBRE_VARIABLES, cible_bl(rom, lecteur + 0x10))
    ecritures = lire_table(rom, ecrivain, 0x34, NOMBRE_VARIABLES - PREMIERE_ECRITURE,
                           cible_bl(rom, ecrivain + 0x20))
    apres_ecriture = ecritures.defaut
    exiger(mot(rom, apres_ecriture + 0x26) + 1 == NOMBRE_NOTIFICATIONS, 'Borne de notification inattendue')
    exiger(unpack_from('<H', rom, apres_ecriture + 0x0C)[0] == 0x3946,
           'L’index de notification doit soustraire 70 avant le saut')
    notifications = lire_table(rom, apres_ecriture, 0x2A, NOMBRE_NOTIFICATIONS,
                               cible_b(rom, apres_ecriture + 0x14))
    return repartiteur, lectures, ecritures, notifications


def lire_symboles(sources):
    code = (sources / 'src/script_engine.cc').read_text(encoding='utf-8')
    table = code.split('".LnativeScriptCallHandlers:', 1)[1].split('".LnativeScriptCallHandlersEnd:', 1)[0]
    dispositions = re.findall(r'\.word \.LscriptCall_([0-9A-F]+) @ 0x([0-9A-F]+) (\w+)', table)
    exiger([int(n, 16) for _, n, _ in dispositions] == list(range(NOMBRE_LIAISONS)),
           'La table des symboles natifs est incomplète')
    entete = (sources / 'data/scripts/eu/fomt_callables.mary.h').read_text(encoding='utf-8')
    table_mary = entete.split('mary_callable_table', 1)[1].split('};', 1)[0]
    noms = re.findall(r'/\*\s*0x([0-9A-F]+)\s*\*/\s*(\w+)', table_mary)
    exiger([int(n, 16) for n, _ in noms] == list(range(NOMBRE_LIAISONS)), 'Table Mary incomplète')
    declarations = re.sub(r'/\*.*?\*/', '', entete, flags=re.DOTALL)
    prototypes = {nom: (retour, ' '.join(args.split())) for retour, nom, args in
                  re.findall(r'^\s*(\w+(?:\s*\*)*)\s+(\w+)\(([^()]*)\)\s*;', declarations, re.MULTILINE)}
    liaisons = []
    for (relatif, _, natif), (_, mary) in zip(dispositions, noms, strict=True):
        exiger(natif == 'NULL' or natif in prototypes, f'Prototype introuvable pour {natif}')
        retour, arguments = prototypes.get(natif, ('', ''))
        liaisons.append((int(relatif, 16), natif, mary, retour, arguments))

    constantes = (sources / 'include/fomt_constants.mary.h').read_text(encoding='utf-8')
    enum = constantes.split('typedef enum MaryVarId', 1)[1].split('} MaryVarId;', 1)[0]
    variables = {int(n): nom for nom, n in re.findall(r'\b(VAR_\w+)\s*=\s*(\d+)\s*,', enum)}
    exiger(set(variables) == set(range(NOMBRE_VARIABLES)), 'Enum MaryVarId incomplet')
    return liaisons, variables


def lire_sites(rom, scripts):
    for script in scripts:
        code = script.sections[b'CODE']
        precedent = avant = (None, None)
        for position, opcode, operande in lire_code(rom, code):
            if opcode == 0x21:
                exiger(0 <= operande < NOMBRE_LIAISONS, f'Appel natif hors table à {hex_rom(position)}')
                indice = valeur = None
                if operande == VAR_GET and precedent[0] in EMPILEMENT_IMMEDIAT:
                    indice = precedent[1]
                if (operande == VAR_SET and precedent[0] in EMPILEMENT_IMMEDIAT
                        and avant[0] in EMPILEMENT_IMMEDIAT):
                    indice, valeur = avant[1], precedent[1]
                yield script.identifiant, position - code.debut - 4, position, operande, indice, valeur
            avant, precedent = precedent, (opcode, operande)


def decrire_branche(table, indice, premier_id):
    index = indice - premier_id
    if not 0 <= index < len(table.destinations):
        return 'hors_table', '', hex_rom(table.defaut)
    destination = table.destinations[index]
    chemin = 'branche_defaut' if destination == table.defaut else 'branche_dediee'
    return chemin, hex_rom(table.case(index)), hex_rom(destination)


def exporter(usa, europe, sources, dossier):
    symboles, noms_variables = lire_symboles(sources)
    moteurs = [lire_moteur(rom, version) for rom, version in ((usa, 'A4NE'), (europe, 'A4NP'))]
    (repart_us, lectures_us, ecritures_us, notifs_us), (repart_eu, lectures_eu, ecritures_eu, notifs_eu) = moteurs
    for us, eu in zip(*moteurs, strict=True):
        decalage = eu.fonction - us.fonction
        exiger(tuple(cible + decalage for cible in us.destinations) == eu.destinations,
               'Disposition des tables différente entre A4NE et A4NP')
        exiger(us.defaut is None or us.defaut + decalage == eu.defaut,
               'Branche de défaut différente entre A4NE et A4NP')
    for i, (relatif, _, _, _, _) in enumerate(symboles):
        exiger(repart_us.fonction + relatif == repart_us.destinations[i],
               f'Symbole incompatible avec l’entrée 0x{i:03X}')

    scripts_us, _ = indexer(usa, 'A4NE')
    scripts_eu, _ = indexer(europe, 'A4NP')
    sites = []
    acces = []
    appels = Counter()
    lectures = Counter()
    ecritures = Counter()
    for americain, europeen in zip(lire_sites(usa, scripts_us), lire_sites(europe, scripts_eu), strict=True):
        script, pc, us, id_natif, indice, valeur = americain
        exiger((script, pc, id_natif, indice, valeur) == europeen[:2] + europeen[3:],
               f'Sites divergents pour le script {script:04d}')
        identifiant = f'0x{id_natif:03X}'
        cle_site = f'{script:04d}', hex_rom(pc), hex_rom(us), hex_rom(europeen[2])
        appels[id_natif] += 1
        sites.append((*cle_site, identifiant))
        if id_natif in (VAR_GET, VAR_SET):
            if indice is not None:
                exiger(indice in noms_variables, f'Variable littérale inconnue à {hex_rom(us)}')
                (lectures if id_natif == VAR_GET else ecritures)[indice] += 1
            acces.append((*cle_site, symboles[id_natif][1], indice, noms_variables.get(indice, ''), valeur))

    liaisons = []
    for i, (_, natif, mary, retour, arguments) in enumerate(symboles):
        liaisons.append((f'0x{i:03X}', natif, mary, retour, arguments,
                         hex_rom(repart_us.case(i)), hex_rom(repart_us.destinations[i]),
                         hex_rom(repart_eu.case(i)), hex_rom(repart_eu.destinations[i]), appels[i]))

    variables = []
    for i in range(NOMBRE_VARIABLES):
        branche, case_us, cible_us = decrire_branche(ecritures_us, i, PREMIERE_ECRITURE)
        _, case_eu, cible_eu = decrire_branche(ecritures_eu, i, PREMIERE_ECRITURE)
        notif, notif_case_us, notif_cible_us = decrire_branche(notifs_us, i, PREMIERE_NOTIFICATION)
        _, notif_case_eu, notif_cible_eu = decrire_branche(notifs_eu, i, PREMIERE_NOTIFICATION)
        variables.append((i, noms_variables[i], hex_rom(lectures_us.case(i)), hex_rom(lectures_us.destinations[i]),
                          hex_rom(lectures_eu.case(i)), hex_rom(lectures_eu.destinations[i]),
                          branche, case_us, cible_us, case_eu, cible_eu,
                          notif, notif_case_us, notif_cible_us, notif_case_eu, notif_cible_eu, lectures[i], ecritures[i]))

    cle_site = ('script', 'pc_code', 'site_a4ne_rom', 'site_a4np_rom')
    ecrire_csv(dossier / 'Liaisons-natives-FoMT.csv',
               ('id_natif', 'symbole_natif', 'symbole_mary', 'retour_mary', 'parametres_mary',
                'case_a4ne_rom', 'handler_a4ne_rom', 'case_a4np_rom', 'handler_a4np_rom', 'sites'), liaisons)
    ecrire_csv(dossier / 'Sites-natifs-FoMT.csv', (*cle_site, 'id_natif'), sites)
    ecrire_csv(dossier / 'Acces-variables-FoMT.csv',
               (*cle_site, 'operation', 'id_variable_litteral', 'symbole_variable', 'valeur_litterale'), acces)
    ecrire_csv(dossier / 'Variables-natives-FoMT.csv',
               ('id_variable', 'symbole', 'case_lecture_a4ne_rom', 'lecture_a4ne_rom', 'case_lecture_a4np_rom',
                'lecture_a4np_rom', 'type_branche_ecriture', 'case_ecriture_a4ne_rom', 'ecriture_a4ne_rom',
                'case_ecriture_a4np_rom', 'ecriture_a4np_rom', 'type_branche_notification', 'case_notification_a4ne_rom',
                'notification_a4ne_rom', 'case_notification_a4np_rom', 'notification_a4np_rom',
                'lectures_litterales', 'ecritures_litterales'), variables)

    noms_tables = ('OnCall', 'VarGet', 'VarSet', 'NotificationVarSet')
    rapport = {version: {nom: table.resume() for nom, table in zip(noms_tables, moteur, strict=True)}
               for version, moteur in zip(('A4NE', 'A4NP'), moteurs, strict=True)}
    rapport['sites'] = len(sites)
    rapport['liaisons_utilisees'] = len(appels)
    rapport['lectures_litterales'] = sum(lectures.values())
    rapport['ecritures_litterales'] = sum(ecritures.values())
    (dossier / 'Tables-natives-FoMT.json').write_text(json.dumps(rapport, indent=2) + '\n', encoding='utf-8')
    return len(sites), len(appels), len(acces)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('a4ne', type=Path)
    parser.add_argument('a4np', type=Path)
    parser.add_argument('sources', type=Path, help='Racine du désassemblage Wokann de référence')
    parser.add_argument('destination', type=Path, help='Nouveau dossier pour les exports')
    args = parser.parse_args()
    try:
        usa, version_us = charger_rom(args.a4ne)
        europe, version_eu = charger_rom(args.a4np)
        exiger((version_us, version_eu) == ('A4NE', 'A4NP'), 'Indiquer la ROM USA puis la ROM Europe')
        exiger(not args.destination.exists(), f'Le dossier {args.destination} existe déjà')
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.routines-natives-', dir=args.destination.parent) as temporaire:
            lot = Path(temporaire) / 'natif'
            lot.mkdir()
            sites, liaisons, acces = exporter(usa, europe, args.sources, lot)
            lot.rename(args.destination)
    except (IndexError, OSError, ValueError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print(f'FoMT USA et Europe · {sites} sites, {liaisons} ID utilisés, {acces} accès aux variables.')


if __name__ == '__main__':
    main()
