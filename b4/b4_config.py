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

import os
import re
import sys
import time

import b4
import b4.b4_functions
import b4.b4_exceptions
##import b4.parsers
import b4.storage.b4_storage
import configparser

__author__  = 'ThorN, Courgette, Fenix'
__version__ = '1.7.9'

try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree


ConfigFileNotFound = b4.b4_exceptions.ConfigFileNotFound
ConfigFileNotValid = b4.b4_exceptions.ConfigFileNotValid
NoOptionError = b4.b4_exceptions.NoOptionError
NoSectionError = b4.b4_exceptions.NoSectionError

# list of plugins that cannot be loaded as disabled from configuration file
MUST_HAVE_PLUGINS = ('admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail')


class B4configparserMixin(object):
    """
    Mixin implementing configparser methods more useful for B4 business.
    """
    def get(self, *args, **kwargs):
        """
        Return a configuration value as a string.
        """
        raise NotImplementedError

    def getboolean(self, section, setting):
        """
        Return a configuration value as a boolean.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        """
        value_raw = self.get(section, setting)
        value = value_raw.lower() if value_raw else ''
        if value in ('yes', '1', 'on', 'true'):
            return True
        elif value in ('no', '0', 'off', 'false'):
            return False
        else:
            raise ValueError("%s.%s : '%s' is not a boolean value" % (section, setting, value))

    def getDuration(self, section, setting=None):
        """
        Return a configuration value parsing the duration time
        notation and converting the value into minutes.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        """
        value = self.get(section, setting).strip()
        return b4.b4_functions.time2minutes(value)

    def getpath(self, section, setting):
        """
        Return an absolute path name and expand the user prefix (~).
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        """
        return b4.getAbsolutePath(self.get(section, setting), decode=True)

    def getTextTemplate(self, section, setting=None, **kwargs):
        """
        Return a text template from the configuration file: will
        substitute all the tokens with the given kwargs.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        :param kwargs: A dict with variables used for string substitution.
        """
        sys.stdout.write("b4_config getTextTemplate %s.%s" % (section, setting))
        value = b4.b4_functions.vars2printf(self.get(section, setting, True)).strip()
        sys.stdout.write("b4_config getTextTemplate value = %s" % value)
        if len(kwargs):
            return value % kwargs
        return value


class Xmlconfigparser(B4configparserMixin):
    """
    A config parser class that mimics the configparser
    settings but reads from an XML format.
    """
    _xml = None
    _settings = None

    fileName = ''
    fileMtime = 0

    def __init__(self):
        """
        Object constructor.
        """
        pass

    def _loadSettings(self):
        """
        Load settings section from the configuration
        file into a dictionary.
        """
        self._settings = {}
        for settings in self._xml.findall("./settings"):
            section = settings.get('name')
            self._settings[section] = {}
            for setting in settings.findall("./set"):
                name = setting.get('name')
                value = setting.text
                self._settings[section][name] = value

    def readfp(self, fp):
        """
        Read the XML config file from a file pointer.
        :param fp: The XML file pointer.
        """
        try:
            self._xml = ElementTree.parse(fp)
        except Exception as e:
            raise ConfigFileNotValid("%s" % e)

        self._loadSettings()

    def setXml(self, xml):
        """
        Read the xml config file from a string.
        :param xml: The XML string.
        """
        self._xml = ElementTree.fromstring(xml)

        self._loadSettings()

    def get(self, section, setting=None, dummy=False):
        """
        Return a configuration value as a string.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        :return basestring
        """
        if setting is None:
            # parse as xpath
            return self._xml.findall(section)
        else:
            try:
                data = self._settings[section][setting]
                if data is None:
                    return ''
                else:
                    return data
            except KeyError:
                raise configparser.NoOptionError(setting, section)

    def getint(self, section, setting):
        """
        Return a configuration value as an integer.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        :return int
        """
        value = self.get(section, setting)
        if value is None:
            raise ValueError("%s.%s : is not an integer" % (section, setting))
        return int(self.get(section, setting))

    def getfloat(self, section, setting):
        """
        Return a configuration value as a floating point number.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        :return float
        """
        value = self.get(section, setting)
        if value is None:
            raise ValueError("%s.%s : is not a number" % (section, setting))
        return float(self.get(section, setting))

    def sections(self):
        """
        Return the list of sections of the configuration file.
        :return list
        """
        return self._settings.keys()

    def options(self, section):
        """
        Return the list of options in the given section.
        :return list
        """
        return self._settings[section].keys()

    def has_section(self, section):
        """
        Tells whether the given section exists in the configuration file.
        :return True if the section exists, False otherwise.
        """
        try:
            self._settings[section]
        except KeyError:
            return False
        else:
            return True

    def has_option(self, section, setting):
        """
        Tells whether the given section/setting combination exists in the configuration file.
        :return True if the section/settings combination exists, False otherwise.
        """
        try:
            self._settings[section][setting]
        except KeyError:
            return False
        else:
            return True

    def items(self, section):
        """
        Return all the elements of the given section.
        """
        return self._settings[section].items()

    def load(self, filename):
        """
        Load a configuration file.
        :param filename: The configuration file name.
        """
        if not os.path.isfile(filename):
            raise ConfigFileNotFound(filename)

        f = open(filename, 'r')
        self.readfp(f)
        f.close()

        self.fileName = filename
        self.fileMtime = os.path.getmtime(self.fileName)
        return True

    def loadFromString(self, xmlstring):
        """
        Read the XML config from a string.
        """
        self.fileName = None
        self.fileMtime = time.time()

        try:
            self._xml = ElementTree.XML(xmlstring)
        except Exception as e:
            raise ConfigFileNotValid("%s" % e)

        self._loadSettings()
        return True

    def save(self):
        # not implemented
        return True

    def set(self, section, option, value):
        # not implemented
        pass


class Cfgconfigparser(B4configparserMixin, configparser.ConfigParser):
    """
    A config parser class that mimics the configparser, reads the cfg format.
    """
    fileName = ''
    fileMtime = 0

    def __init__(self, allow_no_value=False):
        """
        Object constructor.
        :param allow_no_value: Whether to allow empty values in configuration sections
        """
        configparser.ConfigParser.__init__(self, allow_no_value=allow_no_value)

    def add_comment(self, section, comment):
        """
        Add a comment
        :param section: The section where to place the comment
        :param comment: The comment to add
        """
        if not section or section == "DEFAULT":
            sectdict = self._defaults
        else:
            try:
                sectdict = self._sections[section]
            except KeyError:
                raise configparser.NoSectionError(section)
        sectdict['; %s' % (comment,)] = None

    def get(self, section, option, *args, **kwargs):
        """
        Return a configuration value as a string.
        """
        try:
            value = configparser.ConfigParser.get(self, section, option, **kwargs)
            if value is None:
                return ""
            return value
        except configparser.NoSectionError:
            # plugins are used to only catch NoOptionError
            raise configparser.NoOptionError(option, section)

    def load(self, filename):
        """
        Load a configuration file.
        """
        f = open(filename, 'r')
        self.readfp(f)
        f.close()
        self.fileName = filename
        self.fileMtime = os.path.getmtime(self.fileName)
        return True

    def loadFromString(self, cfg_string):
        """
        Read the cfg config from a string.
        """
        from io import StringIO
        fp = StringIO(cfg_string)
        self.readfp(fp)
        fp.close()
        self.fileName = None
        self.fileMtime = time.time()
        return True

    def readfp(self, fp, filename=None):
        """
        Inherits from configparser.configparser to throw our custom exception if needed
        """
        try:
            configparser.ConfigParser.read_file(self, fp, filename)
        except Exception as e:
            raise ConfigFileNotValid("%s" % e)

    def save(self):
        """
        Save the configuration file.
        """
        f = open(self.fileName, 'w')
        self.write(f)
        f.close()
        return True

    def write(self, fp, **kwargs):
        """
        Write an .ini-format representation of the configuration state.
        :param fp: the file pointer
        :param **kwargs: flexible args value/key pairs (unused)
        """
        if self._defaults:
            fp.write("[%s]\n" % configparser.DEFAULTSECT)
            for (key, value) in self._defaults.items():
                self._write_item(fp, key, value)
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            for (key, value) in self._sections[section].items():
                self._write_item(fp, key, value)
            fp.write("\n")

    @staticmethod
    def _write_item(fp, key, value):
        if (key.startswith(';') or key.startswith('#')) and value is None:
            # consider multiline comments
            for line in key.split('\n'):
                line = b4.b4_functions.left_cut(line, ';')
                line = b4.b4_functions.left_cut(line, '#')
                fp.write("; %s\n" % (line.strip(),))
        else:
            if value is not None and str(value).strip() != '':
                fp.write("%s: %s\n" % (key, str(value).replace('\n', '\n\t')))
            else:
                fp.write("%s: \n" % key)


def load(filename):
    """
    Load a configuration file.
    Will instantiate the correct configuration object parser.
    """
    if os.path.splitext(filename)[1].lower() == '.xml':
        config = Xmlconfigparser()
    else:
        # allow the use of empty keys to support the new b4_ini configuration file
        config = Cfgconfigparser(allow_no_value=True)

    filename = b4.getAbsolutePath(filename, True)

    # return the config if it can be loaded
    return config if config.load(filename) else None


class MainConfig(B4configparserMixin):
    """
    Class to use to parse the B4 main config file.
    Responsible for reading the file either in xml or ini format.
    """
    def __init__(self, config_parser):
        self._config_parser = config_parser
        self._plugins = []
        if isinstance(self._config_parser, Xmlconfigparser):
            self._init_plugins_from_xml()
        elif isinstance(self._config_parser, Cfgconfigparser):
            self._init_plugins_from_cfg()
        else:
            raise NotImplementedError("unexpected config type: %r" % self._config_parser.__class__)

    def _init_plugins_from_xml(self):
        self._plugins = []
        for p in self._config_parser.get('plugins/plugin'):
            x = p.get('disabled')
            self._plugins.append({
                'name': p.get('name'),
                'conf': p.get('config'),
                'path': p.get('path'),
                'disabled':  x is not None and x not in MUST_HAVE_PLUGINS and x.lower() in ('yes', '1', 'on', 'true')
            })

    def _init_plugins_from_cfg(self):
        ## Load the list of disabled plugins
        try:
            disabled_plugins_raw = self._config_parser.get('b4', 'disabled_plugins')
        except configparser.NoOptionError:
            disabled_plugins = []
        else:
            disabled_plugins = re.split(r'\W+', disabled_plugins_raw.lower())

        def get_custom_plugin_path(plugin_name):
            try:
                return self._config_parser.get('plugins_custom_path', plugin_name)
            except configparser.NoOptionError:
                return None

        self._plugins = []
        if self._config_parser.has_section('plugins'):
            for name in self._config_parser.options('plugins'):
                self._plugins.append({
                    'name': name,
                    'conf': self._config_parser.get('plugins', name),
                    'path': get_custom_plugin_path(name),
                    'disabled': name.lower() in disabled_plugins and name.lower() not in MUST_HAVE_PLUGINS
                })

    def get_plugins(self):
        """
        :return: list[dict] A list of plugin settings as a dict.
            I.E.:
            [
                {'name': 'admin', 'conf': @conf/plugin_admin.ini, 'path': None, 'disabled': False},
                {'name': 'adv', 'conf': @conf/plugin_adv.xml, 'path': None, 'disabled': False},
            ]
        """
        return self._plugins

    def get_external_plugins_dir(self):
        """
        the directory path (as a string) where additional plugin modules can be found
        :return: str or configparser.NoOptionError
        """
        if isinstance(self._config_parser, Xmlconfigparser):
            return self._config_parser.getpath("plugins", "external_dir")
        elif isinstance(self._config_parser, Cfgconfigparser):
            return self._config_parser.getpath("b4", "external_plugins_dir")
        else:
            raise NotImplementedError("unexpected config type: %r" % self._config_parser.__class__)

    def get(self, *args, **kwargs):
        """
        Override the get method defined in the B4configparserMixin
        """
        return self._config_parser.get(*args, **kwargs)

    def analyze(self):
        """
        Analyze the main configuration file checking for common mistakes.
        This will mostly check configuration file values and will not perform any further check related,
        i.e: connection with the database can be established using the provided dsn, rcon password is valid etc.
        Such validations needs to be handled somewhere else.
        :return: A list of strings highlighting problems found (so they can be logged/displayed easily)
        """
        analysis = []

        def _mandatory_option(section, option):
            if not self.has_option(section, option):
                analysis.append('missing configuration value %s::%s' % (section, option))

        _mandatory_option('b4', 'parser')
        _mandatory_option('b4', 'database')
        _mandatory_option('b4', 'bot_name')

        ## PARSER CHECK
        if self.has_option('b4', 'parser'):
            try:
                # read config [b4] section, parser option
                b4.b4_functions.getModule('b4.parsers.%s' % self.get('b4', 'parser'))
            except ImportError:
                analysis.append('invalid parser specified in b4::parser (%s)' % self.get('b4', 'parser'))

        ## DSN DICT
        if self.has_option('b4', 'database'):
            dsndict = b4.b4_functions.splitDSN(self.get('b4', 'database'))
            if not dsndict:
                analysis.append('invalid database source name specified in b4::database (%s)' % self.get('b4', 'database'))
            elif dsndict['protocol'] not in b4.storage.b4_storage.PROTOCOLS:
                analysis.append('invalid storage protocol specified in b4::database (%s) : '
                                'valid protocols are : %s' % (dsndict['protocol'], ', '.join(b4.storage.b4_storage.PROTOCOLS)))

        ## ADMIN PLUGIN CHECK
        has_admin = False
        has_admin_config = False
        for plugin in self.get_plugins():
            if plugin['name'] == 'admin':
                has_admin = True
                if plugin['conf']:
                    has_admin_config = True
                break

        if not has_admin:
            analysis.append('missing admin plugin in plugins section')
        elif not has_admin_config:
            analysis.append('missing configuration file for admin plugin')

        return analysis

    def __getattr__(self, name):
        """
        Act as a proxy in front of self._config_parser.
        Any attribute or method call which does not exists in this
        object (MainConfig) is then tried on the self._config_parser
        :param name: str Attribute or method name
        """
        if hasattr(self._config_parser, name):
            attr = getattr(self._config_parser, name)
            if hasattr(attr, '__call__'):
                def newfunc(*args, **kwargs):
                    return attr(*args, **kwargs)
                return newfunc
            else:
                return attr
        else:
            raise AttributeError(name)
