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
import index
import message
import process
import sys
import utils

# constants
# -----------------------------------------------------------------------------

# Info messages
INFO_PDF_FILE_GENERATED = " {} generated"

# Warning messages
WARNING_MAX_NB_CYCLES = " The maximum number of cycles, {}, has been reached and the processor still recommends re-running the files"

# Warning messages
ERROR_NO_PDF_FILE_GENERATED = " No pdf output has been generated"


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
    return filename


# -----------------------------------------------------------------------------
# run_latex
#
# This function opens a pipe to the binary to process the LaTeX file, compiles
# the given file and decode both the standard output and error under the
# specified encoding.
# -----------------------------------------------------------------------------
def run_latex(texfile: str,
              processor: process.Processor, encoding: str):
    """This function opens a pipe to the binary to process the LaTeX file,
       compiles the given file and encodes both the standard output and error
       under the specified encoding

    """

    # process the LaTeX file
    processor.run()


# -----------------------------------------------------------------------------
# run_bibtex
#
# This function opens a pipe to the tool used to process bibunits and decode
# both the standard output and error under the specified encoding
# -----------------------------------------------------------------------------
def run_bib(texfile: str,
            tool: bib.Bibtool, encoding: str):
    """This function opens a pipe to the tool used to process bibunits and
       decode both the standard output and error under the specified encoding

    """

    # check first whether it is necessary to process the files
    if tool.get_rerun():

        # get all bibunits that have to be processed
        for bibunit in tool.get_bibfiles():
            tool.run(bibunit)


# -----------------------------------------------------------------------------
# run_index
#
# This function opens a pipe to the tool used to process indices and decode both
# the standard output and error under the specified encoding
# -----------------------------------------------------------------------------
def run_index(texfile: str,
              tool: index.Idxtool, encoding: str):
    """This function opens a pipe to the tool used to process indices and decode
       both the standard output and error under the specified encoding

    """

    # check first whether it is necessary to process the files
    if tool.get_rerun():

        # get all index files that have to be processed
        for idxunit in tool.get_idx_files():
            tool.run(idxunit)


# -----------------------------------------------------------------------------
# Automates processing a specific .tex file (named after texfile), which is
# guaranteed to exist and to be readable
#
# It also guesses whether to process the bib references and/or the index tables
#
# In case an output is given, the resulting pdf file is renamed acordingly
# -----------------------------------------------------------------------------
def main(texfile: str,
         processor: str, bib_hint: str, index_hint: str, encoding: str,
         output: str, quiet: bool):
    """Automates processing a specific .tex file (named after texfile), which is
       guaranteed to exist and to be readable

       It also guesses whether to process the bib references and/or the index
       tables and what tools to do so

       In case an output is given, the resulting pdf file is renamed acordingly

    """

    # count the number of cycles, and set the maximum number of cycles
    nb_cycles = 0
    max_nb_cycles = 5

    # create a LaTeX processor
    processor = process.Processor(texfile, processor, encoding, quiet)

    # initialize the bib/index tools to None
    bibtool, idxtool = None, None

    # until the processor is happy or five full cycles have been consumed. This
    # might happen with some "pathological" docs
    while processor.get_rerun() and nb_cycles < max_nb_cycles:

        # first things first, the unavoidable step is to process the texfile and, if
        # any errors happened, then abort execution
        run_latex(texfile, processor, encoding)
        if len(processor.get_errors()) > 0:
            sys.exit(1)

        # In case the bibtool does not exist yet, create it, and then reuse it
        # in the following cycles.
        if not bibtool:
            bibtool = bib.Bibtool(texfile, encoding, bib_hint, quiet)
        run_bib(texfile, bibtool, encoding)

        # In case the index tool does not exist yet, create it, and then reuse
        # it in the following cycles
        if not idxtool:
            idxtool = index.Idxtool(texfile, encoding, index_hint, quiet)
        run_index(texfile, idxtool, encoding)

        # and update the number of cycles executed
        nb_cycles += 1

    # show a warning in case the processor insists in re-running even if the
    # maximum number of cycles was reached
    if processor.get_rerun() and nb_cycles >= max_nb_cycles:
        print(WARNING_MAX_NB_CYCLES.format(max_nb_cycles))

    # in case an output filename was given, rename the output pdf file to the
    # name given

    # First, verify the pdf exists
    src=Path(texfile).with_suffix('.pdf')
    if not src.exists():
        print(ERROR_NO_PDF_FILE_GENERATED)
        sys.exit(1)

    if output != "":

        # get a path to the output file and rename the pdf file generated
        dst=Path(output).with_suffix('.pdf')
        src.rename(dst)

    else:
        dst=src

    print(INFO_PDF_FILE_GENERATED.format(dst))

# main
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # process the arguments
    cli = argparser.createArgParser().parse_args()

    # guess the full name of the LaTeX file to process
    if not (filename := guess_filename(cli.texfile)):
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

    # show the encoding
    print(f" Using encoding {encoding}")

    # invoke the main service of this #!/usr/bin/env python
    main(filename, cli.processor, cli.bib, cli.index, encoding, cli.output, cli.quiet)


# Local Variables:
# mode:python
# fill-column:80
# End:
