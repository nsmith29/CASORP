#!/usr/bin/env python3

import asyncio
from collections import defaultdict
from pymatgen.core.structure import Structure
# import warnings
from Core.CentralDefinitions import Geo_Settings
from DataCollection.FromFile import read_file_async

__all__ = {'convert_back_charge', 'NewStructure', 'create_structure', 'DefineDefType'}

def rdft(var, num):
    return round(float(var), num)

async def convert_back_charge(charge):
    if type(charge) == str:
        charge = int("".join([charge[1], charge[0]]))
    else:
        pass
    await asyncio.sleep(0.01)
    return charge

class NewStructure(Structure):
    def __init__(self, lattice, species, coords, charge, validate_proximity=False, to_unit_cell=False, coords_are_cartesian=False, site_properties=None):
        super().__init__(lattice, species, coords, charge, validate_proximity, to_unit_cell,  coords_are_cartesian, site_properties)
    def asdict(self):
        sites, dct = [], {}
        for site in self:
            site_dict = site.as_dict(verbosity=1)
            del site_dict["lattice"]
            del site_dict["@module"]
            del site_dict["@class"]
            sites.append(site_dict)
        dct["sites"] = sites
        return dct
    def get_all_neighbors(self, r, include_index=False, include_image=False, sites=None, numerical_tol=1e-8, ):
        if sites is None:
            sites = self.sites
        center_indices, points_indices, images, distances = self.get_neighbor_list(
            r=r, sites=sites, numerical_tol=numerical_tol
        )
        if len(points_indices) < 1:
            return [[]] * len(sites)
        neighbor_dict: dict[int, list] = defaultdict(list)
        bonds = list()
        for cindex, pindex, d in zip(center_indices, points_indices, distances, ):
            if pindex not in neighbor_dict or pindex in neighbor_dict and cindex not in neighbor_dict[pindex]:
                neighbor_dict[int(cindex)].append(int(pindex))
                bonds.append(str("{}-{}".format(cindex, pindex)))

        n_dict = neighbor_dict
        neighbors = []
        for i in range(len(sites)):
            if n_dict[i] != []:
                neighbors.append({i: n_dict[i]})
        return [neighbors, bonds]

async def create_structure(atoms, x, y, z, A, B, C, charge):
    charge = await convert_back_charge(charge)
    matrix = []
    for x_, y_, z_ in zip(list(x), list(y), list(z)):
        matrix.append([x_, y_, z_])
    # warnings.filterwarnings('ignore', '.*CrystalNN.*', )
    # warnings.filterwarnings('ignore', '.*No oxidation.*', )
    structure = NewStructure([A, B, C], atoms, matrix, charge, to_unit_cell=True, coords_are_cartesian=True)
    await asyncio.sleep(0.01)
    return structure

class DefineDefType:
    def __init__(self, calckey, perfxyz, defxyz):
        self.name = calckey
        self.perfxyz, self.defxyz = perfxyz, defxyz
        self.bk_, self.def_ = None, None
        self.bk_crds, self.def_crds = None, None
    def __getitem__(self, j):
        return [1 if self.bk_crds[j] not in self.def_crds else [2 if self.def_crds[j] not in self.bk_crds else None][0]][0]
    def __ne__(self, i):
        return self.bk_crds[i]!=self.def_crds[i]
    def __lt__(self):
        return len(self.bk_crds) if len(self.bk_crds)<len(self.def_crds) else len(self.def_crds)
    async def type_definition(self):
        bulk, defect = await read_file_async(self.perfxyz), await read_file_async(self.defxyz)
        self.bk_, self.def_ = [line.split() for line in bulk.split('\n')][2::], \
                              [line.split() for line in defect.split('\n')][2::]
        self.bk_crds = [[rdft(x, 6), rdft(y, 6), rdft(z, 6)] for x, y, z in
                   [i for i in [l[1::] for l in self.bk_] if i != []]]
        self.def_crds = [[rdft(x, 6), rdft(y, 6), rdft(z, 6)] for x, y, z in
                    [i for i in [l[1::] for l in self.def_] if i != []]]
        if self.bk_crds == self.def_crds:
            substitutional.keys = self.name
            return await substitutional([[self.bk_[i][0], *self.bk_crds[i]] for i in range(len(self.bk_crds))],
                                  [[self.def_[i][0], *self.def_crds[i]] for i in range(len(self.def_crds))]).finding()
        else:
            select = [k for k in [self.__getitem__(j) for j in [i for i in range(self.__lt__()) if self.__ne__(i)]] if k !=None]
            if 1 in select and 2 in select:
                vacancy_interstitial.keys = self.name
                return await vacancy_interstitial([[self.bk_[i][0], *self.bk_crds[i]] for i in range(len(self.bk_crds))],
                                  [[self.def_[i][0], *self.def_crds[i]] for i in range(len(self.def_crds))]).finding()
            elif 2 not in select:
                vacancy.keys = self.name
                return await vacancy([[self.bk_[i][0], *self.bk_crds[i]] for i in range(len(self.bk_crds))],
                                  [[self.def_[i][0], *self.def_crds[i]] for i in range(len(self.def_crds))]).finding()
            elif 1 not in select:
                interstitial.keys = self.name
                return await interstitial([[self.bk_[i][0], *self.bk_crds[i]] for i in range(len(self.bk_crds))],
                                  [[self.def_[i][0], *self.def_crds[i]] for i in range(len(self.def_crds))]).finding()

class defect:
    keys = None
    def __init__(self, bk_, def_):
        self.bk_, self.def_, self.diff_atoms, self.atoms_dict, self.indicator, self.counter = bk_, def_, [], [], None, 0
    def __iadd__(self, func):
        async def wrapper(*args):
            self.counter +=1
            return await func(args)
        return wrapper
    def __len__(self):
        return len(self.def_)
    async def diff(self, *args):
        return args
    def test_variable(self, type_):
        raise NotImplementedError('function deriving variables to use in for loop not implemented')
    async def finding(self):
        diff = None  # will become number of defect sites found.
        idx = -1
        for b, d in zip(self.test_variable(self.bk_), self.test_variable(self.def_)):
            await asyncio.sleep(0.001)
            if diff:
                b, d = await self.diff(b, d, diff)
            idx += 1
            if self.__ne__([b, d]):
                diff = await self.__iadd__(self.ne_satisfied)(idx, b, d, diff)
        print(type(self).__name__, '[DA.GA L127]')
        print('diff_atoms=', self.diff_atoms, '[DA.GA L128]')
        return type(self).__name__, self.__len__(), self.counter, self.diff_atoms, self.atoms_dict
    def ne_satisfied(self, idx, b, d, diff):
        return diff
    def additional(self, dif_atoms):
        additional = []
        keys = self.keys
        for atom in dif_atoms:

            for bond in Geo_Settings().struc_data[keys[1]][keys[2]][keys[3]][keys[4]][keys[0]]['bonds']:
                atoms = bond.replace('-', ' ').split()
                if atom == atoms[0] or atom == atoms[1]:
                    length1 = len(additional)
                    additional.append([atoms[i] for i in range(len(atoms)) if
                                       atoms[i] != atom and atoms[i] not in additional and atom[i] not in dif_atoms])
                    if length1 != len(additional) and len(additional[-1]) == 1:
                        print('in if testing additional length', [additional[-1][0]][0], '[DA.GA L143]')
                        additional.insert(-1, [additional[-1][0]][0])
                    print('just before additional.pop(-1)', additional[-1], '[DA.GA L145]')
                    additional.pop(-1)
        return additional

class substitutional(defect):
    def __init__(self, bk_, def_):
        super().__init__(bk_, def_)
    def __ne__(self, other):
        return other[0] != other[1]
    def test_variable(self, type_):
        return [var[0] for var in [l for l in type_ if l != []]]
    async def ne_satisfied(self, idx, b, d, diff):
        self.diff_atoms.append(str(idx))
        self.atoms_dict.append({str(idx): d})
        return diff

class vacancy(defect):
    def __init__(self, bk_, def_):
        super().__init__(bk_, def_)
    def __ne__(self, v):
        v1, v2 = v[0][1], v[1][1]
        if v1[0] != v2[0] and v1[1] != v2[1] and v1[2] != v2[2] and v1[3] != v2[3] and self.indicator != None:
            self.indicator = None
        elif v1[0] != v2[0] and v1[1] == v2[1] and v1[2] == v2[2] and v1[3] == v2[3]:
            if '_substitution' not in type(self).__name__:
                type(self).__name__ = str(type(self).__name__) + '_substitution'
            self.indicator = 'substitution'
        return v1[0] != v2[0] and v1[1] != v2[1] and v1[2] != v2[2] and v1[3] != v2[3] or v1[0] != v2[0] and v1[1] == \
               v2[1] and v1[2] == v2[2] and v1[3] == v2[3]
    def test_variable(self, type_):
        return [[l1, [a1, x1, y1, z1]] for [l1, [a1, x1, y1, z1]] in enumerate([l for l in type_ if l != []])]
    async def diff(self, b, d, diff):
        l2, a2, x2, y2, z2 = d[0], *d[1]
        l2 = l2 - diff
        a2, x2, y2, z2 = self.def_[l2]
        return [b, [l2, [a2, x2, y2, z2]]]
    async def ne_satisfied(self, idx, b, d, diff):
        if self.indicator is None:
            self.atoms_dict.append({str(idx) + ' missing from defect': b[1][0]})
            toadd = self.additional([idx])
            self.diff_atoms.extend([ i for i in toadd])
            self.atoms_dict.extend({str(i) : self.def_[i][0]} for i in toadd)
            diff_ = diff + 1 if diff else 1
        else:
            self.diff_atoms.append(str(idx))
            self.atoms_dict.append({str(idx): d[1][0]})
            diff_ = diff
        return diff_

class vacancy_interstitial(defect):
    def __init__(self, bk_, def_):
        super().__init__(bk_, def_)
        self.indicator = []
    def __ne__(self, vals):
        b, d = vals[0][1], vals[1][1]
        v, i, k, f = vals[0][0] + 1, vals[1][0] + 1, self.bk_, self.def_
        if b[0] != d[0] and b[1] != d[1] and b[2] != d[2] and b[3] != d[3]:
            if k[v][0] == d[0] and k[v][1] == d[1] and k[v][2] == d[2] and k[v][3] == d[3]:
                self.indicator.append('vacancy')
            elif b[0] == f[i][0] and b[1] == f[i][1] and b[2] == f[i][2] and b[3] == f[i][3]:
                self.indicator.append('interstitial')
            else:
                print('\n', b, '       ', f, '\n', d, '       ', k)
        elif b[0] != d[0] and b[1] == d[1] and b[2] == d[2] and b[3] == d[3]:
            self.indicator.append('substitution')
        return b[0] != d[0] and b[1] != d[1] and b[2] != d[2] and b[3] != d[3] or b[0] != d[0] and b[1] == d[1] and b[
            2] == d[2] and b[3] == d[3]
    def test_variable(self, type_):
        return [[l1, [a1, x1, y1, z1]] for [l1, [a1, x1, y1, z1]] in enumerate([l for l in type_ if l != []])]
    async def diff(self, b, d, diff):
        if self.indicator[0] == 'vacancy':
            b_, d_ = vacancy(self.bk_, self.def_).diff(b, d, diff)
        elif self.indicator[0] == 'interstitial':
            b_, d_ = interstitial(self.bk_, self.def_).diff(b, d, diff)
        return b_, d_
    async def ne_satisfied(self, idx, b, d, diff):
        self.diff_atoms.append(str(idx)) if self.indicator[-1] != 'vacancy' else self.diff_atoms.extend(
            [i for i in self.additional([idx])])
        self.atoms_dict.append({str(idx): d[1][0]}) if self.indicator[-1] != 'vacancy' else self.atoms_dict.extend(
            [{str(idx + ' missing from defect'): b[1][0]}, *[{str(i) : self.def_[i][0]} for i in self.additional([idx])]])
        if self.indicator[-1] == 'substitution':
            diff_ = diff
        else:
            indicators = [i for i in self.indicator if i != 'substitution']
            if len(indicators) == 1:
                diff_ = diff + 1 if diff else 1
            elif len(indicators) == 2:
                diff_ = diff - 1
            elif len(indicators) > 2:
                diff_ = diff - 1 if indicators[-1] == 'vacancy' else diff + 1  # indicators[-1]==interstitial
        return diff_

class interstitial(defect):
    def __init__(self, bk_, def_):
        super().__init__(bk_, def_)
    def __ne__(self, v):
        v1, v2 = v[0][1], v[1][1]
        if v1[0] != v2[0] and v1[1] != v2[1] and v1[2] != v2[2] and v1[3] != v2[3] and self.indicator != None:
            self.indicator = None
        elif v1[0] != v2[0] and v1[1] == v2[1] and v1[2] == v2[2] and v1[3] == v2[3]:
            if '_substitution' not in type(self).__name__:
                type(self).__name__ = str(type(self).__name__) + '_substitution'
            self.indicator = 'substitution'
        return v1[0] != v2[0] and v1[1] != v2[1] and v1[2] != v2[2] and v1[3] != v2[3] or v1[0] != v2[0] and v1[1] == \
               v2[1] and v1[2] == v2[2] and v1[3] == v2[3]
    def test_variable(self, type_):
        return [[l1, [a1, x1, y1, z1]] for [l1, [a1, x1, y1, z1]] in enumerate([l for l in type_ if l != []])]
    async def diff(self, b, d, diff):
        l1, a1, x1, y1, z1 = b[0], *b[1]
        l1 = l1 - diff
        a1, x1, y1, z1 = self.bk_[l1]
        return [[l1, [a1, x1, y1, z1]], d]
    async def ne_satisfied(self, idx, b, d, diff):
        self.diff_atoms.append({str(idx): d[1][0]})
        if self.indicator is None:
            diff_ = diff + 1 if diff else 1
        else:
            diff_ = diff
        return diff_
