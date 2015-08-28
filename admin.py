from Tkinter import *
import multiListBox

class AdminPage:
    def __init__(self, master):
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
        self.label_3 = Label(self.leftFrameTop, text="User ID:")

        self.entry_1 = Entry(self.leftFrameTop) # Name
        self.entry_2 = Entry(self.leftFrameTop, show="*") # Pass
        self.entry_3 = Entry(self.leftFrameTop, show="*") # ID

        self.label_1.grid(row=0, sticky=E)
        self.label_2.grid(row=1, sticky=E)
        self.label_3.grid(row=2, sticky=E)
        self.entry_1.grid(row=0, column=1)
        self.entry_2.grid(row=1, column=1)
        self.entry_3.grid(row=2, column=1)

        self.button_1 = Button(self.leftFrameBtm,text="Add" )
        self.button_1.grid(row=0,column=0, sticky=E)
        self.button_2 = Button(self.leftFrameBtm,text="Delete" )
        self.button_2.grid(row=0,column=1, sticky=E)
        self.button_3 = Button(self.leftFrameBtm,text="Update" )
        self.button_3.grid(row=0,column=2, sticky=E)

        # RIGHT FRAME
        mlb = multiListBox.MultiListbox(self.rightFrame, (('Subject', 40), ('Sender', 20), ('Date', 10)))
        for i in range(1000):
            mlb.insert(END, ('Important Message: %d' % i, 'John Doe', '10/10/%04d' % (1900+i)))
        mlb.pack(expand=YES,fill=BOTH)

        # BOTTOM FRAME
        self.btmFrameTop = Frame(self.btmFrame)
       	self.btmFrameBtm = Frame(self.btmFrame)
       	self.btmFrameTop.grid(row=0,column=0 ,sticky=E)
       	self.btmFrameBtm.grid(row=1,column=0 ,sticky=E)

        self.label_4 = Label(self.btmFrameTop, text="Old Pass:")
        self.label_5 = Label(self.btmFrameTop, text="New Pass:")
        self.label_6 = Label(self.btmFrameTop, text="Confirm Pass:")

        self.entry_4 = Entry(self.btmFrameTop) # Name
        self.entry_5 = Entry(self.btmFrameTop, show="*") # Pass
        self.entry_6 = Entry(self.btmFrameTop, show="*") # ID

        self.label_4.grid(row=0, sticky=E)
        self.label_5.grid(row=1, sticky=E)
        self.label_6.grid(row=2, sticky=E)
        self.entry_4.grid(row=0, column=1)
        self.entry_5.grid(row=1, column=1)
        self.entry_6.grid(row=2, column=1)

        self.button_4 = Button(self.btmFrameBtm,text="Change Password" )
        self.button_4.grid(row=0,column=0, sticky=E)