#   DMXUSBPro.py
#
#	by Claude Heintz
#	copyright 2015 by Claude Heintz Design
#
#   DMXUSBPro.py is free software: you can redistribute it and/or modify
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
#   DMXUSBPro.py is distributed in the hope that it will be useful,
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
#
#   requires download from:  pyserial https://pypi.python.org/pypi/pyserial



import threading
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