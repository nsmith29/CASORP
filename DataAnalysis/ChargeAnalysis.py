#!/usr/bin/env python3

import asyncio
import numpy as np
import pandas as pd

from DataCollection.FileSearch import Entry4FromFiles, GetDirs_iterator
from Core.CentralDefinitions import CaS_Settings, Dirs, ResultsUpdate, SharableDicts


__all__ = {'retrieval', 'percalcdir'}


def percalcdir(func):
    async def wrapper(type_, indices=None):
        async for item_ in GetDirs_iterator(Dirs().dir_calc_keys[type_]):
            n, r, c = item_[0], item_[1], item_[2]
            await func(type_, n, r, c, indices)
    return wrapper

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