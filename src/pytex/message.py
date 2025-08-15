#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# message.py
# Description:
# -----------------------------------------------------------------------------
#
# Started on <mié 13-08-2025 16:34:34.608108256 (1755095674)>
# Carlos Linares López <carlos.linares@uc3m.es>
#

"""
Definition of a generic message and a container for them
"""

# imports
# -----------------------------------------------------------------------------

# constants
# -----------------------------------------------------------------------------

# Error messages
ERROR_UNKNOWN_MESSAGE_SPECIFICATION = "[Message] Unknown format specification: '{}'"


# classes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Message
#
# Definition of any of the types of message acknowledged by this script
# -----------------------------------------------------------------------------
class Message:
    """Definition of any of the types of message acknowledged by this script"""

    def __init__(self, mode: str = "", info: str = "", name: str = "",
                 path: str = "", line: str = ""):
        """A message might consist of an arbitrary number of fields given
        selectively. It is then the responsibility of the caller to use it in
        the right way. In particular, format allows different specs which shows
        information in different ways

        """

        # copy the attributes
        (self._mode, self._info, self._name, self._path, self._line) = (mode, info, name, path, line)

    def __eq__(self, other):
        """Return True if and only this instance and other contain the same
        information"""

        return self._mode == other.get_mode() and \
            self._info == other.get_info() and \
            self._name == other.get_name() and \
            self._path == other.get_path() and \
            self._line == other.get_line()

    def __format__(self, spec: str = ""):
        """Provides a tailored representation of the contents of this instance.

           It acknowledges the following specifications:

             + proc_warning: [mode name Warning] info
             + proc_error: path:line info

           If an unknown specification is given, an exception is raised
        """

        if spec == "proc_warning":
            if self._name == "":
                return f'\t[{self._mode} Warning] {self._info}'
            return f'\t[{self._mode} {self._name} Warning] {self._info}'

        elif spec == "proc_error":
            return f'{self._path}:{self._line} {self._info}'

        raise ValueError(ERROR_UNKNOWN_MESSAGE_SPECIFICATION.format(spec))

    def get_info(self):
        """Return the info of this instance"""

        return self._info

    def get_line(self):
        """Return the line of this instance"""

        return self._line

    def get_mode(self):
        """Return the mode of this instance"""

        return self._mode

    def get_name(self):
        """Return the name of this instance"""

        return self._name

    def get_path(self):
        """Return the path of this instance"""

        return self._path


# -----------------------------------------------------------------------------
# Messages
#
# Definition of a container for messages
# -----------------------------------------------------------------------------
class Messages:
    """Definition of a container for messages"""

    def __init__(self):
        """A container of messages is initialized empty"""

        # initialize the attributes

        # members are initialized empty
        self._members = []

    def __contains__(self, other: Message):
        """Return True if and only if the given Message exists in this container"""

        return other in self._members

    def __format__(self, spec: str = ""):
        """Provides a tailored representation of the contents of this instance.

           It acknowledges the following specifications:

             + proc_warning: [mode name Warning] info
             + proc_error: mode:name info

           If an unknown specification is given, an exception is raised
        """

        output = ""
        for imember in self._members:
            output += imember.__format__(spec)
        return output

    def __iadd__(self, other: Message):
        """Add the given message to the corresponding container"""

        # in case the given message already exists, skip
        if other in self:
            return self
        self._members.append(other)

        return self

    def __len__(self):
        """Return the number of messages stored in this container"""

        return len(self._members)


# Local Variables:
# mode:python
# fill-column:80
# End:
