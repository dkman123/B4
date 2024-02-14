#!/usr/bin/env python
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2010 GrosBedo
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
# TODO:
# - implement cProfile or yappi, or use threading.setProfile and sys.setProfile, or implement one's own multi-threaded profiler:
# http://code.google.com/p/yappi/
# http://code.activestate.com/recipes/465831-profiling-threads/
# http://effbot.org/librarybook/sys.htm
# 
#
# CHANGELOG:
# 2010-09-22 - v0.4.3 - GrosBedo
#   * added error handling if profile and pstats libraries can't be found
# 2010-09-06 - v0.1 - GrosBedo
#    * Initial version.

import cProfile
import multiprocessing
import pos
try:
	import profile
	import pstats
	noprofiler = False
except:
	noprofiler = True
import os
import sys
pathname = os.path.dirname(sys.argv[0])
sys.path.append(os.path.join(pathname, 'b4', 'lib'))

from kthread import *
from profilebrowser import *
try:
	from runsnakerun import runsnake  # runsnakerun needs wxPython lib, if it's not available then we pass
except:
	pass

__author__  = 'GrosBedo'
__version__ = '0.4.3'


def runprofile(mainfunction, output, timeout = 60):
	if noprofiler == True:
		print('ERROR: profiler and/or pstats library missing ! Please install it (probably package named python-profile) before running a profiling !')
		return False
	def profileb4():
		profile.run(mainfunction, output)
	# This is the main function for profiling
	print('=> SAVING MODE\n\n')
	print('Calibrating the profiler...')
	cval = calibrateprofile()
	#print('Found value : %s' % cval)
	print('Initializing the profiler...')
	b4main = KThread(target=profileb4) # we open b4 main function with the profiler, in a special killable thread (see below why)
	print('Will now run the profiling and terminate it in %s seconds. Results will be saved in %s' % (str(timeout), str(output)))
	print('\nCountdown:')
	for i in range(0,5):
		print(str(5-i))
		time.sleep(1)
	print('0\nStarting to profile...')
	b4main.start() # starting the thread
	time.sleep(float(timeout)) # after this amount of seconds, the b4 main function gets killed and the profiler will end its job
	print('\n\nFinishing the profile and saving to the file %s' % str(output))
	b4main.kill() # we must end the main function in order for the profiler to output its results (if we didn't launch a thread and just closed the process, it would have done no result)
	print('=> Profile done ! Exiting...')
	return True

def calibrateprofile():
	pr = profile.Profile()
	calib = []
	crepeat = 10
	for i in range(crepeat):
		calib.append(pr.calibrate(10000))
	final = sum(calib) / crepeat
	profile.Profile.bias = final # Apply computed bias to all Profile instances created hereafter
	return final

def subprocessprofileb4(profiler, mainfunction, output):
	#b4thread = KThread(target=profileb4_timer)
	#b4thread.start()
	profiler.run(mainfunction)

def runprofilesubprocess(mainfunction, output, timeout = 60):
	# Testing function for profiling, using a subprocess (does not really work because of how cProfile works)
	try:
		print('PROFILER SAVING MODE\n--------------------\n')
		print('Preparing the profiler...')
		#b4main = profileb4_thread()
		#b4thread = KThread(target=profileb4_timer)
		#b4thread.start()
		profiler = cProfile.Profile()
		b4main = multiprocessing.Process(target=subprocessprofileb4, args=(profiler, mainfunction,output))
		print('Will now run the profiling and terminate it in %s seconds. Results will be saved in %s' % (str(timeout), str(output)))
		print('\nCountdown:')
		for i in range(0,6):
			print(str(5-i))
			time.sleep(1)
		print('Starting to profile...')
		#profileb4("""b4.tools.profile.subb4()""", output)
		b4main.start() # b4main.start() # starting the thread
		time.sleep(float(timeout)) # after this amount of seconds, the b4 main function gets killed and the profiler will end its job
		print('\n\nFinishing the profile and saving to the file %s' % str(output))
		#b4main.terminate() # b4main.kill() # we must end the main function in order for the profiler to output its results (if we didn't launch a thread and just closed the process, it would have done no result)
		print('=> Profile done ! Exiting...')
		profiler2 = posh.share(profiler)
		profiler2.dump_stats(output)
		#signal.signal(signal.SIGABRT, b4main)
		raise SystemExit(222)
	except SystemExit as e:
		print('SystemExit!')
		sys.exit(223)

def parseprofile(profilelog, out):
	file = open(out, 'w') # opening the output file
	print('Opening the profile in %s...' % profilelog)
	p = pstats.Stats(profilelog, stream=file) # parsing the profile with pstats, and output everything to the file

	print('Generating the stats, please wait...')
	file.write("=== All stats:\n")
	p.strip_dirs().sort_stats(-1).print_stats()
	file.write("=== Cumulative time:\n")
	p.sort_stats('cumulative').print_stats(100)
	file.write("=== Time:\n")
	p.sort_stats('time').print_stats(100)
	file.write("=== Time + cumulative time:\n")
	p.sort_stats('time', 'cum').print_stats(.5, 'init')
	file.write("=== Callees:\n")
	p.print_callees()
	file.write("=== Callers:\n")
	p.print_callers()
	#p.print_callers(.5, 'init')
	#p.add('fooprof')
	file.close()
	print('Stats generated and saved to %s.' % out)
	print('Everything is done. Exiting')

def browseprofile(profilelog):
	print('Starting the pstats profile browser...\n')
	try:
		browser = ProfileBrowser(profilelog)
		print("Welcome to the profile statistics browser. Type help to get started.", file=browser.stream)
		browser.cmdloop()
		print("Goodbye.", file=browser.stream)
	except KeyboardInterrupt:
		pass

def browseprofilegui(profilelog):
	app = runsnake.RunSnakeRunApp(0)
	app.OnInit(profilelog)
	app.MainLoop()
	