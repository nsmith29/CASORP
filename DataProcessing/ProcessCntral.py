#!/usr/bin/env python3

from Core.CentralDefinitions import Dirs, create_nested_dict, UArg, Ctl_Settings, proxyfunction
from DataCollection.FileSearch import MethodFiles, Method, Entry4Files


__all__ = {'Files4DefiningDefect'}

class Files4DefiningDefect(MethodFiles):
    def __init__(self2, keyword, subkeyword, **kwargs):
        Method.__init__(self2, keyword, subkeyword)
        super().assessment_tree(self2, self2.types[1], [self2.flexts_[1][0]], False, **kwargs) # defect
        super().assessment_tree(self2, self2.types[0], self2.flexts_[0], True) if keyword=="geometry" else \
            super().assessment_tree(self2, self2.types[0], self2.flexts_[0], True,  exchange='geometry') # perfect

    def option2(self2, keylst, extension, flpath, Q):
        return exec(f'self2.option2{keylst[0]}(keylst, extension, flpath, Q)')

    def option2defect(self2, k, et, flpath, Q):
        paths, rtn, fnd = et if et == '.inp' else self2.flexts_[1][1], 'pass' if et == '.inp' else 'continue', \
                          False if et != '.inp' else None
        Dirs.address_book, _ = create_nested_dict(k, [paths], [flpath], Dirs().address_book)
        if et == '.inp':
            xyzname = Entry4Files(flpath[0], 'inp', self2.keywrd).Return()
            Q.put([False, [xyzname[1]]])
        else:
            if Ctl_Settings.defining_except_found is True:
                for n, r, c, e in ([n, r, c, e] for n, r, c, e in Ctl_Settings().i_defining['defect'] if
                                   n == k[1] and r == k[2] and e == et):
                    Dirs.address_book, _ = create_nested_dict(['defect', n, r, c], [str(paths + '*')], [flpath],
                                                              Dirs().address_book)
                    path = [p for n_, r_, c_, p in Ctl_Settings().e2_defining['defect'] if n_ == n and r_ == r and
                            c_ == c][ 0]
                    Ctl_Settings().e2_defining['defect'].remove([n, r, c, path])
                    # CaS_Settings().i_nad['defect'].remove([n, r, c, e])
            return rtn


    def option2perfect(self2, keylst, extension, flpath, Q):
        replace_rtn = MethodFiles.option2(self2, keylst, extension, flpath, Q)
        return replace_rtn

    def option4(self2, keylst, extension):
        exec(f'self2.option4{keylst[0]}(keylst, extension)')

    def option4perfect(self2, keylst, extension):
        MethodFiles.option4(self2, keylst, extension)

    def option4defect(self2, k, e):
        Ctl_Settings.nn_and_def_except_found = True if Ctl_Settings().defining_except_found == None else \
                                                        Ctl_Settings().defining_except_found
        fnd =  False if e != '.inp' else None
        dp = '/'.join([d for d in str(Dirs().address_book[k[0]][k[1]][k[2]][k[3]]["path"]).split('/') if d not in
                       str(UArg().cwd).split('/')])
        k.append(dp)
        _, Ctl_Settings.e2_defining = proxyfunction(k, None, None, None, Ctl_Settings().e2_defining)
        for n, r, c in ([n, r, c] for n, r, c in Dirs().dir_calc_keys[k[0]] if
                        n == k[1] and r == k[2] and c != k[3] and e != '.inp'):
            if self2.flexts_[1][1] in Dirs().address_book['defect'][n][r][c].keys() and fnd is False:
                if e == str(Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]]).split('/')[-1]:
                    path= Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]].get()
                    # path, fnd = Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]].get(), True
                    Ctl_Settings().e2_defining['defect'].remove([k[1], k[2], k[3], k[-1]])
                    Dirs.address_book, _ = create_nested_dict(k, [str(path + '*')],
                                                              [Dirs().address_book['defect'][n][r][c]
                                                               [path]], Dirs().address_book)
        if fnd is False:
            k.remove(dp)
            k.append(e)
            _, Ctl_Settings.i_defining = proxyfunction(k, None, None, None, Ctl_Settings().i_defining)