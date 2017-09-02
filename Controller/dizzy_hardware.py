#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on 2 Sep 2017

@author: Rob Probin

@summary:  Amount of Hardware Abstraction for Dizzy (also Vision2 Micromouse Robot)
  Intended to run on a Raspberry Pi on the actual robot.
  Also runs on a Mac with the simulator (low_level_emulator).

@copyright: Copyright 2017 Rob Probin. All original work.

@license: GPLv2

  This program is free software; you can redistribute it and/or
  modify it under the terms of the GNU General Public License
  as published by the Free Software Foundation; either version 2
  of the License, or (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

'''
import sys
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("WARNING: Importing test stub for RPi.GPIO")
    sys.exit(1)
    #from test_stubs import GPIO_stub as GPIO

_Backlight_IO_BCM = 26

class DizzyHardware(object):
    '''
    classdocs
    '''
    
    def __init__(self, params):
        '''
        Constructor
        '''
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(_Backlight_IO_BCM, GPIO.OUT)
    
    def read_time(self):
        pass
    
    def camera_light_on(self):
        GPIO.output(_Backlight_IO_BCM, GPIO.HIGH)
    
    def camera_light_off(self):
        GPIO.output(_Backlight_IO_BCM, GPIO.LOW)


