from Tkinter import *
from PIL import ImageTk, Image
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

state = 0 # for toggling fullscreen in mapWindow
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
        self.table = db['repeater']
        self.initPosition = "+300+30"


        # Set up the GUI

        master.title("DF Panic Alarm")
        master.geometry(self.initPosition)


        # create a toplevel menu
        menubar = Menu(master)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Clear DB", command=self.clearDatabase)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=endCommand)
        menubar.add_cascade(label="File", menu=filemenu)
        centralMenu = Menu(menubar, tearoff=0)
        centralMenu.add_command(label="MCU Reset", command=self.mcuReset )
        centralMenu.add_command(label="Check MCU ID", command=self.mcuIDChecking)
        menubar.add_cascade(label="Central Menu" ,menu=centralMenu )

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
        buttonwidth = 20
        b1 = Button(topFrame,text="Configure Central ID" ,command=self.configCentralId , width=buttonwidth)
        b1.grid(row=0,column=0, sticky=W)
        b2 = Button(topFrame,text="Ask Respond", command=self.askRespond , width=buttonwidth )
        b2.grid(row=0,column=1, sticky=W)
        b3 = Button(topFrame,text="Repeater Search Path", command=self.repeaterSearchPath , width=buttonwidth)
        b3.grid(row=0,column=2, sticky=W)
        b4 = Button(topFrame,text="All Repeater Search Path", command=self.allRepeaterSearchPath, width=buttonwidth )
        b4.grid(row=0,column=3, sticky=W)
        b5 = Button(topFrame,text="Check Central ID", command=self.mcuIDChecking, width=buttonwidth )
        b5.grid(row=0,column=4, sticky=W)
        b6 = Button(topFrame,text="Check Repeater Central ID", command=self.repeaterCheckCentralID , width=buttonwidth)
        b6.grid(row=1,column=0, sticky=W)
        b7 = Button(topFrame,text="Check Repeater Path", command=self.repeaterCheckPath , width=buttonwidth)
        b7.grid(row=1,column=1, sticky=W)
        b8 = Button(topFrame,text="Map", command=self.openMap , width=buttonwidth)
        b8.grid(row=1,column=2, sticky=W)

        #Initialize variables for UI
        listbox_width = 40

        # Middle Frame
        # Receive
        lbl1 = Label(middleFrame, text="Receive")
        lbl1.grid(row=0,column=0)
        scrollbar = Scrollbar(middleFrame)
        self.l1 = Listbox(middleFrame, width=listbox_width,yscrollcommand=scrollbar.set)
        self.l1.grid(row=1,column=0)
        scrollbar.grid(row=1,column=1,sticky=N+S)
        scrollbar.config( command = self.l1.yview)
        
        # Send
        # lbl2 = Label(middleFrame, text="Send")
        # lbl2.grid(row=0,column=2)
        # scrollbar2 = Scrollbar(middleFrame)
        # self.l2 = Listbox(middleFrame, width=listbox_width,yscrollcommand=scrollbar2.set)
        # self.l2.grid(row=1,column=2)
        # scrollbar2.grid(row=1,column=3,sticky=N+S)
        # scrollbar2.config( command = self.l2.yview)
        
        # Bottom Frame 
        # Console logging
        scrollbar3 = Scrollbar(bottomFrame)
        self.log = Text(bottomFrame,yscrollcommand=scrollbar3.set)
        self.log.grid(row=0,column=0)
        scrollbar3.grid(row=0,column=1,sticky=N+S)
        scrollbar3.config( command = self.log.yview)
        clearlog_button = Button(bottomFrame,text="Clear log", command=self.clearLogger )
        clearlog_button.grid(row=1,column=0, sticky=W)

        master.protocol('WM_DELETE_WINDOW', self.on_exit)
        master.resizable(0,0)


        for repeater in self.table:
            self.l1.insert(END, repeater['repeater'])


    def logger(self, msg):
        self.log.insert(END, msg)

    def clearLogger(self):
        self.log.delete('0.0', END)

    def configCentralId(self):
        currentValue = self.l1.get(self.l1.curselection())
        self.send(b"ART"+ currentValue +"G\r")
        msg = "Setting Device ID=" + currentValue + " to this central\n" 
        self.logger(msg)

    def askRespond(self):
        currentValue = self.l1.get(self.l1.curselection())
        self.send(b"ART"+ currentValue +"Z\r")
        msg = "Asking Device ID=" + currentValue + " to respond...\n" 
        self.logger(msg)

    def repeaterSearchPath(self):
        currentValue = self.l1.get(self.l1.curselection())
        self.send(b"ART"+ currentValue +"S000\r")
        msg = "Asking Device ID=" + currentValue + " to search path... Please wait 1 minute..\n"
        self.logger(msg)

    def allRepeaterSearchPath(self):
        self.send(b"ART00000000S000\r")
        self.logger("Asking all repeater to search path... Please wait for reply..\n")

    def mcuIDChecking(self):
        self.send(b"ARI\r")
        # msg = "Central ID=" + currentValue + " to respond...\n" 
        # self.logger(msg)
    
    def repeaterCheckCentralID(self):
        currentValue = self.l1.get(self.l1.curselection())
        self.send(b"ART"+ currentValue + "F\r")
        msg = "Checking Repeater Central ID = " + currentValue + " ..\n"
        self.logger(msg)

    def repeaterCheckPath(self):
        currentValue = self.l1.get(self.l1.curselection())
        self.send(b"ART"+ currentValue + "U\r")
        msg = "Checking Repeater Path = " + currentValue + " ..\n"
        self.logger(msg)
    
    def clearDatabase(self):
        try:
            if tkMessageBox.askyesno("Database Operation", "Do you want to clear the database?"):
                self.table.drop()
        except:
            print "Database already drop and don't exist"
    
    def mcuReset(self):
        if tkMessageBox.askyesno("MCU Operation", "Do you want to reset the MCU?"):
            self.send(b"ARR\r")
            self.logger("MCU Reset..\n")

    def decode(self,b):

        m = re.match('RA(\w)(\d{8})(.{2})?', b)
        if m:
            print m.group(0),'Cmd:', m.group(1), 'Repeater:', m.group(2), 'RSSI: -', m.group(3)

            cmd = m.group(1)
            repeater = m.group(2)
            RSSI = m.group(3)

            if cmd == 'A':
                msg = "Repeater with ID = "+ repeater + " has acknowledged..\n"
                self.logger(msg)
            elif cmd == "I":
                msg = "Central ID = " + repeater + "\n"
                self.logger(msg)
                if not self.table.find_one(repeater=repeater):
                    self.l1.insert(END, repeater)
                    self.table.insert(dict(repeater=repeater))
            elif cmd == "E":
                msg = "Repeater with ID = " + repeater + " has responded..\n"
                self.logger(msg)
            elif cmd == "C":
                msg = "Repeater with ID = " + repeater + " has finished searching path..\n"
                self.logger(msg)
                
                if 'searchedPath' in dir(self):
                    self.searchedPath.append(repeater)
                    print self.searchedPath
                    listofRepeaters = self.l1.get(0, END)
                    diff = list(set(listofRepeaters) - set(self.searchedPath))
                    for i in range(len(self.l1.get(0, END))):
                        self.l1.itemconfig(i, {'bg' : 'green'})
                    for repeater in diff:
                        index = self.getIndexOfListbox(repeater)
                        self.l1.itemconfig(index, {'bg':'red'})         

                else:
                    self.searchedPath = []
                    self.searchedPath.append(repeater)
            elif cmd == "F":
                msg = "Repeater central ID = " + repeater + " ..\n"
                self.logger(msg)
            elif int(cmd) in range(1,4):
                msg = "Repeater path " + cmd + " = " + repeater + " ..\n"
                self.logger(msg)


        else:
            print 'Cant decode', b

    def getIndexOfListbox(self,item):
        for i in range(len(self.l1.get(0, END))):
            if self.l1.get(i) == item:
                return i

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
                # print 'queue'
                msg = self.queue.get(0)
                # Check contents of message and do what it says
                # As a test, we simply print it
                self.decode(msg)
            except Queue.Empty:
                pass


    ####                 ###
    ####   Map Window    ###
    ####                 ###
    
    def openMap(self):
        # topLevel method is to open new window
        # 
        
        mapWindow = Toplevel(self.master)
        self.mapWindow = mapWindow
        mapWindow.attributes('-fullscreen', True)
        mapWindow.geometry(self.initPosition)
        mapWindow.bind('<Escape>',self.toggleFullScreen)

        # Frames for map window
        mapWindowTop = Frame(mapWindow)
        mapWindowTop.pack(side=TOP)
        mapWindowBottom = Frame(mapWindow)
        mapWindowBottom.pack()

        canvas = Canvas(mapWindowBottom, width=mapWindow.winfo_screenwidth()-4, height=mapWindow.winfo_screenheight()-4)
        canvas.pack()

        im = Image.open('map.jpg')
        # Put the image into a canvas compatible class, and stick in an
        # arbitrary variable to the garbage collector doesn't destroy it
        canvas.image = ImageTk.PhotoImage(im)
        canvas.create_image(0, 0, image=canvas.image, anchor='nw')

        # Buttons for map window
        buttonwidth = 20
        b1 = Button(mapWindowTop,text="Upload" ,command=self.uploadImage , width=buttonwidth)
        b1.grid(row=0,column=0, sticky=W)
        b2 = Button(mapWindowTop,text="Ask Respond" , width=buttonwidth )
        b2.grid(row=0,column=1, sticky=W)

    def uploadImage(self):
        pass

    
    def toggleFullScreen(self,event):
        global state
        if state==0:
            self.mapWindow.attributes('-fullscreen', False)
            state = 1
        elif state==1:
            self.mapWindow.attributes('-fullscreen', True)
            state = 0
        

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
            self.d.close()
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


        self.d = d2xx.open(0)
        self.d.setBaudRate(115200)
        self.d.setTimeouts(1, 0)

        
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
            print 'Closed', sys.exc_info()[0]
            self.d.close()

    def endApplication(self):
        self.running = 0

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
