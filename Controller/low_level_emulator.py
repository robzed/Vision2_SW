# -*- coding: utf-8 -*-
#
# This file acts as a simulator (or low level emulation environment)
# for mouse.py. This allows it to be run on a standard computer
# without he I/O controller running.
#
# This operates in two modes: 
#    (1) text mode.
#    (2) graphical mode when called from graphic_emulator.
#
# In the second case we disable text output from this file, and
# route output to the graphic_emulator GUI shell. One advantage
# to this approach is that all text to stdout is generated from
# mouse.py - so you can see what it 'thinks', without
# extra text from simulated environment getting in the way.
#
# Copyright 2016 Rob Probin.
# All original work.
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
from __future__ import print_function
from collections import deque
from maze import Maze
import time
from keyboard_thread import KeyThread
import sys

PAUSE_ON_MOVE = False
AUTOMATIC_KEYS = False

EMULATOR_BATTERY_CELL_VOLTAGE = 4.24 #4.25 #3.8 #3.7
EMULATOR_BATTERY_ADC = 0x3FF & int(((4*EMULATOR_BATTERY_CELL_VOLTAGE) *1023 * 12000) / ((33000+12000) * 5 * 0.95))

if len(sys.argv) >= 2 and sys.argv[1] == "TEXT_SIMULATOR":
    TEXT_SIMULATOR = True
else:
    TEXT_SIMULATOR = False

def lleprint(*args, **kargs):
    if TEXT_SIMULATOR:
        sep  = kargs.get('sep', ' ')            # Keyword arg defaults
        end  = kargs.get('end', '\n')
        _file = kargs.get('file', sys.stdout)
        output = ''
        first  = True
        for arg in args:
            output += ('' if first else sep) + str(arg)
            first = False
        _file.write(output + end)


class intermediate_writer:
    def __init__(self, dest) :
        self.dest = dest
        self.led_text = ""
        self.led_print = False
        self.led_end = time.time() + 1

    def flush(self):
        self.dest.flush()
        
    def write(self, text):
        if self.led_print:
            if text == "\n":
                self.led_text += text
            else:
                self.led_text = text
            self.led_end = time.time() + 0.05
        else:
            if len(self.led_text):
                self.dest.write(self.led_text)
                self.led_text = ""
                self.led_end = time.time() + 1
            self.dest.write(text)

    def start_led_print(self):
        self.led_print = True
    
    def end_led_print(self):
        self.led_print = False

    def flush_leds(self):
        self.end_led_print()
        text = self.led_text
        self.led_text = ""
        self.write(text)
        self.led_end = time.time() + 1

    def do_delayed_LEDs(self):
        if self.led_end < time.time():
            self.flush_leds()

class serial:
    class Serial:
        
        def __init__(self, path, baudrate = 57600, timeout = 0.1):
            
            #self.saved = sys.stdout
            self.iw = intermediate_writer(sys.stdout)
            sys.stdout = self.iw

            self.replies = deque()
            self.locked = True
            
            self.heading = 0
            self.row = 0
            self.column = 0

            self.maze = Maze(16)
            self.maze.load_example_maze()
            self.target_time = time.time() + 2
            self.timer_state = 0
            
            self.IR = False
            if TEXT_SIMULATOR:
                self.keys = KeyThread()
            self.key_delayed = None
            
            self.timeout = timeout
            self.LEDs = [".", ".", ".", ".", ".", ".", ".", ".", "."]
            self.last_LEDs = ""
            
            self.shift_middle()
            
            self.accel_table = [0]*512

        def set_gui(self, gui):
            self.gui = gui
            self.keys = gui

        def shift_left(self):
            self.front = 50
            self.ls = 100
            self.rs = 20
            self.l45 = 80
            self.r45 = 10

        def shift_right(self):
            self.front = 50
            self.ls = 20
            self.rs = 100
            self.l45 = 10
            self.r45 = 80

        def shift_middle(self):
            self.front = 50
            self.ls = 50
            self.rs = 50
            self.l45 = 40
            self.r45 = 40

        def shift_far(self):
            self.front = 20
            self.ls = 50
            self.rs = 50
            self.l45 = 40
            self.r45 = 40

        def show_LEDs(self):
            LED7 = self.LEDs[6]
            LED8 = self.LEDs[7]
            LED9 = self.LEDs[8]
            LEDs = "***%s   %s< ^%s >%s" % ("".join(self.LEDs[0:6])[::-1], LED7, LED8, LED9)
            if LEDs != self.last_LEDs:
                self.iw.start_led_print()
                lleprint(LEDs)
                self.iw.end_led_print()
                self.last_LEDs = LEDs
                
        def set_LED(self, num):
            self.LEDs[num-1] = "#"
        
        def clear_LED(self, num):
            self.LEDs[num-1] = "."

        def do_background_processes(self):
            self.do_timers()
            self.do_keys()
            self.iw.do_delayed_LEDs()
            
        def do_timers(self):
            if time.time() > self.target_time:
                self.timer_state += 1
                if self.timer_state == 1:
                    self.target_time = time.time() + 0.1
                elif self.timer_state == 2:
                    if AUTOMATIC_KEYS: 
                        self._wrdata("\x38")    # A press
                    self.target_time = time.time() + 0.25    # quick press
                elif self.timer_state == 3:
                    if AUTOMATIC_KEYS: 
                        self._wrdata("\x30")    # A release
                    self.target_time = time.time() + 1
                elif self.timer_state == 4:
                    if AUTOMATIC_KEYS: 
                        self._wrdata("\x39")    # B press
                    self.target_time = time.time() + 2  # hold
                elif self.timer_state == 5:
                    if AUTOMATIC_KEYS: 
                        self._wrdata("\x31")    # B release
                    self.target_time = time.time() + 1
                else:
                    self._wrdata(chr(0x10+(EMULATOR_BATTERY_ADC>>8)))
                    self._wrdata(chr(EMULATOR_BATTERY_ADC & 0xFF))
                    self.target_time = time.time() + 0.3
                    # test for EV Speed sample
                    #self._wrdata(chr(0x22))
                    #self._wrdata(chr(0x02))
                    #self._wrdata(chr(0x02))

        def do_keys(self):
            if self.key_delayed is not None:
                (end_time, data) = self.key_delayed
                if time.time() > end_time:
                    self._wrdata(data)
                    self.key_delayed = None
                return
            
            key = self.keys.get_key()
            if key is not None:
                if key == 'a':
                    self._wrdata("\x38")    # A press
                    self._wrdata("\x30")    # A release
                elif key == 'b':
                    self._wrdata("\x39")    # B press
                    self._wrdata("\x31")    # B release
                elif key == 'A':
                    self._wrdata("\x38")    # A press
                    self.key_delayed = (time.time()+2, "\x30")
                elif key == "B":
                    self._wrdata("\x39")    # B press
                    self.key_delayed = (time.time()+2, "\x31")
                elif key == "<":
                    lleprint("*** Mouse a bit left")
                    self.shift_left()
                elif key == ">":
                    lleprint("*** Mouse a bit right")
                    self.shift_right()
                #elif key == "|":
                #    pass
                elif key == "^":
                    lleprint("*** Mouse far away from front wall")
                    self.shift_far()
                elif key == "+":
                    lleprint("*** Mouse centered, in same cell as front wall")
                    self.shift_middle()
                elif key == "P":
                    # pause on move
                    PAUSE_ON_MOVE = not PAUSE_ON_MOVE
                elif key == "?":
                    lleprint("***Emulated Mouse Status")
                    _direction = ["north", "east", "south", "west"] [self.heading]
                    lleprint("*** %s (%d, %d)" % (str(_direction), self.row, self.column))    # ●○
                elif key == '\x13' or '\x10':
                    pass
                else:
                    lleprint("***??? Didn't understand", key)
    
        def inWaiting(self):
            self.do_background_processes()
            return len(self.replies)
        
        def _wrdata(self, data):
            if type(data) is int:
                if data > 255 or data < 0:
                    print("Expected byte value - breakpoint in _wrdata()")
                    sys.exit(1)
                data = chr(data)
            elif len(data) != 1:
                print("Expected length 1 string - fix in _wrdata() by splitting")
                sys.exit(1)
            self.replies.append(data)
        
        def _wrdata_int16(self, data):
            self._wrdata(chr(data>>8))
            self._wrdata(chr(data&255))
            
        def _paramcheck(self, cmdv, params, num_params):
            if len(params) != num_params:
                print("Command", hex(cmdv), "had", len(params), "parameters, not", num_params)
                sys.exit(1)
                
        def _process_cmd(self, cmdv, params):

            if cmdv == 0x20 or cmdv == 0x21:
                self._paramcheck(cmdv, params, 1)
                LEDmask = ord(params[0])
                if cmdv == 0x21: LEDmask += 512
                lleprint("***ALL LEDS:", hex(LEDmask))
                for n in range(1,10):
                    if LEDmask&1:
                        self.set_LED(n)
                    else:
                        self.clear_LED(n)
                    LEDmask >>= 1
                
            elif cmdv >= 0x10 and cmdv <= 0x19:
                LEDnum = cmdv&0x0F
                #lleprint("*** LED", LEDnum, "on")
                self.set_LED(LEDnum)
                self.show_LEDs()
            elif cmdv >= 0x00 and cmdv <= 0x09:
                LEDnum = cmdv&0x0F
                #lleprint("*** LED", LEDnum, "off")
                self.clear_LED(LEDnum)
                self.show_LEDs()
            elif cmdv == 0x80:
                self._paramcheck(cmdv, params, 0)
                self._wrdata(cmdv)
                
            elif cmdv == 0x98:
                self._paramcheck(cmdv, params, 0)
                
                if self.IR == False:
                    print("Scanning IR not on - QUITTING")
                    sys.exit(1)

                # bit 0 = front long
                # bit 1 = front short
                # bit 2 = left side
                # bit 3 = right side
                value = 0x40
                if self.maze.get_front_wall(self.heading, self.row, self.column):
                    value += 3
                    lleprint("***       ___")
                else:
                    nrow = self.row
                    ncolumn = self.column
                    if self.heading == 0:
                        nrow += 1
                    elif self.heading == 1:
                        ncolumn += 1
                    elif self.heading == 2:
                        nrow -= 1
                    else:
                        ncolumn -= 1

                    next_cell = self.maze.get_front_wall(self.heading, nrow, ncolumn)
                    if next_cell == None or next_cell:
                        value += 1
                if self.maze.get_left_wall(self.heading, self.row, self.column):
                    value += 0x04
                    lleprint("***       |", end="")
                else:
                    lleprint("***        ", end="")
                if self.maze.get_right_wall(self.heading, self.row, self.column):
                    value += 0x08
                    lleprint("  |")
                else:
                    lleprint(" ")
                
                #lleprint("*** value", value & 0x0f)
                
                self._wrdata(chr(value))
            
            elif cmdv == 0x9A: # front
                self._paramcheck(cmdv, params, 0)
                self._wrdata("\x61")
                self._wrdata(chr(self.front>>8))
                self._wrdata(chr(self.front&255))

            elif cmdv == 0x9B: # l90
                self._paramcheck(cmdv, params, 0)
                self._wrdata("\x62")
                self._wrdata(chr(self.ls>>8))
                self._wrdata(chr(self.ls&255))
            
            elif cmdv == 0x9C: # l45
                self._paramcheck(cmdv, params, 0)
                self._wrdata("\x63")
                self._wrdata(chr(self.l45>>8))
                self._wrdata(chr(self.l45&255))
            
            elif cmdv == 0x9D: # r90
                self._paramcheck(cmdv, params, 0)
                self._wrdata("\x64")
                self._wrdata(chr(self.rs>>8))
                self._wrdata(chr(self.rs&255))
            
            elif cmdv == 0x9E: # r45
                self._paramcheck(cmdv, params, 0)
                self._wrdata("\x65")
                self._wrdata(chr(self.r45>>8))
                self._wrdata(chr(self.r45&255))
            
            elif cmdv == 0xC0:
                self._paramcheck(cmdv, params, 0)
                lleprint("***STOP MOTORS")

            elif cmdv == 0xC1:
                self._paramcheck(cmdv, params, 2)
                distance_value = ord(params[0])*256+ord(params[1])
                lleprint("***FORWARD!", distance_value)
                
                if PAUSE_ON_MOVE:
                    time.sleep(0.5)

                if self.maze.get_front_wall(self.heading, self.row, self.column):
                    print("*** CRASHED ***!")
                    sys.exit(1)
                    
                if self.heading == 0:
                    self.row += 1
                elif self.heading == 1:
                    self.column += 1
                elif self.heading == 2:
                    self.row -= 1
                else:
                    self.column -= 1
                
                lleprint("***Position (%d, %d) Heading %d" % (self.row, self.column, self.heading))
                self._wrdata("\x20")

            elif cmdv == 0xC2: # right
                self._paramcheck(cmdv, params, 2)
                distance_value = ord(params[0])*256+ord(params[1])
                if distance_value > 180:
                    lleprint("***U-TURN!", distance_value)
                    self.heading = 3 & (self.heading + 2)
                else:
                    lleprint("***RIGHT!", distance_value)
                    self.heading = 3 & (self.heading + 1)
 
                if PAUSE_ON_MOVE:
                    time.sleep(0.5)
               
                lleprint("***Position (%d, %d) Heading %d" % (self.row, self.column, self.heading))
                self._wrdata("\x20")

            elif cmdv == 0xC3: # left
                self._paramcheck(cmdv, params, 2)
                distance_value = ord(params[0])*256+ord(params[1])
                if distance_value > 180:
                    lleprint("***U-TURN!", distance_value)
                    self.heading = 3 & (self.heading + 2)
                else:
                    lleprint("***LEFT!", distance_value)
                    self.heading = 3 & (self.heading - 1)

                if PAUSE_ON_MOVE:
                    time.sleep(0.5)

                lleprint("***Position (%d, %d) Heading %d" % (self.row, self.column, self.heading))

                self._wrdata("\x20")
                
            elif cmdv == 0xC4:
                self._paramcheck(cmdv, params, 2)
                lleprint("***Set speed to", ord(params[0])*256+ord(params[1]))
            
            elif cmdv == 0xC5:
                self._paramcheck(cmdv, params, 2)
                self.steering_correction = ord(params[0])*256+ord(params[1])
                lleprint("***Set Steering correction to", self.steering_correction)

            elif cmdv == 0xC6:
                self._paramcheck(cmdv, params, 0)
                lleprint("***Extend Movement!")
                
            elif cmdv == 0xC7:
                self._paramcheck(cmdv, params, 2)
                self.cell_distance = ord(params[0])*256+ord(params[1])
                lleprint("***Set Cell distance to", self.cell_distance)

            elif cmdv == 0xC8:
                self._paramcheck(cmdv, params, 2)
                self.wall_correction = ord(params[0])*256+ord(params[1])
                lleprint("***Set Wall edge correction to", self.wall_correction)

            elif cmdv == 0xC9:
                self._paramcheck(cmdv, params, 2)
                self.distance_to_test = ord(params[0])*256+ord(params[1])
                lleprint("***Set distance test to", self.distance_to_test)
                lleprint("*** >>>>Not complete yet! <<<<")

            elif cmdv == 0xCF:
                self._paramcheck(cmdv, params, 1)
                subcmd = ord(params[0])
                self._wrdata(cmdv)
                self._wrdata(params[0])
                if subcmd == 0xC5:
                    self._wrdata_int16(self.steering_correction)
                elif subcmd == 0xC7:
                    self._wrdata_int16(self.cell_distance)
                elif subcmd == 0xC8:
                    self._wrdata_int16(self.wall_correction)
                elif subcmd == 0xC9:
                    self._wrdata_int16(self.distance_to_test)
                
            elif cmdv == 0xD0:
                self._paramcheck(cmdv, params, 0)
                lleprint("*** TURN OFF IR***")
                self.IR = False

            elif cmdv == 0xD1:
                self._paramcheck(cmdv, params, 0)
                lleprint("*** TURN ON IR***")
                self.IR = True

            elif cmdv == 0xD8:
                self._paramcheck(cmdv, params, 2)
                self.front_long = ord(params[0])*256+ord(params[1])
                lleprint("***Set front long to", self.front_long)

            elif cmdv == 0xD9:
                self._paramcheck(cmdv, params, 2)
                self.front_short = ord(params[0])*256+ord(params[1])
                lleprint("***Set front short to", self.front_short)

            elif cmdv == 0xDA:
                self._paramcheck(cmdv, params, 2)
                self.left_side = ord(params[0])*256+ord(params[1])
                lleprint("***Set left side to", self.left_side)

            elif cmdv == 0xDB:
                self._paramcheck(cmdv, params, 2)
                self.right_side = ord(params[0])*256+ord(params[1])
                lleprint("***Set right side to", self.right_side)

            elif cmdv == 0xDC:
                self._paramcheck(cmdv, params, 2)
                self.left_45 = ord(params[0])*256+ord(params[1])
                lleprint("***Set left 45 to", self.left_45)

            elif cmdv == 0xDD:
                self._paramcheck(cmdv, params, 2)
                self.right_45 = ord(params[0])*256+ord(params[1])
                lleprint("***Set right 45 to", self.right_45)

            elif cmdv == 0xDE:
                self._paramcheck(cmdv, params, 2)
                self.r45_close = ord(params[0])*256+ord(params[1])
                lleprint("***Set r45 close to", self.r45_close)

            elif cmdv == 0xDF:
                self._paramcheck(cmdv, params, 2)
                self.l45_close = ord(params[0])*256+ord(params[1])
                lleprint("***Set l45 close to", self.l45_close)

                
            elif cmdv == 0xf9:
                # write to acceleration table
                self._paramcheck(cmdv, params, 3)
                addr = ord(params[0])
                data = ord(params[1])*256+ord(params[2])
                self.accel_table[addr] = data
                self._wrdata("\xCE")
                self._wrdata_int16(self.accel_table[addr])

            elif cmdv == 0xfA:
                # write to acceleration table
                self._paramcheck(cmdv, params, 3)
                addr = ord(params[0])+256
                data = ord(params[1])*256+ord(params[2])
                self.accel_table[addr] = data
                self._wrdata("\xCE")
                self._wrdata_int16(self.accel_table[addr])
                
            elif cmdv == 0xfe:
                self._paramcheck(cmdv, params, 3)
                if params != "\xfc\xf8\xfe":
                    print("Unexpected unlock")
                    print("EXITING")
                    sys.exit(1)
                if self.locked:
                    self._wrdata("\xC0")
                else:
                    self._wrdata("\xC1")
                    
            else:
                print("Unknown command", hex(cmdv))
                print("EXITING")
                sys.exit(1)
            self._wrdata("\xEF")
            
            self.do_background_processes()
            
        def write(self, data):
            cmdv = data[0]
            # fix for Python 2
            if type(cmdv) is str:
                cmdv = ord(cmdv)
            self._process_cmd(cmdv, data[1:])
        
        def read(self, bytes_to_read):
            self.do_background_processes()
            if bytes_to_read != 1:
                print("bytes to read != 1")
                sys.exit(1)
            if not self.replies:
                return b""
            else:
                return self.replies.popleft()
            
            
            