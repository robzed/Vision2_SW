#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2016 Rob Probin.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
import datetime
import os
import sys

# switch to the Controller directory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

class Print_Logging:
    def __init__(self):
        # get the time and date as a string
        self.now = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        self.file = None
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.mode = "stdout"
        self.buffer = []
        
    def print_to_stdout(self):
        if self.mode == "stdout":
            return
        
        # ensure not buffered
        self.resume_file_save()
        
        # redirect stdout and stderr to original targets
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def print_to_file(self):
        if self.mode == "file":
            return
        
        self.mode = "file"
        
        if self.file is None:
            self.file = open("mouse_%s.log" % self.now, 'w') 
        
        # redirect stdout and stderr to a file
        sys.stdout = self.file
        sys.stderr = self.file
        
    def hold_file_save(self):
        # only operates on file output
        if self.mode == "file":
            pass

    def resume_file_save(self):
        # stream out buffered data
        # switch off buffer
        pass

l = Print_Logging()
l.print_to_file()


# run the mouse code
import mouse
mouse.main()


