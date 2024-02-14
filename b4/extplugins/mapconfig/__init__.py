# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
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

# 2019.05.29 try a getCmd for pagear
# 2020.11.20 add timelimit

# import b4
# from b4_clients import Client
# import b4_events
import b4.b4_plugin
import os
#import platform
import random

# from b4.b4_clients import Client
from b4.b4_functions import getCmd
from configparser import NoOptionError

__version__ = '0.1'
__author__ = 'isopropanol'

try:
    # import the getCmd function
    import b4_functions.getCmd as getCmd
except ImportError:
    # keep backward compatibility
    def getCmd(instance, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(instance, cmd):
            func = getattr(instance, cmd)
            return func
        return None

class MapconfigPlugin(b4.b4_plugin.Plugin):
    # requiresConfigFile = False

    _adminPlugin = None
    powerAdminUrtPlugin = None

    requiresParsers = ['iourt42', 'iourt43']
    # loadAfter is a higher level of requires. Doing both causes a "cyclic dependency" error
    # requiresPlugins = ['admin', 'poweradminurt']
    loadAfterPlugins = ['poweradminurt']

    # NOTE: if you add fields then add them here
    default_capturelimit = 8
    default_g_suddendeath = 0
    default_g_gear = 0
    default_g_gravity = 800
    default_g_friendlyfire = 2
    default_startmessage = ""
    default_timelimit = 20

    mapcycle_fileName = ""
    # last modified timestamp
    mapcycle_timestamp = 0
    # the mapcycle as a string
    mapcycle = ""

    random_nextmap = 0
    hopper_fileName = ""
    mapconfig_enabled = 1

    # variables held to reduce processing overhead
    _up_mapname = ""
    _up_nextmap = ""
    _up_next3 = ""
    _startmessage = ""
    _rnm_history_length = 5
    rnm_history = []

    built_in_maps = []

    ####################################################################################################################
    #                                                                                                                  #
    #    STARTUP                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def onStartup(self):
        """
        startup the plugin
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        self.powerAdminUrtPlugin = self.console.getPlugin('powerAdminUrtPlugin')

        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp

                func = getCmd(self, cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        self.registerEvent('EVT_GAME_ROUND_START', self.onNewMap)
        self.registerEvent('EVT_GAME_EXIT')
        self.registerEvent('EVT_GAME_ROUND_END')

        # # tried to catch the end of the map to announce the next map, but it's not firing.
        # # it might only catch actual match rounds
        # self.registerEvent('EVT_GAME_ROUND_END', self.onMapEnd)

    def onLoadConfig(self):
        """
        load plugin configuration
        """
        # NOTE: if you add fields then add them here
        try:
            self.default_capturelimit = self.config.getint('settings', 'default_capturelimit')
        except (NoOptionError, ValueError):
            self.default_capturelimit = 8

        self.debug('default_capturelimit : %s' % self.default_capturelimit)

        try:
            self.default_g_suddendeath = self.config.getint('settings', 'default_g_suddendeath')
        except (NoOptionError, ValueError):
            self.default_g_suddendeath = 0

        self.debug('default_g_suddendeath : %s' % self.default_g_suddendeath)

        try:
            self.default_g_gear = self.config.getint('settings', 'default_g_gear')
        except (NoOptionError, ValueError):
            self.default_g_gear = "0"

        self.debug('default_g_gear : %s' % self.default_g_gear)

        try:
            self.default_g_gravity = self.config.getint('settings', 'default_g_gravity')
        except (NoOptionError, ValueError):
            self.default_g_gravity = 800

        self.debug('default_g_gravity : %s' % self.default_g_gravity)

        try:
            self.default_g_friendlyfire = self.config.getint('settings', 'default_g_friendlyfire')
        except (NoOptionError, ValueError):
            self.default_g_friendlyfire = 0

        self.debug('default_g_friendlyfire : %s' % self.default_g_friendlyfire)

        try:
            self.default_startmessage = self.config.get('settings', 'default_startmessage')
        except (NoOptionError, ValueError):
            self.default_startmessage = ""

        self.debug('default_startmessage : %s' % self.default_startmessage)

        try:
            self.mapcycle_fileName = self.config.get('settings', 'mapcycle_fileName')
        except (NoOptionError, ValueError):
            self.mapcycle_fileName = ""

        self.debug('mapcycle_fileName : %s' % self.mapcycle_fileName)

        try:
            self.default_timelimit = self.config.getint('settings', 'default_timelimit')
        except (NoOptionError, ValueError):
            self.default_timelimit = 20

        self.debug('default_timelimit : %s' % self.default_timelimit)

        try:
            self.random_nextmap = self.config.getint('settings', 'random_nextmap')
        except (NoOptionError, ValueError):
            self.random_nextmap = 0

        self.debug('random_nextmap : %s' % self.random_nextmap)

        try:
            self.hopper_fileName = self.config.get('settings', 'hopper_fileName')
        except (NoOptionError, ValueError):
            self.hopper_fileName = ""

        self.debug('hopper_fileName : %s' % self.hopper_fileName)

        self.mapcycle = ""

        try:
            self._rnm_history_length = self.config.getint('settings', 'rnm_history_length')
        except (NoOptionError, ValueError):
            self._rnm_history_length = 5

        self.debug('rnm_history_length : %s' % self._rnm_history_length)

        # NOTE: _stop_at does not need self. because it's local and only used once
        try:
            _stop_at = self.config.getint('built_in_maps', 'stop_at')
        except (NoOptionError, ValueError):
            _stop_at = 40

        self.debug('stop_at : %s' % _stop_at)

        # load the built-in maps list
        _bimerr = 0
        for loop in range(_stop_at):
            try:
                _bim = self.config.get('built_in_maps', 'bim' + str(loop))
                self.built_in_maps.append(_bim)
            except (NoOptionError, ValueError):
                _bimerr = _bimerr + 1
        self.debug('built in maps loaded : %s', len(self.built_in_maps))
        self.debug('bim numbers not found : %s', _bimerr)

        if self.random_nextmap == 1:
            # determine the next random map
            self.cmd_randomnextmap()

        try:
            self.mapconfig_enabled = self.config.getint('settings', 'mapconfig_enabled')
        except (NoOptionError, ValueError):
            self.mapconfig_enabled = 0

        self.debug('mapconfig_enabled : %s' % self.mapconfig_enabled)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onNewMap(self, event):
        """
        Handle EVT_GAME_ROUND_START
        """
        # self.debug('onNewMap handle %s:"%s"', event.type, event.data)
        # event.data is a b4_game.Game object
        mapName = event.data._get_mapName()
        if mapName != self._up_mapname:
            self._up_mapname = mapName

            # only set the mapconfig if it's enabled
            if self.mapconfig_enabled == 1:
                self.setMapSettings(mapName)

            if self.random_nextmap == 1:
                # add to history
                self.rnm_history.append(mapName)

                # remove the first item if the list is long
                if len(self.rnm_history) > self._rnm_history_length:
                    self.rnm_history.remove(self.rnm_history[0])

                # determine the next random map
                self.cmd_randomnextmap()

    def onEvent(self, event):
        if (event.type == self.console.getEventID('EVT_GAME_EXIT')) or \
                (event.type == self.console.getEventID('EVT_GAME_ROUND_END')):
            # self.debug('onEvent')
            self.cmd_upcoming(self)
            #if self.mapcycle_fileName:
            #	if self.random_nextmap == 0:
            #		self.cmd_upcoming(self)
            #else:
            nextmap = self.console.getNextMap()
            if nextmap:
                ad = "^2Next map: ^3" + nextmap
                self.console.say(ad)
            # end of the else was here

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def getMapconfig(self, mapconfig):
        """
        Return a mapconfig object fetching data from the storage.
        :param mapconfig: The mapconfig object to fill with fetch data.
        :return: The mapconfig object given in input with all the fields set.
        """
        # self.console.debug('Storage: getMapconfig %s' % mapconfig)
        if hasattr(mapconfig, 'mapname') and mapconfig["mapname"]:
            # query = QueryBuilder(self.db).SelectQuery('*', 'mapconfig', {'mapname': mapconfig.mapname}, None, 1)
            self.debug("has attribute mapname")
            # pass
        # else:
        # 	raise KeyError('no mapname was set %s' % mapconfig)

        # cursor = self.query(query)
        cursor = self.console.storage.query("SELECT * FROM mapconfig WHERE mapname = '%s'" % (mapconfig["mapname"]))
        if cursor.EOF:
            cursor.close()
            self.debug('no mapconfig found matching %s' % (mapconfig["mapname"]))
            mapconfig["id"] = 0
            return mapconfig
            # raise KeyError('no mapconfig found matching %s' % mapconfig.mapname)

        row = cursor.getOneRow()
        mapconfig["id"] = int(row['id'])
        mapconfig["mapname"] = row['mapname']
        # NOTE: if you add fields then add them here
        mapconfig["capturelimit"] = int(row['capturelimit'])
        mapconfig["g_suddendeath"] = int(row['g_suddendeath'])
        mapconfig["g_gear"] = row['g_gear']
        mapconfig["g_gravity"] = int(row['g_gravity'])
        mapconfig["g_friendlyfire"] = int(row['g_friendlyfire'])
        mapconfig["startmessage"] = row['startmessage']
        mapconfig["timelimit"] = row['timelimit']

        return mapconfig

    def setMapSettings(self, mapName):
        """
        Sends the rcon commands to set the settings
        :param mapName: the map name (without extension)
        :return:
        """
        self.debug('onNewMap map %s' % mapName)
        # need to read b3 table to get values

        # NOTE: if you add fields then add them here
        mapconfig = {"id": 0, \
                     "mapname": mapName, \
                     "capturelimit": self.default_capturelimit, \
                     "g_suddendeath": self.default_g_suddendeath, \
                     "g_gear": self.default_g_gear, \
                     "g_gravity": self.default_g_gravity, \
                     "g_friendlyfire": self.default_g_friendlyfire, \
                     "startmessage": self.default_startmessage, \
                     "timelimit": self.default_timelimit }

        mapconfig = self.getMapconfig(mapconfig)
        # if mapconfig["id"] > 0:
        # then rcon to set game values
        # self.debug('setting capturelimit %s, g_gear %s' % (mapconfig["capturelimit"], mapconfig["g_gear"]))

        # NOTE: if you add fields then add them here
        self.console.write('capturelimit %s ' % (mapconfig["capturelimit"]))
        self.console.write('g_suddendeath %s ' % (mapconfig["g_suddendeath"]))
        self.console.write('g_gear "%s" ' % (mapconfig["g_gear"]))
        self.console.write('g_gravity %s ' % (mapconfig["g_gravity"]))
        self.console.write('g_friendlyfire %s ' % (mapconfig["g_friendlyfire"]))

        self.buildstartmessage(mapconfig)

        self.console.say(self._startmessage)
        self.console.write('timelimit %s ' % (mapconfig["timelimit"]))

        # self.debug('onNewMap updated successfully')

        # I want to have it perform an @gear command if gear limits are on
        # if mapconfig["g_gear"] != "0":
        # self.debug("sending gear cmd")
        # these say it but don't "process" it
        # self.console.say("@pagear")
        # self.console.write('@pagear')

        # these don't work
        # self.console.sayLoudOrPM(None, "@pagear")
        # self.console.cmd_pagear(data=None)
            # client2 = Client()
            # client2.id = 1
            # client2 = self.console.storage.getClient(client2)
            # self.powerAdminUrtPlugin.cmd_pagear(data=None, client=client2, cmd="Command<pagear>")

        # command = self._adminPlugin._commands['admins']
        # command.executeLoud(data=None, client=None)
        # command = functions.getCmd(self.powerAdminUrtPlugin, "pagear")
        # command.executeLoud(data=None, client=None)

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_mapconfig(self, data=None, client=None, cmd=None):
        """
        Set the game settings for this map from the mapconfig table.
        """

        cmd.sayLoudOrPM(client, '^7mapconfig_enabled : %s' % self.mapconfig_enabled)
        mapName = self.console.getMap()
        # mapName = b4_game.getMap()
        self.debug("map name is %s" % mapName)
        self.setMapSettings(mapName)

    def cmd_maplist(self, data=None, client=None, cmd=None):
        """
        Get the mapcycle.txt map list.
        """
        self.debug("maplist entered")

        if not self.mapcycle_fileName or self.mapcycle_fileName == "":
            cmd.sayLoudOrPM(client, '^7MapCycle path not set in ini file.')
            return

        # sclient = self._adminPlugin.findClientPrompt(data, client)
        #
        # if not data:
        # 	client.message('^7invalid data, try !help maplist')
        # 	return
        #
        # if not sclient:
        # 	# a player matching the name was not found, a list of closest matches will be displayed
        # 	# we can exit here and the user will retry with a more specific player
        # 	return

        #if platform.system()
        file_timestamp = os.path.getmtime(self.mapcycle_fileName)
        self.debug("maplist: timestamp is %s" % file_timestamp)

        if self.mapcycle_timestamp != file_timestamp:
            # we need to read the file, because we haven't yet or they've changed
            self.debug("maplist: reading mapcycle")
            self.mapcycle = [line.rstrip('\n') for line in open(self.mapcycle_fileName)]
            self.mapcycle_timestamp = file_timestamp

        if self.mapcycle:
            # get the current map and colorize it if it's in the cycle
            mapname = self.console.getMap()
            if mapname in self.mapcycle:
                idx = self.mapcycle.index(mapname)
                self.mapcycle[idx] = "^8" + self.mapcycle[idx] + "^7"
                cmd.sayLoudOrPM(client, '^7MapList: ^2%s' % '^7, ^2'.join(self.mapcycle))
                self.mapcycle[idx] = mapname
            else:
                cmd.sayLoudOrPM(client, '^7MapList: ^2%s' % '^7, ^2'.join(self.mapcycle))
        else:
            cmd.sayLoudOrPM(client, '^7MapList not found')

    def getNextMaps(self, g_nextmap):
        nummaps = len(self.mapcycle)
        try:
            idx = self.mapcycle.index(g_nextmap)
        except ValueError:
            idx = -1
        idx += 2
        self.debug("nextmap: %s; idx: %s; nummaps: %s" % (g_nextmap, idx, nummaps))
        self.debug("cycle is %s" % self.mapcycle)
        if idx <= nummaps:
            g_nextmap2 = self.mapcycle[idx - 1]
        else:
            idx = 1
            g_nextmap2 = self.mapcycle[idx - 1]

        idx += 1
        if idx <= nummaps:
            g_nextmap3 = self.mapcycle[idx - 1]
        else:
            idx = 1
            g_nextmap3 = self.mapcycle[idx - 1]
        return g_nextmap2, g_nextmap3

    def cmd_upcoming(self, data=None, client=None, cmd=None):
        """
        Show the next 3 upcoming maps.
        """
        # self.debug("upcoming entered")

        if not self.mapcycle_fileName or self.mapcycle_fileName == "":
            cmd.sayLoudOrPM(client, '^7MapCycle path not set in ini file.')
            return

        # sclient = self._adminPlugin.findClientPrompt(data, client)
        #
        # if not data:
        # 	client.message('^7invalid data, try !help maplist')
        # 	return
        #
        # if not sclient:
        # 	# a player matching the name was not found, a list of closest matches will be displayed
        # 	# we can exit here and the user will retry with a more specific player
        # 	return

        mapname = self.console.getMap()
        # try to catch when it wants to pop right at the beginning of a map.
        # it would mistakenly list the first 3 in the cycle because it didn't catch the current map correctly
        if not mapname or mapname == "":
            return
        g_nextmap = self.console.getNextMap()

        # if nothing changed, just cough up the last string
        if mapname == self._up_mapname and g_nextmap == self._up_nextmap:
            self.console.say(self._up_next3)
            self.debug("nothing changed")
            return

        if self.random_nextmap == 1:
            self._up_nextmap = g_nextmap
            self._up_next3 = '^7Upcoming: ^2%s^7, ^2**random**' % self._up_nextmap
            self.console.say(self._up_next3)
            return

        file_timestamp = os.path.getmtime(self.mapcycle_fileName)
        self.debug("upcoming: timestamp is %s" % file_timestamp)

        if self.mapcycle_timestamp != file_timestamp:
            # we need to read the file, because we haven't yet or they've changed
            self.debug("upcoming: reading mapcycle")
            self.mapcycle = [line.rstrip('\n').rstrip('\r') for line in open(self.mapcycle_fileName)]
            self.mapcycle_timestamp = file_timestamp

        nummaps = len(self.mapcycle)

        # i believe that g_nextmap will always have a value here because b3 looks at server var g_nextmap and g_nextcyclemap
        if g_nextmap:
            g_nextmap1 = g_nextmap
            self.debug("g_nextmap is set: %s" % g_nextmap)
            pass
        elif mapname in self.mapcycle:
            self.debug("mapname in cycle")
            idx = self.mapcycle.index(mapname)
            idx += 1
            if idx < nummaps:
                g_nextmap1 = self.mapcycle[idx]
            else:
                g_nextmap1 = self.mapcycle[0]
        else:
            self.debug("flowed to else, using start of mapcycle")
            g_nextmap1 = self.mapcycle[0]

        g_nextmap2, g_nextmap3 = self.getNextMaps(g_nextmap1)

        if self.mapcycle:
            # hold the string so we don't need to reprocess unless something changed
            self._up_mapname = mapname
            self._up_nextmap = g_nextmap1
            self._up_next3 = '^7Upcoming: ^2%s^7, ^2%s^7, ^2%s' % (g_nextmap1, g_nextmap2, g_nextmap3)
            self.console.say(self._up_next3)
        else:
            cmd.sayLoudOrPM(client, '^7Upcoming not found')

    def cmd_startmessage(self, data=None, client=None, cmd=None):
        """
        Repeat the start message from the mapconfig table.
        """
        # catch when b3 is reloaded and doesn't know the map.
        if not self._startmessage or self._startmessage == "":
            mapname = self.console.getMap()
            self.setMapSettings(mapname)
        else:
            self.console.say(self._startmessage)

    def buildstartmessage(self, mapconfig):
        """
        Build the start message from the mapconfig table, so we don't need to rebuild it each time it's called.
        """
        startmessage = mapconfig["startmessage"]

        caps = mapconfig["capturelimit"]
        if 1 == mapconfig["g_suddendeath"]:
            overtime = "^1OT"
        else:
            overtime = "^3Ties"
        if mapconfig["g_gravity"] == 800:
            gravity = "^3normal"
        elif mapconfig["g_gravity"] < 800:
            gravity = "^2low"
        else:
            gravity = "^1high"

        if 0 == mapconfig["g_friendlyfire"]:
            ff = "^2No FF"
        else:
            ff = "^1FF"

        self._startmessage = ('Map Start Message: ^8%s^7; ^2%s ^7Caps; ^2%s^7; %s gravity^7; %s' % (
            startmessage, caps, overtime, gravity, ff))

        self.debug("StartMessage set to %s" % self._startmessage)

    def cmd_randomnextmap(self, data=None, client=None, cmd=None):
        """
        Randomize the next map.
        """
        mapName = self.console.getMap()
        self.debug("Current map %s" % mapName)
        if (self.hopper_fileName == ""):
            # get a new random map from the database
            cursor = self.console.storage.query("SELECT * FROM mapconfig WHERE skiprandom <> 1 order by rand() limit 2")
            if cursor.EOF:
                cursor.close()
                self.debug('no mapconfig found for next map selection')
            # raise KeyError('no mapconfig found matching %s' % mapconfig.mapname)

            row = cursor.getOneRow()
            nextMap = row['mapname']

            # if it's the same map then try again
            if nextMap == mapName:
                self.debug("Dupe map %s, trying again" % nextMap)
                row = cursor.moveNext()
                nextMap = row['mapname']
        else:
            # get a new random map from reading hopper.txt
            lines = []
            with open(self.hopper_fileName, 'r') as file:
                lines = file.readlines()
                # remove crlf and whitespace
                lines = [line.rstrip() for line in lines]
                # removes the .pk3 from the end
                lines = [line[:-4] for line in lines]
            self.debug("Number of indexes in map hopper %s" % len(lines))
            self.addBuiltInMaps(lines)
            self.debug("Number of indexes after adding built-ins %s" % len(lines))
            # remove last X maps (from history)
            if len(lines) > len(self.rnm_history) + 1:
                self.debug("Removing recent %s maps" % len(self.rnm_history))
                for loopmap in range(0, len(self.rnm_history)):
                    # make sure the item is there before trying to remove it
                    if self.rnm_history[loopmap] in lines:
                        lines.remove(self.rnm_history[loopmap])
            # pick a random map
            randInt = random.randrange(0, len(lines))
            nextMap = lines[randInt]
            #self.debug("Comparing %s to %s" % (nextMap, mapName))
            # if it's the same map then try again
            if nextMap == mapName:
                self.debug("Dupe map %s, trying again" % nextMap)
                randInt = random.randrange(0, len(lines))
                nextMap = lines[randInt]

        self.debug("Setting random next map %s" % nextMap)
        self.console.write("g_nextmap %s" % nextMap)
        self.console.say("Next Map: %s" % nextMap)

    def cmd_setrandomnextmap(self, data=None, client=None, cmd=None):
        """
        <on|off or 1|0> Set the random_nextmap config option.
        """
        # self.debug("setrandomnextmap entered")

        # if nothing was entered write the param info
        if not data:
            client.message('^7Current SetRandomNextMap %s, try !help setrandomnextmap for more' % self.random_nextmap)
            return

        # read the data
        if not data or data not in ('on', 'off', '1', '0'):
            client.message('^7Invalid or missing data, try !help setrandomnextmap')
            return

        if data == 'on' or data == '1':
            self.random_nextmap = 1
            cmd.sayLoudOrPM(client, "random_nextmap turned ON")
        else:
            self.random_nextmap = 0
            cmd.sayLoudOrPM(client, "random_nextmap turned OFF")

    def addBuiltInMaps(self, lines):
        """
        Add Built-in maps so the random selection will include them.
        Feel free to comment any maps you don't want chosen
        """
        # add default built-in maps
        lines.extend(self.built_in_maps)

    def cmd_setmapconfig(self, data=None, client=None, cmd=None):
        """
        <on|off or 1|0> Set the map config option to enabled/disabled.
        """
        # self.debug("setmapconfig entered")

        # if nothing was entered write the param info
        if not data:
            client.message('^7setmapconfig is %s, try !help setmapconfig' % self.mapconfig_enabled)
            return

        # read the data
        if not data or data not in ('on', 'off', '1', '0'):
            client.message('^7Invalid or missing data, try !help setmapconfig')
            return

        if data == 'on' or data == '1':
            self.mapconfig_enabled = 1
            cmd.sayLoudOrPM(client, "mapconfig_enabled turned ON")
        else:
            self.mapconfig_enabled = 0
            cmd.sayLoudOrPM(client, "mapconfig_enabled turned OFF")
