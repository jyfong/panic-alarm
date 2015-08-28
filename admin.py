from Tkinter import *
import multiListBox

class AdminPage:
    def __init__(self, master):
        self.master = master
        self.adminWindow = Toplevel(self.master)

        self.leftFrame = LabelFrame(self.adminWindow, text="Guard Info", padx = 5 , pady = 5)
        self.rightFrame = LabelFrame(self.adminWindow, text="Guard List", padx = 5 , pady = 5)
        self.bottomFrame = LabelFrame(self.adminWindow, text="Change Admin Password" , padx = 5, pady= 5)

       	self.leftFrame.pack(side=LEFT)
       	self.rightFrame.pack(side=RIGHT)
       	self.bottomFrame.pack(side=BOTTOM)

       	self.leftFrameTop = Frame(self.leftFrame)
       	self.leftFrameBtm = Frame(self.leftFrame)
       	self.leftFrameTop.pack(side=TOP)
       	self.leftFrameBtm.pack(side=BOTTOM, pady=10)

       	self.label_1 = Label(self.leftFrameTop, text="Name")
        self.label_2 = Label(self.leftFrameTop, text="Password")
        self.label_3 = Label(self.leftFrameTop, text="ID")

        self.entry_1 = Entry(self.leftFrameTop) # Name
        self.entry_2 = Entry(self.leftFrameTop, show="*") # Pass
        self.entry_3 = Entry(self.leftFrameTop, show="*") # ID

        self.label_1.grid(row=0, sticky=E)
        self.label_2.grid(row=1, sticky=E)
        self.label_3.grid(row=2, sticky=E)
        self.entry_1.grid(row=0, column=1)
        self.entry_2.grid(row=1, column=1)
        self.entry_3.grid(row=2, column=1)

        self.addGuard = Button(self.leftFrameBtm,text="Add" )
        self.addGuard.grid(row=0,column=0, sticky=E)
        self.deleteGuard = Button(self.leftFrameBtm,text="Delete" )
        self.deleteGuard.grid(row=0,column=1, sticky=E)
        self.editGuard = Button(self.leftFrameBtm,text="Update" )
        self.editGuard.grid(row=0,column=2, sticky=E)
