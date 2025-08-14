#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pytex.py
# Description:
# -----------------------------------------------------------------------------
#
# Started on <mar 12-08-2025 17:42:34.878303533 (1755013354)>
# Carlos Linares López <carlos.linares@uc3m.es>
#

"""Purpose:

A thin wrapper for latex compilations including: compiling the .tex sources;
processing the bib references and also the indices. It recompiles the original
sources if necessary

Requirements:

- The requested binaries (e.g., pdflatex, xelatex, bibtex, splitindex, etc.)
  must be available in your $PATH

This script is written from pytex.py from Stefan Schinkel, distributed under the
wonderful "the beer-ware license" given below:

* ----------------------------------------------------------------------------
* "THE BEER-WARE LICENSE" (Revision 42):
* <stefan.schinkel@gmail.com> wrote this file. As long as you retain this notice you
* can do whatever you want with this stuff. If we meet some day, and you think
* this stuff is worth it, you can buy me a beer in return
* Stefan Schinkel
* ----------------------------------------------------------------------------

If you ever meet Stefan Schinkel, please invite him to two beers!

"""

# imports
# -----------------------------------------------------------------------------
import os
import re
from pathlib import Path

import argparser
import bib
import message
import process
import sys
import utils

# constants
# -----------------------------------------------------------------------------

# Info messages
INFO_NO_ERROR_FOUND = " No errors found"

# Error messages
ERROR_NO_ERROR_FOUND = " No errors were found, but the return code is non-null. Inspect the .log file!"


# functions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# guess_filename
#
# guess the main LaTeX file to process. The rules are simple:
#
#    1. If the user provided a filename ending in ".tex"/".latex" then that file
#       is readily used
#
#    2. Otherwise, it is checked whether a readable file exists after adding
#       ".tex". If so, that file is used
#
#    3. If not, then the same is tried with the suffix ".latex"
#
# If none of these rules work then None is returned
# -----------------------------------------------------------------------------
def guess_filename(basename: str) -> str:
    """guess the main LaTeX file to process. The rules are simple:

         1. If the user provided a filename ending in ".tex"/".latex" then that
            file is readily used

         2. Otherwise, it is checked whether a readable file exists after adding
            ".tex". If so, that file is used

         3. If not, then the same is tried with the suffix ".latex"

         If none of these rules work then None is returned

    """

    # verify the .tex file given exists and is accessible
    filename = None

    # First, is it a .tex file?
    if (texfile := utils.get_filename(basename, '.tex')) and \
       utils.check_file_exists(texfile) and \
       utils.check_file_readable(texfile):
        filename = texfile

    elif (texfile := utils.get_filename(basename, '.latex')) and \
         utils.check_file_exists(texfile) and \
         utils.check_file_readable(texfile):

        # or is it a .latex file?
        filename = texfile

    # Return None unless the filename was properly guessed
    if filename is not None:
        return filename
    return None


# -----------------------------------------------------------------------------
# run_latex
#
# This function opens a pipe to the binary to process the LaTeX file, compiles
# the given file and decode both the standard output and error under the
# specified encoding.
#
# It returns a processor which contains all the information that resulted from
# processing the texfile
# -----------------------------------------------------------------------------
def run_latex(texfile: str,
              processor: str, encoding: str) -> process.Processor:
    """This function opens a pipe to the binary to process the LaTeX file,
       compiles the given file and encodes both the standard output and error
       under the specified encoding

       It returns a processor which contains all the information that resulted
       from processing the texfile

    """

    # process the LaTeX file
    compiler = process.Processor(texfile, processor, encoding)
    compiler.run()
    print(f"\tReturn code: {compiler.get_return_code()}")

    # process the output to find all warnings and errors, if any
    compiler.process_warnings()
    compiler.process_errors()

    # and show all warnings on the standard console indexed by the file where
    # they were detected
    for ifile in compiler.get_input_files():
        if len(compiler.get_warnings(ifile)) > 0:
            if ifile == "":
                print(" Preamble:")
            else:
                print(f" {ifile}")
            print(f"{compiler.get_warnings(ifile):proc_warning}")

    # and finally, in case there are any errors show them on the standard output
    if len(compiler.get_errors()) > 0:
        print(" Errors found!")
        for ierror in compiler.get_errors():
            print(f'{ierror:proc_error}')

    # if no errors were found, observe the return code anyway. Only if no errors
    # are found and the return code is zero, everything is fine. Otherwise,
    # maybe the processor was not able to find errors, but the user must be
    # warned
    else:
        if compiler.get_return_code() != 0:
            print(ERROR_NO_ERROR_FOUND)
        else:
            print(INFO_NO_ERROR_FOUND)

    # and return the processor
    return compiler


# -----------------------------------------------------------------------------
# run_bibtex
#
# This function opens a pipe to the tool used to process bibunits and decode
# both the standard output and error under the specified encoding
# -----------------------------------------------------------------------------
def run_bib(texfile: str,
            tool: str, encoding: str):
    """This function opens a pipe to the tool used to process bibunits and
       decode both the standard output and error under the specified encoding

    """

    # create a bibtool to process the bib references in the texfile, provided
    # there is any.
    bibtool = bib.Bibtool(texfile, encoding, tool)

    # get all bibunits that have to be processed
    for bibunit in bibtool.get_bibfiles():
        bibtool.run(bibunit)


# -----------------------------------------------------------------------------
# Automates processing a specific .tex file (named after texfile), which is
# guaranteed to exist and to be readable
#
# It also guesses whether to process the bib references and/or the index tables
# -----------------------------------------------------------------------------
def main(texfile: str,
         processor: str, bib: str, index: str, encoding: str):
    """Automates processing a specific .tex file (named after texfile), which is
    guaranteed to exist and to be readable

    It also guesses whether to process the bib references and/or the index
    tables and what tools to do so

    """

    # first things first, the unavoidable step is to process the texfile and, if
    # any errors happened, then abort execution
    compiler = run_latex(texfile, processor, encoding)
    if len(compiler.get_errors()) > 0:
        sys.exit(1)

    # next, process the bib directives in case there is any
    run_bib(texfile, bib, encoding)


# main
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # process the arguments
    cli = argparser.createArgParser().parse_args()

    # guess the full name of the LaTeX file to process
    if (filename := guess_filename(cli.texfile)) and filename is not None:
        print(f" {cli.processor} {filename}")
    else:
        raise ValueError(f"No .tex/.latex file found with name {cli.texfile}")

    # Next, determine the encoding. The user settings are used first; if none is
    # given the env vars are checked and if this did not help either then the
    # default value is ued
    encoding = cli.encoding
    if encoding is None:

        # get the environment variable for LC_ALL
        encoding = os.environ.get("LC_ALL")
        if encoding is None:

            # then resort to the best choice under UTF-8
            encoding = "UTF-8"

    print(f" Using encoding {encoding}")

    # invoke the main service of this #!/usr/bin/env python
    main(filename, cli.processor, cli.bib, cli.index, encoding)


# Local Variables:
# mode:python
# fill-column:80
# End:
