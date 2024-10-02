#!/usr/bin/env python3

from Core.CentralDefinitions import G_Settings, End_Error, Dirs
from Core.Messages import ErrMessages, ask_question, Delay_Print, Global_lock, SlowMessageLines
from DataCollection.FileSearch import Entry4Files, MethodFiles, Method
from Core.CentralDefinitions import boolconvtr, CaS_Settings, create_nested_dict, Dirs, proxyfunction, UArg



__all__ = {'CntrolGeometry', 'GeometryProcessing'}


def CntrolGeometry():

    GeometryProcessing()






class GeometryProcessing(MethodFiles):
    def __init__(self2):
        super().__init__('Geometry')
        super().assessment_tree(self2, self2.type_, self2.flexts, self2.sect)
        # its possible that L.xyz file of perfect calc is initial xyz file of calc - so will be two -L.xyz file in subdir

    def option2(self2, kl, extension, flpath, Q):
        if kl[0] == 'perfect':
            G_Settings.perf_lxyz  = flpath

        if len(flpath) > 1:
            flpath.remove(G_Settings().perf_lxyz)
            End_Error(len(flpath) > 1,
                      ErrMessages.FileSearch_LookupError(extension,
                                                         Dirs().address_book[kl[0]][kl[1]][kl[2]][kl[3]]["path"],
                                                         "geometry"))
        super(GeometryProcessing, self2).option2(kl, extension, flpath, Q)


class DefineProcessing(MethodFiles):
    def __init__(self2, Q_):
        Method.__init__(self2, 'geometry', 'defect defining')
        super().assessment_tree(self2, self2.types[1], [self2.flexts_[1][0]], False)
        super().assessment_tree(self2, self2.types[0], self2.flexts_[0], True, None, 'geometry')

    def option2(self2, keylst, extension, flpath, Q):
        return exec(f'self2.option2{keylst[0]}(keylst, extension, flpath, Q)')

    def option2defect(self2, k, et, flpath, Q):
        paths, rtn, fnd = et if et == '.inp' else self2.flexts_[1][1], 'pass' if et == '.inp' else 'continue', \
                          False if et != '.inp' else None
        Dirs.address_book, _ = create_nested_dict(k, [paths], [flpath], Dirs().address_book)
        if et == '.inp':
            xyzname = Entry4Files(flpath[0], 'inp', 'charges and spins').Return()
            Q.put([False, [xyzname[1]] ])
        else:
            if CaS_Settings().nn_and_def_except_found is True:
                for n,r,c,e in ([n,r,c,e] for n,r,c,e in CaS_Settings().i_nad['defect'] if n==k[1] and r==k[2] and e==et):
                    Dirs.address_book, _ = create_nested_dict(['defect', n, r, c], [str(paths + '*')], [flpath],
                                                              Dirs().address_book)
                    path = [p for n_, r_, c_, p in CaS_Settings().e2n_a_d['defect'] if  n_==n and r_==r and c_==c][0]
                    CaS_Settings().e2n_a_d['defect'].remove([n, r, c, path])
                    CaS_Settings().i_nad['defect'].remove([n, r, c, e])
        return rtn

    def option2perfect(self2, keylst, extension, flpath, Q):
        replace_rtn = MethodFiles.option2(self2, keylst, extension, flpath, Q)
        return replace_rtn

    def option4(self2, keylst, extension):
        exec(f'self2.option4{keylst[0]}(keylst, extension)')

    def option4perfect(self2, keylst, extension):
        MethodFiles.option4(self2, keylst, extension)

    def option4defect(self2, k, e):
        CaS_Settings.nn_and_def_except_found, fnd = True if CaS_Settings().nn_and_def_except_found == None else \
            CaS_Settings().nn_and_def_except_found, False if e != '.inp' else None
        dp = '/'.join([d for d in str(Dirs().address_book[k[0]][k[1]][k[2]][k[3]]["path"]).split('/') if d not in
                       str(UArg().cwd).split('/')])
        k.append(dp)
        _, CaS_Settings.e2n_a_d = proxyfunction(k, None, None, None, CaS_Settings().e2n_a_d)
        for n,r,c in ([n,r,c] for n,r,c in Dirs().dir_calc_keys[k[0]] if n==k[1] and r==k[2] and c!=k[3] and e!='.inp'):
            if self2.flexts_[1][1] in Dirs().address_book['defect'][n][r][c].keys() and fnd is False:
                if e == str(Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]]).split('/')[-1]:
                    path, fnd = Dirs().address_book['defect'][n][r][c][self2.flexts_[1][1]].get(), True
                    CaS_Settings().e2n_a_d['defect'].remove([k[1], k[2], k[3], k[-1]])
                    Dirs.address_book, _= create_nested_dict(k, [str(path+'*')],[Dirs().address_book['defect'][n][r][c]
                                                                                 [path]], Dirs().address_book)
        if fnd is not True:
            k.remove(dp)
            k.append(e)
            _, CaS_Settings.i_nad = proxyfunction(k, None, None, None, CaS_Settings().i_nad)