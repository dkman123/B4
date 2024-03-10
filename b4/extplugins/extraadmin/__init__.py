# Copyright (C) 2011 Beber888# 
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#
# 
#
# Changelog :
# 0.1.0 : initial release
# 2.0.0 : New commands added
# 2.1.0 : Retrait des votes, ajouts dans le plugin Voting
# 2.2.0 : Modification commande !change pour ne pas changer
# quelqu'un avec un niveau > au sien
# 2.3.0 : Default value for RAZ_server = 0, adding 2 parameters
#(time afk and time kafk)
# 2.4.0 : Modify the array "Tableau" for compatibility with any
#numbers of slots

import b4
#import b4.b4_events
import b4.b4_plugin
#import b4.b4_clients
import threading
#import time

__version__ = '2.4.0'
__author__  = 'Beber888'


class Vote:
    Vote = 0


#--------------------------------------------------------------------------------------------------
class ExtraadminPlugin(b4.b4_plugin.Plugin):
    clientAFK = ''
    RAZ = 0
    clientautonuke = None
    PlayerExit = 'None'
    PlayerExitID = ''
    kickafk = 0
    forceafk = 0
    Tableau = []
    i = 0
    _min_level_change = 0
    _min_level_kafk = 0
    _min_level_afk = 0
    _time_afk = 5
    _time_kafk = 5
    _min_level_pm = 0
    _min_level_salut = 0
    showIPclient = 0
    _min_level_autonuke = 0
    RAZserveur = 0
    RAZ_map = 'ut4_abbey'
    RAZ_gametype = '4'
    RAZ_limite = 0
    _min_level_exit = 0

    # --------------CHARGEMENT DES CONFIGS--------------------------------------------
    def onLoadConfig(self):
        try:
            self._min_level_change = self.config.getint('settings', 'min_level_change')
        except:
            self._min_level_change = 0
        try:
            self._min_level_kafk = self.config.getint('settings', 'min_level_kafk')
        except:
            self._min_level_kafk = 0
        try:
            self._min_level_afk = self.config.getint('settings', 'min_level_afk')
        except:
            self._min_level_afk = 0
        try:
            self._time_afk = self.config.getint('settings', 'time_afk')
        except:
            self._time_afk = 5
        try:
            self._time_kafk = self.config.getint('settings', 'time_kafk')
        except:
            self._time_kafk = 5
        try:
            self._min_level_pm = self.config.getint('settings', 'min_level_pm')
        except:
            self._min_level_pm = 0
        try:
            self._min_level_salut = self.config.getint('settings', 'min_level_salut')
        except:
            self._min_level_salut = 0
        try:
            self.showIPclient = self.config.getint('settings', 'showIP')
        except:
            self.showIPclient = 0
        try:
            self._min_level_autonuke = self.config.getint('settings', 'min_level_autonuke')
        except:
            self._min_level_autonuke = 0
        try:
            self.RAZserveur = self.config.getint('settings', 'RAZ_server')
        except:
            self.RAZserveur = 0
        try:
            self.RAZ_map = self.config.get('settings', 'RAZ_map')
        except:
            self.RAZ_map = 'ut4_abbey'
        try:
            self.RAZ_gametype = self.config.get('settings', 'RAZ_gametype')
        except:
            self.RAZ_gametype = '4'
        try:
            self.RAZ_limite = self.config.getint('settings', 'RAZ_limit')
        except:
            self.RAZ_limite = 0
        try:
            self._min_level_exit = self.config.getint('settings', 'min_level_exit')
        except:
            self._min_level_exit = 0

        # get the plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
        else:
            self._adminPlugin.registerCommand(self, 'change', self._min_level_change, self.cmd_ChangePlayer, 'ch')
            self._adminPlugin.registerCommand(self, 'afk', self._min_level_afk, self.cmd_AFK, 'afk')
            self._adminPlugin.registerCommand(self, 'kafk', self._min_level_kafk, self.cmd_KAFK, 'kafk')
            self._adminPlugin.registerCommand(self, 'privatemessage', self._min_level_pm, self.cmd_PM, 'pm')
            self._adminPlugin.registerCommand(self, 'salut', self._min_level_salut, self.cmd_Salut, 'lu')
            self._adminPlugin.registerCommand(self, 'autonuke', self._min_level_autonuke, self.cmd_autonuke, 'an')
            self._adminPlugin.registerCommand(self, 'exit', self._min_level_exit, self.cmd_exit, 'ex')

    def onStartup(self):
        self.Nbports = self.console.getCvar('sv_maxclients').getInt()
        while self.i <= self.Nbports:
                self.Tableau.append('S' + str(self.i))
                self.i = self.i + 1
        self.registerEvent(self.console.getEventID('EVT_CLIENT_KILL'))
        self.registerEvent(self.console.getEventID('EVT_CLIENT_SAY'))
        self.registerEvent(self.console.getEventID('EVT_CLIENT_TEAM_SAY'))
        self.registerEvent(self.console.getEventID('EVT_CLIENT_PRIVATE_SAY'))
        self.registerEvent(self.console.getEventID('EVT_CLIENT_DISCONNECT'))
        self.registerEvent(self.console.getEventID('EVT_CLIENT_CONNECT'))
        self.CycliqueCheck()

    def onEvent(self, event):
        if event.type == self.console.getEventID('EVT_CLIENT_KILL'):
            self.NukeDead(event.target)
        if event.type == self.console.getEventID('EVT_CLIENT_SAY') \
                or event.type == self.console.getEventID('EVT_CLIENT_TEAM_SAY') \
                or event.type == self.console.getEventID('EVT_CLIENT_PRIVATE_SAY'):
            self.AFKSpeak(event)
        if event.type == self.console.getEventID('EVT_CLIENT_DISCONNECT'):
            self.JoueurDeco(event)
        if event.type == self.console.getEventID('EVT_CLIENT_CONNECT'):
            self.showIP(event.client)
            self.JoueurCo(event)

    # --------------COMMANDE CHANGE--------------------------------------------
    def cmd_ChangePlayer(self, data, client, cmd=None):
        """\
        [Player1] [Player2/None] Change team between (1 and 2) or (1 and you)
        """
        # this will split the player name and the message
        if data:
            inputdata = self._adminPlugin.parseUserCmd(data)
        else:
            client.message('Need Player(s) Name(s)')
            return
        # input[0] is the player id
        client1 = self._adminPlugin.findClientPrompt(inputdata[0], client)
        # DEUX JOUEURS DISTINCTS
        if inputdata[1] != None:
            client2 = self._adminPlugin.findClientPrompt(inputdata[1], client)
            if client1 and client2 and client.groupBits > client1.groupBits and client.groupBits > client2.groupBits :
                if client2.team == b4.TEAM_RED:
                    self.console.write('forceteam %s %s' % (client2.cid, 'BLUE'))
                elif client2.team == b4.TEAM_BLUE:
                    self.console.write('forceteam %s %s' % (client2.cid, 'RED'))
                if client1.team == b4.TEAM_RED:
                    self.console.write('forceteam %s %s' % (client1.cid, 'BLUE'))
                elif client1.team == b4.TEAM_BLUE:
                    self.console.write('forceteam %s %s' % (client1.cid, 'RED'))
            else:
                client.message('Cant change more level than you')

        # UN JOUEURS ET L EMETEUR DE LA PHRASE
        if inputdata[1] == None:
            if client1 != client and client.groupBits > client1.groupBits:
                if client1.team == b4.TEAM_RED:
                    self.console.write('forceteam %s %s' % (client1.cid, 'BLUE'))
                elif client1.team == b4.TEAM_BLUE:
                    self.console.write('forceteam %s %s' % (client1.cid, 'RED'))
                if client.team == b4.TEAM_RED:
                    self.console.write('forceteam %s %s' % (client.cid, 'BLUE'))
                elif client.team == b4.TEAM_BLUE:
                    self.console.write('forceteam %s %s' % (client.cid, 'RED'))
            else:
                client.message('Cant change more level than you')
            if client1 == client:
                client.message('Not you, an other')

    # --------------COMMANDE AFK-KAFK-------------------------------------------
    def cmd_AFK(self, data, client, cmd=None):
        """\
        [Player] Ask if player is AFK, if no response, he's forced spectator
        """
        # this will split the player name and the message
        if data:
            inputdata = self._adminPlugin.parseUserCmd(data)
        else:
            client.message('Need Player Name')
            return
        # input[0] is the player id
        clientafk = self._adminPlugin.findClientPrompt(inputdata[0], client)
        if clientafk:
            clientafk.message('^1Hey %s, are you AFK? Say something or Spec' % (clientafk.name))
            self.clientAFK = clientafk.cid
            self.forceafk = 1
            self.TempoAvantForce = threading.Timer(self._time_afk, self.Force)
            self.TempoAvantForce.start()
            self.verbose('Tempo Force lancee')

    def cmd_KAFK(self, data, client, cmd=None):
        """\
        [Player] Ask if player is AFK, if no response, he's kick
        """
        # this will split the player name and the message
        if data:
            inputdata = self._adminPlugin.parseUserCmd(data)
        else:
            client.message('Need Player Name')
            return
        # input[0] is the player id
        clientafk = self._adminPlugin.findClientPrompt(inputdata[0], client)
        if clientafk:
            clientafk.message('^1Hey %s, are you AFK? Say something or Kick' % (clientafk.name))
            self.clientAFK = clientafk.cid
            self.kickafk = 1
            self.TempoAvantKick = threading.Timer(self._time_kafk, self.Kick)
            self.TempoAvantKick.start()
            self.verbose('Tempo avant kick lancee')

    def AFKSpeak(self, event):
        client = event.client
        if client.cid == self.clientAFK:
            if self.forceafk == 1:
                self.forceafk = 0
                self.TempoAvantForce.cancel()
            if self.kickafk == 1:
                self.kickafk = 0
                self.TempoAvantKick.cancel()
            self.verbose('Tempo annulees')

    def Kick(self):
        self.console.write('kick %s' % (self.clientAFK))
        self.kickafk = 0

    def Force(self):
        self.console.write('forceteam %s spectator' % (self.clientAFK))
        self.forceafk = 0

    # --------------COMMANDE PM--------------------------------------------
    def cmd_PM(self, data, client, cmd=None):
        """\
        [Player] [Message] Send a message to a player
        """
        # this will split the player name and the message
        if data:
            inputdata = self._adminPlugin.parseUserCmd(data)
        else:
            client.message('Need Player Name + message')
            return
        # input[0] is the player id
        clientpm = self._adminPlugin.findClientPrompt(inputdata[0], client)
        # Envoi du message
        if len(inputdata[1]):
            Texte = inputdata[1]
            clientpm.message('%s : %s' % (client.exactName, Texte))
        if not len(inputdata[1]):
            client.message('Put text in your command')

    # --------------COMMANDE SALUT--------------------------------------------
    def cmd_Salut(self, data, client, cmd=None):
        """\
        [Player]/[BST] The server show bigtext with Hellow...
        """

        # salut BST
        if data == 'BST':
            self.console.write('bigtext "Greetz to all BST\'s from %s"' % (client.exactName))
            return
        if data == 'bst':
            self.console.write('bigtext "Greetz to all BST\'s from %s"' % (client.exactName))
            return

        # this will split the player name and the message
        elif data:
            inputdata = self._adminPlugin.parseUserCmd(data)
        else:
            client.message('Need Player Name')
            return
        # input[0] is the player id
        clientHello = self._adminPlugin.findClientPrompt(inputdata[0], client)
        # Envoi du bigtext
        if clientHello:
            self.console.write('bigtext "%s says hello to %s"' % (client.exactName, clientHello.exactName))

    # --------------AFFICHAGE IP--------------------------------------------
    def showIP(self, client):
        if self.showIPclient == 1:
            self.console.write('%s connected : %s' % (client.name, client.ip))

    #--------------RAZ MAP - GAMETYPE--------------------------------------------
    def CycliqueCheck(self):
        self.TempoCheck = threading.Timer(120, self.Get_NbPlayer1)
        self.TempoCheck.start()

    def Get_NbPlayer1(self):
        clist = self.console.clients.getClientsByLevel(0)
        self.verbose('Test Nb player1 : %s' % (len(clist)))
        if len(clist) <= self.RAZ_limite:
                self.TempoReCheck = threading.Timer(180, self.Get_NbPlayer2)
                self.TempoReCheck.start()
        else:
                self.CycliqueCheck()
        if len(clist) > self.RAZ_limite:
            self.RAZ = 0

    def Get_NbPlayer2(self):
        clist = self.console.clients.getClientsByLevel(0)
        self.verbose('Test Nb player2 : %s' % (len(clist)))
        if len(clist) <= self.RAZ_limite and self.RAZ == 0 and self.RAZserveur == 1:
            self.console.write('g_gametype %s' % self.RAZ_gametype)
            self.console.write('map %s' % self.RAZ_map)
            self.console.write('bigtext "Change for %s with gametype %s"' % (self.RAZ_map, self.RAZ_gametype))
            self.RAZ = 1
        if len(clist) > self.RAZ_limite:
            self.RAZ = 0
        self.CycliqueCheck()

    # --------------AUTONUKE--------------------------------------------
    def cmd_autonuke(self, data, client, cmd=None):
        """\
        [Player] Send nuke until player die
        """
        # this will split the player name and the message
        if data:
            inputdata = self._adminPlugin.parseUserCmd(data)
        else:
            client.message('Need Player Name')
            return
        # input[0] is the player id
        self.clientautonuke = self._adminPlugin.findClientPrompt(inputdata[0], client)
        if self.clientautonuke:
            self.CycliqueAutoNuke()
            self.clientautonuke.message('^1You have fire in the ass !! Run Forest...')

    def CycliqueAutoNuke(self):
        self.TempoNuke = threading.Timer(2, self.nuke)
        self.TempoNuke.start()

    def nuke(self):
        if self.clientautonuke != '':
            self.console.write('nuke %s' % (self.clientautonuke.cid))
            self.CycliqueAutoNuke()

    def NukeDead(self, client):
        if self.clientautonuke is not None and self.clientautonuke != '':
            if client.cid == self.clientautonuke.cid:
                self.clientautonuke = None

    # --------------EXIT--------------------------------------------
    def cmd_exit(self, data, client, cmd=None):
        """\
        Send the name of the last player disconnect
        """
        client.message('Last disconnected : %s' % (self.PlayerExit))

    def JoueurDeco(self, event):
        self.verbose('Deconnection : %s' % (event.data))
        Slot = int(event.data)
        if self.Tableau[Slot] != 'S%s' %Slot:
            self.PlayerExit = self.Tableau[Slot]
            self.verbose(self.PlayerExit)

    def JoueurCo(self, event):
        self.verbose('Connection : %s' % (event.client.cid))
        SlotClient = int(event.client.cid)
        NomClient = event.client.name
        self.Tableau[SlotClient] = NomClient
