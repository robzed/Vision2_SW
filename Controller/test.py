#
#
from __future__ import print_function

import serial
import time

def main():
    port = serial.Serial("/dev/ttyAMA0", baudrate = 57600, timeout = 1)
    bytes_waiting = port.inWaiting()
    print(bytes_waiting)
    s = port.read(bytes_waiting)
    print(":".join("{:02x}".format(ord(c)) for c in s))

    port.write(b'\xFE\xFC\xF8\xFE')
    for i in range(3):
        s = port.read(10)
        print(len(s))
        print(":".join("{:02x}".format(ord(c)) for c in s))

    port.write(b'\x80')
    for i in range(3):
        s = port.read(10)
        print(len(s))
        print(":".join("{:02x}".format(ord(c)) for c in s))
        
    port.write(b'\x11\x13')
    for i in range(3):
        s = port.read(10)
        print(len(s))
        print(":".join("{:02x}".format(ord(c)) for c in s))

    while True:
        s = port.read(10)
        print(len(s))
        print(":".join("{:02x}".format(ord(c)) for c in s))
    
main()

