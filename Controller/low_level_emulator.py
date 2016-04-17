from __future__ import print_function
from collections import deque

class serial:
    class Serial:
        def __init__(self, path, baudrate = 57600, timeout = 0.1):
            self.replies = deque()
            self.locked = True
        
        def inWaiting(self):
            return 0
        
        def _wrdata(self, data):
            self.replies.append(data)
        
        def _paramcheck(self, cmd, params, num_params):
            if len(params) != num_params:
                print("Command", hex(ord(cmd)), "had", len(params), "parameters, not", num_params)
                exit(1)
        def _process_cmd(self, cmd, params):
            if cmd == "\x20":
                print("***ALL LEDS:", hex(ord(params[0])))
            elif cmd == "\x21":
                self._paramcheck(cmd, params, 1)
                print("***ALL LEDS:", hex(512+ord(params[0])))
                
            elif cmd == "\x80":
                self._paramcheck(cmd, params, 0)
                self._wrdata(cmd)
                
            elif cmd == "\xC0":
                self._paramcheck(cmd, params, 0)
                print("***STOP MOTORS")
            
            elif cmd == "\xD0":
                self._paramcheck(cmd, params, 0)
                print("*** TURN OFF IR***")
                
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
            
        def write(self, data):
            self._process_cmd(data[0], data[1:])
        
        def read(self, bytes_to_read):
            if bytes_to_read != 1:
                print("bytes to read != 1")
                exit(1)
            if not self.replies:
                return ""
            else:
                return self.replies.popleft()
            
    
    