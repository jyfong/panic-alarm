from Tkinter import *
tk = Tk()
paned = PanedWindow(tk, orient=HORIZONTAL, showhandle=0, handlepad=0,
        handlesize=0, sashwidth=2, opaqueresize=1)
paned.pack(side=LEFT, expand=YES, fill=BOTH)
for l,w in [("One",5),("Two",10),("Three",15), ("Four",30)]:
    frame = Frame(paned, border=0)
    paned.add(frame,minsize=16)
    lbl = Label(frame, text=l, borderwidth=1, relief=RAISED)
    lbl.pack(fill=X)
    lst =  Listbox(frame, width=w, background="White")
    lst.pack(expand=YES, fill=BOTH)
    for i in range(100): lst.insert(END,"#%d"%(i))
tk.mainloop()
