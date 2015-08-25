from Tkinter import *


def circle(canvas,x,y, r):
   id = canvas.create_oval(x-r,y-r,x+r,y+r)
   return id
   
if __name__ == '__main__':
	canvas_width = 190
	canvas_height =150

	master = Tk()

	w = Canvas(master, 
	           width=canvas_width, 
	           height=canvas_height)
	w.pack()

	print circle(w, 75, 75, 25)

	mainloop()
