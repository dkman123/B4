# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Plugin for following suspicious users
# Copyright (C) 2010-2011 Sergio Gabriel Teves
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# 07-31-2010 - 1.1.3 - SGT
# Add option to disable remove record when banned
# 01-25-2011 - 1.1.4 - SGT
# Add option to use twitter
# Fix minor error in followinfo
# 05-04-2011 - 1.1.5 - SGT
# Fix error in show message when no admin is set (added through web interface)
# 07-11-2011 - 1.1.6 - Freelander
# Slightly refactored the code
# Added more debug lines
# Fixed false notification messages sent to followed players
# Suspected players properly added into/removed from '_following' list when connected/disconnected.
# Banned players properly removed from plugin's database table
# Better integration with aimbotdetector plugin when used together
# Fixed some bugs
# 07-12-2011 - 1.1.7 - SGT
# Do not remove user when ban is done by B3
# 12-15-2011 - 1.1.8 - SGT
# Add support for ban breaking event
# 02-21-2012 - 1.1.9 - SGT
# Add b3 1.8 client disconnect support
# 04-22-2012 - 1.2.0 - SGT
# Clean banned players

#import b4
import threading
import b4.b4_plugin
#import b4.b4_clients
import b4.b4_cron
import time
import random

from threading import Thread

__version__ = '1.2.0'
__author__ = 'SGT'

class FollowPlugin(b4.b4_plugin.Plugin):
    _adminPlugin = None
    _following = {}

    _crontab = None

    _SELECT_QUERY = "SELECT client_id, reason, admin_id FROM following WHERE client_id = %s"
    _ADD_QUERY = "INSERT INTO following (client_id, admin_id, time_add, reason) VALUES ('%s','%s',%d,'%s')"
    _DEL_QUERY = "DELETE FROM following WHERE client_id = %s"
    _LIST_QUERY = "SELECT client_id FROM following"
    _NOTIFY_MSG = "^1WARNING: ^1%(client_name)s ^7[^2@%(client_id)s^7] ^7has been placed under watch by ^4%(admin_name)s ^7[^2@%(admin_id)s^7] ^7for: ^5%(reason)s"
    _DEFAULT_REASON = "cheating"
    _BANNED = "SELECT f.client_id FROM following f INNER JOIN penalties p ON f.client_id = p.client_id WHERE (p.type = 'Ban' or p.type = 'TempBan') and p.inactive = 0 and (p.duration > %s or p.time_expire = -1)"

    _twit_event = False
    _NOTIFY_LEVEL = 20
    _REMOVE_BAN = True
    _REMOVE_B3_BAN = False
    _MIN_PENALTY_DURATION = 525948

    def onStartup(self):
        self.registerEvent(self.console.getEvent('EVT_CLIENT_AUTH'))
        self.registerEvent(self.console.getEvent('EVT_CLIENT_DISCONNECT'))
        self.registerEvent(self.console.getEvent('EVT_CLIENT_BAN'))
        self.registerEvent(self.console.getEvent('EVT_CLIENT_BAN_TEMP'))
        self.registerEvent(self.console.getEvent('EVT_GAME_ROUND_START'))

        # try:
        #     self.registerEvent(self.console.getEvent('EVT_BAN_BREAK'))
        # except:
        #     self.warning("Unable to register event EVT_BAN_BREAK")

        self.createEvent('EVT_FOLLOW_CONNECTED', 'Suspicious User Connected.')

        # get the plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            self.disable()
            return False

        # register our commands
        self._registerCommands()

        self._twitter = self.console.getPlugin('twity')
        if not self._twitter:
            self.warning("Twitter plugin not available.")

        self._onlinePlayers = {}

        if self._crontab:
            #self.console.cron.cancel(self._crontab)
            self.console.cron - self._crontab

        rhour = random.randint(0, 23)
        rmin = random.randint(5, 59)
        self.debug("will perform cleanup at %02d:%02d every day" % (rhour, rmin))
        self._crontab = b4.b4_cron.PluginCronTab(self, self.cleanup, 0, rmin, rhour, '*', '*', '*')
        self.console.cron + self._crontab

    def onLoadConfig(self):
        """
        Initialize plugin settings
        """
        try:
            self._twit_event = self.config.getboolen('settings', 'twit_connect')
        except:
            self._twit_event = False
        try:
            self._NOTIFY_LEVEL = self.config.getint('settings', 'notify_level')
        except:
            self._NOTIFY_LEVEL = 20
        try:
            self._NOTIFY_MSG = self.config.get('settings', 'message')
        except:
            self.debug("Using default message")
        try:
            self._REMOVE_BAN = self.config.getboolean('settings', 'remove_banned')
        except:
            self._REMOVE_BAN = True
        try:
            self._REMOVE_B3_BAN = self.config.getboolean('settings', 'remove_on_b3ban')
        except:
            self._REMOVE_B3_BAN = False
        try:
            self._MIN_PENALTY_DURATION = self.config.getint('settings', 'remove_ban_minduration')
        except:
            self._MIN_PENALTY_DURATION = 525948

    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
        return None

    def _registerCommands(self):
        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp
                func = self.getCmd(cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

    def onEvent(self, event):
        if event.type == self.console.getEvent('EVT_CLIENT_AUTH'):
            if not event.client or \
                    not event.client.id or \
                    event.client.cid is None or \
                    not event.client.connected or \
                    event.client.pbid == 'WORLD' or \
                    event.client.hide:
                return
            self.process_connect_event(event.client)
        elif event.type == self.console.getEvent('EVT_CLIENT_DISCONNECT'):
            self.process_disconnect_event(event.data, event.client)
        elif event.type == self.console.getEvent('EVT_CLIENT_BAN') \
                or event.type == self.console.getEvent('EVT_CLIENT_BAN_TEMP'):
            if self._REMOVE_BAN:
                Thread(target=self.process_ban, args=(event,)).start()
        elif event.type == self.console.getEvent('EVT_GAME_ROUND_START'):
            b = threading.Timer(10, self.sync_list, (event,))
            b.start()
        else:
            try:
                if event.type == self.console.getEvent('EVT_BAN_BREAK'):
                    client = event.client
                    Thread(target=self.add_follow_client, args=(client, None, 'Ban Break')).start()
            except:
                self.verbose("EVT_BAN_BREAK not supported")

    def sync_list(self, event):
        self._following = {}
        self.debug("Syncing list")
        clients = self.console.clients.getList()
        for c in clients:
            self._add_list(c)

    def process_connect_event(self, client):
        self.debug("Client connected, processing connect event")
        self.debug("Client %s put on connected queue" % client.name)
        t = threading.Timer(30, self._client_connected, (client,))
        t.start()

    def _client_connected(self, client):
        if client.connected:
            self._onlinePlayers[client.cid] = client
            if client.maxLevel < self._NOTIFY_LEVEL:
                if self._add_list(client):
                    self.console.queueEvent(
                        self.console.getEvent('EVT_FOLLOW_CONNECTED', (client.var(self, 'follow_data').value,), client))
                    self.debug("Notifying online admins")
                    self.notify_online_admins(client)
                    self._event_notify(client)
            else:
                if len(self._following) > 0:
                    self.debug('Notifying connecting admin (admin: %s id: %s)' % (client.name, client.id))
                    self.notify_connecting_admin(client)
                else:
                    self.debug('No suspicious players online')

    def _event_notify(self, client):
        if self._twit_event and self._twitter:
            message = "WARNING: Suspicious user is playing."
            self._twitter.post_update(message)

    def notify_online_admins(self, suspect):
        clients = self.console.clients.getList()
        for player in clients:
            if player.maxLevel >= self._NOTIFY_LEVEL:
                self._show_message(player, suspect)
                time.sleep(1)

    def _show_message(self, admin, suspect):
        # prevent faulty messages to non-admin just in case
        if admin.maxLevel < self._NOTIFY_LEVEL:
            self.warning('WARNING: Oooops! Something wrong? %s shouldn\'t receive a message!' % admin.name)
            return False

        data = {'client_name': suspect.name,
                'client_id': suspect.id,
                'admin_name': suspect.var(self, 'follow_admin').value,
                'admin_id': suspect.var(self, 'follow_admin_id').value,
                'reason': suspect.var(self, 'follow_reason').value}

        admin.message(self._NOTIFY_MSG % data)

    def process_ban(self, event):
        self.info("follow process_ban; thread %r" % threading.current_thread().ident)
        client = event.client
        # check if banned client is in follow list
        self.debug('Client ban detected. Checking follow list DB table for %s' % client.name)
        cursor = self.console.storage.query(self._SELECT_QUERY % client.id)
        if cursor.rowcount > 0:
            # check if the ban is from an admin and is greater than X minutes
            penalty = client.lastBan
            if (penalty and (penalty.timeExpire == -1 or penalty.duration > self._MIN_PENALTY_DURATION)
                    and (penalty.adminId is not None or self._REMOVE_B3_BAN)):
                self.debug('Banned client (%s) found in follow list DB table. Removing...' % client.name)
                cursor2 = self.console.storage.query(self._DEL_QUERY % client.id)
                cursor2.close()
            else:
                self.debug('Client (%s) was banned by B3 or ban duration is too short' % client.name)

    def process_disconnect_event(self, client_cid, client):
        self.debug("Processing disconnect event")
        self.verbose('Disconnected client\'s cid = %s, followlist = %s' % (client_cid, self._following))
        if not client:
            try:
                client = self._onlinePlayers.pop(client_cid, None)
            except:
                pass
        if client and client.id in self._following:
            self.debug("Client %s disconnected, removing from online suspect list" % (self._following[client.id]))
            del self._following[client.id]
            if len(self._following) > 0:
                self.verbose('Online suspects: %s' % self._following)
            else:
                self.verbose('All suspected players disconnected')

    def notify_connecting_admin(self, client):
        for suspect in self._following.values():
            self._show_message(client, suspect)
            time.sleep(1)

    def _add_list(self, client):
        if client.id not in self._following:
            self.verbose('online follow list: %s' % self._following)
            self.debug("Checking database for %s [@%s]" % (client.name, client.id))
            cursor = self.console.storage.query(self._SELECT_QUERY % client.id)
            if cursor.rowcount > 0:
                r = cursor.getRow()
                self.debug("Client %s [@%s] found in follow list." % (client.name, client.id))
                if r['reason'] and r['reason'] != '' and r['reason'] != 'None':
                    reason = r['reason']
                else:
                    reason = self._DEFAULT_REASON
                admin = self._adminPlugin.findClientPrompt("@%s" % r['admin_id'])
                if admin:
                    admin_name = admin.name
                    admin_id = admin.id
                else:
                    admin_name = 'B4'
                    admin_id = '0'
                client.setvar(self, 'follow_reason', reason)
                self.verbose('follow_reason: %s' % reason)
                client.setvar(self, 'follow_admin', admin_name)
                self.verbose('follow_admin: %s' % admin_name)
                client.setvar(self, 'follow_admin_id', admin_id)
                self.verbose('follow_admin_id: %s' % admin_id)
                client.setvar(self, 'follow_data', {'reason': reason, 'admin': admin_name, 'admin_id': admin_id})
                self._following[client.id] = client
                self.verbose('online follow list: %s' % self._following)
                return True
        return False

    def cleanup(self):
        self.verbose('Cleaning banned players')
        cursor = self.console.storage.query(self._BANNED % self._MIN_PENALTY_DURATION)
        players = []
        while not cursor.EOF:
            r = cursor.getRow()
            players.append(r['client_id'])
            cursor.moveNext()
        for c_id in players:
            cursor = self.console.storage.query(self._DEL_QUERY % c_id)
            if c_id in self._following:
                del self._following[c_id]
        self.debug('Removed %d players' % len(players))

    def cmd_checkfollow(self, data, client, cmd=None):
        """\
        list connected users being followed
        """
        if len(self._following) > 0:
            client.message("^7Checking...")
            self.notify_connecting_admin(client)
            client.message("^7Check complete.")
        else:
            client.message('Currently there are no players online in follow list')

    def cmd_syncfollow(self, data, client, cmd=None):
        """\
        sync connected players
        """
        client.message("^7Syncing...")
        self.sync_list(None)
        client.message("^7Synced.")

    def cmd_listfollow(self, data, client, cmd=None):
        """\
        list followed users
        """
        cursor = self.console.storage.query(self._LIST_QUERY)
        if cursor.rowcount == 0:
            client.message("^7The list is empty.")
            return False

        names = []
        while not cursor.EOF:
            r = cursor.getRow()
            c = self.console.storage.getClientsMatching({'id': r['client_id']})
            if c:
                names.append("^7[^2@%s^7] %s" % (c[0].id, c[0].name))
            else:
                self.error("Not found client matching id %s" % r['client_id'])
            cursor.moveNext()
        client.message(', '.join(names))

    def cmd_follow(self, data, client, cmd=None):
        """\
        <name> - add user to the follow list
        <reason> - optional
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters, try !help follow')
            return False

        if len(m) == 2:
            cid, reason = m
        elif len(m) == 1:
            cid = m[0]
            reason = ''
        else:
            client.message('^7Invalid parameters, try !help follow')
            return False
        sclient = self._adminPlugin.findClientPrompt(cid, client)

        if not sclient:
            return False

        self.add_follow_client(sclient, client, reason)

    def add_follow_client(self, sclient, client=None, reason=''):
        self.info("follow add_follow_client; thread % r" % threading.current_thread().ident)
        cursor = self.console.storage.query(self._SELECT_QUERY % sclient.id)
        if cursor.rowcount == 0:
            if client:
                admin = client.id
            else:
                admin = 0
            cursor2 = self.console.storage.query(self._ADD_QUERY % (sclient.id, admin, self.console.time(), reason))
            cursor2.close()
            self.debug("%s added to watch list" % sclient.name)
            if client:
                client.message("^7%s has been added to the watch list." % sclient.name)
        else:
            self.debug("%s already in watch list" % sclient.name)
            if client:
                client.message("^7%s already exists in watch list." % sclient.name)
        self.sync_list(None)

    def cmd_unfollow(self, data, client, cmd=None):
        """\
        <name> - remove user from the follow list
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters, try !help unfollow')
            return False

        sclient = self._adminPlugin.findClientPrompt(m[0], client)
        cursor = self.console.storage.query(self._DEL_QUERY % sclient.id)
        if cursor.rowcount == 0:
            self.debug('%s is not in watchlist, giving up...' % sclient.name)
            client.message('%s is not in watchlist, giving up...' % sclient.name)
            return False

        self.debug("%s removed from watch list" % sclient.name)
        client.message("^7%s removed from the watch list." % sclient.name)
        self.sync_list(None)

    def cmd_followinfo(self, data, client, cmd=None):
        """\
        <name> - show more details
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters, try !help followinfo')
            return False

        sclient = self._adminPlugin.findClientPrompt(m[0], client)
        cursor = self.console.storage.query(self._SELECT_QUERY % sclient.id)

        if cursor.rowcount > 0:
            r = cursor.getRow()
            admin = self._adminPlugin.findClientPrompt("@%s" % r['admin_id'], client)
            if admin:
                admin_name = admin.name
            else:
                admin_name = 'B3'
            if r['reason'] and r['reason'] != '' and r['reason'] != 'None':
                reason = r['reason']
            else:
                reason = self._DEFAULT_REASON
            client.message('%s was added by %s for %s' % (sclient.name, admin_name, reason))
        else:
            client.message('No follow info for %s' % sclient.name)

"""
if __name__ == '__main__':
    from b4_fake import fakeConsole
    from b4_fake import superadmin

    p = FollowPlugin(fakeConsole, 'conf/follow.xml')
    p.onStartup()

    superadmin.connects(cid=1)
    time.sleep(1)
    superadmin.says('!listfollow')
    time.sleep(2)
"""
