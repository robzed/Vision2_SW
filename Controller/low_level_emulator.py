# -*- coding: utf-8 -*-
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


class intermediate_writer:
    def __init__(self, dest) :
        self.dest = dest
        self.led_text = ""
        self.led_print = False
        self.led_end = time.time() + 1
        
    def write(self, text) :
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
            self.keys = KeyThread()
            self.key_delayed = None
            
            self.timeout = timeout
            self.LEDs = [".", ".", ".", ".", ".", ".", ".", ".", "."]
            self.last_LEDs = ""
            
            self.shift_middle()
            
            self.accel_table = [0]*512

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
            LEDs = "%s   %s< ^%s >%s" % ("".join(self.LEDs[0:6])[::-1], LED7, LED8, LED9)
            if LEDs != self.last_LEDs:
                self.iw.start_led_print()
                print(LEDs)
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
                    print("*** Mouse a bit left")
                    self.shift_left()
                elif key == ">":
                    print("*** Mouse a bit right")
                    self.shift_right()
                #elif key == "|":
                #    pass
                elif key == "^":
                    print("*** Mouse far away from front wall")
                    self.shift_far()
                elif key == "+":
                    print("*** Mouse centered, in same cell as front wall")
                    self.shift_middle()
                elif key == "P":
                    # pause on move
                    PAUSE_ON_MOVE = not PAUSE_ON_MOVE
                elif key == '\x13' or '\x10':
                    pass
                else:
                    print("??? Didn't understand", key)
    
        def inWaiting(self):
            self.do_background_processes()
            return len(self.replies)
        
        def _wrdata(self, data):
            if len(data) != 1:
                print("Expected length 1 string - fix in _wrdata() by splitting")
                sys.exit(1)
            self.replies.append(data)
        
        def _wrdata_int16(self, data):
            self._wrdata(chr(data>>8))
            self._wrdata(chr(data&255))
            
        def _paramcheck(self, cmd, params, num_params):
            if len(params) != num_params:
                print("Command", hex(ord(cmd)), "had", len(params), "parameters, not", num_params)
                sys.exit(1)
                
        def _process_cmd(self, cmd, params):
            cmdv = ord(cmd)
            if cmd == "\x20" or cmd == "\x21":
                self._paramcheck(cmd, params, 1)
                LEDmask = ord(params[0])
                if cmd == "\x21": LEDmask += 512
                print("***ALL LEDS:", hex(LEDmask))
                for n in range(1,10):
                    if LEDmask&1:
                        self.set_LED(n)
                    else:
                        self.clear_LED(n)
                    LEDmask >>= 1
                
            elif cmdv >= 0x10 and cmdv <= 0x19:
                LEDnum = cmdv&0x0F
                #print("*** LED", LEDnum, "on")
                self.set_LED(LEDnum)
                self.show_LEDs()
            elif cmdv >= 0x00 and cmdv <= 0x09:
                LEDnum = cmdv&0x0F
                #print("*** LED", LEDnum, "off")
                self.clear_LED(LEDnum)
                self.show_LEDs()
            elif cmd == "\x80":
                self._paramcheck(cmd, params, 0)
                self._wrdata(cmd)
                
            elif cmd == "\x98":
                self._paramcheck(cmd, params, 0)
                
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
                    print("       ___")
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
                    print("       |", end="")
                else:
                    print("        ", end="")
                if self.maze.get_right_wall(self.heading, self.row, self.column):
                    value += 0x08
                    print("  |")
                else:
                    print(" ")
                
                #print("*** value", value & 0x0f)
                
                self._wrdata(chr(value))
            
            elif cmd == "\x9A": # front
                self._paramcheck(cmd, params, 0)
                self._wrdata("\x61")
                self._wrdata(chr(self.front>>8))
                self._wrdata(chr(self.front&255))

            elif cmd == "\x9B": # l90
                self._paramcheck(cmd, params, 0)
                self._wrdata("\x62")
                self._wrdata(chr(self.ls>>8))
                self._wrdata(chr(self.ls&255))
            
            elif cmd == "\x9C": # l45
                self._paramcheck(cmd, params, 0)
                self._wrdata("\x63")
                self._wrdata(chr(self.l45>>8))
                self._wrdata(chr(self.l45&255))
            
            elif cmd == "\x9D": # r90
                self._paramcheck(cmd, params, 0)
                self._wrdata("\x64")
                self._wrdata(chr(self.rs>>8))
                self._wrdata(chr(self.rs&255))
            
            elif cmd == "\x9E": # r45
                self._paramcheck(cmd, params, 0)
                self._wrdata("\x65")
                self._wrdata(chr(self.r45>>8))
                self._wrdata(chr(self.r45&255))
            
            elif cmd == "\xC0":
                self._paramcheck(cmd, params, 0)
                print("***STOP MOTORS")

            elif cmd == "\xC1":
                self._paramcheck(cmd, params, 2)
                distance_value = ord(params[0])*256+ord(params[1])
                print("***FORWARD!", distance_value)
                
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
                
                print("***Position (%d, %d) Heading %d" % (self.row, self.column, self.heading))
                self._wrdata("\x20")

            elif cmd == "\xC2": # right
                self._paramcheck(cmd, params, 2)
                distance_value = ord(params[0])*256+ord(params[1])
                if distance_value > 180:
                    print("***U-TURN!", distance_value)
                    self.heading = 3 & (self.heading + 2)
                else:
                    print("***RIGHT!", distance_value)
                    self.heading = 3 & (self.heading + 1)
 
                if PAUSE_ON_MOVE:
                    time.sleep(0.5)
               
                print("***Position (%d, %d) Heading %d" % (self.row, self.column, self.heading))
                self._wrdata("\x20")

            elif cmd == "\xC3": # left
                self._paramcheck(cmd, params, 2)
                distance_value = ord(params[0])*256+ord(params[1])
                if distance_value > 180:
                    print("***U-TURN!", distance_value)
                    self.heading = 3 & (self.heading + 2)
                else:
                    print("***LEFT!", distance_value)
                    self.heading = 3 & (self.heading - 1)

                if PAUSE_ON_MOVE:
                    time.sleep(0.5)

                print("***Position (%d, %d) Heading %d" % (self.row, self.column, self.heading))

                self._wrdata("\x20")
                
            elif cmd == "\xC4":
                self._paramcheck(cmd, params, 2)
                print("***Set speed to", ord(params[0])*256+ord(params[1]))
            
            elif cmd == "\xC5":
                self._paramcheck(cmd, params, 2)
                self.steering_correction = ord(params[0])*256+ord(params[1])
                print("***Set Steering correction to", self.steering_correction)

            elif cmd == "\xC6":
                self._paramcheck(cmd, params, 0)
                print("***Extend Movement!")
                
            elif cmd == "\xC7":
                self._paramcheck(cmd, params, 2)
                self.cell_distance = ord(params[0])*256+ord(params[1])
                print("***Set Cell distance to", self.cell_distance)

            elif cmd == "\xC8":
                self._paramcheck(cmd, params, 2)
                self.wall_correction = ord(params[0])*256+ord(params[1])
                print("***Set Wall edge correction to", self.wall_correction)

            elif cmd == "\xC9":
                self._paramcheck(cmd, params, 2)
                self.distance_to_test = ord(params[0])*256+ord(params[1])
                print("***Set distance test to", self.distance_to_test)
                print("*** >>>>Not complete yet! <<<<")

            elif cmd == "\xCF":
                self._paramcheck(cmd, params, 1)
                subcmd = ord(params[0])
                self._wrdata(str(cmd))
                self._wrdata(params[0])
                if subcmd == 0xC5:
                    self._wrdata_int16(self.steering_correction)
                elif subcmd == 0xC7:
                    self._wrdata_int16(self.cell_distance)
                elif subcmd == 0xC8:
                    self._wrdata_int16(self.wall_correction)
                elif subcmd == 0xC9:
                    self._wrdata_int16(self.distance_to_test)
                
            elif cmd == "\xD0":
                self._paramcheck(cmd, params, 0)
                print("*** TURN OFF IR***")
                self.IR = False

            elif cmd == "\xD1":
                self._paramcheck(cmd, params, 0)
                print("*** TURN ON IR***")
                self.IR = True

            elif cmd == "\xD8":
                self._paramcheck(cmd, params, 2)
                self.front_long = ord(params[0])*256+ord(params[1])
                print("***Set front long to", self.front_long)

            elif cmd == "\xD9":
                self._paramcheck(cmd, params, 2)
                self.front_short = ord(params[0])*256+ord(params[1])
                print("***Set front short to", self.front_short)

            elif cmd == "\xDA":
                self._paramcheck(cmd, params, 2)
                self.left_side = ord(params[0])*256+ord(params[1])
                print("***Set left side to", self.left_side)

            elif cmd == "\xDB":
                self._paramcheck(cmd, params, 2)
                self.right_side = ord(params[0])*256+ord(params[1])
                print("***Set right side to", self.right_side)

            elif cmd == "\xDC":
                self._paramcheck(cmd, params, 2)
                self.left_45 = ord(params[0])*256+ord(params[1])
                print("***Set left 45 to", self.left_45)

            elif cmd == "\xDD":
                self._paramcheck(cmd, params, 2)
                self.right_45 = ord(params[0])*256+ord(params[1])
                print("***Set right 45 to", self.right_45)

            elif cmd == "\xDE":
                self._paramcheck(cmd, params, 2)
                self.r45_close = ord(params[0])*256+ord(params[1])
                print("***Set r45 close to", self.r45_close)

            elif cmd == "\xDF":
                self._paramcheck(cmd, params, 2)
                self.l45_close = ord(params[0])*256+ord(params[1])
                print("***Set l45 close to", self.l45_close)

                
            elif cmd == "\xf9":
                # write to acceleration table
                self._paramcheck(cmd, params, 3)
                addr = ord(params[0])
                data = ord(params[1])*256+ord(params[2])
                self.accel_table[addr] = data
                self._wrdata("\xCE")
                self._wrdata_int16(self.accel_table[addr])

            elif cmd == "\xfA":
                # write to acceleration table
                self._paramcheck(cmd, params, 3)
                addr = ord(params[0])+256
                data = ord(params[1])*256+ord(params[2])
                self.accel_table[addr] = data
                self._wrdata("\xCE")
                self._wrdata_int16(self.accel_table[addr])
                
            elif cmd == "\xfe":
                self._paramcheck(cmd, params, 3)
                if params != "\xfc\xf8\xfe":
                    print("Unexpected unlock")
                    print("EXITING")
                    sys.exit(1)
                if self.locked:
                    self._wrdata("\xC0")
                else:
                    self._wrdata("\xC1")
                    
            else:
                print("Unknown command", hex(ord(cmd)))
                print("EXITING")
                sys.exit(1)
            self._wrdata("\xEF")
            
            self.do_background_processes()
            
        def write(self, data):
            self._process_cmd(data[0], data[1:])
        
        def read(self, bytes_to_read):
            self.do_background_processes()
            if bytes_to_read != 1:
                print("bytes to read != 1")
                sys.exit(1)
            if not self.replies:
                return ""
            else:
                return self.replies.popleft()
            
            
            