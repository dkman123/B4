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
import b4.b4_functions
import re
import sys
import threading
import time
import traceback


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


class ClientVar(object):

    value = None

    def __init__(self, value):
        """
        Object constructor.
        :param value: The variable value.
        """
        self.value = value

    def toInt(self):
        """
        Return the current variable as an integer.
        """
        if self.value is None:
            return 0
        return int(self.value)

    def toString(self):
        """
        Return the current variable as a string.
        """
        if self.value is None:
            return ''
        return str(self.value)

    def items(self):
        """
        Return the elements contained in the variable.
        """
        if self.value is None:
            return ()
        return self.value.items()

    def length(self):
        """
        Return the length of the variable.
        """
        if self.value is None:
            return 0
        return len(self.value)


class Client(object):

    ## PVT
    _autoLogin = 1
    _data = None
    _exactName = ''
    _greeting = ''
    _groupBits = 0
    _groups = None
    _guid = ''
    _id = 0
    _ip = ''
    _lastVisit = None
    _login = ''
    _maskGroup = None
    _maskLevel = 0
    _maxGroup = None
    _maxLevel = None
    _name = ''
    _password = ''
    _pluginData = None
    _pbid = ''
    _team = TEAM_UNKNOWN
    _tempLevel = None
    _timeAdd = 0
    _timeEdit = 0
    _app = ''
    _isocode = ''
    _permmute = 0

    # PUB
    authed = False
    authorizing = False
    bot = False
    cid = None
    connected = True
    console = None
    hide = False
    state = None

    def __init__(self, **kwargs):
        """
        Object constructor.
        :param kwargs: A dict containing client object attributes.
        """
        self._pluginData = {}
        self.state = STATE_UNKNOWN
        self._data = {}        

        # make sure to set console before anything else
        if 'console' in kwargs:
            self.console = kwargs['console']
            
        for k, v in kwargs.items():
            setattr(self, k, v)

    ####################################################################################################################
    #                                                                                                                  #
    #   PLUGIN VARIABLES                                                                                               #
    #                                                                                                                  #
    ####################################################################################################################

    def isvar(self, plugin, key):
        """
        Check whether the given plugin stored a variable under the given key.
        :param plugin: The plugin that stored the value.
        :param key: The key associated to the value.
        :return True if there is a value, False otherwise
        """
        #self.console.verbose3("b4_clients.Client.isvar")
        try:
            d = self._pluginData[id(plugin)][key]
            return True
        except Exception:
            return False

    def setvar(self, plugin, key, value=None):
        """
        Store a new variable in this client object indexing it under plugin/key combination.
        :param plugin: The plugin that is saving the value.
        :param key: The key to associate to this variable.
        :param value: The value of this variable.
        :return The stored variable.
        """
        #self.console.verbose3("b4_clients.Client.setvar")
        try:
            self._pluginData[id(plugin)]
        except Exception:
            self._pluginData[id(plugin)] = {}

        try:
            self._pluginData[id(plugin)][key].value = value
        except Exception:
            self._pluginData[id(plugin)][key] = ClientVar(value)

        return self._pluginData[id(plugin)][key]

    def var(self, plugin, key, default=None):
        """
        Return a variable previously stored by a plugin.
        :param plugin: The plugin that stored the variable.
        :param key: The key of the variable.
        :param default: A default value to be returned if the variable is not stored.
        :return The variable saved under the plugin/key combination or default if it doesn't exists.
        """
        #self.console.verbose3("b4_clients.Client.var")
        try:
            return self._pluginData[id(plugin)][key]
        except Exception:
            return self.setvar(plugin, key, default)

    def varlist(self, plugin, key, default=None):
        #self.console.verbose3("b4_clients.Client.varList")
        if not default:
            default = []
        return self.var(plugin, key, default)

    def vardict(self, plugin, key, default=None):
        #self.console.verbose3("b4_clients.Client.vardict")
        if not default:
            default = {}
        return self.var(plugin, key, default)

    def delvar(self, plugin, key):
        """
        Delete a variable stored by a plugin.
        :param plugin: The plugin that stored the variable.
        :param key: The key of the variable.
        """
        #self.console.verbose3("b4_clients.Client.delvar")
        try:
            del self._pluginData[id(plugin)][key]
        except Exception:
            pass

    ####################################################################################################################
    #                                                                                                                  #
    #   FIELDS IN OBJECT                                                                                               #
    #                                                                                                                  #
    ####################################################################################################################

    def _get_aliases(self):
        #self.console.verbose3("b4_clients.Client._get_aliases")
        return self.console.storage.getClientAliases(self)

    aliases = property(fget=_get_aliases)

    # -----------------------

    def _get_bans(self):
        #self.console.verbose3("b4_clients.Client._get_bans")
        return self.console.storage.getClientPenalties(self, penType=('Ban', 'TempBan'))

    bans = property(fget=_get_bans)

    # -----------------------

    def _set_data(self, data):
        #self.console.verbose3("b4_clients.Client._set_data")
        for k, v in data.items():
            self._data[k] = v

    def _get_data(self):
        #self.console.verbose3("b4_clients.Client._get_data")
        return self._data

    data = property(fget=_get_data, fset=_set_data)

    # -----------------------

    def _get_firstWarning(self):
        #self.console.verbose3("b4_clients.Client._get_firstWarning")
        if not self.id:
            return None
        return self.console.storage.getClientFirstPenalty(self, 'Warning')

    firstWarning = property(fget=_get_firstWarning)

    # -----------------------

    def _get_groups(self):
        #self.console.verbose3("b4_clients.Client._get_groups")
        if not self._groups:
            self._groups = []
            groups = self.console.storage.getGroups()
            guest_group = None
            for g in groups:
                if g.id == 0:
                    guest_group = g
                if g.id & self._groupBits:
                    self._groups.append(g)
            if not len(self._groups) and guest_group:
                self._groups.append(guest_group)
        return self._groups

    groups = property(_get_groups)

    # -----------------------

    def _get_ip_addresses(self):
        #self.console.verbose3("b4_clients.Client._get_ip_addresses")
        return self.console.storage.getClientIpAddresses(self)

    ip_addresses = property(fget=_get_ip_addresses)

    # -----------------------

    def _get_last_visit(self):
        #self.console.verbose3("b4_clients.Client._get_last_visit")
        return self._lastVisit

    def _set_last_visit(self, lastVisit):
        #self.console.verbose3("b4_clients.Client._set_last_visit")
        self._lastVisit = lastVisit

    lastVisit = property(fget=_get_last_visit, fset=_set_last_visit)

    # -----------------------

    def _get_lastBan(self):
        #self.console.verbose3("b4_clients.Client._get_lastBan")
        if not self.id:
            return None
        return self.console.storage.getClientLastPenalty(self, ('Ban', 'TempBan'))

    lastBan = property(fget=_get_lastBan)

    # -----------------------

    def _get_lastWarning(self):
        #self.console.verbose3("b4_clients.Client._get_lastWarning")
        if not self.id:
            return None
        return self.console.storage.getClientLastPenalty(self, 'Warning')

    lastWarning = property(fget=_get_lastWarning)

    # -----------------------

    def _get_maxLevel(self) -> int:
        #self.console.verbose3("b4_clients.Client._get_maxLevel")
        if self._maxLevel is None:
            if self.groups and len(self.groups):
                m = -1
                for g in self.groups:
                    if g.level > m:
                        m = g.level
                        self._maxGroup = g

                self._maxLevel = m
            elif self._tempLevel:
                self._maxGroup = Group(id=-1, name='Unspecified', level=self._tempLevel)
                return self._tempLevel
            else:
                return 0

        return self._maxLevel

    maxLevel = property(fget=_get_maxLevel)

    # -----------------------

    def _get_maxGroup(self) -> int:
        #self.console.verbose3("b4_clients.Client._get_maxGroup")
        self._get_maxLevel()
        return self._maxGroup

    maxGroup = property(fget=_get_maxGroup)

    # -----------------------

    def _get_numBans(self) -> int:
        #self.console.verbose3("b4_clients.Client._get_numBans")
        if not self.id:
            return 0
        return self.console.storage.numPenalties(self, ('Ban', 'TempBan'))

    numBans = property(fget=_get_numBans)

    # -----------------------

    def _get_numWarnings(self) -> int:
        #self.console.verbose3("b4_clients.Client._get_numWarnings")
        if not self.id:
            return 0
        return self.console.storage.numPenalties(self, 'Warning')

    numWarnings = property(fget=_get_numWarnings)

    # -----------------------

    def _get_team(self) -> int:
        #self.console.verbose3("b4_clients.Client._get_team")
        return self._team

    def _set_team(self, team):
        #self.console.verbose3("b4_clients.Client._set_team")
        if self._team != team:
            previous_team = self.team
            self._team = team
            if self.console:
                self.console.queueEvent(self.console.getEvent('EVT_CLIENT_TEAM_CHANGE', self.team, self))
                self.console.queueEvent(self.console.getEvent('EVT_CLIENT_TEAM_CHANGE2', {'previous': previous_team,
                                                                                          'new': self.team}, self))

    team = property(fget=_get_team, fset=_set_team)

    # -----------------------

    def getWarnings(self):
        #self.console.verbose3("b4_clients.Client.getWarnings")
        return self.console.storage.getClientPenalties(self, penType='Warning')

    warnings = property(fget=getWarnings)

    # -----------------------

    def getattr(self, name, default=None):
        #self.console.verbose3("b4_clients.Client.getattr")
        return getattr(self, name, default)

    ####################################################################################################################
    #                                                                                                                  #
    #   FIELDS IN STORAGE                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def _get_auto_login(self):
        #self.console.verbose3("b4_clients.Client._get_auto_login")
        return self._autoLogin

    def _set_auto_login(self, autoLogin):
        #self.console.verbose3("b4_clients.Client._set_auto_login")
        self._autoLogin = autoLogin

    autoLogin = property(fget=_get_auto_login, fset=_set_auto_login)

    # -----------------------

    _connections = 0

    def _get_connections(self):
        #self.console.verbose3("b4_clients.Client._get_connections")
        return self._connections

    def _set_connections(self, v):
        #self.console.verbose3("b4_clients.Client._set_connections")
        self._connections = int(v)

    connections = property(fget=_get_connections, fset=_set_connections)

    # -----------------------

    def _get_greeting(self):
        #self.console.verbose3("b4_clients.Client._get_greeting")
        return self._greeting

    def _set_greeting(self, greeting):
        #self.console.verbose3("b4_clients.Client._set_greeting")
        self._greeting = greeting

    greeting = property(fget=_get_greeting, fset=_set_greeting)

    # -----------------------

    def _get_groupBits(self):
        #self.console.verbose3("b4_clients.Client._get_groupBits")
        return self._groupBits

    def _set_groupBits(self, bits):
        #self.console.verbose3("b4_clients.Client._set_groupBits")
        self._groupBits = int(bits)
        self.refreshLevel()

    groupBits = property(fget=_get_groupBits, fset=_set_groupBits)

    def addGroup(self, group):
        #self.console.verbose3("b4_clients.Client.addGroup")
        self.groupBits = self.groupBits | group.id

    def setGroup(self, group):
        #self.console.verbose3("b4_clients.Client.setGroup")
        self.groupBits = group.id

    def remGroup(self, group):
        #self.console.verbose3("b4_clients.Client.remGroup")
        self.groupBits = self.groupBits ^ group.id

    def inGroup(self, group):
        #self.console.verbose3("b4_clients.Client.inGroup")
        return self.groupBits & group.id

    # -----------------------

    def _get_guid(self):
        #self.console.verbose3("b4_clients.Client._get_guid")
        return self._guid

    def _set_guid(self, guid):
        #self.console.verbose3("b4_clients.Client._set_guid")
        if guid and len(guid) > 2:
            if self._guid and self._guid != guid:
                self.console.error('Client has guid but its not the same %s <> %s', self._guid, guid)
                self.authed = False
            elif not self._guid:
                self._guid = guid
        else:
            self.authed = False
            self._guid = ''

    guid = property(fget=_get_guid, fset=_set_guid)

    # -----------------------

    def _get_id(self):
        #self.console.verbose3("b4_clients.Client._get_id")
        return self._id

    def _set_id(self, v):
        #self.console.verbose3("b4_clients.Client._set_id")
        if not v:
            self._id = 0
        else:
            self._id = int(v)

    id = property(fget=_get_id, fset=_set_id)

    # -----------------------

    def _get_ip(self):
        #self.console.verbose3("b4_clients.Client._get_ip")
        return self._ip

    def _set_ip(self, ip):
        #self.console.verbose3("b4_clients.Client._set_ip")
        if ':' in ip:
            ip = ip[0:ip.find(':')]
        if self._ip != ip:
            self.makeIpAlias(self._ip)
        self._ip = ip

    ip = property(fget=_get_ip, fset=_set_ip)

    # -----------------------

    def _get_login(self):
        #self.console.verbose3("b4_clients.Client._get_login")
        return self._login

    def _set_login(self, login):
        #self.console.verbose3("b4_clients.Client._set_login")
        self._login = login

    login = property(fget=_get_login, fset=_set_login)

    # -----------------------

    def _get_maskGroup(self):
        #self.console.verbose3("b4_clients.Client._get_maskGroup")
        if not self.maskLevel:
            return None
        elif not self._maskGroup:
            try:
                group = self.console.storage.getGroup(Group(level=self.maskLevel))
            except Exception as err:
                self.console.error("Could not find group with level %r" % self.maskLevel, exc_info=err)
                self.maskLevel = 0
                return None
            else:
                self._maskGroup = group
        return self._maskGroup

    def _set_maskGroup(self, g):
        #self.console.verbose3("b4_clients.Client._set_maskGroup")
        self.maskLevel = g.level
        self._maskGroup = None

    maskGroup = property(fget=_get_maskGroup, fset=_set_maskGroup)

    # -----------------------

    def _get_maskedGroup(self):
        #self.console.verbose3("b4_clients.Client._get_maskedGroup")
        group = self.maskGroup
        return group if group else self.maxGroup

    maskedGroup = property(fget=_get_maskedGroup)

    # -----------------------

    def _get_maskLevel(self):
        #self.console.verbose3("b4_clients.Client._get_maskLevel")
        return self._maskLevel

    def _set_maskLevel(self, v):
        #self.console.verbose3("b4_clients.Client._set_maskLevel")
        self._maskLevel = int(v)
        self._maskGroup = None

    maskLevel = property(fget=_get_maskLevel, fset=_set_maskLevel)

    # -----------------------

    def _get_maskedLevel(self):
        #self.console.verbose3("b4_clients.Client._get_maskedLevel")
        group = self.maskedGroup
        if group:
            return group.level
        else:
            return 0

    maskedLevel = property(fget=_get_maskedLevel)

    # -----------------------

    def _get_name(self):
        #self.console.verbose3("b4_clients.Client._get_name")
        return self._name

    def _set_name(self, name):
        #self.console.verbose3("b4_clients.Client._set_name")
        if self.console:
            newName = self.console.stripColors(name)
        else:
            newName = name.strip()

        if self._name == newName:
            if self.console:
                self.console.verbose2('Aborted making alias for cid %s: name is the same' % self.cid)
            return
        if self.cid == '-1' or self.cid == 'Server':  # bfbc2 addition
            if self.console:
                self.console.verbose2('Aborted making alias for cid %s: must be B4' % self.cid)
            return

        self.makeAlias(self._name)
        self._name = newName
        self._exactName = name + '^7'

        if self.console and self.authed:
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_NAME_CHANGE', self.name, self))

    name = property(fget=_get_name, fset=_set_name)               # cleaned

    def _get_exactName(self):
        #self.console.verbose3("b4_clients.Client._get_exactName")
        return self._exactName

    exactName = property(fget=_get_exactName, fset=_set_name)     # with color codes

    # -----------------------

    def _get_password(self):
        #self.console.verbose3("b4_clients.Client._get_password")
        return self._password

    def _set_password(self, password):
        #self.console.verbose3("b4_clients.Client._set_password")
        self._password = password

    password = property(fget=_get_password, fset=_set_password)

    # -----------------------

    def _get_pbid(self):
        #self.console.verbose3("b4_clients.Client._get_pbid")
        return self._pbid

    def _set_pbid(self, pbid):
        #self.console.verbose3("b4_clients.Client._set_pbid")
        self._pbid = pbid

    pbid = property(fget=_get_pbid, fset=_set_pbid)

    # -----------------------

    def _get_timeAdd(self):
        #self.console.verbose3("b4_clients.Client._get_timeAdd")
        return self._timeAdd

    def _set_timeAdd(self, timeAdd):
        #self.console.verbose3("b4_clients.Client._set_timeAdd")
        self._timeAdd = int(timeAdd)

    timeAdd = property(fget=_get_timeAdd, fset=_set_timeAdd)

    # -----------------------

    def _get_timeEdit(self):
        #self.console.verbose3("b4_clients.Client._get_timeEdit")
        return self._timeEdit

    def _set_timeEdit(self, timeEdit):
        #self.console.verbose3("b4_clients.Client._set_timeEdit")
        self._timeEdit = int(timeEdit)

    timeEdit = property(fget=_get_timeEdit, fset=_set_timeEdit)

    # -----------------------

    def _get_app(self):
        #self.console.verbose3("b4_clients.Client._get_app")
        return self._app

    def _set_app(self, app):
        #self.console.verbose3("b4_clients.Client._set_app")
        self._app = app

    app = property(fget=_get_app, fset=_set_app)

    # -----------------------

    def _get_isocode(self):
        #self.console.verbose3("b4_clients.Client._get_isocode")
        return self._isocode

    def _set_isocode(self, isocode):
        #self.console.verbose3("b4_clients.Client._set_isocode")
        self._isocode = isocode

    isocode = property(fget=_get_isocode, fset=_set_isocode)

    # -----------------------

    def _get_permmute(self):
        #self.console.verbose3("b4_clients.Client._get_permmute")
        return self._permmute

    def _set_permmute(self, permmute):
        #self.console.verbose3("b4_clients.Client._set_permmute")
        self._permmute = int(permmute)

    permmute = property(fget=_get_permmute, fset=_set_permmute)

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def refreshLevel(self):
        """
        Refresh the client level.
        """
        #self.console.verbose3("b4_clients.Client.refreshLevel")
        self._maxLevel = None
        self._groups = None

    def disconnect(self):
        """
        Disconnect the client.
        """
        #self.console.verbose3("b4_clients.Client.disconnect")
        self.console.clients.disconnect(self)

    def kick(self, reason='', keyword=None, admin=None, silent=False, data='', *kwargs):
        """
        Kick the client.
        :param reason: The reason for this kick
        :param keyword: The keyword specified before the reason
        :param admin: The admin who performed the kick
        :param silent: Whether to announce this kick
        :param data: Extra data to add to the penalty
        """
        #self.console.verbose3("b4_clients.Client.kick")
        self.console.kick(self, reason, admin, silent)

        if self.id:
            kick = ClientKick()

            if admin:
                kick.adminId = admin.id
            else:
                kick.adminId = 0

            kick.clientId = self.id
            kick.data = data
            kick.keyword = keyword
            kick.reason = reason
            kick.timeExpire = -1
            kick.save(self.console)

    def ban(self, reason='', keyword=None, admin=None, silent=False, data='', *kwargs):
        """
        Permban the client.
        :param reason: The reason for this ban
        :param keyword: The keyword specified before the reason
        :param admin: The admin who performed the ban
        :param silent: Whether to announce this ban or not
        :param data: Extra data to add to the penalty
        """
        #self.console.verbose3("b4_clients.Client.ban")
        self.console.ban(self, reason, admin, silent)

        if self.id:
            ban = ClientBan()

            if admin:
                ban.adminId = admin.id
            else:
                ban.adminId = 0

            ban.clientId = self.id
            ban.data = data
            ban.keyword = keyword
            ban.reason = reason
            ban.timeExpire = -1
            ban.save(self.console)

    def reBan(self, ban):
        """
        Re-apply a ban penalty on this client.
        """
        #self.console.verbose3("b4_clients.Client.reBan")
        if ban.timeExpire == -1:
            self.console.ban(self, ban.reason, None, True)
        elif ban.timeExpire > self.console.time():
            self.console.tempban(self, ban.reason, int((ban.timeExpire - self.console.time()) / 60), None, True)

    def unban(self, reason='', admin=None, silent=False, *kwargs):
        """
        Unban the client.
        :param reason: The reason for the unban
        :param admin: The admin who unbanned this client
        :param silent: Whether to announce this unban
        """
        #self.console.verbose3("b4_clients.Client.unban")
        self.console.unban(self, reason, admin, silent)
        for ban in self.bans:
            ban.inactive = 1
            ban.save(self.console)

    def tempban(self, reason='', keyword=None, duration=2, admin=None, silent=False, data='', *kwargs):
        """
        Tempban this client.
        :param reason: The reason for this tempban
        :param keyword: The keyword specified before the reason
        :param duration: The duration of the tempban
        :param admin: The admin who performed the tempban
        :param silent: Whether to announce this tempban
        :param data: Extra data to add to the penalty
        """
        #self.console.verbose3("b4_clients.Client.tempban")
        duration = b4.b4_functions.time2minutes(duration)
        self.console.tempban(self, reason, duration, admin, silent)

        if self.id:
            ban = ClientTempBan()

            if admin:
                ban.adminId = admin.id
            else:
                ban.adminId = 0

            ban.clientId = self.id
            ban.data = data
            ban.duration = duration
            ban.keyword = keyword
            ban.reason = reason
            ban.timeExpire = self.console.time() + (duration * 60)
            self.console.verbose2("in tempban for CID %s reason %s" % (ban.clientId, ban.reason))

            ban.save(self.console)

    def message(self, msg, *args):
        """
        Send a private message to this client
        :param msg: the message to send
        :param args: substitution arguments (if any).
        """
        self.console.verbose3("b4_clients.Client.message")
        self.console.message(self, msg, *args)

    def warn(self, duration, warning, keyword=None, admin=None, data=''):
        """
        Warn this client.
        :param duration: The duration of this warning
        :param warning: The reason for this warning
        :param keyword: The keyword specified before the reason
        :param admin: The admin who performed the ban
        :param data: Extra data to add to the penalty
        """
        self.console.verbose3("b4_clients.Client.warn")
        if self.id:
            duration = b4.b4_functions.time2minutes(duration)
            warn = ClientWarning()

            if admin:
                warn.adminId = admin.id
            else:
                warn.adminId = 0

            warn.clientId = self.id
            warn.data = data
            warn.duration = duration
            warn.keyword = keyword
            warn.reason = warning
            warn.timeExpire = self.console.time() + (duration * 60)
            warn.save(self.console)

            if self.console:
                self.console.queueEvent(self.console.getEvent('EVT_CLIENT_WARN', data={
                    'reason': warn.reason,
                    'duration': warn.duration,
                    'data': warn.data,
                    'admin': admin,
                    'timeExpire': warn.timeExpire
                }, client=self))

            return warn

    def notice(self, notice, spare, admin=None):
        """
        Add a notice to this client.
        :param notice: The notice text
        :param spare: Wtf is this one?!?!?
        :param admin: The admin who added the notice
        """
        #self.console.verbose3("b4_clients.Client.notice")
        if self.id:
            notice_object = ClientNotice()

            if admin:
                notice_object.adminId = admin.id
            else:
                notice_object.adminId = 0

            notice_object.clientId = self.id
            notice_object.reason = notice
            notice_object.timeAdd = self.console.time()
            notice_object.save(self.console)

            if self.console:
                self.console.queueEvent(self.console.getEvent('EVT_CLIENT_NOTICE', data={
                    'notice': notice,
                    'admin': admin,
                    'timeAdd': notice_object.timeAdd
                }, client=self))
            
            return notice_object

    def makeAlias(self, name):
        """
        Create a new alias for this client.
        :param name: The alias string
        """
        #self.console.verbose3("b4_clients.Client.makeAlias")
        if not self.id or not name:
            return

        try:
            alias = self.console.storage.getClientAlias(Alias(clientId=self.id,alias=name))
        except KeyError:
            alias = None

        if alias:
            if alias.numUsed > 0:
                alias.numUsed += 1
            else:
                alias.numUsed = 1
        else:
            alias = Alias(clientId=self.id, alias=name)

        alias.save(self.console)
        self.console.bot('Created new alias for client @%s: %s', str(self.id), alias.alias)

    def makeIpAlias(self, ip):
        """
        Create a new ip alias for this client.
        :param ip: The ip string
        """
        #self.console.verbose3("b4_clients.Client.makeIpAlias")
        if not self.id or not ip:
            return

        try:
            alias = self.console.storage.getClientIpAddress(IpAlias(clientId=self.id, ip=ip))
        except KeyError:
            alias = None

        if alias:
            if alias.numUsed > 0:
                alias.numUsed += 1
            else:
                alias.numUsed = 1
        else:
            alias = IpAlias(clientId=self.id, ip=ip)

        alias.save(self.console)
        self.console.bot('created new IP alias for client @%s: %s', str(self.id), alias.ip)

    def save(self, console=None):
        """
        Save the current client in the storage.
        """
        #self.console.verbose3("b4_clients.Client.save")
        self.timeEdit = time.time()
        if self.guid is None or str(self.guid) == '0':
            # can't save a client without a guid
            return False
        else:
            # fix missing pbid. Workaround a bug in the database layer that would insert the string "None"
            # in db if pbid is None :/ The empty string being the default value for that db column!! Ã´O
            if self.pbid is None:
                self.pbid = ''
            if console:
                self.console.queueEvent(self.console.getEvent('EVT_CLIENT_UPDATE', data=self, client=self))
            return self.console.storage.setClient(self)

    def auth(self):
        """
        Authorize this client.
        """
        #self.console.debug("b4_clients.Client.auth")
        if not self.authed and self.guid and not self.authorizing:
            self.authorizing = True

            name = self.name
            ip = self.ip
            try:
                inStorage = self.console.storage.getClient(self)
            except KeyError as msg:
                self.console.debug('Client not found %s: %s', self.guid, msg)
                inStorage = False
            except Exception as e:
                self.console.error('Auth self.console.storage.getClient(client) - %s\n%s', e,
                                   traceback.extract_tb(sys.exc_info()[2]))
                self.authorizing = False
                return False

            if inStorage:
                self.console.bot('Client found in storage %s: welcome back %s', str(self.id), self.name)
                self.lastVisit = self.timeEdit
            else:
                self.console.bot('Client not found in the storage %s: create new', str(self.guid))

            self.connections = int(self.connections) + 1
            self.name = name
            self.ip = ip
            self.save()
            self.authed = True

            self.console.debug('Client authorized: [%s] %s - %s', self.cid, self.name, self.guid)

            # check for bans
            #self.console.verbose3('clients numBans = %d' % self.numBans)
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
        return "Client<@%s:%s|%s:\"%s\":%s>" % (self.id, self.guid, self.pbid, self.name, self.cid)


class Struct(object):
    """
    Base class for Penalty/Alias/IpAlias/Group classes.
    """
    _id = 0

    def __init__(self, **kwargs):
        """
        Object constructor.
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

    def _get_id(self):
        #self.console.verbose3("b4_clients.Struct._get_id")
        return self._id

    def _set_id(self, v):
        #self.console.verbose3("b4_clients.Struct._set_id")
        if not v:
            self._id = 0
        else:
            self._id = int(v)

    id = property(fget=_get_id, fset=_set_id)


class Penalty(Struct):
    """
    Represent a penalty.
    """
    data = ''
    inactive = 0
    keyword = ''
    reason = ''
    type = ''

    _adminId = None
    _clientId = None
    _timeAdd = 0
    _timeEdit = 0
    _timeExpire = 0
    _duration = 0

    def _get_admin_id(self):
        #self.console.verbose3("b4_clients.Penalty._get_admin_id")
        return self._adminId

    def _set_admin_id(self, v):
        #self.console.verbose3("b4_clients.Penalty._set_admin_id")
        self._adminId = v

    adminId = property(fget=_get_admin_id, fset=_set_admin_id)

    def _get_client_id(self):
        #self.console.verbose3("b4_clients.Penalty._get_client_id")
        return self._clientId

    def _set_client_id(self, v):
        #self.console.verbose3("b4_clients.Penalty._set_client_id")
        self._clientId = v

    clientId = property(fget=_get_client_id, fset=_set_client_id)

    def _get_duration(self):
        #self.console.verbose3("b4_clients.Penalty._get_duration")
        return self._duration

    def _set_duration(self, v):
        #self.console.verbose3("b4_clients.Penalty._set_duration")
        self._duration = b4.b4_functions.time2minutes(v)

    duration = property(fget=_get_duration, fset=_set_duration)

    def _get_timeAdd(self):
        #self.console.verbose3("b4_clients.Penalty._get_timeAdd")
        return self._timeAdd

    def _set_timeAdd(self, v):
        #self.console.verbose3("b4_clients.Penalty._set_timeAdd")
        self._timeAdd = int(v)

    timeAdd = property(fget=_get_timeAdd, fset=_set_timeAdd)

    def _get_timeEdit(self):
        #self.console.verbose3("b4_clients.Penalty._get_timeEdit")
        return self._timeEdit

    def _set_timeEdit(self, v):
        #self.console.verbose3("b4_clients.Penalty._set_timeEdit")
        self._timeEdit = int(v)

    timeEdit = property(fget=_get_timeEdit, fset=_set_timeEdit)

    def _get_timeExpire(self):
        #self.console.verbose3("b4_clients.Penalty._get_timeExpire")
        return self._timeExpire

    def _set_timeExpire(self, v):
        #self.console.verbose3("b4_clients.Penalty._set_timeExpire")
        self._timeExpire = int(v)

    timeExpire = property(fget=_get_timeExpire, fset=_set_timeExpire)

    def save(self, console):
        """
        Save the penalty in the storage.
        :param console: The console instance
        """
        console.verbose3("b4_clients.Penalty.save")
        self.timeEdit = console.time()
        if not self.id:
            self.timeAdd = console.time()
        return console.storage.setClientPenalty(self)


class ClientWarning(Penalty):
    """
    Represent a Warning.
    """
    type = 'Warning'

    def _get_reason(self):
        #self.console.verbose3("b4_clients.ClientWarning._get_reason")
        return self.reason

    def _set_reason(self, v):
        #self.console.verbose3("b4_clients.ClientWarning._get_reason")
        self.reason = v

    warning = property(fget=_get_reason, fset=_set_reason)


class ClientNotice(Penalty):
    """
    Represent a Notice.
    """
    type = 'Notice'

    def _get_reason(self):
        #self.console.verbose3("b4_clients.ClientNotice._get_reason")
        return self.reason

    def _set_reason(self, v):
        #self.console.verbose3("b4_clients.ClientNotice._set_reason")
        self.reason = v

    notice = property(fget=_get_reason, fset=_set_reason)


class ClientBan(Penalty):
    """
    Represent a Ban.
    """
    type = 'Ban'


class ClientTempBan(Penalty):
    """
    Represent a TempBan.
    """
    type = 'TempBan'


class ClientKick(Penalty):
    """
    Represent a Kick.
    """
    type = 'Kick'


class Alias(Struct):
    """
    Represent an Alias.
    """
    _alias = ''
    _clientId = 0
    _numUsed = 1
    _timeAdd = 0
    _timeEdit = 0

    def _get_alias(self):
        #self.console.verbose3("b4_clients.Alias._get_alias")
        return self._alias

    def _set_alias(self, v):
        #self.console.verbose3("b4_clients.Alias._set_alias")
        self._alias = v

    alias = property(fget=_get_alias, fset=_set_alias)

    def _get_client_id(self):
        #self.console.verbose3("b4_clients.Alias._get_client_id")
        return self._clientId

    def _set_client_id(self, v):
        #self.console.verbose3("b4_clients.Alias._set_client_id")
        self._clientId = v

    clientId = property(fget=_get_client_id, fset=_set_client_id)

    def _get_num_used(self):
        #self.console.verbose3("b4_clients.Alias._get_num_used")
        return self._numUsed

    def _set_num_used(self, v):
        #self.console.verbose3("b4_clients.Alias._set_num_used")
        self._numUsed = v

    numUsed = property(fget=_get_num_used, fset=_set_num_used)

    def _get_time_add(self):
        #self.console.verbose3("b4_clients.Alias._get_time_add")
        return self._timeAdd

    def _set_time_add(self, v):
        #self.console.verbose3("b4_clients.Alias._set_time_add")
        self._timeAdd = int(v)

    timeAdd = property(fget=_get_time_add, fset=_set_time_add)

    def _get_time_edit(self):
        #self.console.verbose3("b4_clients.Alias._get_time_edit")
        return self._timeEdit

    def _set_time_edit(self, v):
        #self.console.verbose3("b4_clients.Alias._set_time_edit")
        self._timeEdit = int(v)

    timeEdit = property(fget=_get_time_edit, fset=_set_time_edit)

    def save(self, console):
        """
        Save the alias in the storage.
        :param console: The console instance.
        """
        #console.info("b4_clients.Alias.save")
        self.timeEdit = console.time()
        if not self.id:
            self.timeAdd = console.time()
        return console.storage.setClientAlias(self)

    def __str__(self):
        return "Alias(id=%s, alias=\"%s\", clientId=%s, numUsed=%s)" % (self.id, self.alias, self.clientId, self.numUsed)


class IpAlias(Struct):
    """
    Represent an Ip Alias.
    """
    _ip = None
    _clientId = 0
    _numUsed = 1
    _timeAdd = 0
    _timeEdit = 0

    def _get_ip(self):
        #self.console.verbose3("b4_clients.IpAlias._get_ip")
        return self._ip

    def _set_ip(self, v):
        #self.console.verbose3("b4_clients.IpAlias._set_ip")
        self._ip = v

    ip = property(fget=_get_ip, fset=_set_ip)

    def _get_client_id(self):
        #self.console.verbose3("b4_clients.IpAlias._get_client_id")
        return self._clientId

    def _set_client_id(self, v):
        #self.console.verbose3("b4_clients.IpAlias.xxxxx")
        self._clientId = v

    clientId = property(fget=_get_client_id, fset=_set_client_id)

    def _get_num_used(self):
        #self.console.verbose3("b4_clients.IpAlias._get_num_used")
        return self._numUsed

    def _set_num_used(self, v):
        #self.console.verbose3("b4_clients.IpAlias._set_num_used")
        self._numUsed = v

    numUsed = property(fget=_get_num_used, fset=_set_num_used)

    def _get_time_add(self):
        #self.console.verbose3("b4_clients.IpAlias._get_time_add")
        return self._timeAdd

    def _set_time_add(self, v):
        #self.console.verbose3("b4_clients.IpAlias._set_time_add")
        self._timeAdd = int(v)

    timeAdd = property(fget=_get_time_add, fset=_set_time_add)

    def _get_time_edit(self):
        #self.console.verbose3("b4_clients.IpAlias._get_time_edit")
        return self._timeEdit

    def _set_time_edit(self, v):
        #self.console.verbose3("b4_clients.IpAlias._set_time_edit")
        self._timeEdit = int(v)

    timeEdit = property(fget=_get_time_edit, fset=_set_time_edit)

    def save(self, console):
        """
        Save the ip alias in the storage.
        :param console: The console implementation
        """
        #console.info("b4_clients.IpAlias.save")
        self.timeEdit = console.time()
        if not self.id:
            self.timeAdd = console.time()
        return console.storage.setClientIpAddress(self)
    
    def __str__(self):
        return "IpAlias(id=%s, ip=\"%s\", clientId=%s, numUsed=%s)" % (self.id, self.ip, self.clientId, self.numUsed)


class Group(Struct):
    """
    Represent a Group.
    """
    _name = ''
    _keyword = ''
    _level = 0
    _timeAdd = 0
    _timeEdit = 0

    def _get_name(self):
        #self.console.verbose3("b4_clients.Group._get_name")
        return self._name

    def _set_name(self, v):
        #self.console.verbose3("b4_clients.Group._set_name")
        self._name = v

    name = property(fget=_get_name, fset=_set_name)

    def _get_keyword(self):
        #self.console.verbose3("b4_clients.Group._get_keyword")
        return self._keyword

    def _set_keyword(self, v):
        #self.console.verbose3("b4_clients.Group._set_keyword")
        self._keyword = v

    keyword = property(fget=_get_keyword, fset=_set_keyword)

    def _get_level(self):
        #self.console.verbose3("b4_clients.Group._get_level")
        return self._level

    def _set_level(self, v):
        #self.console.verbose3("b4_clients.Group._set_level")
        self._level = int(v)

    level = property(fget=_get_level, fset=_set_level)

    def _get_time_add(self):
        #self.console.verbose3("b4_clients.Group._get_time_add")
        return self._timeAdd

    def _set_time_add(self, v):
        #self.console.verbose3("b4_clients.Group._set_time_add")
        self._timeAdd = int(v)

    timeAdd = property(fget=_get_time_add, fset=_set_time_add)

    def _get_time_edit(self):
        #self.console.verbose3("b4_clients.Group._get_time_edit")
        return self._timeEdit

    def _set_time_edit(self, v):
        #self.console.verbose3("b4_clients.Group._set_time_edit")
        self._timeEdit = int(v)

    timeEdit = property(fget=_get_time_edit, fset=_set_time_edit)

    def save(self, console):
        """
        Save the group in the storage.
        :param console: The console implementation
        """
        #console.info("b4_clients.Group.save")
        self.timeEdit = console.time()
        if not self.id:
            self.timeAdd = console.time()
        return console.storage.setGroup(self)

    def __repr__(self):
        return "Group(%r)" % self.__dict__


class Clients(dict):

    _authorizing = False
    _exactNameIndex = None
    _guidIndex = None
    _nameIndex = None

    console = None

    def __init__(self, console):
        """
        Object constructor.
        :param console: The console implementation
        """
        super(Clients, self).__init__()
        self.console = console
        self._exactNameIndex = {}
        self._guidIndex = {}
        self._nameIndex = {}

        self.escape_table = [chr(x) for x in range(128)]
        self.escape_table[0] = u'\\0'
        self.escape_table[ord('\\')] = u'\\\\'
        self.escape_table[ord('\n')] = u'\\n'
        self.escape_table[ord('\r')] = u'\\r'
        self.escape_table[ord('\032')] = u'\\Z'
        self.escape_table[ord('"')] = u'\\"'
        self.escape_table[ord("'")] = u"\\'"

    def find(self, handle, maxres=None):
        """
        Search a client.
        :param handle: The search input
        :param maxres: A maximum amount of results
        """
        #self.console.verbose3("b4_clients.Clients.find")
        matches = self.getByMagic(handle)
        if len(matches) == 0:
            return None
        elif len(matches) > maxres:
            return matches[0:maxres]
        else:
            return matches

    def getByName(self, name):
        """
        Search a client by matching his name.
        :param name: The name to use for the search
        """
        #self.console.verbose3("b4_clients.Clients.getByName")
        name = name.lower()
        try:
            return self[self._nameIndex[name]]
        except Exception:
            for cid, c in self.items():
                if c.name and c.name.lower() == name:
                    # self.console.debug('found client by name %s = %s', name, c.name)
                    self._nameIndex[name] = c.cid
                    return c
        return None

    def getByExactName(self, name):
        """
        Search a client by matching his exact name.
        :param name: The name to use for the search
        """
        #self.console.verbose3("b4_clients.Clients.getByExactName")
        name = name.lower() + '^7'
        try:
            c = self[self._exactNameIndex[name]]
            # self.console.debug('found client by exact name in index %s = %s : %s', name, c.exactName, c.__class__.__name__)
            return c
        except Exception:
            for cid, c in self.items():
                if c.exactName and c.exactName.lower() == name:
                    #self.console.debug('Found client by exact name %s = %s', name, c.exactName)
                    self._exactNameIndex[name] = c.cid
                    return c
        return None

    def getList(self):
        """
        Return the list of line clients.
        """
        #self.console.verbose3("b4_clients.Clients.getList")
        clist = []
        for cid, c in self.items():
            # DK (hide is hiding CI connections)
            #if not c.hide:
            clist.append(c)
        return clist

    def getClientsByLevel(self, min=0, max=100, masked=False):
        """
        Return the list of clients whithin the min/max level range.
        :param min: The minimum level
        :param max: The maximum level
        :param masked: Whether to match masked levels
        """
        #self.console.verbose3("b4_clients.Clients.getClientsByLevel")
        clist = []
        minlevel, maxlevel = int(min), int(max)
        for cid, c in self.items():
            # DK (hide is hiding CI connections)
            # if c.hide:
            #     continue
            # elif
            if not masked and c.maskGroup and minlevel <= c.maskGroup.level <= maxlevel:
                clist.append(c)
            elif not masked and c.maskGroup:
                continue
            elif minlevel <= c.maxLevel <= maxlevel:
                # self.console.debug('getClientsByLevel hidden = %s', c.hide)
                clist.append(c)
        return clist

    def getClientsByName(self, name):
        """
        Return a list of clients matching the given name.
        :param name: The name to match
        """
        #self.console.verbose3("b4_clients.Clients.getClientsByName")
        clist = []
        needle = re.sub(r'\s', '', name.lower())
        for cid,c in self.items():
            cleanname = re.sub(r'\s', '', c.name.lower())
        # DK: this was making clients with 999 (aka, CI connections) untargetable by B3
        # DK (hide is hiding CI connections)
        #    if not c.hide and needle in cleanname:
            if needle in cleanname:
                clist.append(c)
        return clist

    def getClientLikeName(self, name):
        """
        Return the client who has the given name in its name (match substring).
        :param name: The name to match
        """
        #self.console.verbose3("b4_clients.Clients.getClientLikeName")
        name = name.lower()
        for cid, c in self.items():
            # DK (hide is hiding CI connections)
            # if not c.hide and string.find(c.name.lower(), name) != -1:
            if c.name.lower().find(name) != -1:
                return c
        return None

    def getClientsByState(self, state):
        """
        Return a list of clients matching the given state.
        :param state: The clients state
        """
        #self.console.verbose3("b4_clients.Clients.getClientsByState")
        clist = []
        for cid, c in self.items():
            # DK (hide is hiding CI connections)
            # if not c.hide and c.state == state:
            if c.state == state:
                clist.append(c)
        return clist

    def getByDB(self, client_id):
        """
        Return the client matching the given database id.
        """
        #self.console.verbose3("b4_clients.Clients.getByDB")
        m = re.match(r'^@([0-9]+)$', client_id)
        if m:
            try:
                sclient = self.console.storage.getClientsMatching({'id': m.group(1)})
                if not sclient:
                    return []

                collection = []
                for c in sclient:
                    connected_client = self.getByGUID(c.guid)
                    if connected_client:
                        c = connected_client
                    else:
                        c.clients = self
                        c.console = self.console
                        c.exactName = c.name
                    collection.append(c)
                    if len(collection) == 5:
                        break

                return collection
            except Exception:
                return []
        else:
            return self.lookupByName(client_id)

    def getByMagic(self, handle):
        """
        Return the client matching the given handle.
        :param handle: The handle to use for the search
        """
        #self.console.verbose3("b4_clients.Clients.getByMagic")
        handle = handle.strip()
        # if it's all numbers look by client ID
        if re.match(r'^[0-9]+$', handle):
            # seems to be a client id
            client = self.getByCID(handle)
            if client:
                return [client]
            return []
        # if it is @ followed by all numbers, look by B3 ID
        elif re.match(r'^@([0-9]+)$', handle):
            return self.getByDB(handle)
        # if it starts with backslash, look by (B3 name?)
        elif handle[:1] == '\\':
            c = self.getByName(handle[1:])
            # DK (hide is hiding CI connections)
            # if c and not c.hide:
            if c:
                return [c]
            return []
        else:
            # else, look by client name
            return self.getClientsByName(handle)

    def getByGUID(self, guid):
        """
        Return the client matching the given GUID.
        :param guid: The GUID to match
        """
        #self.console.verbose3("b4_clients.Clients.getByGUID")
        guid = guid.upper()
        try:
            return self[self._guidIndex[guid]]
        except Exception:
            for cid,c in self.items():
                if c.guid and c.guid == guid:
                    self._guidIndex[guid] = c.cid
                    return c
                elif b4.b4_functions.fuzzyGuidMatch(c.guid, guid):
                    # found by fuzzy matching: don't index
                    return c
        return None

    def getByCID(self, cid):
        """
        Return the client matching the given slot number.
        :param cid: The client slot number
        """
        #self.console.verbose3("b4_clients.Clients.getByCID")
        try:
            c = self[cid]
        except KeyError:
            return None
        except Exception as e:
            self.console.error('Unexpected error getByCID(%s) - %s', cid, e)
        else:
            # self.console.debug('found client by CID %s = %s', cid, c.name)
            if c.cid == cid:
                return c
            else: 
                return None
        return None

    def escape_string(self, value, mapping=None):
        """
        escape_string escapes *value* but not surround it with quotes.
        Value should be bytes or unicode.
        Source - https://github.com/PyMySQL/PyMySQL/blob/40f6a706144a9b65baa123e6d5d89d23558646ac/pymysql/converters.py
        """
        #self.console.verbose3("b4_clients.Clients.escape_string")
        if isinstance(value, str):
            return value.translate(self.escape_table)
        if isinstance(value, (bytes, bytearray)):
            # b designates a byte literal
            value = value.replace(b'\\', b'\\\\')
            value = value.replace(b'\0', b'\\0')
            value = value.replace(b'\n', b'\\n')
            value = value.replace(b'\r', b'\\r')
            value = value.replace(b'\032', b'\\Z')
            value = value.replace(b"'", b"\\'")
            value = value.replace(b'"', b'\\"')
        return value

    def lookupByName(self, name):
        """
        Return a lst of clients matching the given name.
        Will search both on the online clients list and in the storage.
        :param name: The client name
        """
        #self.console.verbose3("b4_clients.Clients.lookupByName")
        # first check connected users
        c = self.getClientLikeName(name)
        # DK (hide is hiding CI connections)
        # if c and not c.hide:
        if c:
            return [c]

        name = self.escape_string(name)

        sclient = self.console.storage.getClientsMatching({'%name%': name})

        if not sclient:
            return []
        else:
            clients = []
            for c in sclient:
                c.clients = self
                c.console = self.console
                c.exactName = c.name
                clients.append(c)
                if len(clients) == 5:
                    break

            return clients

    def lookupSuperAdmins(self):
        """
        Return the list of superadmins.
        Will search in the storage only.
        """
        #self.console.verbose3("b4_clients.Clients.lookupSuperAdmins")
        try:
            group = Group(keyword='superadmin')
            group = self.console.storage.getGroup(group)
        except Exception as e:
            self.console.error('Could not get superadmin group: %s', e)
            return False

        sclient = self.console.storage.getClientsMatching({'&group_bits': group.id})

        if not sclient:
            return []
        else:
            clients = []
            for c in sclient:
                c.clients = self
                c.console = self.console
                c.exactName = c.name
                clients.append(c)
 
            return clients

    def disconnect(self, client):
        """
        Disconnect a client from the game.
        :param client: The client to disconnect.
        """
        #self.console.verbose3("b4_clients.Clients.disconnect")
        client.connected = False
        if client.cid is None:
            return
        
        cid = client.cid
        if cid in self:
            self[cid] = None
            del self[cid]
            self.console.queueEvent(self.console.getEvent('EVT_CLIENT_DISCONNECT', data=cid, client=client))

        self.resetIndex()

    def resetIndex(self):
        """
        Reset the indexes.
        """
        #self.console.verbose3("b4_clients.Clients.resetIndex")
        self._nameIndex = {}
        self._guidIndex = {}
        self._exactNameIndex = {}

    def newClient(self, cid, **kwargs):
        """
        Create a new client.
        :param cid: The client slot number
        :param kwargs: The client attributes
        """
        #self.console.verbose3("b4_clients.Clients.newClient")
        client = Client(console=self.console, cid=cid, timeAdd=self.console.time(), **kwargs)
        self[client.cid] = client
        self.resetIndex()
        self.console.debug('Client connected: [%s] %s - %s (%s)', self[client.cid].cid,
                           self[client.cid].name, self[client.cid].guid, self[client.cid].data)
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_CONNECT', data=client, client=client))
    
        if client.guid and not client.bot:
            client.auth()
        elif not client.authed:
            self.authorizeClients()
        return client

    def empty(self):
        """
        Empty the clients list
        """
        #self.console.verbose3("b4_clients.Clients.empty")
        self.clear()

    def clear(self):
        """
        Empty the clients list and reset the indexes.
        """
        #self.console.verbose3("b4_clients.Clients.clear")
        self.resetIndex()
        toremove = []
        for cid, c in self.items():
            toremove.append(cid)
        for cid in toremove:
            del self[cid]
            
    def sync(self):
        """
        Synchronize the clients list.
        """
        self.console.info("clients sync; thread %r" % threading.current_thread().ident)
        #self.console.verbose3("b4_clients.Clients.sync")
        mlist = self.console.sync()
        # remove existing clients
        self.clear()
        # add list of matching clients
        for cid, c in mlist.items():
            self[cid] = c

    def authorizeClients(self):
        """
        Authorize the online clients.
        """
        #self.console.verbose3("b4_clients.Clients.authorizeClients")
        if not self._authorizing:
            # lookup is delayed to allow time for auth
            # it will also allow us to batch the lookups if several players
            # are joining at once
            # NOTE: not used in urt4.3
            pass
            #self._authorizing = True
            #t = threading.Timer(5, self._authorizeClients)
            #t.start()

    def _authorizeClients(self):
        """
        Authorize the online clients.
        Must not be called directly: always use authorize_clients().
        """
        #self.console.verbose3("b4_clients.Clients._authorizeClients")
        self.console.authorizeClients()
        self._authorizing = False
