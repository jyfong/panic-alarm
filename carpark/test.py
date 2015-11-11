import threading
import time
import os

class Test:
	def start(self):
		self.do_blink = False;
		self.sosThread = threading.Thread(target=self.sos)
		self.sosThread.start()
		time.sleep(5)
		self.do_blink = True

	def sos(self): 
		while self.do_blink:
			print self.do_blink;
			time.sleep(1)

if __name__ == '__main__':
	Test().start()
	while True:
		pass