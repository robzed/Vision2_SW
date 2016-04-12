#
#
from __future__ import print_function

import serial
import time

def message_into_hex(s):
    return ":".join("{:02x}".format(ord(c)) for c in s)

def send_unlock_command(port):
    print("Send Unlock")
    port.write(b'\xFE\xFC\xF8\xFE')



def send_poll_command(port):
    print("Send Poll")
    port.write(b'\x80')

def wait_for_poll_repl(port):
    s = port.read(1)
    if s == '\x80':
        print("> Got Poll answer")
    elif len(s) == 0:
        print("No message received at all")
    else:
        print("Got", message_into_hex(s))


def send_switch_led_command(port, led, on):
    if on:
        command = 0x10 + led
        print("Switch LED", led, "on")
    else:
        print("Switch LED", led, "off")
        command = 0x00 + led

    port.write(chr(command))

def move_forward(port, distance):
    s = "\xC1" + chr(distance >> 8) + chr(distance & 0xff)
    port.write(s)

def move_right(port, distance):
    s = "\xC2" + chr(distance >> 8) + chr(distance & 0xff)
    port.write(s)

def move_left(port, distance):
    s = "\xC3" + chr(distance >> 8) + chr(distance & 0xff)
    port.write(s)

def turn_on_ir(port):
    port.write("\xD1")
    
def turn_off_ir(port):
    port.write("\xD0")

################################################
    
def recover_from_major_error(): #(port):
    exit(1)

def EV_UKNNOWN_RESET(port, cmd):
    print("Unknown Reset")
    recover_from_major_error()
def EV_POWER_ON_RESET(port, cmd):
    print("Power On Reset")
    recover_from_major_error()
def EV_BROWN_OUT_RESET(port, cmd):
    print("Brown Out Reset")
    recover_from_major_error()
def EV_WATCHDOG_RESET(port, cmd):
    print("Watchdog Reset")
    recover_from_major_error()
def EV_SOFTWARE_RESET(port, cmd):
    print("Software Reset")
    recover_from_major_error()
def EV_EXTERNAL_RESET(port, cmd):
    print("External Reset")
    recover_from_major_error()
def EV_EXCEPTION_RESET(port, cmd):
    print("Exception Reset")
    recover_from_major_error()


def EV_BATTERY_VOLTAGE(port, cmd):
    ADC_reading = port.read(1)
    if len(ADC_reading == 0):
        print("Didn't get second byte of battery voltage")
        recover_from_major_error()
    elif len(ADC_reading > 1):
        print("More than one byte in voltage")
        recover_from_major_error()

    ADC_reading = ord(ADC_reading) + (cmd & 0x03)

    # potential divider is 33K and 12K. This does into an ADC where the reference is approx. 5v.
    voltage = 5 * 12000 * (ADC_reading / (33000+12000))
    print("Approximate battery voltage = ", voltage)

def EV_FINISHED_MOVE(port, cmd):
    print("Got move finished")

def EV_UNLOCK_FROM_LOCK(port, cmd):
    print("Got unlock from lock")

def EV_UNLOCK_FROM_UNLOCK(port, cmd):
    print("Got unlock from unlock")

def EV_LOCK_BY_TIMER(port, cmd):
    print("Got lock by timer")
    recover_from_major_error()

def EV_LOCK_BY_COMMAND(port, cmd):
    print("Got lock by command")
    recover_from_major_error()

def EV_POLL_REPLY(port, cmd):
    print("Got poll reply")

def EV_FAIL_INVALID_COMMAND(port, cmd):
    print("Got innvalid command")
    recover_from_major_error()
    
command_handlers = {
    0x00: EV_UKNNOWN_RESET,
    0x01: EV_POWER_ON_RESET,
    0x02: EV_BROWN_OUT_RESET,
    0x03: EV_WATCHDOG_RESET,
    0x04: EV_SOFTWARE_RESET,
    0x05: EV_EXTERNAL_RESET,
    0x06: EV_EXCEPTION_RESET,

    0x10: EV_BATTERY_VOLTAGE,
    0x11: EV_BATTERY_VOLTAGE,
    0x12: EV_BATTERY_VOLTAGE,
    0x13: EV_BATTERY_VOLTAGE,
    0x20: EV_FINISHED_MOVE,


    # unlocking
    0xC0: EV_UNLOCK_FROM_LOCK,
    0xC1: EV_UNLOCK_FROM_UNLOCK,
    0xC2: EV_LOCK_BY_TIMER,
    0xC3: EV_LOCK_BY_COMMAND,

    0x80: EV_POLL_REPLY,

    0xE2: EV_FAIL_INVALID_COMMAND,
}

def event_processor(port):
    cmd = port.read(1)
    if len(cmd) == 0:
        # no packet in timeout...
        return
    cmd = ord(cmd)
    if cmd in command_handlers:
        command_handlers[cmd](port, cmd)
    else:
        print("Unknown event", hex(cmd), "ignoring")
        #recover_from_major_error()

distance_cell	= 347			# adjust these values for cell distance		
distance_turnl90	= 112		# turn left 90deg
distance_turnr90	= 112		# turn right 90deg
distance_turn180 = 224		# turn 180deg

def main():
    port = serial.Serial("/dev/ttyAMA0", baudrate = 57600, timeout = 0.2)
    bytes_waiting = port.inWaiting()
    print(bytes_waiting)
    s = port.read(bytes_waiting)
    print(":".join("{:02x}".format(ord(c)) for c in s))

    send_unlock_command(port)
    for i in range(3):
        event_processor(port)

    send_poll_command(port)
    for i in range(3):
        event_processor(port)

    send_switch_led_command(port, 1, True)
    for i in range(3):
        event_processor(port)

    turn_on_ir(port)
    for i in range(3):
        event_processor(port)

    move_forward(port, 4*347)
    for i in range(3):
        event_processor(port)

    turn_off_ir(port)
    for i in range(3):
        event_processor(port)

    move_right(port, distance_turn180)
    for i in range(3):
        event_processor(port)

    turn_on_ir(port)
    for i in range(3):
        event_processor(port)

    move_forward(port, 347)
    for i in range(3):
        event_processor(port)

    turn_off_ir(port)
    for i in range(3):
        event_processor(port)

    move_left(port, distance_turnl90)
    for i in range(3):
        event_processor(port)

    send_switch_led_command(port, 3, True)
    for i in range(3):
        event_processor(port)

    while True:
        event_processor(port)
    
main()

