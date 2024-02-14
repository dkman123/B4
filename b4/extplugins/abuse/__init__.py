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

#import b4
#import b4.b4_events
import b4.b4_plugin
#import datetime
#import threading
#import time

from b4.b4_functions import getCmd
from configparser import NoOptionError
# from b4_storage import abuseresult

__version__ = '0.2'
__author__  = 'isopropanol'


class AbusePlugin(b4.b4_plugin.Plugin):
    # requiresConfigFile = True
    # requiresPlugins = ['admin']
    _adminPlugin = None
    # _poweradminPlugin = None
    _immunity_level = None
    # isoTest
    _permmutelist = []
    _autokilllist = []

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
        # self._poweradminPlugin = self.console.getPlugin('poweradminurt')

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

        # self.registerEvent('EVT_GAME_ROUND_START', self.onNewMap)
        self.registerEvent('EVT_CLIENT_KILL_TEAM')
        self.registerEvent('EVT_CLIENT_KILL')
        self.registerEvent('EVT_CLIENT_AUTH')
        # self.registerEvent('EVT_CLIENT_CONNECT')

    def onLoadConfig(self):
        """
        load plugin configuration
        """
        try:
            self._immunity_level = self.config.getint('settings', 'immunity_level')
            self.debug('loaded settings/immunity_level: %s' % self._immunity_level)
        except NoOptionError:
            self.warning('could not find settings/immunity_level in config file, '
                         'using default: %s' % self._immunity_level)
        except KeyError as e:
            self.error('could not load settings/immunity_level config value: %s' % e)
            self.debug('using default value (%s) for settings/immunity_level' % self._immunity_level)

        # try:
        #     self._capture_map_results = self.getSetting('settings', 'capture_map_results', b4_BOOL, self._capture_map_results)
        #     self.debug('loaded settings/capture_map_results: %s' % self._capture_map_results)
        # except NoOptionError:
        #     self.warning('could not find settings/capture_map_results in config file, '
        #                  'using default: %s' % self._capture_map_results)
        # except KeyError as e:
        #     self.error('could not load settings/capture_map_results config value: %s' % e)
        #     self.debug('using default value (%s) for settings/capture_map_results' % self._capture_map_results)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    # def onNewMap(self, event):
    #     """
    #     Handle EVT_GAME_ROUND_START
    #     """
    #     self.debug("onNewMap entered")
    #
    #     # loop through clients and mute if found
    #     clients = self.console.clients.getClientLikeName("")
    #     # if there are no clients, then there's nothing to do
    #     if len(clients) < 1:
    #         return
    #
    #     for c in clients:
    #         if c in self._permmutelist:
    #             # find the slot id
    #             # matches = self.console.clients.getByMagic("%s" % c.id)
    #             # if matches:
    #             #    self.console.write("mute %s" % (matches[0]).cid)
    #             self.debug("onNewMap muting %s" % c.name)
    #             self.console.write("mute %s" % c.cid)

    def onEvent(self, event):
        # if self.console.game.gameType in self._ffa:
        #     # game type is deathmatch, ignore
        #     return
        if (event.type == self.console.getEventID('EVT_CLIENT_KILL_TEAM')) or \
                (event.type == self.console.getEventID('EVT_CLIENT_KILL')):
            # self.debug("onEvent: in Kill/Team Kill")

            # if they are not in the list, then move on
            if event.client.id not in self._autokilllist:
                # self.debug("onEvent: client not in auto-kill list")
                return

            # find the slot id
            # matches = self.console.clients.getByMagic("%s" % event.client.id)
            # if matches:
            #     self.console.write('smite %s' % (matches[0]).cid)
            # self.debug("onEvent smiting %s %s" % (event.client.cid, event.client.name))
            self.console.write("smite %s" % event.client.cid)

        if (event.type == self.console.getEventID('EVT_CLIENT_CONNECT')) or \
                (event.type == self.console.getEventID('EVT_CLIENT_AUTH')):
            # self.debug("onEvent: in Connect/Auth; id %s; cid %s" % (event.client.id, event.client.cid))

            if event.client.maxLevel >= self._immunity_level:
                return

            #self.warning("Abuse: checking permmute")
            if hasattr(event.client, 'permmute'):
                #self.warning("Abuse: user has permmute field %s of %s" % (event.client.name, event.client.permmute))
                if event.client.permmute == 1:
                    #self.warning("Abuse: user has permmute ON %s, sending mute (slot cid %s)" % (event.client.name, event.client.cid))
                    self.console.write("mute %s %s" % (event.client.cid, 60 * 60))

            if event.client.id not in self._permmutelist:
                # self.debug("onEvent: client not in perm-mute list")
                return

            # find the slot id
            # matches = self.console.clients.getByMagic("%s" % event.client.id)
            # if matches:
            #     self.console.write("mute %s" % (matches[0]).cid)
            # self.debug("onEvent muting %s %s" % (event.client.cid, event.client.name))
            # 60 seconds * 60 minutes = 1 hour
            self.console.write("mute %s %s" % (event.client.cid, 60 * 60))

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_abm(self, data=None, client=None, cmd=None):
        """
        <player> - Perm-mute a player
        """
        # self.debug("apm entered")

        if not data:
            client.message('^7invalid data, try !help abm')
            return

        # self.debug(data)
        sclient = self._adminPlugin.findClientPrompt(data, client)
        if not sclient:
            # a player matchin the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        if sclient.maxLevel >= self._immunity_level:
            client.message('^7invalid target, they\'re immune')
            return

        if sclient.id not in self._permmutelist:
            self.debug("abm perm-muting %s %s @%s" % (sclient.cid, sclient.name, sclient.id))
            cmd.sayLoudOrPM(client, "abm perm-muting %s @%s" % (sclient.name, sclient.id))
            self._permmutelist.append(sclient.id)
            # 60 seconds * 60 minutes = 1 hour
            self.console.write("mute %s %s" % (sclient.cid, 60 * 60))
        else:
            cmd.sayLoudOrPM(client, "abm %s @%s is already perm-muted" % (sclient.name, sclient.id))

    def cmd_abum(self, data=None, client=None, cmd=None):
        """
        <player> - un-perm-mute a player
        """
        # self.debug("abum entered")

        if not data:
            client.message('^7invalid data, try !help abum')
            return

        # self.debug(data)
        sclient = self._adminPlugin.findClientPrompt(data, client)
        if not sclient:
            # a player matchin the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        if sclient.id in self._permmutelist:
            self.debug("abum un-perm-muting %s %s @%s" % (sclient.cid, sclient.name, sclient.id))
            cmd.sayLoudOrPM(client, "abum un-perm-muting %s @%s" % (sclient.name, sclient.id))
            self._permmutelist.remove(sclient.id)
            self.console.write("mute %s %s" % (sclient.cid, 0))
        else:
            cmd.sayLoudOrPM(client, "abum %s @%s is not perm-muted" % (sclient.name, sclient.id))

    def cmd_abak(self, data=None, client=None, cmd=None):
        """
        <player> - Auto auto-kill whenever they kill a player
        """
        # self.debug("abak entered")

        if not data:
            client.message('^7invalid data, try !help abak')
            return

        # self.debug(data)
        sclient = self._adminPlugin.findClientPrompt(data, client)
        if not sclient:
            # a player matchin the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        if sclient.maxLevel >= self._immunity_level:
            client.message('^7invalid target, they\'re immune')
            return

        if sclient.id not in self._autokilllist:
            self.debug("abak auto-kill %s %s @%s" % (sclient.cid, sclient.name, sclient.id))
            cmd.sayLoudOrPM(client, "abak auto-kill %s @%s" % (sclient.name, sclient.id))
            self._autokilllist.append(sclient.id)
            # self.console.write("smite %s %s" % (sclient.cid, 0))
        else:
            cmd.sayLoudOrPM(client, "abak adding auto-kill %s @%s" % (sclient.name, sclient.id))

    def cmd_abuak(self, data=None, client=None, cmd=None):
        """
        <player> - Remove a player from auto-kill
        """
        # self.debug("abuak entered")

        if not data:
            client.message('^7invalid data, try !help cmd_abuak')
            return

        # self.debug(data)
        sclient = self._adminPlugin.findClientPrompt(data, client)
        if not sclient:
            # a player matchin the name was not found, a list of closest matches will be displayed
            # we can exit here and the user will retry with a more specific player
            return

        if sclient.id in self._autokilllist:
            self.debug("abuak removing auto-kill for %s %s @%s" % (sclient.cid, sclient.name, sclient.id))
            cmd.sayLoudOrPM(client, "abuak removing auto-kill for %s @%s" % (sclient.name, sclient.id))
            self._autokilllist.remove(sclient.id)
        else:
            cmd.sayLoudOrPM(client, "abuak %s @%s is not in auto-kill" % (sclient.name, sclient.id))

    # NOTE: setting the name on the b3 client does NOT work
    # def cmd_rename(self, data=None, client=None, cmd=None):
    #     """
    #     <player> <newname> - Rename a player
    #     """
    #     # self.debug("rename entered")
    #
    #     if not data:
    #         client.message('^7invalid data, try !help cmd_rename')
    #         return
    #
    #     args = self._adminPlugin.parseUserCmd(data)
    #     if not args:
    #         cmd.sayLoudOrPM(client, "No new name given")
    #         return
    #
    #     # self.debug(data)
    #     # args[0] is player
    #     # args[1] is new name
    #     sclient = self._adminPlugin.findClientPrompt(args[0], client)
    #     if not sclient:
    #         # a player matchin the name was not found, a list of closest matches will be displayed
    #         # we can exit here and the user will retry with a more specific player
    #         return
    #
    #     if sclient.maxLevel >= self._immunity_level:
    #         client.message('^7invalid target, they\'re immune')
    #         return
    #
    #     self.debug("Renaming %s @%s to %s" % (sclient.name, sclient.id, args[1]))
    #     cmd.sayLoudOrPM(client, "Renaming %s @%s to %s" % (sclient.name, sclient.id, args[1]))
    #     sclient.name = args[