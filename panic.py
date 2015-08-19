from Tkinter import *
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

# connecting to a SQLite database
db = dataset.connect('sqlite:///mydatabase.db')

class GuiPart:
    def __init__(self, master, queue, endCommand, send):
        self.master = master
        self.queue = queue
        self.endCommand = endCommand
        self.send = send
        self.repeater = None
        self.current = None
        # Set up the GUI

        master.title("DF Panic Alarm")
        master.geometry("+300+30")

        # create a toplevel menu
        menubar = Menu(master)
        menubar.add_command(label="Quit", command=endCommand)

        # display the menu
        master.config(menu=menubar)

        # Init a frame for whole window
        topFrame = Frame(master)
        topFrame.pack(side=TOP,fill=BOTH, expand=1)
        middleFrame = Frame(master)
        middleFrame.pack(side=TOP,fill=BOTH, expand=1)
        bottomFrame = Frame(master)
        bottomFrame.pack(side=BOTTOM,fill=BOTH, expand=1)


        # Top Frame Buttons
        b1 = Button(topFrame,text="Configure Central ID" ,command=self.configCentralId )
        b1.grid(row=0,column=0)
        b2 = Button(topFrame,text="Ask Respond", command=lambda: send("ART"+self.l1.get(self.l1.curselection())+"Z\r"))
        b2.grid(row=0,column=1)
        b3 = Button(topFrame,text="Repeater Search Path", command=lambda: send("ART"+self.l1.get(self.l1.curselection())+"S000\r"))
        b3.grid(row=0,column=3)
        b4 = Button(topFrame,text="All Repeater Search Path", command=lambda: send("ART00000000S000\r"))
        b4.grid(row=0,column=4)
        b5 = Button(topFrame,text="MCU ID Checking", command=lambda: send("ARI\r"))
        b5.grid(row=0,column=5)

        #Initialize variables for UI
        listbox_width = 51

        # Middle Frame
        # Receive
        lbl1 = Label(middleFrame, text="Receive")
        lbl1.grid(row=0,column=0)
        scrollbar = Scrollbar(middleFrame)
        self.l1 = Listbox(middleFrame, width=listbox_width,yscrollcommand=scrollbar.set)
        self.l1.grid(row=1,column=0)
        scrollbar.grid(row=1,column=1,sticky=N+S)
        scrollbar.config( command = self.l1.yview)
        self.l1.insert(END, "00000005")
        self.l1.insert(END, "00000009")
        
        # Send
        lbl2 = Label(middleFrame, text="Send")
        lbl2.grid(row=0,column=2)
        scrollbar2 = Scrollbar(middleFrame)
        self.l2 = Listbox(middleFrame, width=listbox_width,yscrollcommand=scrollbar2.set)
        self.l2.grid(row=1,column=2)
        scrollbar2.grid(row=1,column=3,sticky=N+S)
        scrollbar2.config( command = self.l2.yview)
        
        # Bottom Frame 
        # Console logging
        scrollbar3 = Scrollbar(bottomFrame)
        self.log = Text(bottomFrame,yscrollcommand=scrollbar3.set)
        self.log.grid(row=0,column=0)
        scrollbar3.grid(row=0,column=1,sticky=N+S)
        scrollbar3.config( command = self.log.yview)

        master.protocol('WM_DELETE_WINDOW', self.on_exit)

    def logger(self, msg):
        self.log.insert(END, msg)

    def configCentralId(self):
        currentValue = self.l1.get(self.l1.curselection())
        self.send("ART"+ currentValue +"G\r")
        msg = "Device ID=" + currentValue + " is set to this central\n" 
        self.logger(msg)

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
                self.logger(msg+"\n")
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


    def decode(b):

        m = re.match('RA(\w)(\d{8})(.{2})?', b)
        if m:
            print m.group(0),'Cmd:', m.group(1), 'Repeater:', m.group(2), 'RSSI: -', m.group(3)

            cmd = m.group(1)
            repeater = m.group(2)
            RSSI = m.group(3)

            if cmd == 'I':
                pass
                # repeaters.add(repeater)

        else:
            print 'Something happen', b

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
        time.sleep(1) # cheat the program to let UI finish loading
        buffer = ''
        try:
            while self.running:
                time.sleep(0.1)
                b = self.d.read(1)

                if b != '' and b != '\r':
                    buffer += b

                if b == '\r':
                    print buffer, len(buffer)
                    # self.decode(buffer)
                    self.queue.put(buffer)
                    buffer = ''
        except:
            print 'Closed', sys.exc_info()[0]
            self.d.close()

    def endApplication(self):
        self.running = 0

    def send(self, cmd):
        print self.d.write(cmd), cmd

if __name__ == '__main__':
    try:
        root = Tk()

        client = ThreadedClient(root)
        root.mainloop()
    except KeyboardInterrupt:
        print 'Interrupted'
        try:
            sys.exit(1)
        except SystemExit:
            os._exit(0)
