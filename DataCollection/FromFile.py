#!/usr/bin/env python3


import multiprocessing as mp
from  Core.CentralDefinitions import TESTING
from Core.DictsAndLists import inp_var_fo, inp_want, log_var_fo, log_want


__all__ = {'Update', 'ResultsRetrieve', 'OpenFile', 'Iterate'}


class OpenFile:
    """
        Opening file and recording all lines from file as a list.
    """

    def __init__(self, os_path):
        opened = open(os_path, 'r')
        self.lines, self.index = [opened.readlines(), len(opened.readlines()) + 1]
        opened.close()


class Iterate(OpenFile, object):
    """
        Iterating through all the lines of file.
    """

    def __init__(self, func):
        self.func = func

    def __call__(self, self2, os_path, varitem, *args):
        OpenFile.__init__(self, os_path)
        if len(self.lines) > 100000 and not list(args):
            ln = [ln for ln in self.lines if ln.startswith(varitem["locate"])][0]
            self.func(self2, varitem, ln)
        else:
            lines = self.lines[::-1] if varitem.get("reverse") is True else self.lines

            Ars =  [ self.lines ] if list(args) else []
            while varitem.get("found") is False and varitem.get("found") is not None:
                for ln in reversed(lines):
                    self.index -= 1

                    varitem = self.func(self2, varitem, ln, *eval("{}".format(Ars)))


class Update:
    """
        Updating varitem dictionary during the mp.process.
    """

    def __init__(self2, varitem):
        self2.varit = varitem

    def found(self2):
        """
            Updating the item value of the "found" key of a variable from False to None.
        """

        self2.varit.update({"found": None})

    def extra(self2, list):
        """
            Updating with intermediate data collected during searching the log file.
        """

        for i in range(0, int(len(list) / 2)):
            self2.varit.update({list[int(2 * i)]: list[int(2 * i + 1)]})

    def switch(self2):
        """
           Switch item values so alternative str is started to be looked for in file.
        """

        rnge = int(len(self2.varit["switch"]) / 2)
        keys, values = [self2.varit["switch"][i] for i in range(0, rnge)], [self2.varit[self2.varit["switch"][rnge + i]]
                                                                           for i in range(0, rnge)]
        [self2.varit.update({key : value}) for key, value in zip(keys, values)]

        self2.varit.update({"swapped": True})

    def reset(self2):
        """
            Resetting varitem dictionary to defaults.
        """

        self2.varit.update({"found": False})

        if "reset" in self2.varit and self2.varit["reset"]:
            [self2.varit.update({self2.varit["reset"][int(2 * i)]: self2.varit["reset"][2 * i + 1]}) for i in
             range(0, int(len(self2.varit["reset"]) / 2))]

        elif "swapped" in self2.varit and self2.varit["swapped"] is True:
            self2.switch()
            self2.varit.update({"swapped": False})


class ResultsRetrieve:
    """
        Set up for creation of mp.Process() processes.
    """

    def __init__(self, file, kywrd):
        self.want, manager = eval("{}_want[kywrd]".format(file)), mp.Manager()

        self.process, self.v2rtn = dict(), manager.list([manager.list() for i in range(sum([len(self.want)]))])


    # mp set up in old FromFile.__init__

    def compute(self):
        """
            Running mp.Process() processes.
        """
        processes = []
        for indx in self.process:
            processes.append(self.process[indx])
        [x.start() for x in processes]
        [x.join() for x in processes]
    # old FromLog.compute





