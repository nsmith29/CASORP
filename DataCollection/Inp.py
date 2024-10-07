#!/usr/bin/env python3

import sys

from Core.DictsAndLists import inp_var_fo, inp_want
from Core.CentralDefinitions import SaveProperties
from DataCollection.FromFile import Iterate, Update

__all__ = {}

class xyz1st(SaveProperties, Update):

    def __init__(xyz, v2rtn, indx, os_path, varitem):
        xyz.all_kinds, xyz.v2rtn, xyz.indx = [], v2rtn, indx
        SaveProperties.__init__(xyz)
        xyz.os_path, xyz.varitem = os_path, varitem
        Update.__init__(xyz, xyz.varitem)
        xyz.searching(xyz, xyz.os_path, xyz.varitem, 'lines', 'index')

        Update.reset(xyz)

    @Iterate
    def searching(xyz, varitem, ln, lines):
        # print('varitem', varitem, 'ln', ln, 'lines', lines, '\n', '[DC.I L24]')
        if varitem["locate"] in ln and varitem["found"] is False:
            index = lines.index(ln) - len(lines) + 1 if varitem["reverse"] is False else lines.index(ln)
            Update.found(xyz)
            key = str(varitem["via"])
            if varitem["swapped"] is True:
                eval(str("xyz.{}(lines, index)".format(key)))
            else:
                eval(str("xyz.{}(ln)".format(key)))

        if varitem["check"] in ln and varitem["found"] is False:
            Update.switch(xyz)

        return varitem


    def find_xyz(xyz, line):
        xyz_name = [str(var[1]) for var in enumerate(line.split()) if var[0] in [1]][0]
        if xyz_name.find('/'):
            xyz_name = xyz_name.split('/')[-1]
        xyz.v2rtn.append(xyz_name)

    def make_xyz(xyz, lines, index):
        # index of line above in self.lines, derival of path of xyz file in same directory as .inp file of self.os_path.
        indx, readlines, filename = index - 2, [], '/'.join(xyz.os_path.split('/')[:-1] + ["geometry.xyz"])
        xyz_file, atoms = open(filename, 'w'), 0  # write new file and create counter for total number of atoms.
        while "&COORD" not in lines[indx]:  # if line contains "&COORD", xyz atom positions finished,
            atoms += 1
            readlines.insert(0, lines[indx])
            indx -= 1
        readlines.insert(0, f"     {atoms}\n\n")  # insert standard xyz file 1st line into lines for writing to new file.
        for string in readlines:
            xyz_file.write(str(string))
        xyz_file.close()

        xyz.v2rtn.append(filename.split('/')[-1])  # append just name of newly written xyz file