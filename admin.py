from Tkinter import *
import multiListBox
import dataset
import tkMessageBox

db = dataset.connect('sqlite:///mydatabase.db')

class AdminPage:
    def __init__(self, master):
        self.tableUsers = db['users']
    	# GUI INITIALIZATION
        self.master = master
        self.adminWindow = Toplevel(self.master)

        self.leftFrame = LabelFrame(self.adminWindow, text="Guard Info", padx = 10 , pady = 10)
        self.rightFrame = LabelFrame(self.adminWindow, text="Guard List", padx = 10 , pady = 10)
        self.btmFrame = LabelFrame(self.adminWindow, text="Change Admin Password" , padx = 10, pady= 10)

        self.leftFrame.grid(row=0,column=0, sticky=N+S+E+W)
        self.rightFrame.grid(row=0,column=1 ,sticky=E,rowspan=2)
       	self.btmFrame.grid(row=1,column=0 ,sticky=N+S+E+W)

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

        self.loadGuards()


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
