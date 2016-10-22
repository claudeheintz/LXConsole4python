#!/usr/bin/python

#   OSCListener.py
#
#	by Claude Heintz
#	copyright 2014 by Claude Heintz Design
#
#   OSCListener.py is free software: you can redistribute it and/or modify
#   it for any purpose provided the following conditions are met:
#
#   1) Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   2) Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
#   3) Neither the name of the copyright owners nor the names of its contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
#   OSCListener.py is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#   INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#   PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#   HOLDERS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
#   OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
#   AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#   SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import socket
import threading
import time
from select import select
import math
import struct

class OSCListener:
	
	def __init__(self):
		self.listen_thread = None

#########################################
#
#	startListening creates the listening socket
#   and creates a thread that runs the listen() method
#
#########################################
	
	def startListening(self, port, delegate=None):
		self.udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.udpsocket.bind(('',port))
		self.udpsocket.setblocking(False)
		self.udpsocket.settimeout(1)
		self.delegate = delegate
  		self.listening = True
  		if self.listen_thread is None:
  			self.listen_thread = threading.Thread(target=self.listen)
  			self.listen_thread.daemon = True
  			self.listen_thread.start()

#########################################
#
#	stopListening sets a flag which will cause the listen loop to end on the next pass
#   setting the delegate to None prevents messages from being sent after stopListening
#   is called.
#
#########################################
 			
  	def stopListening(self):
  		self.delegate = None
  		self.listening = False
  		
#########################################
#
#	listen contains a loop that runs while the self.listening flag is True
#   listen uses select to determine if there is data available from the port
#   if there is, packetReceived is called
#   if not, the thread sleeps for a tenth of a second
#
#########################################
  		
  	def listen(self):
		input = [self.udpsocket]

  		while self.listening:
  			inputready,outputready,exceptready = select(input,[],[],0)
  			if ( len(inputready) == 1 ):
  				self.data,addr = self.udpsocket.recvfrom(256)
  				self.msglen = len(self.data)
  				self.packetReceived()
  			else:
  				time.sleep(0.1)
  	
		self.udpsocket.close()
  		self.listen_thread = None

#########################################
#
#	packetReceived calls processMessageAt for each complete OSC message
#   contained in the packet
#
#########################################
  	
  	def packetReceived(self):
		dataindex = 0
		while ( (dataindex >= 0 ) and ( dataindex < self.msglen ) ):
			dataindex = self.processMessageAt(dataindex);

#########################################
#
#	process message extracts the addressPattern
#   and argument list from the OSC message
#
#	currently the only supported arguments are floats and integers and strings
#
#	returns the index at the end of the complete message
#
#########################################

	def processMessageAt(self, si):
		oi = 0;
		dl = 0;
		zl = self.nextZero(si)
		
		#insure that string will terminate with room for 4 bytes of type definition
		if zl + 4 < self.msglen: 
			addressPattern = self.stringFrom(si)
			if addressPattern.startswith('/'):
				# determine the current index for the type character
				tl = self.nextIndexForString(addressPattern,si)
				
				# determine the current index for the data location
				dl = self.nextIndexForIndex(self.nextZero(tl))
				
				# if there's space for at least one argument, start a loop extracting
				# arguments defined in the type string an adding them to the args list
				if dl+4 <= self.msglen:
					if self.data[tl] == ',':
						tl += 1
					args = []
					done = False
					while ( not done) and ( (dl+4) <= self.msglen ):
						if self.data[tl] == '\x00':
							done = True
						elif self.data[tl] == 'f':
							a = struct.unpack_from('>f', self.data, dl)
							args.append(float(a[0]))
							dl += 4
						elif self.data[tl] == 'i':
							a = struct.unpack_from('>i', self.data, dl)
							args.append(int(a[0]))
						elif self.data[tl] == 's':
							es = nextZero(dl)
							if es <= self.msglen:
								a = self.stringFrom(dl)
								args.append(a)
								dl = nextIndexForIndex(es)
							else:
								done = True
								oi = -1
						else:   #unrecognized argument don't know length
							done = True
							oi = -1
						tl += 1
					
					# when done with the argument extraction loop, notify the delegate
					if self.delegate != None:
						self.delegate.receivedOSC(addressPattern, args)
					#else:
						#print addressPattern
						#print self.args
				else: #no arguments but an address pattern, notify delegate
					oi = -1
					if self.delegate != None:
						self.delegate.receivedOSC(addressPattern, [])
		else:
			oi = -1
			
		if oi != -1:
			oi = dl		#dl could point to another message within the packet
		
		return oi	

#########################################
#
#	nextZero searches for the next null character in the data starting at index si
#
#########################################
		
	def nextZero(self, si):
		i = si
  		notfound = True
  		s = ''
  		while notfound and i<self.msglen:
  			if self.data[i] == '\x00':
  				notfound = False
  			else:
  				i += 1
  		return i

#########################################
#
#	nextIndexForString determines a 4 byte padded index
#   for the length of the string starting from si
#
#########################################
  		
  	def nextIndexForString(self, s, start):
  		ml = math.trunc(len(s) / 4) + 1;
		return start + (ml*4);
		
#########################################
#
#	nextIndexForIndex determines a 4 byte padded index
#   starting from i
#
#########################################
		
	def nextIndexForIndex(self, i):
  		ml = math.trunc(i / 4) + 1;
		return ml*4;

#########################################
#
#	extracts a null terminated string starting at index si
#
#########################################
		
  	def stringFrom(self, si):
  		i = si
  		noterm = True
  		s = ''
  		while noterm and i<len(self.data):
  			if self.data[i] == '\x00':
  				noterm = False
  			else:
  				s += self.data[i]
  			i += 1
  		return s
  			