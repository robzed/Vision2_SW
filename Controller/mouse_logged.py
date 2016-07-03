#!/usr/bin/env python
import datetime
import os
import sys

# switch to the Controller directory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

class Print_Logging:
    def __init__(self):
        # get the time and date as a string
        self.now = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        self.file = None
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.mode = "stdout"
        self.buffer = []
        
    def print_to_stdout(self):
        if self.mode == "stdout":
            return
        
        # ensure not buffered
        self.resume_file_save()
        
        # redirect stdout and stderr to original targets
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def print_to_file(self):
        if self.mode == "file":
            return
        
        self.mode = "file"
        
        if self.file is None:
            self.file = open("mouse_%s.log" % self.now, 'w') 
        
        # redirect stdout and stderr to a file
        sys.stdout = self.file
        sys.stderr = self.file
        
    def hold_file_save(self):
        # only operates on file output
        if self.mode == "file":
            pass

    def resume_file_save(self):
        # stream out buffered data
        # switch off buffer
        pass

l = Print_Logging()
l.print_to_file()


# run the mouse code
import mouse
mouse.main()


