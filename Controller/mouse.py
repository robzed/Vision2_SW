#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import print_function
from __builtin__ import True, False

################################################################
# NORMAL MODE
#
# LED 1 = size 5 maze selected
# LED 2 = size 16 maze selected
#            Both = Calibration mode
#            None = Test mode
# LED 3 = running

# LED 4 = flashing = Failed to Solve
# LED 5 = shutdown running
# LED 6 = Slow flash if running
#         Fast flash if battery problem (going to shutdown soon)
#
# Button A - select between 5, 16 and calibration
# Hold Button B - select/start
#
################################################################
# CALIBRATION MODE
#
# LED 321 = 1 (001) = left close (1cm away)
# LED 321 = 2 (010) = middle
# LED 321 = 3 (011) = right close (1cm away)
# LED 321 = 4 (100) = front same cell
# LED 321 = 5 (101) = front long cell
# LED 321 = 6 (110) = test
# LED 321 = 7 (111) = test + save (save when pressed again)
#
# LED 4 = flashing while in test mode
# LED 5 = shutdown running
# LED 6 = Slow flash if running
#         Fast flash if battery problem (going to shutdown soon)
#
# Button A - next calibration mode
# Button B - abort (without saving, put readings back to previous)
#
################################################################
# TEST MODE
# 
# LED1/LED2 = Flashing
# LED3/LED4 = mode (0=straight, 3=right, 4=left)
#

import sys
if len(sys.argv) == 2 and sys.argv[1] == "SIMULATOR":
    SIMULATOR = True
else:
    SIMULATOR = False

if SIMULATOR:
    from low_level_emulator import serial   #@UnusedImport
else:
    import serial   #@UnresolvedImport @Reimport

import time
from collections import deque
import os
from maze import Maze
import datetime

################################################################
# 
# Constants
# 

verbose = False
print_map_in_progress = True

distance_cell	= 347			# adjust these values for cell distance		
distance_turnl90	= 112		# turn left 90deg
distance_turnr90	= 112		# turn right 90deg
distance_turn180 = 224		    # turn 180deg
wall_edge_correction_factor = 162 # previously 230

HOLD_KEY_TIME = 1.5     # seconds

BATT_VOLTAGE_PER_CELL_WARNING = 3.9
BATTERY_VOLTAGE_WARNING = (4 * BATT_VOLTAGE_PER_CELL_WARNING)
BATT_VOLTAGE_PER_CELL_SHUTDOWN = 3.6
BATTERY_VOLTAGE_SHUTDOWN = (4 * BATT_VOLTAGE_PER_CELL_SHUTDOWN)
BATT_VOLTAGE_COUNT = 30      # scans to register level

log_battery_voltage = True
now_string = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
battery_filename = "battery_%s.txt" % now_string

################################################################
# 
# Module-level Variables
#

#port = None
move_finished = False
battery_voltage = 17

maze_selected = 5   # should be 5 or 16

keys_in_queue = deque()

battery_voltage_mode = 0 # 0 = ok, 1 = low voltage, 2 = shutdown
battery_voltage_count = BATT_VOLTAGE_COUNT

battery_voltage_array = []

################################################################
# 
# Exceptions
# 

class SoftReset(Exception):
    pass

class ShutdownRequest(Exception):
    pass

class MajorError(Exception):
    pass

################################################################
# 
# General functions
# 
def recover_from_major_error():
    print()
    print("Major error - aborting")
    # @todo: some something better to recover
    raise MajorError


# define timer function
# Need to test time.time against datetime.utcnow() or date.now() on RPi
read_accurate_time = time.time


################################################################
# 
# Transmit Management
# 


sent_bytes_in_flight = 0
messages_in_flight_queue = deque()
flight_queue_full = False

def send_message(port, message):
    global sent_bytes_in_flight
    global message_in_flight_queue
    
    ml = len(message)

    # run as many as we can until we are empty
    while port.inWaiting():
        event_processor(port)
    
    if sent_bytes_in_flight + ml > 4:
        print(">", ml, sent_bytes_in_flight)
        
    end_time = time.time() + 0.1
    while (ml + sent_bytes_in_flight) > 4:
        global flight_queue_full
        flight_queue_full = True
        event_processor(port)
        flight_queue_full = False
        if time.time() > end_time:
            print("Waited for response - we should do something")
            end_time = time.time() + 1

    sent_bytes_in_flight += ml
    messages_in_flight_queue.append(ml)
    port.write(message)


def acknowledge_send(port, cmd):
    global sent_bytes_in_flight
    global message_in_flight_queue

    try:
        count = messages_in_flight_queue.popleft()
    except IndexError:
        print("Got acknowledge send without anything in message_in_flight_queue - Ignoring")
        count = 0
        #recover_from_major_error()

    sent_bytes_in_flight -= count

def reset_message_queue():
    global sent_bytes_in_flight
    global message_in_flight_queue

    sent_bytes_in_flight = 0
    messages_in_flight_queue = deque()

################################################################
# 
# Commands to Send
# 

def message_into_hex(s):
    return ":".join("{:02x}".format(ord(c)) for c in s)

def send_unlock_command(port):
    if verbose: print("Send Unlock")
    send_message(port, b'\xFE\xFC\xF8\xFE')


def send_poll_command(port):
    if verbose: print("Send Poll")
    send_message(port, b'\x80')

#def wait_for_poll_repl(port):
#    s = port.read(1)
#    if s == '\x80':
#        if verbose: print("> Got Poll answer")
#    elif len(s) == 0:
#        print("For Poll Reply: No message received at all")
#    else:
#        print("For Poll Reply: Got", message_into_hex(s))


def send_switch_led_command(port, led, on):
    if on:
        command = 0x10 + led
        #if verbose: print("Switch LED", led, "on")
    else:
        #if verbose: print("Switch LED", led, "off")
        command = 0x00 + led

    send_message(port, chr(command))


def send_led_pattern_command(port, led_states):
    # 0x20 = CMD_TYPE_ALL_LEDS - extra byte (leds 1-8, led 9-bit 0 of cmd byte)
    leds_1to8 = chr(led_states & 0xFF)
    cmd_and_led_9 = chr(0x20 + ((led_states >> 8) & 1))
    send_message(port, cmd_and_led_9 + leds_1to8)

def turn_off_all_LEDs(port):
    send_led_pattern_command(port, 0);

    
def turn_off_motors(port):
    if verbose: print("Turn off motors")
    send_message(port, "\xC0")

def move_forward(port, distance):
    global move_finished
    move_finished = False
    
    if verbose: print("Forward")
    s = "\xC1" + chr(distance >> 8) + chr(distance & 0xff)
    send_message(port, s)

def move_right(port, distance):
    global move_finished
    move_finished = False
    
    if verbose: print("right")
    s = "\xC2" + chr(distance >> 8) + chr(distance & 0xff)
    send_message(port, s)

def move_left(port, distance):
    global move_finished
    move_finished = False
    
    if verbose: print("left")
    s = "\xC3" + chr(distance >> 8) + chr(distance & 0xff)
    send_message(port, s)

def turn_on_ir(port):
    if verbose: print("IR on")
    send_message(port, "\xD1")
    
def turn_off_ir(port):
    if verbose: print("IR off")
    send_message(port, "\xD0")


def set_speed(port, speed):
    if verbose: print("set speed", speed)
    s = "\xC4" + chr(speed >> 8) + chr(speed & 0xff)
    send_message(port, s)

def send_get_wall_info(port):
    if verbose: print("Get wall IR")
    send_message(port, "\x98")

def send_get_45_sensor_info(port):
    if verbose: print("Get 45 IR")
    send_message(port, "\x99")

def get_front_level(port):
    send_message(port, "\x9A")

def get_l90_level(port):
    send_message(port, "\x9B")

def get_l45_level(port):
    send_message(port, "\x9C")

def get_r90_level(port):
    send_message(port, "\x9D")

def get_r45_level(port):
    send_message(port, "\x9E")


def set_steering_correction(port, distance):
    if verbose: print("set steering correction distance", distance)
    s = "\xC5" + chr(distance >> 8) + chr(distance & 0xff)
    send_message(port, s)

def extend_movement(port):
    if verbose: print("extent movement")
    send_message(port, "\xC6")

def set_cell_distance(port, distance):
    if verbose: print("set_cell_distance", distance)
    s = "\xC7" + chr(distance >> 8) + chr(distance & 0xff)
    send_message(port, s)

def set_wall_edge_correction(port, distance):
    if verbose: print("set_wall_edge_correction", distance)
    s = "\xC8" + chr(distance >> 8) + chr(distance & 0xff)
    send_message(port, s)

def set_distance_to_test(port, distance):
    if verbose: print("set_distance_to_test", distance)
    s = "\xC9" + chr(distance >> 8) + chr(distance & 0xff)
    send_message(port, s)


#
# IR commands
#
def set_front_long_threshold(port, threshold):
    if verbose: print("set_front_long_threshold", threshold)
    s = "\xD8" + chr(threshold >> 8) + chr(threshold & 0xff)
    send_message(port, s)

def set_front_short_threshold(port, threshold):
    if verbose: print("set_front_short_threshold", threshold)
    s = "\xD9" + chr(threshold >> 8) + chr(threshold & 0xff)
    send_message(port, s)

def set_left_side_threshold(port, threshold):
    if verbose: print("set_left_side_threshold", threshold)
    s = "\xDA" + chr(threshold >> 8) + chr(threshold & 0xff)
    send_message(port, s)

def set_right_side_threshold(port, threshold):
    if verbose: print("set_right_side_threshold", threshold)
    s = "\xDB" + chr(threshold >> 8) + chr(threshold & 0xff)
    send_message(port, s)

def set_left_45_threshold(port, threshold):
    if verbose: print("set_left_45_threshold", threshold)
    s = "\xDC" + chr(threshold >> 8) + chr(threshold & 0xff)
    send_message(port, s)

def set_right_45_threshold(port, threshold):
    if verbose: print("set_right_45_threshold", threshold)
    s = "\xDD" + chr(threshold >> 8) + chr(threshold & 0xff)
    send_message(port, s)

def set_left_45_too_close_threshold(port, threshold):
    if verbose: print("set_left_45_too_close_threshold", threshold)
    s = "\xDE" + chr(threshold >> 8) + chr(threshold & 0xff)
    send_message(port, s)

def set_right_45_too_close_threshold(port, threshold):
    if verbose: print("set_right_45_too_close_threshold", threshold)
    s = "\xDF" + chr(threshold >> 8) + chr(threshold & 0xff)
    send_message(port, s)



def set_default_distances(port):
    #set_speed(port, speed)
    set_steering_correction(port, 10)           # might need to fixed for higher speeds
    set_cell_distance(port, distance_cell)      # 
    set_wall_edge_correction(port, wall_edge_correction_factor)
    set_distance_to_test(port, 300)


################################################################
# 
# Time Management
#
# Non-real-time timer...
#

list_of_events = []
timer_next_end_time = read_accurate_time()+1
battery_count = 10

def add_event(function, repeating=False):
    pass


execution_state_LED6 = True

def run_timers(port):
    global timer_next_end_time
    time_now = read_accurate_time()
    if time_now > timer_next_end_time:
        
        # notice: time slip possible here, no 'catchup' attempted.
        timer_next_end_time = read_accurate_time()
        
        global battery_voltage_mode
        if battery_voltage_mode == 0:
            # no problem
            timer_next_end_time += 1
        else:
            # fast flash if problem
            timer_next_end_time += 0.125

        # only do this if we are not running full already...
        if not flight_queue_full and not SIMULATOR:
            # we hard code a function here, for the moment
            global execution_state_LED6
            send_switch_led_command(port, 6, execution_state_LED6)
            execution_state_LED6 = not execution_state_LED6

        global battery_count
        battery_count -= 1
        if battery_count <= 0:
                print("Batt V", battery_voltage, "cell:", battery_voltage/4.0)
                battery_count = 10

################################################################
# 
# Recieved Event Functions
# 
def EV_UNKNOWN_RESET(port, cmd):
    print("Unknown Reset")
    raise SoftReset
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
    raise SoftReset

def EV_EXCEPTION_RESET(port, cmd):
    print("Exception Reset")
    recover_from_major_error()


# approximately 5v. 1024 steps (1024=max). Multiplier for potential divider.

Vfeed = 5.0
Aref_voltage = 5.0 * 0.95
battery_voltage_conversion = Aref_voltage * (33000+12000) / 12000 / 1023


def EV_BATTERY_VOLTAGE(port, cmd):
    ADC_reading = port.read(1)
    ADClen = len(ADC_reading)
    if ADClen == 0:
        print("Didn't get second byte of battery voltage")
        recover_from_major_error()
    elif ADClen > 1:
        print("More than one byte in voltage")
        recover_from_major_error()

    ADC_reading = ord(ADC_reading) + 256 * (cmd & 0x03)

    # potential divider is 33K and 12K. This does into an ADC where the reference is approx. 5v.
    global battery_voltage_conversion
    global battery_voltage
    battery_voltage = ADC_reading * battery_voltage_conversion
    #print("Batt V", voltage, "cell:", voltage/4)
    
    
    # figure out the warnings and 
    global BATTERY_VOLTAGE_SHUTDOWN
    global BATTERY_VOLTAGE_WARNING
    global battery_voltage_mode
    global battery_voltage_count
    global BATT_VOLTAGE_COUNT
    global log_battery_voltage
    global battery_voltage_array
    if log_battery_voltage:
        battery_voltage_array.append( (time.time(), battery_voltage) )
        if len(battery_voltage_array) == 200:
            with open(battery_filename, "a") as f:
                for item in battery_voltage_array:
                    f.write("%f, %s\n" % (item[0], item[1]))
            battery_voltage_array = []
    potential_mode = 0
    if battery_voltage <= BATTERY_VOLTAGE_WARNING:
        potential_mode = 1
        if battery_voltage <= BATTERY_VOLTAGE_SHUTDOWN:
            potential_mode = 2

        # we only go one way... don't allow increases to 
        # reset the warnings or shutdown!
        if  potential_mode > battery_voltage_mode:
            battery_voltage_count -= 1
            if battery_voltage_count <= 0:
                # become a higher mode
                # two passes are required to reach shutdown!
                battery_voltage_mode += 1
                battery_voltage_count = BATT_VOLTAGE_COUNT
                # shutdown the Raspberry Pi
                if battery_voltage_mode == 1:
                    print("Battery Low.      Batt V", battery_voltage, "cell:", battery_voltage/4.0)
                elif battery_voltage_mode == 2:
                    raise ShutdownRequest
        else:
            battery_voltage_count = BATT_VOLTAGE_COUNT



ir_front_level = 0
ir_front_level_new = False

def EV_IR_FRONT_LEVEL(port, cmd):
    global ir_front_level
    global ir_front_level_new
    ir_front_level = ord(port.read(1))*256
    ir_front_level += ord(port.read(1))
    if verbose: print("IR Front level", ir_front_level)
    ir_front_level_new = True

ir_l90_level = 0
ir_l90_level_new = False
    
def EV_L90_LEVEL(port, cmd):
    global ir_l90_level
    global ir_l90_level_new
    ir_l90_level = ord(port.read(1))*256
    ir_l90_level += ord(port.read(1))
    if verbose: print("IR L90 level", ir_l90_level)
    ir_l90_level_new = True

ir_l45_level = 0
ir_l45_level_new = False
    
def EV_L45_LEVEL(port, cmd):
    global ir_l45_level
    global ir_l45_level_new
    ir_l45_level = ord(port.read(1))*256
    ir_l45_level += ord(port.read(1))
    if verbose: print("IR L45 level", ir_l45_level)
    ir_l45_level_new = True
    
ir_r90_level = 0
ir_r90_level_new = False

def EV_R90_LEVEL(port, cmd):
    global ir_r90_level
    global ir_r90_level_new
    ir_r90_level = ord(port.read(1))*256
    ir_r90_level += ord(port.read(1))
    if verbose: print("IR R90 level", ir_r90_level)
    ir_r90_level_new = True
    
ir_r45_level = 0
ir_r45_level_new = False

def EV_R45_LEVEL(port, cmd):
    global ir_r45_level
    global ir_r45_level_new
    ir_r45_level = ord(port.read(1))*256
    ir_r45_level += ord(port.read(1))
    if verbose: print("IR R45 level", ir_r45_level)
    ir_r45_level_new = True



def EV_FINISHED_MOVE(port, cmd):
    global move_finished
    move_finished = True
    print("Got move finished")

locked = True

def EV_UNLOCK_FROM_LOCK(port, cmd):
    print("Got unlock from lock")
    global locked
    locked = False

def EV_UNLOCK_FROM_UNLOCK(port, cmd):
    print("Got unlock from unlock")
    global locked
    locked = False

def EV_LOCK_BY_TIMER(port, cmd):
    print("Got lock by timer - NOT HANDLED")
    recover_from_major_error()
    global locked
    locked = True
    # @todo: We should issue unlock here, immediately!

def EV_LOCK_BY_COMMAND(port, cmd):
    print("Got lock by command - NOT HANDLED")
    recover_from_major_error()
    global locked
    locked = True
    # @todo: We should issue unlock here, immediately!


def EV_POLL_REPLY(port, cmd):
    print("Got poll reply")

def EV_FAIL_INVALID_COMMAND(port, cmd):
    print("Got invalid command")
    recover_from_major_error()

#def EV_GOT_INSTRUCTION(port, cmd):
#    acknowledge_send()

key_A_start_time = None
key_B_start_time = None

def EV_BUTTON_A_RELEASE(port, cmd):
    global key_A_start_time
    if key_A_start_time == None:
        # no press, ignore release
        return
    #print("KEY A TIME =", read_accurate_time() - key_A_start_time)
    # hold key or normal key?
    if (read_accurate_time() - key_A_start_time) > HOLD_KEY_TIME:
        keys_in_queue.append('A')
        if verbose: print("held A")
    else:
        keys_in_queue.append('a')
        if verbose: print("press A")
        
    key_A_start_time = None

def EV_BUTTON_B_RELEASE(port, cmd):
    global key_B_start_time
    if key_B_start_time == None:
        # no press, ignore release
        return
    #print("KEY B TIME =", read_accurate_time() - key_B_start_time)
    # hold key or normal key?
    if (read_accurate_time() - key_B_start_time) > HOLD_KEY_TIME:
        keys_in_queue.append('B')
        if verbose: print("held B")
    else:
        keys_in_queue.append('b')
        if verbose: print("press B")

    key_B_start_time = None

def EV_BUTTON_A_PRESS(port, cmd):
    global key_A_start_time
    key_A_start_time = read_accurate_time()
    
def EV_BUTTON_B_PRESS(port, cmd):
    global key_B_start_time
    key_B_start_time = read_accurate_time()

got_wall_info = False
left_wall_sense = False
right_wall_sense = False
front_short_wall_sense = False
front_long_wall_sense = False

#EV_IR_FRONT_SIDE_STATE  0x40        // bit 0 = front long
#                                    // bit 1 = front short
#                                    // bit 2 = left side
#                                    // bit 3 = right side
def EV_IR_FRONT_SIDE_STATE(port, cmd):
    global got_wall_info
    global left_wall_sense
    global right_wall_sense
    global front_short_wall_sense
    global front_long_wall_sense
    left_wall_sense = cmd&4
    right_wall_sense = cmd&8
    front_short_wall_sense = cmd&2
    front_long_wall_sense = cmd&1
    got_wall_info = True


got_45_info = False
left_45_sense = False
right_45_sense = False
left_45_too_close_sense = False
right_45_too_close_sense = False

# define EV_IR_45_STATE          0x50        // bit 0 = left 45
#                                           // bit 1 = right 45
#                                           // bit 2 = left 45 too close
#                                           // bit 3 = right 45 too close
def EV_IR_45_STATE(port, cmd):
    global got_45_info
    global left_45_sense
    global right_45_sense
    global left_45_too_close_sense
    global right_45_too_close_sense
    left_45_sense = cmd & 1
    right_45_sense = cmd & 2
    left_45_too_close_sense = cmd & 4
    right_45_too_close_sense = cmd & 8
    got_45_info = True


"""
def EV_IR_FRONT_SIDE_STATE_0(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return False, False, False, False  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_1(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return False, False, False, True  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_2(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return False, True, False, False  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_3(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return False, True, False, True  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_4(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return True, False, False, False  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_5(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return True, False, False, True  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_6(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return True, True, False, False  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_7(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return True, True, False, True  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_8(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return False, False, True, False  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_9(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return False, False, True, True  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_A(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return False, True, True, False  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_B(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return False, True, True, True  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_C(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return True, False, True, False  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_D(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return True, False, True, True  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_E(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return True, True, True, False  # cmd&4, cmd&2, cmd&8, cmd&1

def EV_IR_FRONT_SIDE_STATE_F(port, cmd):
    # we use short sensor for wall measurement
    # left, front, right, front_long
    return True, True, True, True  # cmd&4, cmd&2, cmd&8, cmd&1
"""

################################################################
# 
# Event Processor 
# 
    
command_handlers = {
    0x00: EV_UNKNOWN_RESET,
    0x01: EV_POWER_ON_RESET,
    0x02: EV_BROWN_OUT_RESET,
    0x03: EV_WATCHDOG_RESET,
    0x04: EV_SOFTWARE_RESET,
    0x05: EV_EXTERNAL_RESET,
    0x06: EV_EXCEPTION_RESET,

    0x10: EV_BATTERY_VOLTAGE,   # bit 0 and bit 1 plus extra byte
    0x11: EV_BATTERY_VOLTAGE,
    0x12: EV_BATTERY_VOLTAGE,
    0x13: EV_BATTERY_VOLTAGE,
    
    0x20: EV_FINISHED_MOVE,
    
#    0x21: EV_TEST_DISTANCE,    # single command (but always followed immediately by EV_IR_FRONT_SIDE_STATE)

    0x30: EV_BUTTON_A_RELEASE,
    0x31: EV_BUTTON_B_RELEASE,
    0x38: EV_BUTTON_A_PRESS,
    0x39: EV_BUTTON_B_PRESS,


    0x40: EV_IR_FRONT_SIDE_STATE,
    0x41: EV_IR_FRONT_SIDE_STATE,
    0x42: EV_IR_FRONT_SIDE_STATE,
    0x43: EV_IR_FRONT_SIDE_STATE,
    0x44: EV_IR_FRONT_SIDE_STATE,
    0x45: EV_IR_FRONT_SIDE_STATE,
    0x46: EV_IR_FRONT_SIDE_STATE,
    0x47: EV_IR_FRONT_SIDE_STATE,
    0x48: EV_IR_FRONT_SIDE_STATE,
    0x49: EV_IR_FRONT_SIDE_STATE,
    0x4A: EV_IR_FRONT_SIDE_STATE,
    0x4B: EV_IR_FRONT_SIDE_STATE,
    0x4C: EV_IR_FRONT_SIDE_STATE,
    0x4D: EV_IR_FRONT_SIDE_STATE,
    0x4E: EV_IR_FRONT_SIDE_STATE,
    0x4F: EV_IR_FRONT_SIDE_STATE,

    # not really used (except for steering, which is low level code)
    0x50: EV_IR_45_STATE,
    0x51: EV_IR_45_STATE,
    0x52: EV_IR_45_STATE,
    0x53: EV_IR_45_STATE,
    0x54: EV_IR_45_STATE,
    0x55: EV_IR_45_STATE,
    0x56: EV_IR_45_STATE,
    0x57: EV_IR_45_STATE,
    0x58: EV_IR_45_STATE,
    0x59: EV_IR_45_STATE,
    0x5A: EV_IR_45_STATE,
    0x5B: EV_IR_45_STATE,
    0x5C: EV_IR_45_STATE,
    0x5D: EV_IR_45_STATE,
    0x5E: EV_IR_45_STATE,
    0x5F: EV_IR_45_STATE,

    0x61: EV_IR_FRONT_LEVEL,
    0x62: EV_L90_LEVEL,
    0x63: EV_L45_LEVEL,
    0x64: EV_R90_LEVEL,
    0x65: EV_R45_LEVEL,

    # unlocking
    0xC0: EV_UNLOCK_FROM_LOCK,
    0xC1: EV_UNLOCK_FROM_UNLOCK,
    0xC2: EV_LOCK_BY_TIMER,
    0xC3: EV_LOCK_BY_COMMAND,

    0x80: EV_POLL_REPLY,

    0xE2: EV_FAIL_INVALID_COMMAND,
    0xEF: acknowledge_send,  # no intermediate function required, like EV_GOT_INSTRUCTION
}


def event_processor(port):
    cmd = port.read(1)
    if len(cmd) != 0:
        cmd = ord(cmd)
        if cmd in command_handlers:
            command_handlers[cmd](port, cmd)
        else:
            print("Unknown event", hex(cmd), "ignoring")
            #recover_from_major_error()

    run_timers(port)

################################################################
# 
# Control Functions
#       

def wait_for_move_to_finish(port):
    if verbose: print("Wait for move finished")
    global move_finished
    while not move_finished:
        event_processor(port)
    move_finished = False
    

def wait_for_unlock_to_complete(port):
    if verbose: print("Waiting for unlock to complete")
    start_time = read_accurate_time()

    # run one anway
    event_processor(port)
    while locked:
        event_processor(port)
        if read_accurate_time() > (start_time + 2):
            return False

    return True


def wait_for_poll_reply(port):
    # @todo: complete this funnction
    pass

def get_key(port):
    while True:
        # always poll events at least once
        event_processor(port)
        
        # check the key queue
        if keys_in_queue:
            return keys_in_queue.popleft()


    
def get_wall_info(port):
    global got_wall_info
    got_wall_info = False
    
    send_get_wall_info(port)
    while not got_wall_info:
        event_processor(port)
    
    return left_wall_sense, front_short_wall_sense, right_wall_sense


def get_45_info(port):
    global got_45_info
    got_45_info = False
    
    send_get_45_sensor_info(port)
    while not got_45_info:
        event_processor(port)


def scan_for_walls(port, m, robot_direction, robot_row, robot_column):
    left, front, right = get_wall_info(port)
    if verbose: print("Directions LFR =", left, front, right)
    wall_changed = False
    if left and not m.get_left_wall(robot_direction, robot_row, robot_column):
        m.set_left_wall(robot_direction, robot_row, robot_column)
        wall_changed = True
    if right and not m.get_right_wall(robot_direction, robot_row, robot_column):
        m.set_right_wall(robot_direction, robot_row, robot_column)
        wall_changed = True
    if front and not m.get_front_wall(robot_direction, robot_row, robot_column):
        m.set_front_wall(robot_direction, robot_row, robot_column)
        wall_changed = True

    if wall_changed:
        m.flood_fill_all()

def wait_seconds(port, time):
    if time < 0:
        return
    
    end_time = read_accurate_time() + time
    while read_accurate_time() < end_time:
        event_processor(port)

def is_shortest_path_explored(m, row, column, direction):
    # do a virtual dry run
    #row = 0
    #column = 0
    #direction = 0
    m.clear_marks()
    
    while True:
        m.set_mark(row, column)
        if m.explored[row][column] == False:
            return (False, row, column)
        
        headings = m.get_lowest_directions_against_heading(direction, row, column)
        if len(headings) == 0:
            return (True, None, None)     # don't care, leave
        heading = headings[0]
        if heading == 0:
            if direction == 0:
                row += 1
            elif direction == 1:
                column += 1
            elif direction == 2:
                row -= 1
            else:
                column -= 1
        elif heading == 1:
            direction = 3 & (direction + 1)
        elif heading == 3:
            direction = 3 & (direction - 1)
        else:   # should never need to backtrack!
            return (True, None, None)
    
def cell_one_away(m, robot_row, robot_column, unex_row, unex_column):
    row_diff = abs(robot_row - unex_row)
    column_diff = abs(robot_column - unex_column)
    if (column_diff == 0 and row_diff == 1) or (column_diff == 1 and row_diff == 0):
        # (diagonal is ok)

        # check if there is a wall between the two...
        if unex_row > robot_row:
            heading = 0
        elif unex_column > robot_column:
            heading = 1
        elif unex_row < robot_row:
            heading = 2
        else:
            heading = 3
        if m.get_front_wall(heading, robot_row, robot_column):
            return False
        
        return True
    else:
        return False

flashing_cal4_led = False
def do_calibration_LEDs(port, value):
    send_switch_led_command(port, 1, value & 1)
    send_switch_led_command(port, 2, value & 2)
    send_switch_led_command(port, 3, value & 4)
    if SIMULATOR:
        send_switch_led_command(port, 4, True)
    else:
        global flashing_cal4_led
        send_switch_led_command(port, 4, flashing_cal4_led)
        flashing_cal4_led = not flashing_cal4_led

IR_threshold_defaults = {
            "front_long_threshold":15,
            "front_short_threshold":50,
            "left_side_threshold":200,
            "right_side_threshold":200,
            "left_45_threshold":360,
            "right_45_threshold":540,
            "left_45_too_close_threshold":580,
            "right_45_too_close_threshold":760,
}

def set_default_IR_thresholds(port, IR):
    set_front_long_threshold(port, IR["front_long_threshold"])
    set_front_short_threshold(port, IR["front_short_threshold"])
    set_left_side_threshold(port, IR["left_side_threshold"])
    set_right_side_threshold(port, IR["right_side_threshold"])
    set_left_45_threshold(port, IR["left_45_threshold"])
    set_right_45_threshold(port, IR["right_45_threshold"])
    set_left_45_too_close_threshold(port, IR["left_45_too_close_threshold"])
    set_right_45_too_close_threshold(port, IR["right_45_too_close_threshold"])


def grab_values(target):
    global ir_front_level_new
    global ir_l90_level_new
    global ir_r90_level_new
    global ir_l45_level_new
    global ir_r45_level_new
    
    global ir_front_level
    global ir_l90_level
    global ir_r90_level
    global ir_l45_level
    global ir_r45_level
    
    if ir_front_level_new:
        ir_front_level_new = False
        if 'frmax' not in target or ir_front_level > target['frmax']:
            target['frmax'] = ir_front_level
        if 'frmin' not in target or ir_front_level < target['frmin']:
            target['frmin'] = ir_front_level
        if 'frcount' not in target:
            target['frcount'] = 1
        else:
            target['frcount'] += 1
        
    if ir_l90_level_new:
        ir_l90_level_new = False
        if 'l90max' not in target or ir_l90_level > target['l90max']:
            target['l90max'] = ir_l90_level
        if 'l90min' not in target or ir_l90_level < target['l90min']:
            target['l90min'] = ir_l90_level
        if 'l90count' not in target:
            target['l90count'] = 1
        else:
            target['l90count'] += 1

    if ir_r90_level_new:
        ir_r90_level_new = False
        if 'r90max' not in target or ir_r90_level > target['r90max']:
            target['r90max'] = ir_r90_level
        if 'r90min' not in target or ir_r90_level < target['r90min']:
            target['r90min'] = ir_r90_level
        if 'r90count' not in target:
            target['r90count'] = 1
        else:
            target['r90count'] += 1
        
    if ir_l45_level_new:
        ir_l45_level_new = False
        if 'l45max' not in target or ir_l45_level > target['l45max']:
            target['l45max'] = ir_l45_level
        if 'l45min' not in target or ir_l45_level < target['l45min']:
            target['l45min'] = ir_l45_level
        if 'l45count' not in target:
            target['l45count'] = 1
        else:
            target['l45count'] += 1

    if ir_r45_level_new:
        ir_r45_level_new = False
        if 'r45max' not in target or ir_r45_level > target['r45max']:
            target['r45max'] = ir_r45_level
        if 'r45min' not in target or ir_r45_level < target['r45min']:
            target['r45min'] = ir_r45_level
        if 'r45count' not in target:
            target['r45count'] = 1
        else:
            target['r45count'] += 1


left_count = {}
right_count = {}
far_left_count = {}
far_right_count = {}
middle_count = {}
front_center = {}
front_long_count = {}
cal_IR = {}

def calibration_for_position(port, read_data, position_store):
    if read_data:
        c = position_store
        grab_values(c)
        if c['r90count'] >= 10 and c['r45count'] >= 10 and c['l90count'] >= 10 and c['l45count'] >= 10 and c['frcount'] >= 10:
            return True
    return False

def calculate_and_configure(port, read_data, _):
    #print(left_count)
    #print(right_count)
    #print(middle_count)
    #print(front_center)
    #print(front_long_count)

    #
    # We will need to test these on a real mouse
    #
    # diagonal
    # for too close we select 2/3 and for a bit close 1/3
    # between 1cm away and middle
    l45_diff = left_count['l45max'] - middle_count['l45min']
    r45_diff = right_count['r45max'] - middle_count['r45min']
    cal_IR["left_45_threshold"] = int(l45_diff/ 2.0 ) + middle_count['l45min']
    cal_IR["right_45_threshold"] = int(r45_diff / 2.0) + middle_count['r45min']
    cal_IR["left_45_too_close_threshold"] = left_count['l45min']
    cal_IR["right_45_too_close_threshold"] = right_count['r45min']

    # wall detect - detect over other side
    cal_IR["left_side_threshold"] = far_right_count['l90min']
    cal_IR["right_side_threshold"] = far_left_count['r90min']
    
    # front wall
    cal_IR["front_long_threshold"] = front_long_count['frmin']
    cal_IR["front_short_threshold"] = front_center['frmin']

    set_default_IR_thresholds(port, cal_IR)
    return True

def calibration_test(port, read_data, _):
    # if True, then exit, otherwise just wait by returning False...
    return read_data


def calibration_save_and_quit(port, read_data, _):
    print("Save calibration")
    write_config_file('calibration.txt', cal_IR)
    return None


def read_config_file(filename, key_value_map):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()            
    except IOError:
        return

    for line in lines:
        s = line.split("=", 1) #num=1)
        key = s[0].strip()
        if len(s) == 2 and len(key) > 0 and key in key_value_map:
            try:
                val = int(s[1].strip())
            except ValueError:
                val  = key_value_map[key]
            
            key_value_map[key] = val
            

def write_config_file(filename, key_value_map):
    try:
        with open(filename, 'w') as f:
            for key in key_value_map:
                f.write("%s=%d\n" % (key, key_value_map[key]))
    except IOError:
        pass


def load_IR_calibration(port):
    read_config_file('calibration.txt', IR_threshold_defaults)
    set_default_IR_thresholds(port, IR_threshold_defaults)


cal_dispatcher = [
    (calibration_for_position, "Move to 0cm from left wall", far_left_count),
    (calibration_for_position, "Move to 1.5cm from left wall", left_count),
    (calibration_for_position, "Move to middle between left and right walls", middle_count),
    (calibration_for_position, "Move to 1.5cm from right wall", right_count),
    (calibration_for_position, "Move to 0cm from right wall", far_right_count),
    (calibration_for_position, "Move to furthest away from front wall but most of robot in cell", front_center),
    (calibration_for_position,  "Move front of mouse to 1 cell away from front wall", front_long_count),
    (calculate_and_configure, "Calculating calibration", None),
    (calibration_test, "Test sensor LEDs now", None),
    (calibration_save_and_quit, "Saving sensor calibration", None),
]


def do_calibration(port):
    print("Start Calibration")

    global ir_front_level_new
    global ir_l90_level_new
    global ir_r90_level_new
    global ir_l45_level_new
    global ir_r45_level_new
    ir_front_level_new = False
    ir_l90_level_new = False
    ir_r90_level_new = False
    ir_l45_level_new = False
    ir_r45_level_new = False

    global left_count
    global right_count
    global far_left_count
    global far_right_count
    global middle_count
    global front_center
    global front_long_count
    left_count = {}
    right_count = {}
    middle_count = {}
    front_center = {}
    front_long_count = {}
    far_left_count = {}
    far_right_count = {}


    start = read_accurate_time()
    turn_on_ir(port)
    
    update_state = 1
    cal_state = 0
    print(cal_dispatcher[cal_state][1])
    read_data = False
    flash = True
    while True:
        if (read_accurate_time() - start) > 0.05:
            if update_state == 1:
                get_front_level(port)
            elif update_state == 2:
                get_l90_level(port)
                get_r90_level(port)
            elif update_state == 3:
                get_l45_level(port)
                get_r45_level(port)
            else:
                update_state = 0
                flash = not flash
                if read_data and flash:
                    do_calibration_LEDs(port, 0)
                else:
                    do_calibration_LEDs(port, cal_state + 1)

            update_state += 1
            
            start = read_accurate_time()

        # do the testing
        entry = cal_dispatcher[cal_state]
        need_step = entry[0](port, read_data, entry[2])
        if need_step is None:
            break
        elif need_step:
            read_data = False
            cal_state += 1
            print(cal_dispatcher[cal_state][1])

        if keys_in_queue:
            key = get_key(port)
            if key == "a":
                read_data = True
                
            elif key == 'B' or key == 'b':
                # exit early key
                # return IR to old levels
                set_default_IR_thresholds(port, IR_threshold_defaults)
                break

    print("Exit Calibration")
    turn_off_all_LEDs(port)
    turn_off_ir(port)

def do_test_mode(port):
    print("Start Test")
    start = read_accurate_time()
    turn_on_ir(port)
    
    wait_to_go = None
    flash = True
    mode = 0
    while True:
        if (read_accurate_time() - start) > 0.2:
            flash = not flash
            send_switch_led_command(port, 1, flash)
            if mode != 3:
                send_switch_led_command(port, 2, flash)
            if mode == 1 or mode == 3:
                send_switch_led_command(port, 3, flash)
            elif mode == 2:
                send_switch_led_command(port, 4, flash)

            if wait_to_go is not None:
                wait_to_go -= 1
                if wait_to_go == 0:
                    wait_to_go = None
                    
                    if mode == 0:
                        move_forward(port, distance_cell)
                        wait_for_move_to_finish(port)
                        turn_off_motors(port)
                    elif mode == 1:
                        turn_off_ir(port)
                        move_right(port, distance_turnr90)
                        wait_for_move_to_finish(port)
                        turn_off_motors(port)
                        turn_on_ir(port)
                    elif mode == 2:
                        turn_off_ir(port)
                        move_left(port, distance_turnr90)
                        wait_for_move_to_finish(port)
                        turn_off_motors(port)
                        turn_on_ir(port)
                    elif mode == 3:
                        while not keys_in_queue:
                            get_wall_info(port)
                            get_45_info(port)

                            if left_wall_sense: L = "L<"
                            else: L = "  "
                            send_switch_led_command(port, 5, left_wall_sense)
                            if right_wall_sense: R = ">R"
                            else: R = "  "  
                            send_switch_led_command(port, 2, right_wall_sense)

                            if front_short_wall_sense: FS = "_FS_"
                            else: FS = "    "
                            send_switch_led_command(port, 1, front_short_wall_sense)
                            if front_long_wall_sense: FL = "^FL^"
                            else: FL = "    "

                            wait_seconds(port, 0.1)

                            if left_45_sense: L45 = "\\"
                            else: L45 = " "
                            if right_45_sense: R45 = "/"
                            else: R45 = " "

                            if left_45_too_close_sense: LS45 = "\\"
                            else: LS45 = " "
                            send_switch_led_command(port, 4, left_45_too_close_sense)
                            if right_45_too_close_sense: RS45 = "/"
                            else: RS45 = " "
                            send_switch_led_command(port, 3, right_45_too_close_sense)

                            print(L + L45 + LS45 + FS + FL + RS45 + R45 + R)
                           
                            wait_seconds(port, 0.2)

                        # ignore this key
                        get_key(port)
                        
            start = read_accurate_time()

        if keys_in_queue:
            key = get_key(port)
            turn_off_all_LEDs(port)
            if key == "a":
                wait_to_go = 5
            elif key == 'b':
                mode += 1
                if mode == 4:
                    mode = 0
            elif key == 'B' or key == 'b':
                # exit key
                break

    turn_off_all_LEDs(port)
    turn_off_ir(port)
    print("End Test")

################################################################
#
# Control Loop
#

def run_program(port):

    while True:
        send_unlock_command(port)
        if wait_for_unlock_to_complete(port):
            break
        print("Unlock failed - Retrying")

    turn_off_all_LEDs(port)
    turn_off_motors(port)
    turn_off_ir(port)

    set_default_distances(port)
    load_IR_calibration(port)

    global maze_selected
    calibration_mode = False
    test_mode = False
    while True:
        # let's process some events anyway
        for _ in range(1,10):
            event_processor(port)
        
        send_poll_command(port)
        wait_for_poll_reply(port)

        running = False
        while not running:
            if calibration_mode:
                send_switch_led_command(port, 1, True)
                send_switch_led_command(port, 2, True)
            elif test_mode:
                send_switch_led_command(port, 1, False)
                send_switch_led_command(port, 2, False)
            elif maze_selected == 5:
                send_switch_led_command(port, 1, True)
                send_switch_led_command(port, 2, False)
            elif maze_selected == 16:
                send_switch_led_command(port, 1, False)
                send_switch_led_command(port, 2, True)
            else:
                print("Unknown mode")
                sys.exit(1)

            while True:
                key = get_key(port)
                if key == "a":
                    if calibration_mode:
                        calibration_mode = False
                        test_mode = True
                    elif test_mode:
                        test_mode = False
                        maze_selected = 5
                    elif maze_selected == 5:
                        maze_selected = 16
                    else:   # maze_selected == 16
                        calibration_mode = True
                    break
                elif key == "b":
                    # B key without hold does nothing
                    pass
                elif key == "A":
                    raise ShutdownRequest
                elif key == "B":
                    running  = True
                    break

            # let's capture it here and do calibration
            if running and calibration_mode:
                running = False
                do_calibration(port)
                calibration_mode = False
            if running and test_mode:
                running = False
                do_test_mode(port)
                test_mode = False
            
        start_time = read_accurate_time()
        # start the run
        turn_on_ir(port)        # do this early so IR system has time to scan before scan_for_walls()
        send_switch_led_command(port, 3, True)
        set_speed(port, 100)    # normal search speed
        m = Maze(maze_selected)
        m.target_normal_end_cells()
        m.flood_fill_all()
        robot_direction = 0     # 0=north, 1=east, 2=west 
        robot_row = 0
        robot_column = 0
        
        # this is the start cell. We scan here anyway, although it's not necessary.
        scan_for_walls(port, m, robot_direction, robot_row, robot_column)
        m.set_explored(robot_row, robot_column)
        
        # ensure we wait at least 2 seconds before we move, under all circumstances
        time_left = 2 - (read_accurate_time() - start_time)
        wait_seconds(port, time_left)

        search_phase = 1
        sparse_run = False
        while True:             # search/explore runs
            
            completed = False
            while True:         # single run search

                if keys_in_queue:
                    # keys cancel run!
                    print("Key aborts")
                    while keys_in_queue:
                        get_key(port)
                    completed = False
                    break

                headings = m.get_lowest_directions_against_heading(robot_direction, robot_row, robot_column)
                print(headings)
                if len(headings) == 0:
                    current_cell_value = m.get_cell_value(robot_row, robot_column)
                    if current_cell_value == 0:
                        #completed
                        completed = True
                        break
                    else:
                        # can't get any better cell? Probably unsolvable?
                        completed = False
                        break
                
                if sparse_run:
                    # we don't need to achieve the target IF we have explored all
                    # cells to the target.
                    explored, unex_row, unex_column = is_shortest_path_explored(m, robot_row, robot_column, robot_direction)
                    if explored:
                        completed = True
                        break
                                        
                # @todo: we should select a specific one here, but we just choose the first one at the moment
                heading = headings[0] & 3
                if heading == 0:
                    turn_on_ir(port)
                    move_forward(port, distance_cell)
                    wait_for_move_to_finish(port)
    
                    if robot_direction == 0:
                        robot_row += 1
                    elif robot_direction == 1:
                        robot_column += 1
                    elif robot_direction == 2:
                        robot_row -= 1
                    else:
                        robot_column -= 1
    
                    scan_for_walls(port, m, robot_direction, robot_row, robot_column)
                    m.set_explored(robot_row, robot_column)
                    
                    if print_map_in_progress:
                        m.clear_marks()
                        m.set_mark(robot_row, robot_column)
                        m.print_maze()
                elif heading == 1:
                    turn_off_ir(port)
                    move_right(port, distance_turnr90)
                    wait_for_move_to_finish(port)
                    turn_on_ir(port)
                    robot_direction += 1
                    robot_direction &= 3
                elif heading == 2:
                    turn_off_ir(port)
                    move_right(port, distance_turn180)
                    wait_for_move_to_finish(port)
                    turn_on_ir(port)
                    robot_direction += 2
                    robot_direction &= 3
                else:
                    turn_off_ir(port)
                    move_left(port, distance_turnl90)
                    wait_for_move_to_finish(port)
                    turn_on_ir(port)
                    robot_direction -= 1
                    robot_direction &= 3
    
            # shut down
            turn_off_ir(port)
            turn_off_motors(port)
            
            send_switch_led_command(port, 3, False)
            if not completed:
                print("Failed to complete")
                # flash for 6 seconds
                for _ in range(1, 6):
                    send_switch_led_command(port, 4, True)
                    wait_seconds(port, 0.5)
                    send_switch_led_command(port, 4, False)
                    wait_seconds(port, 0.5)
                send_switch_led_command(port, 4, True)
                break
            
            # we only specifically turn this on if we want it
            sparse_run = False

            if search_phase == 1:
                print()
                print("Got to target")
                print("===========================================")
                print()
                
                # let's floodfill from start to center and see if we know enough
                # to look for the shortest path
                m.clear_targets()
                m.target_normal_end_cells()
                m.flood_fill_all()
                shortest, unex_row, unex_column = is_shortest_path_explored(m, 0, 0, 0)
                print("Is shortest path explored?", shortest)
                m.print_maze()
                
                # if we have explored the shortest path, then we are complete
                if shortest:
                    # Go to start then wait for keys
                    m.clear_targets()
                    m.target_start_cell()
                    m.flood_fill_all()
                    print()
                    print("target start")
                    print("===========================================")
                    print()                    
                    search_phase = 2
                else:
                    # not shortest, go to unexploded cell
                    if not cell_one_away(m, robot_row, robot_column, unex_row, unex_column):
                        m.clear_targets()
                        m.set_target_cell(unex_row, unex_column)
                        m.flood_fill_all()
                        print("Run to unexplored at", unex_row, unex_column)
                    else:
                        # the unexplorded is only one cell away, use a different strategy
                        sparse_run = True
                        m.clear_targets()
                        m.target_normal_end_cells()
                        m.flood_fill_all()

            elif search_phase == 2:
                print()
                print("Back at start, wait for speed run")
                print("===========================================")
                print()
                m.clear_targets()
                m.target_normal_end_cells()
                m.flood_fill_all()
                m.print_maze()
                break

        if completed:
            print("We need to wait for speed run keys here?")
            print("Then assemble and run speed run at 500?")
        else:
            print("Going back to start menu")
                
        # @todo: move test (similar to calibration)
        # @todo: do speed run.
        # @todo: move forward without stopping
        # @todo: curved turns

        # loop back to top to do keys again

def main():
    port = serial.Serial("/dev/ttyAMA0", baudrate = 57600, timeout = 0.1)
    bytes_waiting = port.inWaiting()
    if bytes_waiting != 0:
        print("Bytes Waiting = ", bytes_waiting)

    while True:
        try:
            run_program(port)
            
        except SoftReset, MajorError:
            # @todo: Fix this to reset variables, and restart
            # @todo: Go though all variables in project, and set... maybe collate variables at top?
            reset_message_queue()
            global locked
            locked = True
            global keys_in_queue
            keys_in_queue = deque()
            
        except ShutdownRequest:
            if battery_voltage_mode == 2:
                print("Battery Shutdown.      Batt V", battery_voltage, "cell:", battery_voltage/4.0)

            global log_battery_voltage
            global battery_voltage_array
            if log_battery_voltage:
                with open(battery_filename, "a") as f:
                    for item in battery_voltage_array:
                        f.write("%f, %s\n" % (item[0], item[1]))
                battery_voltage_array = []

            print("Running RPi shutdown command")
            turn_off_motors(port)
            turn_off_ir(port)
            send_led_pattern_command(port, 0x20)
            if not SIMULATOR:
                os.system("sudo poweroff")
            print("sudo poweroff")
            sys.exit(1)
            
main()

