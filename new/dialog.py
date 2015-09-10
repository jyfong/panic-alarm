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

        self.mlb = multiListBox.MultiListbox(self.topFrame, (('Time', 20),('Name', 20), ('Phone', 20), ('Address', 30)))
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
        for h in self.houses:
            h.isPanic = False
    
    def loadPendingAlarm(self):
        pendingPanic = db.query('SELECT panic.time, panic.repeater, repeater.name,repeater.address,repeater.phone FROM panic, repeater WHERE panic.repeater = repeater.repeater AND panic.acknowledged=="None"')

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

    def closed(self):
        pass