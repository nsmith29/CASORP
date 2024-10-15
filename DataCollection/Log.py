#!/usr/bin/env python3

import asyncio
import numpy as np
import sys
import time

from Core.DictsAndLists import log_var_fo, log_want
from Core.CentralDefinitions import Dirs, SharableDicts


__all__ = {'find_a', 'find_at', 'find_charge', 'find_energy', 'find_gap', 'find_kind', 'find_name', 'find_pop1', 'find_pop2',
           'find_run', 'find_version'}


async def find_a(line, index, lines):
    strg1 = line
    strg2 = lines[index]
    strg3 = lines[index - 1]
    collect = []
    for s, item, letter in zip([1, 2, 3], ['a', 'b', 'c'], ['A', 'B', 'C']):
        # extract txt of indices 4,5,6,9 in line split list. {letter} is lat cnst, {item}Latt is {item} line of lat vec.
        exec(f'*{letter}, {item}Latt= [float(var[1]) for var in enumerate(strg{s}.split()) if var[0] in [4,5,6,9]]')
        exec(f'collect.extend([{letter}, {item}Latt])')
    await asyncio.sleep(0.01)
    return collect

async def find_at(ln, lines, index):
    # make empty lists
    X, Y, Z, ELEMENT, MASS = [], [], [], [], []
    # find max number of atoms in calc for information to collected for.
    max = [int(var[1]) for var in enumerate(lines[index + 20].split()) if var[0] in [2]][0]
    # Some log files have an extra blank space between line where "locate" string is found & start of atom info.
    try:
        mass = [var[1] for var in enumerate(lines[index - 3].split()) if var[0] in [8]]
        n = 3
    except ValueError:
        mass = [var[1] for var in enumerate(lines[index - 4].split()) if var[0] in [8]]
        n = 4
    finally:
        for p in range(0, max):
            # extract index 2,4-6,8 in line split list. element - atom element, x/y/z - x/y/z-coord, mass - atomic mass.
            element, x, y, z, mass = [var[1] for var in enumerate(lines[index - n - p].split()) if
                                      var[0] in [2, 4, 5, 6, 8]]
            for f, F in zip([float(x), float(y), float(z), element, mass], [X, Y, Z, ELEMENT, MASS]):
                F.append(f)
    array = np.array([X, Y, Z])
    # place extracted values in corresponding position of proxy list.
    await asyncio.sleep(0.01)
    return array

async def find_charge(line, **kwargs):
    C = [int(var[1]) for var in enumerate(line.split()) if var[0] in [2]][0]
    if C < 0:
        C = "".join(["".join([i for i in list(str(C)) if i != '-']), '-'])
    elif C == 0:
        pass
    else:
        C = "".join([str(C), "+"])
    await asyncio.sleep(0.01)
    return C

async def find_energy(line, **kwargs):
    # extract of txt of index 8 in line split list. E is tot energy of calc converted from hartree units to eV.
    E = [(round(float(var[1]), 10) * 27.211) for var in enumerate(line.split()) if var[0] in [8]][0]
    await asyncio.sleep(0.01)
    return E

async def find_gap(line, index, lines):
    # beta gap
    strg2 = line
    # alpha gap
    strg1 = lines[index - 1]
    collect0 = []
    for spin, s in zip(["alpha", "beta"], [1, 2]):
        # extract txt of index 6 in line split list. {spin}_HOMO_LUMOgap is {spin} band gap in eV.
        exec(f'{spin}_HOMO_LUMOgap = [float(var[1]) for var in enumerate(strg{s}.split()) if var[0] in[6]][0]')
        exec(f'collect0.append({spin}_HOMO_LUMOgap)')
    await asyncio.sleep(0.01)
    return collect0

async def find_kind(lines, **kwargs):
    collect1 = []
    for line in lines:
        # extract indices 3,7 in line split list. kind_ele - name of kind, num_atoms - # of atoms of kind in calc.
        kind_ele, num_atoms = [var[1] for var in enumerate(line.split()) if var[0] in [3, 7]]
        collect1.extend([kind_ele, num_atoms])
    await asyncio.sleep(0.01)
    return collect1

async def find_name(line, **kwargs):
    # extract txt of index 3 in line split list. N is the project name of calculation.
    N = [str(var[1]) for var in enumerate(line.split()) if var[0] in [3]][0]
    # place extracted value in corresponding position of proxy list.
    await asyncio.sleep(0.01)
    return N

async def find_run(line, **kwargs):
    # extract txt of index 3 in line split list. R is the calculation run type.
    R = [str(var[1]) for var in enumerate(line.split()) if var[0] in [3]][0]
    # place extracted value in corresponding position of proxy list.
    await asyncio.sleep(0.01)
    return R

async def find_pop1(atoms, index, lines):
    collect2 = []
    rnge = atoms if len(atoms) > 1 else range(0, int(atoms[0]))
    # A of specific atom indices or from 0 to total number of atoms in system.
    for A in rnge:
        # extract indices 3-6 in line split list. p1_a & p1_b - alpha & beta pops, p1_s & p1_c - Mulliken spin & charge.
        p1_a, p1_b, p1_c, p1_s = [round(float(var[1]), 3) for var in enumerate(lines[int(index + 3 + A)].split())
                                  if var[0] in [3, 4, 5, 6]]
        collect2.append([p1_a, p1_b, p1_c, p1_s])
    await asyncio.sleep(0.01)
    return [collect2]

async def find_pop2(atoms, index, lines, path):
    addbk, ckeys = Dirs().address_book, Dirs().dir_calc_keys
    for p in (p for p in [addbk["perfect"][n][r][c]['log'] for n, r, c in ([n, r, c] for n, r, c in ckeys['perfect'])] if p == path):
        SharableDicts().smd['total atoms'] = atoms
    collect3 = []
    rnge = atoms if len(atoms) > 1 else range(0, int(atoms[0]))
    # A of specific atom indices or from 0 to total number of atoms in system.
    for A in rnge:
        # extract indices 4-7 in line split list. p2_a & p2_b - alpha & beta pops, p2_s & p2_c - Hirshfeld spin & charge.
        p2_a, p2_b, p2_s, p2_c = [round(float(var[1]), 3) for var in enumerate(lines[int(index + 3 + A)].split()) if
                                  var[0] in [4, 5, 6, 7]]
        collect3.append([p2_a, p2_b, p2_c, p2_s])
    await asyncio.sleep(0.01)
    return [collect3]

async def find_version(line, **kwargs):
    # extract txt of index 5 in line split list. V is CP2K version calculation performed with.
    V = [float(var[1]) for var in enumerate(line.split()) if var[0] in [5]][0]
    await asyncio.sleep(0.01)
    return V
