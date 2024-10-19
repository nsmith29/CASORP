#!/usr/bin/env python3

import aiofiles
import asyncio
from Core.DictsAndLists import inp_var_fo, inp_want, log_var_fo, log_want
from Core.Iterables import Lines_iterator
from DataCollection.Log import find_a, find_at, find_charge, find_energy, find_gap, find_kind, find_name, find_pop1, \
    find_pop2, find_run, find_version
from DataCollection.Inp import xyz


__all__ = {'Update', 'inline', 'AsyncIterateManager', 'read_file_async', 'iterate'}

async def read_file_async(filepath):
    """
        file lines fetcher
    """
    async with aiofiles.open(filepath, 'r') as file:
        return await file.read()

async def iterate(os_path, varitem):
    # fetch file lines from os_path file
    lines = await read_file_async(os_path)
    lines = lines.split('\n')
    # Handling of very large files when required information for variable 'via' function is a single line from file
    if len(lines) > 100000 and not len(varitem['kwargs']) > 1:
        ln = [ln for ln in lines if ln.startswith(varitem["locate"])][-1]
        indx = lines.index(ln)
        # preconvertion of variable kwargs item value into a dictionary to be feed as **kwargs to variables 'via' function.
        kwargs = eval("f'{}'".format(*varitem['kwargs']))
        return await eval("{}".format(varitem["via"]))(ln, **eval(f'dict({kwargs})'))
    else:
        lines_ = lines[::-1] if varitem.get("reverse") is True else lines
        # manually call context manager AsyncIterateManager so that information can be returned from the __aenter__ method.
        manager = AsyncIterateManager(varitem, lines_)
        ln, indx = await manager.__aenter__()
        # preconvertion of variable kwargs item value into a dictionary to be feed as **kwargs to variables 'via' function.
        kwargs = str()
        for item in varitem['kwargs']:
            kwargs = str(kwargs + eval("f'{}, '".format(item)))
        return await eval("{}".format(varitem["via"]))(ln, **eval(f'dict({kwargs})'))

async def inline(ln, loc):
    """
        decision tree of where loc str is within certain ln.
    """
    # handling of variables requiring multiple lines
    if type(loc) == list:
        # signal for atom kind variable
        if len(loc) == 1 and loc[0] in ln:
            return None
        # handling of xyz variable from inp file
        elif len(loc) == 3 and loc[0] in ln:
            # print('correctly found here')
            return '0'
        elif len(loc) == 3 and loc[1] in ln:
            # print("correctly found here as well")
            return '1'
        # signal 1 for charge pop variable
        elif len(loc) == 2 and loc[0] in ln:
            return None
        # signal 2 for charge pop variable
        elif len(loc) == 2 and  loc[1] in ln:
                    return [True, None]
        else:
            return False
    # variable requiring single ln
    elif loc in ln:
        return True
    else:
        return False

class AsyncIterateManager:
    """
        Async context manager acting as a iteration controller.
    """
    def __init__(self, varitem, lines):
        self.varitem = varitem
        self.lines = lines
        self.list = []
    async def __aenter__(self):
        async for item_ in Lines_iterator(self.lines):
            item, ln = item_[0], item_[1]
            bool_ = await inline(ln, self.varitem['locate'])
            # print(item, ln, bool_)
            if bool_ == None:
                # handling of multiple lines requiring extracting from log file for atom kinds.
                if len(self.varitem['locate']) == 1:
                    if self.list == []:
                        self.list.append([int(var[1]) for var in enumerate(ln.split()) if var[0] in [6]][0])
                    elif len(self.list) == self.list[0]:
                        self.list.append(ln)
                        self.list.pop(0)
                        # returning of required list of lines containing information regarding atom kinds.
                        return self.list, None
                    else:
                        self.list.append(ln)
                # handling of multiple lines requiring extracting from log file for charge populations.
                else:
                    if self.varitem["num"] == None:
                        self.list.append([var[1] for var in enumerate(self.lines[item - self.varitem["n"]].split()) if var[0] in [0]][0])
                    else:
                        self.list = self.varitem["num"]
            # returning of required information related to charge populations.
            elif bool_ == [True, None]:
                return self.list, item
            # returning of file line and index required for particular variable being collected
            elif bool_ == '0':
                self.list.append(bool_)
                return ln, self.list
            elif bool_ == '1':
                # print('picked up that bool_ = 1')
                self.list.extend([item, bool_])
                return ln, self.list
            elif bool_ == True:
                return ln, item
    async def __aexit__(self,*args):
        pass

class Update:
    """
        Updating varitem dictionary during the mp.process.
    """
    def __init__(self2, varitem):
        self2.varit = varitem
    # def found(self2):
    #     """
    #         Updating the item value of the "found" key of a variable from False to None.
    #     """
    #
    #     self2.varit.update({"found": None})
    def extra(self2, list):
        """
            Updating with intermediate data collected during searching the log file.
        """
        for i in range(0, int(len(list) / 2)):
            self2.varit.update({list[int(2 * i)]: list[int(2 * i + 1)]})
    # def switch(self2):
    #     """
    #        Switch item values so alternative str is started to be looked for in file.
    #     """
    #
    #     rnge = int(len(self2.varit["switch"]) / 2)
    #     keys, values = [self2.varit["switch"][i] for i in range(0, rnge)], [self2.varit[self2.varit["switch"][rnge + i]]
    #                                                                        for i in range(0, rnge)]
    #     [self2.varit.update({key : value}) for key, value in zip(keys, values)]
    #
    #     self2.varit.update({"swapped": True})
    #
    # def reset(self2):
    #     """
    #         Resetting varitem dictionary to defaults.
    #     """
    #
    #     self2.varit.update({"found": False})
    #
    #     if "reset" in self2.varit and self2.varit["reset"]:
    #         [self2.varit.update({self2.varit["reset"][int(2 * i)]: self2.varit["reset"][2 * i + 1]}) for i in
    #          range(0, int(len(self2.varit["reset"]) / 2))]
    #
    #     elif "swapped" in self2.varit and self2.varit["swapped"] is True:
    #         self2.switch()
    #         self2.varit.update({"swapped": False})








