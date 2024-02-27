# -*- coding: utf-8 -*-
#
# BadWeaponForYou for UrbanTerror plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)

#import b4
import b4.b4_clients
#import b4.b4_events
import b4.b4_plugin
#import re
#import threading

from threading import Thread

__author__  = 'PtitBigorneau www.ptitbigorneau.fr'
__version__ = '1.5.3'


class BadweaponforyouPlugin(b4.b4_plugin.Plugin):

    _adminPlugin = None

    _bwfyminlevel = 60
    _glminlevel = 20
    _lbwfyminlevel = 20
    _mlbwfyminlevel = 1
    _protectlevel = 20
    _wgminlevel = 20

    _listplayersgear = {}
    _saysgear = {
        'F':'Beretta 92G',
        'f':'Glock 18',
        'G':'Desert Eagle',
        'H':'SPAS-12',
        'I':'MP5K',
        'J':'UMP45',
        'K':'HK69',
        'L':'LR300ML',
        'M':'G36',
        'N':'PSG-1',
        'Z':'SR-8',
        'a':'AK-103',
        'c':'Negev',
        'e':'M4A1',
        'O':'HE Grenade',
        'P':'Flash Grenade',
        'Q':'HE Smoke',
        'R':'Kevlar Vest',
        'W':'Kevlar Helmet',
        'U':'Silencer',
        'V':'Laser Sight',
        'T':'MedKit',
        'S':'TacGoggles',
        'X':'Extra Anno',
        'g':'Colt1911',
        'h':'Ingram Mac11',
        'i':'FR-F1',
        'j':'Benelli M4 Super 90',
        'k':'FN Herstal P90',
        'l':'.44 Magnum',
        'A':''
    }

    _lgear = {    
        "none":["A", "None"],
        "beretta":["F", "Beretta 92G"],
        "de":["G", "Desert Eagle"],
        "glock":["f", "Glock 18"],
        "spas":["H", "SPAS-12"],
        "mp5":["I", "MP5K"],
        "ump":["J" "UMP45"],               
        "hk":["K", "HK69"],
        "lr300":["L", "LR300ML"],               
        "g36":["M", "G36"],
        "psg1":["N", "PSG-1"],
        "sr8":["Z", "SR-8"],
        "ak":["a", "AK-103"],
        "negev":["c", "Negev"],
        "m4":["e", "M4A1"],
        "he":["O", "HE Grenade"],
        "flash":["P", "Flash Grenade"],
        "smoke":["Q", "HE Smoke"],
        "kevlar":["R", "Kevlar Vest"],
        "helmet":["W", "Kevlar Helmet"],
        "silencer":["U", "Silencer"],
        "laser":["V", "Laser Sight"],
        "medkit":["T", "MedKit"],
        "tac":["S", "TacGoggles"],
        "xtra":["X", "Extra Ammo"],
        "colt":["g", "Colt1911"],
        "mac11":["h", "Ingram Mac11"],
        "frf1":["i", "FR-F1"],
        "benelli":["j", "Benelli M4 Super 90"],
        "p90":["k", "FN Herstal P90"],
        "magnum":["l", ".44 Magnum"]
    }
    
    _gears = ('beretta', 'de', 'glock', 'colt', 'mac11',
              'spas', 'mp5', 'ump', 'hk', 'lr300',
              'g36', 'psg1', 'sr8', 'ak', 'negev',
              'm4', 'he', 'smoke', 'kevlar', 'helmet',
              'silencer', 'laser', 'medkit', 'tac', 'xtra'
              'frf1', 'benelli', 'p90', 'magnum')

    def onStartup(self):

        self._adminPlugin = self.console.getPlugin('admin')
        
        if not self._adminPlugin:

            self.error('Could not find admin plugin')
            return False
        
        self._adminPlugin.registerCommand(self, 'bwfy', self._bwfyminlevel, self.cmd_bwfy)
        self._adminPlugin.registerCommand(self, 'listgear', self._glminlevel, self.cmd_listgear)
        self._adminPlugin.registerCommand(self, 'listbwfy', self._lbwfyminlevel, self.cmd_listbwfy)
        self._adminPlugin.registerCommand(self, 'mylistbwfy', self._mlbwfyminlevel, self.cmd_mylistbwfy)
        self._adminPlugin.registerCommand(self, 'whogear', self._wgminlevel, self.cmd_whogear)

        self.registerEvent(self.console.getEventID('EVT_CLIENT_GEAR_CHANGE'))
        self.registerEvent(self.console.getEventID('EVT_CLIENT_NAME_CHANGE'))
        self.registerEvent(self.console.getEventID('EVT_CLIENT_TEAM_CHANGE'))
        self.registerEvent(self.console.getEventID('EVT_GAME_ROUND_START'))
        self.registerEvent(self.console.getEventID('EVT_GAME_MAP_CHANGE'))

        self.gamename = self.console.game.gameName

        if self.gamename == 'iourt41':

            self.gmessage = 'gear[beretta|de|spas|mp5|ump|hk|lr300|g36|psg1|sr8|ak|negev|he|smoke|kevlar|helmet|silencer|laser|medkit|tag|xtra]'

        if self.gamename == 'iourt42':

            self.gmessage = 'gear[beretta|de|glock|colt|spas|mp5|ump|mac11|hk|lr300|g36|psg1|sr8|ak|negev|he|smoke|kevlar|helmet|silencer|laser|medkit|tag|xtra]'

        if self.gamename == 'iourt43':

            self.gmessage = 'gear[beretta|de|glock|colt|spas|mp5|ump|mac11|hk|lr300|g36|psg1|sr8|ak|negev|he|smoke|kevlar|helmet|silencer|laser|medkit|tag|xtra|frf1|benelli|p90|magnum]'

    def onLoadConfig(self):

        try:
            self._bwfyminlevel = self.config.getint('settings', 'bwfyminlevel')
        except Exception as err:
            self.warning("bwfyminlevel using default value. %s" % (err))

        try:
            self._glminlevel = self.config.getint('settings', 'glminlevel')
        except Exception as err: 
            self.warning("glminlevel using default value. %s" % (err))

        try:
            self._lbwfyminlevel = self.config.getint('settings', 'lbwfyminlevel')
        except Exception as err:
            self.warning("lbwfyminlevel using default value. %s" % (err))

        try:
            self._mlbwfyminlevel = self.config.getint('settings', 'mlbwfyminlevel')
        except Exception as err:
            self.warning("mlbwfyminlevel using default value. %s" % (err))
        try:
            self._protectlevel = self.config.getint('settings', 'protectlevel')
        except Exception as err:
            self.warning("protectlevel using default value. %s" % (err))

        try:
            self._wgminlevel = self.config.getint('settings', 'wgminlevel')        
        except Exception as err:
            self.warning("wgminlevel using default value. %s" % (err))

    def onEvent(self,  event):       
        
        if event.type == self.console.getEventID('EVT_GAME_MAP_CHANGE'):
            
            self._listplayersgear = {}
        
        if (event.type == self.console.getEventID('EVT_CLIENT_TEAM_CHANGE')) \
                or (event.type == self.console.getEventID('EVT_CLIENT_GEAR_CHANGE')) \
                or (event.type == self.console.getEventID('EVT_CLIENT_NAME_CHANGE')):
                
            client = event.client
            fclient = client.id
            test = 0
            listgears = None
                
            if fclient in self._listplayersgear:
                listbabclientgears = self._listplayersgear[fclient]
    
                for babclientgear in listbabclientgears:
                    self.clientgearexists(client)

                    if babclientgear in client.gear:

                        test = test + 1

                        if test == 1:
                            listgears = self._saysgear[babclientgear]
                        else:
                            listgears = listgears + ", " + self._saysgear[babclientgear]
                            
            if test != 0:                                            
                if client.team in (2, 3):
                    # force to spec
                    self.console.write('forceteam %s %s' % (client.cid, 's'))
                    # pm the player
                    client.message('^3Weapon /gear prohibited for %s ^3: ^7-%s-' % (client.exactName, listgears))
            
    def cmd_bwfy(self, data, client, cmd=None):
        """\
        <playername> <on or off> <gear> - prohibits or not a player from using an equipment
        """
        
        if data:
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
            client.message('!bwfy <playername> <on or off> <gear>')
            return
        
        sclient = self._adminPlugin.findClientPrompt(input[0], client)
        
        if not sclient:
            return False
        
        if sclient.maxLevel >= self._protectlevel:
            client.message('%s ^3is immune!' % (sclient.exactName))
            return False
        
        if not input[1]:
            client.message('!bwfy <playername> <on or off> <gear> (missing on|off or gear specification)')
            return False
        nespace = input[1].count(' ')
        
        if nespace == 0:
            client.message('!bwfy <playername> <on or off> <gear> (missing on|off or gear specification)')
            return False        
        
        tdata = input[1].split(' ')
        onoff = tdata[0]
        sgear = tdata[1]    
        sayonoff = ""

        if (onoff == "on") or (onoff == "off"):
            if onoff == 'on':
                sayonoff = '^2authorized'
            if onoff == 'off':
                sayonoff = '^1prohibited'
        else:
            client.message('!bwfy <playername> <on or off> <gear> (param on|off not matched)')
            return False
        
        if sgear not in self._gears:
            client.message('!bwfy <playername> <on or off> <gear> (gear not matched)')
            client.message('%s' % self.gmessage)
            return False
        
        if sclient:
            self._map = self.console.game.mapName
            
            rlgear = self._lgear[sgear]
            rgear = rlgear[0]
            ngear = rlgear[1]     
               
            sid = sclient.id
                            
            if onoff == "off":

                #self.debug("testing client gear")
                self.clientgearexists(sclient)

                if rgear in sclient.gear:
                    # force to spec
                    self.console.write('forceteam %s %s' % (sclient.cid, 's'))
                    # whisper the player
                    sclient.message('^3%s %s %s' % (sclient.exactName, ngear, sayonoff))

                #self.debug("not in current client gear")
                if sid in self._listplayersgear:
                    #self.info("bwfy bwfy sid in playergear")

                    if rgear in self._listplayersgear[sid]:
                        client.message('^3For %s ^7-%s-^3 is already %s' % (sclient.exactName, ngear, sayonoff))
                
                    else:
                        self.console.say('^3For %s ^7-%s-^3 : %s' % (sclient.exactName, ngear, sayonoff))
                        self._listplayersgear[sid].append("%s" % rgear)

                else:
                    #self.info("bwfy bwfy update")
                    self._listplayersgear.update({sid: [rgear]})
                                
            if onoff == "on":

                if sid in self._listplayersgear:
                
                    if rgear in self._listplayersgear[sid]:
                        self._listplayersgear[sid].remove(rgear)
                        sclient.message('^3Now %s: %s ^3again' % (ngear, sayonoff))
                        client.message('^3%s %s %s' % (sclient.exactName, ngear, sayonoff))
                        
                    else:
                        client.message('^3For %s %s ^3was not ^1prohibited' % (sclient.exactName, ngear))

                    if len(self._listplayersgear[sid]) == 0:
                        del self._listplayersgear[sid]
 
                else:
                    client.message('^3%s ^2No Weapon or Gear ^1prohibited' % (sclient.exactName))
                                    
        else:
            return False

    def cmd_listgear(self, data, client, cmd=None):
        """\
        <playername> - list of weapons and equipments of the player
        """
        
        if data:
            input = self._adminPlugin.parseUserCmd(data)
        else:
            client.message('!listgear <playername>')
            return

        sclient = self._adminPlugin.findClientPrompt(input[0], client)

        if not sclient:
            return False
               
        if (sclient):
            #self.info("bwfy listgear sclient was found")
        
            a = 0
            b = 1

            self.clientgearexists(client)
            
            for i in range(7):
                if self._saysgear[sclient.gear[a:b]] != '':
                    client.message('%s^3 weapon / gear : ^7-%s-'
                                   % (sclient.exactName, self._saysgear[sclient.gear[a:b]]))
                a = a + 1
                b = b + 1
                
        else:
            return False
    
    def cmd_listbwfy(self, data, client, cmd=None):
        """
        <playername or all> - list prohibited of weapons and equipments of player 
        """

        if data:
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
            client.message('!listbwfy <playername or all>')
            return
        
        if input[0] == "all":
            lclient = b4.b4_clients.Client()
            lclient.id = -1  # "all"
        else:
            lclient = self._adminPlugin.findClientPrompt(input[0], client)                
        
        if not lclient:
            return False
               
        if (lclient):
        
            if lclient.id == -1:  # "all"
                
                test = False
                
                for x in self._listplayersgear:
                    
                    scid = '@' + str(x)
                    sdclient = self._adminPlugin.findClientPrompt(scid, client)
                        
                    for gear in self._listplayersgear[x]:
                        client.message('^3Weapon /gear prohibited for ^2%s ^3: ^7-%s-' % (sdclient.exactName, self._saysgear[gear]))
                    
                    test = True

                if test == False:
                    client.message('^3No Players in Weapon /gear prohibited list')
                    
            else:
                # list one specific player
                try:

                    for gear in self._listplayersgear[lclient.id]:
                        client.message('^3Weapon /gear prohibited for %s ^3: ^7-%s-' % (lclient.exactName, self._saysgear[gear]))
  
                except:
                
                    client.message('%s ^3is not in Weapon /gear prohibited list' % (lclient.exactName))
        
        else:
            return False
    
    def cmd_mylistbwfy(self, data, client, cmd=None):
        """\
        list of your weapons and equipments prohibited 
        """
        
        try:

            for gear in self._listplayersgear[client.id]:
                client.message('^3Weapon /gear prohibited for %s ^3: ^7-%s-' % (client.exactName, self._saysgear[gear]))
  
        except:
                
            client.message('%s ^3is not in Weapon /gear prohibited list' % (client.exactName))

    def cmd_whogear(self, data, client, cmd=None):
        """\
        <gear> - list of players who have the weapon or gear specify
        """
        
        if data:
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
            client.message('!whogear <gear>')
            client.message('%s' % self.gmessage)
            return
        
        sgear = input[0]
        
        if sgear not in self._gears:
     
            client.message('!whogear <gear>')
            client.message('%s' % self.gmessage)
            return False
               
        if (sgear):
        
            Thread(target=self.dowhogear, args=(client, sgear, cmd)).start()
        
        else:
            return False

    def dowhogear(self, client, sgear, cmd):

        rlgear = self._lgear[sgear]
        rgear = rlgear[0]
        ngear = rlgear[1]  

        names = []
        test = 0
        steam = ""

        for c in self.console.clients.getClientsByLevel():

            sclient = self._adminPlugin.findClientPrompt(c.name, client)

            if sclient.team == 1:
                steam = "^7Spectator"
            if sclient.team == 2:
                steam = "^1Red"
            if sclient.team == 3:
                steam = "^4Blue"

            self.clientgearexists(sclient)

            if rgear in sclient.gear:
                client.message('%s ^7team : %s ^7has ^2%s' % (sclient.exactName, steam, ngear))
                test = 1

        if test == 0:
            client.message('no player with ^2%s' % (ngear))

        return

    def clientgearexists(self, client):
        # if no gear variable on client, create it
        #self.info("bwfy clientgearexists")
        try:
            if not hasattr(client, 'gear'):
                self.debug("client did not have gear")
                setattr(client, 'gear', {})
        except AttributeError:
            self.debug("client did not have gear")
            setattr(client, 'gear', {})
