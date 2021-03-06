#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Graphical Interface for the Vision2 low level Mouse Emulator.
# This is a graphical view for the low_level_emulator.py. 
# For more details see that file.
#
# Copyright 2016-2017 Rob Probin.
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
# Requires Python 3   (It doesn't ... problems with the mouse code mean this is still Python 2 at the moment)
#
# NOTES:
# 
#  * It would be nice if the mouse used asyncio for the serial, and tkinter run loop handled with this. But it doesn't at the moment.
#  * To avoid the problem that mouse.py has it's own control loop and tkinter also requires it's own control loop, we use a second thread.
#   - Co-routines would solve this extra thread problem, but currently Python generators are not flexible enbough.
#  * We use Queue as the thread safe container between threads. We could potentially use collections.deque with fast atomic 
#    append() and popleft() but we don't to avoid weird threading corner cases - and we are not performance bound here.
#
#from __future__ import print_function
import sys

import mouse

# Basic Tkinter
if sys.version_info.major == 3:
    from tkinter import *
    import tkinter.font as tkFont
else:
    print("Python 2 not supported")
    sys.exit(1)
    #from Tkinter import *       # could have used impot Tkinter as tk
    #import tkFont

# Python 3 version
#from tkinter import ttk
#from Tkinter import *
#from tkinter.ttk import *
# Python 2 version
#import ttk
#from Tkinter import *
#from ttk import *

#from Tkinter import Tk
#from Tkinter import Canvas
#from Tkinter import Rect

# Tkinter Canvas
# http://effbot.org/tkinterbook/canvas.htm
# http://www.akeric.com/blog/?p=1116

# Tkinter Geometry managers
# http://effbot.org/zone/tkinter-geometry.htm
# http://www.python-course.eu/tkinter_layout_management.php
# http://effbot.org/tkinterbook/pack.htm

from threading  import Thread

try:
        from Queue import Queue, Empty
except ImportError:
        from queue import Queue, Empty  # python 3.x


class LED(Label):
    LED_font = "not set"
    
    def setup_font(self, parent):
        if self.__class__.LED_font == "not set":
            label = Label(parent, text="x")
            font = tkFont.Font(font=label['font'])
            #print(font.actual())

            newfont = tkFont.Font(family=font['family'], size=font['size']+4)
            #print(newfont.actual())

            self.__class__.LED_font = newfont
            
    def __init__(self, parent, colour=None):
        self.setup_font(parent)
        if colour is None:
            self.colour = "black"
        else:
            self.colour = colour
        Label.__init__(self, parent, text="○", foreground="grey", font=self.LED_font)

    def on(self):
        self.config(text="●", foreground=self.colour)
    
    def off(self):
        self.config(text="○", foreground="grey")
        
    def set(self, state):
        if state:
            self.on()
        else:
            self.off()
            
def create_map(canvas, posx, posy, width, height):
    cw = width / 16
    ch = height / 16
    
    for row in range(16):
        for column in range(16):
            canvas.create_rectangle(posx + cw*column, posy + ch*row, cw, ch, fill="", outline="grey", dash=(4, 4))
            

    


class GUI_App(object):
        def __init__(self, width=256, height=256):
            self.width = width
            self.height = height
            
#            root = Tk()
#            label.pack(expand=True, fill=BOTH, side=TOP)
#            label = Label(root, text = 'Loading...Please Wait') # code before computation starts
#            mainloop()
            
            # 2nd example
            #master=Tk()
            #
            #def print1():
            #    Label(master,text="Thank you").pack()
            #frame=Label(master,text="Python Lake: Welcome").pack()
            #button=Button(master, text="Submit", command=print1).pack()
            #master.mainloop()

            self.root = Tk()
            self.root.title("Vision2")
            #self.root.geometry("%sx%s"%(self.width, self.height))

            self.front_led = LED(self.root, "red")
            self.front_led.pack()

            ######################################################
            self.line2_frame = Frame(self.root)

            self.left_led = LED(self.root, "green")
            self.left_led.pack(side=LEFT)

            self.canvas = Canvas(self.line2_frame, width=self.width, height=self.height)
            self.canvas.pack(side=LEFT)
            self.canvas.create_rectangle(3, 3, self.width, self.height, fill="", outline="grey", dash=(4, 4))

            #self.canvas.create_line(0, 0, 200, 100)
            #self.canvas.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))

            #self.canvas.create_rectangle(50, 25, 150, 75, fill="blue")
            
            #canvas_id = self.canvas.create_text(10, 10, anchor="nw", text="hello\nbye")
            #self.canvas.itemconfig(canvas_id, text="this is the \n text")
            #self.canvas.insert(canvas_id, 14, "new ")

            #self.flash_id = self.canvas.create_text(3, 3, anchor="nw", text="o")
            #self.canvas.itemconfig(flash_id, text="#")
            #self.canvas.insert(flash_id, 14, "new ")
            #self.state = False
            
            self.right_led = LED(self.root, "blue")
            self.right_led.pack(side=RIGHT)
            
            self.line2_frame.pack()
            
            ######################################################            
            label0 = Label(self.root, text="Main LEDs")
            label0.pack()
            
            main_led_frame = Frame(self.root)

            #LEDs = Label(self.root, text=" ○  ○  ○         ●  ●  ●")
            #LEDs.pack()
            self.leds = []
            
            for i in range(6):
                led = LED(main_led_frame, "red")
                led.pack(side=LEFT, ipadx=2)
                if i == 2:
                    Label(main_led_frame, text="              ").pack(side=LEFT)
                self.leds.append(led)
            
            main_led_frame.pack()
            ######################################################
            label = Label(self.root, text="Buttons")
            label.pack()
            button_frame = Frame(self.root)
            def reset_button():
                print("RESET", self)
            def short_a_button():
                self.key_q.put("a")
            def long_A_button():
                self.key_q.put("A")
            def short_b_button():
                self.key_q.put("b")
            def long_B_button():
                self.key_q.put("B")
            self.button_reset=Button(button_frame, text="Reset", command=reset_button).pack(side=LEFT)
            self.button_a=Button(button_frame, text="short [a]", command=short_a_button).pack(side=LEFT)
            self.button_A=Button(button_frame, text="Long [A]", command=long_A_button).pack(side=LEFT)
            self.button_b=Button(button_frame, text="short [b]", command=short_b_button).pack(side=LEFT)
            self.button_B=Button(button_frame, text="Long [B]", command=long_B_button).pack(side=LEFT)
            button_frame.pack()
            
            ######################################################
            label2 = Label(self.root, text="System Status")
            label2.pack(side=TOP)
            label3 = Label(self.root, text="Battery = 0.0v")
            label3.pack(side=TOP)

        def push_maze(self, current_maze):
            pass
        
        def do_received_actions(self):
            while not self.gui_q.empty():
                try:
                    action = self.gui_q.get_nowait()
                except self.gui_q.Empty:
                    break
                if action[0] == "LED":
                    led_num = action[1]
                    led_state = action[2]
                    if led_num < 1 or led_num > 9:
                        print("Unexpected LED number", led_num)
                        sys.exit(1)
                    
                    if led_num <= 6:
                        self.leds[6-led_num].set(led_state)
                    elif led_num == 7:
                        self.left_led.set(led_state)
                    elif led_num == 8:
                        self.front_led.set(led_state)
                    else:
                        self.right_led.set(led_state)
                        
                else:
                    print("Unknown action")
                    sys.exit(1)
                    
        def run(self):
            self.key_q = Queue()
            self.gui_q = Queue()

            def mm():
                mouse.main(self)

            #mm()
            
            self.thread = Thread(target=mm)
            # we ideally want to terminate the mouse gracefully, but this work around will have to suffice
            self.thread.daemon = True # thread dies with the program
            self.thread.start()

            def task():
                if not self.thread.is_alive():
                    print(">>> MOUSE THREAD IS NOT ALIVE - terminating <<< ")
                    sys.exit(1)
                    
                self.do_received_actions()
                
                #self.state = not self.state
                #if self.state:
                #    self.canvas.itemconfig(self.flash_id, text="#")
                #    #self.front_led.on()
                #else:
                #    self.canvas.itemconfig(self.flash_id, text="o")
                #    #self.front_led.off()
                self.root.after(50, task)  # reschedule event in 50 milliseconds
            
            self.root.after(50, task)
            
            def close_window():
                # signal to mouse or low level emulator...
                self.root.destroy()
                
            # make sure we quit mouse properly
            self.root.protocol("WM_DELETE_WINDOW", close_window)
            
            self.root.mainloop()
            #mainloop()

        def set_action(self, action):
            self.gui_q.put(action)                    
                
        def get_key(self):
            try:
                key = self.key_q.get_nowait()
            except Empty:
                return None
            else:
                return key

if __name__ == "__main__":
    gui = GUI_App()
    gui.run()
    