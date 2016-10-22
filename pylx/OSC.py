#   OSC.py
#
#	by Claude Heintz
#	copyright 2014 by Claude Heintz Design
#
#   OSC.py is free software: you can redistribute it and/or modify
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
#   OSC.py is distributed in the hope that it will be useful,
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