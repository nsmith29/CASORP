#!/usr/bin/env python3

import json
import numpy as np
import os
import queue
import sys
import threading as th
import time

from Core.CentralDefinitions import boolconvtr, CaS_Settings, create_nested_dict, Dirs, proxyfunction, UArg
from Core.Messages import ask_question, Delay_Print, ErrMessages, Global_lock, SlowMessageLines
from DataAnalysis.ChargeAnalysis import Prep
from DataCollection.FileSearch import Entry4Files, MethodFiles, Method

__all__ = {'CntrlChrgSpns', 'BaderProcessing', 'OnlyProcessing'}


def CntrlChrgSpns():

    text = str("\n                                      {bcolors.METHOD}{bcolors.UNDERLINE}CHARGE AND SPIN DATA "
               "PROCESSING{bcolors.ENDC}{bcolors.METHOD}...")

    SlowMessageLines(text)

    Q1_, Q2_ = queue.Queue(), queue.Queue()

    t1 = th.Thread(target=ThreadOne, args=(Q1_, Q2_))
    t2 = th.Thread(target=ThreadTwo, args=(Q1_, Q2_))

    [x.start() for x in [t1, t2]]
    [x.join() for x in [t1, t2]]


class ThreadOne:
    def __init__(self, Q1_, Q2_):
        # out_msg -> msg to sent to threadtwo; in_msg -> msg sent from threadtwo
        self._out_msg, self._in_msg, self._exist = Q1_, Q2_, False
        with Global_lock().lock:
            CaS_Settings.nn_and_def = boolconvtr[ask_question("CaSQ1", "YorN", ['Y', 'N'])]
        self._out_msg.put('check_error')
        self.control_tree(str(CaS_Settings().nn_and_def).lower())

    def control_tree(self, bool_):
        while self._exist is False:

            # OnlyProcessing should only be done if answer to CaSQ1 is yes - NEW: then need to check if geometry was in
            # imputted wants of user to work out whether OnlyProcessing should be done - Will need to use
            # SharedMemoryDict to transfer information [like the g_settings equivalent of e2n_a_d and i_nad] between
            # geometry, and charges and spins processes.
            # In geometry branch will need to test for Charges and Spins in
            OnlyProcessing(self._in_msg)
            while self._in_msg.empty() is False:
                item = self._in_msg.get()
                do = eval("self.{}_{}()".format(bool_, item)) if item != 'end' else eval("self.{}()".format(item))
            while self._in_msg.empty() is True:
                time.sleep(0.5)

    def true_set_off(self):
        self._out_msg.put('set_off_perf')
        if CaS_Settings().nn_and_def_except_found is True:
            ErrMessages.CaS_FileNotFoundError(CaS_Settings().e2n_a_d['defect'], ".inp and ''.xyz", "charges and spins "
                                                "for only defect-related atoms", Global_lock().lock)

    def false_set_off(self):
        self._out_msg.put('set_off_perf')
        Prep('defect')
            # self._out_msg.put('end')

    def end(self):
        self._exist = True
        sys.exit(0)


class ThreadTwo:

    def __init__(self, Q1_, Q2_):
        # out_msg -> msg to sent to threadone; in_msg -> msg sent from threadone
        self._out_msg, self._in_msg, self._exist = Q2_, Q1_, False
        self.control_tree()

    def control_tree(self):
        BaderProcessing()
        while self._exist is False:
            while self._in_msg.empty() is False:
                item = self._in_msg.get()
                do = eval("self.{}()".format(item))

            while self._in_msg.empty() is True:
                time.sleep(0.5)

    def check_error(self):
        if CaS_Settings.bader_missing is True:
            ErrMessages.CaS_FileNotFoundError(CaS_Settings().dirs_missing_bader['defect'], "-ELECTRON_DENSITY-1_0.cube",
                                              "analysis of Bader charges of atoms", Global_lock().lock)
            CaS_Settings.cont_bdr = boolconvtr[ask_question("CaSQ2", "YorN", ["Y", "N"])]
        self._out_msg.put('set_off')
        if CaS_Settings.bader_missing is True:
            for calclist in CaS_Settings().dirs_missing_bader['defect']:
                _ = calclist.pop(3)

    def set_off_perf(self):
        Prep('perfect')

    def end(self):
        print('existing', 'DP.CS L100')
        self._out_msg.put('end')
        self._exist = True
        sys.exit(0)


class BaderProcessing(MethodFiles):

    def __init__(self2):
        super().__init__('charges and spins','bader')
        super().assessment_tree(self2, self2.type_, self2.flexts, self2.sect)

    def option4(self2, kl, extension):
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
            dp = '/'.join([d for d in str(Dirs().address_book[kl[0]][kl[1]][kl[2]][kl[3]]["path"]).split('/') if d not
                           in str(UArg().cwd).split('/')])
            kl.append(dp)
            _, CaS_Settings.dirs_missing_bader = proxyfunction(kl, None, None, None, CaS_Settings().dirs_missing_bader)


class OnlyProcessing(MethodFiles):
    def __init__(self2, Q_):
        Method.__init__(self2, 'charges and spins', 'only')
        super().assessment_tree(self2, self2.types[1], [self2.flexts_[1][0]], False)
        super().assessment_tree(self2, self2.types[0], self2.flexts_[0], True, None, 'geometry')

    def option2(self2, keylst, extension, flpath, Q):
        return exec(f'self2.option2{keylst[0]}(keylst, extension, flpath, Q)')

    def option2defect(self2, k, et, flpath, Q):
        paths, rtn, fnd = et if et == '.inp' else self2.flexts_[1][1], 'pass' if et == '.inp' else 'continue', \
                          False if et != '.inp' else None
        Dirs.address_book, _ = create_nested_dict(k, [paths], [flpath], Dirs().address_book)
        if et == '.inp':
            xyzname = Entry4Files(flpath[0], 'inp', 'charges and spins').Return()
            Q.put([False, [xyzname[1]] ])
        else:
            if CaS_Settings().nn_and_def_except_found is True:
                for n,r,c,e in ([n,r,c,e] for n,r,c,e in CaS_Settings().i_nad['defect'] if n==k[1] and r==k[2] and e==et):
                    Dirs.address_book, _ = create_nested_dict(['defect', n, r, c], [str(paths + '*')], [flpath],
                                                              Dirs().address_book)
                    path = [p for n_, r_, c_, p in CaS_Settings().e2n_a_d['defect'] if  n_==n and r_==r and c_==c][0]
                    CaS_Settings().e2n_a_d['defect'].remove([n, r, c, path])
                    CaS_Settings().i_nad['defect'].remove([n, r, c, e])
        return rtn

    def option2perfect(self2, keylst, extension, flpath, Q):
        replace_rtn = MethodFiles.option2(self2, keylst, extension, flpath, Q)
        return replace_rtn

    def option4(self2, keylst, extension):
        exec(f'self2.option4{keylst[0]}(keylst, extension)')

    def option4perfect(self2, keylst, extension):
        MethodFiles.option4(self2, keylst, extension)

    def option4defect(self2, k, e):
        CaS_Settings.nn_and_def_except_found, fnd = True if CaS_Settings().nn_and_def_except_found == None else \
            CaS_Settings().nn_and_def_except_found, False if e != '.inp' else None
        dp = '/'.join([d for d in str(Dirs().address_book[k[0]][k[1]][k[2]][k[3]]["path"]).split('/') if d not in
                       str(UArg().cwd).split('/')])
        k.append(dp)
        _, CaS_Settings.e2n_a_d = proxyfunction(k, None, None, None, CaS_Settings().e2n_a_d)
        for n,r,c in ([n,r,c] for n,r,c in Dirs().dir_calc_keys[k[0]] if n==k[1] and r==k[2] and c!=k[3] and e!='.inp'):
            if self2.flexts_[1][1] in Dirs().address_book['defect'][n][r][c].keys() and fnd is False:
                if e == str(Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]]).split('/')[-1]:
                    path, fnd = Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]].get(), True
                    CaS_Settings().e2n_a_d['defect'].remove([k[1], k[2], k[3], k[-1]])
                    Dirs.address_book, _= create_nested_dict(k, [str(path+'*')],[Dirs().address_book['defect'][n][r][c]
                                                                                 [path]], Dirs().address_book)
        if fnd is not True:
            k.remove(dp)
            k.append(e)
            _, CaS_Settings.i_nad = proxyfunction(k, None, None, None, CaS_Settings().i_nad)


