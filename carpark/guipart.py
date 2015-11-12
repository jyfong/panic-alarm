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
import schedule
from pygame import mixer

import sqlalchemy
import sqlite3
import os.path
from os import listdir, getcwd

from dialog import LoginDialog, PanicDialog, ConfirmedPanicDialog, HealthSignalDialog, healthSignalFailDialog
from point import Point, ResizingCanvas

db = dataset.connect('sqlite:///mydatabase.db')
state = 0 # for toggling fullscreen in mapWindow

class GuiPart:
    def __init__(self, master, queue, endCommand, send):
        self.master = master
        self.queue = queue
        self.endCommand = endCommand
        self.send = send
        self.repeater = None
        self.current = None
        self.listen = False
        self.initPosition = "+250+50"
        self.db_file = "mydatabase.db"
        self.initDB()
        self.logger("Program startup properly..\n")

        toplevel = master.winfo_toplevel()
        toplevel.wm_state('zoomed')

        self.centralId = "00000001"
        self.do_blink = False
        self.isSos = False
        self.isOpenPanicDialog = False
        self.panicdlg = None
        self.lastpanic = None
        self.lastpanictime = None

        healthData = self.tableConfig.find_one(type="signal")
        schedule.every().day.at(healthData['healthSignalCheckTime']).do(self.job)
        # schedule.every(3).minutes.do(self.job)


        # Add default admin user and password
        if self.tableUsers.count() == 0:
            self.tableUsers.insert(dict(username="admin",password="admin",role=""))

        # Set up the GUI
        master.title("DF Panic Alarm")
        # master.overrideredirect(True)
        w, h = master.winfo_screenwidth(), master.winfo_screenheight()
        # master.attributes('-fullscreen', True)
        master.geometry("%dx%d+0+0" % (w, h))

        # create a toplevel menu
        menubar = Menu(master)

        # manage
        manageMenu = Menu(menubar, tearoff=0)
        manageMenu.add_command(label="Admin", command=lambda:self.addUsers(master))
        manageMenu.add_command(label="Installer",command=lambda:self.openInstaller())
        menubar.add_cascade(label="Manage" ,menu=manageMenu )

        # view 
        menubar.add_command(label="New Alarms",command=lambda:PanicDialog(master,self))
        menubar.add_command(label="All Alarms",command=lambda:ConfirmedPanicDialog(master))
        menubar.add_command(label="Health Signal",command=lambda:HealthSignalDialog(master))
        # display the menu
        master.config(menu=menubar)

        master.protocol('WM_DELETE_WINDOW', self.on_exit)

        # Paned window
        paned = PanedWindow(master, orient=HORIZONTAL, showhandle=0, handlepad=0, 
            handlesize=0, sashwidth=5, opaqueresize=1, bg="grey")
        paned.pack(side=LEFT, expand=YES, fill=BOTH)
        leftFrame = Frame(paned, border=0)
        rightFrame = Frame(paned)
        paned.add(leftFrame,minsize=16)
        paned.add(rightFrame,minsize=16)

        self.hbar=Scrollbar(rightFrame,orient=HORIZONTAL)
        self.hbar.pack(side=BOTTOM,fill=X)
        self.vbar=Scrollbar(rightFrame,orient=VERTICAL)
        self.vbar.pack(side=RIGHT,fill=Y)

        self.openGuardMap(rightFrame)

        # Listbox for details
        self.mlb = guardMultiListBox.MultiListbox(leftFrame, (('RepeaterID', 15), ('Name', 20)), self.selectedlistbox)
        # for i in range(1000):
        #     mlb.insert(END, ('Important Message: %d' % i, 'John Doe', '10/10/%04d' % (1900+i)))
        self.mlb.pack(expand=YES,fill=BOTH)


        row = self.tableConfig.find_one(type='map')
        if row:
            self.resizeImage(self.guardcanvas, row['map_width'], row['map_height'])

        try:
            mixer.init()
            mixer.music.load('siren.mp3')
        except:
            if tkMessageBox.showerror("No audio driver found!", "Please install audio driver and restart the program."):
                pass

        self.updateMLB()
        self.updateGuardMap()
        self.checkPanic()
        self.checkHealthSignal()

    def job(self):
        print 'job'
        currentTime = time.time()
        repeaters = db.query('SELECT repeater,name,lastHealthSignal FROM repeater WHERE '+ str(currentTime) + '- lastHealthSignal > 24*60*60 OR lastHealthSignal IS NULL')

        for r in repeaters:
            healthSignalFail = healthSignalFailDialog(self.master,self, False)
            break
        
    def updateMLB(self):
        self.mlb.delete(0,END)

        for item in self.table:
            self.mlb.insert(END, (item['repeater'], item['name']))  

    def initDB(self):
        self.table = db['repeater']
        self.tableImage = db['image']
        self.tableLog = db['log']
        self.tableUsers = db['users']
        self.tablePanic = db['panic']
        self.tableHistory = db['history']
        self.tableConfig = db['config']

        self.tablePanic.create_column('time', sqlalchemy.Integer)
        self.tablePanic.create_column('repeater', sqlalchemy.String)
        self.tablePanic.create_column('acknowledged', sqlalchemy.String)

        self.tableHistory.create_column('time', sqlalchemy.Integer)
        self.tableHistory.create_column('repeater', sqlalchemy.String)
        self.tableHistory.create_column('acknowledged', sqlalchemy.String)

        self.table.create_column('repeater', sqlalchemy.String)
        self.table.create_column('name', sqlalchemy.String)
        self.table.create_column('address', sqlalchemy.String)
        self.table.create_column('phone', sqlalchemy.String)
        self.table.create_column('lastHealthSignal', sqlalchemy.Integer)
        self.initPictureTable()
        healthsignal = self.tableConfig.find_one(type="signal")
        if not healthsignal:
            self.tableConfig.insert(dict(type="signal",healthSignalCheckTime="10:00"))


    def initPictureTable(self):
        conn = sqlite3.connect(self.db_file)
        # if db_is_new:
        print 'Creating schema'
        sql = '''create table if not exists PICTURE(
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        PICTURE BLOB,
        TYPE TEXT,
        FILE_NAME TEXT);'''
        conn.execute(sql) # shortcut for conn.cursor().execute(sql)
        conn.close()
        self.tablePicture = db["PICTURE"]


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
                if msg == "exit":
                    self.deviceError()
                if msg == "error":
                    self.deviceError()
                else:
                    self.decode(msg)
            except Queue.Empty:
                pass


    def decode(self,b):

        m = re.match('.*RA(\w)(.{8})(.{2})?', b)
        if m:
            print m.group(0),'Cmd:', m.group(1), 'Repeater:', m.group(2), 'RSSI: -', m.group(3)

            cmd = m.group(1)
            repeater = m.group(2)
            RSSI = m.group(3)


            if cmd == "I":
                if self.listen == True:

                    msg = "Setting Repeater Central ID = " + repeater + "\n"
                    self.logger(msg)
                    if not self.table.find_one(repeater=repeater):
                        self.l1.insert(END, repeater)
                        self.table.insert(dict(repeater=repeater, coordx=100, coordy=100))

            elif not (self.table.find_one(repeater=repeater) or '00000000' == repeater):
                print "Alien Discovered", repeater
                return

            elif cmd == 'A':
                msg = "Repeater with ID = "+ repeater + " has acknowledged..\n"
                self.logger(msg)
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
            elif cmd == "P":
                if self.lastpanic == repeater and (time.time() - self.lastpanictime < 5):
                    print 'droped panic', repeater
                else:
                    self.lastpanic = repeater
                    self.lastpanictime = time.time()
                    msg = "Repeater central ID = " + repeater + " PANIC ALARM! \n"
                    self.logger(msg)
                    # house.isPanic = True
                    self.panicAlarm(cmd, repeater)
            elif cmd == "J":
                msg = "Current Central ID= " + repeater + "..\n"
                self.logger(msg)
            elif cmd == "R":
                msg = "Health signal from " + repeater + " received..\n"
                self.logger(msg)
                self.table.upsert(dict(repeater=repeater,lastHealthSignal=time.time()),['repeater'])

            # elif int(cmd) in range(1,4):
            #     msg = "Repeater path " + cmd + " = " + repeater + " ..\n"
            #     self.logger(msg)


        else:
            print 'Cant decode', b

    def deviceError(self):
        self.logger("Device disconnected..\n")
        try:
            self.sosThread = threading.Thread(target=lambda:self.sos(True))
            self.sosThread.start()
        except:
            print "Fail to start thread.."

        if tkMessageBox.showerror("Device Not Found!", "Please reconnect Central Device .."):
            python = sys.executable
            os.execl(python, python, * sys.argv)


    def start_blinking(self):
        # print "start blink"
        self.do_blink = True
        # print self.do_blink
        

    def stop_blinking(self):
        self.do_blink = False
        try:
            mixer.music.stop()
        except:
            print "No music init"

    def stopAlarmSiren(self):
        self.warning = False
        try:
            mixer.music.stop()
        except:
            print "No music init"

    # admin page
    def addUsers(self,master):
        login = LoginDialog(master)
        if login.result == 1:
            adminPage = admin.AdminPage(master, self)


    def logger(self, msg):
        print 'logger', msg
        now = time.localtime()
        msg = time.strftime("%y/%m/%d %H:%M", now) + " " +  msg
        timeinsec = time.time()
        if 'log' in dir(self):
            self.log.insert(END, msg)
        # print 'logger2', timeinsec, msg, self
        self.tableLog.insert(dict(time=timeinsec,msg=msg))
        # print 'logger3'


   
    def selectedlistbox(self):
        # print 'selected'
        repeaterID = self.mlb.get(self.mlb.curselection())[0]
        self.guardcanvas.itemconfigure("house", fill="green")
        self.guardcanvas.itemconfigure(self.findHouseByRepeater(repeaterID).item, fill="yellow")

    def onPointSelect(self, repeater):
        # print 'select', repeater
        self.mlb.selection_clear(0, END)
        for i in range(self.mlb.size()):
            if repeater == self.mlb.get(i)[0]:
                # print self.mlb.get(i)[0], i
                self.mlb.selection_set(i)
                self.selectedlistbox()

    def sos(self,warning=False):
        self.warning = warning
        self.isSos = True
        while self.do_blink or self.warning:
            # for i in range(0, 3): winsound.Beep(2500, 100) 
            # for i in range(0, 3): winsound.Beep(2500, 100) 
            # for i in range(0, 3): winsound.Beep(2500, 100)
            try:
                mixer.music.play()
            except:
                print "No music init cant play."
            time.sleep(3)
        self.isSos = False

    def panicAlarm(self, cmd, repeater):
        if self.listen == False:
            currentTime = time.time()
            self.tablePanic.insert(dict(repeater=repeater, time=currentTime,acknowledged="None"))
            print currentTime, repeater
            self.checkPanic()
        

    def checkPanic(self):
        # print 'checkpanic'

        pendingPanic = db.query('SELECT panic.time, panic.repeater, repeater.name FROM panic, repeater WHERE panic.repeater = repeater.repeater AND panic.acknowledged=="None"')
        # self.doBlinkThread = dict()
        try:
            if not self.isSos:
                self.sosThread = threading.Thread(target=self.sos)
                self.sosThread.start()
        except:
            print "Fail to start thread.."

        for item in pendingPanic:
            if not self.table.find_one(repeater=item['repeater']):
                continue
            house = self.findHouseByRepeater(item['repeater'])
            if house != -1:
                if house.isPanic == False:
                    house.isPanic = True
                    self.start_blinking()
                    self.blink(house.item)
                    # self.doBlinkThread[item['repeater']] = threading.Thread(target=lambda:self.blink(house.item))
                    # self.doBlinkThread[item['repeater']].start()

        self.openPanicDlg()

    def openPanicDlg(self):
        # print 'openpanic'
        if self.tablePanic.find_one(acknowledged="None"):
            if self.isOpenPanicDialog:
                self.panicdlg.loadPendingAlarm()
            else:
                self.panicdlg = PanicDialog(self.master,self, False)
        self.master.after(120000, lambda:self.openPanicDlg())   

    def checkHealthSignal(self):
        schedule.run_pending()
        self.master.after(60000, lambda:self.checkHealthSignal()) 

    def on_exit(self):
        """When you click to exit, this function is called"""
        if tkMessageBox.askyesno("Exit", "Do you want to quit the application?"):
            self.logger("Program shutdown properly..\n")
            self.master.destroy()
            self.endCommand()

########################################## INSTALLER WINDOW ################################################



    # installer page
    def openInstaller(self):
        
        result =  tkSimpleDialog.askstring("Database Operation", "Please enter password :", show='*')
        if result == "dfelectronic":
            self.addDevicesWindow = Toplevel(self.master)
            # Menubar for addDevices window
            menubar = Menu(self.addDevicesWindow)
            # filemenu = Menu(menubar, tearoff=0)
            # filemenu.add_command(label="Clear DB", command=self.clearDatabase)
            # filemenu.add_separator()
            # menubar.add_cascade(label="File", menu=filemenu)
            # centralMenu = Menu(menubar, tearoff=0)
            # centralMenu.add_command(label="MCU Reset", command=self.mcuReset )
            # centralMenu.add_command(label="Check MCU ID", command=self.mcuIDChecking)
            # menubar.add_cascade(label="Central Menu" ,menu=centralMenu )

            self.addDevicesWindow.config(menu=menubar)

            topFrame = LabelFrame(self.addDevicesWindow, text="Configure", padx= 5 , pady= 5)
            topFrame.pack(side=TOP,fill=BOTH, expand=1)
            middleFrame = LabelFrame(self.addDevicesWindow , text="Devices", padx= 5 , pady= 5)
            middleFrame.pack(side=LEFT,fill=BOTH, expand=1)
            middleFrameRight = LabelFrame(self.addDevicesWindow , text="Information", padx= 10 , pady= 10)
            middleFrameRight.pack(side=LEFT,fill=BOTH, expand=1)
            bottomFrame = LabelFrame(self.addDevicesWindow,text="Event Log", padx= 5 , pady= 5 )
            bottomFrame.pack(side=BOTTOM,fill=BOTH, expand=1)    
            # Init a frame for whole window

            # Top Frame Buttons
            buttonwidth = 20
            self.b0 = Button(topFrame,text="Listen Mode" ,command=self.listenMode , width=buttonwidth)
            self.b0.grid(row=0,column=0, sticky=W)
            # b1 = Button(topFrame,text="Configure Central ID" ,command=self.configCentralId , width=buttonwidth)
            # b1.grid(row=0,column=1, sticky=W)
            b2 = Button(topFrame,text="Ask Respond", command=self.askRespond , width=buttonwidth )
            b2.grid(row=0,column=1, sticky=W)
            # b3 = Button(topFrame,text="Repeater Search Path", command=self.repeaterSearchPath , width=buttonwidth)
            # b3.grid(row=0,column=3, sticky=W)
            # b4 = Button(topFrame,text="All Repeater Search Path", command=self.allRepeaterSearchPath, width=buttonwidth )
            # b4.grid(row=0,column=4, sticky=W)
            
            # Second Row
            # b5 = Button(topFrame,text="Check Central ID", command=self.mcuIDChecking, width=buttonwidth )
            # b5.grid(row=1,column=0, sticky=W)
            # b6 = Button(topFrame,text="Check Repeater Central ID", command=self.repeaterCheckCentralID , width=buttonwidth)
            # b6.grid(row=1,column=1, sticky=W)
            # b7 = Button(topFrame,text="Check Repeater Path", command=self.repeaterCheckPath , width=buttonwidth)
            # b7.grid(row=1,column=2, sticky=W)
            b7 = Button(topFrame,text="Disable All Alarm", command=self.disableAllAlarm , width=buttonwidth)
            b7.grid(row=1,column=0, sticky=W)
            b8 = Button(topFrame,text="Map", command=lambda:self.openMap() , width=buttonwidth)
            b8.grid(row=1,column=1, sticky=W)
            b9 = Button(topFrame,text="View Old Logs", command=self.openLog , width=buttonwidth)
            b9.grid(row=1,column=2, sticky=W)

            #Initialize variables for UI
            listbox_width = 40

            # Middle Frame
            # Devices and owner information
            scrollbar = Scrollbar(middleFrame)
            self.l1 = Listbox(middleFrame, width=listbox_width,yscrollcommand=scrollbar.set, exportselection=0, height=24)
            self.l1.grid(row=1,column=0)
            self.l1.bind("<<ListboxSelect>>", self.loadEntry)
            scrollbar.grid(row=1,column=1,sticky=N+S)
            scrollbar.config( command = self.l1.yview)
            nameLabel = Label(middleFrameRight, text="Name")
            nameLabel.grid(row=0, column=0)
            self.nameVar = StringVar()
            self.name = Entry(middleFrameRight, textvariable=self.nameVar)
            self.name.grid(row=1,column=0)
            # addressLabel = Label(middleFrameRight, text="Address")
            # addressLabel.grid(row=2, column=0)
            # self.addressVar = StringVar()
            # self.address = Entry(middleFrameRight, textvariable=self.addressVar)
            # self.address.grid(row=3,column=0)
            # phoneLabel = Label(middleFrameRight, text="Phone")
            # phoneLabel.grid(row=4, column=0)
            # self.phoneVar = StringVar()
            # self.phone = Entry(middleFrameRight, textvariable=self.phoneVar)
            # self.phone.grid(row=5,column=0)

            
            # Middle Frame Buttons 
            # b9 = Button(middleFrameRight,text="Load", command=self.loadEntry , width=buttonwidth)
            # b9.grid(row=6,column=0, sticky=W)
            b10 = Button(middleFrameRight,text="Update", command=self.updateEntry , width=buttonwidth)
            b10.grid(row=7,column=0, sticky=W)
            b11 = Button(middleFrameRight,text="Delete", command=self.deleteEntry , width=buttonwidth)
            b11.grid(row=8,column=0, sticky=W)
            
            # Bottom Frame 
            # Console logging
            scrollbar3 = Scrollbar(bottomFrame)
            self.log = Text(bottomFrame,yscrollcommand=scrollbar3.set)
            self.log.grid(row=0,column=0)
            scrollbar3.grid(row=0,column=1,sticky=N+S)
            scrollbar3.config( command = self.log.yview)
            clearlog_button = Button(bottomFrame,text="Clear log", command=self.clearLogger )
            clearlog_button.grid(row=1,column=0, sticky=W)

            self.addDevicesWindow.protocol('WM_DELETE_WINDOW', self.closeAddDevicesWindow)

            for repeater in self.table:
                self.l1.insert(END, repeater['repeater'])
            self.l1.select_set(1)

        else:
            tkMessageBox.showwarning("Error","Wrong Password!")



    def configCentralId(self):
        currentValue = self.l1.get(self.l1.curselection())
        self.send(b"ART"+ currentValue +"G\r")
        msg = "Setting Device ID = " + currentValue + " to this central\n" 
        self.logger(msg)

    def askRespond(self):
        currentValue = self.l1.get(self.l1.curselection())
        self.send(b"ART"+ currentValue +"Z\r")
        msg = "Asking Device ID = " + currentValue + " to respond...\n" 
        self.logger(msg)

    def repeaterSearchPath(self):
        currentValue = self.l1.get(self.l1.curselection())
        self.send(b"ART"+ currentValue +"S000\r")
        msg = "Asking Device ID = " + currentValue + " to search path... Please wait 1 minute..\n"
        self.logger(msg)

    def allRepeaterSearchPath(self):
        del self.repeaterSearchPath
        self.send(b"ART00000000S000\r")
        self.logger("Asking all repeater to search path... Please wait for reply..\n")

    def disableAllAlarm(self):
        self.send(b"ART00000000K\r")
        self.logger("Disabling All Alarm..\n")
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
        result =  tkSimpleDialog.askstring("Database Operation", "Please enter password :")
        if result == "df1397":
            self.table.drop()
            self.tableImage.drop()
            self.tableLog.drop()
            tkMessageBox.showinfo("Success","Database deleted ..")
        else:
            tkMessageBox.showwarning("Error","Wrong Password!")

    def mcuReset(self):
        if tkMessageBox.askyesno("MCU Operation", "Do you want to reset the MCU?"):
            self.send(b"ARR\r")
            self.logger("MCU Reset..\n")


    def getIndexOfListbox(self,item):
        for i in range(len(self.l1.get(0, END))):
            if self.l1.get(i) == item:
                return i


    def updateEntry(self):
        repeaterID = self.l1.get(self.l1.curselection())
        self.table.upsert(dict(repeater=repeaterID,name=self.nameVar.get()), ['repeater'] )

    def deleteEntry(self):
        repeaterID = self.l1.get(self.l1.curselection())
        self.table.delete(repeater=repeaterID)
        self.l1.delete(0,END)
        for repeater in self.table:
            self.l1.insert(END, repeater['repeater'])

    def loadEntry(self, event):
        
        repeaterID = self.l1.get(self.l1.curselection())
        row = self.table.find_one(repeater=repeaterID)
        self.nameVar.set(row['name'])



    def listenMode(self):
        self.listen = not self.listen
        if self.listen == True:
            self.b0.config(relief=SUNKEN)
        else:
            self.b0.config(relief=RAISED) 


    def closeAddDevicesWindow(self):
        del self.log
        self.updateGuardMap()
        self.updateMLB()
        self.addDevicesWindow.destroy()


############################################### LOG ####################################################
    ####                 ###
    ####   Log Window    ###
    ####                 ###    

    def openLog(self):
        logWindow = Toplevel(self.master)
        logWindowTop = LabelFrame(logWindow, text="Event Log")
        logWindowTop.pack(side=TOP)

        scrollbar = Scrollbar(logWindowTop)
        historylog = Text(logWindowTop,yscrollcommand=scrollbar.set)
        historylog.grid(row=0,column=0)
        scrollbar.grid(row=0,column=1,sticky=N+S)
        scrollbar.config( command = historylog.yview)

        logs = self.tableLog.all()

        for log in logs:
            msg = log["msg"]
            historylog.insert(END,msg)





    def clearLogger(self):
        self.log.delete('0.0', END)



################################################ INSTALLER MAP ########################################


    ####                 ###
    ####   Map Window    ###
    ####                 ###
    
    def openMap(self):
        
        # topLevel method is to open new window
        
        mapWindow = Toplevel(self.master)

        self.mapWindow = mapWindow
        # mapWindow.attributes('-fullscreen', True)
        toplevel = mapWindow.winfo_toplevel()
        # toplevel.wm_state('zoomed')
        w, h = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        mapWindow.geometry("%dx%d+0+0" % (w, h))
        
        mapWindow.bind('<Escape>',self.toggleFullScreen)

        # Frames for map window
        mapWindowTop = Frame(mapWindow)
        mapWindowTop.pack(side=TOP)
        mapWindowBottom = Frame(mapWindow)
        mapWindowBottom.pack()
        # mapWindowBottom.bind('<Configure>', self.resizeImage)
        
        vbar = Scrollbar(mapWindowTop, orient=VERTICAL)
        hbar = Scrollbar(mapWindowTop, orient=HORIZONTAL)
        self.admincanvas = ResizingCanvas(mapWindowBottom,width=400, height=400, bg="grey")
        self.admincanvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set, scrollregion=(0, 0, 2480 , 2480))
        self.admincanvas.pack(side=LEFT)
        vbar.pack(side=LEFT,fill=Y)
        vbar.config( command = self.admincanvas.yview)
        hbar.pack(side=LEFT,fill=X)
        hbar.config( command = self.admincanvas.xview)
        self.admincanvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.mapWindow.protocol('WM_DELETE_WINDOW', self.closeInstallerMap)

        # Buttons for map window
        buttonwidth = 20
        b1 = Button(mapWindowTop,text="Upload" ,command=self.uploadImage , width=buttonwidth)
        b1.pack(side=LEFT)

        try:
            # row = self.tableImage.all().next()
            # self.openImage(row["imageName"],self.admincanvas)
            self.openImage(self.admincanvas)
        except:
            print "No map found!"

        for item in self.table:
            if 'coordx' not in item:
                print 'Please update' + item['repeater'] + 'info.'
            elif item['coordx'] != None and item['coordy'] != None:
                Point(self.table, self.admincanvas, (item['coordx'], item['coordy']), item['repeater'],item['name'])

    def closeInstallerMap(self):
        self.mapWindow.destroy()
        self.updateGuardMap()
        self.updateMLB()


    def openImage(self, canvas):
        filename = self.openPicture()
        self.image = Image.open(filename)
        self.img_copy= self.image.copy()
        # size = (self.mapWindow.winfo_screenwidth(), self.mapWindow.winfo_screenheight())
        # self.resizedImage = self.image.resize(size,Image.ANTIALIAS)
        # Put the image into a canvas compatible class, and stick in an
        # arbitrary variable to the garbage collector doesn't destroy it
        canvas.image = ImageTk.PhotoImage(self.image)
        canvas.create_image(0, 0, image=canvas.image, anchor='nw', tags='map')

    def uploadImage(self):
        self.tablePicture.drop()
        self.initPictureTable()
        filename = tkFileDialog.askopenfilename(filetypes=[('PNG','*.png'),('JPG', '*.jpg')], parent=self.mapWindow)
        # self.tableImage.insert(dict(imageName=filename))
        self.insert_picture(filename)
        self.openImage(self.admincanvas)

    def toggleFullScreen(self,event):
        global state
        if state==0:
            self.mapWindow.attributes('-fullscreen', False)
            state = 1
        elif state==1:
            self.mapWindow.attributes('-fullscreen', True)
            state = 0


    def insert_picture(self, picture_file):
        conn = sqlite3.connect(self.db_file)
        with open(picture_file, 'rb') as input_file:
            ablob = input_file.read()
            base=os.path.basename(picture_file)
            afile, ext = os.path.splitext(base)
            print afile, ext
            sql = '''INSERT INTO PICTURE
            (PICTURE, TYPE, FILE_NAME)
            VALUES(?, ?, ?);'''
            conn.execute(sql,[sqlite3.Binary(ablob), ext, afile]) 
            conn.commit()

        conn.close()

    def extract_picture(self, cursor, picture_id):

        sql = "SELECT PICTURE, TYPE, FILE_NAME FROM PICTURE WHERE id = :id"
        param = {'id': picture_id}
        cursor.execute(sql, param)
        ablob, ext, afile = cursor.fetchone()
        filename = afile + ext
        with open(filename, 'wb') as output_file:
            output_file.write(ablob)
        return filename

    def openPicture(self):
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        filename = self.extract_picture(cur, 1)
        cur.close()
        conn.close()
        return filename


############################################# GUARD MAP ##########################################

    def openGuardMap(self, rightFrame):

        # Uneditable Mapbeep
        self.guardcanvas = ResizingCanvas(rightFrame,width=400, height=400, bg="grey")
        self.guardcanvas.pack()
        self.guardcanvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.guardcanvas.bind("<ButtonPress-1>", self._on_press)

        # if self.tableImage.count() != 0:
            # row = self.tableImage.all().next()
            # self.openImage(row["imageName"],self.guardcanvas)
        if self.tablePicture.count() != 0:
            self.openImage(self.guardcanvas)
        self.houses = []


        self.x_error = 0
        self.y_error = 0

        self.updateGuardMap()

    def updateGuardMap(self):
        # clear houses from canvas
        for h in reversed(self.houses):
            self.guardcanvas.delete(h.item)
            self.guardcanvas.delete(h.text)
            self.houses.pop()

        # append houses to canvas
        for item in self.table:
            if 'coordx' not in item:
                print 'Please update '+item['repeater']+' info'
            elif item['coordx'] != None and item['coordy'] != None:
                self.houses.append(Point(self.table, self.guardcanvas, (item['coordx'], item['coordy']), item['repeater'],item['name'], self.onPointSelect, False))


        if self.tablePicture.count() != 0:
            self.openImage(self.guardcanvas)

        self.guardcanvas.tag_raise("house")
        self.guardcanvas.tag_raise("label")



    def resizeImage(self, canvas, new_width, new_height):
        # print 'image:', new_width, new_height
        self.guardcanvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set, scrollregion=(0, 0, new_width, new_height))
        
        self.hbar.config(command=self.guardcanvas.xview)
        self.vbar.config(command=self.guardcanvas.yview)

        self.image = self.img_copy.resize((new_width, new_height))

        canvas.image = ImageTk.PhotoImage(self.image)
        canvas.create_image(0, 0, image=canvas.image, anchor='nw', tags='map')
        self.tableConfig.upsert(dict(type='map', map_width=new_width, map_height=new_height), ['type'])


    def _on_press(self, event):
        # print 'click:', event.x, event.y
        pass

    def _on_mousewheel(self, event):
        scale = 1 + (0.10 *(event.delta/120))

        w, h = self.image.size


        new_width = round(w*scale)
        new_height = round(h*scale)

        if new_width < 500 or new_height > 2000:
            return "zooming level exceed"
        
        self.resizeImage(self.guardcanvas, new_width, new_height)
        self.guardcanvas.tag_raise("house")
        self.guardcanvas.tag_raise("label")

        sw, sh = new_width / w, new_height / h

        for h in self.houses:
            item = h.item
            self.transformPoint(h, sw, sh)

    
    def transformPoint(self, h, scalex, scaley):
        item = h.item
        text = h.text
        a, b, c, d = self.guardcanvas.coords(item)
        x, y = a+5, b+5
        mx, my = a*scalex-a, b*scaley-b
        self.x_error += mx - round(mx)
        self.y_error += my - round(my)
        import math
        self.guardcanvas.move(item, int(round(mx) + math.modf(self.x_error)[1]), int(round(my) + math.modf(self.y_error)[1]))
        self.guardcanvas.move(text, int(round(mx) + math.modf(self.x_error)[1]), int(round(my) + math.modf(self.y_error)[1]))
        # print round(mx) + math.modf(self.x_error)[1]
        self.x_error = math.modf(self.x_error)[0]
        self.y_error = math.modf(self.y_error)[0]


    
    def findHouseByRepeater(self, repeater):
        for h in self.houses:
            if h.repeater == repeater:
                return h

        return -1

    def blink(self, item):
        canvas = self.guardcanvas
        # print 'blink',canvas,self.do_blink
        current_color = canvas.itemcget(item, "fill")
        new_color = "red" if current_color == "green" else "green"
        canvas.itemconfigure(item, fill=new_color)
        # print 'blink', current_color
        if self.do_blink:
            self.master.after(1000, lambda: self.blink(item))
        else:
            canvas.itemconfigure(item, fill='green')
    
