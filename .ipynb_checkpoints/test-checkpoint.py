#!/usr/bin/env python3

import asyncio
from asgiref.sync import sync_to_async, async_to_sync 
import concurrent.futures
import numpy as np
import os
import queue
from shared_memory_dict import SharedMemoryDict
import subprocess
import sys
import threading as th
import time

## DictsAndLists.py

multiplefiles4extension = [".txt", ".png", "1-1_l.cube", "2-1_l.cube", ".wfn", ".dat", ".pdos", ".log", '-L.xyz']

questions = {
    "CaSQ1": "\n{bcolors.QUESTION}Would you like to process {bcolors.METHOD}charge and spin data for only atoms related to defect{bcolors.QUESTION}, i.e. nearest neighbouring atoms to defect site and defect atom, if present?({bcolors.OPTIONS}Y/N{bcolors.QUESTION}){bcolors.EXTRA}\nSelecting {bcolors.OPTIONS}'N'{bcolors.EXTRA} will result in charge and spins being processed for all atoms within a calculation:",
    "CaSQ2": "\n{bcolors.QUESTION}Would you like to continue with {bcolors.METHOD}Bader charge analysis {bcolors.QUESTION}for the found subdirectories which do contain the required files for this charge analysis method?({bcolors.OPTIONS}Y/N{bcolors.QUESTION}){bcolors.EXTRA}\n{bcolors.METHOD}Mulliken and Hirshfeld analysis {bcolors.EXTRA}will still be performed for all found subdirectories. Selecting {bcolors.OPTIONS}'Y'{bcolors.EXTRA} will result in extra datatable columns of {bcolors.METHOD}Bader analysis {bcolors.EXTRA}data for calculations which {bcolors.METHOD}Bader analysis {bcolors.EXTRA}can be \nperformed for:"}

files4res = {
    "band structure": {
        "cp2k_outputs": {"defect": [".log"
            , ".bs"]}
        , "intermediary": {"defect": [".bs.set-1.csv"]}
        , "final_output": [".bs.png"]},
    "charges and spins": {
        "only":
            {"cp2k_outputs": {"perfect": ["-L.xyz"]
                , "defect": [".inp"
                    , "''.xyz"]}}
        , "bader":
            {"cp2k_outputs": {"perfect": ["ELECTRON_DENSITY-1_0.cube"]
                , "defect": ["-ELECTRON_DENSITY-1_0.cube"]}
                , "intermediary": {"perfect": ["ACF.dat"]
                , "defect": ["ACF.dat"]}}
        , "standard":
            {"cp2k_outputs": {"perfect": [".log"]
                , "defect": [".log"]}}
        , "final_output": {"charges.txt"}},
    "charge transition levels": {
        "cp2k_outputs": {"perfect": [".log"]
            , "defect": [".log"]
            , "chem_pot": [".log"]}
        , "final_output": [".clt.png"]},
    "geometry": {
        "defect defining":
            {"cp2k_outputs": {"perfect": ["-L.xyz"]
                , "defect": [".inp"
                    , "''.xyz"]}}
        , "standard":
            {"cp2k_outputs": {"perfect": ["-1.xyz"
                                          ".log"]
                , "defect": ["-1.xyz"
                    , ".log"]}
                , "intermediary": {"perfect": ["-L.xyz"]
                , "defect": ["-L.xyz"]}}
        , "final_output": [".distVdisp.png", "BondLenAng.txt"]},
    "IPR": {
        "cp2k_outputs": {"perfect": []

            , "defect": []}
        , "final_output": []},
    "PDOS": {
        "cp2k_outputs": {"perfect": []
            , "defect": []}
        , "intermediary": {"perfect": []
            , "defect": []}
        , "final_output": []},
    "WFN": {
        "cp2k_outputs": {"perfect": []
            , "defect": []}
        , "intermediary": {"perfect": []
            , "defect": []}
        , "final_output": []},
    "work function": {
        "cp2k_outputs": {"perfect": []
            , "defect": []}
        , "intermediary": {"perfect": []
            , "defect": []}
        , "final_output": []}}

restrictions = {"geometry": "'energy' not in entry"}

functions = {"charges and spins": "BaderFileCreation",
             "Geometry": "GeometryLastCreation"}

inp_want = {"charges and spins": [
                "xyz1st"],
            "geometry": [
                "xyz1st"]}

inp_var_fo = {"xyz1st":{
                   "locate": ['COORD_FILE_NAME', "&END COORD", ['find_xyz', "make_xyz"]], "via": "xyz", "check": "&TOPOLOGY", "reverse": False, "kwargs": ['index={indx}', 'lines={lines_}']}}

log_want = {"band structure": ["version"],
            "charges and spins": ["pop1", "pop2"],
            "charge transition levels": ["charge", "energy", "knd_atms"],
            "geometry": ["a"],
            "original": ["name", "run", "charge"],
            "all":["a", "at_crd", "charge", "energy", "gap", "knd_atms", "name", "pop1", "pop2", "run", "version"],
            "test":["at_crd"]}

log_var_fo = {"a":{"locate": '|a|', "via": "find_a", "reverse": True, "kwargs":['index={indx}', 'lines={lines_}']},
              
              "at_crd":{"locate": "MODULE QUICKSTEP:  ATOMIC COORDINATES IN angstrom", "via": "find_at", "reverse": True, "kwargs":['index={indx}', 'lines={lines_}']},
              
              "charge":{"locate": " DFT| Charge", "via": "find_charge", "reverse": False, "kwargs":['_={indx}']},
              
              "energy":{"locate": "ENERGY| Total FORCE_EVAL", "via": "find_energy", "reverse": False, "kwargs":['_={indx}']},
              
              "gap":{"locate": "HOMO - LUMO gap", "via": "find_gap", "reverse": False, "kwargs":['index={indx}', 'lines={lines_}']},
              
              "knd_atms":{"locate": ["Atomic kind"], "via": "find_kind",  "reverse": False, "kwargs":['_={indx}']},
              
              "name":{"locate": " GLOBAL| Project name", "via": "find_name", "reverse": False, "kwargs":['_={indx}']},
              
              "pop1":{"locate": ["Total charge and spin", "Mulliken Population Analysis"], "via": "find_pop1", "n" : 1, "num": None, "reverse": False, "kwargs": ['index={indx}', 'lines={lines_}']},
              
              "pop2":{"locate": ["Total Charge", 'Hirshfeld Charges'], "via": "find_pop2",  "n" : 2, "num": None, "reverse": False, "kwargs": ['index={indx}', 'lines={lines_}', 'path={os_path}']},
              
              "run":{"locate": " GLOBAL| Run type", "via": "find_run", "reverse": False, "kwargs":['_={indx}']},
              
              "version":{"locate": " CP2K| version string:", "via": "find_version", "reverse": False, "kwargs":['_={indx}']}}

## CentralDefinitions

boolconvtr = {'Y': True, 'N': False}

class CreateSharableDicts:
    def __init__(self, name, dict):
        SharableDicts().smd[name] = dict
        SharableDicts().smd.shm.close()
        
class Userwants:
    def __init__(self):
        self._analysiswants, self._displaywants, self._append, self._overwrite = True, True, None, None
    @property
    def analysiswants(self):
        return self._analysiswants
    @property
    def displaywants(self):
        return self._displaywants
    @property
    def append(self):
        return [item for key, item in boolconvtr.items() if item is not self.overwrite][
            0] if self.overwrite is not None else None
    @property
    def overwrite(self):
        return self._overwrite

class UArg:
    def __init__(self):
        self._cwd, self._perfd, self._defd, self._cptd, self._subd, self._fdsd = '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0', '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/bulk_structure', '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined', '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/chem_pot', [
            'O_Cc1Al_Sic1'], {}
        self._expt, self._only = False, True
    @property
    def cwd(self):
        return self._cwd
    @property
    def perfd(self):
        return self._perfd
    @property
    def defd(self):
        return self._defd
    @property
    def cptd(self):
        return self._cptd
    @property
    def subd(self):
        return self._subd
    @property
    def fdsd(self):
        if self._fdsd == {}:
            for sub in self.subd:
                self._fdsd[str(sub)] = False
        else:
            self._fdsd = self._fdsd
        return self._fdsd
    @property
    def expt(self):
        return True if self.subd != [] and self.only is False else False
    @property
    def only(self):
        return self._only

class TESTING:
    def __init__(self):
        self._in_progress = False
    @property
    def in_progress(self):
        return self._in_progress
    @in_progress.setter
    def in_progress(self, bool):
        self._in_progress = bool

class SharableDicts:
    def __init__(self):
        self._smd = SharedMemoryDict("CASORP", size=1024)
    @property
    def smd(self):
        return self._smd

class ProcessCntrls:
    def __init__(self):
        self._processwants, self._setup, self._processresults = ['charges and spins'], None, {"perfect": dict(),
                                                                                              "defect": dict()}
    @property
    def processwants(self):
        return self._processwants
    @property
    def setup(self):
        return [f"results for {item}" for item in self.processwants]
    @property
    def processresults(self):
        return self._processresults

class Dirs:
    def __init__(self):
        self._address_book = {'perfect': {
            '7x4x1_SiC_GEO_OPT': {
                'GEO_OPT': {
                    0: {
                        'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/bulk_structure',
                        'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/bulk_structure/7x4x1_SiC_GEO_OPT.log'}}}},
            'defect': {
                'PBE0_4H-SiC_w_O_Cc1Al_Sic1': {
                    'GEO_OPT': {
                        '2+': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/positive2',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/positive2/VHC_PBE0_GEO_OPT.log'},
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/neutral/VHC_PBE0_GEO_OPT.log'},
                        '1+': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/positive1',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/positive1/VHC_PBE0_GEO_OPT.log'},
                        '1-': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/negative1',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/negative1/VHC_PBE0_GEO_OPT.log'}},
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/Koopmans',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/Koopmans/KoopmansENERGY.log'}}},
                'O_Cc1Al_Sic1_Q1.2_ENERGY': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q1.2/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q1.2/neutral/Neu__Q1.2_ENERGY.log'},
                        '1-': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q1.2/negative1',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q1.2/negative1/Neg_Q1.2_ENERGY.log'}}},
                'O_Cc1Al_Sic1_Q_0.4_ENERGY': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_0.4/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_0.4/neutral/Neu_Q_0.4_ENERGY.log'},
                        '1-': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_0.4/negative1',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_0.4/negative1/Neg_Q_0.4_ENERGY.log'}}},
                'O_Cc1Al_Sic1_Q3.0_ENERGY': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q3.0/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q3.0/neutral/Neu_Q3.0_ENERGY.log'}}},
                'O_Cc1Al_Sic1_Q_2.0_ENERGY': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_2.0/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_2.0/neutral/Neu_Q_2.0_ENERGY.log'},
                        '1-': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_2.0/negative1',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_2.0/negative1/Neg_Q_2.0_ENERGY.log'}}},
                'O_Cc1Al_Sic1_Q0.8_ENERGY': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q0.8/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q0.8/neutral/Neu__Q0.8_ENERGY.log'},
                        '1-': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q0.8/negative1',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q0.8/negative1/Neg_Q0.8_ENERGY.log'}}},
                'O_Cc1Al_Sic1_Q2.4_ENERGY': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q2.4/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q2.4/neutral/Neu_Q2.4_ENERGY.log'}}},
                'O_Cc1Al_Sic1_Q_0.8_ENERGY': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_0.8/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_0.8/neutral/Neu_Q_0.8_ENERGY.log'},
                        '1-': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_0.8/negative1',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q_0.8/negative1/Neg_Q_0.8_ENERGY.log'}}},
                'O_Cc1Al_Sic1_Q1.6_ENERGY': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q1.6/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q1.6/neutral/Neu__Q1.6_ENERGY.log'},
                        '1-': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q1.6/negative1',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q1.6/negative1/Neg_Q1.6_ENERGY.log'}}},
                'O_Cc1Al_Sic1_Q2.8_ENERGY': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q2.8/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q2.8/neutral/Neu_Q2.8_ENERGY.log'}}},
                'O_Cc1Al_Sic1_Q0.4_ENERGY': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q0.4/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q0.4/neutral/Neu__Q0.4_ENERGY.log'},
                        '1-': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q0.4/negative1',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q0.4/negative1/Neg_Q0.4_ENERGY.log'}}},
                'O_Cc1Al_Sic1_Q2.0_ENERGY': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q2.0/neutral',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q2.0/neutral/Neu_Q2.0_ENERGY.log'},
                        '1-': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q2.0/negative1',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/energy/adiabatic_potentials_/Q2.0/negative1/Neg_Q2.0_ENERGY.log'}}},
                'PBE0_IPR_4H-SiC_w_O_Cc1Al_Sic1': {
                    'ENERGY': {
                        0: {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/neutral/IPR',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/neutral/IPR/IPR_PBE0_ENERGY2.log'}}},
                'O_Cc1Al_Sic1_neg_0GEO_ENERGY': {
                    'ENERGY': {
                        '1-': {
                            'path': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/negative1/geometry/relaxationE',
                            'log': '/Users/appleair/Desktop/PhD/Jupyter_notebooks/Calculations/PBE0_impurities_analysis/Only_PBE0/test_combined/Al-O-Al/O_Cc1Al_Sic1/negative1/geometry/relaxationE/Neg_0GEO_ENERGY.log'}}}}}
        self._dir_calc_keys = {'perfect': [['7x4x1_SiC_GEO_OPT', 'GEO_OPT', 0]],
                               'defect': [['PBE0_4H-SiC_w_O_Cc1Al_Sic1', 'GEO_OPT', '2+'],
                                          ['O_Cc1Al_Sic1_Q1.2_ENERGY', 'ENERGY', 0],
                                          ['O_Cc1Al_Sic1_Q1.2_ENERGY', 'ENERGY', '1-'],
                                          ['O_Cc1Al_Sic1_Q_0.4_ENERGY', 'ENERGY', 0],
                                          ['O_Cc1Al_Sic1_Q_0.4_ENERGY', 'ENERGY', '1-'],
                                          ['O_Cc1Al_Sic1_Q3.0_ENERGY', 'ENERGY', 0],
                                          ['O_Cc1Al_Sic1_Q_2.0_ENERGY', 'ENERGY', 0],
                                          ['O_Cc1Al_Sic1_Q_2.0_ENERGY', 'ENERGY', '1-'],
                                          ['O_Cc1Al_Sic1_Q0.8_ENERGY', 'ENERGY', 0],
                                          ['O_Cc1Al_Sic1_Q0.8_ENERGY', 'ENERGY', '1-'],
                                          ['O_Cc1Al_Sic1_Q2.4_ENERGY', 'ENERGY', 0],
                                          ['O_Cc1Al_Sic1_Q_0.8_ENERGY', 'ENERGY', 0],
                                          ['O_Cc1Al_Sic1_Q_0.8_ENERGY', 'ENERGY', '1-'],
                                          ['O_Cc1Al_Sic1_Q1.6_ENERGY', 'ENERGY', 0],
                                          ['O_Cc1Al_Sic1_Q1.6_ENERGY', 'ENERGY', '1-'],
                                          ['O_Cc1Al_Sic1_Q2.8_ENERGY', 'ENERGY', 0],
                                          ['O_Cc1Al_Sic1_Q0.4_ENERGY', 'ENERGY', 0],
                                          ['O_Cc1Al_Sic1_Q0.4_ENERGY', 'ENERGY', '1-'],
                                          ['O_Cc1Al_Sic1_Q2.0_ENERGY', 'ENERGY', 0],
                                          ['O_Cc1Al_Sic1_Q2.0_ENERGY', 'ENERGY', '1-'],
                                          ['PBE0_4H-SiC_w_O_Cc1Al_Sic1', 'ENERGY', 0],
                                          ['PBE0_4H-SiC_w_O_Cc1Al_Sic1', 'GEO_OPT', 0],
                                          ['PBE0_IPR_4H-SiC_w_O_Cc1Al_Sic1', 'ENERGY', 0],
                                          ['PBE0_4H-SiC_w_O_Cc1Al_Sic1', 'GEO_OPT', '1+'],
                                          ['PBE0_4H-SiC_w_O_Cc1Al_Sic1', 'GEO_OPT', '1-'],
                                          ['O_Cc1Al_Sic1_neg_0GEO_ENERGY', 'ENERGY', '1-']]}
        self._executables_address = '/Users/appleair/CASORP/Executables'
    @property
    def address_book(self):
        return self._address_book
    @address_book.setter
    def address_book(self, dict):
        self._address_book = dict
    @property
    def dir_calc_keys(self):
        return self._dir_calc_keys
    @dir_calc_keys.setter
    def dir_calc_keys(self, dict):
        self._dir_calc_keys = dict
    @property
    def executables_address(self):
        return self._executables_address

class Ctl_Settings:
    def __init__(self):
        self._defining_except_found = None
        self._e2_defining, self._i_define = {"perfect": [], "defect": []}, {"defect": []}
    @property
    def defining_except_found(self):
        return self._defining_except_found
    @defining_except_found.setter
    def defining_except_found(self, bool):
        self._defining_except_found = bool
    @property
    def e2_defining(self):
        return self._e2_defining
    @e2_defining.setter
    def e2_defining(self, dict):
        self._e2_defining = dict
    @property
    def i_defining(self):
        return self._i_define
    @i_defining.setter
    def i_defining(self, dict):
        self._i_define = dict

class CaS_Settings:
    def __init__(self):
        self._nn_and_def, self._cont_bdr = None, None
        self._bader_missing, self._bader_break, self._dirs_missing_bader = None, None, {"perfect": [], "defect": []}
    @property
    def nn_and_def(self):
        return self._nn_and_def
    @nn_and_def.setter
    def nn_and_def(self, bool):
        self._nn_and_def = bool
    @property
    def cont_bdr(self):
        return self._cont_bdr
    @cont_bdr.setter
    def cont_bdr(self, bool):
        self._cont_bdr = bool
    @property
    def bader_missing(self):
        return self._bader_missing
    @bader_missing.setter
    def bader_missing(self, bool):
        self._bader_missing = bool
    @property
    def bader_break(self):
        return self._bader_break
    @bader_break.setter
    def bader_break(self, bool):
        self._bader_break = bool
    @property
    def dirs_missing_bader(self):
        return self._dirs_missing_bader
    @dirs_missing_bader.setter
    def dirs_missing_bader(self, dict):
        self._dirs_missing_bader = dict
        
def savekeys(func):
    def wrapper(keys, subkeys, paths, d1, d2=None, name=None, *args):
        d1 = func(keys, subkeys, paths, d1)
        if name:
            CreateSharableDicts(name[0], d1)
        if d2 is not None:
            assert isinstance(d2, dict), "d2 must be a dictionary which can be populated with list of keys"
            assert keys[0] in d2.keys(), "First str item in keys must be a key within d2"
            if not d2[keys[0]]:
                d2[keys[0]] = [keys[1:]]
            elif len(keys) == 4 and [keys[1], keys[2], keys[3]] not in d2[keys[0]] or len(keys) == 5 and [keys[1], keys[2], keys[3], keys[4]] not in d2[keys[0]]:
                d2[keys[0]].append(keys[1:])
            if name:
                CreateSharableDicts(name[1], d2)
        return d1, d2
    return wrapper

@savekeys
def create_nested_dict(keys, subkeys, paths, d):
    assert isinstance(keys, list), "keys must be a list of major outer nested dict keys strs"
    assert isinstance(subkeys, list), "subkeys must be a list of minor inner nested keys strs"
    assert isinstance(paths, list), "path must be a list of os.path() file path strs"
    assert isinstance(d, dict), "d must be a dictionary which can be populated with keys, subkeys, and paths"
    assert keys[0] in d.keys(), "First str item in keys must be a key within d"
    d_, ks = {keys[0]: d[keys[0]]}, ''
    for indx, key in enumerate(keys):
        d__ = eval("d_{}".format(ks))
        if key in eval("d_{}".format(ks)) and key == keys[-1]:
            k_ = [k for k, v in d__.items()][0]
            for sub, path in zip(subkeys, paths):
                if str("{} : {}".format(sub, path)) not in d__[k_]:
                    d__[k_][sub] = path
        if key not in eval("d_{}".format(ks)):
            if d__ == {}:
                _d = {sub: path for sub, path in zip(subkeys, paths)} if key == keys[-1] else {}
                d__ = {key: _d}
            else:
                d__[key] = {}
                if key == keys[-1]:
                    for sub, path in zip(subkeys, paths):
                        d__[key][sub] = path
            exec(f"d_{ks} = d__ ")
        ks = ks + str("['{}']".format(key))
        d.update({keys[0]: d_[keys[0]]})
    return d

@savekeys
def proxyfunction(keys, subkeys, path, d):
    pass

## Messages

class bcolors:
    KEYVAR = '\033[95m'  # was HEADER
    QUESTION = '\x1b[38;5;135m'
    QUESTION2 = '\x1b[38;5;99m'
    EXTRA = '\033[38;5;27m'
    OPTIONS = '\033[96m'  # was OKCYAN
    CHOSEN = '\x1b[38;5;50m'
    METHOD = '\033[38;5;147m'
    INFO = '\x1b[38;5;221m'
    ACTION = '\033[93m'
    WARN4 = '\033[33m'
    KEYINFO = '\x1b[38;5;220m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'

class linewidth:
    def __init__(self, message):
        # Split string into list at "{" instances.
        message, j = message.split("{"), 0
        for item in message:
            if "}" in item:
                indx, new = message.index(item), [newitem for newitem in item.split("}")]
                message.remove(item)
                [message.insert(indx + idx, n) for idx, n in zip(range(len(new)), new)]
        for indx, item in enumerate(message):
            if "bcolors" not in item and len(item) != 0:
                if "\n" in item:
                    j = 0 + len(item)
                else:
                    j += len(item)
                if j > 110:
                    k, o = 110 - j, [i for i in item]
                    try:
                        while o[k] != ' ':
                            k -= 1
                        o.insert(k + 1, "\n")
                    except IndexError:
                        o.insert(0, "\n")
                    message.remove(item)
                    message.insert(indx, "".join(o))
                    j = j + k - 110
                if j == 110:
                    # reset j back to 0 if at 110.
                    j = j - 110
            if "bcolors" in item:
                # remove inactive bcolors calls
                message.remove(item)
                # replace with active bcolors calls.
                message.insert(indx, str("{}".format(eval("{}".format(item)))))
        # add final reset of color & newline
        message.extend([str("{}".format(eval("{}".format('bcolors.ENDC')))), "\n"])
        message = "".join(message)
        self.message = str(message)
    def Return(self):
        return self.message

class SlowMessageLines(linewidth):
    def __init__(self, message, lock=None):
        super().__init__(message)
        lines = self.message.splitlines()
        # text to be printed is within a multithreading environment.
        if lock:
            with lock:
                self.Print(lines)
        else:
            self.Print(lines)
    def Print(self, lines):
        for line in lines:
            time.sleep(0.75)
            print(f"{line}[code L398]")

class Global_lock:
    def __init__(self):
        self._lock = th.Lock()
    @property
    def lock(self):
        return self._lock

class ErrMessages:
    def __init__(self, f):
        self._f = f
    @staticmethod  # √
    def ValueErrorYorN(lock=None):
        text = str("\n{bcolors.FAIL}WARNING:{bcolors.UNDERLINE}Invalid answer given!{bcolors.ENDC}{bcolors.KEYINFO} "
                   "\nOnly valid answers are {bcolors.OPTIONS}Y {bcolors.ACTION}and {bcolors.OPTIONS}N"
                   "{bcolors.KEYINFO}.{bcolors.ACTION}Try again.  ")
        SlowMessageLines(text)
    @staticmethod
    def FileSearch_LookupError(extension, subdirectory, method=None):
        dirpath = '/'.join([directory for directory in str(subdirectory).split('/') if directory not in
                            str(UArg.cwd).split('/')])
        text = str("\n{bcolors.FAIL}Error: {bcolors.UNDERLINE}Multiple files of the same file extension "
                   "{bcolors.ENDC}{bcolors.KEYVAR}'"
                   + f"{extension}"
                   + "'{bcolors.FAIL}{bcolors.UNDERLINE}have been unexpectedly found within directory "
                     "{bcolors.ENDC}{bcolors.KEYVAR}"
                   + f"{dirpath}"
                   + "{bcolors.FAIL}.{bcolors.KEYINFO}\nThis code is not designed to handle multiple files with this "
                     "particular extension being located in the same file directory.{bcolors.ACTION}\nPlease separate "
                     "files based on each individual calculation they belong to, or if some of files with this extension"
                     " are older/disregardable versions of the file extension for the same calculation, please rename "
                     "their file extensions to {bcolors.ITALIC}{bcolors.KEYVAR}"
                   + f"{extension}"
                   + ".old{bcolors.ACTION}.")
        if method:
            method = str(method).upper()
            text = str(text
                       + "\n                                      {bcolors.METHOD}{bcolors.UNDERLINE}ENDING "
                       + f"{method}"
                       + "PROCESSING{bcolors.ENDC}{bcolors.METHOD}...")
        return linewidth(text).Return()
    @staticmethod
    def FileSearch_FileNotFoundError1(key, lock=None):
        path, cwd = str(UArg.defd).split('/'), str(UArg.cwd).split('/')
        dirpath = '/'.join([directory for directory in path if directory not in cwd])
        text = str("\n{bcolors.FAIL}ERROR: {bcolors.UNDERLINE}[Errno 2] No subdirectory {bcolors.BOLD}{bcolors.KEYVAR}"
                   "'" + f"{key}"
                   + "'{bcolors.ENDC}{bcolors.FAIL}{bcolors.UNDERLINE} found in parent directory:{bcolors.ENDC} "
                     "{bcolors.KEYVAR}'"
                   + f"{dirpath}"
                   + "'{bcolors.FAIL}.{bcolors.INFO}\n"
                   + "Use of key word '{bcolors.CHOSEN}{bcolors.ITALIC}{bcolors.BOLD}only{bcolors.ENDC}"
                     "{bcolors.INFO}' requires all arguments given after '{bcolors.CHOSEN}{bcolors.ITALIC}"
                     "{bcolors.BOLD}only{bcolors.ENDC}{bcolors.INFO}' to be names of subdirectories within the "
                     "{bcolors.KEYVAR}{bcolors.ITALIC}"
                   + f"{str(UArg.defd).split('/')[-1]}"
                   + "{bcolors.ENDC}{bcolors.INFO} parent directory. {bcolors.ENDC}{bcolors.ACTION} \nSpaces or dashes "
                     "within a directories name are not permitted. Rename directory to remove spaces/dashes if present "
                     "in name(s) before rerunning.")
        SlowMessageLines(text, lock)
    @staticmethod
    def FileSearch_FileNotFoundError2(key, lock=None):
        path, cwd = str(UArg.defd).split('/'), str(UArg.cwd).split('/')
        dirpath = '/'.join([directory for directory in path if directory not in cwd])
        text = str(
            "\n{bcolors.FAIL}WARNING: {bcolors.UNDERLINE}[Errno 2] No subdirectory {bcolors.BOLD}{bcolors.KEYVAR}"
            "'" + f"{key}"
            + "'{bcolors.ENDC}{bcolors.FAIL}{bcolors.UNDERLINE} found in parent directory:{bcolors.ENDC} "
              "{bcolors.KEYVAR}'"
            + f"{dirpath}"
            + "'{bcolors.FAIL}.{bcolors.KEYINFO}\n"
            + "Use of key word '{bcolors.CHOSEN}{bcolors.ITALIC}{bcolors.BOLD}only{bcolors.ENDC}{bcolors.KEYINFO}"
              "' requires all arguments given after '{bcolors.CHOSEN}{bcolors.ITALIC}{bcolors.BOLD}only"
              "{bcolors.ENDC}{bcolors.KEYINFO}' to be names of subdirectories within the {bcolors.KEYVAR}"
              "{bcolors.ITALIC}"
            + f"{str(UArg.defd).split('/')[-1]}"
            + "{bcolors.ENDC}{bcolors.KEYINFO} parent directory. {bcolors.ENDC}{bcolors.ACTION}\n"
            + "Spaces or dashes within a directories name are not permitted. Rename directory to remove "
              "spaces/dashes if present in name before rerunning with corrected name for {bcolors.BOLD}"
              "{bcolors.KEYVAR}'"
            + f"{key}"
            + "'{bcolors.ENDC}{bcolors.ACTION} subdirectory.")
        SlowMessageLines(text, lock)
    @staticmethod
    def FileSearch_FileNotFoundError3(keywrd, name, run, charge, filetypes, lock=None):
        print("\n")
        if type(filetypes) != list:
            filetypes = [filetypes]
        for fltyp in filetypes:
            text = str("{bcolors.FAIL}WARNING: {bcolors.UNDERLINE}[Errno 2]{bcolors.ENDC}{bcolors.FAIL} CP2K output "
                       "file type {bcolors.BOLD}{bcolors.KEYVAR}'"
                       + f"{fltyp}"
                       + "'{bcolors.ENDC}{bcolors.FAIL} needed for the {bcolors.METHOD}"
                       + f"{keywrd}"
                       + " processing{bcolors.ENDC}{bcolors.FAIL} method could not be found in the {bcolors.KEYVAR}"
                       + f"{run}"
                       + "{bcolors.ENDC}{bcolors.FAIL} directory for the {bcolors.KEYVAR}"
                       + f"{charge}"
                       + "{bcolors.ENDC}{bcolors.FAIL} charge state of {bcolors.KEYVAR}"
                       + f"{name}"
                       + "{bcolors.ENDC}{bcolors.FAIL}.")
            SlowMessageLines(text, lock)
        text = str("{bcolors.ACTION}Processing for the {bcolors.METHOD}"
                   + f"{keywrd}"
                   + "{bcolors.ENDC}{bcolors.ACTION} method will continue for found subdirectories which contain all "
                     "required filetypes for the method.")
        SlowMessageLines(text, lock)
    @staticmethod
    def CaS_ConnectionAbortedError(path, lock=None):
        path, cwd = str(path).split('/'), str(UArg.cwd).split('/')
        dirpath = '/'.join([directory for directory in path if directory not in cwd])
        text = str("\n{bcolors.FAIL}WARNING: {bcolors.UNDERLINE}[Errno 2]{bcolors.ENDC}{bcolors.FAIL} Needed "
                   "{bcolors.KEYVAR}'-ELECTRON_DENSITY-1_0.cube'{bcolors.ENDC}{bcolors.FAIL} file for {bcolors.METHOD}"
                   "analysis of Bader charges of atoms{bcolors.ENDC}{bcolors.FAIL} could not be found within the "
                   "given directory for perfect, defect-free material CP2K output files:{bcolors.KEYVAR} "
                   + f"{dirpath}"
                   + "{bcolors.KEYINFO} \nSubsequently, {bcolors.METHOD}Bader charge analysis{bcolors.ACTION}"
                     " cannot be completed at all for results. {bcolors.METHOD}Mulliken and Hirshfeld analysis"
                     "{bcolors.KEYINFO} will, however, still be performed for all results found.")
        SlowMessageLines(text, lock)
    @staticmethod
    def CaS_FileNotFoundError(MissingFiles, filetypes, method, lock=Global_lock().lock):
        text = str("\n{bcolors.FAIL}WARNING: {bcolors.UNDERLINE}[Errno 2]{bcolors.ENDC}{bcolors.FAIL} Needed "
                   "{bcolors.KEYVAR}'"
                   + f"{filetypes}"
                   + "'{bcolors.ENDC}{bcolors.FAIL} file(s) for {bcolors.METHOD}"
                   + f"{method}"
                   + "{bcolors.ENDC}{bcolors.FAIL} could not be found within the "
                     "following directories for:")
        SlowMessageLines(text, lock)
        time.sleep(0.75)
        for dir in MissingFiles:
            text = str("{bcolors.KEYVAR}- " + f"{dir[-1]} " + "{bcolors.ENDC}")
            SlowMessageLines(text, lock)
    @staticmethod
    def Geometry_FileExistsError():
        text = str("\n{bcolors.FAIL}ERROR: {bcolors.UNDERLINE} Too many ")

class Stdin_Applied:
    def __init__(self):
        self._applied = False
    @property
    def applied(self):
        return self._applied
    @applied.setter
    def applied(self, bool):
        self._applied = bool

def checkinput(func):
    def wrapper(Q, typ, ans, **kwargs) -> str:
        if Stdin_Applied().applied is False:
            sys.stdin = open(0)
            Stdin_Applied.applied = True
        while True:
            A = func(Q, typ, ans)
            try:
                if isinstance(A, list) == True:
                    if len([a for a in A if a not in ans]) != 0:
                        raise ValueError
                else:
                    if A not in ans:
                        raise ValueError
            except:
                eval("ErrMessages.ValueError{}()".format(typ))
                A = func(Q, typ, ans)
            break
        return A
    return wrapper

@checkinput
def ask_question(Q: str, typ: str, ans: list) -> str:
    _format = {'list': "A.split(', ') if ',' in A else [A]", 'YorN': 'A.upper()'}
    SlowMessageLines(questions[str(Q)])
    A = input()
    # if expected type is list, split string. If expected type is Yes or No, make sure string is upper case.
    A = eval(_format[typ])
    return A

## FileSearch

class Finding:
    def __init__(self, path, extension):
        self.split_path, self.extension, self.layer, self.walk = path.split('/'), extension, 0, os.walk(path)
        self.dirpaths, self.filepaths, self.fnd = [], [], None
    def set_vars(self, bool_, cond_=None):
        if bool_ == True:
            met, layer_met, meet_list, to_meet, indx, num_met, fnd_list = True, 0, None, None, None, None, None
            start, not_ = "", []
        elif bool_ == False:
            met, layer_met, num_met = False, 0, 0
            _, meet_list = ((''.join(cond_.split(")"))).split("(")[0]), eval(
                ((''.join(cond_.split(")"))).split("(")[2]))
            not_ = meet_list if 'not' in _ else []
            to_meet, indx = int(len(meet_list)) if 'not' not in _ else None, None
            num_met, fnd_list = 0 if to_meet > 1 else None, np.empty(to_meet,
                                                                     dtype=bool) if 'not' not in _ and to_meet > 1 else None
        return met, layer_met, not_, num_met, fnd_list, meet_list, to_meet, indx
    def check_num_of_filepaths(self):
        noted_dirpath = ''
        for dir_ in self.dirpaths:
            if dir_ != noted_dirpath:
                noted_dirpath = dir_
            else:
                assert self.extension in multiplefiles4extension, f"{ErrMessages.FileSearch_LookupError(self.extension, noted_dirpath)}"
    def dir_tree_transversing(self, cond="", q_=None):
        met, layer_met, not_, num_met, fnd_list, meet_list, to_meet, indx, = self.set_vars(
            True) if cond == "" else self.set_vars(False, cond)
        if TESTING.in_progress is True:
            print('met =', met, 'extension =', self.extension, '[code 478]')
        layer = {0: {"found": self.split_path[-1], "transversed": []}}
        for (path_, dirs_, files_) in self.walk:
            if TESTING.in_progress is True:
                print('met = ', met, "find =", self.fnd, "layer =", self.layer, "[code L481]")
            if [i for i in path_.split('/') if i in not_]:
                continue
            if self.fnd is True and met is False or self.fnd is False and met is False:  # stops finding directories if fnd is true and met is false
                if type(to_meet) == int and type(num_met) == int:
                    if num_met != to_meet:
                        num_met += 1
                        fnd_list[indx] = self.fnd
                        layer_met, self.fnd = 0, None
                    elif num_met == to_meet:
                        break
                else:
                    if TESTING.in_progress is True:
                        print("should be breaking out of method loop [code L494]")
                    break
            self.layer = len(str(path_).split('/')) - len(self.split_path)
            keys_, met = [key for key in layer.keys() if
                          key > self.layer], False if self.layer != 0 and layer_met > self.layer - 1 else met  # met reset to False if going back in layer num is less than layer num
            [layer.pop(key_) for key_ in keys_]
            layer[int(self.layer + 1)] = {"found": dirs_, "transversed": []} if int(
                self.layer + 1) not in layer.keys() else layer[int(self.layer + 1)]
            if not dirs_ and not files_:
                all_ = [layer[key]["transversed"] == layer[key]["found"] for key in layer.keys()]
                if False not in all_:
                    self.fnd = False
                    met = False
                    break
            elif met is False:
                if eval(cond):
                    met, layer_met = True, self.layer  # set to true when first of directories listed in condition match current path
                    indx = [in_ for in_, i in enumerate(meet_list) if i.endswith(path_.split('/')[-1])][0] if to_meet \
                        else None
            elif met is True:
                for file_ in files_:
                    if file_.endswith(str(self.extension)) and not path_.endswith(".ipynb_checkpoints"):
                        self.dirpaths.append(path_)
                        self.filepaths.append(os.path.join(path_, file_))
                        self.fnd = True  # found all directories and logs for that particular named directory
            end = str(path_).split('/')[-1]
            [layer[self.layer]["transversed"].append(end_) for end_ in [end] if
             end_ in layer[self.layer]["found"] and end_ not in layer[self.layer]["transversed"]]
        if to_meet:
            self.fnd = fnd_list
        else:
            self.fnd = False if self.fnd == None else self.fnd
        if len(self.filepaths) > 1:
            self.check_num_of_filepaths()
            
class async_2FromFiles_iterator():
    def __init__(self, want):
        self.want = want
        self.counter = -1
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.counter >= len(self.want)-1:
            raise StopAsyncIteration
        self.counter +=1
        return self.want[self.counter]    

async def Entry4FromFiles(path, file, keywrd):
    want, var = eval("{}_want[keywrd]".format(file)), eval("{}_var_fo".format(file))
    v2rtn = [iterate(path, var.get(item)) async for item in async_2FromFiles_iterator(want)]
    return await asyncio.gather(*v2rtn) 

class CatalogueFinding(Finding, object):  # Finding needs path and extension.
    def __init__(self, func):
        self.func = func
        self.cats, self.book = None, None  # Dirs().dir_calc_keys.copy(), Dirs().address_book.copy()
        self.errflggd = []
    def definiting(self, base_ext, type_, keywrd=None):
        if keywrd in restrictions.keys():
            self.cats = {type_: [entry for entry in Dirs().dir_calc_keys[type_] if eval(restrictions[keywrd])]}
            print(self.cats, '[code L538]')
        else:
            self.cats = Dirs().dir_calc_keys.copy()
        self.book, self.errflggd = Dirs().address_book.copy(), base_ext
    def __call__(self, self2, type_, fl_exts, section, **kwargs):
        if self.cats == None:
            print(kwargs, type_, fl_exts, '[code 544]')
            self.definiting(fl_exts, type_) if "ignore" in kwargs.keys() else self.definiting(fl_exts, type_,
                                                                                              self2.keywrd)
        for n, r, c in self.cats[type_]:
            Ars = [value for key, value in kwargs.items() if key == 'exchange'] if kwargs else []
            keylst = [type_, n, r, c]
            path, keys, flexts = self.book[type_][n][r][c]["path"], self.book[type_][n][r][c].keys(), []
            [fl_exts.remove(flext_) for flext_ in fl_exts if flext_ in keys]
            Q, pair, flexts, j = queue.Queue(), [section for i in range(len(fl_exts))], fl_exts.copy(), 0
            while j < len(flexts):
                super().__init__(path, flexts[j])
                super().dir_tree_transversing()
                _ = [Ars.insert(0, path) if pair[j] == None else Ars]
                Ars_ = Ars if pair[j] == None else []
                rtn = self.func(self2, keylst, pair[j], flexts[j], self.fnd, self.filepaths, Q,
                                *eval("{}".format(Ars_)))
                while Q.empty() is False:
                    items = Q.get()
                    pair.append(items[0])
                    flexts.append(items[1][0])
                    break
                j += 1
                if rtn == 'continue':
                    j = len(fl_exts) + 1

class Method:  # to be inherited by only spins and msin method get.
    def __init__(self, keywrd, subwrd=None):
        self.keywrd, self.subwrd = keywrd, subwrd
        self.res = files4res[keywrd][subwrd] if not subwrd == None else files4res[keywrd]
        self.out, self.int = "cp2k_outputs", "intermediary"
        inner_dict = self.res[self.int] if self.int in self.res.keys() else self.res[self.out]
        self.types, self.flexts_ = [key for key, value in inner_dict.items()], [value for key, value in
                                                                                inner_dict.items()]
        self.sect = True if self.int in self.res.keys() else False

class MethodFiles(Method):
    def __init__(self2, keywrd, subwrd=None):
        super().__init__(keywrd, subwrd)
        for type_, flexts in zip(self2.types, self2.flexts_):
            self2.type_, self2.flexts = type_, flexts
            self2.assessment_tree(self2, self2.type_, self2.flexts, self2.sect)
    @CatalogueFinding
    def assessment_tree(self2, keylst, sect, extension, fnd, flpath, Q, path=None, exchange=None):
        if exchange:
            self2.keywrd, self2.res = exchange, files4res[exchange]
        if sect is True and fnd is not True:
            self2.option1(keylst, Q)
            rtn = 'pass'
        elif sect is True and fnd is True or sect is False and fnd is True:
            rtn = self2.option2(keylst, extension, flpath, Q)
        elif sect is None and fnd is True:
            self2.option3(keylst, path, flpath)
            rtn = 'continue'
        elif sect is None and fnd is False or sect is False and fnd is False:
            self2.option4(keylst, extension)
            rtn = 'continue'
        return rtn
    def option1(self2, keylst, Q):
        Q.put([None, self2.res[self2.out][keylst[0]]])
    def option2(self2, keylst, extension, flpath, Q):
        Dirs.address_book, _ = create_nested_dict(keylst, [extension], [flpath], Dirs().address_book)
        rtn = 'continue'
        return rtn
    def option3(self2, keylst, path, flpath):
        Q_ = queue.Queue()
        t0a = th.Thread(target=MakingIntermediaryFiles, args=(path, flpath, self2.keywrd, Q_))
        t0a.start()
        while Q_.empty() is False:
            new_fls = Q_.get()
            for ext, nwfl in zip(self2.res[self2.int][keylst[0]], new_fls):
                Dirs.address_book, _ = create_nested_dict(keylst, [ext], [nwfl], Dirs().address_book)
        t0a.join()
    def option4(self2, keylst, extension):
        try:
            raise FileNotFoundError
        except FileNotFoundError:
            ErrMessages.FileSearch_FileNotFoundError3(self2.keywrd, *keylst[1:], extension)

class MakingIntermediaryFiles:
    def __init__(self, dirpath, filepaths, keywrd, q=None):
        self.dirpath, self.filepaths = dirpath, filepaths
        # get list of names of all items within directory of self.dirpath at entry to class.
        before = os.listdir(self.dirpath)
        # call associated function for
        eval("self.{}()".format(functions.get(keywrd)))
        after = os.listdir(self.dirpath)
        self.flns4rtrn = [os.path.join(self.dirpath, file) for file in after if file not in before]
        if q:
            q.put(self.flns4rtrn)
    def BaderFileCreation(self):
        # filename at end of self.filepaths os.path(), cwd when entering function, & os.path() to bader executable.
        baderfile, cwd, BdrExec = self.filepaths.split("/")[-1], os.getcwd(), \
                                  os.path.join(Dirs().executables_address, "bader")
        # change sudo current working directory (cwd) to directory of calculation.
        os.chdir(self.dirpath)
        # acts as: !{bader executable} {filepath}; output created by BdrExec program is suppressed.
        p = subprocess.call([BdrExec, baderfile],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT)
        # change sudo current working directory back to originally set directory in MAIN.py.
        os.chdir(cwd)
    def GeometryLastCreation(self):
        # derive new file name from previous 1.xyz name with the new extension of L.xyz.
        new_xyz_file = "".join([i for i in self.filepaths][:-5] + ["L.xyz"])
        old_xyz, new_xyz1 = open(self.filepaths, 'r'), open(new_xyz_file, 'w')
        # tot # of atoms will not change between 1st & last optimization step - 1st 1.xyz line gives # of atoms in calc.
        tot_atoms, lines, j, index = [str('     ' + "".join(old_xyz.readline().split())), old_xyz.readlines(),
                                      len(old_xyz.readlines()), len(old_xyz.readlines()) + 1]
        last_itr = False
        # for last geometry step, need to start at bottom of 1.xyz file.
        for line in reversed(lines):
            # moving up the lines from the bottom of 1.xyz file.
            index -= 1
            # last line in 1.xyz file which will be written as first line in new L.xyz file.
            if tot_atoms not in line and index == j and last_itr is False:
                string = line
                new_xyz1.write(string)
                new_xyz1.close()
            # rest of the coordinates of the last geometry step and final line with total atoms.
            elif last_itr is False:
                # 1st line of each geometry optimization step has only tot # of atoms - Last line to write.
                if tot_atoms in line and last_itr is False:
                    # Last_itr needs to be set to True to stop the writing of further lines to L.xyz after final line.
                    last_itr = True
                # opening L.xyz file in read+ mode so that file can be read and written to.
                with open(new_xyz_file, 'r+') as new_xyz2:
                    # create list of all lines within the newly created L.xyz file.
                    lines2 = new_xyz2.readlines()
                    # add next line up from the bottom of 1.xyz to the front of the list of lines in L.xyz.
                    lines2.insert(0, line)
                    new_xyz2.seek(0)
                    # write amended list of L.xyz lines with next line from 1.xyz at the top from top of file down.
                    new_xyz2.writelines(lines2)
    def Return(self):
        return self.flns4rtrn

## FromFile

async def read_file_async(filepath):
    async with aiofiles.open(filepath, 'r') as file:
        return await file.read()

async def iterate(os_path, varitem):
    # fetch file lines from os_path file
    lines = await read_file_async(os_path)
    lines = lines.split('\n')
    # Handling of very large files when required information for variable 'via' function is a single line from file
    if len(lines) > 100000 and not len(varitem['kwargs']) > 1:
        ln = [ln for ln in lines if ln.startswith(varitem["locate"])][-1]
        indx = lines.index(ln)
        # preconvertion of variable kwargs item value into a dictionary to be feed as **kwargs to variables 'via' function.
        kwargs = eval("f'{}'".format(*varitem['kwargs']))
        return await eval("{}".format(varitem["via"]))(ln, **eval(f'dict({kwargs})'))
    else:
        lines_ = lines[::-1] if varitem.get("reverse") is True else lines
        # manually call context manager AsyncIterateManager so that information can be returned from the __aenter__ method.
        manager = AsyncIterateManager(varitem, lines_)
        ln, indx = await manager.__aenter__()
        # preconvertion of variable kwargs item value into a dictionary to be feed as **kwargs to variables 'via' function.
        kwargs = eval("f'{}, {}'".format(*varitem['kwargs'])) if len(varitem['kwargs']) > 1 else eval("f'{}'".format(*varitem['kwargs']))
        return await eval("{}".format(varitem["via"]))(ln, **eval(f'dict({kwargs})'))

async def inline(ln, loc, via):
    """
        decision tree of where loc str is within certain ln. 
    """
    # handling of variables requiring multiple lines
    if type(loc) == list:
        # signal for atom kind variable
        if len(loc) == 1 and loc[0] in ln:
            return None
        # handling of xyz variable from inp file
        elif len(loc) == 3 and loc[0] in ln:
            return 0
        elif len(loc) == 3 and loc[1] in ln:
            return 1
        # signal 1 for charge pop variable
        elif len(loc) == 2 and loc[0] in ln:
            return None
        # signal 2 for charge pop variable
        elif len(loc) == 2 and  loc[1] in ln:
                    return [True, None]
        else:
            return False 
    # variable requiring single ln 
    elif loc in ln:
        return True
    else:
        return False        

class async_iterator():
    def __init__(self, lines):
        self.lines = lines
        self.lns = [ln for ln in reversed(lines)]
        self.lcounter = -1
        self.counter = 0
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.counter <= -len(self.lines):
            raise StopAsyncIteration
        self.counter -= 1
        self.lcounter += 1
        return [self.counter, self.lns[self.lcounter]]

class AsyncIterateManager:
    """
        Async context manager acting as a iteration controller. 
    """
    def __init__(self, varitem, lines):
        self.varitem = varitem
        self.lines = lines
        self.list = []
    async def __aenter__(self):
        async for item_ in async_iterator(self.lines):
            item, ln = item_[0], item_[1]
            bool_ = await inline(ln, self.varitem['locate'], self.varitem['via'])
            if bool_ == None:
                # handling of multiple lines requiring extracting from log file for atom kinds. 
                if len(self.varitem['locate']) == 1:
                    if self.list == []:
                        self.list.append([int(var[1]) for var in enumerate(ln.split()) if var[0] in [6]][0])
                    elif len(self.list) == self.list[0]:
                        self.list.append(ln)
                        self.list.pop(0)
                        # returning of required list of lines containing information regarding atom kinds. 
                        return self.list, None
                    else:
                        self.list.append(ln)
                # handling of multiple lines requiring extracting from log file for charge populations. 
                else:
                    if self.varitem["num"] == None:
                        self.list.append([var[1] for var in enumerate(self.lines[item - self.varitem["n"]].split()) if var[0] in [0]][0])
                    else:
                        self.list = self.varitem["num"]
            # returning of required information related to charge populations. 
            elif bool_ == [True, None]:
                return self.list, item
            # returning of file line and index required for particular variable being collected
            elif bool_ == 0:
                self.list.append(bool_)
                return ln, self.list
            elif bool == 1:
                self.list.extend([item, bool_])
            elif bool_ == True:
                return ln, item
    async def __aexit__(self,*args):
        pass

## Inp
    
async def xyz(line, index, lines):
    if index[-1] == 0:
        result = await eval("{}".format(varitem["locate"][2][0]))(line)
    elif index[-1] == 1:
        result = await eval("{}".format(varitem["locate"][2][1]))(lines, index[0])
    return result 

async def find_xyz(line):
    xyz_name = [str(var[1]) for var in enumerate(line.split()) if var[0] in [1]][0]
    if xyz_name.find('/'):
        xyz_name = xyz_name.split('/')[-1]
    await asyncio.sleep(0.01)
    return xyz_name

async def make_xyz(lines, index):
    indx, readlines, filename = index - 2, [], '/'.join(xyz.os_path.split('/')[:-1] + ["geometry.xyz"])
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

## Log

async def find_a(line, index, lines):
    strg1 = line
    strg2 = lines[index]
    strg3 = lines[index - 1]
    collect = []
    for s, item, letter in zip([1, 2, 3], ['a', 'b', 'c'], ['A', 'B', 'C']):
        # extract txt of indices 4,5,6,9 in line split list. {letter} is lat cnst, {item}Latt is {item} line of lat vec.
        exec(f'*{letter}, {item}Latt= [float(var[1]) for var in enumerate(strg{s}.split()) if var[0] in [4,5,6,9]]')
        exec(f'collect.extend([{letter}, {item}Latt])')
    await asyncio.sleep(0.01)
    return collect

async def find_at(ln, lines, index):
    # make empty lists
    X, Y, Z, ELEMENT, MASS = [], [], [], [], []
    # find max number of atoms in calc for information to collected for.
    max = [int(var[1]) for var in enumerate(lines[index + 20].split()) if var[0] in [2]][0]
    # Some log files have an extra blank space between line where "locate" string is found & start of atom info.
    try:
        mass = [var[1] for var in enumerate(lines[index - 3].split()) if var[0] in [8]]
        n = 3
    except ValueError:
        mass = [var[1] for var in enumerate(lines[index - 4].split()) if var[0] in [8]]
        n = 4
    finally:
        for p in range(0, max):
            # extract index 2,4-6,8 in line split list. element - atom element, x/y/z - x/y/z-coord, mass - atomic mass.
            element, x, y, z, mass = [var[1] for var in enumerate(lines[index - n - p].split()) if  var[0] in [2, 4, 5, 6, 8]]
            for f, F in zip([float(x), float(y), float(z), element, mass], [X, Y, Z, ELEMENT, MASS]):
                F.append(f)
    array = np.array([X, Y, Z])
    # place extracted values in corresponding position of proxy list.
    await asyncio.sleep(0.01)
    return array

async def find_charge(line, **kwargs):
    C = [int(var[1]) for var in enumerate(line.split()) if var[0] in [2]][0]
    if C < 0:
        C = "".join(["".join([i for i in list(str(C)) if i != '-']), '-'])
    elif C == 0:
        pass
    else:
        C = "".join([str(C), "+"])
    await asyncio.sleep(0.01)
    return C
        
async def find_energy(line, **kwargs):
    # extract of txt of index 8 in line split list. E is tot energy of calc converted from hartree units to eV.
    E = [(round(float(var[1]), 10) * 27.211) for var in enumerate(line.split()) if var[0] in [8]][0]
    await asyncio.sleep(0.01)
    return E

async def find_gap(line, index, lines):
    # beta gap
    strg2 = line
    # alpha gap
    strg1 = lines[index - 1]
    collect0 = []
    for spin, s in zip(["alpha", "beta"], [1, 2]):
        # extract txt of index 6 in line split list. {spin}_HOMO_LUMOgap is {spin} band gap in eV.
        exec(f'{spin}_HOMO_LUMOgap = [float(var[1]) for var in enumerate(strg{s}.split()) if var[0] in[6]][0]')
        exec(f'collect0.append({spin}_HOMO_LUMOgap)')
    await asyncio.sleep(0.01)
    return collect0

async def find_kind(lines, **kwargs):
    collect1 = []
    for line in lines:
        # extract indices 3,7 in line split list. kind_ele - name of kind, num_atoms - # of atoms of kind in calc.
        kind_ele, num_atoms = [var[1] for var in enumerate(line.split()) if var[0] in [3, 7]]
        collect1.extend([kind_ele, num_atoms])
    await asyncio.sleep(0.01)
    return collect1
    
async def find_name(line, **kwargs):
    # extract txt of index 3 in line split list. N is the project name of calculation.
    N = [str(var[1]) for var in enumerate(line.split()) if var[0] in [3]][0]
    # place extracted value in corresponding position of proxy list.
    await asyncio.sleep(0.01)
    return N
    
async def find_run(line, **kwargs):
    # extract txt of index 3 in line split list. R is the calculation run type.
    R = [str(var[1]) for var in enumerate(line.split()) if var[0] in [3]][0]
    # place extracted value in corresponding position of proxy list.
    await asyncio.sleep(0.01)
    return R

async def find_pop1(atoms, index, lines):
    collect2 = []
    rnge = atoms if len(atoms) > 1 else range(0, int(atoms[0]))
    # A of specific atom indices or from 0 to total number of atoms in system.
    for A in rnge:
        # extract indices 3-6 in line split list. p1_a & p1_b - alpha & beta pops, p1_s & p1_c - Mulliken spin & charge.
        p1_a, p1_b, p1_c, p1_s = [round(float(var[1]), 3) for var in enumerate(lines[int(index + 3 + A)].split())
                                  if var[0] in [3, 4, 5, 6]]
        collect2.append([p1_a, p1_b, p1_c, p1_s])
    await asyncio.sleep(0.01)
    return [collect2]

async def find_pop2(atoms, index, lines, path):
    addbk, ckeys = Dirs().address_book, Dirs().dir_calc_keys 
    for p in (p for p in [addbk["perfect"][n][r][c]['log'] for n, r, c in ([n, r, c] for n, r, c in ckeys['perfect']) ] if p == path ):
        SharableDicts().smd['total atoms'] = atoms
    
    collect3 = []
    rnge = atoms if len(atoms) > 1 else range(0, int(atoms[0]))
    # A of specific atom indices or from 0 to total number of atoms in system.
    for A in rnge:
        # extract indices 4-7 in line split list. p2_a & p2_b - alpha & beta pops, p2_s & p2_c - Hirshfeld spin & charge.
        p2_a, p2_b, p2_s, p2_c = [round(float(var[1]), 3) for var in enumerate(lines[int(index + 3 + A)].split()) if var[0] in [4, 5, 6, 7]]
        collect3.append([p2_a, p2_b, p2_c, p2_s])
    await asyncio.sleep(0.01)
    return [collect3]

async def find_version(line, **kwargs):
    # extract txt of index 5 in line split list. V is CP2K version calculation performed with.
    V = [float(var[1]) for var in enumerate(line.split()) if var[0] in [5]][0]
    await asyncio.sleep(0.01)
    return V
    
## ChargesSpins
    
async def CntrlChrgSpns():
    # Main Asyncio task - set up subtasks
    condition = asyncio.Condition()
    tasks = await asyncio.gather(ThreadOne(condition), ThreadTwo(condition))
    await asyncio.sleep(1)
    # async with condition:
    #     condition.notify_all()
    await asyncio.wait(tasks)    

class BaderProcessing(MethodFiles):
    def __init__(self2):
        super().__init__('charges and spins', 'bader')
        super().assessment_tree(self2, self2.type_, self2.flexts, self2.sect)
    def option4(self2, kl, extension):
        try:
            if kl[0] == 'perfect':
                raise ConnectionAbortedError
            else:
                raise FileNotFoundError
        except ConnectionAbortedError:
            CaS_Settings.bader_break = True
            path_ = Dirs().address_book[kl[0]][kl[1]][kl[2]][kl[3]]["path"]
            ErrMessages.CaS_ConnectionAbortedError(path_, Global_lock().lock)
            sys.exit(0)
        except FileNotFoundError:
            CaS_Settings.bader_missing = True
            dp = '/'.join([d for d in str(Dirs().address_book[kl[0]][kl[1]][kl[2]][kl[3]]["path"]).split('/') if d not in str(UArg().cwd).split('/')])
            kl.append(dp)
            _, CaS_Settings.dirs_missing_bader = proxyfunction(kl, None, None, None, CaS_Settings().dirs_missing_bader)

class OnlyProcessing:
    def __init__(self2):
        if 'geometry' in ProcessCntrls().processwants:
            print("geometry should have worked this out already [code L952]")
        else:
            Files4DefiningDefect("charges and spins", "only")

async def ThreadOne(condition):
    print('waiting in thread 1 for condition [code L960]')
    result = await  sync_to_async(ask_question)("CaSQ1", "YorN", ['Y', 'N'])
    CaS_Settings.nn_and_def = boolconvtr[result]
    print(result, '[code L962]')
    async with condition:
        condition.notify_all()
    await asyncio.sleep(0.03)
    print('no longer waiting for thread 1 [code L967]')
    if CaS_Settings().nn_and_def is True:
        await sync_to_async(OnlyProcessing())
    if CaS_Settings().bader_missing is True:
        async with condition:
            await condition.wait()
    # 1. Ask question CaSQ1
    # 2. if True, OnlyProcessing; if False, wait for answer to whether there is errors from BaderProcessing

async def ThreadTwo(condition):
    BaderProcessing()
    print('done')
    if CaS_Settings().bader_missing is True:
        async with condition:
            await condition.wait()
        ErrMessages.CaS_FileNotFoundError(CaS_Settings().dirs_missing_bader['defect'], "-ELECTRON_DENSITY-1_0.cube", "analysis of Bader charges of atoms", Global_lock().lock)
        CaS_Settings.cont_bdr = boolconvtr[ask_question("CaSQ2", "YorN", ["Y", "N"])]
        for calclist in CaS_Settings().dirs_missing_bader['defect']:
            _ = calclist.pop(3)
        async with condition:
            condition.notify_all()
    print('works so far [code L1081]')

    # 1. BaderProcessing
    # 2. Check for errors from BaderProcessing

## ProcessCntral

class Files4DefiningDefect(MethodFiles):
    def __init__(self2, keyword, subkeyword, **kwargs):
        Method.__init__(self2, keyword, subkeyword)
        super().assessment_tree(self2, self2.types[1], [self2.flexts_[1][0]], False, **kwargs) # defect
        super().assessment_tree(self2, self2.types[0], self2.flexts_[0], True) if keyword=="geometry" else super().assessment_tree(self2, self2.types[0], self2.flexts_[0], True,  exchange='geometry') # perfect
    def option2(self2, keylst, extension, flpath, Q):
        if keylst[0] == 'defect':
            return await eval("self2.option2{}".format(keylst[0]))(keylst, extension, flpath, Q)
        else:
            exec(f'func = self2.option2{keylst[0]}(keylst, extension, flpath, Q)')
            return func
    def option2defect(self2, k, et, flpath, Q):
        paths, rtn, fnd = et if et == '.inp' else self2.flexts_[1][1], 'pass' if et == '.inp' else 'continue', False if et != '.inp' else None
        Dirs.address_book, _ = create_nested_dict(k, [paths], [flpath], Dirs().address_book)
        if et == '.inp':
            xyzname = Entry4FromFiles(flpath[0], 'inp', self2.keywrd)
            Q.put([False, [xyzname[1]]])
        else:
            if Ctl_Settings.defining_except_found is True:
                for n, r, c, e in ([n, r, c, e] for n, r, c, e in Ctl_Settings().i_defining['defect'] if
                                   n == k[1] and r == k[2] and e == et):
                    Dirs.address_book, _ = create_nested_dict(['defect', n, r, c], [str(paths + '*')], [flpath],Dirs().address_book)
                    path = [p for n_, r_, c_, p in Ctl_Settings().e2_defining['defect'] if n_ == n and r_ == r and c_ == c][ 0]
                    Ctl_Settings().e2_defining['defect'].remove([n, r, c, path])
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
        dp = '/'.join([d for d in str(Dirs().address_book[k[0]][k[1]][k[2]][k[3]]["path"]).split('/') if d not in str(UArg().cwd).split('/')])
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
    
asyncio.run(CntrlChrgSpns())