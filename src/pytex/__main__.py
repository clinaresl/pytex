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
import shutil
import sys

from pathlib import Path

from . import argparser
from . import bib
from . import conf
from . import index
from . import process


# constants
# -----------------------------------------------------------------------------

# regexps

# regexp used to determine whether a string can produce an arbitrary number of
# matches with pathlib.glob or not
RE_GLOB_MATCHES = re.compile(r"[*?\[]")

# regexp used to identify blank lines and comments in the description of
# ancilliary files
RE_ANCILLIARY_IGNORE = re.compile(r'^(\s*|\s*#.*)$')

# messages

# Info messages
INFO_PDF_FILE_GENERATED = " {} generated"
INFO_REMOVING_FILE = " Removing file {} ..."
INFO_REMOVING_DIRECTORY = " Removing directory {} ..."

# Warning messages
WARNING_MAX_NB_CYCLES = " The maximum number of cycles, {}, has been reached and the processor still recommends re-running the files"
WARNING_NB_WARNINGS = " Number of warnings: {}"

# Warning messages
ERROR_NO_PDF_FILE_GENERATED = " No pdf output has been generated"


# functions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# guess_filename
#
# guess the main LaTeX file to process. The rules are simple:
#
#    1. The extension .tex is tried first (even if the user did not provide it)
#
#    2. The extension .latex is tried after.
#
# If none of these rules work then None is returned
# -----------------------------------------------------------------------------
def guess_filename(basename: str) -> Path | None:
    """guess the main LaTeX file to process. The rules are simple:

         1. The extension .tex is tried first (even if the user did not provide
            it)

         2. The extension .latex is tried after.


       If none of these rules work then None is returned

    """

    # is it a .tex file?
    base = Path(basename)
    texfile = base.with_suffix(".tex")
    if texfile.exists() and os.access(texfile, os.R_OK):
        return texfile

    # is it a .latex file?
    latexfile = base.with_suffix(".latex")
    if latexfile.exists() and os.access(latexfile, os.R_OK):
        return latexfile

    return None

# -----------------------------------------------------------------------------
# run_latex
#
# run the LaTeX processor
# -----------------------------------------------------------------------------
def run_latex(processor: process.Processor, quiet: bool):
    """run the LaTeX processor

    """

    # process the LaTeX file
    processor.run()

    if len(processor.get_errors()) > 0:
        sys.exit(1)

    # in case that any warning was generated, show the number in spite of
    # the value of quiet
    if processor.get_nbwarnings() > 0:
        print(WARNING_NB_WARNINGS.format(processor.get_nbwarnings()))

    # and leave a blank line
    if not quiet:
        print()


# -----------------------------------------------------------------------------
# run_bibtex
#
# run the bib tool
#
# It returns whether a bib tool was effectively used or not
# -----------------------------------------------------------------------------
def run_bib(tool: bib.Bibtool) -> bool:
    """run the bib tool

       It returns whether a bib tool was effectively used or not

    """

    # -- init
    bib_exec = False

    # check first whether it is necessary to process the files
    if tool.get_rerun():

        # get all bibunits that have to be processed
        for bibunit in tool.get_bibfiles():
            bib_exec = bib_exec or tool.run(bibunit)

    return bib_exec

# -----------------------------------------------------------------------------
# run_index
#
# run the index tool
#
# It returns whether an index tool was effectively used or not
# -----------------------------------------------------------------------------
def run_index(tool: index.Idxtool) -> bool:
    """run the index tool

       It returns whether a bib tool was effectively used or not

    """

    # -- init
    index_exec = False

    # check first whether it is necessary to process the files
    if tool.get_rerun():

        # get all index files that have to be processed
        for idxunit in tool.get_idx_files():
            index_exec = index_exec or tool.run(idxunit)

    return index_exec

# -----------------------------------------------------------------------------
# Automates processing a specific .tex file (named after texfile), which is
# guaranteed to exist and to be readable
#
# It also guesses whether to process the bib references and/or the index tables
#
# In case an output is given, the resulting pdf file is renamed acordingly
# -----------------------------------------------------------------------------
def run_pipeline(texfile: Path,
                 processor: str, bib_hint: str, index_hint: str, encoding: str,
                 output: str, quiet: bool):
    """Automates processing a specific .tex file (named after texfile), which is
       guaranteed to exist and to be readable

       It also guesses whether to process the bib references and/or the index
       tables and what tools to do so

       In case an output is given, the resulting pdf file is renamed acordingly

    """

    # set the maximum number of cycles
    max_nb_cycles = 5

    # create a LaTeX processor
    compiler = process.Processor(texfile, processor, encoding, quiet)

    # initialize the bib/index tools to None
    bibtool, idxtool = None, None

    # and also initialize the executions of the bib/index tools
    bib_exec, index_exec = False, False

    # until the processor is happy or five full cycles have been consumed. This
    # might happen with some "pathological" docs. Also, if a bib/index tool was
    # used in the last iteration, then force a new processing stage
    while (compiler.get_rerun() or bib_exec or index_exec) and \
          compiler.get_nbcycles() < max_nb_cycles:

        # first things first, the unavoidable step is to process the texfile and, if
        # any errors happened, then abort execution
        run_latex(compiler, quiet)

        # In case the bibtool does not exist yet, create it, and then reuse it
        # in the following cycles.
        if not bibtool:
            bibtool = bib.Bibtool(texfile, encoding, bib_hint, quiet)
        bib_exec = run_bib(bibtool)

        # In case the index tool does not exist yet, create it, and then reuse
        # it in the following cycles
        if not idxtool:
            idxtool = index.Idxtool(texfile, encoding, index_hint, quiet)
        index_exec = run_index(idxtool)

    # show a warning in case the processor insists in re-running even if the
    # maximum number of cycles was reached
    if compiler.get_rerun() and compiler.get_nbcycles() >= max_nb_cycles:
        print(WARNING_MAX_NB_CYCLES.format(max_nb_cycles))

    # in case an output filename was given, rename the output pdf file to the
    # name given

    # First, verify the output pdf exists
    src = texfile.with_suffix('.pdf')
    if not src.exists():
        print(ERROR_NO_PDF_FILE_GENERATED)
        sys.exit(1)

    if output != "":

        # get a path to the output file and rename the pdf file generated
        dst = Path(output).with_suffix('.pdf')
        src.rename(dst)

    else:
        dst = src

    print(INFO_PDF_FILE_GENERATED.format(dst))


# -----------------------------------------------------------------------------
# Removes all ancilliary files/directories and, in case is True, it also removes
# the final pdf file. No confirmation is required and the removal is enforced,
# ie., no error is generated in case that the specified file does not exist
# -----------------------------------------------------------------------------
def run_clear(texfile: Path, delete: bool):
    """Removes all ancilliary files/directories and, in case delete is
    True, it also removes the final pdf file. No confirmation is required and
    the removal is enforced, ie., no error is generated in case that the
    specified file does not exist

    """

    # The description of the ancilliary files is given in the configuration
    # file, which in turn, is taken from the typical .gitignore used in LaTeX
    # projects. All entries might be either files or directories
    for ipattern in conf.ANCILLIARY_EXT.splitlines():

        # ignore both blank lines and comments
        if not RE_ANCILLIARY_IGNORE.match(ipattern):

            # look in the current working directory for all occurrences of this
            # pattern
            base = Path('.')
            for imatch in base.glob(ipattern):

                # in case this pattern was expected to produce an arbitrary
                # number of matches, then check the match contains the name of
                # the texfile without suffix; otherwise, accept it and proceed
                # to its removal
                multiple = re.search(RE_GLOB_MATCHES, ipattern)
                if not multiple or \
                   (multiple and texfile.with_suffix('').name in imatch.name):

                    # Next verify, whether this is a file or a directory and in
                    # either case enforce removing the corresponding match
                    # accordingly
                    if imatch.is_file():
                        print(INFO_REMOVING_FILE.format(imatch))
                        imatch.unlink(missing_ok=True)
                    elif imatch.is_dir():
                        print(INFO_REMOVING_DIRECTORY.format(imatch))
                        shutil.rmtree(imatch, ignore_errors=True)

    # in case it is also requested to remove the .pdf file, ...
    if delete:
        pdf = texfile.with_suffix('.pdf')
        if pdf.exists():
            print(INFO_REMOVING_FILE.format(pdf))
            pdf.unlink(missing_ok=True)


# -----------------------------------------------------------------------------
# main
#
# Main entry point
# -----------------------------------------------------------------------------
def main():
    """Main entry point"""

    # process the arguments
    cli = argparser.create_arg_parser().parse_args()

    # guess the full name of the LaTeX file to process
    if not (filename := guess_filename(cli.texfile)):
        raise ValueError(f"No .tex/.latex file found with name {cli.texfile}")

    # in case either --clear or --delete was given, skip any processing and just
    # remove the corresponding files
    if (cli.clear or cli.delete):
        run_clear(filename, cli.delete)
    else:

        # Otherwise, proceed to process the given latex file. First determine
        # the encoding. The user settings are used first; if none is given the
        # env vars are checked and if this did not help either then the default
        # value is ued
        encoding = cli.encoding
        if encoding is None:

            # get the environment variable for LC_ALL
            encoding = os.environ.get("LC_ALL")
            if encoding is None:

                # then resort to UTF-8
                encoding = "UTF-8"

        # show the encoding
        print(f" Using encoding {encoding}")

        # invoke the main service of this #!/usr/bin/env python
        run_pipeline(filename, cli.processor, cli.bib, cli.index, encoding, cli.output, cli.quiet)


# main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()


# Local Variables:
# mode:python
# fill-column:80
# End:
