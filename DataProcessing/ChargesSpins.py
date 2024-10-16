#!/usr/bin/env python3


import asyncio
from asgiref.sync import sync_to_async
import sys
import time

from Core.CentralDefinitions import boolconvtr, CaS_Settings, Ctl_Settings, Dirs, proxyfunction, UArg, ProcessCntrls
from Core.Messages import ask_question, ErrMessages, Global_lock, SlowMessageLines
from DataProcessing.ProcessCntral import Files4DefiningDefect
from DataAnalysis.ChargeAnalysis import retrieval, percalcdir
from DataCollection.FileSearch import  MethodFiles

__all__ = {'CntrlChrgSpns', 'BaderProcessing', 'OnlyProcessing'}


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

