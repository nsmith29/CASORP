#!/usr/bin/env python3

import asyncio
from asgiref.sync import sync_to_async
from collections import defaultdict
from pymatgen.core.structure import Structure
# import warnings
from Core.CentralDefinitions import Geo_Settings
from Core.Iterables import DefectTypeTestVariables_iterator, AdditionalAtoms_iterator, standard_iterator
from DataCollection.FromFile import read_file_async

__all__ = {'rdft', 'convert_back_charge', 'NewStructure', 'create_structure', 'DefineDefType', 'defect',
           'substitutional', 'vacancy', 'vacancy_interstitial', 'interstitial'}

def rdft(vr, nm) -> float:
    """
        :param vr: item to be converted to float and rounded.
        :param nm: number of decimal places to round item to
        :param list:

        :return float: rounded float
    """
    if len(str(vr)) > str(vr).index('.')+nm+1 and str(vr)[str(vr).index('.')+nm+1] == str(5) and \
            float(str(vr)[:nm+str(vr).index('.')+1]) == round(float(vr), nm):
        return round(float(vr)+(1*(10**(-nm-1))), nm)
    else:
        return round(float(vr), nm)

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
                bonds.append({str("{}-{}".format(cindex, pindex)): rdft(d,4)})
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
    structure = NewStructure([A, B, C], atoms, matrix, charge, to_unit_cell=True, coords_are_cartesian=True)
    await asyncio.sleep(0.01)
    return structure

class DefineDefType:
    def __init__(self, calckey, perfxyz, defxyz):
        self.name = calckey
        # self.perfxyz, self.defxyz = perfxyz, defxyz
        # self.bk_, self.def_ = None, None
        self.bk_, self.def_ = perfxyz, defxyz
        self.bk_crds, self.def_crds = None, None
        # self.bk_, self.def_ = perfatoms, defatoms
        # self.bk_crds, self.def_crds = perfxyz, defxyz
    def __getitem__(self, j):
        return [1 if self.bk_crds[j] not in self.def_crds else [2 if self.def_crds[j] not in self.bk_crds else None][0]][0]
    def __ne__(self, i):
        return self.bk_crds[i]!=self.def_crds[i]
    def __lt__(self):
        return len(self.bk_crds) if len(self.bk_crds)<len(self.def_crds) else len(self.def_crds)
    async def type_definition(self):
        self.bk_crds = [[rdft(self.bk_[i][1], 6), rdft(self.bk_[i][2], 6), rdft(self.bk_[i][3], 6)] async for i in
                   standard_iterator(len(self.bk_))]
        self.def_crds = [[rdft(self.def_[i][1], 6),  rdft(self.def_[i][2], 6), rdft(self.def_[i][3], 6)] async for i in
                    standard_iterator(len(self.def_))]
        if self.bk_crds == self.def_crds:
            substitutional.keys = self.name
            return await substitutional([[self.bk_[i][0], *self.bk_crds[i]] async for i in standard_iterator(len(self.bk_crds))],
                                  [[self.def_[i][0], *self.def_crds[i]] async for i in standard_iterator(len(self.def_crds))]).finding()
        else:
            select = [k for k in [self.__getitem__(j) for j in [i async for i in standard_iterator(self.__lt__()) if self.__ne__(i)]] if k !=None]
            if 1 in select and 2 in select:
                vacancy_interstitial.keys = self.name
                return await vacancy_interstitial([[self.bk_[i][0], *self.bk_crds[i]] async for i in standard_iterator(len(self.bk_crds))],
                                  [[self.def_[i][0], *self.def_crds[i]] async for i in standard_iterator(len(self.def_crds))]).finding()
            elif 2 not in select:
                vacancy.keys = self.name
                return await vacancy([[self.bk_[i][0], *self.bk_crds[i]] async for i in standard_iterator(len(self.bk_crds))],
                                  [[self.def_[i][0], *self.def_crds[i]] async for i in standard_iterator(len(self.def_crds))]).finding()
            elif 1 not in select:
                interstitial.keys = self.name
                return await interstitial([[self.bk_[i][0], *self.bk_crds[i]] async for i in standard_iterator(len(self.bk_crds))],
                                  [[self.def_[i][0], *self.def_crds[i]] async for i in standard_iterator(len(self.def_crds))]).finding()

class defect:
    keys = None
    def __init__(self, bk_, def_):
        # print('within defect type class')
        self.bk_, self.def_, self.diff_atoms, self.atoms_dict, self.indicator, self.counter = bk_, def_, [], [], None, 0
        self.additional_noted = []
    def __iadd__(self, func):
        async def wrapper(*args):
            self.counter +=1
            return await func(*args)
        return wrapper
    def __len__(self):
        return len(self.def_)
    async def diff(self, *args):
        return args
    # def test_variable(self, type_):
    #     raise NotImplementedError('function deriving variables to use in for loop not implemented')
    async def finding(self):
        # print('within finding of defect type class')
        diff = None  # will become number of defect sites found.
        idx = -1
        async for b, d in DefectTypeTestVariables_iterator(type(self).__name__, self.bk_, self.def_):
            await asyncio.sleep(0.001)
            if diff:
                b, d = await self.diff(b, d, diff)
            idx += 1
            if self.__ne__([b, d]):
                diff = await self.__iadd__(self.ne_satisfied)(idx, b, d, diff)
        return type(self).__name__, self.__len__(), self.counter, self.diff_atoms, self.atoms_dict
    async def ne_satisfied(self, idx, b, d, diff):
        return diff
    async def additional(self, dif_atom):
        additional = []
        k = self.keys
        async for bd in AdditionalAtoms_iterator(dif_atom, Geo_Settings().struc_data[k[1]][k[2]][k[3]][k[4]][k[0]]['bonds']):
            atoms = bd.replace('-', ' ').split()
            adding = [int(atoms[i]) for i in range(len(atoms)) if
                               atoms[i] != str(dif_atom) and atoms[i] not in self.additional_noted]
            if adding != []:
                additional.extend(adding)
                self.additional_noted.extend(adding)
        return additional

class substitutional(defect):
    def __init__(self, bk_, def_):
        super().__init__(bk_, def_)
    def __ne__(self, other):
        return other[0] != other[1]
    # def test_variable(self, type_):
    #     return [var[0] for var in [l for l in type_ if l != []]]
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
    # def test_variable(self, type_):
    #     return [[l1, [a1, x1, y1, z1]] for [l1, [a1, x1, y1, z1]] in enumerate([l for l in type_ if l != []])]
    async def diff(self, b, d, diff):
        l2, a2, x2, y2, z2 = d[0], *d[1]
        l2 = l2 - diff
        a2, x2, y2, z2 = self.def_[l2]
        return [b, [l2, [a2, x2, y2, z2]]]
    async def ne_satisfied(self, idx, b, d, diff):
        if self.indicator is None:
            self.atoms_dict.append({str(idx) + ' missing from defect': b[1][0]})
            toadd = await self.additional(idx)
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
    # def test_variable(self, type_):
    #     return [[l1, [a1, x1, y1, z1]] for [l1, [a1, x1, y1, z1]] in enumerate([l for l in type_ if l != []])]
    async def diff(self, b, d, diff):
        if self.indicator[0] == 'vacancy':
            b_, d_ = vacancy(self.bk_, self.def_).diff(b, d, diff)
        elif self.indicator[0] == 'interstitial':
            b_, d_ = interstitial(self.bk_, self.def_).diff(b, d, diff)
        return b_, d_
    async def ne_satisfied(self, idx, b, d, diff):
        toadd = str(idx) if self.indicator[-1] != 'vacancy' else [i for i in await self.additional(idx)]
        self.diff_atoms.append(toadd) if self.indicator[-1] != 'vacancy' else self.diff_atoms.extend(
            toadd)
        self.atoms_dict.append({toadd: d[1][0]}) if self.indicator[-1] != 'vacancy' else self.atoms_dict.extend(
            [{str(idx + ' missing from defect'): b[1][0]}, *[{str(i) : self.def_[i][0]} for i in toadd]])
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
    # def test_variable(self, type_):
    #     return [[l1, [a1, x1, y1, z1]] for [l1, [a1, x1, y1, z1]] in enumerate([l for l in type_ if l != []])]
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
