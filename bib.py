#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# bib.py
# Description:
# -----------------------------------------------------------------------------
#
# Started on <mié 13-08-2025 20:54:47.052588680 (1755111287)>
# Carlos Linares López <carlos.linares@uc3m.es>
#

"""Definition of a bib processor along with various services for parsing both
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

# regular expression used to look for bib directives in .aux files
RE_BIB = re.compile(r'\\bibdata\{.*?\}|\\bibstyle\{.*?\}')

# functions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# guess_bibtool
#
# Follow a number of simple thumb rules to guess the bib tool to use. In a
# nutshell,
#
# 1. If a .bcf has been generated, then biber is recommended
#
# 2. If there is no .bcf but the .aux file contains directives such as `bibdata`
#    and/or `bibstyle`, then bibtex is recommended
#
# 3. Otherwise, it is assumed that there are no bib references and None is
#    returned
# -----------------------------------------------------------------------------
def guess_bibtool(filename: str, encoding: str) -> str | None:
    """Follow a number of simple thumb rules to guess the bib tool to use. In a
       nutshell,

         1. If a .bcf has been generated, then biber is recommended

         2. If there is no .bcf but the .aux file contains directives such as
            `bibdata` and/or `bibstyle`, then bibtex is recommended

         3. Otherwise, it is assumed that there are no bib references and None is
            returned

    """

    base = Path(filename)

    # Check whether there is a file .bcf named after the name LaTeX file
    bcf_path = base.with_suffix(".bcf")
    if bcf_path.exists():
        return "biber"

    # Otherwise, check whether there are files with extension .aux that contain
    # bib directives
    aux_files = []
    for aux_path in list(Path.cwd().glob("*.aux")):

        try:
            txt = aux_path.read_text(encoding=encoding, errors="ignore")
        except Exception:
            continue
        if RE_BIB.search(txt):
            return "bibtex"

    # otherwise, make no recommendation
    return None


# -----------------------------------------------------------------------------
# guess_bibfiles
#
# Return a list of bibunits to process with the given bibtool:
#
# 1. If "biber" is given, then a ".bcf" file should be found
#
# 2. If "bibtex" is given, then a number of ".aux" files with bib directives
#    should be found
# -----------------------------------------------------------------------------
def guess_bibfiles(filename: str, tool: str, encoding: str) -> list[Path]:
    """Return a list of bibunits to process with the given bibtool:

          1. If "biber" is given, then a ".bcf" file should be found

          2. If "bibtex" is given, then a number of ".aux" files with bib
             directives should be found

    """

    aux_files = []
    base = Path(filename)

    # If biber is given, then look for a .bcf file
    if tool == "biber":
        bcf_path = base.with_suffix(".bcf")
        if bcf_path.exists():
            aux_files.append(bcf_path)
        return aux_files

    # Otherwise, return only the .aux files that contain bib directives
    for aux_path in list(Path.cwd().glob("*.aux")):

        try:
            txt = aux_path.read_text(encoding=encoding, errors="ignore")
        except Exception:
            print(" Exception")
            continue
        if RE_BIB.search(txt):
            aux_files.append(aux_path)

    # and return all files
    return aux_files


# -----------------------------------------------------------------------------
# Bibtool
#
# Definition of a bib processor along with various services for parsing both the
# standard output and the standard error
# -----------------------------------------------------------------------------
class Bibtool:
    """Definition of a bib processor along with various services for parsing
       both the standard output and the standard error

    """

    def __init__(self, texfile: str, encoding: str, tool: str = ""):
        """A bib interpreter is created for a specific LaTeX file which is
           expected to produce relevant information when being processed,
           without the suffix, e.g., "main" if the file being processed is
           "main.tex". The contents of this file or others are interpreted
           according to the given encoding

           The user can specifically set a tool for processing the
           bibreferences. If not given, then it is guessed from the evidence
           found in the current working directory.

        """

        # copy the attributes
        (self._bibfile, self._encoding, self._tool) = (texfile, encoding, tool)

        # also, initialize other attributes that might be required later for
        # other services
        (self._stdout, self._stderr, self._return_code) = ("", "", None)

        # in case that no tool has been specifically given, then guess it
        if not tool or tool == "":
            self._tool = guess_bibtool(texfile, encoding)

        # and now get all bibunits to process
        self._bib_files = guess_bibfiles(texfile, self._tool, encoding)


    def get_tool(self) -> str:
        """Return the tool to use for processing the bib directives"""

        return self._tool

    def get_bibfiles(self) -> [str]:
        """Return the files to process"""

        return self._bib_files

    def run(self, bibfile: str):
        """Opens a pipe to the binary to process the specified bib file, and
           encodes both the standard output and error under the specified
           encoding

        """

        # if no bib entries have to be processed return immediately
        if not self._tool or self._tool == "":
            return

        # determine the command to run
        cmd = self._tool
        if self._tool == "bibtex":
            cmd = "bibtex"
        elif self._tool == "biber":
            cmd = "biber"
        
        # first things first, run the tool
        print(f' {cmd} {bibfile.stem}')
        sproc = subprocess.Popen(
            shlex.split(f'{cmd} {bibfile.stem}'),
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

        # check whether there are any errors
        if self._return_code != 0:
            print(" Errors found!")
            for iline in self._stderr.splitlines():
                print(f"\t{iline}")
        else:
            print(" No errors found")


# Local Variables:
# mode:python
# fill-column:80
# End:
