#   LXPatch.py
#
#	by Claude Heintz
#	copyright 2014 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html


class LXPatchableAddress:

	def __init__(self, number, level=1.0, option=0):
		self.number = number
		self.level = level
		self.option = option
		
	def convertPercent(self, level):
		value = round(level/100.0*255.0)
		if value < 0:
			return 0
		if value > 255:
			return 255
		return int(value)
		
	def dmxForLevel(self, level, master=1.0):
		if self.option == 0:
			return self.convertPercent(master*self.level*level)
		elif self.option == 1:
			# option 1 is non-dim
			if self.convertPercent(master*self.level*level) > 0:
				return 255
		elif self.option == 2:
			# option 2 is always on
			return self.convertPercent(100*self.level)
		elif self.option == 3:
			# option 3 is no master
			return self.convertPercent(level*self.level)
		
		return 0

class LXPatchList:
	
	def __init__(self, number):
		self.list = []
		self.list.append(LXPatchableAddress(number))
		
	def patchAddress(self, address, level=1.0, option=0):
		self.list.append(LXPatchableAddress(address, level, option))
		
	def unpatchAddress(self, address):
		newlist = []
		for i in range (len(self.list)):
			if self.list[i].number != address:
				newlist.append(self.list[i])
		self.list = newlist
		
	def highestAddress(self, h):
		for i in range (len(self.list)):
			if self.list[i].number > h:
				h = self.list[i].number
		return h
		
	def setOptionForAddress(self, addr, option, level=-1):
		for i in range (len(self.list)):
			if self.list[i].number == addr:
				self.list[i].option = option
				if level >= 0:
					self.list[i].level = level/100.0
				return True
		return False
		
	def containsAddress(self, addr):
		for i in range (len(self.list)):
			if self.list[i].number == addr-1:
				return True
		return False
		
class LXPatch:

	def __init__(self, channels, addresses):
		self.addresses = addresses
		self.patch = []
		for i in range (channels):
			self.patch.append(LXPatchList(i))
			
	def unpatchAddress(self, address):
		for i in range (len(self.patch)):
			self.patch[i].unpatchAddress(address)
			
	def unpatchAll(self):
		for i in range (len(self.patch)):
			self.patch[i].list = []	
			
	def patchAddressToChannel(self, address, channel, level=1.0, option=0):
		if address > 0 and address <= self.addresses:
			self.unpatchAddress(address-1)
			if channel > 0 and channel <= len(self.patch):
				self.patch[channel-1].patchAddress(address-1, level, option)
		
	def highestAddress(self):
		h = 0
		for i in range (len(self.patch)):
			h = self.patch[i].hightstAddress(h)
		return h
		
	def setOptionForAddress(self, addr, option, level=-1):
		for i in range (len(self.patch)):
			if self.patch[i].setOptionForAddress(addr-1, option, level):
				break
		
	def patchString(self):
		ca = []
		la = []
		for k in range(self.addresses):
			ca.append(0)
			la.append(0)
		if len(self.patch) > 0:
			for i in range(len(self.patch)):
				pl = self.patch[i]
				if len(pl.list) > 0:
					for j in range(len(pl.list)):
						ca[pl.list[j].number] = i + 1
						la[pl.list[j].number] = int(pl.list[j].level*100)
		s = ""
		tc = 0
		for k in range(self.addresses):
			if tc == 0:
				s = s + "Patch 1 " + str(ca[k]) +"<"+ str(k+1) +"@" + str(la[k])
				tc = 1;
			else:
				s = s + " " + str(ca[k]) +"<"+ str(k+1) +"@" + str(la[k])
				tc += 1
			if tc > 5:
				s += "\n"
				tc = 0
		if tc > 0:
			s += "\n"
		return s
		
	def optionString(self):
		s='\n'
		if len(self.patch) > 0:
			for i in range(len(self.patch)):
				pl = self.patch[i]
				if len(pl.list) > 0:
					for j in range(len(pl.list)):
						if pl.list[j].option > 0:
							s += "$$dimoption "
							s += str(pl.list[j].number+1)
							s += " "
							s += str(pl.list[j].option)
							s += "\n"
			s += "\n"
		return s
		
	def byteArrayFromFloatList(self, fl, master=1.0):
		ba = bytearray(self.addresses)
		for j in range(self.addresses):	#zero the bytearray
			ba[j] = 0
		if len(fl) == len(self.patch):		#error if these are not the same length
			for i in range(len(fl)):
				pl = self.patch[i]
				if len(pl.list) > 0:
					for j in range(len(pl.list)):
						ba[pl.list[j].number] = pl.list[j].dmxForLevel(fl[i], master)
		return ba
		
	def channelForDimmer(self, dimmer):
		for i in range (len(self.patch)):
			if self.patch[i].containsAddress(dimmer):
				return i+1
		return 0
			