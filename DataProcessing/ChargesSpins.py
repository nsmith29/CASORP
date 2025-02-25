#!/usr/bin/env python3


import asyncio
import json

from asgiref.sync import sync_to_async
import numpy as np
import pandas as pd
import sys
import time

from Core.CentralDefinitions import CaS_Settings, Ctl_Settings, Dirs, UArg, ProcessCntrls, percalcdir, ResultsUpdate, \
    Redistribute, SharableDicts, Geo_Settings
from Core.DictsAndLists import boolconvtr
from Core.Messages import ask_question, ErrMessages, Global_lock, SlowMessageLines
from DataCollection.FileSearch import  MethodFiles, Entry4FromFiles
from DataProcessing.ProcessCntral import Files4DefiningDefect, AppendDefDict
from DataProcessing.Geometry import viaperfectretrieval, DefProcessing, recorddefatnumanswers



__all__ = {'CntrlChrgSpns', 'ThreadOne', 'ThreadTwo', 'BaderFiles', 'OnlyProcessing', 'retrieval'}


async def CntrlChrgSpns():
    text = str("\n                                      {bcolors.METHOD}{bcolors.UNDERLINE}CHARGE AND SPIN DATA "
               "PROCESSING{bcolors.ENDC}{bcolors.METHOD}...")
    SlowMessageLines(text)
    event = asyncio.Event()
    # async run two coroutine paths
    coroutines = [ThreadOne(event), ThreadTwo(event)]
    tasks = await asyncio.gather(*coroutines)

async def ThreadOne(e1):
    #----------- [A] -----------
    # Ask user question on charges and spins for only defect related atoms.
    result = await  sync_to_async(ask_question)("CaSQ1", "YorN", ['Y', 'N'])
    CaS_Settings.nn_and_def = boolconvtr[result]
    e1.set()  # Alert ThreadTwo that user has answered question
    await asyncio.sleep(0.5)
    e1.clear()  # Clear event so that event can be reset by ThreadTwo
    #---opt i[B] & iii[B]---
    if CaS_Settings().nn_and_def is True and CaS_Settings().bader_missing is True or \
            CaS_Settings().nn_and_def is True and CaS_Settings().bader_missing is False:
        # Search all calculation subdirectories for files related to processing only defect related atom charge & spins.
        await OnlyProcessing()
    # ---opt ii[B]---
    if CaS_Settings().nn_and_def is False and CaS_Settings().bader_missing is True:
        # Charges/spins for all atoms wanted but bader files missing for calcs - collect M&H spins/charges for all atoms
        for n, r, c in [[n, r, c] for n, r, c in [i[:3:] for i in CaS_Settings().dirs_missing_bader['defect']]]:
            await retrieval('defect', n, r, c)
    #---opt i[B] & ii[B]---
    if CaS_Settings().nn_and_def is True and CaS_Settings().bader_missing is True:
        # Wait for alert from ThreadTwo that Warning message shown & question answered.
        await e1.wait()
        e1.clear()
    #---opt iV[B]---
    if CaS_Settings().nn_and_def is False and CaS_Settings().bader_missing is False:
        # Collect B&M&H spins/charges for all atoms for all defect calculations.
        await percalcdir(retrieval)('defect')
    # ---opt i[C] & iii[C]---
    if CaS_Settings().nn_and_def is True and CaS_Settings().bader_missing is True or \
            CaS_Settings().nn_and_def is True and CaS_Settings().bader_missing is False:
        if 'geometry' in ProcessCntrls().processwants:
            Redistribute('Geo_Settings.checkdefatnum')
        if Geo_Settings().checkdefatnum is True:
            answers = await SlowMessageLines(str(Geo_Settings().question_def_sites), a_sync=True, Qask=True).asynctoask("'N' in results")
            await recorddefatnumanswers(answers)
        e1.set()
    # ---opt ii[C]--- = percalcdir for 'defect' if n, r, c not in dirs_missing_bader
    # ---opt iv[C]---

    return

async def ThreadTwo(e1): # handling of Bader and all atom processing no exceptions
    #----------- [A] -----------
    # Search all calculation subdirectories to find files related to processing bader charges.
    await BaderFiles().setoffassessment()
    await e1.wait() # Wait for alert from ThreadOne that user has answered question.
    #---opt i[B] & ii[B]---
    if CaS_Settings().bader_missing is True and CaS_Settings().nn_and_def is True or \
            CaS_Settings().bader_missing is True and CaS_Settings().nn_and_def is False:
        # Missing files for bader charge analysis picked up.
        await asyncio.sleep(0.2)
        # Run Warning message for missing related bader charge files.
        result = await SlowMessageLines(str(CaS_Settings().dirs_missing_bader), a_sync=True, Qask=True).asynctoask()
        CaS_Settings.cont_bdr = boolconvtr[result[0]]
        # Alert ThreadOne that user has answered associated question to missing bader charge files.
        e1.set()
    # ---opt iv[B]---
    if CaS_Settings().bader_missing is False and CaS_Settings().nn_and_def is False:
        await asyncio.sleep(0.5)
    # ---opt iii[B] & iv[B] & ii [C]---
    if CaS_Settings().bader_missing is False and CaS_Settings().nn_and_def is True or \
            CaS_Settings().bader_missing is False and CaS_Settings().nn_and_def is False or \
            CaS_Settings().bader_missing is True and CaS_Settings().nn_and_def is False:
        # Collect spins/charges for all atoms in perfect structure calculation
        await percalcdir(retrieval)('perfect')
    #---opt iii[B]---
    if CaS_Settings().bader_missing is False and CaS_Settings().nn_and_def is True:
        while Ctl_Settings().defining_except_found is None:
            await asyncio.sleep(0.005)
    #---opt i[C] & iii[C]---
    if CaS_Settings().nn_and_def is True and Ctl_Settings().defining_except_found is True or \
            CaS_Settings().bader_missing is False and CaS_Settings().nn_and_def is True and \
            Ctl_Settings().defining_except_found is True:
        # Run Warning message for missing files needed to define defect type and atoms related to defect.
        await SlowMessageLines(str(Ctl_Settings().e2_defining), a_sync=True).asyncprint()
        # Bader files found for all but defining defect files missing for calcs - collect spins/charges for all atoms
        for n, r, c in [[n, r, c] for n, r, c in [i[:3:] for i in Ctl_Settings().e2_defining['defect']]]:
            await retrieval('defect', n, r, c)
        if Geo_Settings().checkdefatnum is True:
            await e1.wait()
            for n, r, c in [[n, r, c] for n, r, c in [ele[0] for ele in
                                                      [value for value in Geo_Settings().question_def_sites.values()
                                                       for value in value]]]:
                await retrieval('defect', n, r, c)
    #---opt ii[C]---
    #---opt iv[C]---

    return

class BaderFiles(MethodFiles):
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
            dp = '/'.join([d for d in str(Dirs().address_book[kl[0]][kl[1]][kl[2]][kl[3]]["path"]).split('/')
                           if d not in str(UArg().cwd).split('/')])
            CaS_Settings.dirs_missing_bader = await AppendBader('CaS_Settings', 'dirs_missing_bader')(kl, dp)

class AppendBader(AppendDefDict):
    def __init__(self, klass, method):
        super().__init__(klass, method)
    def __str__(self):
        str_ = super().__str__()
        str_ = str_ + '{ask_question("CaSQ2", "YorN", ["Y", "N"])}'
        return str_

async def OnlyProcessing():
    if 'geometry' in ProcessCntrls().processwants:
        for name in ['defining_except_found', 'e2_defining', 'i_defining']:
            key = str('Ctl_Settings.' + name)
            Redistribute(key)
    else:
        await Files4DefiningDefect.setoffassessment("charges and spins", "only")
        await viaperfectretrieval(DefProcessing)('defect', ignore=True)

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
    if CaS_Settings().bader_break is not True and CaS_Settings().cont_bdr is True and type_ == "perfect" or \
       CaS_Settings().bader_break is not True and CaS_Settings().cont_bdr is True and [n, r, c] not in \
       [i[:3:] for i in CaS_Settings().dirs_missing_bader[type_]]:
        f, a = Dirs().address_book[type_][n][r][c]["ACF.dat"], int(SharableDicts().smd['total atoms'][0])
        bader = np.loadtxt(f, skiprows=2, usecols=4, max_rows=a, unpack=True)
        clmnstrngs.append("Bader")
        for indx in indices:
            matline = bader[indx]
            TypeC[indx].append(round(int(matline), 3))
    df = pd.DataFrame(TypeC,
                      columns=clmnstrngs, index=indexstrings)
    n = df.columns.str.split(', ', expand=True).values
    df.columns = pd.MultiIndex.from_tuples([('', x[0]) if pd.isnull(x[1]) else x for x in n])
    await asyncio.sleep(0.01)
    return "charges and spins", df