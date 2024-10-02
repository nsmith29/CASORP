#!/usr/bin/env python3

import numpy as np
import sys
import time

from Core.DictsAndLists import log_var_fo, log_want
from Core.CentralDefinitions import SharableDicts, SaveProperties
from DataCollection.FromFile import Iterate, Update

__all__ = {'a', 'at_crd', 'knd_atms', 'charge', 'energy', 'gap', 'version', 'run', 'name', 'Pop', 'pop1', 'pop2',
           'Fork1', 'Fork2'}

class Fork1(Update):

    def __init__(self2, varitem):
        super().__init__(varitem)

    @Iterate
    def searchingA(self2, varitem, ln, lines):
        """
            Searching for instances of the "locate" string.
        """

        if varitem["locate"] in ln and varitem["found"] is False:
            index = lines.index(ln) - len(lines) + 1 if varitem["reverse"] is False else lines.index(ln)
            super().found()
            key = str(varitem["via"])
            eval(str("self2.{}(ln, index, lines)".format(key)))
            sys.exit()
        return varitem
    # combination of FromInp.reset_dict and FromLog.rest_dict


class Fork2(Update):

    def __init__(self2, varitem):
        super().__init__(varitem)

    @Iterate
    def searchingB(self2, varitem, ln):
        """
            Searching for instances of the "locate" string.
        """

        if varitem["locate"] in ln and varitem["found"] is False:
            super().found()
            key = str(varitem["via"])
            eval(str("self2.{}(ln)".format(key)))
        return varitem


class a(SaveProperties, Fork1):
    """
        Get lattice parameters from log file.
    """

    def __init__(a, v2rtn, indx, os_path, varitem):
        a.v2rtn, a.indx = v2rtn, indx
        SaveProperties.__init__(a)
        a.os_path, a.varitem = os_path, varitem
        Fork1.__init__(a, a.varitem)
        Fork1.searchingA(a, a.os_path, a.varitem, 'self.index', 'self.lines')

        Update.reset(a)

    def find_a(a, line, index, lines):
        """
            Extracting lattice parameters of calculation cell.
        """

        strg1 = line
        strg2 = lines[index]
        strg3 = lines[index + 1]
        collect1 = []
        for s, item, letter in zip([1, 2, 3], ['a', 'b', 'c'], ['A', 'B', 'C']):
            # extract txt of indices 4,5,6,9 in line split list. {letter} is lat cnst, {item}Latt is {item} line of lat vec.
            exec(f'*{letter}, {item}Latt= [float(var[1]) for var in enumerate(strg{s}.split()) if var[0] in [4,5,6,9]]')
            exec(f'collect1.extend([{letter}, {item}Latt])')

        # place extracted values in corresponding position of proxy list.
        a.v2rtn[a.indx] = collect1

        # return self2.v2rtn


class at_crd(SaveProperties, Update):
    """
        Get atomic coordinates and identities from log file.
    """

    def __init__(at, v2rtn, indx, os_path, varitem):

        at.v2rtn, at.indx = v2rtn, indx
        SaveProperties.__init__(at)
        at.os_path, at.varitem = os_path, varitem
        Update.__init__(at, at.varitem)
        at.searching(at, at.os_path, at.varitem, 'self.index', 'self.lines')

        Update.reset(at)

    @Iterate
    def searching(at, varitem, ln, lines):
        """
            Searching for instances of the "locate" string for lattice constants.
        """


        if varitem["locate"].upper().split() == ln.upper().split() and varitem.get("found") is False:
            index = lines.index(ln)
            Update.found(at)
            key = str(varitem["via"])
            eval(str("at.{}(index, lines)".format(key)))
            sys.exit()
        return varitem

    def find_at(at, index, lines):
        """
            Extracting details of atomic coordinates and identities.
        """

        # make empty lists
        X, Y, Z, ELEMENT, MASS = [], [], [], [], []
        # find max number of atoms in calc for information to collected for.
        max = [int(var[1]) for var in enumerate(lines[index - 20].split()) if var[0] in [2]][0]
        # Some log files have an extra blank space between line where "locate" string is found & start of atom info.
        try:
            mass = [var[1] for var in enumerate(lines[index + 3].split()) if var[0] in [8]]
            n = 3
        except ValueError:
            mass = [var[1] for var in enumerate(lines[index + 4].split()) if var[0] in [8]]
            n = 4
        finally:
            for p in range(0, max):
                # extract index 2,4-6,8 in line split list. element - atom element, x/y/z - x/y/z-coord, mass - atomic mass.
                element, x, y, z, mass = [var[1] for var in enumerate(lines[index + n + p].split()) if  var[0] in [2, 4, 5, 6, 8]]
                for f, F in zip([float(x), float(y), float(z), element, mass], [X, Y, Z, ELEMENT, MASS]):
                    F.append(f)
        array = np.array([X, Y, Z])
        # place extracted values in corresponding position of proxy list.
        at.v2rtn[at.indx] = [array]


class charge(SaveProperties, Fork2):

    def __init__(charge, v2rtn, indx, os_path, varitem):
        charge.v2rtn, charge.indx = v2rtn, indx
        SaveProperties.__init__(charge)
        charge.os_path, charge.varitem = os_path, varitem
        Update.__init__(charge, charge.varitem)
        Fork2.searchingB(charge, charge.os_path, charge.varitem)

        Update.reset(charge)

    def find_charge(charge, line):
        """
            Extracting charge state of calculation
        """

        # extracted txt of index 2 in line split list, C is the charge state of calc.
        C = [int(var[1]) for var in enumerate(line.split()) if var[0] in [2]][0]

        # alter C so reported charge state is given with sign of charge state after number of charge ie -1 -> 1-
        if C < 0:
            # negative charge states.
            C = "".join(["".join([i for i in list(str(C)) if i != '-']), '-'])
        elif C == 0:
            pass
        else:
            # positive charge states.
            C = "".join([str(C), "+"])

        # place extracted value in corresponding position of proxy list.
        charge.v2rtn[charge.indx] = [C]


class energy(SaveProperties, Fork2):

    def __init__(energy, v2rtn, indx, os_path, varitem):
        energy.v2rtn, energy.indx = v2rtn, indx
        SaveProperties.__init__(energy)
        energy.os_path, energy.varitem = os_path, varitem
        Update.__init__(energy, energy.varitem)
        Fork2.searchingB(energy, energy.os_path, energy.varitem)

        Update.reset(energy)

    def find_energy(energy, line):
        """
            Extracting total energy of calculation.
        """

        # extract of txt of index 8 in line split list. E is tot energy of calc converted from hartree units to eV.
        E = [(round(float(var[1]), 10) * 27.211) for var in enumerate(line.split()) if var[0] in [8]][0]

        # place extracted value in corresponding position of proxy list.
        energy.v2rtn[energy.indx] = [E]


class gap(SaveProperties, Fork1):
    """

    """

    def __init__(gap, v2rtn, indx, os_path, varitem):

        gap.v2rtn, gap.indx = v2rtn, indx
        SaveProperties.__init__(gap)
        gap.os_path, gap.varitem = os_path, varitem
        Fork1.__init__(gap, gap.varitem)
        Fork1.searchingA(gap, gap.os_path, gap.varitem, 'self.index', 'self.lines')


        Update.reset(gap)

    def find_gap(gap, line, index, lines):
        """
            Extraction of details about band gap of calculation.
        """

        # beta gap
        strg2 = line
        # alpha gap
        strg1 = lines[index - 2]
        collect2 = []
        for spin, s in zip(["alpha", "beta"], [1, 2]):
            # extract txt of index 6 in line split list. {spin}_HOMO_LUMOgap is {spin} band gap in eV.
            exec(f'{spin}_HOMO_LUMOgap = [float(var[1]) for var in enumerate(strg{s}.split()) if var[0] in[6]][0]')
            exec(f'collect2.append({spin}_HOMO_LUMOgap)')

        # place extracted values in corresponding position of proxy list.
        gap.v2rtn[gap.indx] = collect2


class knd_atms(SaveProperties, Update):
    """
        Get atomic kind information from log file.
    """

    def __init__(knd, v2rtn, indx, os_path, varitem):
        knd.all_kinds, knd.v2rtn, knd.indx = [], v2rtn, indx
        SaveProperties.__init__(knd)
        knd.os_path, knd.varitem = os_path, varitem
        Update.__init__(knd, knd.varitem)
        knd.searching(knd, knd.os_path, knd.varitem)

        Update.reset(knd)

    @Iterate
    def searching(knd, varitem, ln):
        """
            Searching for instances of the "locate" string for atomic kinds.
        """
        if varitem["locate"] in ln and varitem.get("found") is False:
            if not varitem["num"]:
                knd.kind_first_found(ln)
            elif varitem["num"]:
                knd.all_kinds.append(ln)
                Update.extra(knd, ["cnt", int(varitem["cnt"] + 1)])

                if int(varitem["cnt"]) == int(varitem["num"]):
                    Update.found(knd)
                    key = str(varitem["via"])
                    eval(str("knd.{}(knd.all_kinds)".format(key)))
        return varitem

    def find_kind(knd, lines):
        """
            Extracting details about each atomic kind in calculation.
        """

        collect3 = []
        for line in lines:
            # extract indices 3,7 in line split list. kind_ele - name of kind, num_atoms - # of atoms of kind in calc.
            kind_ele, num_atoms = [var[1] for var in enumerate(line.split()) if var[0] in [3, 7]]
            collect3.extend([kind_ele, num_atoms])

        knd.v2rtn[knd.indx] = collect3

    def kind_first_found(knd, ln):
        """
            Obtaining total number of atomic kinds in calculation system.
        """

        # extract txt of index 6 in line split list. number is number of different element kinds in calc.
        number = [int(var[1]) for var in enumerate(ln.split()) if var[0] in [6]][0]

        Update.extra(knd, ["num", number, "cnt", 0])


class name(SaveProperties, Fork2):

    def __init__(name, v2rtn, indx, os_path, varitem):
        name.v2rtn, name.indx = v2rtn, indx
        SaveProperties.__init__(name)
        name.os_path, name.varitem = os_path, varitem
        Update.__init__(name, name.varitem)
        Fork2.searchingB(name, name.os_path, name.varitem)

        Update.reset(name)

    def find_name(name, line):
        """
            Extracting project name of calculation.
        """

        # extract txt of index 3 in line split list. N is the project name of calculation.
        N = [str(var[1]) for var in enumerate(line.split()) if var[0] in [3]][0]

        # place extracted value in corresponding position of proxy list.
        name.v2rtn[name.indx] = [N]


class Pop(Update):
    def __init__(pop, varitem):
        super().__init__(varitem)

    @Iterate
    def searching_pop(pop, varitem, ln, lines):
        if varitem["locate"][0] in ln and not varitem["num"] and varitem["found"] is False:
            index = max(i for i, it in enumerate(lines) if it == ln) - len(lines) + 1
            pop.pop_first_found(index, lines)
        elif varitem["locate"][1] in ln and varitem["found"] is False:
            index = max(i for i, it in enumerate(lines) if it == ln) - len(lines) + 1
            super().found()
            atoms, key = int(varitem["num"]), str(varitem["via"])
            eval(str("pop.{}(atoms, index, lines)".format(key)))
            sys.exit()
        return varitem

    def pop_first_found(pop, index, lines):
        """
            Obtaining total number of atoms in calculation system.
        """
        #
        # # extra blank line in file between lines containing "locate"[0] and last atom for "pop2"
        # n = 2 if pop == "pop1" else 3
        # extract txt of index 0 in line split list. number is atom # of last atom listed in analysis = calc tot atoms.
        number = [var[1] for var in enumerate(lines[index - pop.varit["n"]].split())
                  if var[0] in [0]][0]
        # save total number of atoms in dict for later reference.
        super().extra(["num", number])


class pop1(SaveProperties, Pop):
    def __init__(pop1, v2rtn, indx, os_path, varitem):

        pop1.v2rtn, pop1.indx = v2rtn, indx
        SaveProperties.__init__(pop1)
        pop1.os_path, pop1.varitem = os_path, varitem
        Pop.__init__(pop1, pop1.varitem)
        Pop.searching_pop(pop1, pop1.os_path, pop1.varitem, 'self.index', 'self.lines')

        Update.reset(pop1)
        #

    def find_pop1(pop1, atoms, index, lines):
        """
            Extraction of details related to Mulliken Population Analysis of all or only certain atoms within calculation.
        """

        collect = []
        rnge = atoms if type(atoms) == list else range(0, atoms)
        # A of specific atom indices or from 0 to total number of atoms in system.
        for A in rnge:
            # extract indices 3-6 in line split list. p1_a & p1_b - alpha & beta pops, p1_s & p1_c - Mulliken spin & charge.
            p1_a, p1_b, p1_c, p1_s = [round(float(var[1]), 3) for var in enumerate(lines[int(index + 2 + A)].split())
                                      if var[0] in [3, 4, 5, 6]]
            collect.append([p1_a, p1_b, p1_c, p1_s])

        # place extracted values in corresponding position of proxy list.
        pop1.v2rtn[pop1.indx] = collect


class pop2(SaveProperties, Pop):
    def __init__(pop2, v2rtn, indx, os_path, varitem):
        pop2.v2rtn, pop2.indx = v2rtn, indx
        SaveProperties.__init__(pop2)
        pop2.os_path, pop2.varitem = os_path, varitem
        Pop.__init__(pop2, pop2.varitem)
        Pop.searching_pop(pop2, pop2.os_path, pop2.varitem, 'self.index', 'self.lines')

        Update.reset(pop2)

    def find_pop2(pop2, atoms, index, lines):
        """
            Extraction of details related to Hirshfeld Population Analysis of all or only certain atoms within calculation.
        """
        # smd = SharedMemoryDict("CASORP", size=1024)
        addressbook, calckeys = SharableDicts().smd[str('Dirs.address_book')], SharableDicts().smd[str('Dirs.dir_calc_keys')]
        # print(pop2.os_path, addressbook['perfect'], [p for p in ( addressbook['perfect'][n][r][c]['log'] for n,r,c in ([n,r,c] for n,r,c in calckeys['perfect'] ) ) ], 'DC.L L391' )
        for p in (p for p in [addressbook['perfect'][n][r][c]['log'] for n, r, c in ([n, r, c] for n, r, c in calckeys['perfect']) ] if p == pop2.os_path):
            # print(p, 'DC.L L393')
            SharableDicts().smd['total atoms'] = atoms

        collect = []
        rnge = atoms if type(atoms) == list else range(0, atoms)
        # A of specific atom indices or from 0 to total number of atoms in system.
        for A in rnge:
            # extract indices 4-7 in line split list. p2_a & p2_b - alpha & beta pops, p2_s & p2_c - Hirshfeld spin & charge.
            p2_a, p2_b, p2_s, p2_c = [round(float(var[1]), 3) for var in enumerate(lines[int(index + 2 + A)].split())
                                      if var[0] in [4, 5, 6, 7]]
            collect.append([p2_a, p2_b, p2_c, p2_s])

        # place extracted values in corresponding position of proxy list.
        pop2.v2rtn[pop2.indx] = collect


class run(SaveProperties, Fork2):

    def __init__(run, v2rtn, indx, os_path, varitem):
        run.v2rtn, run.indx = v2rtn, indx
        SaveProperties.__init__(run)
        run.os_path, run.varitem = os_path, varitem
        Update.__init__(run, run.varitem)
        Fork2.searchingB(run, run.os_path, run.varitem)

        Update.reset(run)

    def find_run(run, line):
        """
            Extracting run type of calculation.
        """

        # extract txt of index 3 in line split list. R is the calculation run type.
        R = [str(var[1]) for var in enumerate(line.split()) if var[0] in [3]][0]

        # place extracted value in corresponding position of proxy list.
        run.v2rtn[run.indx] = [R]


class version(SaveProperties, Fork2):

    def __init__(ver, v2rtn, indx, os_path, varitem):
        ver.v2rtn, ver.indx = v2rtn, indx
        SaveProperties.__init__(ver)
        ver.os_path, ver.varitem = os_path, varitem
        Update.__init__(ver, ver.varitem)
        Fork2.searchingB(ver, ver.os_path, ver.varitem)

        Update.reset(ver)

    def find_version(ver, line):
        """
            Extracting CP2K version calculation was run with.
        """

        # extract txt of index 5 in line split list. V is CP2K version calculation performed with.
        V = [float(var[1]) for var in enumerate(line.split()) if var[0] in [5]][0]

        # place extracted value in corresponding position of proxy list.
        ver.v2rtn[ver.indx] = [V]