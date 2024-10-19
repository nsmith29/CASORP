#!/usr/bin/env python3

# import json
import asyncio
import multiprocessing as mp

import sys
from shared_memory_dict import SharedMemoryDict
from Core.DictsAndLists import boolconvtr, args4pool
from Core.Iterables import GetDirs_iterator

__all__ = {'add2addressbook', 'CaS_Settings', 'create_nested_dict', 'CreateSharableDicts', 'Ctl_Settings', 'Dirs',
           'End', 'End_Error', 'Geo_Settings', 'GetDirs', 'proxyfunction', 'ProcessCntrls', 'Redistribute',
           'ResultsUpdate', 'SaveProperties', 'SharableDicts', 'sharable_vars', 'TESTING', 'savekeys', 'UArg',
           'Userwants'}


## functions

def savekeys(func):
    """
        Adding list of strs of dict major nested keys - name, run, and chrg - for specific calc to separate dict.
    """
    def wrapper(keys, subkeys, paths, d1, d2=None, name=None, *args):
        d1 = func(keys, subkeys, paths, d1)
        if name:
            CreateSharableDicts(name[0], d1)
        if d2 is not None:
            assert isinstance(d2, dict), "d2 must be a dictionary which can be populated with list of keys"
            assert keys[0] in d2.keys(), "First str item in keys must be a key within d2"
            if not d2[keys[0]]:
                d2[keys[0]] = [keys[1:]]
            elif len(keys) == 4 and [keys[1], keys[2], keys[3]] not in d2[keys[0]] or len(keys) == 5 and [keys[1], keys[2], keys[3], keys[4]] not in d2[keys[0]]:
                d2[keys[0]].append(keys[1:])
            if name:
                CreateSharableDicts(name[1], d2)
        return d1, d2
    return wrapper

def add2addressbook(keys,subkeys, path, d):
    for sub, val in zip(subkeys, path):
        # if sub not in d[keys[0]][keys[1]][keys[2]][keys[3]].keys():
        d[keys[0]][keys[1]][keys[2]][keys[3]][sub] = val
    return d

@savekeys
def create_nested_dict(keys, subkeys, paths, d):
    """
        Creating/Adding nested dict data to [pre-existing] dictionary entries, instead of creating new entry of same key.
    """

    assert isinstance(keys, list), "keys must be a list of major outer nested dict keys strs"
    assert isinstance(subkeys, list), "subkeys must be a list of minor inner nested keys strs"
    assert isinstance(paths, list), "path must be a list of os.path() file path strs"
    assert isinstance(d, dict), "d must be a dictionary which can be populated with keys, subkeys, and paths"
    assert keys[0] in d.keys(), "First str item in keys must be a key within d"

    d_, ks = {keys[0]: d[keys[0]]}, ''
    for indx, key in enumerate(keys):
        d__ = eval("d_{}".format(ks))

        if key in eval("d_{}".format(ks)) and key == keys[-1]:
            k_ = [k for k, v in d__.items()][0]
            for sub, path in zip(subkeys, paths):
                if str("{} : {}".format(sub, path)) not in d__[k_]:
                    d__[k_][sub] = path

        if key not in eval("d_{}".format(ks)):
            if d__ == {}:
                _d = {sub: path for sub, path in zip(subkeys, paths)} if key == keys[-1] else {}
                d__ = {key: _d}
            else:
                d__[key] = {}
                if key == keys[-1]:
                    for sub, path in zip(subkeys, paths):
                        d__[key][sub] = path
            exec(f"d_{ks} = d__ ")

        ks = ks + str("['{}']".format(key))
        d.update({keys[0]: d_[keys[0]]})

    return d

@savekeys
def proxyfunction(keys, subkeys, path, d):
    pass

def sharable_vars(var, value):
    SharableDicts().smd[var] = value
    exec(f'{var} = value')
    SharableDicts().smd.shm.close()

def GetDirs(func):
    def wrapper(self2, type_):
        for n, r, c in ([n, r, c] for n, r, c in Dirs().dir_calc_keys[type_]):
            func(self2, type_, n, r, c)
    return wrapper

def percalcdir(func):
    async def wrapper(type_, indices=None):
        async for item_ in GetDirs_iterator(Dirs().dir_calc_keys[type_]):
            n, r, c = item_[0], item_[1], item_[2]
            await func(type_, n, r, c, indices)
    return wrapper

# classes

class End_Error:
    def __init__(self, cond, msg):
        if eval("{}".format(cond)) is True:
            return
        try:
            if eval(cond) is False:
                raise Exception
        except:
            msg
            smd = SharedMemoryDict(name="CASORP", size=1024)
            smd.shm.close()
            smd.shm.unlink()
            End.triggered = True

            sys.exit(1)

class CreateSharableDicts:
    def __init__(self, name, dict):
        SharableDicts().smd[name] = dict
        SharableDicts().smd.shm.close()

class Pool_Args_check:
    def __init__(self, list):
        print('checking pool args [C.CD L131]')
        for cond, func in args4pool.items():
            print(cond, '[C.CD L133]')
            if eval("{}".format(cond)) is True:
                print('condition is True [C.CD L135]')
                print(func)
                eval("self.{}()".format(func))
    def create_pipe(self):
        print('creating pipe [C.CD L138]')
        conn1, conn2 = mp.Pipe()
        for var, value in zip(['Pool_Args.CaSGeoRecver', 'Pool_Args.CaSGeoSender'], [conn1, conn2]):
            exec(f'{var} = value')
        print("saved properly", Pool_Args().CaSGeoRecver, Pool_Args().CaSGeoSender, '[C.CD L143]')

class Redistribute:
    def __init__(self, t):
        for key in SharableDicts().smd.keys():
            exec(f'{key} = SharableDicts().smd[key]')
        self.populate_processresults('perfect')
        self.populate_processresults('defect')
        SharableDicts().smd.shm.close()
    @GetDirs
    def populate_processresults(self, type, n, r, c):
        ProcessCntrls.processresults, _ = create_nested_dict([type, n, r, c], ProcessCntrls().processwants,
                                                             ProcessCntrls().setup, ProcessCntrls().processresults, None)

class ResultsUpdate:
    def __init__(self, func):
        self._func = func
    async def __call__(self, t, n, r, c, *args):
        method, result = await self._func(t, n, r, c, *args)
        ProcessCntrls().processresults[t][n][r][c].update({method : result})

# class properties

class Ctl_Settings:
    def __init__(self):
        self._defining_except_found = None
        self._e2_defining, self._i_define = {"perfect": [], "defect": []}, {"defect": []}

    @property
    def defining_except_found(self):
        """
            defining_exept_found(bool) : Indication of whether defect subdirectories have been found to be missing
                                         files needed for working out which atoms are related to defect.
        """

        return self._defining_except_found

    @defining_except_found.setter
    def defining_except_found(self, bool):
        """
            bool(bool)                 : To be turned True when a defect subdirectory is found to be missing
                                         file(s) needed for working out which atoms are related to defect.
        """

        self._defining_except_found = bool

    @property
    def e2_defining(self):
        """
            execpt2_defining(dict)     : Record of all subdirectories in which needed files for working out which
                                         atoms are related to defect were missing.
        """

        return self._e2_defining

    @e2_defining.setter
    def e2_defining(self, dict):
        """
            dict(dict)                 : Updated version of dictionary to replace with.
        """

        self._e2_defining = dict

    @property
    def i_defining(self):
        """
            Inter_defining(dict)       : Record of subdirectories to have their inital xyz file checked for in other
                                         subdirectories of the same project name and charge state.
        """

        return self._i_define

    @i_defining.setter
    def i_defining(self, dict):
        """
            dict(dict)                 : Updated version of dictionary to replace with.
        """

        self._i_define = dict

class CaS_Settings:

    def __init__(self):
        self._nn_and_def, self._cont_bdr = None, None
        self._bader_missing, self._bader_break, self._dirs_missing_bader = None, None, {"perfect": [], "defect": []}
        # self._nn_and_def_except_found, self._e2n_a_d, self._i_nad = None, {"perfect": [], "defect": []}, {"defect": []}

    @property
    def nn_and_def(self):
        return self._nn_and_def

    @nn_and_def.setter
    def nn_and_def(self, bool):
        self._nn_and_def = bool

    @property
    def cont_bdr(self):
        return self._cont_bdr

    @cont_bdr.setter
    def cont_bdr(self, bool):
        self._cont_bdr = bool

    @property
    def bader_missing(self):
        """
            badermissing(None->True)     : Indication of whether defect subdirectories have been found to be missing
                                           either CP2K output and/or intermediary files needed for bader charge analysis.
        """

        return self._bader_missing

    @bader_missing.setter
    def bader_missing(self, bool):
        """
            bool(bool)                   : To be turned True when a defect subdirectory is found to be missing
                                           file(s) needed for bader charge analysis of the calculation.
        """

        self._bader_missing = bool

    @property
    def bader_break(self):
        """
            BaderBreak(None->True)       : Indication of whether bader charge analysis can be performed.
        """

        return self._bader_break

    @bader_break.setter
    def bader_break(self, bool):
        """
            bool(bool)                   : To be turned True when both CP2K output and intermediary file(s) needed for
                                           bader analysis are not found in the defect-free perfect directory.
        """

        self._bader_break = bool

    @property
    def dirs_missing_bader(self):
        """
            dirsmissingbader(dict)       : Record of all subdirectories in which needed files for bader analysis
                                           were missing. {type: [[name, run, charge, shortened path],...], type:[...] }.
        """

        return self._dirs_missing_bader

    @dirs_missing_bader.setter
    def dirs_missing_bader(self, dict):
        """
            dict(dict)                   : Updated version of dictionary to replace with.
        """

        self._dirs_missing_bader = dict

class End:
    def __init__(self):
        self._triggered = None

    @property
    def triggered(self):
        return self._triggered

    @triggered.setter
    def triggered(self, bool):
        self._triggered = bool

class Dirs:
    """
        All class properties needed for searching for specific files needed for particular result processing methods.
    """
    def __init__(self):
        self._address_book, self._dir_calc_keys = {"perfect": dict(), "defect": dict()}, {"perfect": [], "defect": []}
        self._executables_address =  None
    @property
    def address_book(self):
        """
            address_book(dict)           : Dictionary of os.path strs perfect and defect directory paths, and
                                           os.path strs to CP2K output and intermediary files in these directories.
        """
        return self._address_book
    @address_book.setter
    def address_book(self, dict):
        """
            dict(dict)                   : Updated version of dictionary to replace with
        """
        self._address_book = dict
    @property
    def dir_calc_keys(self):
        """
            dir_calc_keys(dict)          : Dictionary of lists of nested dictionary keys specific to each
                                           specific nested dictionary entry within the Address_book dictionary.
        """
        return self._dir_calc_keys
    @dir_calc_keys.setter
    def dir_calc_keys(self, dict):
        """
            dict(dict)                   : Updated version of dictionary to replace with.
        """
        self._dir_calc_keys = dict
    @property
    def executables_address(self):
        """
            executables_address(os.path) : File path for 'Executables' directory in the CASORP package for execution
                                           of unix executable files needed for results processing method completion.
        """
        return self._executables_address
    @executables_address.setter
    def executables_address(self, string):
        """
             string(str)                 : File path of directory holding all unix executable files used by CASORP
        """
        self._executables_address = string

class Geo_Settings:
    """
            {perfect : {name1 : {run1: {charge1: {extension1: {'nns' : [{'ai': {'0': nn_a1, '1': nn_a2, '2':nn_a3, '3':nn_a4},
                                                          {'a2': ...}, ...]
                                                            },
                                                            {'bonds': ['a - nn_a', ...]},
                                                            {'lat paras': [A, B, C]}, ...
                                                 }, {extension2: ...}, ...
                                        }, {charge2 : ...}, ,,,
                                }, {run2 : ...}, ...
                        }, {name2 : ,,,}, ...
            }, {defect: ...}
    """
    def __init__(self):
        self._structural_data = {"perfect": dict(), "defect": dict()}
        self._perf_Lxyz = ''
    @property
    def struc_data(self):
        return self._structural_data
    @struc_data.setter
    def struc_data(self, dict):
        self._structural_data = dict
    @property
    def perf_lxyz(self):
        return self._perf_Lxyz
    @perf_lxyz.setter
    def perf_lxyz(self, str):
        self._perf_Lxyz = str

class ProcessCntrls:
    """
        Saving the results processing options given by user in commandline input.
    """
    def __init__(self):
        self._processwants, self._setup, self._processresults = None, None, {"perfect": dict(), "defect": dict()}
    @property
    def processwants(self):
        """
            ProcessWants(None -> list) : Saved list of result processing
                                         methods wanted by user.
        """
        return self._processwants
    @processwants.setter
    def processwants(self, list):
        """
            list(list)                 : List of result processing options given by user in
                                         commandline input.
        """
        self._processwants = list
    @property
    def setup(self):
        """
            setup(list)                : List of placeholder item values for pairing and creation
                                         of inner nested dictionary of ProcessResults.
        """
        return [f"results for {item}" for item in self.processwants]

    @property
    def processresults(self):
        """
            processresults(dict)       : Dictionary of fully calculated result products from each defect
                                         subdirectory for each result processing method wanted by user.
        """
        return self._processresults
    @processresults.setter
    def processresults(self, dict):
        """
            dict(dict)                 : Updated version of dictionary to replace with
        """
        self._processresults = dict

class Pool_Args:
    def __init__(self):
        self._CaSGeoRecver, self._CaSGeoSender = None, None
    @property
    def CaSGeoRecver(self):
        return self._CaSGeoRecver
    @CaSGeoRecver.setter
    def CaSGeoRecver(self, mp_Connection):
        self._CaSGeoRecver = mp_Connection
    @property
    def CaSGeoSender(self):
        return self._CaSGeoSender
    @CaSGeoSender.setter
    def CaSGeoSender(self, mp_Connection):
        self._CaSGeoSender = mp_Connection


class SaveProperties:
    """
        Saving file path of file and the corresponding specific dictionary of the variable to be extracted.
    """
    def __init__(self):
        self._os_path, self._varitem = "", {}
    @property
    def os_path(self):
        """
            os_path(os.path) : Saved full directory path to file variable to be extracted from.
        """
        return self._os_path
    @os_path.setter
    def os_path(self, str):
        """
            str(str)         : Name of file variable to be extracted from.
        """
        self._os_path = str
    @property
    def varitem(self):
        """
            varitem(dict)    : Specific variable nested var_fo dictionary for file type being searched.
        """
        return self._varitem
    @varitem.setter
    def varitem(self, dict):
        """
            dict(dict)       : Updated version of dictionary to replace with
        """
        self._varitem = dict

class SharableDicts:
    def __init__(self):
        self._smd = SharedMemoryDict("CASORP", size=1024)
    @property
    def smd(self):
        return self._smd

class TESTING:
    def __init__(self):
        self._in_progress = False
    @property
    def in_progress(self):
        return self._in_progress
    @in_progress.setter
    def in_progress(self, bool):
        self._in_progress = bool

class UArg:
    """
        Saving commandline arguments from user upon execution of MAIN.py as class definitions.
    """
    def __init__(self):
        self._cwd, self._perfd, self._defd, self._cptd, self._subd, self._fdsd= '', '', '', '', [], {}
        self._expt, self._only = False, False
    @property
    def cwd(self):
        """

        """
        return self._cwd
    @cwd.setter
    def cwd(self, string):
        """
            string(str)       : Name of sudo current working directory.
        """
        self._cwd = string
    @property
    def perfd(self):
        """
            perfd(os.path)    : Saved full directory path to directory user named as the
                                directory of CP2K output files for the perfect structure.
        """
        return self._perfd
    @perfd.setter
    def perfd(self, string):
        """
            string(str)       : Name of directory containing CP2K output files for the perfect
                                defect-free material structure given by user.
        """
        self._perfd = string
    @property
    def defd(self):
        """
            defd(os.path)     : Saved full directory path to directory user named as the parent
                                directory of particular type of defect studied within material.
        """
        return self._defd
    @defd.setter
    def defd(self, string):
        """
            string(str)       : Name of parent directory of particular  type of defect studied
                                within material given by user.
        """
        self._defd = string
    @property
    def cptd(self):
        """
            cptd(os.path)     : Saved full directory path to directory user named as the parent
                                directory for individual calc reference chem pots.
        """
        return self._cptd
    @cptd.setter
    def cptd(self, string):
        """
            string(str)       : Name of parent directory of subdirectories for individual calc
                                reference chem pots for host and/or impurity elements in material.
        """
        self._cptd = string
    @property
    def subd(self):
        """
            subd(list)        : Saved list of subdirectory names given by user at the end of the
                                commandline arguments after keyword only or except.
        """
        return self._subd
    @subd.setter
    def subd(self, list):
        """
            list(list)        : List of subdirectory names user wants to be excluded from data processing.
        """
        self._subd = list
    @property
    def fdsd(self):
        """
            fdsd(dict)        : Dictionary populated if 'only' given for commandline args[4]. Key of each
                                named subdirectory in args[5:] with value False until found in dir tree.
        """
        if self._fdsd == {}:
            for sub in self.subd:
                self._fdsd[str(sub)] = False
        else:
            self._fdsd = self._fdsd
        return self._fdsd
    @fdsd.setter
    def fdsd(self, dict):
        """
            dict(dict)        : Updated version of dictionary to replace with.
        """
        self._fdsd = dict
    @property
    def expt(self):
        """
            expt(boolean)     : True if user wants all defect subdirectories except ones stated after
                                in commandline arguments to be included in the data processing.
        """
        return True if self.subd != [] and self.only is False else False
    @property
    def only(self):
        """
            only(boolean)     : True if user wants only data processing of data within subdirectories
                                stated after in command line argument.
        """
        return self._only
    @only.setter
    def only(self, YorN):
        """
            list(list)        : List of subdirectory names user only wants to be data processed.
        """
        self._only = YorN

class Userwants:
    """
        Saving commandline inputs given by user related to their analysis and display needs.
    """

    def __init__(self):
        self._analysiswants, self._displaywants, self._append, self._overwrite = None, None, None, None

    @property
    def analysiswants(self):
        """
            analysiswants(None -> boolean) : True if user responds 'Y' to question 2 and wants results analysis.
        """

        return self._analysiswants

    @analysiswants.setter
    def analysiswants(self, YorN):
        """
            YorN(str)                      : String of either 'Y' or 'N' corresponding to whether user
                                             wants analysis to be performed.
        """

        self._analysiswants = YorN

    @property
    def displaywants(self):
        """
            displaywants(None -> boolean)  : True if user responds 'Y' to Follow-up question 1 and wants
                                             to display results via GUI.
        """

        return self._displaywants

    @displaywants.setter
    def displaywants(self, YorN):
        """
            YorN(str)                      : String of either 'Y' or 'N' corresponding to whether user
                                             wants results to be displayed in a GUI window.
        """

        self._displaywants = YorN

    @property
    def append(self):
        """
            overwrite(None -> boolean)     : True if user responds 'Y' to Follow-up question 2.
        """

        return [item for key, item in boolconvtr.items() if item is not self.overwrite][0] if self.overwrite is not \
                                                                                              None else None

    @property
    def overwrite(self):
        """
            append(None -> boolean)        : True if user responds 'N' to Follow-up question 2.
        """

        return self._overwrite

    @overwrite.setter
    def overwrite(self, YorN):
        """
            yes(str)                       : String of either 'Y' or 'N' corresponding to whether user
                                             wants to append to the file processed_data.txt.
        """

        self._overwrite = YorN





