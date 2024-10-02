#!/usr/bin/env python3

__all__ = {'argv_dict', 'defect_type', 'files4res', 'functions', 'inp_var_fo', 'inp_want', 'log_var_fo',
           'log_want', 'multiplefiles4extension', 'optdict', 'options',  'questions'}

## LISTS
options = ("band structure", "charges and spins", "charge transition levels", "geometry", "IPR", "PDOS", "WFN",
               "work function", "test")

multiplefiles4extension = [".txt", ".png", "1-1_l.cube", "2-1_l.cube", ".wfn", ".dat", ".pdos", ".log", '-L.xyz']

## DICTIONARIES
argv_dict = {"1": "{bcolors.ITALIC}the name of the {bcolors.KEYINFO}{bcolors.BOLD}directory{bcolors.ENDC}"
                  "{bcolors.ITALIC}{bcolors.INFO} of CP2K output files for the {bcolors.KEYINFO}{bcolors.BOLD}"
                  "perfect, defect-free material{bcolors.ENDC}{bcolors.ITALIC}{bcolors.INFO}.",

             "2": "{bcolors.ITALIC}the name of the {bcolors.KEYINFO}{bcolors.BOLD}parent directory{bcolors.ENDC}"
                  "{bcolors.ITALIC}{bcolors.INFO} which holds all subdirectories of each specific defect "
                  "calculation run for a {bcolors.KEYINFO}{bcolors.BOLD}particular defect type{bcolors.ENDC}"
                  "{bcolors.ITALIC}{bcolors.INFO}",

             "3": "{bcolors.ITALIC}the name of the {bcolors.KEYINFO}{bcolors.BOLD}parent directory{bcolors.ENDC}"
                  "{bcolors.ITALIC}{bcolors.INFO} which holds all subdirectories of individual reference "
                  "{bcolors.KEYINFO}{bcolors.BOLD}chemical potentials{bcolors.ENDC}{bcolors.ITALIC}{bcolors.INFO}"
                  " for host and impurity atoms "
             }

defect_type = {'substitution': "finding_substitutional",
               'vacancy': "finding_vacancy",
               'interstitial': "finding_interstitial"
               }

files4res ={"band structure":{
                         "cp2k_outputs":{"defect":[".log"                   # To determine CP2K version of calc

                                                   ,".bs"]}                 # CP2K band structure output file.

                         ,"intermediary":{"defect":[".bs.set-1.csv"]}       # Dataclass files for band structure plots.

                         ,"final_output":[".bs.png"]},

            "charges and spins":{
                     "only":
                        {"cp2k_outputs":{"perfect":["-L.xyz"]               # Compare perf final & def initial geometry

                                         ,"defect":[".inp"                  # Extract name of def initial geometry file

                                                    ,"''.xyz"]}}            # Initial xyz file of defect calculation.

                     ,"bader":                                              # Analysis separate process to standard.

                        {"cp2k_outputs":{"perfect":["ELECTRON_DENSITY-1_0.cube"]   # CP2K output file for bader charges.

                                         ,"defect":["-ELECTRON_DENSITY-1_0.cube"]} # CP2K output file for bader charges.

                         ,"intermediary":{"perfect":["ACF.dat"]             # bader coord file - atom charge & location.

                                          ,"defect":["ACF.dat"]}}           # bader coord file - atom charge & location.

                     ,"standard":                                           # Mulliken and Hirshfeld charge analysis.

                        {"cp2k_outputs":{"perfect":[".log"]                 # Mulliken and Hirshfeld data in log file.

                                         ,"defect":[".log"]}}               # Mulliken and Hirshfeld data in log file.

                         ,"final_output":{"charges.txt"}},                  # File of dataframe of charges & spins.

            "charge transition levels":{                                    # Q: charge corrections? Dielectric matrix?
                         "cp2k_outputs":{"perfect":[".log"]                 # Atom kinds, tot nums, total E.

                                         ,"defect":[".log"]                 # Atom kinds, tot nums, charge state, tot E.

                                         ,"chem_pot":[".log"]}              # Tot E, Q: which chempot <list> for <kind>?

                         ,"final_output":[".clt.png"]},

            "geometry":{
                    "defect defining":
                        {"cp2k_outputs":{"perfect":["-L.xyz"]               # Compare perf final & def initial geometry

                                         ,"defect":[".inp"                  # Extract name of def initial geometry file

                                                    ,"''.xyz"]}}            # Initial xyz file of defect calculation.

                         ,"cp2k_outputs":{"perfect":["-1.xyz"               # CP2K output file of every geo opt step.,
                                                    
                                                    ".log"]                 # Lattice parameters.

                                         ,"defect":["-1.xyz"                # W: error displaying particular defect{??}.

                                                    ,".log"]}               # Lattice parameters.

                         ,"intermediary":{"perfect": ["-L.xyz"]             # disp of def final with perf final geometry.

                                          , "defect": ["-L.xyz"]}           # disp of def final with perf final geometry.

                         ,"final_output":[".distVdisp.png","BondLenAng.txt"]}, # File of bond length & angle dataframe.

            "IPR":{
                         "cp2k_outputs":{"perfect":[]

                                         ,"defect":[]}

                         ,"final_output":[]},

            "PDOS":{
                         "cp2k_outputs":{"perfect":[]

                                         ,"defect":[]}

                         ,"intermediary":{"perfect":[]

                                         ,"defect":[]}

                         ,"final_output":[]},

            "WFN":{
                         "cp2k_outputs":{"perfect":[]

                                         ,"defect":[]}

                         ,"intermediary":{"perfect":[]

                                         ,"defect":[]}

                         ,"final_output":[]},

            "work function":{
                         "cp2k_outputs":{"perfect":[]

                                         ,"defect":[]}

                         ,"intermediary":{"perfect":[]

                                         ,"defect":[]}

                         ,"final_output":[]}
}

functions = {"charges and spins": "BaderFileCreation",
             "Geometry": "GeometryLastCreation"}

log_want = {"band structure": [
                                "version"],

            "charges and spins": [
                                "pop1", "pop2"],

            "charge transition levels": [
                                "charge", "energy", "knd_atms"],

            "geometry": [
                                "a"],

            "original": [
                                "charge", "name", "run"],

            "all":[
                                "a","at_crd","charge","energy","gap","knd_atms","name","pop1","pop2","run","version"],

            "test":[
                                "at_crd"]
}

log_var_fo = {"a":{
                   "locate": '|a|', "via": "find_a", "found": False, "reset": None, "reverse": True},

              "at_crd":{
                   "locate": "MODULE QUICKSTEP:  ATOMIC COORDINATES IN angstrom", "via": "find_at", "found": False,
                   "reset": None, "reverse": True},

              "charge":{
                   "locate": " DFT| Charge", "via": "find_charge", "found": False, "reset": None, "reverse": False},

              "energy":{
                   "locate": "ENERGY| Total FORCE_EVAL", "via": "find_energy", "found": False, "reset": None, "reverse": False},

              "gap":{
                   "locate": "HOMO - LUMO gap", "via": "find_gap", "found": False, "reset": None, "reverse": False},

              "knd_atms":{
                   "locate": "Atomic kind", "via": "find_kind", "found": False, "num": None, "cnt": None,
                   "reset": ["num", None, "count", None], "reverse": False},

              "name":{
                   "locate": " GLOBAL| Project name", "via": "find_name", "found": False, "reset": None, "reverse": False},

              "pop1":{
                   "locate": ["Total charge and spin", "Mulliken Population Analysis"], "via": "find_pop1", "n" : 2,
                   "found": False, "num": None, "reset": ["num", None], "reverse": False},

              "pop2":{
                   "locate": ["Total Charge", 'Hirshfeld Charges'], "via": "find_pop2", "found": False, "n" : 3,
                   "num": None, "reset": ["num", None], "reverse": False},

              "run":{
                   "locate": " GLOBAL| Run type", "via": "find_run", "found": False, "reset": None, "reverse": False},

              "version":{
                   "locate": " CP2K| version string:", "via": "find_version", "found": False, "reset": None, "reverse": False}
}

inp_want = {"charges and spins": [
                "xyz1st"],
            "geometry": [
                "xyz1st"]
}

inp_var_fo = {"xyz1st":{
                   "locate": 'COORD_FILE_NAME', "via": 'find_xyz', "check": "&TOPOLOGY", "swapped": False,
                   "alt": "&END COORD", "alt_via": "make_xyz", "found": False,
                   "switch": ["locate", "via", "alt", "alt_via", "alt", "alt_via", "locate", "via"], "reverse": False}
}

optdict= {"band structure": None,
          "charges and spins": "CntrlChrgSpns",
          "charge transition levels": None, #DataProcessing.CTLsetup()
          "geometry": None, #"Presentation.geometryGUI",
          "IPR": None,
          "PDOS": None, # "GraphicAnalysis.plotpdos",
          "WFN": None, # "Presentation.WFNGUI",
          "work function": None,
          "test": None}

questions = {"MQ1": str("\n{bcolors.QUESTION}Which results types would you like to process?{bcolors.ENDC}"
                        "{bcolors.EXTRA}\nResults options include: {bcolors.OPTIONS}"
                        + f"{', '.join(options[0:6])} "
                        +"                            "
                        +f" {', '.join(options[6:9])}" ),

             "MQ2": str("\n{bcolors.QUESTION}Would you like to perform data analysis?({bcolors.OPTIONS}Y/N"
                        "{bcolors.QUESTION}){bcolors.ENDC}{bcolors.EXTRA}\nSelecting {bcolors.OPTIONS}'N'"
                        "{bcolors.EXTRA} will generate png files of analysed results: "),

             "MQ2fup1": "\n{bcolors.QUESTION}Would you like to create a GUI to display results?({bcolors.OPTIONS}"
                        "Y/N{bcolors.QUESTION}){bcolors.ENDC}{bcolors.EXTRA}\nSelecting {bcolors.OPTIONS}'N'"
                        "{bcolors.EXTRA} will generate png files of analysed results: ",

             "MQ2fup2": "{bcolors.EXTRA}If processed_data.txt already exists, data processed in this run will "
                        "be appended to file{bcolors.QUESTION}\nWould you like to overwrite this file?("
                        "{bcolors.OPTIONS}Y/N{bcolors.QUESTION}){bcolors.ENDC}",

             "CaSQ1":   "\n{bcolors.QUESTION}Would you like to process {bcolors.METHOD}charge and spin data for only "
                        "atoms related to defect{bcolors.QUESTION}, i.e. nearest neighbouring atoms to defect site and"
                        " defect atom, if present?({bcolors.OPTIONS}Y/N{bcolors.QUESTION}){bcolors.EXTRA}\nSelecting "
                        "{bcolors.OPTIONS}'N'{bcolors.EXTRA} will result in charge and spins being processed "
                        "for all atoms within a calculation:",

             "CaSQ2":   "\n{bcolors.QUESTION}Would you like to continue with {bcolors.METHOD}Bader charge analysis "
                        "{bcolors.QUESTION}for the found subdirectories which do contain the required files for this "
                        "charge analysis method?({bcolors.OPTIONS}Y/N{bcolors.QUESTION}){bcolors.EXTRA}\n"
                        "{bcolors.METHOD}Mulliken and Hirshfeld analysis {bcolors.EXTRA}will still be performed for all"
                        " found subdirectories. Selecting {bcolors.OPTIONS}'Y'{bcolors.EXTRA} will result in extra "
                        "datatable columns of {bcolors.METHOD}Bader analysis {bcolors.EXTRA}data for calculations which "
                        "{bcolors.METHOD}Bader analysis {bcolors.EXTRA}can be \nperformed for:"
             }
