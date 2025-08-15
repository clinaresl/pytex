#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# argparser.py
# Description:
# -----------------------------------------------------------------------------
#
# Started on <mar 12-08-2025 17:49:39.433036238 (1755013779)>
# Carlos Linares López <carlos.linares@uc3m.es>
#

"""
Command-line interface parser
"""

# imports
# -----------------------------------------------------------------------------
import argparse
import version

# -----------------------------------------------------------------------------
# create a command parser to parse all params passed to the script program
# -----------------------------------------------------------------------------
def createArgParser():
    """create a command parser to parse all params passed to the script program"""

    # initialize a parser
    parser = argparse.ArgumentParser(description=version.__description__)

    # Group of mandatory arguments
    mandatory = parser.add_argument_group("Mandatory arguments", "The following arguments are mandatory and they must be provided:")
    mandatory.add_argument("texfile",
                           help="Main LaTeX file to process. Only files with suffix '.tex' and '.latex' are accepted.")

    # Group of optional arguments
    optional = parser.add_argument_group("Optional arguments", "The following arguments are optional and can be used to override variables automatically set by this script:")
    optional.add_argument('-p', '--processor',
                          type=str,
                          default="pdflatex",
                          help="What LaTeX processor must be used to compile the main .tex file, e.g., 'latex', 'pdflatex', 'xelatex', etc. By default 'pdflatex'")
    optional.add_argument('-b', '--bib',
                          type=str,
                          help="Tool used to process the bib entries, if any is found. Only 'bibtex' and 'biber' are automatically supported if no option is given")
    optional.add_argument('-i', '--index',
                          type=str,
                          help="Tool used to process the indices, if any is found, e.g., 'makeidx', 'splitindex', etc.")
    optional.add_argument('-e', '--encoding',
                          type=str,
                          help="Encoding used to capture the output produced by the different tools. If none is given, the contents of the env variable 'LC_ALL' are used")
    optional.add_argument('-o', '--output',
                          default="",
                          type=str,
                          help="Name of the pdf generated file. If none is given, it will be named after the input filename")

    # and return the parser
    return parser


# Local Variables:
# mode:python
# fill-column:80
# End:
