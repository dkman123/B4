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


import os       # system os functions
import platform # like os
import re       # regular expressions
import shutil   # high level file utilities
import signal
#import string
import sys      # system functions
#import time     # time and sleep
import traceback    # stack traces for exception logging
import b4.b4_config
import b4.b4_functions
import b4.b4_pkg_handler

from tempfile import TemporaryFile
#from configparser import NoOptionError
#from configparser import NoSectionError

__author__ = 'ThorN'
__version__ = '1.13.2'

modulePath = b4_pkg_handler.resource_directory(__name__)

versionId = 'v%s' % __version__
version = '^8www.bigbrotherbot.net ^0(^8b4^0) ^9%s ^9[^3LeadAlbatross^9]^3' % versionId

confdir = None
console = None

# STRINGS
B4_TITLE = 'BigBrotherBot (B4) %s' % versionId
B4_TITLE_SHORT = 'B4 %s' % versionId
B4_COPYRIGHT = 'Copyright © 2005 Michael "ThorN" Thornton'
B4_LICENSE = 'GNU General Public License v2'
B4_FORUM = 'http://forum.bigbrotherbot.net/'
B4_WEBSITE = 'http://www.bigbrotherbot.net'
B4_WIKI = 'http://wiki.bigbrotherbot.net/'
B4_CONFIG_GENERATOR = 'http://config.bigbrotherbot.net/'
B4_DOCUMENTATION = 'http://doc.bigbrotherbot.net/'
B4_DONATE = 'http://www.bigbrotherbot.net/donate'
B4_XLRSTATS = 'http://www.xlrstats.com/'
B4_PLUGIN_REPOSITORY = 'http://forum.bigbrotherbot.net/downloads/?cat=4'
B4_RSS = 'http://forum.bigbrotherbot.net/news-2/?type=rss;action=.xml'

# TEAMS
TEAM_UNKNOWN = -1
TEAM_FREE = 0
TEAM_SPEC = 1
TEAM_RED = 2
TEAM_BLUE = 3

# PLAYER STATE
STATE_DEAD = 1
STATE_ALIVE = 2
STATE_UNKNOWN = 3

# CUSTOM TYPES FOR DYNAMIC CASTING
STRING = STR = 1                        ## built-in string
INTEGER = INT = 2                       ## built-in integer
BOOLEAN = BOOL = 3                      ## built-in boolean
FLOAT = 4                               ## built-in float
LEVEL = 5                               ## b4.clients.Group level
DURATION = 6                            ## b4.functions.time2minutes conversion
PATH = 7                                ## b4.getAbsolutePath path conversion
TEMPLATE = 8                            ## b4.functions.vars2printf conversion
LIST = 9                                ## string split into list of tokens


def getHomePath():
    """
    Return the path to the B4 home directory.
    """
    path = os.path.normpath(os.path.expanduser('~/.b4')).encode("latin-1").decode(sys.getfilesystemencoding())


    ## RENAME v1.10.1 -> v1.10.7
    path_1 = os.path.normpath(os.path.expanduser('~/BigBrotherBot')).encode("latin-1").decode(sys.getfilesystemencoding())
    if os.path.isdir(path_1):
        shutil.move(path_1, path)

    ## CREATE IT IF IT DOESN'T EXISTS
    if not os.path.isdir(path):
        os.mkdir(path)

    return path


# APP HOME DIRECTORY
HOMEDIR = getHomePath()


def getB4Path(decode=False):
    """
    Return the path to the main B4 directory.
    :param decode: if True will decode the path string using the default file system encoding before returning it
    """
    if b4_functions.main_is_frozen():
        path = os.path.dirname(sys.executable)
    else:
        path = modulePath
    if not decode:
        return os.path.normpath(os.path.expanduser(path))
    return b4_functions.decode(os.path.normpath(os.path.expanduser(path)))


def getConfPath(decode=False, conf=None):
    """
    Return the path to the B4 main configuration directory.
    :param decode: if True will decode the path string using the default file system encoding before returning it.
    :param conf: the current configuration being used :type Xmlconfigparser|Cfgconfigparser|MainConfig|str:
    """
    if conf:
        if isinstance(conf, str):
            path = os.path.dirname(conf)
        elif isinstance(conf, b4_config.Xmlconfigparser) \
                or isinstance(conf, b4_config.Cfgconfigparser) \
                or isinstance(conf, b4_config.MainConfig):
            path = os.path.dirname(conf.fileName)
        else:
            raise TypeError('invalid configuration type specified: expected str|Xmlconfigparser|Cfgconfigparser|MainConfig, got %s instead' % type(conf))
    else:
        path = confdir

    if not decode:
        return path
    return b4_functions.decode(path)


def getAbsolutePath(path, decode=False, conf=None):
    """
    Return an absolute path name and expand the user prefix (~).
    :param path: the relative path we want to expand
    :param decode: if True will decode the path string using the default file system encoding before returning it
    :param conf: the current configuration being used :type Xmlconfigparser|Cfgconfigparser|MainConfig|str:
    """
    if path[0:4] == '@b4\\' or path[0:4] == '@b4/':
        path = os.path.join(getB4Path(decode=False), path[4:])
    elif path[0:6] == '@conf\\' or path[0:6] == '@conf/':
        path = os.path.join(getConfPath(decode=False, conf=conf), path[6:])
    elif path[0:6] == '@home\\' or path[0:6] == '@home/':
        path = os.path.join(HOMEDIR, path[6:])
    if not decode:
        return os.path.normpath(os.path.expanduser(path))
    return b4_functions.decode(os.path.normpath(os.path.expanduser(path)))


def getPlatform():
    """
    Return the current platform name.
    :return: nt || darwin || linux
    """
    if sys.platform in ('win32', 'win64'):
        # Windows family
        return 'nt'
    elif sys.platform in ('darwin', 'mac'):
        # OS X family
        return 'darwin'
    else:
        # Fallback linux distro
        return 'linux'


def getB4versionInfo():
    """
    Returns a tuple with B4 version information.
    :return: version, platform, architecture :type: tuple
    """
    return __version__, getPlatform(), b4_functions.right_cut(platform.architecture()[0], 'bit')


def getB4versionString():
    """
    Return the B4 version as a string.
    """
    sversion = re.sub(r'\^[0-9a-z]', '', version)
    if b4_functions.main_is_frozen():
        vinfo = getB4versionInfo()
        sversion = '%s [%s%s]' % (sversion, vinfo[1], vinfo[2])
    return sversion


def getWritableFilePath(filepath, decode=False):
    """
    Return an absolute filepath making sure the current user can write it.
    If the given path is not writable by the current user, the path will be converted
    into an absolute path pointing inside the B4 home directory (defined in the `HOMEDIR` global
    variable) which is assumed to be writable.
    :param filepath: the relative path we want to expand
    :param decode: if True will decode the path string using the default file system encoding before returning it
    """
    filepath = getAbsolutePath(filepath, decode)
    if not filepath.startswith(HOMEDIR):
        try:
            tmp = TemporaryFile(dir=os.path.dirname(filepath))
        except (OSError, IOError):
            # no need to decode again since HOMEDIR is already decoded
            # and os.path.join will handle everything itself
            filepath = os.path.join(HOMEDIR, os.path.basename(filepath))
        else:
            tmp.close()
    return filepath


def getShortPath(filepath, decode=False, first_time=True):
    """
    Convert the given absolute path into a short path.
    Will replace path string with proper tokens (such as @b4, @conf, ~, ...)
    :param filepath: the path to convert
    :param decode: if True will decode the path string using the default file system encoding before returning it
    :param first_time: whether this is the first function call attempt or not
    :return: string
    """
    # NOTE: make sure to have os.path.sep at the end otherwise also files starting with 'b4' will be matched
    homepath = getAbsolutePath('@home/', decode) + os.path.sep
    if filepath.startswith(homepath):
        return filepath.replace(homepath, '@home' + os.path.sep)
    confpath = getAbsolutePath('@conf/', decode) + os.path.sep
    if filepath.startswith(confpath):
        return filepath.replace(confpath, '@conf' + os.path.sep)
    b4path = getAbsolutePath('@b4/', decode) + os.path.sep
    if filepath.startswith(b4path):
        return filepath.replace(b4path, '@b4' + os.path.sep)
    userpath = getAbsolutePath('~', decode) + os.path.sep
    if filepath.startswith(userpath):
        return filepath.replace(userpath, '~' + os.path.sep)
    if first_time:
        return getShortPath(filepath, not decode, False)
    return filepath


def loadParser(pname):
    """
    Load the parser module given its name.
    :param pname: The parser name
    :return The parser module
    """
    name = 'b4.parsers.%s' % pname
    mod = __import__(name)
    components = name.split('.')
    components.append('%sParser' % pname.title())
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def start(mainconfig, options):
    """
    Main B4 startup.
    :param mainconfig: The B4 configuration file instance :type: b4.config.MainConfig
    :param options: command line options
    """
    b4_functions.clearscreen()
    global confdir
    confdir = os.path.dirname(mainconfig.fileName)

    sys.stdout.write('Starting B4      : %s\n' % getB4versionString())
    sys.stdout.write('Autorestart mode : %s\n' % ('ON' if options.autorestart else 'OFF'))

    sys.stdout.flush()

    # NOTE: skipping update check
    # try:
    #     update_channel = mainconfig.get('update', 'channel')
    # except (NoSectionError, NoOptionError):
    #     pass
    # else:
    #     sys.stdout.write('Checking update  : ')
    #     sys.stdout.flush()
    #     if update_channel == 'skip':
    #         sys.stdout.write('SKIP\n')
    #         sys.stdout.flush()
    #     else:
    #         updatetext = checkUpdate(__version__, channel=update_channel, singleLine=True, showErrormsg=True)
    #         if updatetext:
    #             sys.stdout.write('%s\n' % updatetext)
    #             sys.stdout.flush()
    #             time.sleep(2)
    #         else:
    #             sys.stdout.write('no update available\n')
    #             sys.stdout.flush()
    #             time.sleep(1)

    # not real loading but the user will get what's configuration he is using
    sys.stdout.write('Loading config   : %s\n' % getShortPath(mainconfig.fileName, True))
    sys.stdout.flush()

    parsertype = mainconfig.get('b4', 'parser')
    sys.stdout.write('Loading parser   : %s\n' % parsertype)
    sys.stdout.flush()

    parser = loadParser(parsertype)
    global console
    console = parser(mainconfig, options)

    def termSignalHandler(signum, frame):
        """
        Define the signal handler so to handle B4 shutdown properly.
        """
        console.bot("TERM signal received: shutting down")
        console.shutdown()
        raise SystemExit(222)

    try:
        # necessary if using the function profiler,
        # because signal.signal cannot be used in threads
        signal.signal(signal.SIGTERM, termSignalHandler)
    except Exception:
        pass

    try:
        console.start()
    except KeyboardInterrupt:
        console.shutdown()
        print('Goodbye')
        return
    except SystemExit as msg:
        print('EXITING: %s' % msg)
        raise
    except Exception as msg:
        print('ERROR: %s' % msg)
        traceback.print_exc()
        sys.exit(223)

#
# from b4_config import Xmlconfigparser
# from b4_config import Cfgconfigparser
# from b4_config import MainConfig
# from b4_functions import clearscreen
# from b4_functions import decode as decode_
# from b4_functions import main_is_frozen
# from b4_functions import right_cut
#from b4_update import checkUpdate
