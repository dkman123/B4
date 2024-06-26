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

import atexit
import datetime
import glob
# import imp
import importlib
import importlib.util
import os
import queue
import re
import socket
import sys
import threading
import time

import b4
import b4.b4_clients
import b4.b4_config
import b4.storage.b4_storage
import b4.b4_events
import b4.b4_functions
import b4.b4_game
import b4.b4_cron
import b4.b4_output
import b4.parsers.q3a.rcon
import b4.b4_timezones
import b4.b4_update

from b4.b4_decorators import Memoize
from b4.b4_exceptions import MissingRequirement
from b4.b4_plugin import PluginData
from collections import OrderedDict
from configparser import NoOptionError
from textwrap import TextWrapper
from traceback import extract_tb

try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree

__author__ = 'ThorN, Courgette, xlr8or, Bakes, Ozon, Fenix'
__version__ = '1.43.6'


class Parser(object):
    OutputClass = b4.parsers.q3a.rcon.Rcon  # default output class set to the q3a rcon class

    _commands = {}  # will hold RCON commands for the current game
    _cron = None  # cron instance
    _events = {}  # available events (K=>EVENT)
    _eventNames = {}  # available event names (K=>NAME)
    _eventsStats_cronTab = None  # crontab used to log event statistics
    _handlers = {}  # event handlers
    _lineTime = None  # used to track log file time changes
    _lineFormat = re.compile('^([a-z ]+): (.*?)', re.IGNORECASE)
    _line_color_prefix = ''  # a color code prefix to be added to every line resulting from getWrap
    _line_length = 80  # max wrap length
    _messages = {}  # message template cache
    _message_delay = 0  # delay between consequent sent say messages (apply also to private messages)
    _multiline = False  # whether linebreaks \n can be manually used in messages
    _multiline_noprefix = False  # whether B4 adds > to multiline messages
    _paused = False  # set to True when B4 is paused
    _pauseNotice = False  # whether to notice B4 being paused
    _plugins = OrderedDict()  # plugin instances
    _port = 0  # the port used by the gameserver for clients connection
    _publicIp = ''  # game server public ip address
    _rconIp = ''  # the ip address where to forward RCON commands
    _rconPort = None  # the virtual port where to forward RCON commands
    _rconPassword = ''  # the rcon password set on the server
    _reColor = re.compile(r'\^[0-9a-z]')  # regex used to strip out color codes from a given string
    _timeStart = None  # timestamp when B4 has first started
    _use_color_codes = True  # whether the game supports color codes or not

    autorestart = False  # whether B4 has been started in autorestart mode
    clients = None
    config = None  # parser configuration file instance
    delay = 0.33  # time between each game log lines fetching (0.33)
    delay2 = 0.02  # time between each game log line processing: max number of lines processed in one second (0.02)
    encoding = 'latin-1'
    game = None
    gameName = None  # console name
    log = None  # logger instance
    logTime = 0  # time in seconds of epoch of game log
    name = 'b4'  # bot name
    output = None  # will contain the instance used to send data to the game server (default to b4_parsers.q3a.rcon.Rcon)
    privateMsg = False  # will be set to True if the game supports private messages
    queue = None  # event queue
    rconTest = False  # whether to perform RCON testing or not
    remoteLog = False
    screen = None
    storage = None  # storage module instance
    type = None
    working = True  # whether B4 is running or not
    wrapper = None  # textwrapper instance

    deadPrefix = '[DEAD]^7'  # say dead prefix
    msgPrefix = ''  # say prefix
    pmPrefix = '^8[pm]^7'  # private message prefix
    prefix = '^2%s:^3'  # B4 prefix

    # default messages in case one is missing from config file
    _messages_default = {
        "kicked_by": "$clientname^7 was kicked by $adminname^7 $reason",
        "kicked": "$clientname^7 was kicked $reason",
        "banned_by": "$clientname^7 was banned by $adminname^7 $reason",
        "banned": "$clientname^7 was banned $reason",
        "temp_banned_by": "$clientname^7 was temp banned by $adminname^7 for $banduration^7 $reason",
        "temp_banned": "$clientname^7 was temp banned for $banduration^7 $reason",
        "unbanned_by": "$clientname^7 was un-banned by $adminname^7 $reason",
        "unbanned": "$clientname^7 was un-banned $reason",
    }

    _frostBiteGameNames = ['bfbc2', 'moh', 'bf3', 'bf4']

    # === Exiting ===
    #
    # The parser runs two threads: main and handler.  The main thread is
    # responsible for the main loop parsing and queuing events, and process
    # termination. The handler thread is responsible for processing queued events
    # including raising ``SystemExit'' when a user-requested exit is needed.
    #
    # The ``SystemExit'' exception bubbles up only as far as the top of the handler
    # thread -- the ``handleEvents'' method.  To expose the exit status to the
    # ``run'' method in the main thread, we store the value in ``exitcode''.
    #
    # Since the teardown steps in ``run'' and ``handleEvents'' would occur in
    # parallel, we use a lock (``exiting'') to ensure that ``run'' waits for
    # ``handleEvents'' to finish before proceeding.
    #
    # How exiting works, in detail:
    #
    #   - the parallel loops in run() and handleEvents() are terminated only when working==False.
    #   - die() or restart() invokes shutdown() from the handler thread.
    #   - the exiting lock is acquired by shutdown() in the handler thread before it sets working=False to
    #     end both loops.
    #   - die() or restart() raises SystemExit in the handler thread after shutdown() and a few seconds delay.
    #   - when SystemExit is caught by handleEvents(), its exit status is pushed to the main context via exitcode.
    #   - handleEvents() ensures the exiting lock is released when it finishes.
    #   - run() waits to acquire the lock in the main thread before proceeding with teardown, repeating
    #     sys.exit(exitcode) from the main thread if set.
    #
    #   In the case of an abnormal exception in the handler thread, ``exitcode''
    #   will be None and the ``exiting'' lock will be released when``handleEvents''
    #   finishes so the main thread can still continue.
    #
    #   Exits occurring in the main thread do not need to be synchronised.

    exiting = threading.Lock()
    exitcode = None

    _instances = {}
    _lock = threading.Lock()

    def __call__(self, *args, **kwargs):
        if self not in self._instances:
            with self._lock:
                if self not in self._instances:
                    self._instances[self] = super(Parser, self)
        return self._instances[self]

    def __new__(cls, *args, **kwargs):
        cls.__read = cls.__read_input
        if sys.platform == 'darwin':
            cls.__read = cls.___read_input_darwin
        return object.__new__(cls)

    def __init__(self, conf, options):
        """
        Object constructor.
        :param conf: The B4 configuration file
        :param options: command line options
        """
        self._timeStart = self.time()

        # store in the parser whether we are running B4 in auto-restart mode so
        # plugins can react on this and perform different operations
        self.autorestart = options.autorestart

        if not self.loadConfig(conf):
            print('CRITICAL ERROR : COULD NOT LOAD CONFIG')
            raise SystemExit(220)

        # set game server encoding
        if self.config.has_option('server', 'encoding'):
            self.encoding = self.config.get('server', 'encoding')

        # set up logging
        logfile = self.config.getpath('b4', 'logfile')
        log2console = self.config.has_option('devmode', 'log2console') and \
                      self.config.getboolean('devmode', 'log2console')

        # make sure the logfile is writable
        logfile = b4.getWritableFilePath(logfile, True)

        try:
            logsize = b4.b4_functions.getBytes(self.config.get('b4', 'logsize'))
        except (TypeError, NoOptionError):
            logsize = b4.b4_functions.getBytes('10MB')

        # create the main logger instance
        self.log = b4.b4_output.getInstance(logfile, self.config.getint('b4', 'log_level'), logsize, log2console)

        # save screen output to self.screen
        self.screen = sys.stdout
        self.screen.write(
            'Activating log   : %s\n' % b4.getShortPath(os.path.abspath(b4.getAbsolutePath(logfile, True))))
        self.screen.flush()

        sys.stdout = b4.b4_output.STDOutLogger(self.log)
        sys.stderr = b4.b4_output.STDErrLogger(self.log)

        # setup ip addresses
        if self.gameName in 'bf3':
            self._publicIp = ''
            if self.config.has_option('server', 'public_ip'):
                self._publicIp = self.config.get('server', 'public_ip')
            self._port = ''
            if self.config.has_option('server', 'port'):
                self._port = self.config.getint('server', 'port')
        else:
            self._publicIp = self.config.get('server', 'public_ip')
            self._port = self.config.getint('server', 'port')

        self._rconPort = self._port  # if rcon port is the same as the game port, rcon_port can be omitted
        self._rconIp = self._publicIp  # if rcon ip is the same as the game port, rcon_ip can be omitted

        if self.config.has_option('server', 'rcon_ip'):
            self._rconIp = self.config.get('server', 'rcon_ip')
        if self.config.has_option('server', 'rcon_port'):
            self._rconPort = self.config.getint('server', 'rcon_port')
        if self.config.has_option('server', 'rcon_password'):
            self._rconPassword = self.config.get('server', 'rcon_password')

        if self._publicIp and self._publicIp[0:1] in ('~', '/'):
            # load ip from a file
            f = open(b4.getAbsolutePath(self._publicIp, decode=True))
            self._publicIp = f.read().strip()
            f.close()

        if self._rconIp[0:1] in ('~', '/'):
            # load ip from a file
            f = open(b4.getAbsolutePath(self._rconIp, decode=True))
            self._rconIp = f.read().strip()
            f.close()

        try:
            # resolve domain names
            self._rconIp = socket.gethostbyname(self._rconIp)
        except socket.gaierror:
            pass

        self.bot('b4_parser %s', b4.getB4versionString())
        self.bot('b4_parser Python: %s', sys.version.replace('\n', ''))
        self.bot('b4_parser Default encoding: %s', sys.getdefaultencoding())
        self.bot('b4_parser Starting %s v%s for server %s:%s (autorestart = %s)', self.__class__.__name__,
                 getattr(b4.b4_functions.getModule(self.__module__), '__version__', ' Unknown'),
                 self._rconIp, self._port, 'ON' if self.autorestart else 'OFF')

        # get events
        self.Events = b4.b4_events.eventManager
        self._eventsStats = b4.b4_events.EventsStats(self)

        self.bot('--------------------------------------------')

        # setup bot
        bot_name = self.config.get('b4', 'bot_name')
        if bot_name:
            self.name = bot_name

        bot_prefix = self.config.get('b4', 'bot_prefix')
        if bot_prefix:
            self.prefix = bot_prefix
        else:
            self.prefix = ''

        self.msgPrefix = self.prefix

        # delay between log reads
        if self.config.has_option('server', 'delay'):
            delay = self.config.getfloat('server', 'delay')
            if self.delay > 0:
                self.delay = delay

        # delay between each log's line processing
        if self.config.has_option('server', 'lines_per_second'):
            delay2 = self.config.getfloat('server', 'lines_per_second')
            if delay2 > 0:
                self.delay2 = 1 / delay2

        try:
            # setup storage module
            dsn = self.config.get('b4', 'database')
            self.storage = b4.storage.b4_storage.getStorage(dsn=dsn, dsnDict=b4.b4_functions.splitDSN(dsn),
                                                            console=self)
        except (AttributeError, ImportError) as e:
            # exit if we don't manage to set up the storage module: B4 will stop working upon Admin
            # Plugin loading, so it makes no sense to keep going with the console initialization
            self.critical('b4_parser Could not setup storage module: %s', e)

        #sys.stdout.write("Parser about to connect storage")
        # establish a connection with the database
        self.storage.connect()

        #sys.stdout.write("Parser looking for game_log")
        if self.config.has_option('server', 'game_log'):
            # open log file
            game_log = self.config.get('server', 'game_log')
            #sys.stdout.write("Parser found setting for game_log %s" % game_log)
            if game_log[0:6] == 'ftp://' or game_log[0:7] == 'sftp://' or game_log[0:7] == 'http://':
                self.remoteLog = True
                self.bot('b4_parser Working in remote-log mode: %s', game_log)

                if self.config.has_option('server', 'local_game_log'):
                    f = self.config.getpath('server', 'local_game_log')
                else:
                    logext = str(self._rconIp.replace('.', '_'))
                    logext = 'games_mp_' + logext + '_' + str(self._port) + '.log'
                    f = os.path.normpath(os.path.expanduser(logext))

                # make sure game log file can be written
                f = b4.getWritableFilePath(f, True)

                if self.config.has_option('server', 'log_append'):
                    if not (self.config.getboolean('server', 'log_append') and os.path.isfile(f)):
                        self.screen.write('Creating gamelog : %s\n' % b4.getShortPath(os.path.abspath(f)))
                        ftptempfile = open(f, "w")
                        ftptempfile.close()
                    else:
                        self.screen.write('Append to gamelog: %s\n' % b4.getShortPath(os.path.abspath(f)))
                else:
                    self.screen.write('Creating gamelog : %s\n' % b4.getShortPath(os.path.abspath(f)))
                    ftptempfile = open(f, "w")
                    ftptempfile.close()

            else:
                #self.bot('Game log is: %s', game_log)
                f = self.config.getpath('server', 'game_log')
                #sys.stdout.write("Parser opened game_log")

            self.bot('Parser Starting bot reading file: %s', os.path.abspath(f))
            self.screen.write('b4_parser Using gamelog    : %s\n' % b4.getShortPath(os.path.abspath(f)))

            if os.path.isfile(f):
                self.input = open(f, 'r')
                if self.config.has_option('server', 'seek'):
                    seek = self.config.getboolean('server', 'seek')
                    if seek:
                        self.input.seek(0, os.SEEK_END)
                else:
                    self.input.seek(0, os.SEEK_END)
            else:
                self.screen.write(">>> Cannot read file: %s\n" % os.path.abspath(f))
                self.screen.flush()
                self.critical("b4_parser Cannot read file: %s", os.path.abspath(f))

        try:
            # setup rcon
            self.output = self.OutputClass(self, (self._rconIp, self._rconPort), self._rconPassword)
        except Exception as err:
            self.screen.write(">>> Cannot setup RCON: %s\n" % err)
            self.screen.flush()
            self.critical("b4_parser Cannot setup RCON: %s" % err, exc_info=err)

        if self.config.has_option('server', 'rcon_timeout'):
            custom_socket_timeout = self.config.getfloat('server', 'rcon_timeout')
            self.output.socket_timeout = custom_socket_timeout
            self.bot('b4_parser Setting rcon socket timeout to: %0.3f sec', custom_socket_timeout)

        # allow configurable max line length
        if self.config.has_option('server', 'max_line_length'):
            self._line_length = self.config.getint('server', 'max_line_length')
            self.bot('b4_parser Setting line_length to: %s', self._line_length)

        # allow configurable line color prefix
        if self.config.has_option('server', 'line_color_prefix'):
            self._line_color_prefix = self.config.get('server', 'line_color_prefix')
            self.bot('b4_parser Setting line_color_prefix to: "%s"', self._line_color_prefix)

        # allow configurable multiline (manual line breaks)
        if self.config.has_option('server', 'multiline'):
            self._multiline = self.config.getboolean('server', 'multiline')
            self.bot('b4_parser Setting multiline to: %s', self._multiline)

        # allow configurable multiline (manual line breaks)
        if self.config.has_option('server', 'multiline_noprefix'):
            self._multiline_noprefix = self.config.getboolean('server', 'multiline_noprefix')
            self.bot('b4_parser Setting multiline_noprefix to: %s', self._multiline_noprefix)

        # testing rcon
        self.bot('b4_parser testing rcon')
        try:
            if self.rconTest:
                res = self.output.write('status')
                self.output.flush()
                self.screen.write('Testing RCON     : ')
                self.screen.flush()
                badRconReplies = ['Bad rconpassword.', 'Invalid password.']
                if res in badRconReplies:
                    self.screen.write('>>> Oops: Bad RCON password\n'
                                      '>>> Hint: This will lead to errors and render B4 without any power to interact!\n')
                    self.screen.flush()
                    time.sleep(2)
                elif res == '':
                    self.screen.write('>>> Oops: No response\n'
                                      '>>> Could be something wrong with the rcon connection to the server!\n'
                                      '>>> Hint 1: The server is not running or it is changing maps.\n'
                                      '>>> Hint 2: Check your server-ip and port.\n')
                    self.screen.flush()
                    time.sleep(2)
                else:
                    #self.log.info("b4_parser rcon test returned %s", res)
                    self.screen.write('OK\n')
        except Exception as ex:
            self.log.error("b4_parser testing rcon: %s", ex)

        #self.bot('b4_parser Loading events')
        self.loadEvents()
        self.screen.write('Loading events   : %s events loaded\n' % len(self._events))
        self.clients = b4.b4_clients.Clients(self)

        self.loadPlugins()
        self.loadArbPlugins()

        self.game = b4.b4_game.Game(self, self.gameName)

        try:
            queuesize = self.config.getint('b4', 'event_queue_size')
        except NoOptionError:
            queuesize = 50
        except ValueError as err:
            queuesize = 50
            self.warning(err)

        #self.bot('b4_parser Creating the event queue')
        self.log.debug("Parser Creating the event queue with size %s", queuesize)
        self.queue = queue.Queue(queuesize)

        atexit.register(self.shutdown)

    def getAbsolutePath(self, path, decode=False):
        """
        Return an absolute path name and expand the user prefix (~)
        :param path: the relative path we want to expand
        :param decode: True to decode bytes, False for string
        """
        #sys.stdout.write("b4_parser.Parser.getAbsolutePath\n")
        return b4.getAbsolutePath(path, decode=decode)

    def _dumpEventsStats(self):
        """
        Dump event statistics into the B4 log file.
        """
        #sys.stdout.write("b4_parser.Parser._dumpEventsStats\n")
        self._eventsStats.dumpStats()

    def start(self):
        """
        Start B4
        """
        #sys.stdout.write("b4_parser.Parser.start\n")
        self.bot("b4_parser Starting parser..")
        self.startup()
        self.say('%s ^2[ONLINE]' % b4.version)
        self.call_plugins_onLoadConfig()
        self.bot("b4_parser Starting plugins")
        self.startPlugins()
        self._eventsStats_cronTab = b4.b4_cron.CronTab(self._dumpEventsStats)
        self.cron.add(self._eventsStats_cronTab)
        self.bot("b4_parser All plugins started")
        self.pluginsStarted()
        self.bot("b4_parser Starting event dispatching thread")
        threading.Thread(target=self.handleEvents, args=()).start()
        self.bot("b4_parser Start reading game events")
        self.run()

    def die(self):
        """
        Stop B4 with the die exit status (222)
        """
        #sys.stdout.write("b4_parser.Parser.die\n")
        self.shutdown()
        self.finalize()
        time.sleep(5)
        self.exitcode = 222

    def restart(self):
        """
        Stop B4 with the restart exit status (221)
        """
        #sys.stdout.write("b4_parser.Parser.restart\n")
        self.shutdown()
        time.sleep(5)
        self.bot('Restarting...')
        self.exitcode = 221

    def upTime(self):
        """
        Amount of time B4 has been running
        """
        #sys.stdout.write("b4_parser.Parser.upTime\n")
        return self.time() - self._timeStart

    def loadConfig(self, conf):
        """
        Set the config file to load
        """
        # DEBUG
        #sys.stdout.write("self is type %s. self.log is not set yet.\n" % type(self).__name__)
        #sys.stdout.write("b4_parser.Parser.loadConfig\n")
        if not conf:
            return False

        self.config = conf
        """:type : MainConfig"""
        return True

    def saveConfig(self):
        """
        Save configration changes
        """
        sys.stdout.write("b4_parser.Parser.saveConfig\n")
        self.bot('Saving config: %s', self.config.fileName)
        return self.config.save()

    def startup(self):
        """
        Called after the parser is created before run(). Overwrite this
        for anything you need to initialize you parser with.
        """
        #sys.stdout.write("b4_parser.Parser.startup\n")
        pass

    def pluginsStarted(self):
        """
        Called after the parser loaded and started all plugins. 
        Overwrite this in parsers to take actions once plugins are ready
        """
        #sys.stdout.write("b4_parser.Parser.pluginsStarted\n")
        pass

    def pause(self):
        """
        Pause B4 log parsing
        """
        #sys.stdout.write("b4_parser.Parser.pause\n")
        self.bot('PAUSING')
        self._paused = True

    def unpause(self):
        """
        Unpause B4 log parsing
        """
        #sys.stdout.write("b4_parser.Parser.unpause\n")
        self._paused = False
        self._pauseNotice = False
        self.input.seek(0, os.SEEK_END)

    def loadEvents(self):
        """
        Load events from event manager
        """
        #sys.stdout.write("b4_parser.Parser.loadEvents\n")
        self._events = self.Events.events

    def createEvent(self, key, name=None):
        """
        Create a new event
        """
        #sys.stdout.write("b4_parser.Parser.createEvent\n")
        self.Events.createEvent(key, name)
        self._events = self.Events.events
        return self._events[key]

    def getEventID(self, key):
        """
        Get the numeric ID of an event key
        """
        #sys.stdout.write("b4_parser.Parser.getEventID\n")
        return self.Events.getId(key)

    def getEvent(self, key, data=None, client=None, target=None):
        """
        Return a new Event object for an event name
        """
        #sys.stdout.write("b4_parser.Parser.getEvent\n")
        return b4.b4_events.Event(self.Events.getId(key), data, client, target)

    def getEventName(self, key):
        """
        Get the name of an event by its key
        """
        #sys.stdout.write("b4_parser.Parser.getEventName\n")
        return self.Events.getName(key)

    def getEventKey(self, event_id):
        """
        Get the key of a given event ID
        """
        #sys.stdout.write("b4_parser.Parser.getEventKey\n")
        return self.Events.getKey(event_id)

    def getPlugin(self, plugin):
        """
        Get a reference to a loaded plugin
        """
        #sys.stdout.write("b4_parser.Parser.getPlugin\n")
        try:
            return self._plugins[plugin]
        except KeyError:
            return None

    def reloadConfigs(self):
        """
        Reload all config files
        """
        #sys.stdout.write("b4_parser.Parser.reloadConfigs\n")
        # reload main config
        self.config.load(self.config.fileName)
        for k in self._plugins:
            self.bot('Reload configuration file for plugin %s', k)
            self._plugins[k].loadConfig()
        self.updateDocumentation()

    def loadPlugins(self):
        """
        Load plugins specified in the config
        """
        #sys.stdout.write("b4_parser.Parser.loadPlugins\n")
        self.screen.write('Loading plugins  : ')
        self.screen.flush()

        extplugins_dir = self.config.get_external_plugins_dir()
        self.bot('Loading plugins (external plugin directory: %s)' % extplugins_dir)

        def _get_plugin_config(p_name, p_clazz, p_config_path=None):
            """
            Helper that load and return a configuration file for the given Plugin
            :param p_name: The plugin name
            :param p_clazz: The class implementing the plugin
            :param p_config_path: The plugin configuration file path
            """
            #sys.stdout.write("b4_parser.Parser._get_plugin_config")

            def _search_config_file(match):
                """
                Helper that returns a list of configuration files.
                :param match: The plugin name
                """
                #sys.stdout.write("b4_parser.Parser._search_config_file\n")
                # first look in the built-in plugins directory
                search = '%s%s*%s*' % (b4.getAbsolutePath('@conf\\', decode=True), os.path.sep, match)
                self.log.debug('b4_parser Searching for configuration file(s) matching: %s' % search)
                collection = glob.glob(search)
                if len(collection) > 0:
                    return collection
                # if none is found, then search in the extplugins directory
                search = '%s%s*%s*' % (
                    os.path.join(b4.getAbsolutePath(extplugins_dir, decode=True), match, 'conf'), os.path.sep, match)
                self.log.debug('b4_parser Searching for configuration file(s) matching: %s' % search)
                collection = glob.glob(search)
                return collection

            if p_config_path is None:
                # no plugin configuration file path specified: we can still load the plugin
                # if there is non need for a configuration file, otherwise we will look up one
                if not p_clazz.requiresConfigFile:
                    self.log.debug('b4_parser No configuration file specified for plugin %s: is not required either' % p_name)
                    return None

                # lookup a configuration file for this plugin
                self.warning(
                    'b4_parser No configuration file specified for plugin %s: searching a valid configuration file...' % p_name)

                search_path = _search_config_file(p_name)
                if len(search_path) == 0:
                    # raise an exception so the plugin will not be loaded (since we miss the needed config file)
                    raise b4.b4_config.ConfigFileNotFound(
                        'could not find any configuration file for plugin %s' % p_name)
                if len(search_path) > 1:
                    # log all the configuration files found so users can decide to remove some of them on the next B4 startup
                    self.warning('b4_parser Multiple configuration files found for plugin %s: %s', p_name, ', '.join(search_path))

                # if the load fails, an exception is raised and the plugin won't be loaded
                self.warning('Using %s as configuration file for plugin %s', search_path[0], p_name)
                self.bot('b4_parser Loading configuration file %s for plugin %s', search_path[0], p_name)
                return b4.b4_config.load(search_path[0])
            else:
                # configuration file specified: load it if it's found. If we are not able to find the configuration
                # file, then keep loading the plugin if such a plugin doesn't require a configuration file (optional)
                # otherwise stop loading the plugin and loag an error message.
                p_config_absolute_path = b4.getAbsolutePath(p_config_path, decode=True)
                if os.path.exists(p_config_absolute_path):
                    self.bot('b4_parser Loading configuration file %s for plugin %s', p_config_absolute_path, p_name)
                    return b4.b4_config.load(p_config_absolute_path)

                # notice missing configuration file
                self.warning('b4_parser Could not find specified configuration file %s for plugin %s', p_config_absolute_path,
                             p_name)

                if p_clazz.requiresConfigFile:
                    # stop loading the plugin
                    raise b4.b4_config.ConfigFileNotFound(
                        'plugin %s cannot be loaded without a configuration file' % p_name)

                self.warning(
                    'Not loading a configuration file for plugin %s: plugin %s can work also without a configuration file',
                    p_name, p_name)
                self.info(
                    'NOTE: plugin %s may behave differently from what expected since no user configuration file has been loaded',
                    p_name)
                return None

        plugin_list = []  # hold an unsorted plugins list used to filter plugins that needs to be excluded
        plugin_required = []  # hold a list of required plugin names which have not been specified in b4_ini
        sorted_plugin_list = []  # hold the list of plugins sorted according requirements
        plugins = OrderedDict()  # no need for OrderedDict anymore but keep for backwards compatibility!

        # here below we will parse the plugins section of b4_ini, looking for plugins to be loaded.
        # we will import needed python classes and generate configuration file instances for plugins.
        for p in self.config.get_plugins():

            if p['name'] in [plugins[i].name for i in plugins if plugins[i].name == p['name']]:
                # do not load a plugin multiple times
                self.warning('Plugin %s already loaded: avoid multiple entries of the same plugin', p['name'])
                continue

            try:
                mod = self.pluginImport(p['name'], p['path'])
                clz = getattr(mod, '%sPlugin' % p['name'].title())
                cfg = _get_plugin_config(p['name'], clz, p['conf'])
                plugins[p['name']] = PluginData(name=p['name'], module=mod, clazz=clz, conf=cfg, disabled=p['disabled'])
            except Exception as err:
                self.error('Could not load plugin %s' % p['name'], exc_info=err)

        # check for AdminPlugin
        if 'admin' not in plugins:
            # critical will exit, admin plugin must be loaded!
            self.critical('Plugin admin is essential and MUST be loaded! Cannot continue without admin plugin')

        # at this point we have an OrderedDict of PluginData of plugins listed in b4_ini and which can be loaded
        # correctly: all the plugins which have not been installed correctly, but are specified in b4_ini, have
        # been already excluded. next we build a list of PluginData instances, then we will sort it according
        # to plugin order importance:
        #   - we'll try to load other plugins required by a listed one
        #   - we'll remove plugin that do not meet requirements

        def _get_plugin_data(p_data):
            """
            Return a list of PluginData of plugins needed by the current one
            :param p_data: A PluginData containing plugin information
            :return: list[PluginData] a list of PluginData of plugins needed by the current one
            """
            #sys.stdout.write("b4_parser.Parser._get_plugin_data\n")
            if p_data.clazz:

                # check for correct B4 version
                if p_data.clazz.requiresVersion \
                        and b4.b4_update.B4version(p_data.clazz.requiresVersion) \
                        > b4.b4_update.B4version(b4.__version__):
                    raise MissingRequirement(
                        'plugin %s requires B4 version %s (you have version %s) : please update your '
                        'B4 if you want to run this plugin' % (
                            p_data.name, p_data.clazz.requiresVersion, b4.__version__))

                # check if the current game support this plugin (this may actually exclude more than one plugin
                # in case a plugin is built on top of an incompatible one, due to plugin dependencies)
                if p_data.clazz.requiresParsers and self.gameName not in p_data.clazz.requiresParsers:
                    raise MissingRequirement('plugin %s is not compatible with %s parser : supported games are : %s' % (
                        p_data.name, self.gameName, ', '.join(p_data.clazz.requiresParsers)))

                # check if the plugin needs a particular storage protocol to work
                if p_data.clazz.requiresStorage and self.storage.protocol not in p_data.clazz.requiresStorage:
                    raise MissingRequirement('plugin %s is not compatible with the storage protocol being used (%s) : '
                                             'supported protocols are : %s' % (p_data.name, self.storage.protocol,
                                                                               ', '.join(p_data.clazz.requiresStorage)))

                # check for plugin dependency
                if p_data.clazz.requiresPlugins:
                    # DFS: look first at the whole requirement tree and try to load from ground up
                    collection = [p_data]
                    for r in p_data.clazz.requiresPlugins:
                        if r not in plugins and r not in plugin_required:
                            try:
                                # missing requirement, try to load it
                                self.log.debug('Plugin %s has unmet dependency : %s : trying to load plugin %s...' % (
                                    p_data.name, r, r))
                                collection += _get_plugin_data(PluginData(name=r))
                                self.log.debug('Plugin %s dependency satisfied: %s' % (p_data.name, r))
                            except Exception as ex:
                                raise MissingRequirement(
                                    'missing required plugin: %s : %s' % (r, extract_tb(sys.exc_info()[2])), ex)

                    return collection

            # plugin has not been loaded manually nor a previous automatic load attempt has been done
            if p_data.name not in plugins and p_data.name not in plugin_required:
                # we are at the bottom step where we load a new requirement by importing the
                # plugin module, class and configuration file. If the following generate an exception, recursion
                # will catch it here above and raise it back so we can exclude the first plugin in the list from load
                self.log.debug('Looking for plugin %s module and configuration file...' % p_data.name)
                p_data.module = self.pluginImport(p_data.name)
                p_data.clazz = getattr(p_data.module, '%sPlugin' % p_data.name.title())
                p_data.conf = _get_plugin_config(p_data.name, p_data.clazz)
                plugin_required.append(p_data.name)  # load just once

            return [p_data]

        # construct a list of all the plugins which needs to be loaded
        # here below we will discard all the plugin which have unmet dependency
        for plugin_name, plugin_data in plugins.items():
            try:
                plugin_list += _get_plugin_data(plugin_data)
            except MissingRequirement as err:
                self.error('Could not load plugin %s' % plugin_name, exc_info=err)

        plugin_dict = {x.name: x for x in plugin_list}  # dict(str, PluginData)
        plugin_data = plugin_dict.pop('admin')  # remove admin plugin from dict
        plugin_list.remove(plugin_data)  # remove admin plugin from unsorted list
        sorted_plugin_list.append(plugin_data)  # put admin plugin as first and discard from the sorting

        # sort remaining plugins according to their inclusion requirements
        self.bot('Sorting plugins according to their dependency tree...')
        sorted_list = [y for y in \
                       b4.b4_functions.topological_sort([(x.name, set(x.clazz.requiresPlugins +
                                                                      [z for z in
                                                                       x.clazz.loadAfterPlugins
                                                                       if z in plugin_dict]))
                                                         for
                                                         x in plugin_list])]

        for plugin_name in sorted_list:
            sorted_plugin_list.append(plugin_dict[plugin_name])

        # make sure that required plugins are enabled (both if loaded in b4_ini or loaded automatically)
        for plugin_data in sorted_plugin_list:
            if plugin_data.disabled:
                if plugin_data.name == 'admin':
                    plugin_data.enabled = True
                else:
                    if plugin_data.clazz.requiresPlugins:
                        for req in plugin_data.clazz.requiresPlugins:
                            plugin_dict = {x.name: x for x in sorted_plugin_list}
                            if req in plugin_dict and plugin_dict[req].enabled:
                                plugin_data.enabled = True

        # notice in log for later inspection
        self.bot('Ready to create plugin instances: %s' % ', '.join([x.name for x in sorted_plugin_list]))

        plugin_num = 1
        self._plugins = OrderedDict()
        for plugin_data in sorted_plugin_list:

            # plugin_conf_path = '--' if plugin_data.conf is None else plugin_data.conf.fileName
            if plugin_data.conf is None:
                plugin_conf_path = '--'
            else:
                plugin_conf_path = plugin_data.conf.fileName

            try:
                self.bot('Loading plugin #%s : %s [%s]', plugin_num, plugin_data.name, plugin_conf_path)
                self._plugins[plugin_data.name] = plugin_data.clazz(self, plugin_data.conf)
            except Exception as err:
                self.error('Could not load plugin %s' % plugin_data.name, exc_info=err)
                self.screen.write('x')
            else:
                if plugin_data.disabled:
                    self.info("Disabling plugin %s" % plugin_data.name)
                    self._plugins[plugin_data.name].disable()
                plugin_num += 1
                version = getattr(plugin_data.module, '__version__', 'Unknown Version')
                author = getattr(plugin_data.module, '__author__', 'Unknown Author')
                self.bot('Plugin %s (%s - %s) loaded', plugin_data.name, version, author)
                self.screen.write('.')
            finally:
                self.screen.flush()

    def call_plugins_onLoadConfig(self):
        """
        For each loaded plugin, call the onLoadConfig hook.
        """
        #sys.stdout.write("b4_parser.Parser.call_plugins_onLoadConfig\n")
        for plugin_name in self._plugins:
            p = self._plugins[plugin_name]
            p.onLoadConfig()

    def loadArbPlugins(self):
        """
        Load must have plugins.
        """
        #sys.stdout.write("b4_parser.Parser.loadArbPlugins\n")
        # if we fail to load one of those plugins, B4 will exit
        _mandatory_plugins = ['ftpytail', 'sftpytail', 'httpytail']

        def _load_plugin(console, plugin_name):
            """
            Helper which takes care of loading a single plugin.
            :param console: The current console instance
            :param plugin_name: The name of the plugin to load
            """
            #sys.stdout.write("b4_parser.Parser._load_plugin")
            try:
                console.bot('Loading plugin : %s', plugin_name)
                plugin_module = console.pluginImport(plugin_name)
                console._plugins[plugin_name] = getattr(plugin_module, '%sPlugin' % plugin_name.title())(console)
                version = getattr(plugin_module, '__version__', 'Unknown Version')
                author = getattr(plugin_module, '__author__', 'Unknown Author')
            except Exception as e:
                console.screen.write('x')
                if plugin_name in _mandatory_plugins:
                    # critical will stop B4 from running
                    console.screen.write('\n')
                    console.screen.write('>>> CRITICAL: missing mandatory plugin: %s\n' % plugin_name)
                    console.critical('Could not start B4 without %s plugin' % plugin_name, exc_info=e)
                else:
                    console.error('Could not load plugin %s' % plugin_name, exc_info=e)
            else:
                console.screen.write('.')
                console.bot('Plugin %s (%s - %s) loaded', plugin_name, version, author)
            finally:
                console.screen.flush()

        if 'publist' not in self._plugins:
            _load_plugin(self, 'publist')

        if self.config.has_option('server', 'game_log'):
            game_log = self.config.get('server', 'game_log')
            remote_log_plugin = None
            if game_log.startswith('ftp://'):
                remote_log_plugin = 'ftpytail'
            elif game_log.startswith('sftp://'):
                remote_log_plugin = 'sftpytail'
            elif game_log.startswith('http://'):
                remote_log_plugin = 'httpytail'

            if remote_log_plugin and remote_log_plugin not in self._plugins:
                _load_plugin(self, remote_log_plugin)

        self.screen.write(' (%s)\n' % len(self._plugins.keys()))
        self.screen.flush()

    def pluginImport(self, name, path=None):
        """
        Import a single plugin.
        :param name: The plugin name
        """
        #sys.stdout.write("b4_parser.Parser.pluginImport\n")
        if path is None:
            path = os.path.join(str(b4.getB4Path(True)), 'plugins', name, "__init__.py")

        if not os.path.isfile(path):
            self.log.info("b4_parser %s not found in %s" % (name, path))
            # look in extplugins
            path = os.path.join(str(b4.getB4Path(True)), 'extplugins', name, "__init__.py")

        spec = importlib.util.spec_from_file_location(name, path)

        if spec is None:
            raise ImportError(f"Could not load spec for module '{name}' at: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except FileNotFoundError as e:
            raise ImportError(f"{e.strerror}: {path}") from e
        return module

    def startPlugins(self):
        """
        Start all loaded plugins.
        """
        #sys.stdout.write("b4_parser.Parser.startPlugins\n")
        self.screen.write('Starting plugins : ')
        self.screen.flush()

        def start_plugin(console, p_name):
            """
            Helper which handles the startup of a single plugin
            :param console: the console instance
            :param p_name: the plugin name
            """
            #sys.stdout.write("b4_parser.Parser.start_plugin")
            p = console._plugins[p_name]
            p.onStartup()
            #sys.stdout.write("b4_parser.Parser.start_plugin onStartup complete")
            p.start()
            #sys.stdout.write("b4_parser.Parser.start_plugin start complete")

        plugin_num = 1

        for plugin_name in self._plugins:

            try:
                self.bot('b4_parser Starting plugin #%s : %s' % (plugin_num, plugin_name))
                start_plugin(self, plugin_name)
                self.bot('b4_parser Started plugin #%s : %s' % (plugin_num, plugin_name))
            except Exception as err:
                self.error("b4_parser Could not start plugin %s" % plugin_name, exc_info=err)
                self.screen.write('x')
            else:
                self.screen.write('.')
                plugin_num += 1
            finally:
                self.screen.flush()

        self.screen.write(' (%s)\n' % str(plugin_num - 1))

    def disablePlugins(self):
        """
        Disable all plugins except for 'admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail', 'cod7http'
        """
        #sys.stdout.write("b4_parser.Parser.disablePlugins\n")
        for k in self._plugins:
            if k not in ('admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail', 'cod7http'):
                p = self._plugins[k]
                self.bot('b4_parser Disabling plugin: %s', k)
                p.disable()

    def enablePlugins(self):
        """
        Enable all plugins except for 'admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail', 'cod7http'
        """
        #sys.stdout.write("b4_parser.Parser.enablePlugins\n")
        for k in self._plugins:
            if k not in ('admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail', 'cod7http'):
                p = self._plugins[k]
                self.bot('Enabling plugin: %s', k)
                p.enable()

    def getMessage(self, msg, *args):
        """
        Return a message from the config file
        """
        #sys.stdout.write("b4_parser.Parser.getMessage\n")
        try:
            msg = self._messages[msg]
        except KeyError:
            try:
                msg = self._messages[msg] = self.config.getTextTemplate('messages', msg)
            except Exception as err:
                self.warning("Falling back on default message for '%s': %s" % (msg, err))
                msg = b4.b4_functions.vars2printf(self._messages_default.get(msg, '')).strip()

        if len(args):
            if type(args[0]) == dict:
                return msg % args[0]
            else:
                return msg % args
        else:
            return msg

    @staticmethod
    def getMessageVariables(*args, **kwargs):
        """
        Dynamically generate a dictionary of fields available for messages in config file.
        """
        #sys.stdout.write("b4_parser.Parser.getMessageVariables\n")
        variables = {}
        for obj in args:
            if obj is None:
                continue
            if type(obj).__name__ in ('str', 'unicode'):
                if obj not in variables:
                    variables[obj] = obj
            else:
                for attr in vars(obj):
                    pattern = re.compile('[\W_]+')
                    cleanattr = pattern.sub('', attr)  # trim any underscore or any non alphanumeric character
                    variables[cleanattr] = getattr(obj, attr)

        for key, obj in kwargs.items():
            # self.log.debug('Type of kwarg %s: %s' % (key, type(obj).__name__))
            if obj is None:
                continue
            if type(obj).__name__ in ('str', 'unicode'):
                if key not in variables:
                    variables[key] = obj
            # elif type(obj).__name__ == 'instance':
            # self.log.debug('Classname of object %s: %s' % (key, obj.__class__.__name__))
            else:
                for attr in vars(obj):
                    pattern = re.compile('[\W_]+')
                    cleanattr = pattern.sub('', attr)  # trim any underscore or any non alphanumeric character
                    currkey = ''.join([key, cleanattr])
                    variables[currkey] = getattr(obj, attr)

        return variables

    def getCommand(self, cmd, **kwargs):
        """
        Return a reference to a loaded command
        """
        #sys.stdout.write("b4_parser.Parser.getCommand\n")
        try:
            cmd = self._commands[cmd]
        except KeyError:
            return None

        return cmd % kwargs

    @Memoize
    def getGroup(self, data):
        """
        Return a valid Group from storage.
        <data> can be either a group keyword or a group level.
        Raises KeyError if group is not found.
        """
        #sys.stdout.write("b4_parser.Parser.getGroup\n")
        if type(data) is int or isinstance(data, str) and data.isdigit():
            g = b4.b4_clients.Group(level=data)
        else:
            g = b4.b4_clients.Group(keyword=data)
        return self.storage.getGroup(g)

    def getGroupLevel(self, data):
        """
        Return a valid Group level.
        <data> can be either a group keyword or a group level.
        Raises KeyError if group is not found.
        """
        #sys.stdout.write("b4_parser.Parser.getGroupLevel\n")
        group = self.getGroup(data)
        return group.level

    def getTzOffsetFromName(self, tz_name=None):
        """
        Returns the timezone offset given its name.
        :param tz_name: The timezone name
        :return: tuple
        """
        #sys.stdout.write("b4_parser.Parser.getTzOffsetFromName\n")
        if tz_name:
            if not tz_name in b4.b4_timezones.timezones:
                self.warning(
                    "b4_parser Unknown timezone name [%s]: falling back to auto-detection mode. Valid timezone codes "
                    "can be found on http://wiki.bigbrotherbot.net/doku.php/usage:available_timezones" % tz_name)
            else:
                self.info("Using timezone: %s : %s" % (tz_name, b4.b4_timezones.timezones[tz_name]))
                return b4.b4_timezones.timezones[tz_name], tz_name

        # AUTO-DETECT TZ NAME/OFFSET
        self.log.debug("b4_parser Auto detecting timezone information...")

        # this will compute the timezone offset from UTC
        tz_info = datetime.timedelta(hours=time.timezone / -3600)

        self.info("b4_parser Using timezone offset of: %s " % (time.timezone / -3600))
        return tz_info

    def formatTime(self, gmttime, tz_name=None):
        """
        Return a time string formatted to local time in the b4 config time_format
        :param gmttime: The current GMT time
        :param tz_name: The timezone name to be used for time formatting
        """
        #sys.stdout.write("b4_parser.Parser.formatTime\n")
        if tz_name:
            # if a timezone name has been specified try to use it to format the given gmttime
            tz_name = str(tz_name).strip().upper()
            try:
                # used when the user manually specifies the offset (i.e: !time +4)
                tz_offset = float(tz_name) * 3600
            except ValueError:
                # treat it as a timezone name (can potentially fallback to autodetection mode)
                tz_offset, tz_name = self.getTzOffsetFromName(tz_name)
        else:
            # use the timezone name specified in b4 main configuration file (if specified),
            # or make use of the timezone offset autodetection implemented in getTzOffsetFromName
            tz_name = None
            if self.config.has_option('b4', 'time_zone'):
                tz_name = self.config.get('b4', 'time_zone').strip().upper()
                tz_name = tz_name if tz_name and tz_name != 'AUTO' else None
            tz_offset, tz_name = self.getTzOffsetFromName(tz_name)

        time_format = self.config.get('b4', 'time_format').replace('%Z', tz_name).replace('%z', tz_name)
        self.log.debug('b4_parser Formatting time with timezone [%s], tzOffset : %s' % (tz_name, tz_offset))
        return time.strftime(time_format, time.gmtime(gmttime + int(tz_offset * 3600)))

    def run(self):
        """
        Main worker thread for B4
        """
        #self.verbose3("b4_parser.Parser.run")
        self.screen.write('Startup complete : B4 is running! Let\'s get to work!\n\n')
        self.screen.write('If you run into problems check your B4 log file for more information\n')
        self.screen.flush()
        self.say('B4 ^2[Startup Complete]')
        self.updateDocumentation()

        log_time_start = None
        log_time_last = 0
        while self.working:
            if self._paused:
                if not self._pauseNotice:
                    self.bot('b4_parser PAUSED - not parsing any lines: B4 will be out of sync')
                    self._pauseNotice = True
            else:
                lines = self.read()
                if lines:
                    for line in lines:
                        line = str(line).strip()
                        if line and self._lineTime is not None:
                            # Track the log file time changes. This is mostly for
                            # parsing old log files for testing and to have time increase
                            # predictably
                            m = self._lineTime.match(line)
                            if m:
                                log_time_current = (int(m.group('minutes')) * 60) + int(m.group('seconds'))
                                if log_time_start and log_time_current - log_time_start < log_time_last:
                                    # Time in log has reset
                                    log_time_start = log_time_current
                                    log_time_last = 0
                                    self.log.debug('b4_parser log time reset %d' % log_time_current)
                                elif not log_time_start:
                                    log_time_start = log_time_current

                                # Remove starting offset, we want the first line to be at 0 seconds
                                log_time_current -= log_time_start
                                self.logTime += log_time_current - log_time_last
                                log_time_last = log_time_current

                            self.console(line)

                            try:
                                self.parseLine(line)
                            except SystemExit:
                                raise
                            except Exception as msg:
                                self.error('b4_parser Could not parse line %s: %s', msg, extract_tb(sys.exc_info()[2]))

                            time.sleep(self.delay2)

            time.sleep(self.delay)

        self.bot('b4_parser Stop reading')

        with self.exiting:
            self.input.close()
            self.output.close()

            if self.exitcode:
                sys.exit(self.exitcode)

    def parseLine(self, line):
        """
        Parse a single line from the log file
        """
        #self.verbose3("b4_parser.Parser.parseLine")
        m = re.match(self._lineFormat, line)
        if m:
            self.queueEvent(b4.b4_events.Event(self.getEventID('EVT_UNKNOWN'), m.group(2)[:1]))

    def registerHandler(self, event_name, event_handler):
        """
        Register an event handler.
        """
        #self.verbose3("b4_parser.Parser.registerHandler")
        self.log.debug('b4_parser %s: register event <%s>', event_handler.__class__.__name__, self.getEventName(event_name))
        if not event_name in self._handlers:
            self._handlers[event_name] = []
        if event_handler not in self._handlers[event_name]:
            self._handlers[event_name].append(event_handler)

    def unregisterHandler(self, event_handler):
        """
        Unregister an event handler.
        """
        #self.verbose3("b4_parser.Parser.unregisterHandler")
        for event_name in self._handlers:
            if event_handler in self._handlers[event_name]:
                self.log.debug('b4_parser %s: unregister event <%s>', event_handler.__class__.__name__, self.getEventName(event_name))
                self._handlers[event_name].remove(event_handler)

    def queueEvent(self, event, expire=30):
        # DK changed from 10 to 30 as a test
        """
        QueEvents.gevent for processing.
        """
        #self.verbose3("b4_parser.Parser.queueEvent")
        if not hasattr(event, 'type'):
            return False
        elif event.type in self._handlers:  # queue only if there are handlers to listen for this event
            self.verbose('b4_parser Queueing event %s : %s', self.getEventName(event.type), event.data)
            try:
                time.sleep(0.001)  # wait a bit so event doesn't get jumbled
                self.queue.put((self.time(), self.time() + expire, event), True, 2)
                return True
            except queue.Full:
                self.error('b4_parser **** Event queue was full (%s)', self.queue.qsize())
                return False

        return False

    def handleEvents(self):
        """
        Event handler thread.
        """
        self.info("b4_parser.Parser.handleEvents; thread %r" % threading.current_thread().ident)
        while self.working:
            added, expire, event = self.queue.get(True)
            if event.type == self.getEventID('EVT_EXIT') or event.type == self.getEventID('EVT_STOP'):
                self.working = False

            event_name = self.getEventName(event.type)
            # determine how long it's been in queue
            self._eventsStats.add_event_wait((self.time() - added) * 1000)
            if self.time() >= expire:  # events can only sit in the queue until expire time
                self.error('**** Event sat in queue too long: %s %s', event_name, self.time() - expire)
            else:
                nomore = False
                for hfunc in self._handlers[event.type]:
                    if not hfunc.isEnabled():
                        continue
                    elif nomore:
                        break

                    self.verbose('Parsing event: %s: %s', event_name, hfunc.__class__.__name__)
                    timer_plugin_begin = time.perf_counter()
                    try:
                        hfunc.parseEvent(event)
                        time.sleep(0.001)
                    except b4.b4_events.VetoEvent:
                        # plugin called for event halt, do not continue processing
                        self.bot('Event %s vetoed by %s', event_name, str(hfunc))
                        nomore = True
                    except SystemExit as e:
                        self.exitcode = e.code
                    except Exception as msg:
                        self.error('Handler %s could not handle event %s: %s: %s %s', hfunc.__class__.__name__,
                                   event_name, msg.__class__.__name__, msg, extract_tb(sys.exc_info()[2]))
                    finally:
                        elapsed = time.perf_counter() - timer_plugin_begin
                        self._eventsStats.add_event_handled(hfunc.__class__.__name__, event_name, elapsed * 1000)

        self.bot('Shutting down event handler')

        # releasing lock if it was set by self.shutdown() for instance
        if self.exiting.locked():
            self.exiting.release()

    def write(self, msg, maxRetries=None, socketTimeout=None):
        """
        Write a message to Rcon/Console
        """
        #self.verbose3("b4_parser.Parser.write")
        if self.output:
            res = self.output.write(str(msg))
            self.output.flush()
            return str(res)

    def writelines(self, msg):
        """
        Write a sequence of messages to Rcon/Console. Optimized for speed.
        :param msg: The message to be sent to Rcon/Console.
        """
        #self.verbose3("b4_parser.Parser.writelines")
        if self.output and msg:
            res = self.output.writelines(msg)
            self.output.flush()
            return res

    def __read_input(self, game_log):
        """
        Read lines from the log file
        :param game_log: The game log file pointer
        """
        #self.verbose3("b4_parser.Parser.__read_input")
        return game_log.readlines()

    def ___read_input_darwin(self, game_log):
        """
        Read lines from the log file (darwin version)
        :param game_log: The game log file pointer
        """
        #self.verbose3("b4_parser.Parser.___read_input_darwin")
        return [game_log.readline()]

    def read(self):
        """
        Read from game server log file
        """
        #self.verbose3("b4_parser.Parser.read")
        if not hasattr(self, 'input'):
            self.critical("Cannot read game log file: check that you have a correct "
                          "value for the 'game_log' setting in your main config file")

        # Getting the stats of the game log (we are looking for the size)
        filestats = os.fstat(self.input.fileno())
        # Compare the current cursor position against the current file size,
        # if the cursor is at a number higher than the game log size, then
        # there's a problem
        if self.input.tell() > filestats.st_size:
            self.log.debug('Parser: game log is suddenly smaller than it was before (%s bytes, now %s), '
                       'the log was probably either rotated or emptied. B4 will now re-adjust to the new '
                       'size of the log' % (str(self.input.tell()), str(filestats.st_size)))
            self.input.seek(0, os.SEEK_END)
        # NOTE: __read is defined at runtime in __new__
        return self.__read(self.input)

    def shutdown(self):
        """
        Shutdown B4.
        """
        self.verbose3("b4_parser.Parser.shutdown")
        try:
            if self.working and self.exiting.acquire():
                self.bot('b4_parser Shutting down...')
                self.working = False
                for k, plugin in self._plugins.items():
                    plugin.parseEvent(b4.b4_events.Event(self.getEventID('EVT_STOP'), ''))
                if self._cron:
                    self.bot('b4_parser Stopping cron')
                    self._cron.stop()
                if self.storage:
                    self.bot('b4_parser Shutting down database connection')
                    self.storage.shutdown()
        except Exception as e:
            self.error(e)

    def finalize(self):
        """
        Commons operation to be done on B4 shutdown.
        Called internally by b4_parser.die()
        """
        self.verbose3("b4_parser.Parser.finalize")
        if b4.getPlatform() in ('linux', 'darwin'):
            # check for PID file if B4 has been started using the provided BASH initialization scripts.
            b4_name = os.path.basename(self.config.fileName)
            for x in ('.xml', '.ini'):
                b4_name = b4.b4_functions.right_cut(b4_name, x)

            pidpath = os.path.join(b4.getAbsolutePath('@b4/', decode=True), '..', 'scripts', 'pid', '%s.pid' % b4_name)
            if os.path.isfile(pidpath):
                self.bot('b4_parser Found PID file : %s : attempt to remove it' % pidpath)
                try:
                    os.unlink(pidpath)
                except Exception as e:
                    self.error('b4_parser Could not remove PID file (%s) : %s' % (pidpath, e))
                else:
                    self.bot('b4_parser PID file removed (%s)' % pidpath)

    def getWrap(self, text):
        """
        Returns a sequence of lines for text that fits within the limits.
        And wrap if \n character encountered.
        :param text: The text that needs to be split.
        """
        self.verbose3("b4_parser.Parser.getWrap")
        if not text:
            return []

        # remove all color codes if not needed
        if not self._use_color_codes:
            text = self.stripColors(text)

        if not self.wrapper:
            # initialize the text wrapper if not already instantiated
            self.wrapper = TextWrapper(width=self._line_length, drop_whitespace=True,
                                       break_long_words=True, break_on_hyphens=False)

        self.verbose3("b4_parser getWrap 1*")
        # Apply wrap + manual linebreak
        if self._multiline:
            wrapped_text = []
            for line in text.split(r'\n'):
                if line.strip() != '':
                    wrapped_text.extend(self.wrapper.wrap(line))
        # Apply only wrap
        else:
            wrapped_text = self.wrapper.wrap(text)

        self.verbose3("b4_parser getWrap 2*")
        if self._use_color_codes:
            lines = []
            color = self._line_color_prefix
            self.verbose3("b4_parser getWrap 3*")
            for line in wrapped_text:
                if not lines or self._multiline_noprefix:
                    lines.append('%s%s' % (color, line))
                else:
                    lines.append('^3>%s%s' % (color, line))
                match = re.findall(self._reColor, line)
                if match:
                    color = match[-1]
            self.verbose3("b4_parser getWrap 4*")
            return lines
        else:
            if self._multiline_noprefix:
                lines = wrapped_text
            else:
                # we still need to add the > prefix w/o color codes
                # to all the lines except the first one
                lines = [wrapped_text[0]]
                if len(wrapped_text) > 1:
                    self.verbose3("b4_parser getWrap 5*")
                    for line in wrapped_text[1:]:
                        lines.append('>%s' % line)
            self.verbose3("b4_parser getWrap 6*")
            return lines

    def error(self, msg, *args, **kwargs):
        """
        Log an ERROR message.
        """
        self.log.error(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """
        Log a DEBUG message.
        """
        self.log.debug(msg, *args, **kwargs)

    def bot(self, msg, *args, **kwargs):
        """
        Log a BOT message.
        """
        self.log.bot(msg, *args, **kwargs)

    def verbose(self, msg, *args, **kwargs):
        """
        Log a VERBOSE message.
        """
        self.log.verbose(msg, *args, **kwargs)

    def verbose2(self, msg, *args, **kwargs):
        """
        Log an EXTRA VERBOSE message.
        """
        self.log.verbose2(msg, *args, **kwargs)

    def verbose3(self, msg, *args, **kwargs):
        """
        Log an EXTRA VERBOSE message.
        """
        self.log.verbose3(msg, *args, **kwargs)

    def console(self, msg, *args, **kwargs):
        """
        Log a CONSOLE message.
        """
        self.log.console(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """
        Log a WARNING message.
        """
        self.log.warning(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Log an INFO message.
        """
        self.log.info(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """
        Log an EXCEPTION message.
        """
        self.log.exception(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Log a CRITICAL message and shutdown B4.
        """
        self.log.critical(msg, *args, **kwargs)
        self.shutdown()
        self.finalize()
        time.sleep(2)
        self.exitcode = 220
        raise SystemExit(self.exitcode)

    @staticmethod
    def time():
        """
        Return the current time in GMT/UTC.
        """
        #sys.stdout.write("b4_parser.Parser.time\n")
        return int(time.time())

    def _get_cron(self):
        """
        Instantiate the main Cron object.
        """
        #sys.stdout.write("b4_parser.Parser._get_cron\n")
        if not self._cron:
            self._cron = b4.b4_cron.Cron(self)
            self._cron.start()
            #sys.stdout.write("b4_parser.Parser._get_cron continuing\n")
        return self._cron

    cron = property(_get_cron)

    def stripColors(self, text):
        """
        Remove color codes from the given text.
        :param text: the text to clean from color codes.
        :return: str
        """
        #sys.stdout.write("b4_parser.Parser.stripColors\n")
        return re.sub(self._reColor, '', text).strip()

    def isFrostbiteGame(self, gamename=None):
        """
        Tells whether we are running a Frostbite based game.
        :return: True if we are running a Frostbite game, False otherwise
        """
        #sys.stdout.write("b4_parser.Parser.isFrostbiteGame\n")
        if not gamename:
            gamename = self.gameName
        return gamename in self._frostBiteGameNames

    def updateDocumentation(self):
        """
        Create a documentation for all available commands.
        """
        #sys.stdout.write("b4_parser.Parser.updateDocumentation\n")
        if self.config.has_section('autodoc'):
            try:
                from b4.tools.documentationBuilder import DocBuilder
                docbuilder = DocBuilder(self)
                docbuilder.save()
            except Exception as err:
                self.error("b4_parser Failed to generate user documentation")
                self.exception(err)
        else:
            self.info('b4_parser No user documentation generated: to enable update your configuration file')

    ####################################################################################################################
    #                                                                                                                  #
    #   INHERITING CLASSES MUST IMPLEMENTS THE FOLLOWING METHODS                                                       #
    #   PLUGINS THAT ARE GAME INDEPENDENT ASSUME THOSE METHODS EXIST                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def getPlayerList(self):
        """
        Query the game server for connected players.
        return a dict having players' id for keys and players' data as another dict for values
        """
        #sys.stdout.write("b4_parser.Parser.getPlayerList\n")
        raise NotImplementedError

    def authorizeClients(self):
        """
        For all connected players, fill the client object with properties allowing to find 
        the user in the database (usually guid, or punkbuster id, ip) and call the
        Client.auth() method 
        """
        #sys.stdout.write("b4_parser.Parser.authorizeClients\n")
        raise NotImplementedError

    def sync(self):
        """
        For all connected players returned by self.getPlayerList(), get the matching Client
        object from self.clients (with self.clients.getByCID(cid) or similar methods) and
        look for inconsistencies. If required call the client.disconnect() method to remove
        a client from self.clients.
        This is mainly useful for games where clients are identified by the slot number they
        occupy. On map change, a player A on slot 1 can leave making room for player B who
        connects on slot 1.
        """
        #sys.stdout.write("b4_parser.Parser.sync\n")
        raise NotImplementedError

    def say(self, msg, *args):
        """
        Broadcast a message to all players
        """
        #sys.stdout.write("b4_parser.Parser.say\n")
        raise NotImplementedError

    def saybig(self, msg, *args):
        """
        Broadcast a message to all players in a way that will catch their attention.
        """
        #sys.stdout.write("b4_parser.Parser.saybig\n")
        raise NotImplementedError

    def message(self, client, text, *args):
        """
        Display a message to a given player
        """
        #sys.stdout.write("b4_parser.Parser.message\n")
        raise NotImplementedError

    def kick(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Kick a given player
        """
        #sys.stdout.write("b4_parser.Parser.kick\n")
        raise NotImplementedError

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Ban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN', data={'reason': reason, 
        'admin': admin}, client=target)
        """
        #sys.stdout.write("b4_parser.Parser.ban\n")
        raise NotImplementedError

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Unban a given player on the game server
        """
        #sys.stdout.write("b4_parser.Parser.unban\n")
        raise NotImplementedError

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """
        Tempban a given player on the game server and in case of success
        fire the event ('EVT_CLIENT_BAN_TEMP', data={'reason': reason, 
        'duration': duration, 'admin': admin}, client=target)
        """
        #sys.stdout.write("b4_parser.Parser.tempban\n")
        raise NotImplementedError

    def getMap(self):
        """
        Return the current map/level name
        """
        #sys.stdout.write("b4_parser.Parser.getMap\n")
        raise NotImplementedError

    def getNextMap(self):
        """
        Return the next map/level name to be played
        """
        #sys.stdout.write("b4_parser.Parser.getNextMap\n")
        raise NotImplementedError

    def getMaps(self):
        """
        Return the available maps/levels name
        """
        #sys.stdout.write("b4_parser.Parser.getMaps\n")
        raise NotImplementedError

    def rotateMap(self):
        """
        Load the next map/level
        """
        #sys.stdout.write("b4_parser.Parser.rotateMap\n")
        raise NotImplementedError

    def changeMap(self, map_name):
        """
        Load a given map/level
        Return a list of suggested map names in cases it fails to recognize the map that was provided
        """
        #sys.stdout.write("b4_parser.Parser.changeMap\n")
        raise NotImplementedError

    def getPlayerPings(self, filter_client_ids=None):
        """
        Returns a dict having players' id for keys and players' ping for values
        :param filter_client_ids: If filter_client_id is an iterable, only return values for the given client ids.
        """
        #sys.stdout.write("b4_parser.Parser.getPlayerPings\n")
        raise NotImplementedError

    def getPlayerScores(self):
        """
        Returns a dict having players' id for keys and players' scores for values
        """
        #sys.stdout.write("b4_parser.Parser.getPlayerScores\n")
        raise NotImplementedError

    def inflictCustomPenalty(self, penalty_type, client, reason=None, duration=None, admin=None, data=None):
        """
        Called if b4_admin.penalizeClient() does not know a given penalty type. 
        Overwrite this to add customized penalties for your game like 'slap', 'nuke', 
        'mute', 'kill' or anything you want.
        /!\ This method must return True if the penalty was inflicted.
        """
        #sys.stdout.write("b4_parser.Parser.inflictCustomPenalty\n")
        pass


class StubParser(object):
    """
    Parser implementation used when dealing with the Storage module while updating B4 database.
    """

    screen = sys.stdout

    def __init__(self):
        class StubSTDOut(object):
            def write(self, *args, **kwargs):
                pass

        if not b4.b4_functions.main_is_frozen():
            self.screen = StubSTDOut()

    def bot(self, msg, *args, **kwargs):
        pass

    def info(self, msg, *args, **kwargs):
        pass

    def debug(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass

    def verbose(self, msg, *args, **kwargs):
        pass

    def verbose2(self, msg, *args, **kwargs):
        pass

    def critical(self, msg, *args, **kwargs):
        pass
