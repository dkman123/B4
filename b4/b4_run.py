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
import b4.b4_config
import b4.b4_functions
import b4.b4_pkg_handler
import b4.b4_update
import os
import sys
import argparse
import traceback

from time import sleep

__author__ = 'ThorN'
__version__ = '1.8'

modulePath = b4.b4_pkg_handler.resource_directory(__name__)


def run_autorestart(args=None):
    """
    Run B4 in auto-restart mode.
    """
    restart_num = 0

    if b4.b4_functions.main_is_frozen():
        # if we are running the frozen application we do not
        # need to run any script, just the executable itself
        script = ''
    else:
        # if we are running from sources, then sys.executable is set to `python`
        script = os.path.join(modulePath[:-3], 'b4_run.py')
        if not os.path.isfile(script):
            # must be running from the wheel, so there is no b4_run
            script = os.path.join(modulePath[:-3], 'b4', 'run.py')
        if os.path.isfile(script + 'c'):
            script += 'c'

    if args:
        script = '%s %s %s --autorestart' % (sys.executable, script, ' '.join(args))
    else:
        script = '%s %s --autorestart' % (sys.executable, script)

    while True:

        try:

            #try:
            #    import subprocess32 as subprocess
            #except ImportError:
            import subprocess

            status = subprocess.call(script, shell=True)

            sys.stdout.write('Exited with status: %s ... ' % status)
            sys.stdout.flush()
            sleep(2)

            if status == 221:
                restart_num += 1
                sys.stdout.write('restart requested (%s)\n' % restart_num)
                sys.stdout.flush()
            elif status == 222:
                sys.stdout.write('shutdown requested!\n')
                sys.stdout.flush()
                break
            elif status == 220 or status == 223:
                sys.stdout.write('B4 error (check log file)\n')
                sys.stdout.flush()
                break
            elif status == 224:
                sys.stdout.write('B4 error (check console)\n')
                sys.stdout.flush()
                break
            elif status == 256:
                sys.stdout.write('python error, (check log file)\n')
                sys.stdout.flush()
                break
            elif status == 0:
                sys.stdout.write('normal shutdown\n')
                sys.stdout.flush()
                break
            elif status == 1:
                sys.stdout.write('general error (check console)\n')
                sys.stdout.flush()
                break
            else:
                restart_num += 1
                sys.stdout.write('unknown exit code (%s), restarting (%s)...\n' % (status, restart_num))
                sys.stdout.flush()

            sleep(4)

        except KeyboardInterrupt:
            print('Quit')
            break


def run_update(config=None):
    """
    Run the B4 update.
    :param config: The B4 configuration file instance
    """
    update = b4.b4_update.DBUpdate(config)
    update.run()


def run(options):
    """
    Run B4 in console.
    :param options: command line options
    """
    analysis = None  # main config analysis result
    printexit = False  # whether the exit message has been printed already or not

    try:

        if options.config:
            config = b4.getAbsolutePath(options.config, True)
            if not os.path.isfile(config):
                printexit = True
                b4.b4_functions.console_exit('ERROR: configuration file not found (%s).\n'
                                             'Please visit %s to create one.' % (config, b4.B4_CONFIG_GENERATOR))
        else:
            config = None
            for p in ('b4.%s', 'conf/b4.%s', 'b4/conf/b4.%s',
                      os.path.join(b4.HOMEDIR, 'b4.%s'), os.path.join(b4.HOMEDIR, 'conf', 'b4.%s'),
                      os.path.join(b4.HOMEDIR, 'b4', 'conf', 'b4.%s'), '@b4/conf/b4.%s'):
                for e in ('ini', 'cfg', 'xml'):
                    path = b4.getAbsolutePath(p % e, True)
                    if os.path.isfile(path):
                        print("Using configuration file: %s" % path)
                        config = path
                        sleep(3)
                        break

            if not config:
                printexit = True
                b4.b4_functions.console_exit('ERROR: could not find any valid configuration file.\n'
                                             'Please visit %s to create one.' % b4.B4_CONFIG_GENERATOR)

        # LOADING MAIN CONFIGURATION
        main_config = b4.b4_config.MainConfig(b4.b4_config.load(config))
        analysis = main_config.analyze()
        if analysis:
            raise b4.b4_config.ConfigFileNotValid('invalid configuration file specified')

        # START B4
        b4.start(main_config, options)

    except b4.b4_config.ConfigFileNotValid:
        if analysis:
            print('CRITICAL: invalid configuration file specified:\n')
            for problem in analysis:
                print("  >>> %s\n" % problem)
        else:
            print('CRITICAL: invalid configuration file specified!')
        raise SystemExit(1)
    except SystemExit as msg:
        if not printexit and b4.b4_functions.main_is_frozen():
            if sys.stdout != sys.__stdout__:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
            print(msg)
            input("press any key to continue...")
        raise
    except Exception:
        if sys.stdout != sys.__stdout__:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        traceback.print_exc()
        input("press any key to continue...")


def main():
    """
    Main execution.
    """
    p = argparse.ArgumentParser()
    p.add_argument('-c', '--config', dest='config', default=None, metavar='b4.ini',
                   help='B4 config file. Example: -c b4.ini')
    p.add_argument('-r', '--restart', action='store_true', dest='restart', default=False,
                   help='Auto-restart B4 on crash')
    p.add_argument('-s', '--setup', action='store_true', dest='setup', default=False,
                   help='Setup main b4.ini config file')
    p.add_argument('-u', '--update', action='store_true', dest='update', default=False,
                   help='Update B4 database to latest version')
    p.add_argument('-v', '--version', action='version', default=False, version=b4.getB4versionString(),
                   help='Show B4 version and exit')
    p.add_argument('-a', '--autorestart', action='store_true', dest='autorestart', default=False,
                   help=argparse.SUPPRESS)

    (options, args) = p.parse_known_args()

    if not options.config and len(args) == 1:
        options.config = args[0]

    if options.setup:
        # setup procedure is deprecated: show configuration file generator web tool url instead
        sys.stdout.write('\n')
        b4.b4_functions.console_exit("  *** NOTICE: the console setup procedure is deprecated!\n" \
                                     "  *** Please visit %s to generate a new B4 configuration file.\n" % b4.B4_CONFIG_GENERATOR)

    # add current dir to sys path
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)
    #sys.stdout.write("Exec Path: %s\n" % path)

    if options.update:
        ## UPDATE => CONSOLE
        run_update(config=options.config)

    if options.restart:
        ## AUTORESTART => CONSOLE
        if options.config:
            run_autorestart(['--config', options.config] + args)
        else:
            run_autorestart([])
    else:
        run(options)


if __name__ == '__main__':
    main()
