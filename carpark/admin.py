from Tkinter import *
import multiListBox
import dataset
import tkMessageBox
import sqlite3
import tkFileDialog
import shutil
from datetime import date
import os
import sys
import time

db = dataset.connect('sqlite:///mydatabase.db')

class AdminPage:
    def __init__(self, master, guipart):
        self.tableUsers = db['users']
        self.table = db['repeater']
    	# GUI INITIALIZATION
        self.master = master
        listbox_width = 40
        self.adminWindow = Toplevel(self.master)
        self.adminWindow.geometry("+%d+%d" % ( master.winfo_rootx()+50, master.winfo_rooty()))

        # create a toplevel menu
        menubar = Menu(self.adminWindow)

        # view 
        menubar.add_command(label="Backup Database",command=lambda:self.dbOperation("backup"))
        menubar.add_command(label="Purge Database",command=lambda:self.dbOperation("purge"))
        menubar.add_command(label="Restore Database",command=lambda:self.dbOperation("restore"))

        # display the menu
        self.adminWindow.config(menu=menubar)

        self.leftFrame = LabelFrame(self.adminWindow, text="Guard Info", padx = 10 , pady = 10)
        self.rightFrame = LabelFrame(self.adminWindow, text="Guard List", padx = 10 , pady = 10)
        self.btmFrame = LabelFrame(self.adminWindow, text="Change Admin Password" , padx = 10, pady= 10)
        self.listboxFrame = LabelFrame(self.adminWindow, text="House Details" , padx = 10, pady= 10)
        self.editlistboxFrame = LabelFrame(self.adminWindow, text="Edit House Details" , padx = 10, pady= 10)

        self.leftFrame.grid(row=0,column=0, sticky=N+S+E+W)
        self.rightFrame.grid(row=0,column=1 ,sticky=E,rowspan=2)
       	self.btmFrame.grid(row=1,column=0 ,sticky=N+S+E+W)
        self.listboxFrame.grid(row=2,column=0 ,sticky=N+S+E+W)
        self.editlistboxFrame.grid(row=2,column=1 ,sticky=N+S+E+W)

        scrollbar = Scrollbar(self.listboxFrame)
        self.l1 = Listbox(self.listboxFrame, width=listbox_width,yscrollcommand=scrollbar.set, exportselection=0, height=16)
        self.l1.grid(row=0,column=0)
        self.l1.bind("<<ListboxSelect>>", self.loadEntry)
        scrollbar.grid(row=0,column=1,sticky=N+S)
        scrollbar.config( command = self.l1.yview)

       	# LEFT FRAME
       	self.leftFrameTop = Frame(self.leftFrame)
       	self.leftFrameBtm = Frame(self.leftFrame)
       	self.leftFrameTop.grid(row=0,column=0 ,sticky=E)
       	self.leftFrameBtm.grid(row=1,column=0 ,sticky=E)

       	self.label_1 = Label(self.leftFrameTop, text="Username:")
        self.label_2 = Label(self.leftFrameTop, text="Password:")
        # self.label_3 = Label(self.leftFrameTop, text="User ID:")

        self.usernameVar = StringVar()
        self.passwordVar = StringVar()
        self.entry_1 = Entry(self.leftFrameTop , textvariable=self.usernameVar) # Name
        self.entry_2 = Entry(self.leftFrameTop, show="*", textvariable=self.passwordVar) # Pass
        # self.entry_3 = Entry(self.leftFrameTop) # ID

        self.label_1.grid(row=0, sticky=E)
        self.label_2.grid(row=1, sticky=E)
        # self.label_3.grid(row=2, sticky=E)
        self.entry_1.grid(row=0, column=1)
        self.entry_2.grid(row=1, column=1)
        # self.entry_3.grid(row=2, column=1)

        self.button_1 = Button(self.leftFrameBtm,text="Add",command=self.addGuard )
        self.button_1.grid(row=0,column=0, sticky=E)
        self.button_2 = Button(self.leftFrameBtm,text="Delete",command=self.deleteGuard )
        self.button_2.grid(row=0,column=1, sticky=E)
        # self.button_3 = Button(self.leftFrameBtm,text="Update",command=self.updateGuard )
        # self.button_3.grid(row=0,column=2, sticky=E)

        # RIGHT FRAME
        self.mlb = multiListBox.MultiListbox(self.rightFrame, (('Username', 20), ('Password', 20)))
        self.mlb.pack(expand=YES,fill=BOTH)


        # BOTTOM FRAME
        self.btmFrameTop = Frame(self.btmFrame)
       	self.btmFrameBtm = Frame(self.btmFrame)
       	self.btmFrameTop.grid(row=0,column=0 ,sticky=E)
       	self.btmFrameBtm.grid(row=1,column=0 ,sticky=E)

        self.label_4 = Label(self.btmFrameTop, text="Old Pass:")
        self.label_5 = Label(self.btmFrameTop, text="New Pass:")
        self.label_6 = Label(self.btmFrameTop, text="Confirm Pass:")

        self.entry_4 = Entry(self.btmFrameTop, show="*") # Old
        self.entry_5 = Entry(self.btmFrameTop, show="*") # new
        self.entry_6 = Entry(self.btmFrameTop, show="*") # confirm

        self.label_4.grid(row=0, sticky=E)
        self.label_5.grid(row=1, sticky=E)
        self.label_6.grid(row=2, sticky=E)
        self.entry_4.grid(row=0, column=1)
        self.entry_5.grid(row=1, column=1)
        self.entry_6.grid(row=2, column=1)

        self.button_4 = Button(self.btmFrameBtm,text="Change Password", command=self.changeAdminPassword)
        self.button_4.grid(row=0,column=0, sticky=E)

        nameLabel = Label(self.editlistboxFrame, text="Name")
        nameLabel.grid(row=0, column=0)
        self.nameVar = StringVar()
        self.name = Entry(self.editlistboxFrame, textvariable=self.nameVar)
        self.name.grid(row=1,column=0)
        addressLabel = Label(self.editlistboxFrame, text="Address")
        addressLabel.grid(row=2, column=0)
        self.addressVar = StringVar()
        self.address = Entry(self.editlistboxFrame, textvariable=self.addressVar)
        self.address.grid(row=3,column=0)
        phoneLabel = Label(self.editlistboxFrame, text="Phone")
        phoneLabel.grid(row=4, column=0)
        self.phoneVar = StringVar()
        self.phone = Entry(self.editlistboxFrame, textvariable=self.phoneVar)
        self.phone.grid(row=5,column=0)

        b10 = Button(self.editlistboxFrame,text="Update", command=self.updateEntry , width=20)
        b10.grid(row=6,column=0, sticky=W)
        b11 = Button(self.editlistboxFrame,text="Delete", command=self.deleteEntry , width=20)
        b11.grid(row=7,column=0, sticky=W)
        b12 = Button(self.editlistboxFrame,text="Map", command=guipart.openMap , width=20)
        b12.grid(row=8,column=0, sticky=W)

        # load stuff
        self.loadGuards()
        self.mlb.selection_set(0)

        for repeater in self.table:
            self.l1.insert(END, repeater['repeater']+'/'+ repeater['name'])
        self.l1.select_set(0)


    def changeAdminPassword(self):
        oldpass = str(self.entry_4.get())
        rows = self.tableUsers.find_one(username="admin", password=oldpass)
        
        if rows is not None:
            if self.entry_5.get()==self.entry_6.get():
                newpass = str(self.entry_5.get())
                self.tableUsers.update(dict(username="admin",password=newpass),['username'])
                tkMessageBox.showinfo("Success", "Password Changed")
                self.entry_4.delete(0,END)
                self.entry_5.delete(0,END)
                self.entry_6.delete(0,END)
            else:
                tkMessageBox.showwarning("Input Error","Different New Password")
        else:
            tkMessageBox.showwarning("Input Error","Wrong Old Password!")

    def addGuard(self):
        username = str(self.entry_1.get())
        password = str(self.entry_2.get())
        self.tableUsers.insert(dict(username=username, password=password, role="guard"))
        self.mlb.insert(END,(username,password))
        self.entry_1.delete(0,END)
        self.entry_2.delete(0,END)

    def deleteGuard(self):
        username,password = self.mlb.get(self.mlb.curselection())
        self.tableUsers.delete(username=username)
        self.mlb.delete(0,END)
        self.loadGuards()

    def loadGuards(self):
        users = self.tableUsers.find(role="guard")
        for item in users:
            self.mlb.insert(END,(item["username"],item["password"]))

    def loadEntry(self, event):
        repeaterID = self.l1.get(self.l1.curselection()).partition('/')[0]
        row = self.table.find_one(repeater=repeaterID)
        self.nameVar.set(row['name'])
        self.addressVar.set(row['address'])
        self.phoneVar.set(row['phone'])        

    def updateEntry(self):
        repeaterID = self.l1.get(self.l1.curselection()).partition('/')[0]
        self.table.upsert(dict(repeater=repeaterID,name=self.nameVar.get(),address=self.addressVar.get(),phone=self.phoneVar.get(), coordx=100, coordy=100), ['repeater'] )

    def deleteEntry(self):
        repeaterID = self.l1.get(self.l1.curselection())
        self.table.delete(repeater=repeaterID)
        self.l1.delete(0,END)
        for repeater in self.table:
            self.l1.insert(END, repeater['repeater'])

    def dbOperation(self, dbcommand):
        self.dbfile = "mydatabase.db"
        connection = sqlite3.connect(self.dbfile)
        cursor = connection.cursor()

        # Lock database before making a backup
        cursor.execute('begin immediate')
        # Make new backup file
        initialfile = date.today().isoformat() + ".db"
        if dbcommand == "backup":
            backup_file = tkFileDialog.asksaveasfilename(filetypes=[('SQLITE_DB','*.db')], initialfile=initialfile)
            if backup_file:
                shutil.copyfile(self.dbfile, backup_file)   
        elif dbcommand == "restore":
            backup_file = tkFileDialog.askopenfilename(filetypes=[('SQLITE_DB','*.db')])
            if backup_file:
                shutil.copyfile(backup_file, self.dbfile)
        elif dbcommand == "purge":
            connection.rollback()
            cursor.execute("INSERT INTO history(time,repeater,acknowledged) SELECT * FROM log WHERE time <=" + str(time.time() - 31536000) + "")
            cursor.execute("DELETE FROM log WHERE time <=" + str(time.time() - 31536000) + "")
            connection.commit()
            if tkMessageBox.showinfo("Purge Success", "Deleted logs older than 1 year!"):
                pass
        else:
            print "DB operation failure"
        # Unlock database
        connection.rollback()

        if tkMessageBox.showinfo("Restart Required", "Restarting Application!"):
            python = sys.executable
            os.execl(python, python, * sys.argv)

