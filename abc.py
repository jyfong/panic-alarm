from Tkinter import *

class MyApp(Tk):
    def __init__(self):
        Tk.__init__(self)
        fr = Frame(self)
        fr.pack()
        self.canvas  = Canvas(fr, height = 100, width = 100)
        self.canvas.pack()
        self.rect = self.canvas.create_rectangle(25, 25, 75, 75, fill = "white")
        self.do_blink = False
        start_button = Button(self, text="start blinking", 
                              command=self.start_blinking)
        stop_button = Button(self, text="stop blinking", 
                              command=self.stop_blinking)
        start_button.pack()
        stop_button.pack()

    def start_blinking(self):
        self.do_blink = True
        self.blink()

    def stop_blinking(self):
        self.do_blink = False

    def blink(self):
        if self.do_blink:
            current_color = self.canvas.itemcget(self.rect, "fill")
            new_color = "red" if current_color == "white" else "white"
            self.canvas.itemconfigure(self.rect, fill=new_color)
            self.after(1000, self.blink)


if __name__ == "__main__":
    root = MyApp()
    root.mainloop()