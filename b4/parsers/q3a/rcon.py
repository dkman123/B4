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

import re
import socket
import select
import time
import threading
import queue

from threading import Thread

__author__ = 'ThorN'
__version__ = '1.11'


class Rcon(object):

    host = ()
    password = None
    lock = threading.Lock()
    lock.acquire()
    socket = None
    queue = None
    console = None
    socket_timeout = 0.80
    # NOTE: \377 is octal for 0xFF
    rconsendstring = '\377\377\377\377rcon "%s" %s\n'
    rconreplystring = '\377\377\377\377print\n'
    qserversendstring = '\377\377\377\377%s\n'

    # default expire time for the status cache in seconds and cache type
    status_cache_expire_time = 2
    status_cache = False
    status_cache_expired = None
    status_cache_data = ''

    def __init__(self, console, host, password):
        """
        Object contructor.
        :param console: The console implementation
        :param host: The host where to send RCON commands
        :param password: The RCON password
        """
        self.console = console
        self.queue = queue.Queue()

        if self.console.config.has_option('caching', 'status_cache_type'):
            status_cache_type = self.console.config.get('caching', 'status_cache_type').lower()
            if status_cache_type == 'memory':
                self.status_cache = True

        if self.console.config.has_option('caching', 'status_cache_expire'):
            self.status_cache_expire_time = abs(self.console.config.getint('caching', 'status_cache_expire'))
            if self.status_cache_expire_time > 5:
                self.status_cache_expire_time = 5
        # set the cache expire time to now, so the first status request will retrieve a status from the server
        status_cache_expired = time.time()

        self.console.bot('Rcon status cache expire time: [%s sec] Type: [%s]' % (self.status_cache_expire_time,
                                                                                 self.status_cache))
        self.console.bot('Game name is: %s' % self.console.gameName)
        self.socket = socket.socket(type=socket.SOCK_DGRAM)
        self.host = host
        self.password = password
        self.socket.settimeout(2)
        self.socket.connect(self.host)

        self._stopEvent = threading.Event()
        Thread(target=self._writelines, args=()).start()

    def encode_data(self, data, source):
        """
        Encode data before sending them onto the socket.
        :param data: The string to be encoded
        :param source: Who requested the encoding
        """
        self.console.info("rcon encode_data %s; source %s" % (data, source))
        try:
            if isinstance(data, bytes):
                data = str(data, 'utf_8', errors='ignore')
            data = data.encode(self.console.encoding, 'replace')
            #if isinstance(data, str):
            #    data = bytes(data, 'utf_8', errors='ignore')
        except Exception as msg:
            self.console.warning('%s: error encoding data: %r', source, msg)
            data = 'Encoding error'
            
        return data
        
    def send(self, data, maxRetries=None, socketTimeout=None):
        """
        Send data over the socket.
        :param data: The string to be sent
        :param maxRetries: How many times we have to retry the sending upon failure
        :param socketTimeout: The socket timeout value
        """
        self.console.info("rcon send")
        if socketTimeout is None:
            socketTimeout = self.socket_timeout
        if maxRetries is None:
            maxRetries = 2

        data = data.strip()
        # encode the data
        if self.console.encoding:
            data = self.encode_data(data, 'QSERVER')

        self.console.verbose('QSERVER sending (%s:%s) %r', self.host[0], self.host[1], data)
        start_time = time.time()

        retries = 0
        while time.time() - start_time < 5:
            readables, writeables, errors = select.select([], [self.socket], [self.socket], socketTimeout)
            if len(errors) > 0:
                self.console.warning('QSERVER: %r', errors)
            elif len(writeables) > 0:
                try:
                    writeables[0].send(self.qserversendstring % data)
                except Exception as msg:
                    self.console.warning('QSERVER: error sending: %r', msg)
                else:
                    try:
                        data = self.readSocket(self.socket, socketTimeout=socketTimeout)
                        self.console.verbose2('QSERVER: received %r' % data)
                        return data
                    except Exception as msg:
                        self.console.warning('QSERVER: error reading: %r', msg)
            else:
                self.console.verbose('QSERVER: no writeable socket')

            time.sleep(0.05)
            retries += 1

            if retries >= maxRetries:
                self.console.error('QSERVER: too many tries: aborting (%r)', data.strip())
                break

            self.console.verbose('QSERVER: retry sending %r (%s/%s)...', data.strip(), retries, maxRetries)

        self.console.debug('QSERVER: did not send any data')
        return ''

    def sendRcon(self, data, maxRetries=None, socketTimeout=None):
        """
        Send an RCON command.
        :param data: The string to be sent
        :param maxRetries: How many times we have to retry the sending upon failure
        :param socketTimeout: The socket timeout value
        """
        #self.console.info("rcon sendRcon")
        if socketTimeout is None:
            socketTimeout = self.socket_timeout
        if maxRetries is None:
            maxRetries = 2

        data = data.strip()
        # encode the data
        if self.console.encoding:
            data = self.encode_data(data, 'RCON')

        if type(data) is not str:
            data = data.decode('utf-8')
        self.console.verbose('RCON sending (%s:%s) %r', self.host[0], self.host[1], data)
        start_time = time.time()

        retries = 0
        while time.time() - start_time < 5:
            readables, writeables, errors = select.select([], [self.socket], [self.socket], socketTimeout)

            if len(errors) > 0:
                self.console.warning('RCON: %s', str(errors))
            elif len(writeables) > 0:
                try:
                    # convert the string to bytes before sending
                    tosend = self.rconsendstring % (self.password, data)
                    tohex = " ".join("{:02x}".format(ord(c)) for c in tosend)
                    self.console.info("rcon sending hex %s" % tohex)
                    # convert to bytes or no?
                    writeables[0].send(bytearray.fromhex(tohex))
                except Exception as msg:
                    self.console.warning('RCON: error sending: %r', msg)
                else:
                    try:
                        data = self.readSocket(self.socket, socketTimeout=socketTimeout)
                        self.console.verbose2('RCON: received %r' % data)
                        return data
                    except Exception as msg:
                        self.console.warning('RCON: error reading: %r', msg)

                if re.match(r'^quit|map(_rotate)?.*', data):
                    # do not retry quits and map changes since they prevent the server from responding
                    self.console.verbose2('RCON: no retry for %r', data)
                    return ''

            else:
                self.console.verbose('RCON: no writeable socket')

            time.sleep(0.05)

            retries += 1

            if retries >= maxRetries:
                self.console.error('RCON: too many tries: aborting (%r)', data.strip())
                break

            self.console.verbose('RCON: retry sending %r (%s/%s)...', data.strip(), retries, maxRetries)

        self.console.debug('RCON: did not send any data')
        return ''

    def stop(self):
        """
        Stop the rcon writelines queue.
        """
        self.console.info("rcon stop")
        self._stopEvent.set()

    def _writelines(self):
        """
        Write multiple RCON commands on the socket.
        """
        #self.console.info("rcon _writelines")
        while not self._stopEvent.is_set():
            lines = self.queue.get(True)
            for cmd in lines:
                if not cmd:
                    continue
                with self.lock:
                    self.sendRcon(cmd, maxRetries=1)

    def writelines(self, lines):
        """
        Enqueue multiple RCON commands for later processing.
        :param lines: A list of RCON commands.
        """
        #self.console.info("rcon writelines")
        self.queue.put(lines)

    def write(self, cmd, maxRetries=None, socketTimeout=None):
        """
        Write a RCON command.
        :param cmd: The string to be sent
        :param maxRetries: How many times we have to retry the sending upon failure
        :param socketTimeout: The socket timeout value
        """
        #self.console.info("rcon write")
        # intercept status request for caching construct
        if (cmd == 'status' or cmd == 'PB_SV_PList') and self.status_cache:
            if time.time() < self.status_cache_expired:
                self.console.verbose2('Using Status: Cached %s' % cmd)
                return self.status_cache_data
            else:
                #with self.lock:
                data = self.sendRcon(cmd, maxRetries=maxRetries, socketTimeout=socketTimeout)
                if data:
                    self.status_cache_data = data
                    self.status_cache_expired = time.time() + self.status_cache_expire_time
                    self.console.verbose2('Using Status: Fresh %s' % cmd)
                else:
                    # if no data returned set the cached status to empty, but don't update the expired timer so next attempt will try
                    # to read a new value
                    self.status_cache_data = ''
                return self.status_cache_data
        
        #with self.lock:
        data = self.sendRcon(cmd, maxRetries=maxRetries, socketTimeout=socketTimeout)
        return data if data else ''

    def flush(self):
        #self.console.info("rcon flush")
        pass

    def readNonBlocking(self, sock):
        """
        Read data from the socket (non blocking).
        :param sock: The socket from where to read data
        """
        self.console.info("rcon readNonBlocking")
        sock.settimeout(2)
        start_time = time.time()
        data = ''
        while time.time() - start_time < 1:
            try:
                d = str(sock.recv(4096))
            except socket.error as detail:
                self.console.debug('RCON: error reading: %s' % detail)
                break
            else:
                if d:
                    # remove rcon header
                    data += d.replace(self.rconreplystring, '')
                elif len(data) > 0 and ord(data[-1:]) == 10:
                    break

        return data.strip()

    def readSocket(self, sock, size=4096, socketTimeout=None):
        """
        Read data from the socket.
        :param sock: The socket from where to read data
        :param size: The read size
        :param socketTimeout: The socket timeout value
        """
        #self.console.info("rcon readSocket")
        if socketTimeout is None:
            socketTimeout = self.socket_timeout

        data = ''
        readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)

        if not len(readables):
            self.console.verbose('No readable socket')
            return ''

        while len(readables):
            d = str(sock.recv(size))

            if d:
                self.console.info("attempting decode of received data %r" % d)
                if type(d) is not str:
                    d = d.decode('utf-8')
                # remove rcon header
                data += d.replace(self.rconreplystring, '')

            readables, writeables, errors = select.select([sock], [], [sock], socketTimeout)
            if len(readables):
                self.console.verbose('RCON: more data to read in socket')

        return data

    def close(self):
        self.console.info("rcon close")
        pass

    def getRules(self):
        self.console.info("rcon getRules")
        self.lock.acquire()
        try:
            data = self.send('getstatus')
        finally:
            self.lock.release()
        return data if data else ''

    def getInfo(self):
        self.console.info("rcon getInfo")
        self.lock.acquire()
        try:
            data = self.send('getinfo')
        finally:
            self.lock.release()
        return data if data else ''

########################################################################################################################
#
# import sys
#
# if __name__ == '__main__':
#     # To run tests : python b3/parsers/q3a_rcon.py <rcon_ip> <rcon_port> <rcon_password>
#     from b3.fake import fakeConsole
#     r = Rcon(fakeConsole, (sys.argv[1], int(sys.argv[2])), sys.argv[3])
#
#     for cmd in ['say "test1"', 'say "test2"', 'say "test3"', 'say "test4"', 'say "test5"']:
#         fakeConsole.info('Writing %s', cmd)
#         data = r.write(cmd)
#         fakeConsole.info('Received %s', data)
#
#     print '----------------------------------------'
#     for cmd in ['say "test1"', 'say "test2"', 'say "test3"', 'say "test4"', 'say "test5"']:
#         fakeConsole.info('Writing %s', cmd)
#         data = r.write(cmd, socketTimeout=0.45)
#         fakeConsole.info('Received %s', data)
#
#     print '----------------------------------------'
#     for cmd in ['.B3', '.Administrator', '.Admin', 'status', 'sv_mapRotation', 'players']:
#         fakeConsole.info('Writing %s', cmd)
#         data = r.write(cmd)
#         fakeConsole.info('Received %s', data)
#
#     print '----------------------------------------'
#     for cmd in ['.B3', '.Administrator', '.Admin', 'status', 'sv_mapRotation', 'players']:
#         fakeConsole.info('Writing %s', cmd)
#         data = r.write(cmd, socketTimeout=0.55)
#         fakeConsole.info('Received %s', data)
#
#     print '----------------------------------------'
#     fakeConsole.info('getRules')
#     data = r.getRules()
#     fakeConsole.info('Received %s', data)
#
#     print '----------------------------------------'
#     fakeConsole.info('getInfo')
#     data = r.getInfo()
#     fakeConsole.info('Received %s', data)