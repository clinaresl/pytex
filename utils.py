#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# utils.py
# Description:
# -----------------------------------------------------------------------------
#
# Started on <mar 12-08-2025 18:20:09.625779523 (1755015609)>
# Carlos Linares López <carlos.linares@uc3m.es>
#

"""Free functions required by the main script. They provide support to simple
ops

"""

# imports
# -----------------------------------------------------------------------------
import errno
import os
import re

# -----------------------------------------------------------------------------
# check_file_exists
#
# return whether the given file exists and it is a file indeed
# -----------------------------------------------------------------------------
def check_file_exists(fnm: str) -> bool:
    """return whether the given file exists and it is a file indeed

    """

    return os.path.exists(fnm) and os.path.isfile(fnm)

# -----------------------------------------------------------------------------
# check_file_readable
#
# return whether the given file can be read or not, in spite of it existing or
# not. If the file is not readable it returns in addition an error message which
# is empty if the file is readable
# -----------------------------------------------------------------------------
def check_file_readable(fnm: str) -> (bool, str):
    """return whether the given file can be read or not, in spite of it
        existing or not. If the file is not readable it returns in addition an
        error message which is empty if the file is readable

    """

    try:
        with open(fnm, encoding="utf-8") as f:
            _ = f.read()
            return True, ""
    except IOError as x:
        if x.errno == errno.ENOENT:
            return False, f"'{fnm}' does not exist"
        if x.errno == errno.EACCES:
            return False, f"'{fnm}' cannot be read"
        return False, f"'{fnm}' unknown error!"
    except UnicodeDecodeError:

        # in case of this error, the file has proven itself to be readable
        return True, ""

# -----------------------------------------------------------------------------
# get_basename
#
# return the basename of a file, i.e., the whole string but the contents after
# the *last* dot
# -----------------------------------------------------------------------------
def get_basename(filename: str):
    """return the basename of a file, i.e., the whole string but the contents after
       the *last* dot

    """

    # verify there is at least one dot
    match = re.match(r'(?P<filename>.*)\..*', filename)

    # if none exists, reeturn the whole string
    if not match:
        return filename

    # otherwise, just return everything before the last dot ---note this
    # function strongly relies on the greedy behaviour of the package re
    return match.group("filename")

# -----------------------------------------------------------------------------
# get_filename
#
# return the right name of a file. If the given filename already finishes with
# the given suffix, then it is readily used; otherwise, the given suffix is
# added
# -----------------------------------------------------------------------------
def get_filename(filename: str, suffix: str) -> str:
    """return the right name of a file. If the given filename already finishes
       with the given suffix, then it is readily used; otherwise, the given
       suffix is added

    """

    # trivial case - no suffix is given
    if not suffix:
        return filename

    # break the filename into its different components
    split = os.path.splitext(filename)

    # make sure the specified suffix starts with a dot
    suffix = suffix.strip()
    suffix = '.' + suffix if suffix[0] != '.' else suffix

    # if the given suffix is already in use, then return the given filename
    # straight ahead
    if split[-1] == suffix:
        return filename

    # in any other case (either if no extension was given, or an extension
    # different than the specified suffix) was given, then add the given suffix
    return filename + suffix


# Local Variables:
# mode:python
# fill-column:80
# End:
