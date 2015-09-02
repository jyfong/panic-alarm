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
import multiListBox

state = 0 # for toggling fullscreen in mapWindow
# connecting to a SQLite database
db = dataset.connect('sqlite:///mydatabase.db')

class LoginDialog(customtkSimpleDialog.Dialog):
    

    def body(self, master):
        self.tableUsers = db['users']

        Label(master, text="Username:").grid(row=0)
        Label(master, text="Password:").grid(row=1)

        self.e1 = Entry(master)
        self.e2 = Entry(master, show="*")

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        return self.e1 # initial focus

    def apply(self):
        username = str(self.e1.get())
        password = str(self.e2.get())
        
        rows = self.tableUsers.find_one(username=username, password=password)

        if rows is not None:
            print "Login Success"
            self.result = 1
            self.user = username
        else:
            tkMessageBox.showwarning("Fail","Wrong Username or Password!")
            print "Fail Login"
            self.result = 0
        

    def canceled(self):
        self.result = 0
        
class PanicDialog(customtkSimpleDialog.Dialog):

    def body(self,master):
        self.tablePanic = db['panic']
        self.topFrame = LabelFrame(master, text="Pending Panic Alarm", padx = 10 , pady = 10)
        self.topFrame.grid(row=0, sticky=N+S+E+W)
        self.btmFrame = LabelFrame(master, text="Action", padx = 10 , pady = 10)
        self.btmFrame.grid(row=1, sticky=N+S+E+W)

        self.mlb = multiListBox.MultiListbox(self.topFrame, (('Time', 20),('Name', 20), ('Phone', 20), ('Address', 30)))
        self.mlb.grid(row=0, sticky=N+S+E+W)

        self.loadPendingAlarm()

        self.button_1 = Button(self.btmFrame,text="Acknowledge", command=self.acknowledgeAll )
        self.button_1.grid(row=0,column=0, sticky=N+S+E+W)


    def canceled(self):
        pass

    def acknowledgeAll(self):
        login = LoginDialog(self.master)
        if login.result == 0:
            return

        currentUser = login.user
        db.query('UPDATE panic SET acknowledged="' + currentUser + '" WHERE acknowledged="None"')

        self.mlb.delete(0,END)
        self.loadPendingAlarm()
        self.stop_blinking()
    
    def loadPendingAlarm(self):
        pendingPanic = db.query('SELECT panic.time, panic.repeater, repeater.name,repeater.address,repeater.phone FROM panic, repeater WHERE panic.repeater = repeater.repeater AND panic.acknowledged=="None"')

        for item in pendingPanic:
            currentTime = time.strftime("%y/%m/%d %H:%M", time.localtime(item['time']))
            self.mlb.insert(END,(currentTime,item['name'],item['phone'],item['address']))

class ConfirmedPanicDialog(customtkSimpleDialog.Dialog):

    def body(self,master):
        self.tablePanic = db['panic']
        self.topFrame = LabelFrame(master, text="Confirmed Panic Alarm", padx = 10 , pady = 10)
        self.topFrame.grid(row=0, sticky=N+S+E+W)
        self.btmFrame = LabelFrame(master, text="Action", padx = 10 , pady = 10)
        self.btmFrame.grid(row=1, sticky=N+S+E+W)

        self.mlb = multiListBox.MultiListbox(self.topFrame, (('Time', 20),('Name', 20), ('Phone', 20), ('Address', 30),('Acknowledged by',20)))
        self.mlb.grid(row=0, sticky=N+S+E+W)

        self.loadConfirmedAlarm()

    def canceled(self):
        pass

    def loadConfirmedAlarm(self):
        pendingPanic = db.query('SELECT panic.time, panic.repeater,panic.acknowledged, repeater.name,repeater.address,repeater.phone FROM panic, repeater WHERE panic.repeater = repeater.repeater AND panic.acknowledged!="None"')

        for item in pendingPanic:
            currentTime = time.strftime("%y/%m/%d %H:%M", time.localtime(item['time']))
            self.mlb.insert(END,(currentTime,item['name'],item['phone'],item['address'],item['acknowledged']))


class ResizingCanvas(Canvas):
    def __init__(self,parent,**kwargs):
        Canvas.__init__(self,parent,**kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self,event):
        # determine the ratio of old width/height to new width/height
        wscale = float(event.width)/self.width
        hscale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        # resize the canvas 
        self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        # self.scale("all",0,0,wscale,hscale)

class GuiPart:
    def __init__(self, master, queue, endCommand, send):
        self.master = master
        self.queue = queue
        self.endCommand = endCommand
        self.send = send
        self.repeater = None
        self.current = None
        self.table = db['repeater']
        self.tableImage = db['image']
        self.tableLog = db['log']
        self.tableUsers = db['users']
        self.tablePanic = db['panic']
        self.initPosition = "+300+30"
        self.logger("Program startup properly..\n")

        # Add default admin user and password
        if self.tableUsers.count() == 0:
            self.tableUsers.insert(dict(username="admin",password="admin",role=""))

        # Set up the GUI
        master.title("DF Panic Alarm")
        master.geometry(self.initPosition)

        # create a toplevel menu
        menubar = Menu(master)

        # manage
        manageMenu = Menu(menubar, tearoff=0)
        manageMenu.add_command(label="Admin", command=lambda:self.addUsers(master))
        manageMenu.add_command(label="Installer",command=lambda:self.addDevices(master))
        menubar.add_cascade(label="Manage" ,menu=manageMenu )

        # view 
        menubar.add_command(label="New Alarms",command=lambda:PanicDialog(master))
        menubar.add_command(label="All Alarms",command=lambda:ConfirmedPanicDialog(master))

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

        # Listbox for details
        mlb = multiListBox.MultiListbox(leftFrame, (('RepeaterID', 15), ('Name', 20), ('Address', 30)))
        # for i in range(1000):
        #     mlb.insert(END, ('Important Message: %d' % i, 'John Doe', '10/10/%04d' % (1900+i)))
        mlb.pack(expand=YES,fill=BOTH)

        # Uneditable Map
        self.guardcanvas = ResizingCanvas(rightFrame,width=400, height=400, bg="grey")
        self.guardcanvas.pack()
        self.guardcanvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.guardcanvas.bind("<ButtonPress-1>", self._on_press)


        if self.tableImage.count() != 0:
            row = self.tableImage.all().next()
            self.openImage(row["imageName"],self.guardcanvas)
        self.houses = []

        for item in self.table:
            mlb.insert(END, (item['repeater'], item['name'], item['address']))
            if item['coordx'] != None and item['coordy'] != None:
                self.houses.append(Point(self.table, self.guardcanvas, (item['coordx'], item['coordy']), item['repeater'],item['name']))

        self.x_error = 0
        self.y_error = 0
        self.do_blink = False


    def _on_press(self, event):
        print 'click:', event.x, event.y

    def _on_mousewheel(self, event):
        scale = 1 + (0.10 *(event.delta/120))

        w, h = self.image.size
        
        self.resizeImage(self.guardcanvas, round(w*scale), round(h*scale))
        self.guardcanvas.tag_raise("house")

        sw, sh = round(w*scale) / w, round(h*scale) / h

        for h in self.houses:
            item = h.item
            self.transformPoint(item, sw, sh)

    
    def transformPoint(self, item, scalex, scaley):
        a, b, c, d = self.guardcanvas.coords(item)
        x, y = a+5, b+5
        mx, my = a*scalex-a, b*scaley-b
        self.x_error += mx - round(mx)
        self.y_error += my - round(my)
        import math
        self.guardcanvas.move(item, int(round(mx) + math.modf(self.x_error)[1]), int(round(my) + math.modf(self.y_error)[1]))
        # print round(mx) + math.modf(self.x_error)[1]
        self.x_error = math.modf(self.x_error)[0]
        self.y_error = math.modf(self.y_error)[0]

    # admin page
    def addUsers(self,master):
        login = LoginDialog(master)
        if login.result == 1:
            adminPage = admin.AdminPage(master)


    # installer page
    def addDevices(self,master):
        result =  tkSimpleDialog.askstring("Database Operation", "Please enter password :", show='*')
        if result == "1":
            self.addDevicesWindow = Toplevel(self.master)
            # Menubar for addDevices window
            menubar = Menu(self.addDevicesWindow)
            filemenu = Menu(menubar, tearoff=0)
            filemenu.add_command(label="Clear DB", command=self.clearDatabase)
            filemenu.add_separator()
            menubar.add_cascade(label="File", menu=filemenu)
            centralMenu = Menu(menubar, tearoff=0)
            centralMenu.add_command(label="MCU Reset", command=self.mcuReset )
            centralMenu.add_command(label="Check MCU ID", command=self.mcuIDChecking)
            menubar.add_cascade(label="Central Menu" ,menu=centralMenu )

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
            b1 = Button(topFrame,text="Configure Central ID" ,command=self.configCentralId , width=buttonwidth)
            b1.grid(row=0,column=1, sticky=W)
            b2 = Button(topFrame,text="Ask Respond", command=self.askRespond , width=buttonwidth )
            b2.grid(row=0,column=2, sticky=W)
            b3 = Button(topFrame,text="Repeater Search Path", command=self.repeaterSearchPath , width=buttonwidth)
            b3.grid(row=0,column=3, sticky=W)
            b4 = Button(topFrame,text="All Repeater Search Path", command=self.allRepeaterSearchPath, width=buttonwidth )
            b4.grid(row=0,column=4, sticky=W)
            
            # Second Row
            b5 = Button(topFrame,text="Check Central ID", command=self.mcuIDChecking, width=buttonwidth )
            b5.grid(row=1,column=0, sticky=W)
            b6 = Button(topFrame,text="Check Repeater Central ID", command=self.repeaterCheckCentralID , width=buttonwidth)
            b6.grid(row=1,column=1, sticky=W)
            b7 = Button(topFrame,text="Check Repeater Path", command=self.repeaterCheckPath , width=buttonwidth)
            b7.grid(row=1,column=2, sticky=W)
            b8 = Button(topFrame,text="Map", command=self.openMap , width=buttonwidth)
            b8.grid(row=1,column=3, sticky=W)
            b9 = Button(topFrame,text="View Old Logs", command=self.openLog , width=buttonwidth)
            b9.grid(row=1,column=4, sticky=W)

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
            addressLabel = Label(middleFrameRight, text="Address")
            addressLabel.grid(row=2, column=0)
            self.addressVar = StringVar()
            self.address = Entry(middleFrameRight, textvariable=self.addressVar)
            self.address.grid(row=3,column=0)
            phoneLabel = Label(middleFrameRight, text="Phone")
            phoneLabel.grid(row=4, column=0)
            self.phoneVar = StringVar()
            self.phone = Entry(middleFrameRight, textvariable=self.phoneVar)
            self.phone.grid(row=5,column=0)

            
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

            self.addDevicesWindow.protocol('WM_DELETE_WINDOW', self.closeAddDevices)

            for repeater in self.table:
                self.l1.insert(END, repeater['repeater'])
            self.l1.select_set(0)

            self.listen = False
        else:
            tkMessageBox.showwarning("Error","Wrong Password!")

    def listenMode(self):
        self.listen = not self.listen
        if self.listen == True:
            self.b0.config(relief=SUNKEN)
        else:
            self.b0.config(relief=RAISED)

    def closeAddDevices(self):
        del self.log
        self.addDevicesWindow.destroy()

    def updateEntry(self):
        repeaterID = self.l1.get(self.l1.curselection())
        self.table.upsert(dict(repeater=repeaterID,name=self.nameVar.get(),address=self.addressVar.get(),phone=self.phoneVar.get(), coordx=100, coordy=100), ['repeater'] )

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
        self.addressVar.set(row['address'])
        self.phoneVar.set(row['phone'])

    def logger(self, msg):
        now = time.localtime()
        msg = time.strftime("%y/%m/%d %H:%M", now) + " " +  msg
        timeinsec = time.time()
        if 'log' in dir(self):
            self.log.insert(END, msg)
        self.tableLog.insert(dict(time=timeinsec,msg=msg))

    def clearLogger(self):
        self.log.delete('0.0', END)

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

    def on_exit(self):
        """When you click to exit, this function is called"""
        if tkMessageBox.askyesno("Exit", "Do you want to quit the application?"):
            self.logger("Program shutdown properly..\n")
            root.destroy()
            self.endCommand()
            

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


    ####                 ###
    ####   Map Window    ###
    ####                 ###
    
    def openMap(self):
        # topLevel method is to open new window
        
        mapWindow = Toplevel(self.master)
        self.mapWindow = mapWindow
        mapWindow.attributes('-fullscreen', False)
        mapWindow.geometry(self.initPosition)
        mapWindow.bind('<Escape>',self.toggleFullScreen)

        # Frames for map window
        mapWindowTop = Frame(mapWindow)
        mapWindowTop.pack(side=TOP)
        mapWindowBottom = Frame(mapWindow)
        mapWindowBottom.pack()
        # mapWindowBottom.bind('<Configure>', self.resizeImage)

        self.admincanvas = Canvas(mapWindowBottom, width=mapWindow.winfo_screenwidth()-4, height=mapWindow.winfo_screenheight()-4)
        self.admincanvas.pack()

        # Buttons for map window
        buttonwidth = 20
        b1 = Button(mapWindowTop,text="Upload" ,command=self.uploadImage , width=buttonwidth)
        b1.grid(row=0,column=0, sticky=W)
        # b2 = Button(mapWindowTop,text="Ask Respond" , width=buttonwidth )
        # b2.grid(row=0,column=1, sticky=W)

        row = self.tableImage.all().next()
        self.openImage(row["imageName"],self.admincanvas)

        for item in self.table:
            if item['coordx'] != None and item['coordy'] != None:
                Point(self.table, self.admincanvas, (item['coordx'], item['coordy']), item['repeater'],item['name'])

    def resizeImage(self, canvas, new_width, new_height):
        print 'image:', new_width, new_height
        self.image = self.img_copy.resize((new_width, new_height))

        canvas.image = ImageTk.PhotoImage(self.image)
        canvas.create_image(0, 0, image=canvas.image, anchor='nw')

    def openImage(self,filename,canvas):
        self.image = Image.open("map.jpg")
        self.img_copy= self.image.copy()
        # size = (self.mapWindow.winfo_screenwidth(), self.mapWindow.winfo_screenheight())
        # self.resizedImage = self.image.resize(size,Image.ANTIALIAS)
        # Put the image into a canvas compatible class, and stick in an
        # arbitrary variable to the garbage collector doesn't destroy it
        canvas.image = ImageTk.PhotoImage(self.image)
        canvas.create_image(0, 0, image=canvas.image, anchor='nw')

    def uploadImage(self):
        filename = tkFileDialog.askopenfilename(filetypes=[('JPG', '*.jpg')])
        self.openImage(filename,self.admincanvas)
        self.tableImage.insert(dict(imageName=filename))

    def toggleFullScreen(self,event):
        global state
        if state==0:
            self.mapWindow.attributes('-fullscreen', False)
            state = 1
        elif state==1:
            self.mapWindow.attributes('-fullscreen', True)
            state = 0

    def sos(self): 
        for i in range(0, 3): winsound.Beep(2000, 100) 
        for i in range(0, 3): winsound.Beep(2000, 400) 
        for i in range(0, 3): winsound.Beep(2000, 100)

    def panicAlarm(self,msg):
        master = self.master
        cmd, repeater = msg
        currentTime = time.time()
        self.tablePanic.insert(dict(repeater=repeater, time=currentTime,acknowledged="None"))
        self.sos()
        panic = PanicDialog(master)
        

    def findHouseByRepeater(self, repeater):
        for h in self.houses:
            if h.repeater == repeater:
                return h.item

        return -1


    def start_blinking(self):
        self.do_blink = True
        

    def stop_blinking(self):
        self.do_blink = False

    def blink(self, house):
        canvas = self.guardcanvas
        if self.do_blink:
            current_color = canvas.itemcget(house, "fill")
            new_color = "red" if current_color == "black" else "black"
            canvas.itemconfigure(house, fill=new_color)
            self.master.after(1000, lambda:self.blink(house))

    def decode(self,b):

        m = re.match('.*RA(\w)(.{8})(.{2})?', b)
        if m:
            print m.group(0),'Cmd:', m.group(1), 'Repeater:', m.group(2), 'RSSI: -', m.group(3)

            cmd = m.group(1)
            repeater = m.group(2)
            RSSI = m.group(3)


            if cmd == "I":
                if self.listen == True:

                    msg = "Central ID = " + repeater + "\n"
                    self.logger(msg)
                    if not self.table.find_one(repeater=repeater):
                        self.l1.insert(END, repeater)
                        self.table.insert(dict(repeater=repeater))

                else:
                    return

            if not self.table.find_one(repeater=repeater):
                print "Alien Discovered", repeater
                return

            if cmd == 'A':
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
                self.queue.put((cmd,repeater))
                msg = "Repeater central ID = " + repeater + " PANIC ALARM! \n"
                self.logger(msg)
                self.start_blinking()
                self.blink(self.findHouseByRepeater(repeater))

            elif int(cmd) in range(1,4):
                msg = "Repeater path " + cmd + " = " + repeater + " ..\n"
                self.logger(msg)


        else:
            print 'Cant decode', b

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
                    if tkMessageBox.showerror("Device Not Found!", "Please connect Central Device .."):
                        os._exit(0)
                elif type(msg) is tuple:
                    self.panicAlarm(msg)
                else:
                    self.decode(msg)
            except Queue.Empty:
                pass

class Point:
    def __init__(self, table, canvas, coord, repeater,name, color='black'):

        (x,y) = coord
        self.item = canvas.create_oval(x-5, y-5, x+5, y+5,
                                outline=color, fill=color, tags="house")
        self.text = canvas.create_text(x+0, y-15, text=repeater)
        self.repeater = repeater
        self.canvas = canvas
        self.table = table

        self._drag_data = {"x": 0, "y": 0, "item": None}

        # add bindings for clicking, dragging and releasing over
        # any object with the "token" tag
        canvas.tag_bind(self.item, "<ButtonPress-1>", self.OnTokenButtonPress)
        canvas.tag_bind(self.item, "<ButtonRelease-1>", self.OnTokenButtonRelease)
        canvas.tag_bind(self.item, "<B1-Motion>", self.OnTokenMotion)


    def OnTokenButtonPress(self, event):
        '''Being drag of an object'''
        # record the item and its location
        print event.x, event.y
        self._drag_data["item"] = self.canvas.find_closest(event.x, event.y)[0]
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def OnTokenButtonRelease(self, event):
        '''End drag of an object'''
        # reset the drag information
        self._drag_data["item"] = None
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0

        data = dict(repeater=self.repeater, coordx=event.x, coordy=event.y)
        self.table.update(data, ['repeater'])


    def OnTokenMotion(self, event):
        '''Handle dragging of an object'''
        # compute how much this object has moved
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        # move the object the appropriate amount
        self.canvas.move(self._drag_data["item"], delta_x, delta_y)
        self.canvas.move(self.text, delta_x, delta_y)
        # record the new position
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

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

                # if b == '':
                #     continue

                # if not (ord(b) == 13 or (ord(b) in range(48, 58)) or (ord(b) in range(65, 91))):
                #     print b
                #     continue

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
        self.d.close()

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
