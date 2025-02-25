#!/usr/bin/env python3

import asyncio

__all__ = {'async_pairing_iterator', 'ListElement_iterator', 'FileExt_iterator', 'Lines_iterator', 'standard_iterator',
           'DefectTypeTestVariables_iterator', 'AdditionalAtoms_iterator'}

class async_pairing_iterator():
    """
        iterator through all filepaths and directories
    """
    def __init__(self, func, filepaths, dirpaths):
        self.func = func
        self.filepaths = filepaths
        self.dirpaths = dirpaths
        self.counter = -1
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.counter >= len(self.filepaths)-1:
            raise StopAsyncIteration
        self.counter +=1
        return await self.func(self.filepaths[self.counter], 'log', 'original'), ["path", "log"], [self.dirpaths[self.counter], self.filepaths[self.counter]] #Entry4FromFiles

class ListElement_iterator(): # ListElement_iterator
    def __init__(self, element):
        self.ele = element
        self.counter = -1
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.counter >= len(self.ele)-1:
            raise StopAsyncIteration
        self.counter +=1
        return self.ele[self.counter]

class FileExt_iterator():
    def __init__(self, flexts):
        self.flexts = flexts
        self.counter = -1
    def __aiter__(self):
        return self
    async def __anext__(self, update=None):
        if update:
            self.flexts = update
            return
        if self.counter > len(self.flexts) - 1:
            raise StopAsyncIteration
        self.counter += 1
        return self.counter

class Lines_iterator():
    """
        index and ln iteratables creator.
    """
    def __init__(self, lines):
        self.lines = lines
        self.lns = [ln for ln in reversed(lines)]
        self.lcounter = -1
        self.counter = 0
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.counter <= -len(self.lines):
            raise StopAsyncIteration
        self.counter -= 1
        self.lcounter += 1
        return [self.counter, self.lns[self.lcounter]]

class standard_iterator():
    def __init__(self, num):
        self.num = num
        self.counter = -1
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.counter >= self.num - 1:
            raise StopAsyncIteration
        self.counter +=1
        return self.counter

class DefectTypeTestVariables_iterator():
    def __init__(self, name, bk_, def_):
        self.bk_, self.def_ = bk_, def_
        self._name_self2_ = name
        self.indxcntr = -1
    def __lt__(self):
        return len(self.bk_) if len(self.bk_)<len(self.def_) else len(self.def_)
    def __len__(self):
        return self.__lt__()
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.indxcntr >= self.__len__() - 1:
            raise StopAsyncIteration
        self.indxcntr += 1
        if self._name_self2_ == 'substitutional' and self.bk_[self.indxcntr] != [] and self.def_[self.indxcntr] != []:
            return [self.bk_[self.indxcntr][0], self.def_[self.indxcntr][0]]
        elif self.bk_[self.indxcntr] != [] and self.def_[self.indxcntr] != []:
            return [[self.indxcntr, self.bk_[self.indxcntr]], [self.indxcntr, self.def_[self.indxcntr]]]

class AdditionalAtoms_iterator():
    def __init__(self, atom, dct):
        self.atom = atom
        self.dct = dct
        self.indxcntr = -1
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.indxcntr >= len(self.dct) - 1:
            raise StopAsyncIteration
        self.indxcntr += 1
        if str(self.atom) in [key for key in self.dct[self.indxcntr].keys()][0]:
            return [key for key in self.dct[self.indxcntr].keys()][0]
        else:
            return await self.__anext__()

class GroupLstDefSites_iterator():
    def __init__(self, dct):
        self.indxcntr = -1
        self.dct = dct
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.indxcntr >= len(self.dct) - 1:
            raise StopAsyncIteration
        self.indxcntr +=1
        return [self.indxcntr, self.dct[self.indxcntr][0]]