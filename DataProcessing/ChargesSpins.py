#!/usr/bin/env python3


import asyncio
from asgiref.sync import sync_to_async
import numpy as np
import pandas as pd
import sys

from Core.CentralDefinitions import CaS_Settings, Ctl_Settings, Dirs, proxyfunction, UArg, ProcessCntrls, percalcdir, \
    ResultsUpdate, SharableDicts
from Core.DictsAndLists import boolconvtr
from Core.Messages import ask_question, ErrMessages, Global_lock, SlowMessageLines
from DataCollection.FileSearch import  MethodFiles, Entry4FromFiles
from DataProcessing.ProcessCntral import Files4DefiningDefect
# from DataAnalysis.ChargeAnalysis import retrieval


__all__ = {'CntrlChrgSpns', 'BaderProcessing', 'retrieval', 'OnlyProcessing', 'ThreadOne', 'ThreadTwo'}


async def CntrlChrgSpns():
    # Main Asyncio task - set up subtasks
    text = str("\n                                      {bcolors.METHOD}{bcolors.UNDERLINE}CHARGE AND SPIN DATA "
               "PROCESSING{bcolors.ENDC}{bcolors.METHOD}...")
    SlowMessageLines(text)
    event = asyncio.Event()
    coroutines = [ThreadOne(event), ThreadTwo(event)]
    tasks = await asyncio.gather(*coroutines)
    print(tasks)

async def ThreadOne(e1):
    result = await  sync_to_async(ask_question)("CaSQ1", "YorN", ['Y', 'N'])
    CaS_Settings.nn_and_def = boolconvtr[result]
    e1.set()
    await asyncio.sleep(0.5)
    e1.clear()
    await asyncio.sleep(0.2)
    if CaS_Settings().bader_missing is True:
        if CaS_Settings().nn_and_def is True:
            await OnlyProcessing()
            await e1.wait()
            if Ctl_Settings().defining_except_found is True:
                ErrMessages.CaS_FileNotFoundError(Ctl_Settings().e2_defining['defect'], ".inp and ''.xyz",
                                                  "charges and spins "
                                                  "analysis of only defect-related atoms")
        else:
            await e1.wait()
    else:
        await percalcdir(retrieval)('defect')
    return True
    # 1. Ask question CaSQ1
    # 2. if True, OnlyProcessing; if False, wait for answer to whether there is errors from BaderProcessing

async def ThreadTwo(e1):
    await BaderProcessing().setoffassessment()
    await e1.wait()
    if CaS_Settings().bader_missing is True:
        await asyncio.sleep(0.2)
        ErrMessages.CaS_FileNotFoundError(CaS_Settings().dirs_missing_bader['defect'], "-ELECTRON_DENSITY-1_0.cube",
                                              "analysis of Bader charges of atoms")
        result = await sync_to_async(ask_question)("CaSQ2", "YorN", ["Y", "N"])
        CaS_Settings.cont_bdr = boolconvtr[result]
        e1.set()
        for calclist in CaS_Settings().dirs_missing_bader['defect']:
            _ = calclist.pop(3)
    await asyncio.sleep(0.5)
    await percalcdir(retrieval)('perfect')
    return True
    # 1. BaderProcessing
    # 2. Check for errors from BaderProcessing

class BaderProcessing(MethodFiles):
    def __init__(self2):
        super().__init__('charges and spins', 'bader')
    @classmethod
    async def setoffassessment(cls):
        self2 = cls()
        for type_, flexts in zip(self2.types, self2.flexts_):
            self2.type_, self2.flexts = type_, flexts
            await super().assessment_tree(self2, self2.type_, self2.flexts, self2.sect)
    async def option4(self2, kl, extension):
        await asyncio.sleep(0.01)
        try:
            if kl[0] == 'perfect':
                raise ConnectionAbortedError
            else:
                raise FileNotFoundError
        except ConnectionAbortedError:
            CaS_Settings.bader_break = True
            path_ = Dirs().address_book[kl[0]][kl[1]][kl[2]][kl[3]]["path"]
            ErrMessages.CaS_ConnectionAbortedError(path_, Global_lock().lock)
            sys.exit(0)
        except FileNotFoundError:
            CaS_Settings.bader_missing = True
            dp = '/'.join([d for d in str(Dirs().address_book[kl[0]][kl[1]][kl[2]][kl[3]]["path"]).split('/') if d not in str(UArg().cwd).split('/')])
            kl.append(dp)
            _, CaS_Settings.dirs_missing_bader = proxyfunction(kl, None, None, None, CaS_Settings().dirs_missing_bader)

async def OnlyProcessing():
    if 'geometry' in ProcessCntrls().processwants:
        print("geometry should have worked this out already [code L952]")
    else:
        await Files4DefiningDefect.setoffassessment("charges and spins", "only")

@ResultsUpdate
async def retrieval(type_, n, r, c, indices=None):
    TypeC, indexstrings, clmnstrngs = [], [], []
    log = Dirs().address_book.copy()[type_][n][r][c]['log']
    item = await Entry4FromFiles(log, 'log', "charges and spins")
    mulliken, hirshfeld = item[0], item[1]
    indices = [i for i in range(0, len(mulliken))] if not indices else indices
    clmnstrngs.extend(["Mulliken, \u03B1 pop", "Mulliken, \u03B2 pop", "Mulliken, charges", "Mulliken, spins"])
    for indx, matline in zip(indices, mulliken):
        indexstrings.append(indx)
        TypeC.append(matline)
    clmnstrngs.extend(["Hirshfeld, \u03B1 pop", "Hirshfeld, \u03B2 pop", "Hirshfeld, charges", "Hirshfeld, spins"])
    for indx, matline in zip(indices, hirshfeld):
        TypeC[indx].extend(matline)
    if CaS_Settings().bader_break is not True and [n, r, c] not in CaS_Settings().dirs_missing_bader[type_]:
        f, a = Dirs().address_book[type_][n][r][c]["ACF.dat"][0], int(SharableDicts().smd['total atoms'][0])
        bader = np.loadtxt(f, skiprows=2, usecols=4, max_rows=a, unpack=True)
        clmnstrngs.append("Bader")
        for indx in indices:
            matline = bader[indx]
            TypeC[indx].append(round(int(matline), 3))
    elif CaS_Settings().bader_break is not True and [n, r, c] in CaS_Settings().dirs_missing_bader[type_]:
        print(n, r, c)
    df = pd.DataFrame(TypeC,
                      columns=clmnstrngs, index=indexstrings)
    n = df.columns.str.split(', ', expand=True).values
    df.columns = pd.MultiIndex.from_tuples([('', x[0]) if pd.isnull(x[1]) else x for x in n])
    await asyncio.sleep(0.01)
    return "charges and spins", df