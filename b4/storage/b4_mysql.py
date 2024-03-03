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

import b4
import b4.storage.b4_common
import sys
import threading

from time import time
from traceback import extract_tb


class PymysqlStorage(b4.storage.b4_common.DatabaseStorage):
    """
    Base inheritance class for MysqlStorage when using pymysql driver.
    """

    def __init__(self, dsn, dsnDict, console):
        """
        Object constructor.
        Every exception raised from here should make B4 non-operational since we won't have storage support.
        :param dsn: The database connection string.
        :param dsnDict: The database connection string parsed into a dict.
        :param console: The console instance.
        """
        super(PymysqlStorage, self).__init__(dsn, dsnDict, console)

    ####################################################################################################################
    #                                                                                                                  #
    #   CONNECTION INITIALIZATION/TERMINATION/RETRIEVAL                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def getConnection(self):
        """
        Return the database connection. If the connection has not been established yet, will establish a new one.
        :return The connection instance, or None if no connection can be established.
        """
        sys.stdout.write("b4_mysql PymysqlStorage getConnection %r\n" % threading.current_thread().ident)
        if (threading.current_thread().ident in self.db
                and self.db[threading.current_thread().ident]
                and self.db[threading.current_thread().ident].open):
            return self.db[threading.current_thread().ident]
        return self.connect()

    def shutdown(self):
        """
        Close the current active database connection.
        """
        #sys.stdout.write("b4_mysql PymysqlStorage shutdown\n")
        if (threading.current_thread().ident in self.db
                and self.db[threading.current_thread().ident]
                and self.db[threading.current_thread().ident].open):
            # checking 'open' will prevent exception raising
            self.console.bot('Closing connection with MySQL database...')
            self.db[threading.current_thread().ident].close()
        if threading.current_thread().ident in self.db:
            del self.db[threading.current_thread().ident]

    ####################################################################################################################
    #                                                                                                                  #
    #   UTILITY METHODS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def status(self):
        """
        Check whether the connection with the storage layer is active or not.
        :return True if the connection is active, False otherwise.
        """
        #sys.stdout.write("b4_mysql PymysqlStorage status\n")
        if (threading.current_thread().ident in self.db
                and self.db[threading.current_thread().ident]
                and self.db[threading.current_thread().ident].open):
            return True
        return False


class MysqlConnectorStorage(b4.storage.b4_common.DatabaseStorage):
    """
    Base inheritance class for MysqlStorage when using mysql.connector driver.
    """

    def __init__(self, dsn, dsnDict, console):
        """
        Object constructor.
        Every exception raised from here  should make B4 non-operational since we won't have storage support.
        :param dsn: The database connection string.
        :param dsnDict: The database connection string parsed into a dict.
        :param console: The console instance.
        """
        super(MysqlConnectorStorage, self).__init__(dsn, dsnDict, console)

    ####################################################################################################################
    #                                                                                                                  #
    #   CONNECTION INITIALIZATION/TERMINATION/RETRIEVAL                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def getConnection(self):
        """
        Return the database connection. If the connection has not been established yet, will establish a new one.
        :return The connection instance, or None if no connection can be established.
        """
        sys.stdout.write("b4_mysql MysqlConnectorStorage getConnection %r\n" % threading.current_thread().ident)
        if (threading.current_thread().ident in self.db
                and self.db[threading.current_thread().ident]
                and self.db[threading.current_thread().ident]._socket is not None):
            return self.db[threading.current_thread().ident]
        return self.connect()

    def shutdown(self):
        """
        Close the current active database connection.
        """
        #sys.stdout.write("b4_mysql MysqlConnectorStorage shutdown\n")
        self.console.info("b4_mysql.MysqlConnectorStorage.shutdown")
        if (threading.current_thread().ident in self.db
                and self.db[threading.current_thread().ident]
                and self.db[threading.current_thread().ident]._socket is not None):
            # the shutdown method is already exception safe
            self.console.bot('Closing connection with MySQL database...')
            self.db[threading.current_thread().ident].shutdown()
        if threading.current_thread().ident in self.db:
            del self.db[threading.current_thread().ident]

    ####################################################################################################################
    #                                                                                                                  #
    #   UTILITY METHODS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def status(self):
        """
        Check whether the connection with the storage layer is active or not.
        :return True if the connection is active, False otherwise.
        """
        #sys.stdout.write("b4_mysql MysqlConnectorStorage status\n")
        self.console.info("b4_mysql.MysqlConnectorStorage.status")
        if (threading.current_thread().ident in self.db
                and self.db[threading.current_thread().ident]
                and self.db[threading.current_thread().ident]._socket is not None):
            return True
        return False


class MySQLdbStorage(b4.storage.b4_common.DatabaseStorage):
    """
    Base inheritance class for MysqlStorage when using MySQLdb driver.
    """

    def __init__(self, dsn, dsnDict, console):
        """
        Object constructor.
        Every exception raised from here should make B4 non-operational since we won't have storage support.
        :param dsn: The database connection string.
        :param dsnDict: The database connection string parsed into a dict.
        :param console: The console instance.
        """
        super(MySQLdbStorage, self).__init__(dsn, dsnDict, console)

    ####################################################################################################################
    #                                                                                                                  #
    #   CONNECTION INITIALIZATION/TERMINATION/RETRIEVAL                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def getConnection(self):
        """
        Return the database connection. If the connection has not been established yet, will establish a new one.
        :return The connection instance, or None if no connection can be established.
        """
        sys.stdout.write("b4_mysql MySQLdbStorage connect %r\n" % threading.current_thread().ident)
        if (threading.current_thread().ident in self.db
                and self.db[threading.current_thread().ident]
                and self.db[threading.current_thread().ident].open):
            return self.db[threading.current_thread().ident]
        return self.connect()

    def shutdown(self):
        """
        Close the current active database connection.
        """
        #sys.stdout.write("b4_mysql MySQLdbStorage shutdown\n")
        if (threading.current_thread().ident in self.db
                and self.db[threading.current_thread().ident]
                and self.db[threading.current_thread().ident].open):
            # checking 'open' will prevent exception raising
            self.console.bot('Closing connection with MySQL database...')
            self.db[threading.current_thread().ident].close()
        if threading.current_thread().ident in self.db:
            del self.db[threading.current_thread().ident]

    ####################################################################################################################
    #                                                                                                                  #
    #   UTILITY METHODS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def status(self):
        """
        Check whether the connection with the storage layer is active or not.
        :return True if the connection is active, False otherwise.
        """
        #sys.stdout.write("b4_mysql MySQLdbStorage status\n")
        if (threading.current_thread().ident in self.db
                and self.db[threading.current_thread().ident]
                and self.db[threading.current_thread().ident].open):
            return True
        return False


class MysqlStorage(b4.storage.b4_common.DatabaseStorage):
    _reconnectDelay = 60
    protocol = 'mysql'

    def __new__(cls, *args, **kwargs):
        """
        Will set the MysqlStorage base class according to the driver available on the system running B4.
        :raise ImportError: If the system misses the necessary libraries needed to setup the storage module.
        """
        try:
            # fil = open("/home/urt/test.txt", "w")

            # PREFER PYMYSQL
            # fil.write("trying pymysql driver");
            import pymysql as mysqldriver
            cls.__bases__ = (PymysqlStorage,)
            cls.__driver = mysqldriver
            # new inheritance: MysqlStorage -> PymysqlStorage -> DatabaseStorage -> Storage
        except ImportError:

            try:
                # BACKUP USING MYSQL.CONNECTOR
                # fil.write("trying mysql.connector driver");
                import b4_mysql.connector as mysqldriver
                cls.__bases__ = (MysqlConnectorStorage,)
                cls.__driver = mysqldriver
                # new inheritance: MysqlStorage -> MysqlConnectorStorage -> DatabaseStorage -> Storage
            except ImportError:

                try:
                    # USE MYSQLDB AS LAST OPTION
                    # fil.write("trying MySQLdb driver");
                    import MySQLdb as mysqldriver
                    cls.__bases__ = (MySQLdbStorage,)
                    cls.__driver = mysqldriver
                    # new inheritance: MysqlStorage -> MySQLdbStorage -> DatabaseStorage -> Storage
                except ImportError:
                    mysqldriver = None
                    # re-raise ImportError with a custom message since it will be logged and it may
                    # help end users in fixing the problem by themselves (installing libraries)
                    raise ImportError("missing MySQL connector driver. You need to install one of the following MySQL "
                                      "connectors: 'pymysql', 'python-mysql.connector', 'MySQL-python': look for "
                                      "'dependencies' in B4 documentation.")

        # fil.close()
        return super(MysqlStorage, cls).__new__(cls)

    def __init__(self, dsn, dsnDict, console):
        """
        Object constructor.
        Every exception raised from here should make B4 non-operational since we won't have storage support.
        :param dsn: The database connection string.
        :param dsnDict: The database connection string parsed into a dict.
        :param console: The console instance.
        :raise AttributeError: if the given dsnDict is missing required information.
        """
        super(MysqlStorage, self).__init__(dsn, dsnDict, console)
        # check for valid MySQL host
        if not self.dsnDict['host']:
            raise AttributeError(
                "invalid MySQL host in %(protocol)s://%(user)s:******@%(host)s:%(port)s%(path)s" % self.dsnDict)
        # check for valid MySQL database name
        if not self.dsnDict['path'] or not self.dsnDict['path'][1:]:
            raise AttributeError(
                "missing MySQL database name in %(protocol)s://%(user)s:******@%(host)s:%(port)s%(path)s"
                % self.dsnDict)

    ####################################################################################################################
    #                                                                                                                  #
    #   CONNECTION INITIALIZATION/TERMINATION/RETRIEVAL                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def connect(self):
        """
        Establish and return a connection with the storage layer.
        Will store the connection object also in the 'db' attribute so in the future we can reuse it.
        :return The connection instance if established successfully, otherwise None.
        """
        #sys.stdout.write("b4_mysql MysqlStorage connect\n")
        self.console.info("b4_mysql.MysqlStorage.connect %r" % threading.current_thread().ident)
        # do not retry too soon because the MySQL server could
        # have connection troubles, and we do not want to spam it
        if time() - self._lastConnectAttempt < self._reconnectDelay:
            # remove the key from the dictionary
            if threading.current_thread().ident in self.db:
                del self.db[threading.current_thread().ident]
            self.console.bot('New MySQL database connection requested but last connection attempt '
                             'failed less than %s seconds ago: exiting...' % self._reconnectDelay)
        else:
            # close the active connection (if any)
            self.shutdown()
            self.console.bot(
                'Connecting to MySQL database: %(protocol)s://%(user)s:******' +
                '@%(host)s:%(port)s%(path)s...', self.dsnDict)
            # uncomment the following line to show the password
            # self.console.bot('Using pass %(password)s', self.dsnDict)

            try:
                # sys.stdout.write(" Host: %s\n Port: %s\n User: %s\n  Pass: %s\n  DB: %s\n " %
                #                  (self.dsnDict['host'], self.dsnDict['port'],
                #                   self.dsnDict['user'], self.dsnDict['password'],
                #                   self.dsnDict['path'][1:]))
                # create the connection instance using the specified connector
                self.db[threading.current_thread().ident] = self.__driver.connect(host=self.dsnDict['host'],
                                                port=self.dsnDict['port'],
                                                user=self.dsnDict['user'],
                                                password=self.dsnDict['password'],
                                                db=self.dsnDict['path'][1:],
                                                charset="UTF8MB4")

                self.console.bot('Successfully established a connection with MySQL database %r'
                                 % threading.current_thread().ident)
                self._lastConnectAttempt = 0

                if self._consoleNotice:
                    self.console.screen.write('Connecting to DB : OK\n')
                    self._consoleNotice = False

                # check whether the database is ready for usage or if we have to import B4 sql files to generate
                # necessary tables: if database is empty, then AdminPlugin will raise an exception upon loading
                # hence B4 won't be operational. I placed the check here since it doesn't make sense to keep
                # loading plugins if B4 will crash.
                #sys.stdout.write("mysql about to getTables\n")
                localCursor = list(self.getTables())
                if not localCursor:

                    try:
                        self.console.info("Missing MySQL database tables: importing SQL file: %s..."
                                          % b4.getAbsolutePath("@b4/sql/mysql/b4.sql"))
                        self.queryFromFile("@b4/sql/mysql/b4.sql")
                    except Exception as e:
                        self.shutdown()
                        self.console.critical("Missing MySQL database tables. You need to create the necessary tables "
                                              "for B4 to work. You can do so by importing the following SQL script "
                                              "into your database: %s. An attempt of creating tables automatically "
                                              "just failed: %s" % (b4.getAbsolutePath("@b4/sql/mysql/b4.sql"), e))
            except Exception as e:
                self.console.error('Database connection failed: working in remote mode: %s - %s',
                                   e, extract_tb(sys.exc_info()[2]))
                if threading.current_thread().ident in self.db:
                    del self.db[threading.current_thread().ident]
                self._lastConnectAttempt = time()
                if self._consoleNotice:
                    self.console.screen.write('Connecting to DB : FAILED!\n')
                    self._consoleNotice = False

        return self.db[threading.current_thread().ident]

    ####################################################################################################################
    #                                                                                                                  #
    #   STORAGE INTERFACE                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def getTables(self):
        """
        List the tables of the current database.
        :return: list of strings.
        """
        self.console.verbose3("b4_mysql MysqlStorage getTables")
        tables = []
        #self.console.info("about to query")
        try:
            cursor = self.query("SHOW TABLES")
            if cursor and not cursor.EOF:
                while not cursor.EOF:
                    row = cursor.getRow()
                    tables.append(list(row.values())[0])
                    cursor.moveNext()
                #sys.stdout.write("cursor is not empty\n")
            #else:
            #    sys.stdout.write("cursor is empty\n")
            if cursor is not None:
                cursor.close()
        except Exception as ex:
            self.console.error("b4_mysql MysqlStorage getTables %s" % ex)
            raise ex
        return tables

    def truncateTable(self, table):
        """
        Empty a database table (or a collection of tables)
        :param table: The database table or a collection of tables
        :raise KeyError: If the table is not present in the database
        """
        #sys.stdout.write("b4_mysql MysqlStorage truncateTable\n")
        self.console.info("b4_mysql.MysqlStorage.truncateTable")
        try:
            self.query("""SET FOREIGN_KEY_CHECKS=0;""")
            current_tables = self.getTables()
            if isinstance(table, tuple) or isinstance(table, list):
                for v in table:
                    if v not in current_tables:
                        raise KeyError("could not find table '%s' in the database" % v)
                    self.query("TRUNCATE TABLE %s;" % v)
            else:
                if table not in current_tables:
                    raise KeyError("could not find table '%s' in the database" % table)
                self.query("TRUNCATE TABLE %s;" % table)
        finally:
            self.query("""SET FOREIGN_KEY_CHECKS=1;""")
