# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B4) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #


import configparser


class ConfigFileNotFound(Exception):
    """
    Raised whenever the configuration file can't be found.
    """
    def __init__(self, message):
        Exception.__init__(self, message)
        
    def __str__(self):
        return repr(self)


class ConfigFileNotValid(Exception):
    """
    Raised whenever we are parsing an invalid configuration file.
    """
    def __init__(self, message):
        Exception.__init__(self, message)
        
    def __str__(self):
        return repr(self)


class MissingRequirement(Exception):
    """
    Raised whenever we can't initialize a functionality because some modules are missing.
    """
    def __init__(self, message, throwable=None):
        Exception.__init__(self, message)
        self.throwable = throwable

    def __str__(self):
        if self.throwable:
            return '%s - %r' % (self, repr(self.throwable))
        return repr(self)


class ProgrammingError(Exception):
    """
    Raised whenever a programming error is detected.
    """
    def __init__(self, message):
        Exception.__init__(self, message)

    def __str__(self):
        return repr(self)


class DatabaseError(Exception):
    """
    Raised whenever there are inconsistences with the database schema.
    """
    def __init__(self, message):
        Exception.__init__(self, message)

    def __str__(self):
        return repr(self)


class UpdateError(Exception):
    """
    Raised whenever we fail in updating B4 sources.
    """
    def __init__(self, message, throwable=None):
        Exception.__init__(self, message)
        self.throwable = throwable

    def __str__(self):
        if self.throwable:
            return '%s - %r' % (self, repr(self.throwable))
        return repr(self)


NoOptionError = configparser.NoOptionError
NoSectionError = configparser.NoSectionError
