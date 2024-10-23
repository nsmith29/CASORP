#!/usr/bin/env python3

# import json
import asyncio
import multiprocessing as mp

import sys
from shared_memory_dict import SharedMemoryDict
import Core
from Core.DictsAndLists import boolconvtr, args4pool
from Core.Iterables import GetDirs_iterator

__all__ = {'add2addressbook', 'CaS_Settings', 'create_nested_dict', 'CreateSharableDicts', 'Ctl_Settings', 'Dirs',
           'End', 'End_Error', 'Geo_Settings', 'GetDirs', 'proxyfunction', 'ProcessCntrls', 'Redistribute',
           'ResultsUpdate', 'SharableDicts', 'sharable_vars', 'TESTING', 'savekeys', 'UArg',
           'Userwants'}

## functions

def sort_charges(list):
    pos, neg, zero = [], [], []
    if list == []:
        return list
    for indx, i_ in enumerate(list):
        if '+' in str(i_[2]):
            pos.append(i_)
        elif '-' in str(i_[2]):
            neg.append(i_)
        else:
            zero.append(i_)
    for lst in [pos, neg]:
        sorted(lst)
    rtn = pos + zero + neg
    return rtn

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
                inner = sort_charges([item for item in d2[keys[0]] if keys[1] in item and keys[2] in item])
                if len(inner) > 0:
                    indx = sorted([d2[keys[0]].index(item) for item in inner])
                    for idx, item in zip(indx, inner):
                        d2[keys[0]].pop(idx)
                        d2[keys[0]].insert(idx, item)
                    d2[keys[0]].insert((d2[keys[0]].index(inner[-1]) + 1), keys[1:])
                else:
                    d2[keys[0]].append(keys[1:])
            if name:
                CreateSharableDicts(name[1], d2)
        return d1, d2
    return wrapper

def add2addressbook(keys, subkeys, path, d):
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
    assert isinstance(paths, list), "path must be a list [usually of os.path() file path strs]"
    assert isinstance(d, dict), f"d must be a dictionary which can be populated with keys, subkeys, and paths, type of d is {type(d)}"
    assert keys[0] in d.keys(), "First str item in keys must be a key within d"

    d_, ks = {keys[0]: d[keys[0]]}, ''
    if TESTING.in_progress is True:
        print("[C.CD L60] d_ =", d_, "ks =", ks)
    for indx, key in enumerate(keys):
        d__ = eval("d_{}".format(ks))
        if TESTING.in_progress is True:
            print("[C.CD L64] d__ =", d__ )
        if key in eval("d_{}".format(ks)) and key == keys[-1]:
            k_ = [k for k, v in d__.items()][0]
            if TESTING.in_progress is True:
                print("[C.CD L68] k_=", k_)
            for sub, path in zip(subkeys, paths):
                if TESTING.in_progress is True:
                    print("[C.CD L71] sub =", sub, "path =", path)
                if str("{} : {}".format(sub, path)) not in d__[k_]:
                    d__[k_][sub] = path
                    if TESTING.in_progress is True:
                        print("[C.CD L75] d__=", d__, "k_=", k_, "sub", sub, "d__[k_][sub] =", f"{d__}[{k_}][{sub}] =", d__[k_][sub])

        if key not in eval("d_{}".format(ks)):
            if d__ == {}:
                _d = {sub: path for sub, path in zip(subkeys, paths)} if key == keys[-1] else {}
                d__ = {key: _d}
            else:
                d__[key] = {}
                if key == keys[-1]:
                    for sub, path in zip(subkeys, paths):
                        d__[key][sub] = path
            if TESTING.in_progress is True:
                print('[c.CD L87] d__ = ', d__)
            exec(f"d_{ks} = d__ ")
            if TESTING.in_progress is True:
                print("[C.CD L90] d_{ks} =", f"d_{ks} =", eval("d_{}".format(ks)))

        ks = ks + str("['{}']".format(key)) if type(key) == str else ks + str("[{}]".format(key))
        if TESTING.in_progress is True:
            print("[C.CD L94] ks =", ks)
        d.update({keys[0]: d_[keys[0]]})
        if TESTING.in_progress is True:
            print("[C.CD L97] d =", d)

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
    async def wrapper(type_, **kwargs):
        async for item_ in GetDirs_iterator(Dirs().dir_calc_keys[type_]):
            n, r, c = item_[0], item_[1], item_[2]
            await func(type_, n, r, c, **kwargs)
    return wrapper

# classes

class End_Error:
    def __init__(self, cond, msg):
        if eval("{}".format(cond)) is True:
            return
        try:
            if eval("{}".format(cond)) is False:
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
        self.list = []
        # print(type(list), 'C.CD L131')
        for cond, func in args4pool.items():
            if eval("{}".format(cond)) is True:
                self.list = eval("self.{}(list)".format(func))
        if self.list == []:
            self.list = list
    def create_pipe(self, list_):
        con1, con2 = mp.Pipe()
        list_[list_.index("charges and spins")] = ("charges and spins", con1)
        list_[list_.index("geometry")] = ("geometry", con2)
        return list_
    def Return(self):
        return self.list

class Redistribute:
    def __init__(self, Key = None):
        if Key is None:
            for key in SharableDicts().smd.keys():
                exec(f'{key} = SharableDicts().smd[key]')
            self.populate_processresults('perfect')
            self.populate_processresults('defect')
        else:
            exec(f'{Key} = SharableDicts().smd[Key]')
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

class NewProperty(object):
    def __init__(self, function):
        self.function = function
        self.name = function.__name__
    def __get__(self, obj, type=None) -> object:
        obj.__dict__[self.name] = self.function(obj)
        return obj.__dict__[self.name]


class Ctl_Settings:
    @NewProperty
    def defining_except_found(self, bool=None):
        """
            defining_exept_found(bool) : Indication of whether defect subdirectories have been found to be missing
                                         files needed for working out which atoms are related to defect.
        """
        return bool
    @NewProperty
    def e2_defining(self, dict_=None):
        """
            execpt2_defining(dict)     : Record of all subdirectories in which needed files for working out which
                                         atoms are related to defect were missing.
        """
        if dict_ is None:
            dct = {"perfect": [], "defect": []}
        return dct
    @NewProperty
    def i_defining(self, dict_=None):
        """
            Inter_defining(dict)       : Record of subdirectories to have their inital xyz file checked for in other
                                         subdirectories of the same project name and charge state.
        """
        if dict_ is None:
            dct = {"defect": []}
        return dct

class CaS_Settings:
    @NewProperty
    def nn_and_def(self, bool=None):
        return bool
    @NewProperty
    def cont_bdr(self, bool=None):
        return bool
    @NewProperty
    def bader_missing(self, bool=None):
        """
            badermissing(None->True)     : Indication of whether defect subdirectories have been found to be missing
                                           either CP2K output and/or intermediary files needed for bader charge analysis.
        """
        return bool
    @NewProperty
    def bader_break(self, bool=None):
        """
            BaderBreak(None->True)       : Indication of whether bader charge analysis can be performed.
        """
        return bool
    @NewProperty
    def dirs_missing_bader(self, dict_=None):
        """
            dirsmissingbader(dict)       : Record of all subdirectories in which needed files for bader analysis
                                           were missing. {type: [[name, run, charge, shortened path],...], type:[...] }.
        """
        if dict_ is None:
            dct = {"perfect": [], "defect": []}
        return dct

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
    @NewProperty
    def address_book(self, dict_=None):
        """
            address_book(dict)           : Dictionary of os.path strs perfect and defect directory paths, and
                                           os.path strs to CP2K output and intermediary files in these directories.
        """
        if dict_ is None:
            dct = {"perfect": dict(), "defect": dict()}
        return dct
    @NewProperty
    def dir_calc_keys(self, dict_=None):
        """
            dir_calc_keys(dict)          : Dictionary of lists of nested dictionary keys specific to each
                                           specific nested dictionary entry within the Address_book dictionary.
        """
        if dict_ is None:
            dct = {"perfect": [], "defect": []}
        return dct
    @NewProperty
    def executables_address(self, string=None):
        """
            executables_address(os.path) : File path for 'Executables' directory in the CASORP package for execution
                                           of unix executable files needed for results processing method completion.
        """
        return string

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
    @NewProperty
    def struc_data(self, dict_=None):
        if dict_ is None:
            dct = {"perfect": dict(), "defect": dict()}
        return dct
    @NewProperty
    def perf_lxyz(self, string=None):
        return string

class ProcessCntrls:
    """
        Saving the results processing options given by user in commandline input.
    """
    @NewProperty
    def processwants(self, list_=None):
        """
            ProcessWants(None -> list) : Saved list of result processing
                                         methods wanted by user.
        """
        return list_ #self._processwants
    @property
    def setup(self):
        """
            setup(list)                : List of placeholder item values for pairing and creation
                                         of inner nested dictionary of ProcessResults.
        """
        return [f"results for {item}" for item in self.processwants]
    @NewProperty
    def processresults(self, dict_=None):
        """
            processresults(dict)       : Dictionary of fully calculated result products from each defect
                                         subdirectory for each result processing method wanted by user.
        """
        if dict_ is None:
            dct = {"perfect": dict(), "defect": dict()}
        return dct

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
    @NewProperty
    def cwd(self, string=''):
        """

        """
        return string
    @NewProperty
    def perfd(self, string = ''):
        """
            perfd(os.path)    : Saved full directory path to directory user named as the
                                directory of CP2K output files for the perfect structure.
        """
        return string
    @NewProperty
    def defd(self, string = ''):
        """
            defd(os.path)     : Saved full directory path to directory user named as the parent
                                directory of particular type of defect studied within material.
        """
        return string
    @NewProperty
    def cptd(self, string= ''):
        """
            cptd(os.path)     : Saved full directory path to directory user named as the parent
                                directory for individual calc reference chem pots.
        """
        return string
    @NewProperty
    def subd(self, list_=None):
        """
            subd(list)        : Saved list of subdirectory names given by user at the end of the
                                commandline arguments after keyword only or except.
        """
        if list_ is None:
            list_ = []
        return list_
    @NewProperty
    def fdsd(self, dict_=None):
        """
            fdsd(dict)        : Dictionary populated if 'only' given for commandline args[4]. Key of each
                                named subdirectory in args[5:] with value False until found in dir tree.
        """
        if dict_ is None:
            dict_ = {}
            for sub in self.subd:
                dict_[str(sub)] = False
        return dict_
    @property
    def expt(self):
        """
            expt(boolean)     : True if user wants all defect subdirectories except ones stated after
                                in commandline arguments to be included in the data processing.
        """
        return True if self.subd != [] and self.only is False else False
    @NewProperty
    def only(self, YorN=False):
        """
            only(boolean)     : True if user wants only data processing of data within subdirectories
                                stated after in command line argument.
        """
        return YorN

class Userwants:
    """
        Saving commandline inputs given by user related to their analysis and display needs.
    """
    def __init__(self):
        self._analysiswants, self._displaywants, self._append, self._overwrite = None, None, None, None
    @NewProperty
    def analysiswants(self, YorN=None):
        """
            analysiswants(None -> boolean) : True if user responds 'Y' to question 2 and wants results analysis.
        """
        return YorN
    @NewProperty
    def displaywants(self, YorN=None):
        """
            displaywants(None -> boolean)  : True if user responds 'Y' to Follow-up question 1 and wants
                                             to display results via GUI.
        """
        return YorN
    @property
    def append(self):
        """
            overwrite(None -> boolean)     : True if user responds 'Y' to Follow-up question 2.
        """
        return [item for key, item in boolconvtr.items() if item is not self.overwrite][0] if self.overwrite is not \
                                                                                              None else None
    @NewProperty
    def overwrite(self, YorN=None):
        """
            append(None -> boolean)        : True if user responds 'N' to Follow-up question 2.
        """
        return YorN




