#!/usr/bin/env python3

import asyncio

__all__ = {'async_pairing_iterator', 'GetDirs_iterator', 'FileExt_iterator', 'keylist_iterator', 'Lines_iterator',
           'toFromFiles_iterator'}

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

class getDirs_iterator():
    def __init__(self, cat):
        self.cat = cat
        self.counter = -1
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.counter >= len(self.cat)-1:
            raise StopAsyncIteration
        self.counter +=1
        return self.cat[self.counter]

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

class keylist_iterator():
    def __init__(self, dif_chrgs):
        self.counter  = -1
        self.dif_chrgs = dif_chrgs
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.counter >= len(self.dif_chrgs)-1:
            raise StopAsyncIteration
        self.counter +=1
        return self.dif_chrgs[self.counter]

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

class toFromFiles_iterator():
    """
        Iterator for cycling through the multiple variables required for extraction/collection for result processing method.
    """
    def __init__(self, want):
        self.want = want
        self.counter = -1
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.counter >= len(self.want) - 1:
            raise StopAsyncIteration
        self.counter += 1
        return self.want[self.counter]