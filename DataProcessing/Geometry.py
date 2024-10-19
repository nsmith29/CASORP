#!/usr/bin/env python3

import asyncio
import json
import numpy as np

from Core.CentralDefinitions import Geo_Settings, End_Error, ProcessCntrls, Ctl_Settings, Dirs, sharable_vars, create_nested_dict
from Core.Iterables import Lines_iterator
from Core.Messages import ErrMessages
from DataCollection.FileSearch import  MethodFiles
from DataCollection.FromFile import read_file_async
from DataProcessing.ProcessCntral import Files4DefiningDefect


__all__ = {'CntrlGeometry', 'GeometryProcessing', 'DefProcessing'}


async def CntrlGeometry(sender=None):
    if sender != None:
        print('sender received', sender, '[DC.G L20]')
    coroutines = [GeometryProcessing.setoffassessment(), DefProcessing(sender)]
    Tasks = await asyncio.gather(*coroutines)

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
        if len(flpath) > 1:
            [flpath.remove(entry) for entry in flpath if str(entry).split('/')[-1] == str(Geo_Settings().perf_lxyz).split('/')[-1]]
            End_Error(len(flpath) > 1, ErrMessages.FileSearch_LookupError(extension,
                                        Dirs().address_book[kl[0]][kl[1]][kl[2]][kl[3]]["path"],"geometry"))
            keylist = kl
            keylist.append(extension)
            Geo_Settings.struc_data = create_nested_dict(keylist, ['nns', 'bonds', 'lat paras'], [['None'],['None'],['None']], Geo_Settings().struc_data)
        replace_rtn = await super().option2(kl, extension, flpath, Q)
        return replace_rtn

async def DefProcessing(sender):
    if 'charges and spins' in ProcessCntrls().processwants:
        if sender:
            print("working, sender here. Completing assessment now")
        await Files4DefiningDefect.setoffassessment('geometry', 'defect defining', ignore=True)
        # save collected Ctl_settings properties to shared memory dictionary for transfer between processes

        for name in ['defining_except_found', 'e2_defining', 'i_defining']:
            name, var = str('Ctl_Settings' + name), eval('Ctl_Settings().{}'.format(name))
            sharable_vars(name, var)
    else:
        await Files4DefiningDefect.setoffassessment('geometry', 'defect defining')

async def retrieval(filepath):
    x_data, y_data, z_data = np.loadtxt(filepath, skiprows=2, usecols=(1,2,3), unpack=True)
    atom_data = []
    lines = await read_file_async(filepath)
    # as Lines_iterator goes through file from bottom to top, reverse lines so resultant list matches x-, y-, z-data.
    lines = lines[::-1]
    async for item_ in Lines_iterator(lines):
        indx, ln = item_[0], item_[1]
        if indx >= 2:
            atom_data.append(" ".join([str(var[1]) for var in enumerate(ln.split()) if var[0] in [0]]))
    return  atom_data, x_data, y_data, z_data

