#   ArtNet.py
#
#	by Claude Heintz
#	copyright 2014-2015 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html
#
#	Art-Net(TM) Designed by and Copyright Artistic Licence Holdings Ltd.


import socket
import threading
import time

class DMXInterface:
	
	def __init__(self):
		self.send_thread = None
		self.lock = threading.Lock()
		self.last_send_time = 0.0
		self.ok = False
		
	def setDMXValue(self, address, value):
		print ("SetDMXValue")
		#override this method
		
	def setDMXValues(self, values):
		print ("setDMXValues")
		self.sending = False
		#override this method
		
	def sendDMXNow(self):
		print ("sendDMXNow")
		#override this method
	
	def send(self):
		while self.sending:
			st = time.time() - self.last_send_time
			if  st >= 2:
				try:
					self.sendDMXNow()
				except:
					self.sending = False
			else:
				time.sleep(2-st)
		self.send_thread = None
		self.sending = False
	
	def startSending(self):
		self.sending = True
		if self.send_thread is None:
			self.send_thread = threading.Thread(target=self.send)
			self.send_thread.daemon = True
			self.send_thread.start()
			
	def stopSending(self):
		while self.send_thread != None:
			self.sending = False
	
	def close(self):
		self.stopSending()
		
	

class ArtNetInterface(DMXInterface):
	ARTNET_PORT = 0x1936
	
	def __init__(self, ip):
		self.seqcounter = 0
		self.send_thread = None
		self.lock = threading.Lock()
		self.last_send_time = 0.0
		self.target_ip = ip
		self.ok = False
		try:
			self.udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.udpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
			self.ok = True
		except:
			print ("Socket Error")
		self.buffer = bytearray(529)
		try:
			self.buffer[0:6] = "Art-Net"
		except:
			self.buffer[0:6] = bytes("Art-Net", 'utf-8')
			#python 3
		self.buffer[7] = 0
		self.buffer[8] = 0		#opcode l/h
		self.buffer[9] = 0x50
		self.buffer[10] = 0		#version h/l
		self.buffer[11] = 14
		self.buffer[12] = 0 	#sequence
		self.buffer[13] = 0		#physical
		self.buffer[14] = 0		#subnet
		self.buffer[15] = 0		#universe
		self.buffer[16] = 2		#dmxcount h/l
		self.buffer[17] = 0
		for i in range(512):
			self.buffer[i+18] = 0

	def sendDMXNow(self):
		self.seqcounter += 1
		if self.seqcounter > 255:
			self.seqcounter = 0
		self.buffer[12] = self.seqcounter
		with self.lock:
			self.udpsocket.sendto(self.buffer, (self.target_ip, self.ARTNET_PORT))
		self.last_send_time = time.time()
		
	def setDMXValue(self, address, value):
		with self.lock:
			self.buffer[address+17] = value
		
	def setDMXValues(self, values):
		with self.lock:
			for i in range (len(values)):
				self.buffer[18+i] = values[i]

	def close(self):
		self.stopSending()
		self.udpsocket.close()

