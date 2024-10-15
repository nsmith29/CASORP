#!/usr/bin/env python3

import asyncio


__all__ = {'xyz', 'find_xyz', 'make_xyz'}

async def xyz(line, index, lines, funcs, path):
    if index[-1] == '0':
        result = await eval("{}".format(funcs[0]))(line)
    elif index[-1] == '1':
        result = await eval("{}".format(funcs[1]))(lines, index[0], path)
    return result

async def find_xyz(line):
    xyz_name = [str(var[1]) for var in enumerate(line.split()) if var[0] in [1]][0]
    if xyz_name.find('/'):
        xyz_name = xyz_name.split('/')[-1]
    await asyncio.sleep(0.01)
    return xyz_name

async def make_xyz(lines, index, os_path):
    indx, readlines, filename = index - 2, [], '/'.join(os_path.split('/')[:-1] + ["geometry.xyz"])
    # write new file and create counter for total number of atoms.
    xyz_file, atoms = open(filename, 'w'), 0
    # if line contains "&COORD", xyz atom positions finished,
    while "&COORD" not in lines[indx]:
        atoms += 1
        readlines.insert(0, lines[indx])
        indx -= 1
    # insert standard xyz file 1st line into lines for writing to new file.
    readlines.insert(0, f"     {atoms}\n\n")
    for string in readlines:
        xyz_file.write(str(string))
    xyz_file.close()
    await asyncio.sleep(0.01)
    return filename.split('/')[-1]