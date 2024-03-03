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

import b4
#import b4.b4_events
import b4.b4_plugin
import datetime
import random
import threading
import time

from b4.b4_functions import getCmd
from b4.storage.b4_common import mapresult
from configparser import NoOptionError

__version__ = '0.2'
__author__  = 'isopropanol'


def skuffle_thread(self):
    self.debug("Thread skuffle_thread: starting; thread %r" % threading.current_thread().ident)
    self.console.say("Shuffle in %s seconds" % self._shuffle_delay)
    time.sleep(self._shuffle_delay)
    # self.console.say("Score Auto Shuffle")
    self._poweradminPlugin.cmd_paskuffle()
    self.debug("Thread skuffle_thread: finishing")

def randomshuffle_thread(self):
    self.debug("Thread randomshuffle_thread: starting; thread %r" % threading.current_thread().ident)
    self.console.say("Shuffle in %s seconds" % self._shuffle_delay)
    time.sleep(self._shuffle_delay)
    # self.console.say("Score Auto Shuffle")
    self.cmd_randomshuffle()
    self.debug("Thread randomshuffle_thread: finishing")


class FlagannouncePlugin(b4.b4_plugin.Plugin):
    # requiresConfigFile = True
    # requiresPlugins = ['admin']
    _adminPlugin = None
    _poweradminPlugin = None
    _immunity_level = None
    _red_score = 0
    _blue_score = 0
    _has_red = -1
    _has_blue = -1
    _shuffle_score_diff = 0
    _shuffle_delay = 20
    _shuffle_now_diff = 0
    _shuffle_now_map = ""
    _balance_now_diff = 0
    _balance_now_map = ""
    _warmup = False
    _capture_map_results = False
    # variables for mapresults
    _mapname = ""
    _start_time = None
    _low_player = 99
    _high_player = 0
    _flag_smite = False
    _flag_smite_taunt = False
    _flag_smite_quote = ["A flag has been captured", "Hulk smash", "Thou hast offended me", "Red is going to win", "Blue is going to win"]

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
        self._poweradminPlugin = self.console.getPlugin('poweradminurt')

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

        self.registerEvent('EVT_CLIENT_ACTION', self.onAction)
        self.registerEvent('EVT_GAME_ROUND_START', self.onNewMap)
        self.registerEvent('EVT_GAME_ROUND_END')
        self.registerEvent('EVT_GAME_EXIT')

    def onLoadConfig(self):
        """
        load plugin configuration
        """
        try:
            self._shuffle_score_diff = self.config.getint('settings', 'shuffle_score_diff')
            self.debug('loaded settings/shuffle_score_diff: %s' % self._shuffle_score_diff)
        except NoOptionError:
            self.warning('could not find settings/shuffle_score_diff in config file, '
                         'using default: %s' % self._shuffle_score_diff)
        except KeyError as e:
            self.error('could not load settings/shuffle_score_diff config value: %s' % e)
            self.debug('using default value (%s) for settings/shuffle_score_diff' % self._shuffle_score_diff)

        try:
            self._shuffle_delay = self.config.getint('settings', 'shuffle_delay')
            self.debug('loaded settings/shuffle_delay: %s' % self._shuffle_delay)
        except NoOptionError:
            self.warning('could not find settings/shuffle_delay in config file, '
                         'using default: %s' % self._shuffle_delay)
        except KeyError as e:
            self.error('could not load settings/shuffle_delay config value: %s' % e)
            self.debug('using default value (%s) for settings/shuffle_delay' % self._shuffle_delay)

        try:
            self._shuffle_now_diff = self.config.getint('settings', 'shuffle_now_diff')
            self.debug('loaded settings/shuffle_now_diff: %s' % self._shuffle_now_diff)
        except NoOptionError:
            self.warning('could not find settings/shuffle_now_diff in config file, '
                         'using default: %s' % self._shuffle_now_diff)
        except KeyError as e:
            self.error('could not load settings/shuffle_now_diff config value: %s' % e)
            self.debug('using default value (%s) for settings/shuffle_now_diff' % self._shuffle_now_diff)

        try:
            self._balance_now_diff = self.config.getint('settings', 'balance_now_diff')
            self.debug('loaded settings/balance_now_diff: %s' % self._balance_now_diff)
        except NoOptionError:
            self.warning('could not find settings/balance_now_diff in config file, '
                         'using default: %s' % self._balance_now_diff)
        except KeyError as e:
            self.error('could not load settings/balance_now_diff config value: %s' % e)
            self.debug('using default value (%s) for settings/balance_now_diff' % self._balance_now_diff)

        try:
            self._capture_map_results = self.getSetting('settings', 'capture_map_results', b4.BOOL, self._capture_map_results)
            self.debug('loaded settings/capture_map_results: %s' % self._capture_map_results)
        except NoOptionError:
            self.warning('could not find settings/capture_map_results in config file, '
                         'using default: %s' % self._capture_map_results)
        except KeyError as e:
            self.error('could not load settings/capture_map_results config value: %s' % e)
            self.debug('using default value (%s) for settings/capture_map_results' % self._capture_map_results)

        try:
            self._flag_smite = self.getSetting('settings', 'flag_smite', b4.BOOL, self._flag_smite)
        except (NoOptionError, ValueError):
            self._flag_smite = False

        try:
            self._flag_smite_taunt = self.getSetting('settings', 'flag_smite_taunt', b4.BOOL, self._flag_smite_taunt)
        except (NoOptionError, ValueError):
            self._flag_smite_taunt = False

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def onAction(self, event):
        """
        Handle EVT_CLIENT_ACTION.
        """
        # edata = event.data
        # cname = event.client.name
        # if not cname:
        #     cname = "none?"
        # self.debug("FlagAnnounce: %s by %s" % (edata, cname))

        # think of it as "flag captured at COLOR:
        if event.data == 'flag_dropped':
            if self._has_red == event.client.cid:
                self._has_red = -1
            elif self._has_blue == event.client.cid:
                self._has_blue = -1
        if event.data == 'team_CTF_redflag':
            # flag grabbed
            self._has_red = event.client.cid
            # self.debug("DK: _has_red %s" % self._has_red)
        elif event.data == 'team_CTF_blueflag':
            # flag grabbed
            self._has_blue = event.client.cid
            # self.debug("DK: _has_blue %s" % self._has_blue)
        if event.data in 'flag_captured':
            self._warmup = True
            # self.debug("DK: slot id: %s; has_blue %s; has_red %s" % (event.client.cid, self._has_blue, self._has_red))
            caplimit = self.console.getCvar('capturelimit').getInt()
            if event.client.cid == self._has_blue:
                self._red_score += 1
                self._has_blue = -1

                self.debug("DK: red scored %s" % self._has_blue)

                if caplimit - self._red_score > 0:
                    self.console.say(self.getMessage('red_flags_to_limit', (caplimit - self._red_score)))
            elif event.client.cid == self._has_red:
                self._blue_score += 1
                self._has_red = -1

                self.debug("DK: blue scored %s" % self._has_red)

                if caplimit - self._blue_score > 0:
                    self.console.say(self.getMessage('blue_flags_to_limit', (caplimit - self._blue_score)))

            self.debug("FlagAnnounce Red: %s; Blue: %s" % (self._red_score, self._blue_score))

            self.checkPlayerCount()

            # self.debug("FlagAnnounce %s Red: %s by has_blue %s; Blue: %s by has_red %s"
            #            % (event.data, self._red_score, self._has_blue, self._blue_score, self._has_red))
            if (self._shuffle_now_diff > 0
                    and self._shuffle_now_diff == abs(self._red_score - self._blue_score)):
                mapName = self.console.getMap()
                if (mapName != self._shuffle_now_map):
                    self.debug("Running shuffle now")
                    self._shuffle_now_map = mapName
                    self._poweradminPlugin.cmd_paskuffle()

            if (self._balance_now_diff > 0
                    and self._balance_now_diff == abs(self._red_score - self._blue_score)):
                mapName = self.console.getMap()
                if (mapName != self._balance_now_map):
                    self.debug("Running balance now")
                    self._balance_now_map = mapName
                    self._poweradminPlugin.cmd_pabalance()

            if self._flag_smite:
                # kill players after a cap
                clients = self.console.clients.getList()
                pos = 0
                while pos < len(clients):
                    self.console.write("smite %s" % clients[pos].cid)
                    pos = pos + 1
                if self._flag_smite_taunt:
                    # say a random taunt
                    pos = random.randint(0, len(self._flag_smite_quote) - 1)
                    # self.debug("FlagAnnounce chose quote [%s] %s" % (pos, self._flag_smite_quote[pos]))
                    self.console.write('bigtext "%s"' % self._flag_smite_quote[pos])
                    # self.console.say("%s" % self._flag_smite_quote[pos])

            # randomorder doesn't seem to do anything
            # if (self._red_score == caplimit or self._blue_score == caplimit):
            #     if self._shuffle_score_diff > 0 and abs(self._red_score - self._blue_score) >= self._shuffle_score_diff:
            #         self.debug("FlagAnnounce: setting shuffle due to last map cap difference %s >= %s"
            #                    % (abs(self._red_score - self._blue_score), self._shuffle_score_diff))
            #         self.console.setCvar('g_randomorder', 1)

    def onNewMap(self, event):
        """
        Handle EVT_GAME_ROUND_START
        """
        # self.debug("DK: shuffle diff %s; actual diff %s; (red %s; blue %s)" % (self._shuffle_score_diff, abs(self._red_score - self._blue_score), self._red_score, self._blue_score))

        if self._warmup:
            # this catches the original map load
            self._warmup = False

            # to shuffle during warm up
            # shuffle if the score difference is set and the difference is at least that value
            if self._shuffle_score_diff > 0 and abs(self._red_score - self._blue_score) >= self._shuffle_score_diff:
                self.debug("FlagAnnounce: turning random order off")
                # random order doesn't seem to do anything
                #    self.console.setCvar('g_randomorder', 0)
                # skill shuffle at the very beginning of a map doesn't do anything
                #     self.debug("FlagAnnounce: shuffling due to last map cap difference %s >= %s"
                #                % (abs(self._red_score - self._blue_score), self._shuffle_score_diff))
                #     # start a thread to wait and run skuffle after the delay
                #     bt = threading.Thread(target=skuffle_thread, args=(self,))
                #     bt.start()
                # do a true random shuffle
                self.debug("FlagAnnounce: shuffling due to last map cap difference %s >= %s"
                           % (abs(self._red_score - self._blue_score), self._shuffle_score_diff))
                # start a thread to wait and run skuffle after the delay
                bt = threading.Thread(target=randomshuffle_thread, args=(self,))
                bt.start()

        else:
            # this runs after warmup ends
            self._mapname = self.console.getMap()

            # # to shuffle after warm up
            # # shuffle if the score difference is set and the difference is at least that value
            # if self._shuffle_score_diff > 0 and abs(self._red_score - self._blue_score) >= self._shuffle_score_diff:
            #     self.debug("FlagAnnounce: turning random order off")
            #     # random order doesn't seem to do anything
            #     #    self.console.setCvar('g_randomorder', 0)
            #     # skill shuffle at the very beginning of a map doesn't do anything
            #     #     self.debug("FlagAnnounce: shuffling due to last map cap difference %s >= %s"
            #     #                % (abs(self._red_score - self._blue_score), self._shuffle_score_diff))
            #     #     # start a thread to wait and run skuffle after the delay
            #     #     bt = threading.Thread(target=skuffle_thread, args=(self,))
            #     #     bt.start()
            #     # do a true random shuffle
            #     self.debug("FlagAnnounce: shuffling due to last map cap difference %s >= %s"
            #                % (abs(self._red_score - self._blue_score), self._shuffle_score_diff))
            #     # start a thread to wait and run skuffle after the delay
            #     bt = threading.Thread(target=randomshuffle_thread, args=(self,))
            #     bt.start()

            self._red_score = 0
            self._blue_score = 0
            self._has_red = -1
            self._has_blue = -1
            self._start_time = datetime.datetime.now()
            self._low_player = 99
            self._high_player = 0
            self.checkPlayerCount()

    def onEvent(self, event):
        if (event.type == self.console.getEventID('EVT_GAME_EXIT')) or \
                (event.type == self.console.getEventID('EVT_GAME_ROUND_END')):

            # if (event.type == self.console.getEventID('EVT_GAME_EXIT')):
            #     self.debug("EVT_GAME_EXIT")
            # if (event.type == self.console.getEventID('EVT_GAME_ROUND_END')):
            #     self.debug("EVT_GAME_ROUND_END")

            # getmap doesn't work after mapexit, it returns "None"
            # but this event is firing twice as mapexit, so use the second one to actually write
            localmapname = self.console.getMap()

            if not localmapname:
                maptime = "00:00"
                if self._start_time:
                    timediff = datetime.datetime.now() - self._start_time
                    diffminutes, diffseconds = divmod(timediff.seconds, 60)
                    maptime = "%02i:%02i" % (diffminutes, diffseconds)
                self.debug("onEvent %s. Red %s, Blue %s; map time %s; low-high %s-%s; localmapname: %s"
                           % (self._mapname, self._red_score, self._blue_score, maptime, self._low_player, self._high_player, localmapname))

                # NOTE: for some reason this fires before the final cap is counted, so update from poweradmin (doesn't work)
                # self._red_score, self._blue_score = self._poweradminPlugin.getTeamScores()

                mapresult1 = mapresult(self._mapname, self._red_score, self._blue_score, maptime,
                                       self._low_player, self._high_player, None, None)
                # self.debug("DK: made it past")
                self.console.storage.setMapResult(mapresult1)
                # return 0

    ####################################################################################################################
    #                                                                                                                  #
    #    OTHER METHODS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def checkPlayerCount(self):
        if self._capture_map_results is True:
            clients = self.console.clients.getList()
            players = len(clients)
            # for rec in clients:
            #     self.debug(rec.name)
            self.debug("player count: %s" % players)
            if self._low_player > players:
                self._low_player = players
            if self._high_player < players:
                self._high_player = players

    ####################################################################################################################
    #                                                                                                                  #
    #    COMMANDS                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cmd_faset(self, data=None, client=None, cmd=None):
        """
        <red_score> <blue_score> - Set the scores.  Only needed if B3 was restarted during a map.
        """
        # self.debug("faset entered")

        # auto pull the map name
        self._mapname = self.console.getMap()

        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Missing data, try !help faset')
            return False

        self.debug("FASet: %s red %s blue %s" % (self._mapname, m[0], m[1]))
        self._red_score = m[0]
        self._blue_score = m[1]
        # NOTE: for some reason this fires before the final cap is counted, so update from poweradmin (doesn't work)
        # self._red_score, self._blue_score = self._poweradminPlugin.getTeamScores()

        if not self._start_time:
            self._start_time = datetime.datetime.now()

        self.checkPlayerCount()

        cmd.sayLoudOrPM(client, '^7FlagAnnounce set %s ^1Red %s^7, ^4Blue %s^7. Low-High %s-%s'
                        % (self._mapname, self._red_score, self._blue_score, self._low_player, self._high_player))

    def cmd_fashow(self, data=None, client=None, cmd=None):
        """
        Show the scores, low-high player count, and map start time (using server time).
        """
        # self.debug("fashow entered")

        if not self._start_time:
            self._start_time = datetime.datetime.now()

        cmd.sayLoudOrPM(client, '^7FlagAnnounce %s ^1Red %s^7, ^4Blue %s^7. Low-High %s-%s. start time %s'
                        % (self._mapname, self._red_score, self._blue_score, self._low_player, self._high_player
                           , self._start_time.strftime("%H:%M")))

    def cmd_randomshuffle(self, data=None, client=None, cmd=None):
        """
        Straight random shuffle
        """
        self.debug("RandomShuffle entered")

        # slotstoletters = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J', 10: 'K',
        #                   11: 'L', 12: 'M', 13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U',
        #                   21: 'V', 22: 'W', 23: 'X', 24: 'Y', 25: 'Z', 26: '[', 27: '\\', 28: ']', 29: '^', 30: '_',
        #                   31: '`'}

        letterstoslots = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9, 'K': 10,
                          'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19, 'U': 20,
                          'V': 21, 'W': 22, 'X': 23, 'Y': 24, 'Z': 25, '[': 26, '\\': 27, ']': 28, '^': 29, '_': 30,
                          '`':  31}

        teamred = self.console.getCvar('g_redteamlist').getString()
        teamblue = self.console.getCvar('g_blueteamlist').getString()

        self.debug("RandomShuffle red: %s" % teamred)
        self.debug("RandomShuffle blue: %s" % teamblue)

        # if client:
        #     client.message("randomshuffle red: %s" % teamred)
        #     client.message("randomshuffle blue: %s" % teamblue)
        reds = list(teamred)
        blues = list(teamblue)

        # self.debug("RandomShuffle reds: %s" % reds)
        # self.debug("RandomShuffle blues: %s" % blues)

        # get the count of the smaller team
        teamsize = len(reds)
        if len(blues) < teamsize:
            teamsize = len(blues)
        # get half that number, rounded down
        shufflecount = teamsize / 2
        if shufflecount < 1:
            self.console.say("Not enough players to shuffle. Red %s; Blue %s" % (len(reds), len(blues)))
            return

        # determine method
        # methodlist = {1: 'even', 2: 'odd', 3: 'low', 4: 'high'}
        pos = 0
        step = 1
        method = random.randint(1, 4)
        if method == 1:
            # even
            self.console.say("RandomShuffle: Even")
            self.debug("RandomShuffle Even")
            #pos = 0
            step = 2
        elif method == 2:
            # odd
            self.console.say("RandomShuffle: Odd")
            self.debug("RandomShuffle Odd")
            pos = 1
            step = 2
        elif method == 3:
            # low
            self.console.say("RandomShuffle: Low")
            self.debug("RandomShuffle Low")
            #pos = 0
            #step = 1
            # to trick it into only doing half the team
            teamsize = shufflecount
        elif method == 4:
            # high
            self.console.say("RandomShuffle: High")
            self.debug("RandomShuffle High")
            pos = shufflecount
            #step = 1

        # /rcon swap <clientA> <clientB>
        # if we run across a flag carrier hold the other character.  if we have 2 at the end swap them
        hold_red = -1
        hold_blue = -1
        self.debug("RandomShuffle Has Red %s; Has Blue %s" % (self._has_red, self._has_blue))
        # python did not want to do a number to number comparison, so we need to force the issue
        hasblue = int(self._has_blue)
        hasred = int(self._has_red)

        while pos < teamsize:
            redplayer = int(letterstoslots[reds[pos]])
            blueplayer = int(letterstoslots[blues[pos]])
            self.debug("RandomShuffle looking at %s %s" % (redplayer, blueplayer))
            holding = False
            # don't swap the flag carrier
            if redplayer == hasblue:
                hold_blue = blueplayer
                self.debug("RandomShuffle Red slot %s has blue flag. Holding blue slot %s" % (self._has_blue, hold_blue))
                holding = True
            if blueplayer == hasred:
                hold_red = redplayer
                self.debug("RandomShuffle Blue slot %s has red flag. Holding red slot %s" % (self._has_red, hold_red))
                holding = True
            if not holding:
                self.debug("RandomShuffle swapping %s %s" % (redplayer, blueplayer))
                self.console.write('swap %s %s' % (redplayer, blueplayer))
            pos += step
        if hold_red != -1 and hold_blue != -1:
            self.debug("RandomShuffle swapping %s %s" % (hold_red, hold_blue))
            self.console.write('swap %s %s' % (hold_red, hold_blue))

    def cmd_teamswap(self, data=None, client=None, cmd=None):
        """
        Swap full teams.  Red to Blue and Blue to Red
        """
        self.debug("TeamSwap entered")

        # slotstoletters = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J', 10: 'K',
        #                   11: 'L', 12: 'M', 13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U',
        #                   21: 'V', 22: 'W', 23: 'X', 24: 'Y', 25: 'Z', 26: '[', 27: '\\', 28: ']', 29: '^', 30: '_',
        #                   31: '`'}

        letterstoslots = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9, 'K': 10,
                          'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19, 'U': 20,
                          'V': 21, 'W': 22, 'X': 23, 'Y': 24, 'Z': 25, '[': 26, '\\': 27, ']': 28, '^': 29, '_': 30,
                          '`':  31}

        teamred = self.console.getCvar('g_redteamlist').getString()
        teamblue = self.console.getCvar('g_blueteamlist').getString()

        self.debug("TeamSwap red: %s" % teamred)
        self.debug("TeamSwap blue: %s" % teamblue)

        # if client:
        #     client.message("TeamSwap red: %s" % teamred)
        #     client.message("TeamSwap blue: %s" % teamblue)
        reds = list(teamred)
        blues = list(teamblue)

        # self.debug("TeamSwap reds: %s" % reds)
        # self.debug("TeamSwap blues: %s" % blues)

        # get the count of the smaller team
        teamsize = len(reds)
        if len(blues) < teamsize:
            teamsize = len(blues)
        if teamsize < 1:
            self.console.say("Not enough players to shuffle. Red %s; Blue %s" % (len(reds), len(blues)))
            return

        pos = 0
        step = 1

        # /rcon swap <clientA> <clientB>

        while pos < teamsize:
            redplayer = letterstoslots[reds[pos]]
            blueplayer = letterstoslots[blues[pos]]
            self.debug("TeamSwap swapping %s %s" % (redplayer, blueplayer))
            self.console.write('swap %s %s' % (redplayer, blueplayer))
            pos += step

    def cmd_flagsmite(self, data=None, client=None, cmd=None):
        """
        Turn Flag Smite on (1) or off (0) You can also use on/off.
        """
        # self.debug("flagsmite entered")

        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Missing data, try !help flagsmite')
            return False

        opt = m[0].lower()
        self.debug("flagsmite: setting to %s" % (opt))
        if opt == "1" or opt == "on" or opt == "true":
            self._flag_smite = True
            self.console.say('Flag Smite is %s ' % "on")
        else:
            self._flag_smite = False
            self.console.say('Flag Smite is %s ' % "off")
