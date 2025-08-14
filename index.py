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
import hashlib
import re
import shlex
import subprocess

from pathlib import Path


# constants
# -----------------------------------------------------------------------------

# warning messages
WARNING_DIFFERENT_TOOL = " {} was given to process the indices and it will be used, but it is recommended to use {} instead"
WARNING_NO_INDEX_FILES = " No index files found with tool {}"

# regular expressions

# The following regular expression matches index directives which are extracted
# to compute the fingerprint of the indices
RE_INDEX = r'\\indexentry(?:\[[^]]+\])?\{.*\}\{.*\}\s*'

# The following regular expressions intentionally distinguish between tagged and
# untagged index entries
RE_TAGGED_INDEX_ENTRY = r'^\s*\\indexentry\[[^]]+\]'
RE_UNTAGGED_INDEX_ENTRY = r'^\s*\\indexentry\{'

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
    tagged_idx = Path.cwd().glob(f"{filename}-*.idx")

    # In case there is a single .idx file
    if idx_main.exists():
        txt = idx_main.read_text(encoding=encoding, errors="replace")

        # if this file contains tagged index entries, then recommend splitindex
        if re.search(RE_TAGGED_INDEX_ENTRY, txt, flags=re.M) is not None:
            return "splitindex"

        # otherwise, if there are only untagged entries, then recommend
        # makeindex
        if re.search(RE_UNTAGGED_INDEX_ENTRY, txt, flags=re.M) is not None and \
           not tagged_idx:
            return "makeindex"

    # In case there are several idx files, and at least one contains untagged
    # entries
    if tagged_idx:
        for idxfile in [p.with_suffix("").name for p in tagged_idx]:
            txt = idxfile.read_text(encoding=encoding, errors="replace")

            # if this file contains untagged entries, then suggest makeindex
            if re.search(RE_UNTAGGED_INDEX_ENTRY, txt, flags=re.M) is not None:
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
        if re.search(RE_UNTAGGED_INDEX_ENTRY, txt, flags=re.M) is not None and \
           not tagged_idx:
            return [filename]

    # In case there are several idx files
    aux_files = []
    if tagged_idx:
        for idxfile in [p.with_suffix("").name for p in tagged_idx]:
            txt = idxfile.read_text(encoding=encoding, errors="replace")

            # if this file contains untagged entries, then add it to the files
            # to process
            if re.search(RE_UNTAGGED_INDEX_ENTRY, txt, flags=re.M) is not None:
                aux_files.append(idxfile)

    # and return all files
    return aux_files


# -----------------------------------------------------------------------------
# hash_index_files
#
# Return a md5 hash code that provides a blueprint of the last processing of the
# indices. This blueprint is used later to determine whether the index tool has to
# be run again, or not.
# -----------------------------------------------------------------------------
def hash_index_files(filename: str, tool: str, encoding: str) -> str:
    """Return a md5 hash code that provides a blueprint of the last processing
       of the indices. This blueprint is used later to determine whether the
       index tool has to be run again, or not.

    """

    # First, get the files to process
    idx_files = guess_index_files(filename, tool, encoding)

    # in case splitindex is used, just return the md5 hash code of the idx file
    if tool == "splitindex":
        txt = idx_files[0].read_text(encoding=encoding, errors="ignore")
        return hashlib.md5(txt.encode(encoding)).hexdigest()

    # if makeindex is used, then process all files and build a string which
    # contains only lines with \indexentry
    if tool == "makeindex":

        contents = ""
        for aux_path in idx_files:
            txt = aux_path.read_text(encoding=encoding, errors="ignore")

            # and now get all the index directives in this file
            idx_contents = ""
            for m in RE_INDEX.finditer(txt):
                idx_contents += m.group(0) + '\n'

            # and add it to the overall contents
            contents += idx_contents

        # and return the md5 hash code
        return hashlib.md5(contents.encode(encoding)).hexdigest()

    # This should never happen but ...
    return ""


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

        # guess the recommended tool for processing the indices and, in case the
        # user provided a selection, then verify it matches. If not, warn her
        recommended = guess_index_tool(texfile, encoding)
        if tool and tool != "" and tool != recommended:
            print(WARNING_DIFFERENT_TOOL.format(self._tool, recommended))
        if not tool or tool == "":
            self._tool = recommended

        # and now get all index unit to process
        self._idx_files = guess_index_files(texfile, self._tool, encoding)
        if self._tool is not None and self._tool != "" and len(self._idx_files) == 0:
            print(WARNING_NO_INDEX_FILES.format(self._tool))

        # in case that no tool has been specifically given, then guess it
        if not tool or tool == "":
            self._tool = guess_index_tool(texfile, encoding)

        # also, the index directives are summarized in a md5 hash code to check
        # whether it is necessary to run the index tool again. This is computed
        # after every execution of the index tool
        self._fingerprint = ""

    def get_fingerprint(self) -> str:
        """Return the fingerprint of all the index directives"""

        return self._fingerprint


    def get_idx_files(self) -> [str]:
        """Return the files to process"""

        return self._idx_files

    def get_rerun(self) -> bool:
        """Return whether the processing has to be repeated"""

        # compute the hash index of the files to process. If it is different
        # than the current one then it is necessary to re-process again.
        return hash_index_files(self._idxfile, self._tool, self._encoding) != self._fingerprint

    def get_tool(self) -> str:
        """Return the tool to use for processing the indices"""

        return self._tool

    def run(self, idxfile: str):
        """Opens a pipe to the binary to process the specified index file, and
           encodes both the standard output and error under the specified
           encoding

        """

        # if no indices have to be processed return immediately
        if not self._tool or self._tool == "":
            return

        # update the fingerprint
        self._fingerprint = hash_index_files(self._idxfile, self._tool, self._encoding)

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

        # leave a blank line
        print()


# Local Variables:
# mode:python
# fill-column:80
# End:
