#!/usr/bin/env python3

"""
    run: ./MAIN.py perf_bulk_directory parent_defect_directory chemical_potentials_directory keyword [optional]
    keyword: all/only/except
    [optional]: name(s)_of_defect_subdirectories

    Must be run individually per specific material system.
"""

import multiprocessing as mp
import os
import os.path as pth
import queue
import sys
import time
import threading as th
from shared_memory_dict import SharedMemoryDict

from Core.CentralDefinitions import  Dirs, End, End_Error, ProcessCntrls, SharableDicts, sharable_vars, UArg,\
    Userwants, Pool_Args_check, Geo_Settings
from Core.DictsAndLists import options, boolconvtr
from Core.Messages import ask_question, ErrMessages, Global_lock, SlowMessageLines, Delay_Print
from Core.NoDaemonicChildren_mp import PoolNoDaemonProcess, Rooting
from DataCollection.FileSearch import Cataloging


class Start:
    def __init__(self, cwd, _wd, proxylist, t, *args):#
        """
            Processing command line arguments upon running of MAIN.py. Decides code path to take.
        """
        sharable_vars('Dirs.executables_address', pth.join(_wd,"Executables"))
        # set sudo current working directory
        os.chdir(cwd)
        self.proxylist, self.args = proxylist, list(args)[0]
        sharable_vars("UArg.cwd", cwd)
        self.error_testing(cwd, t)
        # saving directory str given by user for 1st 3 arguments.
        for var, value in zip(['UArg.perfd','UArg.defd','UArg.cpt'], [pth.join(cwd, self.args[1]), pth.join(cwd, self.args[2]), pth.join(cwd, self.args[3])]):
            sharable_vars(var, value)
        if self.args[4] != 'all':
            # creation of list of specific defect subdirectories given by user.
            defects = [i for i in self.args[5:]]
            # saving defect subdirectory name(s) & enacting setting for data processing of wanted defect subdirectories.
            for var, value in zip(['UArg.only', 'UArg.subd'], [True if self.args[4] == 'only' else False, defects]):
                sharable_vars(var, value)
        ## multithreading set up
        q_ = queue.Queue()
        c_ = th.Condition()
        self.done = None
        b = th.Thread(target=self.branch_, args=(c_, q_, t))
        d = th.Thread(target=Cataloging, args=(UArg().defd, 'defect', c_, q_, t))
        _ = th.Thread(target=Delay_Print, args=(['-'], Global_lock().lock, 0.25, q_))
        [x.start() for x in [b, d]]
        b.join()
        while b.is_alive() is False and d.is_alive() is True:
            _.start()
            break
        d.join()
        while d.is_alive() is False and _.is_alive() is True:
            q_.put('finished')
            _.join()
            break
        while End.triggered is True:
            sys.exit(1)
        # self.proxylist.append(ProcessCntrls().processwants)
        self.Return()
    def branch_(self, c_, q_, t):
        t1 = th.Thread(target=Cataloging, args=(UArg.perfd, 'perfect'))
        t2 = th.Thread(target=self.questions2ask, args=())
        with c_:
            c_.wait_for(lambda : q_.empty() is False)
            item = q_.get()
            if item == 'start':
                [x.start() for x in [t1, t2]]
                [x.join() for x in [t1, t2]]
            elif item == 'end':
                pass
            # print('branch finished in', time.time()-t, '[M L85]')
            sys.exit(1)
    def Return(self):
        return self.proxylist
    def questions2ask(self):
        """
            Asking the user base questions to gain understanding of how user would like the programme to do.
        """
        with Global_lock().lock:
            answer  = ask_question("MQ1", 'list', list(options))
            if type(answer) == tuple:
                self.proxylist.append(list(answer)[0])
                answer = list(answer)[1]
            else:
                self.proxylist.append(answer)
            sharable_vars('ProcessCntrls.processwants', answer)
        with Global_lock().lock:
            sharable_vars('Userwants.analysiswants',  boolconvtr[ask_question("MQ2", "YorN", ['Y', 'N'])])
        with Global_lock().lock:
            sharable_vars('Userwants.displaywants',
                          boolconvtr[ask_question("MQ2fup1", "YorN", ['Y','N'])] if Userwants.analysiswants is \
                                                                                          True else boolconvtr['N'])
            sharable_vars('Userwants.overwrite', None if Userwants.analysiswants is True \
                else boolconvtr[ask_question("MQ2fup2", "YorN", ['Y','N'])])
    def error_testing(self, cwd, t):
        """
            testing whether commandline arguments 1-4 given by user trigger any error codes.
        """
        # whether correct number of arguments has been given,
        End_Error(len(self.args) > 4, ErrMessages.MAIN_IndexError())
        # whether fourth argument is a valid keyword.
        End_Error(self.args[4] in ["all", "except", "only"], ErrMessages.MAIN_KeyError(self.args[4]))
        # whether strs given in argvs 1, 2, and 3 correspond to actual directories.
        for i in 1, 2, 3:
            End_Error(pth.exists(pth.join(cwd, str(self.args[i]))) is True, ErrMessages.MAIN_DirNotFndError(self.args[i], i))

if __name__ =='__main__':
    smd = SharableDicts().smd
    smd.shm.close()
    CPUs2use, manager  = int(os.cpu_count() * 2 / 3), mp.Manager()
    _wd, cwd =  os.getcwd(), '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0'
    proxylist = manager.list()
    t = time.time()
    Start(cwd, _wd, proxylist, t, sys.argv) #
    p = PoolNoDaemonProcess()  # CPUs2use
    run = p.map(Rooting, proxylist[0])
    p.close()
    p.join()
    smd.shm.close()
    smd.shm.unlink()
    del smd
    Geo_Settings().closedown()
