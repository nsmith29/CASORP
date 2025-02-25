#!/usr/bin/env python3

import asyncio
from asgiref.sync import sync_to_async
import time
from Core.CentralDefinitions import Dirs,  UArg, Ctl_Settings, proxyfunction, add2addressbook, Geo_Settings, \
    create_nested_dict, DictProperty
from Core.Iterables import ListElement_iterator
from DataCollection.FileSearch import MethodFiles, Entry4FromFiles
from Core.Messages import SlowMessageLines


__all__ = {'Files4DefiningDefect'}


class Files4DefiningDefect(MethodFiles):
    def __init__(self2, *args):
        super().__init__(*args)
    @classmethod
    async def setoffassessment(cls, keyword, subkeyword, **kwargs):
        self2 = cls(keyword, subkeyword)
        await super().assessment_tree(self2, self2.types[1], [self2.flexts_[1][0]], False, **kwargs) # defect
        if keyword != "geometry":
            await super().assessment_tree(self2, self2.types[0], self2.flexts_[0], True,  exchange=['geometry','standard']) # perfect
        [Ctl_Settings().i_defining['defect'].remove(it) for it in [[n,r,c,e] for n,r,c,e in Ctl_Settings().i_defining['defect']
                                                                   for n_,r_,c_,p in Ctl_Settings().e2_defining['defect']
                                                                   if n == n_ and r == r_ and c_ == c]]
        if Ctl_Settings().e2_defining['defect'] == [] and Ctl_Settings().defining_except_found is True or \
                Ctl_Settings().defining_except_found is None:
            Ctl_Settings.defining_except_found = False
        for item in Ctl_Settings().i_defining['defect']:
            item.pop(-1)
    async def option2(self2, keylst, extension, flpath, Q):
        return await eval("self2.option2{}".format(keylst[0]))(keylst, extension, flpath, Q)
    async def option2defect(self2, k, et, flpath, Q):
        paths, rtn, fnd = et if et=='.inp' else self2.flexts_[1][1], 'pass' if et=='.inp' else 'continue', False if \
                                                                                                           et!='.inp' \
                                                                                                           else None
        if type(flpath) == list and len(flpath) > 1 and et == '.inp':
            flpath.pop(-1)
        Dirs.address_book = await add2addressbook(k, [paths], [flpath], Dirs().address_book)
        if et == '.inp':
            xyzname = await Entry4FromFiles(flpath[0], 'inp', self2.keywrd) if type(flpath) == list else \
                await Entry4FromFiles(flpath, 'inp', self2.keywrd)
            await Q.put([False, xyzname])
        else:
            # check if same initial xyz file not found for any diff charge state dirs of same name & runtype when checked
            await self2.structural_data(k, self2.flexts_[1][1])
            if Ctl_Settings().defining_except_found is True:
                dif_chrgs = [[n, r, c, e] for n, r, c, e in Ctl_Settings().i_defining['defect'] if n==k[1] and r==k[2]
                             and c!=k[3] and e==et]
                async for n, r, c, e in ListElement_iterator(dif_chrgs):
                    if  str(self2.flexts_[1][1]+"*") not in Dirs().address_book['defect'][n][r][c].keys():
                        Dirs.address_book = await add2addressbook(['defect', n, r, c], [str(paths+'*')], [flpath],
                                                            Dirs().address_book)
                        await self2.structural_data(['defect', n, r, c], self2.flexts_[1][1])
                        path = [p for n_, r_, c_, p in Ctl_Settings().e2_defining['defect'] if n_==n and r_==r and
                                c_==c][0]
                        Ctl_Settings().e2_defining['defect'].remove([n, r, c, path])
            await asyncio.sleep(0.01)
            return rtn
    async def option2perfect(self2, keylst, extension, flpath, Q):
        await self2.structural_data(keylst, extension, [{'atoms': [], 'coords': [], 'nns': [], 'bonds': []}])
        replace_rtn = await MethodFiles.option2(self2, keylst, extension, flpath, Q)
        return replace_rtn
    async def option4(self2, keylst, extension):
        await eval('self2.option4{}'.format(keylst[0]))(keylst, extension)
    async def option4perfect(self2, keylst, extension):
        await MethodFiles.option4(self2, keylst, extension)
    async def option4defect(self2, k, e):
        # print('k entering option4 is', k)
        # indicate that dirs have been found with missing files
        Ctl_Settings.defining_except_found = True if Ctl_Settings().defining_except_found == None else \
                                                        Ctl_Settings().defining_except_found
        # get name of last dir in path of dir specified by keylist and add to keylist to save in 'analysis can't be done
        # [missing files]' dict
        l_dir_in_path = '/'.join([dir for dir in str(Dirs().address_book[k[0]][k[1]][k[2]][k[3]]["path"]).split('/') if
                                  dir not in str(UArg().cwd).split('/')])
        Ctl_Settings.e2_defining = await AppendDefDict('Ctl_Settings', 'e2_defining')(k, l_dir_in_path)
        await asyncio.sleep(0.01)
        # check for diff c dirs w/ same n & r have ''.xyz filepath same as e already found. If so, remove k from
        # 'analysis can't be done [missing files]' dict & add ''.xyz of diff c w/ same n & r to k's addressbook w/ *.
        dif_chrgs = [[n, r, c] for n, r, c in Dirs().dir_calc_keys[k[0]] if n==k[1] and r==k[2] and c!=k[3] and e!='.inp']
        async for n, r, c in ListElement_iterator(dif_chrgs):
            if self2.flexts_[1][1] in Dirs().address_book['defect'][n][r][c].keys():
                if e == str(Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]]).split('/')[-1]:
                    path = Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]]
                    # print('k before removing from e2_defining is', k)
                    Ctl_Settings().e2_defining['defect'].remove([k[1], k[2], k[3], k[-1]])
                    Dirs.address_book = await add2addressbook(k[:4], [str(self2.flexts_[1][1] + '*')], [path], Dirs().address_book)
                    await self2.structural_data(k[:4], self2.flexts_[1][1])
                    break
        if e != '.inp':
            # prep keylist to save in 'check for file in diff c dirs of same n & r' dict
            k.remove(l_dir_in_path)
            k.append(e)
            _, Ctl_Settings.i_defining = proxyfunction(k, None, None, None, Ctl_Settings().i_defining)
    async def structural_data(self2, k, ext, extdct=[{'nns': [], 'bonds':[]}]):
        await asyncio.sleep(0.01)
        if k[1] not in Geo_Settings().struc_data[k[0]] or k[2] not in Geo_Settings().struc_data[k[0]][k[1]] or \
           k[3] not in Geo_Settings().struc_data[k[0]][k[1]][k[2]] or \
          'lat paras' not in Geo_Settings().struc_data[k[0]][k[1]][k[2]][k[3]].keys():
            Geo_Settings.struc_data, _ = create_nested_dict(k, [ext, 'lat paras', 'defect type',
                                                                'defect indx'],
                                                            [extdct[0], [], '', []],
                                                            dict(Geo_Settings().struc_data))
        else:
            Geo_Settings.struc_data = await add2addressbook(k, ext, [extdct[0]],
                                                      dict(Geo_Settings().struc_data))


class AppendDefDict(DictProperty):
    def __init__(self, klass, method, ):
        super().__init__(klass, method)
    async def __call__(self, k, extra):
        k.append(extra)
        await asyncio.sleep(0.005)
        _, rtn = proxyfunction(k, None, None, None, self)
        self['defect'] = rtn['defect']
        return self
    def __str__(self):
        str_ = str("\n{bcolors.FAIL}WARNING: {bcolors.UNDERLINE}[Errno 2]{bcolors.ENDC}{bcolors.FAIL} Needed "
                         "{bcolors.KEYVAR}'"
                         + f"{self['filetypes']}"
                         + "'{bcolors.ENDC}{bcolors.FAIL} file(s) for {bcolors.METHOD}"
                         + f"{self['method']}"
                         + "{bcolors.ENDC}{bcolors.FAIL} could not be found within the "
                           "following directories for:")
        for value in self['defect']:
            str_ = str_ + str("\n{bcolors.KEYVAR}- " + f"{value[-1]} " + "{bcolors.ENDC}")
        return str_