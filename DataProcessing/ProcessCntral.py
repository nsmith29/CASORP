#!/usr/bin/env python3

import asyncio
from Core.CentralDefinitions import Dirs,  UArg, Ctl_Settings, proxyfunction, add2addressbook, Geo_Settings, create_nested_dict
from Core.Iterables import keylist_iterator
from DataCollection.FileSearch import MethodFiles, Entry4FromFiles


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
        if Ctl_Settings().e2_defining['defect'] == [] and Ctl_Settings().defining_except_found is True:
            Ctl_Settings.defining_except_found = False
        for item in Ctl_Settings().i_defining['defect']:
            item.pop(-1)
    async def option2(self2, keylst, extension, flpath, Q):
        return await eval("self2.option2{}".format(keylst[0]))(keylst, extension, flpath, Q)
    async def option2defect(self2, k, et, flpath, Q):
        paths, rtn, fnd = et if et == '.inp' else self2.flexts_[1][1], 'pass' if et == '.inp' else 'continue', False if et != '.inp' else None
        if type(flpath) == list and len(flpath) > 1 and et == '.inp':
            flpath.pop(-1)
        Dirs.address_book = add2addressbook(k, [paths], [flpath], Dirs().address_book)
        if et == '.inp':
            xyzname = await Entry4FromFiles(flpath[0], 'inp', self2.keywrd) if type(flpath) == list else await Entry4FromFiles(flpath, 'inp', self2.keywrd)
            await Q.put([False, xyzname])
        else:
            # check if same initial xyz file not found for any diff charge state dirs of same name & runtype when checked
            self2.structural_data(k)
            if Ctl_Settings().defining_except_found is True:
                dif_chrgs = [[n, r, c, e] for n, r, c, e in Ctl_Settings().i_defining['defect'] if n==k[1] and r==k[2] and c!=k[3] and e==et]
                async for n, r, c, e in keylist_iterator(dif_chrgs):
                    if  str(self2.flexts_[1][1]+"*") not in Dirs().address_book['defect'][n][r][c].keys():
                        Dirs.address_book = add2addressbook(['defect', n, r, c], [str(paths+'*')], [flpath], Dirs().address_book)
                        self2.structural_data(['defect', n, r, c])
                        path = [p for n_, r_, c_, p in Ctl_Settings().e2_defining['defect'] if n_==n and r_==r and c_==c][0]
                        Ctl_Settings().e2_defining['defect'].remove([n, r, c, path])
            await asyncio.sleep(0.01)
            return rtn
    async def option2perfect(self2, keylst, extension, flpath, Q):
        replace_rtn = await MethodFiles.option2(self2, keylst, extension, flpath, Q)
        return replace_rtn
    async def option4(self2, keylst, extension):
        await eval('self2.option4{}'.format(keylst[0]))(keylst, extension)
    async def option4perfect(self2, keylst, extension):
        await MethodFiles.option4(self2, keylst, extension)
    async def option4defect(self2, k, e):
        # indicate that dirs have been found with missing files
        Ctl_Settings.defining_except_found = True if Ctl_Settings().defining_except_found == None else \
                                                        Ctl_Settings().defining_except_found
        # get name of last dir in path of dir specified by keylist and add to keylist to save in 'analysis can't be done
        # [missing files]' dict
        l_dir_in_path = '/'.join([dir for dir in str(Dirs().address_book[k[0]][k[1]][k[2]][k[3]]["path"]).split('/') if
                                  dir not in str(UArg().cwd).split('/')])
        k.append(l_dir_in_path)
        _, Ctl_Settings.e2_defining = proxyfunction(k, None, None, None, Ctl_Settings().e2_defining)
        await asyncio.sleep(0.01)
        # check for diff c dirs w/ same n & r have ''.xyz filepath same as e already found. If so, remove k from
        # 'analysis can't be done [missing files]' dict & add ''.xyz of diff c w/ same n & r to k's addressbook w/ *.
        dif_chrgs = [[n, r, c] for n, r, c in Dirs().dir_calc_keys[k[0]] if n==k[1] and r==k[2] and c!=k[3] and e!='.inp']
        async for n, r, c in keylist_iterator(dif_chrgs):
            if self2.flexts_[1][1] in Dirs().address_book['defect'][n][r][c].keys():
                if e == str(Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]]).split('/')[-1]:
                    path = Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]]
                    Ctl_Settings().e2_defining['defect'].remove([k[1], k[2], k[3], k[-1]])
                    Dirs.address_book = add2addressbook(k, [str(self2.flexts_[1][1] + '*')], [path], Dirs().address_book)
                    self2.structural_data(k)
                    break
        if e != '.inp':
            # prep keylist to save in 'check for file in diff c dirs of same n & r' dict
            k.remove(l_dir_in_path)
            k.append(e)
            _, Ctl_Settings.i_defining = proxyfunction(k, None, None, None, Ctl_Settings().i_defining)
    def structural_data(self2, k):
        #
        if k[1] not in Geo_Settings().struc_data[k[0]] or k[2] not in Geo_Settings().struc_data[k[0]][k[1]] or \
           k[3] not in Geo_Settings().struc_data[k[0]][k[1]][k[2]] or \
          'lat paras' not in Geo_Settings().struc_data[k[0]][k[1]][k[2]][k[3]].keys():
            Geo_Settings.struc_data, _ = create_nested_dict(k, [self2.flexts_[1][1], 'lat paras', 'defect type', 'defect indx'],
                                                         [{'nns': [], 'bonds': []}, [], '', []],
                                                        Geo_Settings().struc_data)
        else:
            Geo_Settings.struc_data = add2addressbook(k, [self2.flexts_[1][1]], [{'nns': [], 'bonds': []}], Geo_Settings().struc_data)