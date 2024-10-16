#!/usr/bin/env python3

import asyncio
import json
from Core.CentralDefinitions import Geo_Settings, End_Error, ProcessCntrls
from Core.Messages import ErrMessages
from DataProcessing.ProcessCntral import Files4DefiningDefect
from DataCollection.FileSearch import  MethodFiles
from Core.CentralDefinitions import Dirs, sharable_vars

__all__ = {'CntrlGeometry', 'GeometryProcessing', 'DefProcessing'}


async def CntrlGeometry():
    coroutines = [GeometryProcessing.setoffassessment(), DefProcessing()]

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
            print(flpath)
            [flpath.remove(entry) for entry in flpath if str(entry).split('/')[-1] == Geo_Settings().perf_lxyz]
            End_Error(len(flpath) > 1, ErrMessages.FileSearch_LookupError(extension,
                                        Dirs().address_book[kl[0]][kl[1]][kl[2]][kl[3]]["path"],"geometry"))
        replace_rtn = await super().option2(kl, extension, flpath, Q)
        return replace_rtn

async def DefProcessing():
    if 'charges and spins' in ProcessCntrls().processwants:
        await Files4DefiningDefect.setoffassessment('geometry', 'defect defining', ignore=True)
        print(json.dumps(Dirs().address_book, indent=1))
    else:
        await Files4DefiningDefect.setoffassessment('geometry', 'defect defining')
    print('done DefProcessing')