#!/usr/bin/env python3

#   Messages.py handles all settings for presentation/printing of text to the commandline terminal when
#   CASORP is run.
#   ----------------------------------------------------------
#   Author: Niamh Smith; E-mail: niamh.smith.17 [at] ucl.ac.uk
#   Date:

# import os
import sys
import time
import threading as th
from Core.CentralDefinitions import UArg, Pool_Args_check
from Core.DictsAndLists import argv_dict, options, questions


__all__ = {'ask_question', 'bcolors', 'checkinput', 'Delay_Print', 'ErrMessages', 'Global_lock', 'ProcessTakingPlace',
           'SlowMessageLines',  'Stdin_Applied'}

class bcolors:
    """
        Colours to be used for command line messages and for user inputs upon run of python file.

        Class definitions are each either a Select Graphic Rendition (SGR) or 8-bit Escape (ESC) color mode code.
    """

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

class Delay_Print:
    """
        Delayed horizontal (on same line) printing of the characters within a string.

        Inputs:
            s(str)         : String to be printed character by character.

            lock(th.Lock)  : Unowned lock synchronization primitive shared
                             between threads which when called upon blocks the ability
                             of any other thread to print until the lock has finished the
                             printing commands within the current with statement it has
                             acquired and is released.

            t(float)       : Optional. Input given if downtime between printing
                             characters needs to be changed from default of 0.024
                             seconds.

            q(queue.Queue) : Optional. Included if information from another
                             thread needs to be passed to this method in order to
                             disrupt printing of str characters one by one while waiting
                             for other threads are being executed.
    """

    def __init__(self, s_, lock, t = None, q = None):
        count = 0
        if q:
            while q.empty() is True:
                for s in s_:
                    with lock:
                        count += 1
                        sys.stdout.write(s)
                        sys.stdout.flush()
                        time.sleep(t)
                        if count == 110:
                            sys.stdout.write('\n')
                            sys.stdout.flush()
                            count = 0
            else:
                # print('queue called and item given [C.M L81]')
                sys.exit(0)
        else:
            with lock:
                self.printer(s_, t)

    def printer(self, s, t = None):
        """
            code for actually printing each letter of the string one by one. Separated from __init__ to avoid repetition.
        """
        for c in s:
            sys.stdout.write(c)
            sys.stdout.flush()
            if t:
                time.sleep(t)
            else:
                time.sleep(0.024)

class ProcessTakingPlace:
    """
        Printing of buffer user statement and '----'.

        Printing in times of visual downtime (i.e no printing of questions/KEYINFOs/
        errors/results) to indicate that the programme is not ideal and processing is
        taking place.

        Inputs:
            lock(th.Lock)       : Unowned lock synchronization primitive shared
                                  between threads which when called upon blocks the ability
                                  of any other thread to print until the lock has finished the
                                  printing commands within the current with statement it has
                                  acquired and is released.

            t(float/empty list) : Optional input given if downtime between printing
                                  characters needs to be changed from default of 0.024
                                  seconds.

            miss(None/True)     : Optional. Input given if the user message should
                                  not be printed along with '-----' when method is called.

            q(queue.Queue)      : Optional. Included if information from another
                                  thread needs to be passed to the Core.delay_print method
                                  in order to disrupt printing of str characters one by one
                                  while waiting for other threads are being executed.
    """

    def __init__(self, lock, t, miss = None, q = None):
        if not miss:
            # print user message.
            text = str("                                      {bcolors.EXTRA}Thank you. Processing taking place.")
            SlowMessageLines(text, lock)
        text = str(
            f"{bcolors.EXTRA}----------------------------------------------------------------------------------------"
            f"----------------------{bcolors.ENDC}\n")
        if q:
            t0 = th.Thread(target=Delay_Print, args=(text, lock, t, q))
        elif t and not q:
            t0 = th.Thread(target=Delay_Print, args=(text, lock, t))
        else:
            t0 = th.Thread(target=Delay_Print, args=(text, lock))
        t0.start()
        t0.join()

class linewidth:
    """
        To ensure that all printed lines of text are 110 characters long or less.

        Inputs:
            trial(str) : String to be printed.

    """
    def __init__(self, message):
        # Split string into list at "{" instances.
        message, j = message.split("{"), 0
        for item in message:
            if "}" in item:
                # get index of item in list and split list items in two at the "}" instance.
                indx, new  = message.index(item), [newitem for newitem in item.split("}")]
                # remove item from list so that it can be replaced by its two halves.
                message.remove(item)
                # 1st half of item placed back at original index of item, 2nd half inserted at index + 1.
                [message.insert(indx + idx, n) for idx, n in zip(range(len(new)), new)]
        for indx, item in enumerate(message):
            # Don't want to count characters of bcolors calls.
            if "bcolors" not in item and len(item) != 0:
                # pre-inserted newline in string (ie linebreak for providing further context) found
                if "\n" in item:
                    # reset j to 0, add item characters length. '\n' stated after txt color change at start of str.
                    j = 0 + len(item)
                else:
                    # add length of character of item to j.
                    j += len(item)
                if j > 110:
                    # k is num of characters j is over 110 by. o is  list of characters in item.
                    k, o = 110 - j, [i for i in item]
                    try:
                        while o[k] != ' ':
                            # move back characters from would be character 110 until character is a blank space.
                            k -= 1
                        o.insert(k + 1, "\n")
                    # index error if string is shorter than index stated to be character 110 of the line.
                    except IndexError:
                        # insert newline at beginning of string.
                        o.insert(0, "\n")
                    # put broken characters of item back together and replace item in main list
                    message.remove(item)
                    message.insert(indx, "".join(o))
                    # return j value to account for removing 110 characters now on previous line, add characters now on current line.
                    j = j + k - 110
                if j == 110:
                    # reset j back to 0 if at 110.
                    j = j - 110
            # inactive bcolors (txt color) calls. Characters in these not to be counted as str characters.
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
    """
        Delayed printing of whole lines of text to command line terminal. Slowing down pace at which information given.

        Inputs:
            message(str)  : Message to be printed to the commandline terminal.

            lock(th.Lock) : Optional. Unowned lock synchronization primitive shared
                            between threads which when called upon blocks the ability of
                            any other thread to print until the lock has finished the printing
                            commands within the current with statement it has acquired and
                            is released.
    """
    def __init__(self, message, lock = None):
        super().__init__(message)
        lines = self.message.splitlines()
        # text to be printed is within a multithreading environment.
        if lock:
            with lock:
                self.Print(lines)
        else:
            self.Print(lines)
    def Print(self,lines):
        for line in lines:
            time.sleep(0.75)
            print(f"{line}")#[C.M L249]")

class Global_lock:
    def __init__(self):
        self._lock = th.Lock()
    @property
    def lock(self):
        return self._lock

class ErrMessages:
    """
        All error messages that can be triggered in package.

        Each individual message is given as a staticmethod function,
                        named as so: {py filename error occurred in}_{type of error occurred}.

        Class definitions
            argv_dict(dict) : Dictionary of partial error message strings related to
                              each commandline argument.
    """
    def __init__(self, f):
        self._f= f
    @staticmethod #√
    def MAIN_IndexError():
        text = str("\n{bcolors.FAIL}ERROR: {bcolors.UNDERLINE}Wrong number of arguments!{bcolors.ENDC}"
                   "{bcolors.ACTION} \nValid usage includes:{bcolors.OPTIONS}{bcolors.ITALIC} "
                   "\n./MAIN.py perf_mat_dir_str defect_parent_dir_str chem_pot_dir_str all "
                   "\n./MAIN.py perf_mat_dir_str defect_parent_dir_str chem_pot_dir_str only str_of_defect_subdir "
                   "\n./MAIN.py perf_mat_subdir_str defect_parent_dir_str chem_pot_dir_str except str_of_defect_subdir")
        # pass text to function to print certain number of characters on each line.
        return linewidth(text).Return()
    @staticmethod #√
    def MAIN_KeyError(keywrd):
        """
            Inputs:
                keywrd(str) : user given commandline argument four
        """
        text = str("\n{bcolors.FAIL}ERROR: {bcolors.UNDERLINE}Invalid keyword {bcolors.BOLD}{bcolors.CHOSEN}'"
                   +f"{keywrd}"
                   +"'{bcolors.ENDC}{bcolors.FAIL}{bcolors.UNDERLINE} given!{bcolors.ENDC}{bcolors.KEYINFO} "
                    "\nValid keywords for argument four are:  '{bcolors.OPTIONS}{bcolors.ITALIC}all{bcolors.KEYINFO}' "
                    "/ '{bcolors.OPTIONS}except{bcolors.KEYINFO}' / '{bcolors.OPTIONS}only{bcolors.KEYINFO}'.")
        # pass text to function to print certain number of characters on each line.
        return linewidth(text).Return()
    @staticmethod #√
    def MAIN_DirNotFndError(dirpath, i):
        """
            Inputs:
                err(error code) : Error code returned when one of the named
                                  directories in commandline arguments 1-3.

                i(int)          : Number of the argument which triggered the error code.
        """
        text = str("\n{bcolors.FAIL}ERROR: {bcolors.UNDERLINE}[Errno 2] No such file or directory{bcolors.ENDC} "
                   "{bcolors.KEYVAR}"
                   +f"{dirpath}"
                   +"{bcolors.FAIL}.{bcolors.KEYINFO} \nArgument "
                   +f"{i}"
                   +" {bcolors.INFO}should be "
                   +f"{argv_dict[str(i)]}"
                   +" {bcolors.ENDC}{bcolors.ACTION}\n"
                    "Spaces or dashes within a directories name are not permitted. Rename directory to remove "
                    "spaces/dashes if present in name before rerunning.")
        # pass text to function to print certain number of characters on each line.
        return linewidth(text).Return()
    @staticmethod #√
    def ValueErrorlist(lock = None):
        """
            Inputs:
                options(list) : List of the methods of data processing the user can
                                choose from.

                lock(th.Lock) : Unowned lock synchronization primitive shared
                                between threads which when called upon blocks the ability
                                of any other thread to print until the lock has finished the
                                printing commands within the current with statement it has
                                acquired and is released.
        """
        text = str("\n{bcolors.FAIL}ERROR: {bcolors.UNDERLINE}Invalid results type given!{bcolors.ENDC}"
                   "{bcolors.KEYINFO} "
                   "\nValid methods implemented are:{bcolors.OPTIONS}{bcolors.ITALIC} \n"
                   +f"{', '.join(options)}"
                   +"{bcolors.ENDC}{bcolors.ACTION} "
                    "\nPlease use commas to separate the names of each method within your answer.")
        # pass text & lock to function to print each line of error slowly when lock is next unreleased & available.
        SlowMessageLines(text)
    @staticmethod #√
    def ValueErrorYorN(lock = None):
        """
            Inputs:
                lock(th.Lock) : Unowned lock synchronization primitive shared
                                between threads which when called upon blocks the ability
                                of any other thread to print until the lock has finished the
                                printing commands within the current with statement it has
                                acquired and is released.
        """
        text = str("\n{bcolors.FAIL}WARNING:{bcolors.UNDERLINE}Invalid answer given!{bcolors.ENDC}{bcolors.KEYINFO} "
                   "\nOnly valid answers are {bcolors.OPTIONS}Y {bcolors.ACTION}and {bcolors.OPTIONS}N"
                   "{bcolors.KEYINFO}.{bcolors.ACTION}Try again.  ")
        # pass text & lock to function to print each line of error slowly when lock is next unreleased & available.
        SlowMessageLines(text)
    @staticmethod
    def Main_NotImplementedError(lock):
        """
            Inputs:
                lock(th.Lock) : Unowned lock synchronization primitive shared between
                                threads which when called upon blocks the ability of any
                                other thread to print until the lock has finished the printing
                                commands within the current with statement it has
                                acquired and is released.
        """
        text = str("\n{bcolors.FAIL}WARNING: {bcolors.UNDERLINE}Results asked to be processed include {bcolors.CHOSEN} "
                   "'WFN'{bcolors.FAIL}.{bcolors.ENDC}{bcolors.KEYINFO} \nWFN results can not be displayed in a csv file. "
                   "\n{bcolors.ACTION}If you do not wish for analysis to be performed on the other results asked for "
                   "please press {bcolors.OPTIONS}{bcolors.ITALIC}Crt+C{bcolors.ENDC}{bcolors.ACTION} now. Otherwise "
                   "press {bcolors.OPTIONS}Y{bcolors.ACTION}.")
        # pass text & lock to function to print each line of error slowly when lock is next unreleased & available.
        SlowMessageLines(text)
    @staticmethod
    def Main_TypeError(err, lock):
        """
            Inputs:
                err(error code) : Error code of TypeError which has been triggered.

                lock(th.Lock)   : Unowned lock synchronization primitive shared between threads which when called upon
                                  blocks the ability of any other thread to print until the lock has finished the
                                  printing commands within the current with statement it has acquired and is released.
        """
        text = str("\n{bcolors.FAIL}ERROR: {bcolors.UNDERLINE}"+f"{err}"+"{bcolors.ENDC}")
        # pass text & lock to function to print each line of error slowly when lock is next unreleased & available.
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
    def FileSearch_FileNotFoundError1(key, lock = None):
        """
            Inputs:
                key(str)      : Name of subdirectory listed after 'only' by user in commandline arguments which cannot
                                be found within parent directory.

                lock(th.Lock) : Unowned lock synchronization primitive shared between threads which when called upon
                                blocks the ability of any other thread to print until the lock has finished the printing
                                commands within the current with statement it has acquired and is released.
        """
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
    def FileSearch_FileNotFoundError2(key, lock = None):
        """
            Inputs:
                key(str)      : Name of subdirectory listed after 'only' by user in commandline arguments which cannot
                                be found within parent directory.

                lock(th.Lock) : Unowned lock synchronization primitive shared between threads which when called upon
                                blocks the ability of any other thread to print until the lock has finished the printing
                                commands within the current with statement it has acquired and is released.
        """
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
    def FileSearch_FileNotFoundError3(keywrd, name, run, charge, filetypes, lock = None):
        """
            Inputs:
                keywrd(str)   : Keyword which corresponds to the result processing method that FileNotFoundError has
                                been flagged for.

                name(str)     : Nested dict item key of project name of the particular defect geometry/placement/
                                impurity inclusion.

                run(str)      : Nested dict item key of runtype of the calculation of the particular defect geometry/
                                placement/impurity inclusion.

                chrg(int)     : Nested dict item key of charge state of the calculation of the particular defect
                                geometry/placement/impurity inclusion.

                lock(th.Lock) : Unowned lock synchronization primitive shared between threads which when called upon
                                blocks the ability of any other thread to print until the lock has finished the printing
                                commands within the current with statement it has acquired and is released.
        """
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
        """
            Inputs:
                path(os.path) : File path of the directory in which file was being searched for.

                lock(th.Lock) : Unowned lock synchronization primitive shared between threads which when called upon
                                blocks the ability of any other thread to print until the lock has finished the printing
                                commands within the current with statement it has acquired and is released.
        """
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
    def CaS_FileNotFoundError(MissingFiles, filetypes, method, lock=None):
        """
            Inputs:
                DirsMissingBader(list) : List of file paths of the directory in which file was being searched for.

                lock(th.Lock)          : Unowned lock synchronization primitive shared between threads which when called
                                         upon blocks the ability of any other thread to print until the lock has
                                         finished the printing commands within the current with statement it has
                                         acquired and is released.
        """
        text = str("\n{bcolors.FAIL}WARNING: {bcolors.UNDERLINE}[Errno 2]{bcolors.ENDC}{bcolors.FAIL} Needed "
                   "{bcolors.KEYVAR}'"
                   + f"{filetypes}"
                   + "'{bcolors.ENDC}{bcolors.FAIL} file(s) for {bcolors.METHOD}"
                   + f"{method}"
                   + "{bcolors.ENDC}{bcolors.FAIL} could not be found within the "
                     "following directories for:")
        SlowMessageLines(text, lock)
        time.sleep(0.5)
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
    """
         Testing for error in user's input response to questions asked.
    """
    def wrapper(Q, typ, ans, *args) -> str:
        """
            Inputs:
                Q(str)        : Key for one of the questions within Core.PrePopDictsAndLists.questions.

                typ(str)      : Expected type of the answer and must match a key within func._format.

                ans(list)     : List of multiple valid answer options the user can choose from

                args          : extra arguments such as a th.Lock or queue.Queue for controlling passing
                                of into between threads and/or preventing simultaneous printing of
                                multiple threads.

            Outputs:
                A(str)        : If error exception is triggered, return answer given by user when question
                                asked again by function. If error exception is not triggered, return value
                                of input A as given to function.
        """
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
                # trigger error informing user that they've given an input which is invalid.
                eval("ErrMessages.ValueError{}()".format(typ))
                A = ask_question(Q, typ, ans)
            break
        if isinstance(A, list) == True:
            Acopy = A.copy()
            _ = Pool_Args_check(Acopy).Return()
            if _ != A:
                A = (_, A)
        return A
    return wrapper

@checkinput
def ask_question(Q: str, typ: str, ans: list) -> str:
    """
        Asking required user input question.
    """
    _format = {'list': "A.split(', ') if ',' in A else [A]", 'YorN': 'A.upper()'}
    assert Q in questions.keys(), "Q must be a key for one of the questions within Core.PrePopDictsAndLists.questions."
    assert typ in _format.keys(), "typ is the expected type of the answer and must match a key within _format."
    assert isinstance(ans, list), "ans must be a list of multiple valid answer options the user can choose from"
    SlowMessageLines(questions[str(Q)])
    A = input()
    # if expected type is list, split string. If expected type is Yes or No, make sure string is upper case.
    A = eval(_format[typ])
    return A
