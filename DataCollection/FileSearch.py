#!/usr/bin/env python3

import asyncio
from asgiref.sync import sync_to_async
import numpy as np
import os
import subprocess

from Core.CentralDefinitions import Dirs, create_nested_dict, End_Error, TESTING, UArg, add2addressbook
from Core.DictsAndLists import  files4res, finding_conditions, functions, inp_want, inp_var_fo, log_want, log_var_fo,\
    multiplefiles4extension, restrictions
from Core.Iterables import async_pairing_iterator, toFromFiles_iterator, getDirs_iterator, FileExt_iterator
from Core.Messages import ErrMessages, Global_lock
from DataCollection.FromFile import iterate

__all__ = {'Finding', 'verify_only', 'DirsAndLogs', 'Cataloging', 'Entry4FromFiles', 'MakingIntermediaryFiles'}

class Finding:
    """
        Finding specific files needed for particular result processing methods inside directories of CP2K output files.
    """
    def __init__(self, path, extension, async_=False):
        self.split_path, self.extension, self.layer, self.walk = path.split('/'), extension, 0, os.walk(path)
        self.dirpaths, self.filepaths, self.fnd = [], [], None
        if async_ is True:
            self.dir_tree_transversing()
    def set_vars(self, bool_, cond_ = None):
        if bool_ == True:
            met, layer_met, meet_list, to_meet, indx, num_met, fnd_list = True, 0, None, None, None, None, None
            start, not_ = "", []
        elif bool_ == False:
            met, layer_met, num_met = False, 0, 0
            _, meet_list =((''.join(cond_.split(")"))).split("(")[0]), eval(((''.join(cond_.split(")"))).split("(")[2]))
            not_ = meet_list if 'not' in _ else []
            to_meet, indx = int(len(meet_list)) if 'not' not in _ else None, None
            num_met, fnd_list = 0 if to_meet > 1 else None, np.empty(to_meet, dtype = bool)  if 'not' not in _ and \
                                                                                                to_meet > 1 else None
        return met, layer_met,  not_, num_met, fnd_list, meet_list, to_meet, indx
    def check_num_of_filepaths(self):
        noted_dirpath = ''
        for dir_ in self.dirpaths:
            if dir_ != noted_dirpath:
                noted_dirpath = dir_
            else:
                assert self.extension in multiplefiles4extension, \
                    f"{ErrMessages.FileSearch_LookupError(self.extension,noted_dirpath)}"
    def dir_tree_transversing(self, cond="", q_=None):
        """
            Searching for file within the os.walk() directory tree of subdirectory path.
        """
        met, layer_met, not_, num_met, fnd_list, meet_list, to_meet, indx, = self.set_vars(True) if cond == "" else \
            self.set_vars(False, cond)
        if TESTING.in_progress is True:
            print('met =', met, 'extension =', self.extension, '[DC.FS L67]')
        layer = {0: {"found": self.split_path[-1], "transversed": [] }}
        for (path_, dirs_, files_) in self.walk:
            if TESTING.in_progress is True:
                print('met = ', met, "find =", self.fnd, "layer =", self.layer, "[DC.FS L72]")
            if [i for i in path_.split('/') if i in not_]:
                continue
            if self.fnd is True and met is False or self.fnd is False and met is False:  # stops finding directories if fnd is true and met is false
                if type(to_meet) == int and type(num_met) == int:
                    if num_met != to_meet:
                        num_met += 1
                        fnd_list[indx] = self.fnd
                        layer_met, self.fnd = 0, None
                    elif num_met == to_meet:
                        break
                else:
                    if TESTING.in_progress is True:
                        print("should be breaking out of method loop [DC.FS L86]")
                    break
            self.layer = len(str(path_).split('/')) - len(self.split_path)
            keys_, met = [key for key in layer.keys() if
                          key > self.layer], False if self.layer != 0 and layer_met > self.layer - 1 else met # met reset to False if going back in layer num is less than layer num
            [layer.pop(key_) for key_ in keys_]
            layer[int(self.layer + 1)] = {"found": dirs_, "transversed": []} if int(
                self.layer + 1) not in layer.keys() else layer[int(self.layer + 1)]
            if not dirs_ and not files_:
                all_ = [layer[key]["transversed"] == layer[key]["found"] for key in layer.keys()]
                if False not in all_:
                    self.fnd = False
                    met = False
                    break
            elif met is False:
                if eval(cond):
                    met, layer_met = True, self.layer # set to true when first of directories listed in condition match current path
                    indx =[in_ for in_, i in enumerate(meet_list) if i.endswith(path_.split('/')[-1])][0] if to_meet \
                        else None
            elif met is True:
                for file_ in files_:
                    if file_.endswith(str(self.extension)) and not path_.endswith(".ipynb_checkpoints"):
                        self.dirpaths.append(path_)
                        self.filepaths.append(os.path.join(path_, file_))
                        self.fnd = True # found all directories and logs for that particular named directory
            end = str(path_).split('/')[-1]
            [layer[self.layer]["transversed"].append(end_) for end_ in [end] if
             end_ in layer[self.layer]["found"] and end_ not in layer[self.layer]["transversed"]]
        if to_meet:
            self.fnd = fnd_list
        else:
            self.fnd = False if self.fnd == None else self.fnd
        if len(self.filepaths) > 1:
            self.check_num_of_filepaths()
    def returning(self):
        return self.fnd, self.filepaths

class verify_only:
    """
        Testing the existence of all subdirectories named by user in command line arguments after arg[4] = only.
    """

    def __init__(self, func):
        self._func = func

    def __call__(self, self2, c_=None, q_=None):
        # t = time.time()
        dirs = self._func(self2)
        if c_ != None:
            if UArg().only is True:
                copy = UArg().fdsd.copy()
                for dir_ in dirs:
                    for key in copy.keys():
                        [copy.update({key: True}) if key in dir_.split('/') and copy[key] != True else copy]
                values, keys,  = [value for value in copy.values()], [key for key in copy.keys()]
                if True not in values:
                    with c_:
                        q_.put('end')
                        c_.notify()
                    End_Error(True in tuple([value for value in copy.values()]), ErrMessages.FileSearch_FileNotFoundError1(keys, Global_lock().lock))
                try:
                    if False in copy.values():
                        raise FileNotFoundError
                except FileNotFoundError:
                    ErrMessages.FileSearch_FileNotFoundError2([key for key, value in copy.items() if value is False], Global_lock().lock) # print("one of directories couldn't be found!")
                else:
                    UArg.fdsd = copy
            with c_:
                # print('pass [DC.FS L160]')
                q_.put('start')
                c_.notify()
        return dirs

class DirsAndLogs(Finding):
    """
        Searching for individual subdirectories holding CP2K output files via finding .log files.
    """
    def __init__(self, path, extension, type_):
        super().__init__(path, extension)
        if type_ == "defect":
            self.condition = self.conditional()
        else:
            self.condition = ""
    def conditional(self):
        """
            Stating conditions to be met for any restrictions [only/except used for commandline arg[4]] set by user.
        """
        return finding_conditions.get(str("[{}][{}]".format(UArg().expt, UArg().only)))
    @verify_only
    def dir_tree_transversing(self):
        """
            Overriding .dir_tree_transversing to search directory tree with conditions for gaining the correct subdirectories applied.
        """
        super().dir_tree_transversing(self.condition)
        return self.dirpaths

class Cataloging(DirsAndLogs):
    """
        Recording down every subdirectories with CP2K data to be included in programme execution.
    """
    def __init__(self, path, type_, c_=None, q_=None, t=None):
        # print(type_, 'c_=', c_, 'q_=', q_, '[DC.FS L206]')
        self.type_ = type_
        super().__init__(path, ".log", type_)
        super().dir_tree_transversing(self, c_=c_, q_=q_) if c_ != None else super().dir_tree_transversing(self)
        asyncio.run(self.pairing())
    async def pairing(self):
        """
            Populating dictionaries with corresponding directory paths and file paths and data to specify each individual calculation.
        """
        async for item in async_pairing_iterator(Entry4FromFiles, self.filepaths, self.dirpaths):
            outer_keys, inner_keys, inner_values = item
            outer_keys.insert(0, self.type_)
            Dirs.address_book, Dirs.dir_calc_keys = create_nested_dict(outer_keys, inner_keys, inner_values,
                                                                       Dirs().address_book, Dirs().dir_calc_keys,
                                                                   ["Dirs.address_book", "Dirs.dir_calc_keys"])

async def Entry4FromFiles(path, file, keywrd):
    """
        Passing on data for variable extraction/collection from files
    """
    want, var = eval("{}_want[keywrd]".format(file)), eval("{}_var_fo".format(file))
    v2rtn = [iterate(path, var.get(item)) async for item in toFromFiles_iterator(want)]
    return await asyncio.gather(*v2rtn)

def CatalogueFinding(func):
    async def wrapper(self2, type_, fl_exts, section, **kwargs):
        if "ignore" in kwargs.keys() and self2.keywrd in restrictions.keys() or self2.keywrd not in restrictions.keys():
            cats = Dirs().dir_calc_keys.copy()
        else:
            cats = {type_: [entry for entry in Dirs().dir_calc_keys[type_] if eval(restrictions[self2.keywrd])]}
        book, errflaggd, Q = Dirs().address_book.copy(), fl_exts, asyncio.Queue()
        async for item_ in getDirs_iterator(cats[type_]):
            n, r, c, keylst = item_[0], item_[1], item_[2], [type_, item_[0], item_[1], item_[2]]
            Ars = [value for key, value in kwargs.items() if key == 'exchange'] if kwargs else []
            path, keys, flexts = book[type_][n][r][c]["path"], book[type_][n][r][c].keys(), []
            [fl_exts.remove(flext_) for flext_ in fl_exts if flext_ in keys]
            pair, flexts, len_ = [section for i in range(len(fl_exts))], fl_exts.copy(), len(fl_exts),
            while True:
                iterable = FileExt_iterator(flexts)
                async for j in iterable:
                    if TESTING.in_progress is True:
                        print(j, flexts)
                    find = Finding(path, flexts[j], True)
                    fnd, filepaths = await sync_to_async(find.returning)()
                    filepaths = filepaths[0] if len(filepaths) == 1 else filepaths
                    _ = [Ars.insert(0, path) if pair[j] == None else Ars]
                    Ars_ = Ars if pair[j] == None else []
                    rtn = await func(self2, keylst, pair[j], flexts[j], fnd, filepaths, Q, *eval("{}".format(Ars_)))
                    while Q.empty() is False:
                        items = await Q.get()
                        pair.append(items[0])
                        flexts.append(items[1][0])
                        if j + 1 > len_ - 1:
                            await iterable.__anext__(update=flexts)
                    if rtn == 'continue':
                        await iterable.__anext__()
                break
    return wrapper

class Method: # to be inherited by only spins and msin method get.
    def __init__(self, keywrd, subwrd = None):
        self.keywrd, self.subwrd = keywrd, subwrd
        self.res = files4res[keywrd][subwrd] if not subwrd == None else files4res[keywrd]
        self.out, self.int = "cp2k_outputs", "intermediary"
        inner_dict = self.res[self.int] if self.int in self.res.keys() else self.res[self.out]
        self.types, self.flexts_= [key for key, value in inner_dict.items()], [value for key, value in inner_dict.items()]
        self.sect = True if self.int in self.res.keys() else False

class MethodFiles(Method):
    """
        Finding specific files needed for particular result processing methods inside directories of CP2K output files.
    """
    def __init__(self2, keywrd, subwrd=None):
        super().__init__(keywrd, subwrd)
    @CatalogueFinding
    async def assessment_tree(self2, keylst, sect, extension, fnd, flpath, Q, path=None, exchange=None):
        if exchange:
            self2.keywrd, self2.res = exchange[0], files4res[exchange[0]][exchange[1]]
        if sect is True and fnd is not True:
            await self2.option1(keylst, Q)
            rtn = 'pass'
        elif sect is True and fnd is True or sect is False and fnd is True:
            rtn = await self2.option2(keylst, extension, flpath, Q)
        elif sect is None and fnd is True:
            await self2.option3(keylst, path, flpath)
            rtn = 'continue'
        elif sect is None and fnd is False or sect is False and fnd is False:
            await self2.option4(keylst, extension)
            rtn = 'continue'
        return rtn
    async def option1(self2, keylst, Q):
        await Q.put([None, self2.res[self2.out][keylst[0]]])
    async def option2(self2, keylst, extension, flpath, Q):
        Dirs.address_book = add2addressbook(keylst, [extension], [flpath], Dirs().address_book)
        await asyncio.sleep(0.01)
        rtn = 'continue'
        return rtn
    async def option3(self2, keylst, path, flpath):
        Q_ = asyncio.Queue()
        await sync_to_async(MakingIntermediaryFiles(path, flpath, self2.keywrd, Q_))
        while True:
            while Q_.empty() is False:
                new_fls = await Q_.get()
                for ext, nwfl in zip(self2.res[self2.int][keylst[0]], new_fls):
                    Dirs.address_book = add2addressbook(keylst, [ext], [nwfl], Dirs().address_book)
            Q_.task_done()
    async def option4(self2, keylst, extension):
        await asyncio.sleep(0.01)
        try:
            raise FileNotFoundError
        except FileNotFoundError:
            ErrMessages.FileSearch_FileNotFoundError3(self2.keywrd, *keylst[1:], extension)

class MakingIntermediaryFiles:
    """
        Creating intermediary files needed for results processing method from given CP2K output files.

        Definitions:
            functions(dict)                : Dictionary of associated functions within class which should be used to
                                             create the needed intermediary files for each particular result processing
                                             method.

        Inputs:
            dirpath(os.path)               : Directory path to directory of calculation where intermediate file needs
                                             to be created in.

            filepaths(str/list of os.path) : File path(s) of CP2K output file(s) to be used for creating the
                                             intermediary file(s).

            keywrd(str)                    : Keyword corresponding to the result processing method wanting to be
                                             performed by user.

            q(queue.Queue)                 : Optional. When given shared between this class and function
                                             Core.InDirectory.PostAssessmentTree to allow the returning of New file
                                             os.path()(s) for the newly created intermediary file(s) back to
                                             Core.InDirectory.PostAssessmentTree.

        Outputs:
            flns4rtrn(str/list of os.path) : New file os.path()(s) for the newly created intermediary file(s).
    """
    def __init__(self, dirpath, filepaths, keywrd, q = None):
        self.dirpath, self.filepaths = dirpath, filepaths
        # get list of names of all items within directory of self.dirpath at entry to class.
        before = os.listdir(self.dirpath)

        # call associated function for
        eval("self.{}()".format(functions.get(keywrd)))

        after = os.listdir(self.dirpath)
        self.flns4rtrn = [os.path.join(self.dirpath, file) for file in after if file not in before]
        if q:
            q.put(self.flns4rtrn)
    def BaderFileCreation(self):
        """
            Creation of "ACF.dat" (atom coords), "AVF.dat"(bader coords), "BCF.dat"(atomic vol) files for bader analysis.

            self.filepaths should consist of one os.path() for file with file extension '-ELECTRON_DENSITY-1_0.cube.'

        """
        # filename at end of self.filepaths os.path(), cwd when entering function, & os.path() to bader executable.
        baderfile, cwd, BdrExec = self.filepaths.split("/")[-1], os.getcwd(), \
                                  os.path.join(Dirs().executables_address, "bader")
        # change sudo current working directory (cwd) to directory of calculation.
        os.chdir(self.dirpath)
        # acts as: !{bader executable} {filepath}; output created by BdrExec program is suppressed.
        p = subprocess.call([BdrExec, baderfile],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT)
        # change sudo current working directory back to originally set directory in MAIN.py.
        os.chdir(cwd)
    def GeometryLastCreation(self):
        """
            Creation of new xyz file which contains the coordinates of the final geometry optimization step of the calc.

            self.filepaths should consist of one os.path() for file with the file extension of '1.xyz'.
        """
        # derive new file name from previous 1.xyz name with the new extension of L.xyz.
        new_xyz_file = "".join([i for i in self.filepaths][:-5] + ["L.xyz"])
        old_xyz, new_xyz1 = open(self.filepaths, 'r'), open(new_xyz_file, 'w')
        # tot # of atoms will not change between 1st & last optimization step - 1st 1.xyz line gives # of atoms in calc.
        tot_atoms, lines, j, index = [str('     ' + "".join(old_xyz.readline().split())), old_xyz.readlines(),
                                      len(old_xyz.readlines()), len(old_xyz.readlines()) + 1]
        last_itr = False
        # for last geometry step, need to start at bottom of 1.xyz file.
        for line in reversed(lines):
            # moving up the lines from the bottom of 1.xyz file.
            index -= 1
            # last line in 1.xyz file which will be written as first line in new L.xyz file.
            if tot_atoms not in line and index == j and last_itr is False:
                string = line
                new_xyz1.write(string)
                new_xyz1.close()
            # rest of the coordinates of the last geometry step and final line with total atoms.
            elif last_itr is False:
                # 1st line of each geometry optimization step has only tot # of atoms - Last line to write.
                if tot_atoms in line and last_itr is False:
                    # Last_itr needs to be set to True to stop the writing of further lines to L.xyz after final line.
                    last_itr = True
                # opening L.xyz file in read+ mode so that file can be read and written to.
                with open(new_xyz_file, 'r+') as new_xyz2:
                    # create list of all lines within the newly created L.xyz file.
                    lines2 = new_xyz2.readlines()
                    # add next line up from the bottom of 1.xyz to the front of the list of lines in L.xyz.
                    lines2.insert(0, line)
                    new_xyz2.seek(0)
                    # write amended list of L.xyz lines with next line from 1.xyz at the top from top of file down.
                    new_xyz2.writelines(lines2)
    def Return(self):
        return self.flns4rtrn