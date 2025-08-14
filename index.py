#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# index.py
# Description:
# -----------------------------------------------------------------------------
#
# Started on <jue 14-08-2025 12:46:02.911772264 (1755168362)>
# Carlos Linares López <carlos.linares@uc3m.es>
#

"""Definition of an idx processor along with various services for parsing both
the standard output and the standard error

"""

# imports
# -----------------------------------------------------------------------------
import re
import shlex
import subprocess

from pathlib import Path


# constants
# -----------------------------------------------------------------------------

# regular expressions


# functions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# guess_index_tool
#
# Follow a number of simple thumb rules to guess the index tool to use:
#
# 1. If there is a single <texfile>.idx:
#
#    1.a. With entries of the form \indexentry[...]{} then `splitindex` is
#         recommended
#
#    1.b. With no entries of the previous form, but only \indexentry{...},
#         makeindex is recommended
#
# 2. If there are several <filename>-*.idx, then return makeindex
# -----------------------------------------------------------------------------
def guess_index_tool(filename: str, encoding: str) -> str | None:
    """Follow a number of simple thumb rules to guess the index tool to use:

         1. If there is a single <texfile>.idx:

            1.a. With entries of the form \\indexentry[...]{} then `splitindex` is
                 recommended

            1.b. With no entries of the previous form, but only \\indexentry{...},
                 makeindex is recommended

         2. If there are several <filename>-*.idx, then return makeindex

    """

    # Get a path to the index file and also to the different -*.idx files
    base = Path(filename)
    idx_main = base.with_suffix(".idx")
    tagged_idx = Path('.').glob(f"{filename}-*.idx")

    # In case there is a single .idx file
    if idx_main.exists():
        txt = idx_main.read_text(encoding=encoding, errors="replace")

        # if this file contains tagged index entries, then recommend splitindex
        if re.search(r'^\s*\\indexentry\[[^]]+\]', txt, flags=re.M) is not None:
            return "splitindex"

        # otherwise, if there are only untagged entries, then recommend
        # makeindex
        if re.search(r'^\s*\\indexentry\{', txt, flags=re.M) is not None and \
           not tagged_idx:
            return "makeindex"

    # In case there are several idx files, and at least one contains untagged
    # entries
    if tagged_idx:
        for idxfile in [p.with_suffix("").name for p in tagged_idx]:
            txt = idxfile.read_text(encoding=encoding, errors="replace")

            # if this file contains untagged entries, then suggest makeindex
            if re.search(r'^\s*\\indexentry\{', txt, flags=re.M) is not None:
                return "makeindex"

    # At this point, it is assumed that no indices are required and None is
    # returned
    return None


# -----------------------------------------------------------------------------
# guess_index_files
#
# Return a list of files to process with the given index tool
#
# 1. If "splitindex" is given, then a single idx file is returned
#
# 2. If "makeindex" is given, then either a single file or several files are
#    returned:
#
#    2.a. If there is only one <filename>.idx then return it.
#
#    2.b. If there are several <filename>-*.idx then return those
# -----------------------------------------------------------------------------
def guess_index_files(filename: str, tool: str, encoding: str) -> list[Path]:
    """Return a list of files to process with the given index tool

         1. If "splitindex" is given, then a single idx file is returned

         2. If "makeindex" is given, then either a single file or several files
            are returned:

            2.a. If there is only one <filename>.idx then return it.

            2.b. If there are several <filename>-*.idx then return those

    """

    # get a path to the current filename and also its .idx cousing
    base = Path(filename)
    idx_main = base.with_suffix(".idx")

    # in case splitindex is given, then a single idx file should be available.
    # Certainly, there should be one .idx file per index, but they should be all
    # summarized in a single idx file.
    if tool == "splitindex":
        return [idx_main]

    # in case makeindex is given, then check whether there are a single file to
    # process or an arbitrary number of them
    tagged_idx = Path('.').glob(f"{filename}-*.idx")
    if idx_main.exists():
        txt = idx_main.read_text(encoding=encoding, errors="replace")

        # if this file contains untagged entries and there are no multiple
        # -*.idx files, then return it right away
        if re.search(r'^\s*\\indexentry\{', txt, flags=re.M) is not None and \
           not tagged_idx:
            return [filename]

    # In case there are several idx files
    aux_files = []
    if tagged_idx:
        for idxfile in [p.with_suffix("").name for p in tagged_idx]:
            txt = idxfile.read_text(encoding=encoding, errors="replace")

            # if this file contains untagged entries, then add it to the files
            # to process
            if re.search(r'^\s*\\indexentry\{', txt, flags=re.M) is not None:
                aux_files.append(idxfile)

    # and return all files
    return aux_files


# -----------------------------------------------------------------------------
# Idxtool
#
# Definition of an idx processor along with various services for parsing both
# the standard output and the standard error
# -----------------------------------------------------------------------------
class Idxtool:
    """Definition of an idx processor along with various services for parsing
       both the standard output and the standard error

    """

    def __init__(self, texfile: str, encoding: str, tool: str = ""):
        """An idx tool is created for a specific LaTeX file which is expected to
           produce relevant information when being processed, without the
           suffix, e.g., "main" if the file being processed is "main.tex". The
           contents of this file or others are interpreted according to the
           given encoding

           The user can specifically set a tool for processing the indices. If
           not given, then it is guessed from the evidence found in the current
           working directory.

        """

        # copy the attributes
        (self._idxfile, self._encoding, self._tool) = (texfile, encoding, tool)

        # also, initialize other attributes that might be required later for
        # other services
        (self._stdout, self._stderr, self._return_code) = ("", "", None)

        # in case that no tool has been specifically given, then guess it
        if not tool or tool == "":
            self._tool = guess_index_tool(texfile, encoding)

        # and now get all files to process
        self._idx_files = guess_index_files(texfile, self._tool, encoding)

    def get_tool(self) -> str:
        """Return the tool to use for processing the indices"""

        return self._tool

    def get_idx_files(self) -> [str]:
        """Return the files to process"""

        return self._idx_files

    def run(self, idxfile: str):
        """Opens a pipe to the binary to process the specified index file, and
           encodes both the standard output and error under the specified
           encoding

        """

        # if no indices have to be processed return immediately
        if not self._tool or self._tool == "":
            return

        # determine the command to run: makeindex can be optionally run "-q" to
        # produce minimalist output, but anyway, it does not generate so much
        # info so that I'm happy just to run the selected tool over the
        # necessary files
        cmd = f'{self._tool}'

        # first things first, run the tool
        print(f' {cmd} {idxfile.stem}')
        sproc = subprocess.Popen(
            shlex.split(f'{cmd} {idxfile.stem}'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # get both the standard output and standard error decoded under the
        # specified encoding schema
        out_bytes, err_bytes = sproc.communicate()
        self._stdout = out_bytes.decode(encoding=self._encoding, errors="replace")
        self._stderr = err_bytes.decode(encoding=self._encoding, errors="replace")
        self._return_code = sproc.returncode

        # show all lines of the standard output indented
        for iline in self._stdout.splitlines():
            print(f"\t{iline}")
        for iline in self._stderr.splitlines():
            print(f"\t{iline}")

        # check whether there are any errors
        if self._return_code != 0:
            print("Errors found!")
        else:
            print(" No errors found")


# Local Variables:
# mode:python
# fill-column:80
# End:
