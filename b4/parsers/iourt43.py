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
import re
import time

import b4.b4_clients
import b4.b4_events
import b4.b4_functions
from b4.parsers.iourt41 import Iourt41Parser
from b4.plugins.spamcontrol import SpamcontrolPlugin
from types import MethodType as instancemethod


__author__ = 'Courgette, Fenix, ptitbigorneau'
__version__ = '0.2'

    
class Iourt43Client(b4.b4_clients.Client):

    def auth_by_guid(self):
        """
        Authorize this client using his GUID.
        """
        self.console.debug("b4.parsers.Iourt43Client.auth_by_guid")
        self.console.debug("Auth by guid: %r", self.guid)
        try:
            return self.console.storage.getClient(self)
        except KeyError as msg:
            self.console.debug('User not found %s: %s', self.guid, msg)
            return False

    def auth_by_pbid(self):
        """
        Authorize this client using his PBID.
        """
        self.console.debug("b4.parsers.Iourt43Client.auth_by_pbid")
        self.console.debug("Auth by FSA: %r", self.pbid)
        clients_matching_pbid = self.console.storage.getClientsMatching(dict(pbid=self.pbid))
        if len(clients_matching_pbid) > 1:
            self.console.warning("Found %s client having FSA '%s'", len(clients_matching_pbid), self.pbid)
            return self.auth_by_pbid_and_guid()
        elif len(clients_matching_pbid) == 1:
            self.id = clients_matching_pbid[0].id
            # we may have a second client entry in database with current guid.
            # we want to update our current client guid only if it is not the case.
            try:
                client_by_guid = self.console.storage.getClient(Iourt43Client(guid=self.guid))
            except KeyError:
                pass
            else:
                if client_by_guid.id != self.id:
                    # so storage.getClient is able to overwrite the value which will make
                    # it remain unchanged in database when .save() will be called later on
                    self._guid = None
            return self.console.storage.getClient(self)
        else:
            self.console.debug('Frozen Sand account [%s] unknown in database', self.pbid)
            return False

    def auth_by_pbid_and_guid(self):
        """
        Authorize this client using both his PBID and GUID.
        """
        self.console.debug("b4.parsers.Iourt43Client.auth_by_pbid_and_guid")
        self.console.debug("Auth by both guid and FSA: %r, %r", self.guid, self.pbid)
        clients_matching_pbid = self.console.storage.getClientsMatching({'pbid': self.pbid, 'guid': self.guid})
        if len(clients_matching_pbid):
            self.id = clients_matching_pbid[0].id
            return self.console.storage.getClient(self)
        else:
            self.console.debug("Frozen Sand account [%s] with guid '%s' unknown in database", self.pbid, self.guid)
            return False

    def auth(self):
        """
        The b4_clients.Client.auth method needs to be changed to fit the UrT4.2 authentication scheme.
        In UrT4.2 :
           * all connected players have a cl_guid
           * some have a Frozen Sand account (FSA)
        The FSA is a worldwide identifier while the cl_guid only identify a player on a given game server.
        See http://forum.bigbrotherbot.net/urban-terror-4-2/urt-4-2-discussion/
        """
        self.console.debug("b4.parsers.Iourt43Client.auth")
        if not self.authed and self.guid and not self.authorizing:

            self.authorizing = True

            name = self.name
            pbid = self.pbid
            guid = self.guid
            ip = self.ip

            if not pbid and self.cid:
                fsa_info = self.console.queryClientFrozenSandAccount(self.cid)
                self.pbid = pbid = fsa_info.get('login', None)

            self.console.verbose("Auth with %r", {'name': name, 'ip': ip, 'pbid': pbid, 'guid': guid})

            # FSA will be found in pbid
            if not self.pbid:
                # auth with cl_guid only
                try:
                    in_storage = self.auth_by_guid()
                    # fix up corrupted data due to bug #162
                    if in_storage and in_storage.pbid == 'None':
                        in_storage.pbid = None
                except Exception as e:
                    self.console.error("Auth by guid failed", exc_info=e)
                    self.authorizing = False
                    return False
            else:
                # auth with FSA
                try:
                    in_storage = self.auth_by_pbid()
                except Exception as e:
                    self.console.error("Auth by FSA failed", exc_info=e)
                    self.authorizing = False
                    return False

                if not in_storage:
                    # fallback on auth with cl_guid only
                    try:
                        in_storage = self.auth_by_guid()
                    except Exception as e:
                        self.console.error("Auth by guid failed (when no known FSA)", exc_info=e)
                        self.authorizing = False
                        return False

            if in_storage:
                self.lastVisit = self.timeEdit
                self.console.bot("Client found in the storage @%s: welcome back %s [FSA: '%s']", self.id, self.name, self.pbid)
            else:
                self.console.bot("Client not found in the storage %s [FSA: '%s'], create new", str(self.guid), self.pbid)

            self.connections = int(self.connections) + 1
            self.name = name
            self.ip = ip
            if pbid:
                self.pbid = pbid
            self.save()
            self.authed = True

            self.console.debug("Client authorized: %s [@%s] [GUID: '%s'] [FSA: '%s']", self.name, self.id, self.guid, self.pbid)

            # check for bans
            self.console.debug('parser iourt43 numBans = %s', self.numBans)

            if self.numBans > 0:
                ban = self.lastBan
                if ban:
                    self.reBan(ban)
                    self.authorizing = False
                    return False

            self.refreshLevel()
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_AUTH', data=self, client=self))
            self.authorizing = False
            return self.authed
        else:
            return False

    def __str__(self):
        return "Client43<@%s:%s|%s:\"%s\":%s>" % (self.id, self.guid, self.pbid, self.name, self.cid)


class Iourt43Parser(Iourt41Parser):
   
    gameName = 'iourt43'
    spamcontrolPlugin = None

    _logSync = 2

    _permban_with_frozensand = False
    _tempban_with_frozensand = False
    _allow_userinfo_overflow = False

    _commands = {
        'broadcast': '%(message)s',
        'message': 'tell %(cid)s %(message)s',
        'deadsay': 'tell %(cid)s %(message)s',
        'say': 'say %(message)s',
        'saybig': 'bigtext "%(message)s"',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'kick %(cid)s "%(reason)s"',
        'ban': 'addip %(cid)s',
        'tempban': 'kick %(cid)s "%(reason)s"',
        'banByIp': 'addip %(ip)s',
        'unbanByIp': 'removeip %(ip)s',
        'auth-permban': 'auth-ban %(cid)s 0 0 0',
        'auth-tempban': 'auth-ban %(cid)s %(days)s %(hours)s %(minutes)s',
        'slap': 'slap %(cid)s',
        'nuke': 'nuke %(cid)s',
        'mute': 'mute %(cid)s %(seconds)s',
        'kill': 'smite %(cid)s',
    }

    # remove the time off of the line
    _lineClear = re.compile(r'^(?:[0-9:]+\s?)?')
    _line_length = 90

    _lineFormats = (
        # Radio: 0 - 7 - 2 - "New Alley" - "I'm going for the flag"
        re.compile(r'^(?P<action>Radio): '
                   r'(?P<data>(?P<cid>[0-9]+) - '
                   r'(?P<msg_group>[0-9]+) - '
                   r'(?P<msg_id>[0-9]+) - '
                   r'"(?P<location>.*)" - '
                   r'"(?P<text>.*)")$', re.IGNORECASE),

        # Callvote: 1 - "map dressingroom"
        re.compile(r'^(?P<action>Callvote): (?P<data>(?P<cid>[0-9]+) - "(?P<vote_string>.*)")$', re.IGNORECASE),

        # Vote: 0 - 2
        re.compile(r'^(?P<action>Vote): (?P<data>(?P<cid>[0-9]+) - (?P<value>.*))$', re.IGNORECASE),

        # VotePassed: 1 - 0 - "reload"
        re.compile(r'^(?P<action>VotePassed): (?P<data>(?P<yes>[0-9]+) - (?P<no>[0-9]+) - "(?P<what>.*)")$', re.I),

        # VoteFailed: 1 - 1 - "restart"
        re.compile(r'^(?P<action>VoteFailed): (?P<data>(?P<yes>[0-9]+) - (?P<no>[0-9]+) - "(?P<what>.*)")$', re.I),

        # FlagCaptureTime: 0: 1234567890
        # FlagCaptureTime: 1: 1125480101
        re.compile(r'^(?P<action>FlagCaptureTime):\s(?P<cid>[0-9]+):\s(?P<captime>[0-9]+)$', re.IGNORECASE),

        # 13:34 ClientJumpRunStarted: 0 - way: 1
        # 13:34 ClientJumpRunStarted: 0 - way: 1 - attempt: 1 of 5
        re.compile(r'^(?P<action>ClientJumpRunStarted):\s'
                   r'(?P<cid>\d+)\s-\s'
                   r'(?P<data>way:\s'
                   r'(?P<way_id>\d+)'
                   r'(?:\s-\sattempt:\s'
                   r'(?P<attempt_num>\d+)\sof\s'
                   r'(?P<attempt_max>\d+))?)$', re.IGNORECASE),

        # 13:34 ClientJumpRunStopped: 0 - way: 1 - time: 12345
        # 13:34 ClientJumpRunStopped: 0 - way: 1 - time: 12345 - attempt: 1 of 5
        re.compile(r'^(?P<action>ClientJumpRunStopped):\s'
                   r'(?P<cid>\d+)\s-\s'
                   r'(?P<data>way:\s'
                   r'(?P<way_id>\d+)'
                   r'\s-\stime:\s'
                   r'(?P<way_time>\d+)'
                   r'(?:\s-\sattempt:\s'
                   r'(?P<attempt_num>\d+)\sof\s'
                   r'(?P<attempt_max>\d+'
                   r'))?)$', re.IGNORECASE),

        # 13:34 ClientJumpRunCanceled: 0 - way: 1
        # 13:34 ClientJumpRunCanceled: 0 - way: 1 - attempt: 1 of 5
        re.compile(r'^(?P<action>ClientJumpRunCanceled):\s'
                   r'(?P<cid>\d+)\s-\s'
                   r'(?P<data>way:\s'
                   r'(?P<way_id>\d+)'
                   r'(?:\s-\sattempt:\s'
                   r'(?P<attempt_num>\d+)\sof\s'
                   r'(?P<attempt_max>\d+))?)$', re.IGNORECASE),

        # 13:34 ClientSavePosition: 0 - 335.384887 - 67.469154 - -23.875000
        # 13:34 ClientLoadPosition: 0 - 335.384887 - 67.469154 - -23.875000
        re.compile(r'^(?P<action>Client(Save|Load)Position):\s'
                   r'(?P<cid>\d+)\s-\s'
                   r'(?P<data>'
                   r'(?P<x>-?\d+(?:\.\d+)?)\s-\s'
                   r'(?P<y>-?\d+(?:\.\d+)?)\s-\s'
                   r'(?P<z>-?\d+(?:\.\d+)?))$', re.IGNORECASE),

        # 13:34 ClientGoto: 0 - 1 - 335.384887 - 67.469154 - -23.875000
        re.compile(r'^(?P<action>ClientGoto):\s'
                   r'(?P<cid>\d+)\s-\s'
                   r'(?P<tcid>\d+)\s-\s'
                   r'(?P<data>'
                   r'(?P<x>-?\d+(?:\.\d+)?)\s-\s'
                   r'(?P<y>-?\d+(?:\.\d+)?)\s-\s'
                   r'(?P<z>-?\d+(?:\.\d+)?))$', re.IGNORECASE),

        # ClientSpawn: 0
        # ClientMelted: 1
        re.compile(r'^(?P<action>Client(Melted|Spawn)):\s(?P<cid>[0-9]+)$', re.IGNORECASE),
        
        # Assist: 0 14 15: -[TPF]-PtitBigorneau assisted Bot1_14 to kill Bot1_15
        re.compile(
            r'^(?P<action>Assist):\s(?P<acid>[0-9]+)\s(?P<kcid>[0-9]+)\s(?P<dcid>[0-9]+):\s+(?P<text>.*)$',
            re.IGNORECASE),
        
        # Generated with ioUrbanTerror v4.1:
        # Hit: 12 7 1 19: BSTHanzo[FR] hit ercan in the Helmet
        # Hit: 13 10 0 8: Grover hit jacobdk92 in the Head
        re.compile(r'^(?P<action>Hit):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<hitloc>[0-9]+)\s'
                   r'(?P<aweap>[0-9]+):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # 6:37 Kill: 0 1 16: XLR8or killed =lvl1=Cheetah by UT_MOD_SPAS
        # 2:56 Kill: 14 4 21: Qst killed Leftovercrack by UT_MOD_PSG1
        # 6:37 Freeze: 0 1 16: Fenix froze Biddle by UT_MOD_SPAS
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<aweap>[0-9]+):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # ThawOutStarted: 0 1: Fenix started thawing out Biddle
        # ThawOutFinished: 0 1: Fenix thawed out Biddle
        re.compile(r'^(?P<action>ThawOut(Started|Finished)):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<tcid>[0-9]+):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # Processing chats and tell events...
        # 5:39 saytell: 15 16 repelSteeltje: nno
        # 5:39 saytell: 15 15 repelSteeltje: nno
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<acid>[0-9]+)\s'
                   r'(?P<name>.+?):\s+'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # SGT: fix issue with onSay when something like this come and the match could'nt find the name group
        # say: 7 -crespino-:
        # say: 6 ^5Marcel ^2[^6CZARMY^2]: !help
        re.compile(r'^(?P<action>[a-z]+):\s'
                   r'(?P<data>'
                   r'(?P<cid>[0-9]+)\s'
                   r'(?P<name>[^ ]+):\s*'
                   r'(?P<text>.*))$', re.IGNORECASE),

        # 15:42 Flag Return: RED
        # 15:42 Flag Return: BLUE
        re.compile(r'^(?P<action>Flag Return):\s(?P<data>(?P<color>.+))$', re.IGNORECASE),

        # Bombmode actions:
        # 3:06 Bombholder is 2
        re.compile(r'^(?P<action>Bombholder)(?P<data>\sis\s(?P<cid>[0-9]))$', re.IGNORECASE),

        # was planted, was defused, was tossed, has been collected (doh, how gramatically correct!)
        # 2:13 Bomb was tossed by 2
        # 2:32 Bomb was planted by 2
        # 3:01 Bomb was defused by 3!
        # 2:17 Bomb has been collected by 2
        re.compile(r'^(?P<action>Bomb)\s'
                   r'(?P<data>(was|has been)\s'
                   r'(?P<subaction>[a-z]+)\sby\s'
                   r'(?P<cid>[0-9]+).*)$', re.IGNORECASE),

        # 17:24 Pop!
        re.compile(r'^(?P<action>Pop)!$', re.IGNORECASE),

        # Falling thru? Item stuff and so forth
        re.compile(r'^(?P<action>[a-z]+):\s(?P<data>.*)$', re.IGNORECASE),

        # Shutdowngame and Warmup... the one word lines
        re.compile(r'^(?P<action>[a-z]+):$', re.IGNORECASE)
    )

    # map: ut4_casa
    # num score ping name            lastmsg address               qport rate
    # --- ----- ---- --------------- ------- --------------------- ----- -----
    #   2     0   19 ^1XLR^78^8^9or        0 145.99.135.227:27960  41893  8000  # player with a live ping
    #   4     0 CNCT Dz!k^7              450 83.175.191.27:64459   50308 20000  # connecting player
    #   9     0 ZMBI ^7                 1900 81.178.80.68:27960    10801  8000  # zombies (need to be disconnected!)
    _regPlayer = re.compile(r'^\s*(?P<slot>[0-9]+)\s+(?P<score>[0-9-]+)\s+'
                            r'(?P<ping>[0-9]+|CNCT|ZMBI)\s+(?P<name>.*?)\s+'
                            r'(?P<last>[0-9]+)\s+(?P<ip>.*)\s+'
                            r'(?P<qport>[0-9]+)\s+(?P<rate>[0-9]+)$', re.IGNORECASE)

    _reColor = re.compile(r'(\^\d)')

    # Map: ut4_algiers
    # Players: 8
    # Scores: R:97 B:98
    # 0:  FREE k:0 d:0 ping:0
    # 4: yene RED k:16 d:8 ping:50 92.104.110.192:63496
    _reTeamScores = re.compile(r'^Scores:\s+'
                               r'R:(?P<RedScore>.+)\s+'
                               r'B:(?P<BlueScore>.+)$', re.IGNORECASE)

    _rePlayerScore = re.compile(r'^(?P<slot>[0-9]+):(?P<name>.*)\s+'
                                r'TEAM:(?P<team>RED|BLUE|SPECTATOR|FREE)\s+'
                                r'KILLS:(?P<kill>[0-9]+)\s+'
                                r'DEATHS:(?P<death>[0-9]+)\s+'
                                r'ASSISTS:(?P<assist>[0-9]+)\s+'
                                r'PING:(?P<ping>[0-9]+|CNCT|ZMBI)\s+'
                                r'AUTH:(?P<auth>.*)\s+IP:(?P<ip>.*)$', re.IGNORECASE)

    # /rcon auth-whois replies patterns
    # 'auth: id: 0 - name: ^7Courgette - login: courgette - notoriety: serious - level: -1  \n'
    _re_authwhois = re.compile(r'^auth: id: (?P<cid>\d+) - '
                               r'name: \^7(?P<name>.+?) - '
                               r'login: (?P<login>.*?) - '
                               r'notoriety: (?P<notoriety>.+?) - '
                               r'level: (?P<level>-?\d+?)(?:\s+- (?P<extra>.*))?\s*$', re.MULTILINE)

    ## kill modes (xlr_weaponstats)
    MOD_WATER = '1'
    MOD_LAVA = '3'
    MOD_TELEFRAG = '5'
    MOD_FALLING = '6'
    MOD_SUICIDE = '7'
    MOD_TRIGGER_HURT = '9'
    MOD_CHANGE_TEAM = '10'
    UT_MOD_KNIFE = '12'
    UT_MOD_KNIFE_THROWN = '13'
    UT_MOD_BERETTA = '14'
    UT_MOD_DEAGLE = '15'
    UT_MOD_SPAS = '16'
    UT_MOD_UMP45 = '17'
    UT_MOD_MP5K = '18'
    UT_MOD_LR300 = '19'
    UT_MOD_G36 = '20'
    UT_MOD_PSG1 = '21'
    UT_MOD_HK69 = '22'
    UT_MOD_BLED = '23'
    UT_MOD_KICKED = '24'
    UT_MOD_HEGRENADE = '25'
    UT_MOD_SR8 = '28'
    UT_MOD_AK103 = '30'
    UT_MOD_SPLODED = '31'
    UT_MOD_SLAPPED = '32'
    UT_MOD_SMITED = '33'
    UT_MOD_BOMBED = '34'
    UT_MOD_NUKED = '35'
    UT_MOD_NEGEV = '36'
    UT_MOD_HK69_HIT = '37'
    UT_MOD_M4 = '38'
    UT_MOD_GLOCK = '39'
    UT_MOD_COLT1911 = '40'
    UT_MOD_MAC11 = '41'
    UT_MOD_FRF1 = '42'
    UT_MOD_BENELLI = '43'
    UT_MOD_P90 = '44'
    UT_MOD_MAGNUM = '45'
    UT_MOD_TOD50 = '46'
    UT_MOD_FLAG = '47'
    UT_MOD_GOOMBA = '48'

    # HIT LOCATIONS (xlr_bodyparts)
    HL_HEAD = '1'
    HL_HELMET = '2'
    HL_TORSO = '3'
    HL_VEST = '4'
    HL_ARM_L = '5'
    HL_ARM_R = '6'
    HL_GROIN = '7'
    HL_BUTT = '8'
    HL_LEG_UPPER_L = '9'
    HL_LEG_UPPER_R = '10'
    HL_LEG_LOWER_L = '11'
    HL_LEG_LOWER_R = '12'
    HL_FOOT_L = '13'
    HL_FOOT_R = '14'

    ## weapons id on Hit: lines are different than the one
    ## on the Kill: lines. Here the translation table
    hitweapon2killweapon = {
        1: UT_MOD_KNIFE,
        2: UT_MOD_BERETTA,
        3: UT_MOD_DEAGLE,
        4: UT_MOD_SPAS,
        5: UT_MOD_MP5K,
        6: UT_MOD_UMP45,
        8: UT_MOD_LR300,
        9: UT_MOD_G36,
        10: UT_MOD_PSG1,
        14: UT_MOD_SR8,
        15: UT_MOD_AK103,
        17: UT_MOD_NEGEV,
        19: UT_MOD_M4,
        20: UT_MOD_GLOCK,
        21: UT_MOD_COLT1911,
        22: UT_MOD_MAC11,
        23: UT_MOD_FRF1,
        24: UT_MOD_BENELLI,
        25: UT_MOD_P90,
        26: UT_MOD_MAGNUM,
        27: UT_MOD_TOD50,
        29: UT_MOD_KICKED,
        30: UT_MOD_KNIFE_THROWN,
    }

    ## damage table
    ## Fenix: Hit locations start with index 1 (HL_HEAD).
    ##        Since lists are 0 indexed we'll need to adjust the hit location
    ##        code to match the index number. Instead of adding random values
    ##        in the damage table, the adjustment will be made in _getDamagePoints.
    damage = {
        MOD_TELEFRAG: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        UT_MOD_KNIFE: [100, 60, 44, 35, 20, 20, 40, 37, 20, 20, 18, 18, 15, 15],
        UT_MOD_KNIFE_THROWN: [100, 60, 44, 35, 20, 20, 40, 37, 20, 20, 18, 18, 15, 15],
        UT_MOD_BERETTA: [100, 40, 33, 22, 13, 13, 22, 22, 15, 15, 13, 13, 11, 11],
        UT_MOD_DEAGLE: [100, 66, 57, 38, 22, 22, 42, 38, 28, 28, 22, 22, 18, 18],
        UT_MOD_SPAS: [100 ,80 ,80 ,40 ,32 ,32 ,59 ,59 ,40 ,40 ,40 ,40 ,40 ,40],
        UT_MOD_UMP45: [100, 51, 44, 29, 17, 17, 31, 28, 20, 20, 17, 17, 14, 14],
        UT_MOD_MP5K: [50, 34, 30, 22, 13, 13, 22, 20, 15, 15, 13, 13, 11, 11],
        UT_MOD_LR300: [100, 51, 44, 29, 17, 17, 31, 28, 20, 20, 17, 17, 14, 14],
        UT_MOD_G36: [100, 51, 44, 29, 17, 17, 29, 28, 20, 20, 17, 17, 14, 14],
        UT_MOD_PSG1: [100, 100, 97, 70, 36, 36, 75, 70, 41, 41, 36, 36, 29, 29],
        UT_MOD_HK69: [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
        UT_MOD_BLED: [15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15],
        UT_MOD_KICKED: [30, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20],
        UT_MOD_HEGRENADE: [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
        UT_MOD_SR8: [100, 100, 100, 100, 50, 50, 100, 100, 60, 60, 50, 50, 40, 40],
        UT_MOD_AK103: [100, 58, 51, 34, 19, 19, 39, 35, 22, 22, 19, 19, 15, 15],
        UT_MOD_NEGEV: [50, 34, 30, 22, 11, 11, 23, 21, 13, 13, 11, 11, 9, 9],
        UT_MOD_HK69_HIT: [20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20],
        UT_MOD_M4: [100, 51, 44, 29, 17, 17, 31, 28, 20, 20, 17, 17, 14, 14],
        UT_MOD_GLOCK: [100, 45, 29, 35, 15, 15, 29, 27, 20, 20, 15, 15, 11, 11],
        UT_MOD_COLT1911: [100, 60, 40, 30, 15, 15, 32, 29, 22, 22, 15, 15, 11, 11],
        UT_MOD_MAC11: [50, 29, 20, 16, 13, 13, 16, 15, 15, 15, 13, 13, 11, 11],
        UT_MOD_GOOMBA: [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
        UT_MOD_TOD50: [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
        UT_MOD_FRF1: [100, 100, 96, 76, 40, 40, 76, 74, 50, 50, 40, 40, 30, 30],
        UT_MOD_BENELLI: [100, 100, 90, 67, 32, 32, 60, 50, 35, 35, 30, 30, 20, 20],
        UT_MOD_P90: [50, 40, 33, 27, 16, 16, 27, 25, 17, 17, 15, 15, 12, 12],
        UT_MOD_MAGNUM: [100, 82, 66, 50, 33, 33, 57, 52, 40, 33, 25, 25],
    }   

    ####################################################################################################################
    #                                                                                                                  #
    #   PARSER INITIALIZATION                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def __new__(cls, *args, **kwargs):
        Iourt43Parser.patch_Clients()
        return Iourt41Parser.__new__(cls)

    def startup(self):
        """
        Called after the parser is created before run().
        """
        #self.debug("b4.parsers.Iourt43Parser.startup\n")
        try:
            cvar = self.getCvar('gamename')
            gamename = cvar.getString() if cvar else None
            if gamename != 'q3urt43':
                self.error("The iourt43 B4 parser cannot be used with a game server other than Urban Terror 4.3")
                raise SystemExit(220)
        except Exception as e:
            self.warning("Could not query server for gamename.", exc_info=e)

        Iourt41Parser.startup(self)

        # add UrT 4.2 specific events
        self.Events.createEvent('EVT_CLIENT_RADIO', 'Event client radio')
        self.Events.createEvent('EVT_GAME_FLAG_HOTPOTATO', 'Event game hotpotato')
        self.Events.createEvent('EVT_CLIENT_CALLVOTE', 'Event client call vote')
        self.Events.createEvent('EVT_CLIENT_VOTE', 'Event client vote')
        self.Events.createEvent('EVT_VOTE_PASSED', 'Event vote passed')
        self.Events.createEvent('EVT_VOTE_FAILED', 'Event vote failed')
        self.Events.createEvent('EVT_FLAG_CAPTURE_TIME', 'Event flag capture time')
        self.Events.createEvent('EVT_CLIENT_JUMP_RUN_START', 'Event client jump run started')
        self.Events.createEvent('EVT_CLIENT_JUMP_RUN_STOP', 'Event client jump run stopped')
        self.Events.createEvent('EVT_CLIENT_JUMP_RUN_CANCEL', 'Event client jump run canceled')
        self.Events.createEvent('EVT_CLIENT_POS_SAVE', 'Event client position saved')
        self.Events.createEvent('EVT_CLIENT_POS_LOAD', 'Event client position loaded')
        self.Events.createEvent('EVT_CLIENT_GOTO', 'Event client goto')
        self.Events.createEvent('EVT_CLIENT_SPAWN', 'Event client spawn')
        self.Events.createEvent('EVT_CLIENT_SURVIVOR_WINNER', 'Event client survivor winner')
        self.Events.createEvent('EVT_CLIENT_FREEZE', 'Event client freeze')
        self.Events.createEvent('EVT_CLIENT_THAWOUT_STARTED', 'Event client thawout started')
        self.Events.createEvent('EVT_CLIENT_THAWOUT_FINISHED', 'Event client thawout finished')
        self.Events.createEvent('EVT_CLIENT_MELTED', 'Event client melted')
        # add UrT 4.3 specific events
        self.EVT_ASSIST = self.Events.createEvent('EVT_ASSIST', 'Event assist')

        self._eventMap['hotpotato'] = self.getEventID('EVT_GAME_FLAG_HOTPOTATO')
        self._eventMap['warmup'] = self.getEventID('EVT_GAME_WARMUP')

        self.load_conf_frozensand_ban_settings()
        self.load_conf_userinfo_overflow()

    def pluginsStarted(self):
        """
        Called when all plugins are started.
        """
        self.debug("b4.parsers.Iourt43Parser.pluginsStarted\n")
        self.spamcontrolPlugin = self.getPlugin("spamcontrol")
        if self.spamcontrolPlugin:
            self.patch_spamcontrolPlugin()

    ####################################################################################################################
    #                                                                                                                  #
    #   CONFIG LOADERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def load_conf_frozensand_ban_settings(self):
        """
        Load ban settings according to auth system cvars.
        """
        self.debug("b4.parsers.Iourt43Parser.load_conf_frozensand_ban_settings\n")
        try:
            frozensand_auth_available = self.is_frozensand_auth_available()
        except Exception as e:
            self.warning("Could not query server for cvar auth", exc_info=e)
            frozensand_auth_available = False
        self.info("Frozen Sand auth system enabled : %s" % ('yes' if frozensand_auth_available else 'no'))

        try:
            cvar = self.getCvar('auth_owners')
            if cvar:
                frozensand_auth_owners = cvar.getString()
            else:
                frozensand_auth_owners = None
        except Exception as e:
            self.warning("Could not query server for cvar auth_owners", exc_info=e)
            frozensand_auth_owners = ""

        yn = ('yes - %s' % frozensand_auth_available) if frozensand_auth_owners else 'no'
        self.info("Frozen Sand auth_owners set : %s" % yn)

        if frozensand_auth_available and frozensand_auth_owners:
            self.load_conf_permban_with_frozensand()
            self.load_conf_tempban_with_frozensand()
            if self._permban_with_frozensand or self._tempban_with_frozensand:
                self.info("NOTE: when banning with the Frozen Sand auth system, B3 cannot remove "
                          "the bans on the urbanterror.info website. To unban a player you will "
                          "have to first unban him on B3 and then also unban him on the official Frozen Sand "
                          "website : http://www.urbanterror.info/groups/list/all/?search=%s" % frozensand_auth_owners)
        else:
            self.info("Ignoring settings about banning with Frozen Sand auth system as the "
                      "auth system is not enabled or auth_owners not set")

    def load_conf_permban_with_frozensand(self):
        """
        Load permban configuration from b4_xml.
        """
        self.debug("b4.parsers.Iourt43Parser.load_conf_permban_with_frozensand\n")
        self._permban_with_frozensand = False
        if self.config.has_option('server', 'permban_with_frozensand'):
            try:
                self._permban_with_frozensand = self.config.getboolean('server', 'permban_with_frozensand')
            except ValueError as err:
                self.warning(err)

        self.info("Send permbans to Frozen Sand : %s" % ('yes' if self._permban_with_frozensand else 'no'))

    def load_conf_tempban_with_frozensand(self):
        """
        Load tempban configuration from b4_xml.
        """
        self.debug("b4.parsers.Iourt43Parser.load_conf_tempban_with_frozensand\n")
        self._tempban_with_frozensand = False
        if self.config.has_option('server', 'tempban_with_frozensand'):
            try:
                self._tempban_with_frozensand = self.config.getboolean('server', 'tempban_with_frozensand')
            except ValueError as err:
                self.warning(err)

        self.info("Send temporary bans to Frozen Sand : %s" % ('yes' if self._tempban_with_frozensand else 'no'))

    def load_conf_userinfo_overflow(self):
        """
        Load userinfo overflow configuration settings.
        """
        self.debug("b4.parsers.Iourt43Parser.load_conf_userinfo_overflow\n")
        self._allow_userinfo_overflow = False
        if self.config.has_option('server', 'allow_userinfo_overflow'):
            try:
                self._allow_userinfo_overflow = self.config.getboolean('server', 'allow_userinfo_overflow')
            except ValueError as err:
                self.warning(err)

        self.info("Allow userinfo string overflow : %s" % ('yes' if self._allow_userinfo_overflow else 'no'))

        if self._allow_userinfo_overflow:
            self.info("NOTE: due to a bug in UrT 4.3 gamecode it is possible to exploit the maximum client name length "
                      "and generate a userinfo string longer than the imposed limits: clients connecting with nicknames "
                      "longer than 32 characters will be automatically kicked by B3 in order to prevent any sort of error")
        else:
            self.info("NOTE: due to a bug in UrT 4.3 gamecode it is possible to exploit the maximum client name length "
                      "and generate a userinfo string longer than the imposed limits: B3 will truncate nicknames of clients "
                      "which are longer than 32 characters")

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################
    
    def OnClientuserinfo(self, action, data, match=None):
        # 2 \ip\145.99.135.227:27960\challenge\-232198920\qport\2781\protocol\68\battleye\1\name\[SNT]^1XLR^78or..
        # 0 \gear\GMIORAA\team\blue\skill\5.000000\characterfile\bots/ut_chicken_c.c\color\4\sex\male\race\2\snaps\20\..
        self.debug("b4.parsers.Iourt43Parser.OnClientuserinfo\n")
        bclient = self.parseUserInfo(data)
        bot = False
        if not 'cl_guid' in bclient and 'skill' in bclient:
            # must be a bot connecting
            self.bot('Bot connecting!')
            bclient['ip'] = '0.0.0.0'
            bclient['cl_guid'] = 'BOT' + str(bclient['cid'])
            bot = True

        if 'name' in bclient:
            # remove spaces from name
            bclient['name'] = bclient['name'].replace(' ', '')

        # split port from ip field
        if 'ip' in bclient:
            ip_port_data = bclient['ip'].split(':', 1)
            bclient['ip'] = ip_port_data[0]
            if len(ip_port_data) > 1:
                bclient['port'] = ip_port_data[1]

        if 'team' in bclient:
            bclient['team'] = self.getTeam(bclient['team'])

        # because using the name client would get confusing we're calling the "client software" app
        if 'client' in bclient:
            if len(bclient['client']) > 32:
                bclient['app'] = bclient['client'][0:32]
            else:
                bclient['app'] = bclient['client']
            #self.debug('NOISY client found in bclient')
        else:
            bclient['app'] = ''
            #self.debug('NOISY client not in bclient')

        if 'isocode' not in bclient:
            bclient['isocode'] = ''

        if 'permmute' not in bclient:
            bclient['permmute'] = '0'

        self.verbose('Parsed user info1: %s' % bclient)

        if bclient:

            client = self.clients.getByCID(bclient['cid'])

            if client:
                # update existing client
                for k, v in bclient.iteritems():
                    if hasattr(client, 'gear') and k == 'gear' and client.gear != v:
                        self.queueEvent(b4.b4_events.Event(self.getEventID('EVT_CLIENT_GEAR_CHANGE'), v, client))
                    if not k.startswith('_') and k not in ('login', 'password', 'groupBits', 'maskLevel', 'autoLogin', 'greeting', 'app'):
                        setattr(client, k, v)
                        #self.debug("NOISY iourt43 setting client field %s to %s" % (k, v))
                    if k == 'app' and client.app == "":
                        setattr(client, k, v)
                        #self.console.warning("NOISY iourt43 %s; id %s setting app to %s" % (client.name, client.id, v))
            else:
                # make a new client
                if 'cl_guid' in bclient:
                    guid = bclient['cl_guid']
                else:
                    guid = 'unknown'

                if 'authl' in bclient:
                    # authl contains FSA since UrT 4.2.022
                    fsa = bclient['authl']
                else:
                    # query FrozenSand Account
                    auth_info = self.queryClientFrozenSandAccount(bclient['cid'])
                    fsa = auth_info.get('login', None)

                # v1.0.17 - mindriot - 02-Nov-2008
                if 'name' not in bclient:
                    bclient['name'] = self._empty_name_default

                # v 1.10.5 => https://github.com/BigBrotherBot/big-brother-bot/issues/346
                if len(bclient['name']) > 32:
                    self.debug("UrT4.3 bug spotted! %s [GUID: '%s'] [FSA: '%s'] has a too long "
                               "nickname (%s characters)", bclient['name'], guid, fsa, len(bclient['name']))
                    if self._allow_userinfo_overflow:
                        x = bclient['name'][0:32]
                        self.debug('Truncating %s (%s) nickname => %s (%s)', bclient['name'], len(bclient['name']), x, len(x))
                        bclient['name'] = x
                    else:
                        self.debug("Connection denied to  %s [GUID: '%s'] [FSA: '%s']", bclient['name'], guid, fsa)
                        self.write(self.getCommand('kick', cid=bclient['cid'], reason='userinfo string overflow protection'))
                        return

                if 'ip' not in bclient:
                    if guid == 'unknown':
                        # happens when a client is (temp)banned and got kicked so client was destroyed,
                        # but infoline was still waiting to be parsed.
                        self.debug('Client disconnected: ignoring...')
                        return None
                    else:
                        try:
                            # see issue xlr8or/big-brother-bot#87 - ip can be missing
                            self.debug("Missing ip: trying to get ip with 'status'")
                            plist = self.getPlayerList()
                            data = plist[bclient['cid']]
                            ip = data['ip']
                            if ip in {'loopback', 'localhost'}:
                                ip = '127.0.0.1'
                            elif ':' in ip:
                                ip = ip.split(':')[0]
                            bclient['ip'] = ip
                        except Exception as err:
                            bclient['ip'] = ''
                            self.warning("Failed to get client %s ip address" % bclient['cid'], err)

                if 'app' not in bclient:
                    bclient['app'] = ''

                if 'isocode' not in bclient:
                    bclient['isocode'] = ''

                nguid = ''
                # override the guid... use ip's only if self.console.IpsOnly is set True.
                if self.IpsOnly:
                    nguid = bclient['ip']
                # replace last part of the guid with two segments of the ip
                elif self.IpCombi:
                    i = bclient['ip'].split('.')
                    d = len(i[0]) + len(i[1])
                    nguid = guid[:-d] + i[0] + i[1]
                # Quake clients don't have a cl_guid, we'll use ip instead
                elif guid == 'unknown':
                    nguid = bclient['ip']

                if nguid != '':
                    guid = nguid

                self.clients.newClient(bclient['cid'], name=bclient['name'], ip=bclient['ip'], bot=bot, guid=guid, pbid=fsa, app=bclient['app'], isocode=bclient['isocode'], permmute=bclient['permmute'])

        return None

    def OnClientuserinfochanged(self, action, data, match=None):
        # 7 n\[SNT]^1XLR^78or\t\3\r\2\tl\0\f0\\f1\\f2\\a0\0\a1\0\a2\0
        self.debug("b4.parsers.Iourt43Parser.OnClientuserinfochanged\n")
        parseddata = self.parseUserInfo(data)
        self.verbose('Parsed userinfo: %s' % parseddata)
        if parseddata:
            client = self.clients.getByCID(parseddata['cid'])
            if client:
                # update existing client
                if 'n' in parseddata:
                    setattr(client, 'name', parseddata['n'])

                if 't' in parseddata:
                    team = self.getTeam(parseddata['t'])
                    setattr(client, 'team', team)

                    if 'r' in parseddata:
                        if team == b4.b4_clients.TEAM_BLUE:
                            setattr(client, 'raceblue', parseddata['r'])
                        elif team == b4.b4_clients.TEAM_RED:
                            setattr(client, 'racered', parseddata['r'])
                        elif team == b4.b4_clients.TEAM_FREE:
                            setattr(client, 'racefree', parseddata['r'])

                    if parseddata.get('f0') is not None \
                        and parseddata.get('f1') is not None \
                        and parseddata.get('f2') is not None:

                        data = "%s,%s,%s" % (parseddata['f0'], parseddata['f1'], parseddata['f2'])
                        if team == b4.b4_clients.TEAM_BLUE:
                            setattr(client, 'funblue', data)
                        elif team == b4.b4_clients.TEAM_RED:
                            setattr(client, 'funred', data)

                if 'a0' in parseddata and 'a1' in parseddata and 'a2' in parseddata:
                    setattr(client, 'cg_rgb', "%s %s %s" % (parseddata['a0'], parseddata['a1'], parseddata['a2']))

    def OnRadio(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnRadio\n")
        cid = match.group('cid')
        msg_group = match.group('msg_group')
        msg_id = match.group('msg_id')
        location = match.group('location')
        text = match.group('text')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_RADIO', client=client, data={'msg_group': msg_group, 'msg_id': msg_id,
                                                                      'location': location, 'text': text})

    def OnCallvote(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnCallvote\n")
        cid = match.group('cid')
        vote_string = match.group('vote_string')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_CALLVOTE', client=client, data=vote_string)

    def OnVote(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnVote\n")
        cid = match.group('cid')
        value = match.group('value')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_VOTE', client=client, data=value)

    def OnVotepassed(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnVotepassed\n")
        yes_count = int(match.group('yes'))
        no_count = int(match.group('no'))
        vote_what = match.group('what')
        return self.getEvent('EVT_VOTE_PASSED', data={'yes': yes_count, 'no': no_count, 'what': vote_what})

    def OnVotefailed(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnVotefailed\n")
        yes_count = int(match.group('yes'))
        no_count = int(match.group('no'))
        vote_what = match.group('what')
        return self.getEvent('EVT_VOTE_FAILED', data={'yes': yes_count, 'no': no_count, 'what': vote_what})

    def OnFlagcapturetime(self, action, data, match=None):
        # FlagCaptureTime: 0: 1234567890
        # FlagCaptureTime: 1: 1125480101
        self.debug("b4.parsers.Iourt43Parser.OnFlagcapturetime\n")
        cid = match.group('cid')
        captime = int(match.group('captime'))
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_FLAG_CAPTURE_TIME', client=client, data=captime)

    def OnClientjumprunstarted(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnClientjumprunstarted\n")
        cid = match.group('cid')
        way_id = match.group('way_id')
        attempt_num = match.group('attempt_num')
        attempt_max = match.group('attempt_max')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_JUMP_RUN_START', client=client, data={'way_id': way_id,
                                                                               'attempt_num': attempt_num,
                                                                               'attempt_max': attempt_max})

    def OnClientjumprunstopped(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnClientjumprunstopped\n")
        cid = match.group('cid')
        way_id = match.group('way_id')
        way_time = match.group('way_time')
        attempt_num = match.group('attempt_num')
        attempt_max = match.group('attempt_max')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_JUMP_RUN_STOP', client=client, data={'way_id': way_id,
                                                                              'way_time': way_time,
                                                                              'attempt_num': attempt_num,
                                                                              'attempt_max': attempt_max})
    
    def OnClientjumpruncanceled(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnClientjumpruncanceled\n")
        cid = match.group('cid')
        way_id = match.group('way_id')
        attempt_num = match.group('attempt_num')
        attempt_max = match.group('attempt_max')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_JUMP_RUN_CANCEL', client=client, data={'way_id': way_id,
                                                                                'attempt_num': attempt_num,
                                                                                'attempt_max': attempt_max})
    
    def OnClientsaveposition(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnClientsaveposition\n")
        cid = match.group('cid')
        position = float(match.group('x')), float(match.group('y')), float(match.group('z'))
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_POS_SAVE', client=client, data={'position': position})

    def OnClientloadposition(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnClientloadposition\n")
        cid = match.group('cid')
        position = float(match.group('x')), float(match.group('y')), float(match.group('z'))
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        return self.getEvent('EVT_CLIENT_POS_LOAD', client=client, data={'position': position})
    
    def OnClientgoto(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnClientgoto\n")
        cid = match.group('cid')
        tcid = match.group('tcid')
        position = float(match.group('x')), float(match.group('y')), float(match.group('z'))
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None
        
        target = self.getByCidOrJoinPlayer(tcid)
        if not target:
            self.debug('No target client found')
            return None
            
        return self.getEvent('EVT_CLIENT_GOTO', client=client, target=target, data={'position': position})

    def OnClientspawn(self, action, data, match=None):
        # ClientSpawn: 0
        self.debug("b4.parsers.Iourt43Parser.OnClientspawn\n")
        cid = match.group('cid')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None

        client.state = b4.b4_clients.STATE_ALIVE
        return self.getEvent('EVT_CLIENT_SPAWN', client=client)

    def OnClientmelted(self, action, data, match=None):
        # ClientMelted: 0
        self.debug("b4.parsers.Iourt43Parser.OnClientmelted\n")
        cid = match.group('cid')
        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client found')
            return None

        client.state = b4.b4_clients.STATE_ALIVE
        return self.getEvent('EVT_CLIENT_MELTED', client=client)

    def OnSurvivorwinner(self, action, data, match=None):
        # SurvivorWinner: Blue
        # SurvivorWinner: Red
        # SurvivorWinner: 0
        # queue round and in any case (backwards compatibility for plugins)
        self.debug("b4.parsers.Iourt43Parser.OnSurvivorwinner\n")
        self.queueEvent(self.getEvent('EVT_GAME_ROUND_END'))
        if data in ('Blue', 'Red'):
            return self.getEvent('EVT_SURVIVOR_WIN', data=data)
        else:
            client = self.getByCidOrJoinPlayer(data)
            if not client:
                self.debug('No client found')
                return None
            return self.getEvent('EVT_CLIENT_SURVIVOR_WINNER', client=client)

    def OnFreeze(self, action, data, match=None):
        # 6:37 Freeze: 0 1 16: Fenix froze Biddle by UT_MOD_SPAS
        self.debug("b4.parsers.Iourt43Parser.OnFreeze\n")
        victim = self.getByCidOrJoinPlayer(match.group('cid'))
        if not victim:
            self.debug('No victim')
            return None

        attacker = self.getByCidOrJoinPlayer(match.group('acid'))
        if not attacker:
            self.debug('No attacker')
            return None

        weapon = match.group('aweap')
        if not weapon:
            self.debug('No weapon')
            return None

        victim.state = b4.b4_clients.STATE_DEAD
        return self.getEvent('EVT_CLIENT_FREEZE', data=weapon, client=attacker, target=victim)

    def OnThawoutstarted(self, action, data, match=None):
        # ThawOutStarted: 0 1: Fenix started thawing out Biddle
        self.debug("b4.parsers.Iourt43Parser.OnThawoutstarted\n")
        client = self.getByCidOrJoinPlayer(match.group('cid'))
        if not client:
            self.debug('No client')
            return None

        target = self.getByCidOrJoinPlayer(match.group('tcid'))
        if not target:
            self.debug('No target')
            return None

        return self.getEvent('EVT_CLIENT_THAWOUT_STARTED', client=client, target=target)

    def OnThawoutfinished(self, action, data, match=None):
        # ThawOutFinished: 0 1: Fenix thawed out Biddle
        self.debug("b4.parsers.Iourt43Parser.OnThawoutfinished\n")
        client = self.getByCidOrJoinPlayer(match.group('cid'))
        if not client:
            self.debug('No client')
            return None

        target = self.getByCidOrJoinPlayer(match.group('tcid'))
        if not target:
            self.debug('No target')
            return None

        target.state = b4.b4_clients.STATE_ALIVE
        return self.getEvent('EVT_CLIENT_THAWOUT_FINISHED', client=client, target=target)
        
    def OnAssist(self, action, data, match=None):
        self.debug("b4.parsers.Iourt43Parser.OnAssist\n")

        cid = match.group('acid')
        vid = match.group('dcid')
        aid = match.group('kcid')

        client = self.getByCidOrJoinPlayer(cid)
        if not client:
            self.debug('No client')
            return None

        victim = self.getByCidOrJoinPlayer(vid)
        if not victim:
            self.debug('No victim')
            return None

        attacker = self.getByCidOrJoinPlayer(aid)
        if not attacker:
            self.debug('No attacker')
            return None

        return self.getEvent(self.EVT_ASSIST, client=client, target=victim, data=attacker)

    ####################################################################################################################
    #                                                                                                                  #
    #   B3 PARSER INTERFACE IMPLEMENTATION                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def authorizeClients(self):
        """
        For all connected players, fill the client object with properties allowing to find
        the user in the database (usually guid, or punkbuster id, ip) and call the
        Client.auth() method.
        """
        self.debug("b4.parsers.Iourt43Parser.authorizeClients\n")
        pass

    def ban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Ban a given client.
        :param client: The client to ban
        :param reason: The reason for this ban
        :param admin: The admin who performed the ban
        :param silent: Whether to announce this ban
        """
        self.debug("b4.parsers.Iourt43Parser.ban\n")
        self.debug('BAN : client: %s, reason: %s', client, reason)
        if isinstance(client, b4.b4_clients.Client) and not client.guid:
            # client has no guid, kick instead
            return self.kick(client, reason, admin, silent)
        elif isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('ban', cid=client, reason=reason))
            return
        elif not client.id:
            # no client id, database must be down, do tempban
            self.error('Q3AParser.ban(): no client id, database must be down, doing tempban')
            return self.tempban(client, reason, 1440, admin, silent)

        if admin:
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin)
            fullreason = self.getMessage('banned_by', variables)
        else:
            variables = self.getMessageVariables(client=client, reason=reason)
            fullreason = self.getMessage('banned', variables)

        if client.cid is None:
            # ban by ip, this happens when we !permban @xx a player that is not connected
            self.debug('EFFECTIVE BAN : %s', self.getCommand('banByIp', ip=client.ip, reason=reason))
            self.write(self.getCommand('banByIp', ip=client.ip, reason=reason))
        else:
            # ban by cid
            self.debug('EFFECTIVE BAN : %s', self.getCommand('ban', cid=client.cid, reason=reason))

            if self._permban_with_frozensand:
                cmd = self.getCommand('auth-permban', cid=client.cid)
                self.info('Sending ban to Frozen Sand : %s' % cmd)
                rv = self.write(cmd)
                if rv:
                    if rv == "Auth services disabled" or rv.startswith("auth: not banlist available."):
                        self.warning(rv)
                    elif rv.startswith("auth: sending ban"):
                        self.info(rv)
                        time.sleep(.250)
                    else:
                        self.warning(rv)
                        time.sleep(.250)

            if client.connected:
                cmd = self.getCommand('ban', cid=client.cid, reason=reason)
                self.info('Sending ban to server : %s' % cmd)
                rv = self.write(cmd)
                if rv:
                    self.info(rv)

        if not silent and fullreason != '':
            self.say(fullreason)

        if admin:
            admin.message('^7Banned^7: ^1%s^7 (^2@%s^7)' % (client.exactName, client.id))
            admin.message('^7His last ip (^1%s^7) has been added to banlist' % client.ip)

        self.queueEvent(self.getEvent('EVT_CLIENT_BAN', data={'reason': reason, 'admin': admin}, client=client))
        client.disconnect()

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """
        Tempban a client.
        :param client: The client to tempban
        :param reason: The reason for this tempban
        :param duration: The duration of the tempban
        :param admin: The admin who performed the tempban
        :param silent: Whether to announce this tempban
        """
        self.debug("b4.parsers.Iourt43Parser.tempban\n")
        duration = b4.b4_functions.time2minutes(duration)
        if isinstance(client, b4.b4_clients.Client) and not client.guid:
            # client has no guid, kick instead
            return self.kick(client, reason, admin, silent)
        elif isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(self.getCommand('tempban', cid=client, reason=reason))
            return
        elif admin:
            banduration = b4.b4_functions.minutesStr(duration)
            variables = self.getMessageVariables(client=client, reason=reason, admin=admin, banduration=banduration)
            fullreason = self.getMessage('temp_banned_by', variables)
        else:
            banduration = b4.b4_functions.minutesStr(duration)
            variables = self.getMessageVariables(client=client, reason=reason, banduration=banduration)
            fullreason = self.getMessage('temp_banned', variables)

        if self._tempban_with_frozensand:
            minutes = duration
            days = hours = 0
            while minutes >= 60:
                hours += 1
                minutes -= 60
            while hours >= 24:
                days += 1
                hours -= 24

            cmd = self.getCommand('auth-tempban', cid=client.cid, days=days, hours=hours, minutes=int(minutes))
            self.info('Sending ban to Frozen Sand : %s' % cmd)
            rv = self.write(cmd)
            if rv:
                if rv == "Auth services disabled" or rv.startswith("auth: not banlist available."):
                    self.warning(rv)
                elif rv.startswith("auth: sending ban"):
                    self.info(rv)
                    time.sleep(.250)
                else:
                    self.warning(rv)
                    time.sleep(.250)

        if client.connected:
            cmd = self.getCommand('tempban', cid=client.cid, reason=reason)
            self.info('Sending ban to server : %s' % cmd)
            rv = self.write(cmd)
            if rv:
                self.info(rv)

        if not silent and fullreason != '':
            self.say(fullreason)

        self.queueEvent(self.getEvent('EVT_CLIENT_BAN_TEMP', data={'reason': reason,
                                                                   'duration': duration,
                                                                   'admin': admin}, client=client))
        client.disconnect()

    def inflictCustomPenalty(self, penalty_type, client, reason=None, duration=None, admin=None, data=None):
        """
        Urban Terror specific punishments.
        """
        self.debug("b4.parsers.Iourt43Parser.inflictCustomPenalty\n")
        if penalty_type == 'slap' and client:
            cmd = self.getCommand('slap', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif penalty_type == 'nuke' and client:
            cmd = self.getCommand('nuke', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif penalty_type == 'mute' and client:
            if duration is None:
                seconds = 60
            else:
                seconds = round(float(b4.b4_functions.time2minutes(duration) * 60), 0)

            # make sure to unmute first
            cmd = self.getCommand('mute', cid=client.cid, seconds=0)
            self.write(cmd)
            # then mute
            cmd = self.getCommand('mute', cid=client.cid, seconds=seconds)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

        elif penalty_type == 'kill' and client:
            cmd = self.getCommand('kill', cid=client.cid)
            self.write(cmd)
            if reason:
                client.message("%s" % reason)
            return True

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################
    
    def getTeam(self, team):
        """
        Return a B3 team given the team value.
        :param team: The team value
        """
        self.debug("b4.parsers.Iourt43Parser.getTeam\n")

        match = str(team).lower()
        if match in {'red', 'r', '1'}:
            return b4.b4_clients.TEAM_RED
        if match in {'blue', 'b', '2'}:
            return b4.b4_clients.TEAM_BLUE
        if match in {'spectator', 's', '3'}:
            return b4.b4_clients.TEAM_SPEC

        return b4.b4_clients.TEAM_UNKNOWN

    def queryClientFrozenSandAccount(self, cid):
        """
        : auth-whois 0
        auth: id: 0 - name: ^7laCourge - login:  - notoriety: 0 - level: 0  - ^7no account

        : auth-whois 0
        auth: id: 0 - name: ^7laCourge - login: courgette - notoriety: serious - level: -1

        : auth-whois 3
        Client 3 is not active.
        """
        self.debug("b4.parsers.Iourt43Parser.queryClientFrozenSandAccount\n")
        data = self.write('auth-whois %s' % cid)
        if not data:
            return dict()

        if data == "Client %s is not active." % cid:
            return dict()

        m = self._re_authwhois.match(data)
        if m:
            return m.groupdict()
        else:
            return {}

    def queryAllFrozenSandAccount(self, max_retries=None):
        """
        Query the accounts of all the online clients.
        """
        self.debug("b4.parsers.Iourt43Parser.queryAllFrozenSandAccount\n")
        data = self.write('auth-whois all', maxRetries=max_retries)
        if not data:
            return {}
        players = {}
        for m in re.finditer(self._re_authwhois, data):
            players[m.group('cid')] = m.groupdict()
        return players

    def is_frozensand_auth_available(self):
        """
        Check whether the auth system is available.
        """
        self.debug("b4.parsers.Iourt43Parser.is_frozensand_auth_available\n")
        cvar = self.getCvar('auth')
        if cvar:
            auth = cvar.getInt()
            return auth != 0
        else:
            return False
    
    def defineGameType(self, gametype_int):
        """
        Translate the gametype to a readable format (also for teamkill plugin!)
        """
        self.debug("b4.parsers.Iourt43Parser.defineGameType\n")
        gametype = str(gametype_int)

        if gametype_int == '0':
            gametype = 'ffa'
        elif gametype_int == '1':  # Last Man Standing
            gametype = 'lms'
        elif gametype_int == '2':  # Quake 3 Arena single player
            gametype = 'dm'
        elif gametype_int == '3':
            gametype = 'tdm'
        elif gametype_int == '4':
            gametype = 'ts'
        elif gametype_int == '5':
            gametype = 'ftl'
        elif gametype_int == '6':
            gametype = 'cah'
        elif gametype_int == '7':
            gametype = 'ctf'
        elif gametype_int == '8':
            gametype = 'bm'
        elif gametype_int == '9':
            gametype = 'jump'
        elif gametype_int == '10':
            gametype = 'freeze'
        elif gametype_int == '11':
            gametype = 'gungame'
        return gametype

    def _getDamagePoints(self, weapon, hitloc):
        """
        Provide the estimated number of damage points inflicted by
        a hit of a given weapon to a given body location.
        """
        self.debug("b4.parsers.Iourt43Parser._getDamagePoints\n")
        try:
            points = self.damage[weapon][int(hitloc) - 1]
            self.debug("_getDamagePoints(%s, %s) -> %d" % (weapon, hitloc, points))
            return points
        except (KeyError, IndexError) as err:
            self.warning("_getDamagePoints(%s, %s) cannot find value : %s" % (weapon, hitloc, err))
            return 15

    def patch_spamcontrolPlugin(self):
        """
        This method alters the Spamcontrol plugin after it started to make it aware of RADIO spam.
        """
        self.debug("b4.parsers.Iourt43Parser.patch_spamcontrolPlugin\n")
        self.info("Patching spamcontrol plugin...")

        def onRadio(this, event):
            self.debug("b4.parsers.Iourt43Parser.onRadio\n")
            new_event = b4.b4_events.Event(type=event.type, client=event.client, target=event.target, data=repr(event.data))
            this.onChat(new_event)

        #self.spamcontrolPlugin.onRadio = instancemethod(onRadio, self.spamcontrolPlugin, SpamcontrolPlugin)
        self.spamcontrolPlugin.onRadio = instancemethod(onRadio, SpamcontrolPlugin)
        self.spamcontrolPlugin.registerEvent('EVT_CLIENT_RADIO', self.spamcontrolPlugin.onRadio)

    @staticmethod
    def patch_Clients():

        def newClient(self, cid, **kwargs):
            """
            Patch the newClient method in the Clients class to handle UrT 4.2 specific client instances.
            """
            self.debug("b4.parsers.Iourt43Parser.newClient\n")
            client = Iourt43Client(console=self.console, cid=cid, timeAdd=self.console.time(), **kwargs)
            self[client.cid] = client
            self.resetIndex()

            self.console.debug('Urt43 Client Connected: [%s] %s - %s (%s)',  self[client.cid].cid, self[client.cid].name,
                                                                             self[client.cid].guid, self[client.cid].data)

            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_CONNECT', data=client, client=client))

            if client.guid:
                client.auth()
            elif not client.authed:
                self.authorizeClients()
            return client

        def newGetByMagic(self, handle):
            """
            Patch the getByMagic method in the Clients class so it's possible to lookup players using the auth login.
            """
            self.debug("b4.parsers.Iourt43Parser.newGetByMagic\n")
            handle = handle.strip()
            if re.match(r'^[0-9]+$', handle):
                client = self.getByCID(handle)
                if client:
                    return [client]
                return []
            elif re.match(r'^@([0-9]+)$', handle):
                return self.getByDB(handle)
            elif handle[:1] == '\\':
                c = self.getByName(handle[1:])
                if c and not c.hide:
                    return [c]
                return []
            else:
                clients = []
                needle = re.sub(r'\s', '', handle.lower())
                for cid, c in self.items():
                    cleanname = re.sub(r'\s', '', c.name.lower())
                    if not c.hide and (needle in cleanname or needle in c.pbid) and not c in clients:
                        clients.append(c)
                return clients

        b4.b4_clients.Client.newClient = newClient
        b4.b4_clients.Client.getByMagic = newGetByMagic