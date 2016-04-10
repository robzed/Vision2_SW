#
#
from __future__ import print_function

import serial
import time

def main():
    port = serial.Serial("/dev/ttyAMA0", baudrate = 57600, timeout = 2)
    bytes_waiting = port.in_waiting()
    print(bytes_waiting)
    s = port.read(bytes_waiting)
    print(":".join("{:02x}".format(ord(c)) for c in s))

main()

