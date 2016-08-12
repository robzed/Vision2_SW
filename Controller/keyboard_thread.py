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
# based on http://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
import sys
#from subprocess import PIPE, Popen
from threading  import Thread

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names


class KeyThread:
    def __init__(self):

        #p = Popen(['myprogram.exe'], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
        self.q = Queue()
        t = Thread(target=self.enqueue_output)
        t.daemon = True # thread dies with the program
        t.start()
        
    def enqueue_output(self):
        while True:
            line = sys.stdin.readline()
            for c in line:
                self.q.put(c)
            
    def get_key(self):
        try:  
            key = self.q.get_nowait() # or q.get(timeout=.1)
        except Empty:
            return None
        else:
            return key
