from __future__ import print_function
from collections import deque
from maze import Maze
import time

PAUSE_ON_MOVE = False

class serial:
    class Serial:
        
        def __init__(self, path, baudrate = 57600, timeout = 0.1):
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


        def do_timers(self):
            if time.time() > self.target_time:
                self.timer_state += 1
                if self.timer_state == 1:
                    self.target_time = time.time() + 0.1
                elif self.timer_state == 2:
                    self._wrdata("\x38")    # A press
                    self.target_time = time.time() + 0.25    # quick press
                elif self.timer_state == 3:
                    self._wrdata("\x30")    # A release
                    self.target_time = time.time() + 1
                elif self.timer_state == 4:
                    self._wrdata("\x39")    # B press
                    self.target_time = time.time() + 2  # hold
                elif self.timer_state == 5:
                    self._wrdata("\x31")    # B release
                    self.target_time = time.time() + 10

        
        def inWaiting(self):
            self.do_timers()
            return len(self.replies)
        
        def _wrdata(self, data):
            if len(data) != 1:
                print("Expected length 1 string - fix in _wrdata() by splitting")
                exit(1)
            self.replies.append(data)
        
        def _paramcheck(self, cmd, params, num_params):
            if len(params) != num_params:
                print("Command", hex(ord(cmd)), "had", len(params), "parameters, not", num_params)
                exit(1)
                
        def _process_cmd(self, cmd, params):
            cmdv = ord(cmd)
            if cmd == "\x20":
                print("***ALL LEDS:", hex(ord(params[0])))
            elif cmd == "\x21":
                self._paramcheck(cmd, params, 1)
                print("***ALL LEDS:", hex(512+ord(params[0])))
            elif cmdv >= 0x10 and cmdv <= 0x19:
                print("*** LED", cmdv&0x0F, "on")
            elif cmdv >= 0x00 and cmdv <= 0x09:
                print("*** LED", cmdv&0x0F, "on")
            elif cmd == "\x80":
                self._paramcheck(cmd, params, 0)
                self._wrdata(cmd)
                
            elif cmd == "\x98":
                self._paramcheck(cmd, params, 0)
                
                if self.IR == False:
                    print("Scanning IR not on - QUITTING")
                    exit(1)

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
                    exit(1)
                    
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
                
            elif cmd == "\xD0":
                self._paramcheck(cmd, params, 0)
                print("*** TURN OFF IR***")
                self.IR = False

            elif cmd == "\xD1":
                self._paramcheck(cmd, params, 0)
                print("*** TURN ON IR***")
                self.IR = True
                
            elif cmd == "\xfe":
                self._paramcheck(cmd, params, 3)
                if params != "\xfc\xf8\xfe":
                    print("Unexpected unlock")
                    print("EXITING")
                    exit(1)
                if self.locked:
                    self._wrdata("\xC0")
                else:
                    self._wrdata("\xC1")
                    
            else:
                print("Unknown command", hex(ord(cmd)))
                print("EXITING")
                exit(1)
            self._wrdata("\xEF")
            
            self.do_timers()
            
        def write(self, data):
            self._process_cmd(data[0], data[1:])
        
        def read(self, bytes_to_read):
            self.do_timers()
            if bytes_to_read != 1:
                print("bytes to read != 1")
                exit(1)
            if not self.replies:
                return ""
            else:
                return self.replies.popleft()
            
    
    