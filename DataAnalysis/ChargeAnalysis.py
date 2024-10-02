#!/usr/bin/env python3

import numpy as np
import pandas as pd

from DataCollection.FileSearch import Entry4Files
from Core.CentralDefinitions import CaS_Settings, Dirs, get_dirs, ResultsUpdate, SharableDicts

__all__ = {'Extraction', 'Prep'}


class Extraction:

    def __init__(self, type_):
        self.t, self.n, self.r, self.c = '', '', '', ''
        self.data(self, type_)


    @get_dirs
    def data(self, t, n, r, c):
        self.t, self.n, self.r, self.c = t, n, r, c
        self.mulliiken, self.hirshfeld = Entry4Files(Dirs.address_book[t][n][r][c]['log'], 'log',
                                                    "charges and spins").Return()

        f = Dirs.address_book[t][n][r][c]["ACF.dat"][0]
        # print(file, SharableDicts().smd['total atoms'], 'DA.CA L26')
        a  = int(SharableDicts().smd['total atoms'])
        self.bader = np.loadtxt(f, skiprows=2, usecols=4, max_rows=a, unpack=True) if CaS_Settings().bader_break is not \
                                                                                      True and [n, r, c] not in \
                                                                                      CaS_Settings().dirs_missing_bader[t] else []

class Prep(Extraction):

    def __init__(self2, type_, indices = None):
        super().__init__(type_)
        self2.indices = [i for i in range(0, len(self2.mulliiken))] if not indices else indices
        self2.collation(self2, 'charges and spins')

    @ResultsUpdate
    def collation(self):
        TypeC, indexstrings, clmnstrngs = [], [], []

        clmnstrngs.extend(["Mulliken, \u03B1 pop", "Mulliken, \u03B2 pop", "Mulliken, charges", "Mulliken, spins"])
        for indx, matline in zip(self.indices, self.mulliiken):
            indexstrings.append(indx)
            TypeC.append(matline)

        clmnstrngs.extend(["Hirshfeld, \u03B1 pop", "Hirshfeld, \u03B2 pop", "Hirshfeld, charges", "Hirshfeld, spins"])
        for indx, matline in zip(self.indices,  self.hirshfeld):
            TypeC[indx].extend(matline)

        if len(self.bader) > 0:
            clmnstrngs.append("Bader")
            for indx, matline in zip(self.indices, self.bader):
                TypeC[indx].append(round(int(matline), 3))

        df = pd.DataFrame(TypeC,
                          columns=clmnstrngs, index=indexstrings)
        n = df.columns.str.split(', ', expand=True).values
        df.columns = pd.MultiIndex.from_tuples([('', x[0]) if pd.isnull(x[1]) else x for x in n])

        return df