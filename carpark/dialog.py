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

db = dataset.connect('sqlite:///mydatabase.db')

class LoginDialog(customtkSimpleDialog.Dialog):
    

    def body(self, master,guipart):
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

    def closed(self):
        pass
        
class PanicDialog(customtkSimpleDialog.Dialog):

    def body(self,master,guipart):
        self.guipart = guipart
        self.tablePanic = db['panic']
        self.topFrame = LabelFrame(master, text="Pending Panic Alarm", padx = 10 , pady = 10)
        self.topFrame.grid(row=0, sticky=N+S+E+W)
        self.btmFrame = LabelFrame(master, text="Action", padx = 10 , pady = 10)
        self.btmFrame.grid(row=1, sticky=N+S+E+W)

        self.mlb = multiListBox.MultiListbox(self.topFrame, (('Time', 20),('Name', 20)))
        self.mlb.grid(row=0, sticky=N+S+E+W)

        self.loadPendingAlarm()

        self.button_1 = Button(self.btmFrame,text="Acknowledge", command=self.acknowledgeAll )
        self.button_1.grid(row=0,column=0, sticky=N+S+E+W)

        self.guipart.isOpenPanicDialog = True


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
        self.guipart.stop_blinking()
        self.guipart.disableAllAlarm()
        for h in self.guipart.houses:
            h.isPanic = False
    
    def loadPendingAlarm(self):
        pendingPanic = db.query('SELECT panic.time, panic.repeater, repeater.name,repeater.address,repeater.phone FROM panic, repeater WHERE panic.repeater = repeater.repeater AND panic.acknowledged=="None"')
        if self.mlb.size() != 0:
            self.mlb.delete(0, END)
        for item in pendingPanic:

            currentTime = time.strftime("%y/%m/%d %H:%M", time.localtime(item['time']))
            self.mlb.insert(END,(currentTime,item['name'],item['phone'],item['address']))

    def closed(self):
        self.guipart.isOpenPanicDialog = False

class ConfirmedPanicDialog(customtkSimpleDialog.Dialog):

    def body(self,master,guipart):
        self.tablePanic = db['panic']
        self.topFrame = LabelFrame(master, text="Confirmed Panic Alarm", padx = 10 , pady = 10)
        self.topFrame.grid(row=0, sticky=N+S+E+W)
        self.btmFrame = LabelFrame(master, text="Action", padx = 10 , pady = 10)
        self.btmFrame.grid(row=1, sticky=N+S+E+W)

        self.mlb = multiListBox.MultiListbox(self.topFrame, (('Time', 20),('Name', 20),('Acknowledged by',20)))
        self.mlb.grid(row=0, sticky=N+S+E+W)

        self.loadConfirmedAlarm()

    def canceled(self):
        pass

    def loadConfirmedAlarm(self):
        pendingPanic = db.query('SELECT panic.time, panic.repeater,panic.acknowledged, repeater.name,repeater.address,repeater.phone FROM panic, repeater WHERE panic.repeater = repeater.repeater AND panic.acknowledged!="None"')

        for item in pendingPanic:
            currentTime = time.strftime("%y/%m/%d %H:%M", time.localtime(item['time']))
            self.mlb.insert(END,(currentTime,item['name'],item['acknowledged']))

    def closed(self):
        pass

class HealthSignalDialog(customtkSimpleDialog.Dialog):

    def body(self,master,guipart):
        self.repeater = db['repeater']
        self.topFrame = LabelFrame(master, text="Health Signal", padx = 10 , pady = 10)
        self.topFrame.grid(row=0, sticky=N+S+E+W)
        self.btmFrame = LabelFrame(master, text="Action", padx = 10 , pady = 10)
        self.btmFrame.grid(row=1, sticky=N+S+E+W)

        self.mlb = multiListBox.MultiListbox(self.topFrame, (('Repeater', 20),('Name', 20),('Last Health Signal',20)))
        self.mlb.grid(row=0, sticky=N+S+E+W)

        self.loadHealthSignal()

    def canceled(self):
        pass

    def loadHealthSignal(self):
        repeaters = db.query('SELECT repeater,name,lastHealthSignal FROM repeater')

        for item in repeaters:
            if item['lastHealthSignal']:
                lastHealthSignal = time.strftime("%y/%m/%d %H:%M", time.localtime(item['lastHealthSignal']))
            else:
                lastHealthSignal = "None"
            self.mlb.insert(END,(item['repeater'],item['name'],lastHealthSignal))

    def closed(self):
        pass

class healthSignalFailDialog(customtkSimpleDialog.Dialog):

    def body(self,master,guipart):
        self.guipart = guipart
        self.topFrame = LabelFrame(master, text="Health Signal Fail", padx = 10 , pady = 10)
        self.topFrame.grid(row=0, sticky=N+S+E+W)
        self.btmFrame = LabelFrame(master, text="Action", padx = 10 , pady = 10)
        self.btmFrame.grid(row=1, sticky=N+S+E+W)

        self.mlb = multiListBox.MultiListbox(self.topFrame, (('Repeater', 20),('Name', 20),('Last Health Signal',20)))
        self.mlb.grid(row=0, sticky=N+S+E+W)

        self.loadFailedHealthSignal()

    def canceled(self):
        print 'press cancel'
        pass

    def loadFailedHealthSignal(self):
        currentTime = time.time()
        print 'loadFailedHealthSignal', currentTime
        repeaters = db.query('SELECT repeater,name,lastHealthSignal FROM repeater WHERE '+ str(currentTime) + '- lastHealthSignal > 24*60*60')

        for item in repeaters:
            lastHealthSignal = time.strftime("%y/%m/%d %H:%M", time.localtime(item['lastHealthSignal']))
            self.mlb.insert(END,(item['repeater'],item['name'],lastHealthSignal))

    def apply(self):
        login = LoginDialog(self.master)
        if login.result == 1:
            self.guipart.logger("Health fail acknowledged by " +login.user+ "\n")


    def closed(self):
        pass