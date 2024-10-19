#!/usr/bin/env python3

from pymatgen.core.structure import Structure
import warnings

from Core.DictsAndLists import defect_type

__all__ = {}

# think about putting wrapper on function.
async def create_structure(atoms, x, y, z, A, B, C):
    matrix = []
    for x_, y_, z_ in zip(list(x), list(y), list(z)):
        matrix.append([x_, y_, z_])
    warnings.filterwarnings('ignore', '.*CrystalNN.*', )
    warnings.filterwarnings('ignore', '.*No oxidation.*', )
    structure = Structure([A, B, C], atoms, matrix, 0, to_unit_cell=True, coords_are_cartesian=True)
    return structure


class DefineDefType:

    def __init__(self, ):
        i= 9

