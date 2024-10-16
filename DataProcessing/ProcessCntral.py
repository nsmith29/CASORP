#!/usr/bin/env python3

import asyncio
from Core.CentralDefinitions import Dirs, create_nested_dict, UArg, Ctl_Settings, proxyfunction, add2addressbook
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
            await super().assessment_tree(self2, self2.types[0], self2.flexts_[0], True,  exchange='geometry') # perfect
    async def option2(self2, keylst, extension, flpath, Q):
        return await eval("self2.option2{}".format(keylst[0]))(keylst, extension, flpath, Q)

    async def option2defect(self2, k, et, flpath, Q):
        paths, rtn, fnd = et if et == '.inp' else self2.flexts_[1][1], 'pass' if et == '.inp' else 'continue', False if et != '.inp' else None
        Dirs.address_book = add2addressbook(k, [paths], [flpath], Dirs().address_book)
        if et == '.inp':
            xyzname = await Entry4FromFiles(flpath[0], 'inp', self2.keywrd)
            await Q.put([False, xyzname])
        else:
            if Ctl_Settings.defining_except_found is True:
                for n, r, c, e in ([n, r, c, e] for n, r, c, e in Ctl_Settings().i_defining['defect'] if
                                   n == k[1] and r == k[2] and c != k[3] and e == et):
                    Dirs.address_book = add2addressbook(['defect', n, r, c], [str(paths + '*')], [flpath], Dirs().address_book)
                    path = [p for n_, r_, c_, p in Ctl_Settings().e2_defining['defect'] if n_ == n and r_ == r and c_ == c][ 0]
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
        Ctl_Settings.defining_except_found = True if Ctl_Settings().defining_except_found == None else \
                                                        Ctl_Settings().defining_except_found
        fnd =  False if e != '.inp' else None
        dp = '/'.join([d for d in str(Dirs().address_book[k[0]][k[1]][k[2]][k[3]]["path"]).split('/') if d not in str(UArg().cwd).split('/')])
        k.append(dp)
        _, Ctl_Settings.e2_defining = proxyfunction(k, None, None, None, Ctl_Settings().e2_defining)
        await asyncio.sleep(0.01)
        for n, r, c in ([n, r, c] for n, r, c in Dirs().dir_calc_keys[k[0]] if
                        n == k[1] and r == k[2] and c != k[3] and e != '.inp'):
            if self2.flexts_[1][1] in Dirs().address_book['defect'][n][r][c].keys() and fnd is False:
                if e == str(Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]]).split('/')[-1]:
                    path= Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]].get()
                    Ctl_Settings().e2_defining['defect'].remove([k[1], k[2], k[3], k[-1]])
                    Dirs.address_book = add2addressbook(k, [str(self2.flexts_[1][1] + '*')],
                                                              [Dirs().address_book['defect'][n][r][c]
                                                               [path]], Dirs().address_book)
        if fnd is False:
            k.remove(dp)
            k.append(e)
            _, Ctl_Settings.i_defining = proxyfunction(k, None, None, None, Ctl_Settings().i_defining)
