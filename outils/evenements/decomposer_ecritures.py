#!/usr/bin/env python3
"""Retrouve les arguments de VarSet et les sources locales dans les scripts FoMT."""

import argparse
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from exporter_routines_natives import VAR_SET, exiger
from exporter_terrain import ecrire_csv
from indexer_scripts import EMPILEMENT_IMMEDIAT, charger_rom, hex_rom, indexer, lire_code, u32


RELEVES = Path(__file__).resolve().parents[2] / 'ressources/donnees/routines-natives'
BINAIRE = {0x07: '+', 0x08: '-', 0x09: '*', 0x0A: '/', 0x0B: '%', 0x0C: '&&', 0x0D: '||', 0x12: 'cmp'}
UNAIRE = {0x0E: 'inc', 0x0F: 'dec', 0x10: 'neg', 0x11: 'non'}


class ExpressionInconnue(ValueError):
    """Un chemin ou un opcode sort du périmètre de la décomposition."""


def lire_csv(nom):
    with (RELEVES / nom).open(encoding='utf-8', newline='') as fichier:
        return list(csv.DictReader(fichier))


def branches_jump(rom, section, indice):
    table = section.debut + 4
    groupe = table + u32(rom, table + 4 * indice)
    defaut = u32(rom, groupe + 4)
    return defaut, tuple(u32(rom, groupe + 12 + 8 * cas) for cas in range(u32(rom, groupe)))


def graphe(rom, script, instructions):
    """Prédécesseurs possibles, où chaque cible est un PC relatif à CODE."""
    predecesseurs = {pc: [] for pc in instructions}
    successeurs = {pc: [] for pc in instructions}
    fin = script.sections[b'CODE'].fin - script.sections[b'CODE'].debut - 4
    for pc, (opcode, operande, suivant) in instructions.items():
        destinations = ()
        if opcode == 0x18:
            destinations = (operande,)
        elif 0x19 <= opcode <= 0x1E:
            destinations = (operande, suivant)
        elif opcode == 0x24:
            defaut, cas = branches_jump(rom, script.sections[b'JUMP'], operande)
            destinations = (defaut if 0 < defaut < 0x80000000 else suivant, *cas)
        elif opcode == 0x1F:
            raise ExpressionInconnue('Saut par la pile')
        elif opcode != 0x20:
            destinations = (suivant,)
        for cible in dict.fromkeys(destinations):
            if cible == fin:
                continue
            exiger(cible in instructions, f'Cible de branche inattendue à {hex_rom(cible)}')
            predecesseurs[cible].append(pc)
            successeurs[pc].append(cible)
    accessibles = set()
    a_visiter = [0]
    while a_visiter:
        pc = a_visiter.pop()
        if pc not in accessibles:
            accessibles.add(pc)
            a_visiter.extend(successeurs[pc])
    return predecesseurs, accessibles


class Analyse:
    def __init__(self, rom, script, prototypes):
        code = script.sections[b'CODE']
        self.base = code.debut + 4
        brut = list(lire_code(rom, code))
        suivis = [position for position, _, _ in brut[1:]] + [code.fin]
        self.instructions = {position - self.base: (opcode, operande, suivant - self.base)
                             for (position, opcode, operande), suivant in zip(brut, suivis, strict=True)}
        self.predecesseurs, self.accessibles = graphe(rom, script, self.instructions)
        self.prototypes = prototypes

    def arguments(self, pc, nombre):
        expr = []
        for _ in range(nombre):
            expression, pc = self.expression(pc)
            expr.append(expression)
        return tuple(reversed(expr)), pc

    def expression(self, pc):
        precedents = self.predecesseurs[pc]
        if len(precedents) != 1 or self.instructions[precedents[0]][2] != pc:
            raise ExpressionInconnue(f'Plusieurs chemins possibles avant {hex_rom(pc)}')
        pc = precedents[0]
        opcode, operande, _ = self.instructions[pc]
        if opcode in EMPILEMENT_IMMEDIAT:
            return ('litteral', operande), pc
        if opcode == 0x13:
            return ('locale', operande, pc), pc
        if opcode in BINAIRE:
            args, debut = self.arguments(pc, 2)
            return ('binaire', BINAIRE[opcode], *args), debut
        if opcode in UNAIRE:
            arg, debut = self.expression(pc)
            return ('unaire', UNAIRE[opcode], arg), debut
        if opcode == 0x21 and operande in self.prototypes:
            nom, nombre = self.prototypes[operande]
            args, debut = self.arguments(pc, nombre)
            return ('natif', operande, nom, *args), debut
        raise ExpressionInconnue(f'Opcode 0x{opcode:02X} non suivi avant {hex_rom(pc)}')

    def origines_locales(self, indice, lecture):
        """Remonte chaque chemin jusqu’à la dernière affectation connue de cette locale."""
        a_visiter = [lecture]
        visites = set()
        origines = {}
        initiale = incomplet = False
        while a_visiter:
            apres = a_visiter.pop()
            if apres in visites or apres not in self.accessibles:
                continue
            visites.add(apres)
            if apres == 0:
                initiale = True
            for pc in self.predecesseurs[apres]:
                if pc not in self.accessibles:
                    continue
                opcode, operande, _ = self.instructions[pc]
                if not (1 <= opcode <= 6 or opcode == 0x14):
                    a_visiter.append(pc)
                    continue
                try:
                    valeur, debut_valeur = self.expression(pc)
                    if opcode == 0x14:
                        cible = ('litteral', operande)
                    else:
                        cible, _ = self.expression(debut_valeur)
                    if cible[0] != 'litteral':
                        raise ExpressionInconnue('Indice local calculé')
                    if cible[1] != indice:
                        a_visiter.append(pc)
                        continue
                    # Une affectation composée dépend aussi de la valeur précédente.
                    origines[pc] = valeur if opcode in (0x01, 0x14) else None
                    if origines[pc] is None:
                        incomplet = True
                except ExpressionInconnue:
                    incomplet = True
        return sorted(origines.items()), initiale, incomplet or not visites


def afficher(expr, variables):
    nature, *args = expr
    if nature == 'litteral':
        return str(args[0])
    if nature == 'locale':
        return f'locale[{args[0]}]'
    if nature == 'unaire':
        return f'{args[0]}({afficher(args[1], variables)})'
    if nature == 'binaire':
        return f'({afficher(args[1], variables)} {args[0]} {afficher(args[2], variables)})'
    natif, nom, *parametres = args
    if natif == 0x03D and parametres[0][0] == 'litteral':
        variable = parametres[0][1]
        return f'VarGet({variables.get(variable, variable)})'
    return f'{nom}({", ".join(afficher(p, variables) for p in parametres)})'


def encoder(expr):
    return json.dumps(expr, separators=(',', ':'), ensure_ascii=False) if expr is not None else ''


def lire_ecritures(rom, edition, prototypes, variables):
    scripts, _ = indexer(rom, edition)
    for script in scripts:
        code = script.sections[b'CODE']
        positions = [position for position, opcode, operande in lire_code(rom, code)
                     if opcode == 0x21 and operande == VAR_SET]
        if not positions:
            continue
        analyse = Analyse(rom, script, prototypes)
        for position in positions:
            pc = position - analyse.base
            try:
                (cible, valeur), debut = analyse.arguments(pc, 2)
            except ExpressionInconnue as erreur:
                raise ValueError(f'Script {script.identifiant:04d} à {hex_rom(position)} ({erreur})') from erreur
            exiger(cible[0] == 'litteral' and cible[1] in variables,
                   f'ID de variable indéterminé à {hex_rom(position)}')
            origines, initiale, incomplet = [], False, False
            if valeur[0] == 'locale':
                _, indice, lecture = valeur
                origines, initiale, incomplet = analyse.origines_locales(indice, lecture)
            yield script.identifiant, pc, analyse.base, debut, cible[1], valeur, origines, initiale, incomplet


def exporter(usa, europe, dossier):
    variables = {int(r['id_variable']): r['symbole'] for r in lire_csv('Variables-natives-FoMT.csv')}
    prototypes = {int(r['id_natif'], 16): (r['symbole_natif'],
                  0 if r['parametres_mary'] == 'void' else len(r['parametres_mary'].split(',')))
                  for r in lire_csv('Liaisons-natives-FoMT.csv') if r['retour_mary'] not in ('', 'void')}
    ancien = {(r['script'], r['pc_code']): r for r in lire_csv('Acces-variables-FoMT.csv')
              if r['operation'] == 'VarSet'}
    ecritures, provenances = [], []
    editions = (lire_ecritures(usa, 'A4NE', prototypes, variables),
                lire_ecritures(europe, 'A4NP', prototypes, variables))
    for us, eu in zip(*editions, strict=True):
        script, pc, base_us, debut, variable, valeur, origines, initiale, incomplet = us
        exiger(us[:2] + us[3:] == eu[:2] + eu[3:], f'Décomposition divergente dans {script:04d}')
        base_eu = eu[2]
        cle = f'{script:04d}', hex_rom(pc)
        site_us, site_eu = hex_rom(base_us + pc), hex_rom(base_eu + pc)
        observe = ancien.pop(cle)
        exiger((site_us, site_eu) == (observe['site_a4ne_rom'], observe['site_a4np_rom']),
               'Le site diffère du relevé natif')
        if observe['id_variable_litteral']:
            exiger(str(variable) == observe['id_variable_litteral']
                   and valeur == ('litteral', int(observe['valeur_litterale'])),
                   'Les arguments diffèrent du relevé littéral')
        ecritures.append((*cle, site_us, site_eu, hex_rom(base_us + debut), hex_rom(base_eu + debut),
                          variable, variables[variable], valeur[0], afficher(valeur, variables), encoder(valeur),
                          len(origines), int(initiale), int(incomplet)))
        for affectation, origine in origines:
            provenances.append((*cle, valeur[1], hex_rom(affectation), hex_rom(base_us + affectation),
                                hex_rom(base_eu + affectation), afficher(origine, variables) if origine else '',
                                encoder(origine)))
    exiger(not ancien, 'Écritures du relevé natif absentes du résultat')
    ecrire_csv(dossier / 'Ecritures-decomposees-FoMT.csv',
               ('script', 'pc_code', 'site_a4ne_rom', 'site_a4np_rom', 'debut_arguments_a4ne_rom',
                'debut_arguments_a4np_rom', 'id_variable', 'symbole_variable', 'forme', 'expression',
                'expression_json', 'origines_locales', 'origine_locale_initiale_possible',
                'origine_locale_incomplete'), ecritures)
    ecrire_csv(dossier / 'Origines-locales-VarSet-FoMT.csv',
               ('script', 'pc_varset', 'index_local', 'pc_affectation', 'affectation_a4ne_rom',
                'affectation_a4np_rom', 'expression', 'expression_json'), provenances)
    return len(ecritures), len(provenances)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('a4ne', type=Path)
    parser.add_argument('a4np', type=Path)
    parser.add_argument('destination', type=Path, help='Nouveau dossier pour les deux CSV')
    args = parser.parse_args()
    try:
        usa, version_us = charger_rom(args.a4ne)
        europe, version_eu = charger_rom(args.a4np)
        exiger((version_us, version_eu) == ('A4NE', 'A4NP'), 'Indiquer la ROM USA puis la ROM Europe')
        exiger(not args.destination.exists(), f'Le dossier {args.destination} existe déjà')
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.varset-', dir=args.destination.parent) as temporaire:
            lot = Path(temporaire) / 'varset'
            lot.mkdir()
            ecritures, origines = exporter(usa, europe, lot)
            lot.rename(args.destination)
    except (KeyError, OSError, ValueError) as erreur:
        parser.exit(1, f'{erreur}\n')
    print(f'FoMT USA et Europe · {ecritures} écritures décomposées et {origines} origines locales.')


if __name__ == '__main__':
    main()
