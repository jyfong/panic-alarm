from Tkinter import *
import time
import threading
import random
import Queue
import re
import sys
import d2xx
import tkMessageBox

class GuiPart:
    def __init__(self, master, queue, endCommand, send):
        self.queue = queue
        self.endCommand = endCommand
        self.send = send
        # Set up the GUI

        master.title("DF Panic Alarm")
        master.geometry("800x600+300+30")

        # create a toplevel menu
        menubar = Menu(master)
        menubar.add_command(label="Quit", command=endCommand)

        # display the menu
        master.config(menu=menubar)

        # create a frame for whole window
        topFrame = Frame(master)
        topFrame.pack()
        bottomFrame = Frame(master)
        bottomFrame.pack()

        # Top Frame Buttons
        b1 = Button(topFrame,text="Configure Central ID" ,command=self.printMsg)
        b1.grid(row=0,column=0)
        b2 = Button(topFrame,text="Button2", command=self.send)
        b2.grid(row=0,column=1)

        # Bottom Frame
        # Receive
        lbl1 = Label(bottomFrame, text="Receive")
        lbl1.grid(row=0,column=0)
        l1 = Listbox(bottomFrame)
        l1.grid(row=1,column=0)
        l1.insert(END, "00000005")
        l1.insert(END, "00000001")
        l1.insert(END, "00000000")

        # Send
        lbl2 = Label(bottomFrame, text="Send")
        lbl2.grid(row=0,column=1)
        self.l2 = Listbox(bottomFrame)
        self.l2.grid(row=1,column=1)

        console = Button(master, text='Done', command=self.endCommand)
        console.pack()

        master.protocol('WM_DELETE_WINDOW', self.on_exit)


    def printMsg(self):
        print "test"

    def on_exit(self):
        """When you click to exit, this function is called"""
        if tkMessageBox.askyesno("Exit", "Do you want to quit the application?"):
            root.destroy()
            self.endCommand()

    def processIncoming(self):
        """
        Handle all the messages currently in the queue (if any).
        """
        while self.queue.qsize():
            try:
                msg = self.queue.get(0)
                # Check contents of message and do what it says
                # As a test, we simply print it
                self.l2.insert(END, msg)
                print msg
            except Queue.Empty:
                pass

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
        self.master = master

        # Create the queue
        self.queue = Queue.Queue()

        # Set up the GUI part
        self.gui = GuiPart(master, self.queue, self.endApplication, self.send)

        # Set up the thread to do asynchronous I/O
        # More can be made if necessary
        self.running = 1
    	self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

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
        self.d = d2xx.open(0)
        self.d.setBaudRate(115200)
        self.d.setTimeouts(1, 0)
        buffer = ''
        try:
            while self.running:
                # time.sleep(10)
                # print ('t')
                b = self.d.read(1)

                if b != '' and b != '\r':
                    buffer += b

                if b == '\r':
                    print buffer, len(buffer)
                    # decode(buffer)
                    self.queue.put(buffer)
                    buffer = ''
        except:
            print 'close'
            self.d.close()

    def endApplication(self):
        self.running = 0

    def send(self):
        print self.d.write("ART00000005G\r")

rand = random.Random()
root = Tk()

client = ThreadedClient(root)
root.mainloop()