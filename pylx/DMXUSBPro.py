#   DMXUSBPro.py
#
#	by Claude Heintz
#	copyright 2015 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html
#

import threading
#   requires pyserial download from: https://pypi.python.org/pypi/pyserial
import serial
import sys
from ArtNet import DMXInterface


class DMXUSBProInterface(DMXInterface):
	
	def __init__(self, com_port=3):
		self.send_thread = None
		self.lock = threading.Lock()
		self.last_send_time = 0.0
		self.buffer = bytearray(517)
		# start code
		self.buffer[0] = 0x7E
		# send DMX
		self.buffer[1] = 6
		# size LSB
		self.buffer[2] = 0
		# size MSB
		self.buffer[3] = 2
		# DMX start
		self.buffer[4] = 0
		
		# end code
		self.buffer[516] = 0xE7
		self.ok = False
		self.widget = None
		try:
			self.widget = serial.Serial(com_port, 57600)
			print ("Widget Connected!")
			self.ok = True
		except:
			print ("Could not open serial connection", sys.exc_info()[0])
		

	def setDMXValue(self, address, value):
		with self.lock:
			self.buffer[5+address] = value
		
	def setDMXValues(self, values):
		with self.lock:
			for i in range (len(values)):
				self.buffer[5+i] = values[i]
		
	def sendDMXNow(self):
		if self.widget != None:
			with self.lock:
				self.widget.write(self.buffer)

	def close(self):
		self.stopSending()
		if self.widget != None:
			self.widget.close()
			self.widget = None