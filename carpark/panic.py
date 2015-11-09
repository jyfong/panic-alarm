from Tkinter import *
from PIL import ImageTk, Image
import tkFileDialog
import time
import threading
import random
import Queue
import re
import sys
import d2xx
import tkMessageBox
import os
import dataset
import winsound
import time
import tkSimpleDialog
import customtkSimpleDialog
import admin
import guardMultiListBox
import multiListBox

from guipart import GuiPart
from dialog import LoginDialog, PanicDialog, ConfirmedPanicDialog

# connecting to a SQLite database
db = dataset.connect('sqlite:///mydatabase.db')


class ThreadedClient:
    """
    Launch the main part of the GUI and the worker thread. periodicCall and
    endApplication could reside in the GUI part, but putting them here
    means that you have all the thread controls in a single place.
    """
    def __init__(self, master):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI. We spawn a new thread for the worker.
        """
        try:
            d = d2xx.open(0)
            d.purge(0)
            d.purge(1)
            d.resetPort()
            d.close()
        except:
            print 'resetport'

        self.master = master

        # Create the queue
        self.queue = Queue.Queue()

        # Set up the thread to do asynchronous I/O
        # More can be made if necessary
        self.running = 1
        # self.thread1 = threading.Thread(target=self.workerThread1)
        # self.thread1.start()

        # Set up the GUI part
        self.gui = GuiPart(master, self.queue, self.endApplication, self.send)

        
        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall()

    def periodicCall(self):
        """
        Check every 100 ms if there is something new in the queue.
        """
        self.gui.processIncoming()
        if not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            import sys
            sys.exit(1)
        self.master.after(1000, self.periodicCall)


    def workerThread1(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select()'.
        One important thing to remember is that the thread has to yield
        control.
        """

        time.sleep(1) # cheat the program to let UI finish loading

        try:
            self.d = d2xx.open(0)
            self.d.setBaudRate(115200)
            self.d.setTimeouts(1, 0)
        except:
            self.queue.put("exit")
            self.running = 0
            return
        
        buffer = ''
        try:
            while self.running:
                time.sleep(0.01)
                b = self.d.read(1)


                if b != '' and b != '\r':
                    buffer += b

                if b == '\r':
                    print "Receive:", buffer, len(buffer)
                    self.queue.put(buffer)
                    buffer = ''
                    
        except:
            self.queue.put("error")
            print 'Closed', sys.exc_info()
            self.d.close()
            

    def endApplication(self):
        self.running = 0
        # try:
        self.d.close()
            # pass
        # except:
        #     print "Can't shutdown application."

    def send(self, cmd):
        print "Sending : Bytes sent-", self.d.write(cmd),"Command -", cmd


if __name__ == '__main__':
    try:
        root = Tk()

        client = ThreadedClient(root)
        root.mainloop()
    except KeyboardInterrupt:
        print 'Interrupted'
        try:
            client.endApplication()
            sys.exit(1)
        except SystemExit:
            client.endApplication()
            os._exit(0)
