#!/usr/bin/env python
import datetime
import os
import sys

# switch to the Controller directory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

# get the time and date as a string
now = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

# redirect stdout and stderr to a file
sys.stdout = open("mouse_%s.log" % now, 'w')
sys.stderr = sys.stdout

# run the mouse code
import mouse
mouse.main()
