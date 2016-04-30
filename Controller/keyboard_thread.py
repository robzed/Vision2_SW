# based on http://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
import sys
#from subprocess import PIPE, Popen
from threading  import Thread

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names


class KeyThread:
    def __init__(self):

        #p = Popen(['myprogram.exe'], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
        self.q = Queue()
        t = Thread(target=self.enqueue_output, args=(self))
        t.daemon = True # thread dies with the program
        t.start()
        
    def enqueue_output(self):
        while True:
            line = sys.stdin.readline()
            for c in line:
                self.queue.put(c)

    def get_key(self):
        try:  
            key = self.q.get_nowait() # or q.get(timeout=.1)
        except Empty:
            return None
        else:
            return key
