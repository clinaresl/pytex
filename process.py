#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# process.py
# Description:
# -----------------------------------------------------------------------------
#
# Started on <mar 12-08-2025 20:44:04.450449625 (1755024244)>
# Carlos Linares López <carlos.linares@uc3m.es>
#

"""
Definition of a LaTeX processor along with various services for parsing both the
standard output and the standard error
"""


# imports
# -----------------------------------------------------------------------------
import re
import os
import shlex
import sys
import subprocess

from collections import defaultdict
from pathlib import Path

import message
import utils

# constants
# -----------------------------------------------------------------------------

# Info messages
INFO_NO_ERROR_FOUND = " No errors found"

# Warning messages
WARNING_NO_FILE_FOUND = " Warning: no file found with the name {}"

# Error messages
ERROR_NO_ERROR_FOUND = " No errors were found, but the return code is non-null. Inspect the .log file!"


# regular expressions

# Re-running regexp
RE_RERUN = re.compile(r'(?:LaTeX|Package(?:\s+\w+)?)\s+Warning:(.*\bRerun\b.*|\s+There were undefined (?:references|citations))')

# Warning regexp
RE_WARNING_INPUT = re.compile(r'\((?P<filename>\.[^\.]+)(?P<suffix>\.[^\.\s)]+)')
RE_WARN_GENERIC = re.compile(
    r'(?P<mode>LaTeX|Package|Class)\s+(?P<name>.+)?\s*Warning:\s*(?P<msg>.+?)$',
    re.M,
)
RE_COMBINED_INPUT_WARN_GENERIC = re.compile(
    r'\((?P<filename>\.[^\.]+)(?P<suffix>\.[^\.\s)]+)|(?P<mode>LaTeX|Package|Class)\s+(?P<name>.+)?\s*Warning:\s*(?P<msg>.+?)$',
    re.M,
)
RE_OVERUNDER = re.compile(
    r'^(?P<type>Over|Under)full \\hbox .*? at lines? (?P<line1>\d+)(?:--(?P<line2>\d+))?',
    re.M,
)

# Error regexp
RE_ERROR = re.compile(r'(?ms)^(?P<path>(?:/|~/|\./|\../)?(?:[^\s/\r\n]+/)*[^\s/\r\n]+\.[^\s./\r\n]+):(?P<line>\d+)(?P<body>.*?)(?=\r?\n\s*\r?\n|\Z)')

# classes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# ProcessorWarnings
#
# Definition of a container of warnings issued by the processor
# -----------------------------------------------------------------------------
class ProcessorWarnings:
    """Definition of a container of warnings issued by the processor"""

    def __init__(self):
        """A container of messages is initialized empty"""

        # initialize the attributes

        # There are three different types of warning: latex, package and class.
        # Each one is also categorized by their name, and hence they are stored
        # separately as dictionaries.
        (self._latex, self._package, self._class) = (defaultdict(list), defaultdict(list), defaultdict(list))

    def __contains__(self, other: message.Message):
        """Return True if and only if the given Message exists in this container"""

        if other.get_mode() == "LaTeX":
            return other in self._latex[other.get_name()]
        elif other.get_mode() == "Package":
            return other in self._package[other.get_name()]
        if other.get_mode() == "Class":
            return other in self._class[other.get_name()]

    def __format__(self, spec: str = ""):
        """Provides a tailored representation of the contents of this instance.

           It acknowledges the following specifications:

             + proc_warning: [mode name Warning] info
             + proc_error: mode:name info

           If an unknown specification is given, an exception is raised
        """

        output = ""

        # First, show the package messages
        for iname in self._package:
            for imessage in self._package[iname]:
                output += imessage.__format__(spec) + '\n'

        # Next, the class messages
        for iname in self._class:
            for imessage in self._class[iname]:
                output += imessage.__format__(spec) + '\n'

        # Finally, the latex messages
        for iname in self._latex:
            for imessage in self._latex[iname]:
                output += imessage.__format__(spec) + '\n'

        return output

    def __iadd__(self, other: message.Message):
        """Add the given message to the corresponding container"""

        # in case the given message already exists, skip
        if other in self:
            return self

        if other.get_mode() == "LaTeX":
            self._latex[other.get_name()].append(other)
        elif other.get_mode() == "Package":
            self._package[other.get_name()].append(other)
        if other.get_mode() == "Class":
            self._class[other.get_name()].append(other)

        return self

    def __len__(self):
        """Return the number of messages stored in this container"""

        return len(self._latex) + \
            len(self._package) + \
            len(self._class)


# -----------------------------------------------------------------------------
# Processor
#
# Definition of a LaTeX processor along with various services for parsing both
# the standard output and the standard error
# -----------------------------------------------------------------------------
class Processor:
    """Definition of a LaTeX processor along with various services for parsing
       both the standard output and the standard error

    """

    def __init__(self, texfile: str, processor: str, encoding: str, quiet: bool):
        """A processor is created with a LaTeX file to process, a binary
           accessible from the current $PATH and a specific encoding used to
           decode both the standard output and standard error

           In case quiet is True, then all output messages but the most
           important ones are skipped

        """

        # copy the attributes
        (self._texfile, self._processor, self._encoding, self._quiet) = (texfile, processor, encoding, quiet)

        # also, initialize other attributes that might be required later for
        # other services
        (self._stdout, self._stderr, self._return_code) = ("", "", None)

        # as a result of processing the output generated a number of warnings
        # might be issued. These are stored as a dictionary indexed by the
        # filename under which they appeared. Some warnings might happen before
        # a file is being processed, and the empty string is then used as the
        # key
        self._warnings = defaultdict(ProcessorWarnings)

        # also, a global collection of warnings is maintained to avoid showing
        # the same warning in case it happens when processing different files
        self._global_warnings = message.Messages()

        # warnings must be shown in the same order they appeared. For this, the
        # names of all files being processed is stored separately. Note that the
        # blank string is added first which stands for those warnings that might
        # have been found before any file was input
        self._input_files: list[str] = [""]

        # Also, every processor keeps information about all errors found in the
        # log file. These are always given with the filename and lineno where
        # they were detected and hence they are not categorized in any way. Even
        # if only one error should be generated (if any), it is assumed that
        # there might be an arbitrary number of them
        self._errors: list[message.Message] = []

        # It is necessary as well to check whether the processor chosen requests
        # re-running the files again, e.g., because there are cross-references.
        # Initially, this flag takes the value true because the files should be
        # processed at least once
        self._rerun = True

    def get_errors(self):
        """Return all errors generated during this process"""

        return self._errors

    def get_input_files(self):
        """Return the names of all files being processed in the same order they
        appeared

        """

        return self._input_files

    def get_rerun(self) -> bool:
        """Return whether the processor recommends re-running the files"""

        return self._rerun

    def get_return_code(self):
        """Return the error code generated by the process of the LaTeX file"""

        return self._return_code

    def get_warnings(self, key: str = None):
        """Return all warnings. In case a key is provided, return only the
        warnings for that specific key"""

        if key is not None:
            return self._warnings[key]
        return self._warnings

    def run(self):
        """Opens a pipe to the binary to process the LaTeX file, compiles the
           given file and encodes both the standard output and error under the
           specified encoding

        """

        # show the command to run even if quiet is True
        print(f' {self._processor} {self._texfile}')

        # When starting a new process, ensure that all warnings and errors are removed
        self._warnings = defaultdict(ProcessorWarnings)
        self._global_warnings = message.Messages()
        self._errors: list[message.Message] = []

        # first things first, run latex at least once over the given tex file
        sproc = subprocess.Popen(
            shlex.split(f'{self._processor} -interaction=nonstopmode -halt-on-error -file-line-error -recorder {self._texfile}'),
            env={**os.environ},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
        )

        # get both the standard output and standard error decoded under the
        # specified encoding schema
        out_bytes, err_bytes = sproc.communicate()
        self._stdout = out_bytes.decode(encoding=self._encoding, errors="replace")
        self._stderr = err_bytes.decode(encoding=self._encoding, errors="replace")
        self._return_code = sproc.returncode

        # update the rerun flag. The information should be found in the .log file
        base = Path(self._texfile)
        log_file = base.with_suffix(".log")
        txt = log_file.read_text(encoding=self._encoding, errors="ignore")
        self._rerun = RE_RERUN.search(txt) is not None

        # process the output to find all warnings and errors, if any
        self.process_warnings()
        self.process_errors()

        # and show all warnings on the standard console indexed by the file where
        # they were detected unless quiet is True
        if not self._quiet:
            for ifile in self.get_input_files():
                if len(self.get_warnings(ifile)) > 0:
                    if ifile == "":
                        print(" Preamble:")
                    else:
                        print(f" {ifile}")
                    print(f"{self.get_warnings(ifile):proc_warning}")

        # and finally, in case there are any errors show them on the standard
        # output even in quiet mode
        if len(self.get_errors()) > 0:
            print(" Errors found!")
            for ierror in self.get_errors():
                print(f'{ierror:proc_error}')

        # if no errors were found, observe the return code anyway. Only if no errors
        # are found and the return code is zero, everything is fine. Otherwise,
        # maybe the processor was not able to find errors, but the user must be
        # warned in spite of the value of quiet
        else:
            if self.get_return_code() != 0:
                print(ERROR_NO_ERROR_FOUND)
            else:
                if not self._quiet:
                    print(INFO_NO_ERROR_FOUND)

        # leave a blank line
        if not self._quiet:
            print()

    def process_warnings(self):
        """Process the .log file generated by the processing of the main LaTeX
           file and updates information about all warnings encountered

        """

        # open the log file
        log_filename = utils.get_filename(utils.get_basename(self._texfile), ".log")
        if not utils.check_file_exists(log_filename):
            print(WARNING_NO_FILE_FOUND.format(log_filename))
            return

        # and now get all contents using the specified encoding, and process
        # them removing all embedded newlines because LaTeX warnings usually
        # span over several lines. Also, check for input files being processed
        # and store the warnings found under the current file being processed
        log_text = Path(log_filename).read_text(encoding=self._encoding, errors="replace")
        log_no_wrap = re.sub(r'\n(?!\n)', ' ', log_text)

        # Process all forms of warnings and retrieve information from them
        file_key = ""
        for m in RE_COMBINED_INPUT_WARN_GENERIC.finditer(log_no_wrap):

            # If this is a file being processed
            if m.group("filename") is not None:

                # and create a new entry for this file to store all warnings
                # that might be found unless it already exists. It might happen
                # that a processor inputs the same file several times (e.g.,
                # *.aux) but warnings should be shown only once
                file_key = m.group("filename") + m.group("suffix")
                if file_key not in self._input_files:
                    self._input_files.append(file_key)
                continue

            # otherwise, create a new warning
            new_warning = message.Message(
                mode=m.group("mode").strip(),
                name="" if m.group("name") is None else m.group("name").strip(),
                info=re.sub(r' {2,}', ' ', m.group("msg").strip()),
            )

            # and add it to the collection of warnings of the file being
            # currently processed, unless it has been found before
            if new_warning not in self._global_warnings:
                self._warnings[file_key] += new_warning
                self._global_warnings += new_warning


    def process_errors(self):
        """Process the .log file generated by the processing of the main LaTeX
           file and updates information about all errors encountered, though
           only one should be generated but let us be paranoid!

        """

        # open the log file
        log_filename = utils.get_filename(utils.get_basename(self._texfile), ".log")
        if not utils.check_file_exists(log_filename):
            print(WARNING_NO_FILE_FOUND.format(log_filename))
            return

        # and get all contents of this file
        log_text = Path(log_filename).read_text(encoding=self._encoding, errors="replace")

        # Now, look for errors
        for m in RE_ERROR.finditer(log_text):

            # Then create a new message with the data of an error
            new_error = message.Message(
                path=m.group("path"),
                line=m.group("line"),
                info=m.group("body"),
            )
            self._errors.append(new_error)


# Local Variables:
# mode:python
# fill-column:80
# End:
