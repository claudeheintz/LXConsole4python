#   OSC.py
#
#	by Claude Heintz
#	copyright 2014 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html


import socket
import threading
import time

class OSCInterface:
	
	def __init__(self):
		self.udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	def sendOSC(self, target_ip, port, message):
		ml = len(message)
		buffer = bytearray(ml + 1)
		buffer[ml] = 0
		buffer[0:ml] = message
		self.udpsocket.sendto(buffer, (target_ip, port))
		
	def sendOSCFromString(self, string):
		cp=string.split("~")
		if len(cp) == 2:
			np = cp[0].split(":")
			if len(np) == 2:
				self.sendOSC(np[0], int(np[1]), cp[1])
				
	def sendOSCstring(self, target_ip, port, message, string):
		ml = len(message) + 1
		sl = len(string) + 1
		rl = ml % 4
		if rl > 0:
			rl = 4 - rl
		srl = sl % 4
		if srl > 0:
			srl = 4 - srl
		bl = ml+rl+4+sl+srl
		buffer = bytearray(bl)
		for i in range(bl):
			buffer[i] = 0
		buffer[0:ml-1] = message
		ss = ml + rl
		buffer[ss] = ','
		buffer[ss+1] = 's'
		ss += 4
		buffer[ss:ss+sl-1] = string
		self.udpsocket.sendto(buffer, (target_ip, port))