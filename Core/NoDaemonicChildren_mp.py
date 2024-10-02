#!/usr/bin/env python3

import multiprocessing as mp
import multiprocessing.pool
import os
import psutil
from shared_memory_dict import SharedMemoryDict
import signal
import sys
import traceback as tb
import threading as th
from Core.CentralDefinitions import Redistribute
from Core.DictsAndLists import optdict
from DataProcessing.ChargesSpins import CntrlChrgSpns


__all__ = { 'ProcessNoDaemonProcess', 'PoolNoDaemonProcess', 'Rooting'}


def sendkillSignal(error, value, tb_):
    sys.exit(1)


class Thread(th.Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon = None):
        th.Thread.__init__(self, group, target, name, args, kwargs)
        self.original_run = self.run()
        self.run = self.patched_run()

    def patched_run(self):
        try:
            self.original_run()
        except:
            sendkillSignal(*sys.exc_info())

class ProcessNoDaemonProcess(mp.Process):
    """
        Modified version of mp.Process specific for this package to make mp.Pool() non-daemonic child processes.

        Daemon attributes will always be turned as False.

        Inheritance:
            mp.Process(class) : Processes spawned by creating a Process
                                object. Process objects represent activity that is run in
                                a separate process. Equivalents of all the methods of
                                threading.Thread.
    """

    @property
    def daemon(self):
        """
            Overriding property of parent. Process’s daemon flag, a Boolean value. Return whether process is a daemon.

            Change initial value inherited from the creating process to False.
        """
        return False

    @daemon.setter
    def daemon(self, value):
        """
            Overriding property setter of parent. Set whether process is a daemon.

            Process’s daemon flag must be set before start() in mp.Process is called.

            Input:
                value(daemonic) : Sets self._config['daemon'] in mp.Process.
        """
        pass


class PoolNoDaemonProcess(mp.pool.Pool):
    """
        Modified version of mp.pool.Pool specific for this package for mp.Pool() non-daemonic workers.

        Inheritance:
            mp.pool.Pool(class) : Supports an async version of applying functions to arguments.
    """


    def Process(self, *args, **kwargs):
        """
            PoolNoDaemonProcess subclass method inheriting mp.pool.Pool superclass method of same name.

            Inputs:
                *arg:
                **kwargs:
        """

        # call to inherited mp.pool.Pool superclass method, staticmethod Process.
        proc = super().Process(*args,**kwargs)
        # declaring call method of proc as class ProcessNoDaemonProcess.
        proc.__class__ = ProcessNoDaemonProcess

        return proc


class Rooting:
    """
        Rooting of mp.Pool() child process to specific code stem for wanted result processing method of child process.

        Wanted entry point function is determined via evaluation and execution of the item value str corresponding to
        the item key str within optdict which matches the input str value of the child worker process.

        Class definitions:
            optdict(dict) : Dictionary of specific entry point functions for each
                            implemented result processing method.

        Inputs:
            want(str)     : str assigned to specific mp.Pool() child process accessing
                            class which equates to the specific result processing
                            method assigned to the child worker process out of the
                            result processing methods chosen by user.
    """

    def __init__(self, want):
        Redistribute()
        run = eval(str("{}()".format(optdict.get(want))))

