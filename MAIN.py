#!/usr/bin/env python3

import multiprocessing as mp
import os
import os.path as pth
import queue
import sys
import time
import threading as th
from shared_memory_dict import SharedMemoryDict

from Core.CentralDefinitions import boolconvtr, Dirs, End_Error, ProcessCntrls, SharableDicts, sharable_vars, UArg,\
    Userwants
from Core.DictsAndLists import options
from Core.Messages import ask_question, ErrMessages, Global_lock, SlowMessageLines
from Core.NoDaemonicChildren_mp import PoolNoDaemonProcess, Rooting
from DataCollection.FileSearch import Cataloging

def programme_setup(wd):
    Dirs.executables_address = pth.join(wd, "Executables")

class Start:
    def __init__(self, cwd, _wd, proxylist, *args):
        """
            Processing command line arguments upon running of MAIN.py. Decides code path to take.
        """

        sharable_vars('Dirs.executables_address', pth.join(_wd,"Executables"))
        # set sudo current working directory
        os.chdir(cwd)
        self.proxylist, self.args = proxylist, list(args)[0]

        sharable_vars("UArg.cwd", cwd)

        self.error_testing(cwd)

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
        _Q_ = mp.Queue()
        b = th.Thread(target=self.branch_, args=(q_,))
        b.start()
        Cataloging(UArg.defd, 'defect', q_)
        b.join()
        # print('Out of branch_ [M L57]')

        self.proxylist.append(ProcessCntrls().processwants)

        self.Return()

    def branch_(self, q_):
        t1 = th.Thread(target=Cataloging, args=(UArg.perfd, 'perfect', q_))
        t2 = th.Thread(target=self.questions2ask, args=())
        while q_.empty() is True:
            time.sleep(0.05)
        while q_.empty() is False:
            item = q_.get()
            # print(item)
            if item == 'start':
                [x.start() for x in [t1, t2]]

                [x.join() for x in [t1, t2]]
                q_.put('finished')
            elif item == 'end':
                pass
            sys.exit(1)

    def Return(self):
        return self.proxylist

    def questions2ask(self):
        """
            Asking the user base questions to gain understanding of how user would like the programme to do.
        """
        time.sleep(0.5)

        with Global_lock().lock:
            sharable_vars('ProcessCntrls.processwants', ask_question("MQ1", 'list', list(options)))

        with Global_lock().lock:
            sharable_vars('Userwants.analysiswants',  boolconvtr[ask_question("MQ2", "YorN", ['Y', 'N'])])

        with Global_lock().lock:
            sharable_vars('Userwants.displaywants',
                          boolconvtr[ask_question("MQ2fup1", "YorN", ['Y','N'])] if Userwants.analysiswants is \
                                                                                          True else boolconvtr['N'])

            sharable_vars('Userwants.overwrite', None if Userwants.analysiswants is True \
                else boolconvtr[ask_question("MQ2fup2", "YorN", ['Y','N'])])

    def error_testing(self, cwd):
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
    smd = SharableDicts().smd #SharedMemoryDict(name="CASORP", size=1024)
    smd.shm.close()
    CPUs2use, manager = int(os.cpu_count() * 2 / 3), mp.Manager()
    _wd, cwd =  os.getcwd(), '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0'
    p = PoolNoDaemonProcess() # CPUs2use
    proxylist = manager.list()
    Start(cwd, _wd, proxylist, sys.argv)
    # start = p.apply(Start, [cwd, _wd, proxylist, sys.argv])
    run = p.map(Rooting, proxylist[0])
    p.close()
    p.join()
    smd.shm.close()
    smd.shm.unlink()
    del smd

