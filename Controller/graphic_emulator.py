#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Graphical Interface for the Vision2 low level Mouse Emulator.
# This is a graphical view for the low_level_emulator.py. 
# For more details see that file.
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
# Requires Python 3
from __future__ import print_function

# Basic Tkinter
from tkinter import *

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

# http://effbot.org/tkinterbook/canvas.htm
# http://www.akeric.com/blog/?p=1116

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

            self.canvas = Canvas(self.root, width=self.width, height=self.height)
            self.canvas.pack()

            self.canvas.create_line(0, 0, 200, 100)
            self.canvas.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))

            self.canvas.create_rectangle(50, 25, 150, 75, fill="blue")
            
            canvas_id = self.canvas.create_text(10, 10, anchor="nw", text="hello\nbye")
            self.canvas.itemconfig(canvas_id, text="this is the \n text")
            self.canvas.insert(canvas_id, 14, "new ")

            flash_id = self.canvas.create_text(3, 3, anchor="nw", text="o")
            #self.canvas.itemconfig(flash_id, text="#")
            #self.canvas.insert(flash_id, 14, "new ")
            self.state = False
            
            label0 = Label(self.root, text="Main LEDs")
            label0.pack()
            LEDs = Label(self.root, text=" ○  ○  ○         ●  ●  ●")
            LEDs.pack()
            label = Label(self.root, text="Buttons")
            label.pack()
            button_frame = Frame(self.root)
            button_reset=Button(button_frame, text="Reset").pack(side=LEFT)
            button_a=Button(button_frame, text="short [a]").pack(side=LEFT)
            button_A=Button(button_frame, text="Long [A]").pack(side=LEFT)
            button_b=Button(button_frame, text="short [b]").pack(side=LEFT)
            button_B=Button(button_frame, text="Long [B]").pack(side=LEFT)
            button_frame.pack()
            label2 = Label(self.root, text="System Status")
            label2.pack(side=TOP)
            label3 = Label(self.root, text="Battery = 0.0v")
            label3.pack(side=TOP)
            
            def task():
                self.state = not self.state
                if self.state:
                    self.canvas.itemconfig(flash_id, text="#")
                else:
                    self.canvas.itemconfig(flash_id, text="o")
                self.root.after(500, task)  # reschedule event in 2 seconds
            
            self.root.after(500, task)
            
            self.root.mainloop()
            #mainloop()

if __name__ == "__main__":
    GUI_App()
    
    