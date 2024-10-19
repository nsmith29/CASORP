#!/usr/bin/env python3

import asyncio
from Core.CentralDefinitions import Dirs,  UArg, Ctl_Settings, proxyfunction, add2addressbook
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

    async def option2(self2, keylst, extension, flpath, Q):
        return await eval("self2.option2{}".format(keylst[0]))(keylst, extension, flpath, Q)

    async def option2defect(self2, k, et, flpath, Q):
        paths, rtn, fnd = et if et == '.inp' else self2.flexts_[1][1], 'pass' if et == '.inp' else 'continue', False if et != '.inp' else None
        if len(flpath) > 1 and et == '.inp':
            flpath.pop(-1)
        Dirs.address_book = add2addressbook(k, [paths], [flpath], Dirs().address_book)
        if et == '.inp':
            xyzname = await Entry4FromFiles(flpath[0], 'inp', self2.keywrd)
            await Q.put([False, xyzname])
        else:
            # check if same initial xyz file not found for any diff charge state dirs of same name & runtype when checked
            if Ctl_Settings().defining_except_found is True:
                dif_chrgs = [[n, r, c, e] for n, r, c, e in Ctl_Settings().i_defining['defect'] if n==k[1] and r==k[2] and c!=k[3] and e==et]
                async for n, r, c, e in keylist_iterator(dif_chrgs):
                    if  str(self2.flexts_[1][1]+"*") not in Dirs().address_book['defect'][n][r][c].keys():
                        Dirs.address_book = add2addressbook(['defect', n, r, c], [str(paths+'*')], [flpath], Dirs().address_book)
                        path = [p for n_, r_, c_, p in Ctl_Settings().e2_defining['defect'] if n_==n and r_==r and c_==c][0]
                        Ctl_Settings().e2_defining['defect'].remove([n, r, c, path])
                        print('found for', n, r, c, e)
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
        # get name of last dir in path of dir specified by keylist
        l_dir_in_path = '/'.join([dir for dir in str(Dirs().address_book[k[0]][k[1]][k[2]][k[3]]["path"]).split('/') if
                                  dir not in str(UArg().cwd).split('/')])
        # add name of last dir to keylist
        k.append(l_dir_in_path)
        # save keylist in dictionary of dirs where analysis may not be able to be done due to missing files.
        _, Ctl_Settings.e2_defining = proxyfunction(k, None, None, None, Ctl_Settings().e2_defining)
        await asyncio.sleep(0.01)
        # check for diff charge state dirs of same name & runtype.
        dif_chrgs = [[n, r, c] for n, r, c in Dirs().dir_calc_keys[k[0]] if n==k[1] and r==k[2] and c!=k[3] and e!='.inp']
        async for n, r, c in keylist_iterator(dif_chrgs):
            # check if these diff charge state dir w/ same name & runtype have had path of initial xyz file found.
            if self2.flexts_[1][1] in Dirs().address_book['defect'][n][r][c].keys():
                # check if initial xyz in diff charge state dir w/ same name & runtype is same as looking for, for k.
                if e == str(Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]][0]).split('/')[-1]:
                    path = Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]][0]
                    # remove k from dictionary of dirs where analysis may not be able to be done due to missing files.
                    Ctl_Settings().e2_defining['defect'].remove([k[1], k[2], k[3], k[-1]])
                    # add initial xyz of diff charge state w/ same name & runtype to k's book & indicate assumed path w/ *
                    Dirs.address_book = add2addressbook(k, [str(self2.flexts_[1][1] + '*')], [path], Dirs().address_book)
                    break
        if e != '.inp':
            # prep keylist to save in dict of dirs where diff charge state dirs of same name & runtype searched for file
            k.remove(l_dir_in_path)
            k.append(e)
            _, Ctl_Settings.i_defining = proxyfunction(k, None, None, None, Ctl_Settings().i_defining)
