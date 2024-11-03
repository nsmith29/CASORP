#!/usr/bin/env python3

import asyncio
from asgiref.sync import sync_to_async
import json
import numpy as np

from Core.CentralDefinitions import Geo_Settings, End_Error, ProcessCntrls, Ctl_Settings, Dirs, sharable_vars, \
    create_nested_dict, percalcdir, add2addressbook, proxy4keys, DictProperty
from Core.DictsAndLists import boolconvtr
from Core.Iterables import Lines_iterator
from Core.Messages import ErrMessages, SlowMessageLines, ask_question
from DataCollection.FileSearch import  MethodFiles, Entry4FromFiles
from DataCollection.FromFile import read_file_async
from DataProcessing.ProcessCntral import Files4DefiningDefect
from DataAnalysis.GeometryAnalysis import create_structure, DefineDefType


__all__ = {'CntrlGeometry', 'ThreadOne', 'ThreadTwo','GeometryProcessing', 'getbondsandneighbours',  'DefProcessing', 'retrieval',
           'AppendDefSitesNum'}


async def CntrlGeometry():
    coroutines = [ThreadOne(), ThreadTwo()]
    Tasks = await asyncio.gather(*coroutines)

async def ThreadOne():
    await GeometryProcessing.setoffassessment()

class GeometryProcessing(MethodFiles):
    def __init__(self2):
        super().__init__('geometry','standard')
    @classmethod
    async def setoffassessment(cls):
        self2 = cls()
        for type_, flexts in zip(self2.types, self2.flexts_):
            self2.type_, self2.flexts = type_, flexts
            await super().assessment_tree(self2, self2.type_, self2.flexts, self2.sect)
    async def option2(self2, kl, extension, flpath, Q):
        if kl[0] == 'perfect':
            Geo_Settings.perf_lxyz = flpath
        if type(flpath) == list and len(flpath) > 1:
            [flpath.remove(entry) for entry in flpath if str(entry).split('/')[-1] == str(Geo_Settings().perf_lxyz).split('/')[-1]]
            End_Error(len(flpath) == 1, ErrMessages.FileSearch_LookupError(extension,
                                        Dirs().address_book[kl[0]][kl[1]][kl[2]][kl[3]]["path"],"geometry"))
        keylist = kl
        Geo_Settings.struc_data, _ = create_nested_dict(keylist, [extension, 'lat paras', 'defect type', 'defect indx'],
                                                    [{'nns': [], 'bonds':[]}, [], '', []], Geo_Settings().struc_data)
        replace_rtn = await super().option2(kl, extension, flpath, Q)
        return replace_rtn

async def ThreadTwo():
    for item in Ctl_Settings().e2_defining['defect']:
        item.pop(-1)
    if 'charges and spins' in ProcessCntrls().processwants:
        await Files4DefiningDefect.setoffassessment('geometry', 'defect defining', ignore=True)
        # save collected Ctl_settings properties to shared memory dictionary for transfer between processes.
        for name in ['defining_except_found', 'e2_defining', 'i_defining']:
            name, var = str('Ctl_Settings.' + name), eval('Ctl_Settings().{}'.format(name))
            sharable_vars(name, var)
        await percalcdir(DefProcessing)('defect', ignore=True)

        if  Geo_Settings.checkdefatnum is True:
            print(str(Geo_Settings().question_def_sites))
    else:
        await Files4DefiningDefect.setoffassessment('geometry', 'defect defining')
        await percalcdir(DefProcessing)('defect')
        if  Geo_Settings.checkdefatnum is True:
            print(str(Geo_Settings().question_def_sites))

async def getbondsandneighbours(t_, n, r, c, atoms, x, y, z):
    if Geo_Settings().struc_data[t_][n][r][c]['lat paras'] == []:
        # get lattice parameters and save parameters to struc_data dict : Entry4FromFiles(path, file, keywrd)
        item = await Entry4FromFiles(Dirs.address_book[t_][n][r][c]['log'], 'log', 'geometry')
        a_, b_, c_ = item[0][0], item[0][1], item[0][2]
        Geo_Settings.struc_data = add2addressbook([t_, n, r, c], ['lat paras'], [[a_, b_, c_]], Geo_Settings().struc_data)
    lat_vecs = Geo_Settings().struc_data[t_][n][r][c]['lat paras']
    # get structure from create_structure and dictionaries of nns and bonds -> save to struc_data dict.
    structure = await create_structure(atoms, x, y, z, lat_vecs[0][0], lat_vecs[1][0], lat_vecs[2][0], c)
    nns, bonds = structure.get_all_neighbors(sites=structure, r=3, include_index=True)
    Geo_Settings.struc_data = add2addressbook([t_, n, r, c], ["''.xyz"], [{'nns': nns, 'bonds': bonds}],
                                              Geo_Settings().struc_data)

async def DefProcessing(t_, n, r, c, **kws):
    if "ignore" in kws.keys() and [n, r, c] not in Ctl_Settings.e2_defining[t_] or "ignore" not in kws.keys() and r!="ENERGY":
        # retrieve x, y, z and atoms data from xyz file.
        defxyz = Dirs().address_book[t_][n][r][c]["''.xyz"] if [n, r, c] not in \
                        Ctl_Settings.i_defining[t_] else Dirs().address_book[t_][n][r][c]["''.xyz*"]
        atoms, x, y, z = await retrieval(defxyz)
        await getbondsandneighbours(t_, n, r, c, atoms, x, y, z)
        pt, pn, pr, pc = await proxy4keys('perfect', retrn=True)
        # pass to defect definer -> save indices of defect atom(s)
        deftype, tnumdef, defatnum, defidxs, defdict = await DefineDefType(["''.xyz", t_, n, r, c],
                                                                Dirs().address_book['perfect'][pn][pr][pc]["-L.xyz"],
                                                                defxyz).type_definition()
        if defatnum / tnumdef >= 0.05:
            Geo_Settings.checkdefatnum = True if Geo_Settings().checkdefatnum == None else Geo_Settings().checkdefatnum
            Geo_Settings.question_def_sites = AppendDefSitesNum('Geo_Settings', 'question_def_sites')([n, r, c], tnumdef,
                                                                                                    defatnum, deftype,
                                                                                                    defidxs, defdict)
        else:
            Geo_Settings.struc_data = add2addressbook([t_, n, r, c], ['defect type', 'defect indx'],
                                                  [deftype, [defidxs, defdict]], Geo_Settings().struc_data)
    # print(t_, n, r, c, deftype, defidx, defdict, '[DP.G L96]')

async def retrieval(filepath):
    x_data, y_data, z_data = np.loadtxt(filepath, skiprows=2, usecols=(1,2,3), unpack=True)
    atom_data = []
    lines = await read_file_async(filepath)
    lines = lines.split('\n')
    lines = lines[::-1]
    async for item_ in Lines_iterator(lines):
        indx, ln = item_[0], item_[1]
        if indx <= -3 and ln != '':
            atom_data.append(" ".join([str(var[1]) for var in enumerate(ln.split()) if var[0] in [0]]))
    assert atom_data[-1] != '', "blank line at end of xyz file has been incorrectly recorded in list of atoms"
    assert len(atom_data) == len(
        x_data), f"length of list of atoms [{len(atom_data)}]must equal length of list of coordinates [{len(x_data)}]"
    return atom_data, x_data, y_data, z_data

class AppendDefSitesNum(DictProperty):
    """
            1. bool test if num of def atoms found is over 5% of the total number of atoms in the structure
            2. if True -> record  deftype, tnumdef, defatnum, defidx, defdict, and keys in a new list or dict separate to
               Geo_Settings().struc_data
            3. grouping of dirs with - same name & runtype (passive check that total number of atoms & def atoms found match)
                                     - same runtype & total number of atoms & def atoms
            4. for each grouping - provide user with info on number of defect site found in structure
                                 - ask if this is the expected number of defect sites in the structure
            5. Wait until all groups have an answer, inform user that defect type[geometry only]/charges&spins for atoms
               only related to defect[charges&spins wanted] cannot be performed for dirs where user indicates that an
               unexpected amount of defect sites have been found - State that the reason for this may be related to the
               initial xyz file of particular calculation
    """
    def __init__(self, klass, method):
        super().__init__(klass, method)
        # dict4kwargs = eval("{}().{}".format(klass, method))
        # super().__init__(dict4kwargs)
    def __missing__(self, key):
        # print(f'{key} being made.')
        self[key] = []
        return self[key]
    def __call__(self, key: list, tnumdef: int, defatnum: int, deftype: str, defidx: list, defdict: dict, ):
        group, placed = 1, False
        while placed is False:
            grouplst = self[str('group{}'.format(group))]
            if grouplst == []:
                self[str('group{}'.format(group))] = [[key, tnumdef, defatnum, deftype, defidx, defdict]]
                placed = True
                break
            for idx, j in enumerate([i[0] for i in [i for i in grouplst]]):
                if key[1] in j and tnumdef == grouplst[idx][1] and defatnum == grouplst[idx][2]:
                    self[str('group{}'.format(group))].append([key, tnumdef, defatnum, deftype, defidx, defdict])
                    placed = True
                    break
            else:
                group += 1
        return self
    def __str__(self):
        SlowMessageLines(
            str("\n{bcolors.FAIL}WARNING: {bcolors.UNDERLINE}A potentially unexpected number of defect sites have been found."))
        answers = []
        for value in self.values():
            str_ = str(
                "{bcolors.CHOSEN}{bcolors.BOLD}    " + f"{value[0][2]}" + "{bcolors.ENDC}{bcolors.KEYINFO}/" +
                f"{value[0][1]} defect sites in total have been found for:" + "{bcolors.ENDC}")
            for i in value:
                str_ = str_ + str("\n{bcolors.KEYVAR}        - " + f"{i[0][0]}, {i[0][1]}, {i[0][2]}")
            SlowMessageLines(str_)
            answers.append(boolconvtr[ask_question("GeoQ1", "YorN", ["Y", "N"])])
            if answers[-1] is True:
                for i in value:
                    Geo_Settings.struc_data = add2addressbook(['defect', i[0][0], i[0][1], i[0][2]],
                                                              ['defect type', 'defect indx'], [i[3], [i[4], i[5]]],
                                                              Geo_Settings().struc_data)
        print(answers)
        if False in answers:
            method = "atom displacements for distance from defect site" \
                     if 'charges and spins' not in ProcessCntrls().processwants else "charges&spins for atoms only " \
                                                                                     "related to defect"
            SlowMessageLines(
                str("{bcolors.EXTRA}For the groups of calculations where you have indicated that the number of found "
                    "defect sites is incorrect,{bcolors.METHOD}"
                    + f" {method}"
                    + "{bcolors.EXTRA} will not be able to be performed because the defect type of the calculation "
                      "cannot be reliably determined.\n{bcolors.QUESTION2}This is likely due to the initial xyz file of "
                      "each of these particular calculations being derived from or a copy of the last geometry step "
                      "structure of another defect calculation (likely a different runtype for the same defect project "
                      "and charge state) rather than the defect-free, perfect structure."))
        return " "