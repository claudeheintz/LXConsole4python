#   LXCuesAsciiParser.py
#
#	by Claude Heintz
#	copyright 2014 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html

from LXCues import LXCue
from LXCues import LXCues
from USITTAsciiParser import USITTAsciiParser

class LXCuesAsciiParser (USITTAsciiParser):

	def __init__(self, channels, dimmers, interface):
		USITTAsciiParser.__init__(self)
		self.cues = LXCues(channels, dimmers)
		#default is 1-1 patch, start blank
		self.cues.clearPatch()
		self.cues.livecue.output = interface;
		
	def gethex(self, hc):
		ohc = ord(hc)
		if ohc >= 48 and ohc <= 57:
			return ohc - 48
		if ohc >= 65 and ohc <= 70:
			return ohc - 55
		if ohc >= 97 and ohc <= 102:
			return ohc - 87
		return 0
		
	def getlv(self, level):
		if level.startswith('H') or level.startswith('h'):
			if len(level) == 3:
				return (self.gethex(level[1])*16 + self.gethex(level[2]))/255.0*100.0
			return 0
		return int(level)
		
	def getsecs(self, tstr):
		i = tstr.find(':')
		if i < 0:
			return float(tstr)
		tparts = tstr.split(':')
		return int(tparts[0])*60+float(tparts[1])
		
	def doPatch(self, page, channel, dimmer, level):
		self.cues.patchAddressToChannel(int(dimmer),int(channel),self.getlv(level))
		return True # no error checking
		
	def doChannelForCue(self, cue, page, channel, level):
		q = self.cues.createCueForNumber(cue)
		q.setNewLevel(channel, self.getlv(level))
		return True
		
	def doDownForCue(self, cue, page, down, waitdown):
		q = self.cues.createCueForNumber(cue)
		q.downtime = self.getsecs(down)
		q.waitdowntime = self.getsecs(waitdown)
		
	def doUpForCue(self, cue, page, up, waitup):
		q = self.cues.createCueForNumber(cue)
		q.uptime = self.getsecs(up)
		q.waituptime = self.getsecs(waitup)
		
	def doFollowonForCue(self, cue, page, follow):
		q = self.cues.createCueForNumber(cue)
		q.followtime = self.getsecs(follow)
		
	def doOSCstringForCue(self, cue, string):
		q = self.cues.createCueForNumber(cue)
		q.oscstring = string
		
	def keywordMfgForCue(self, keyword):
		if keyword == "$$OSCstrin":
			self.doKeywordOSCstringForCue()
		return True
		
	def doKeywordOSCstringForCue(self,):
		if len(self.tokens) >= 2:
		#assumes that the tokens were broken up by slashes which were read as delimiters
		#this will not work if the OSC message contains any other delimiter characters
			self.doOSCstringForCue(self.cue, self.tokenStringForText("/"))
			return True
		self.addMessage("bad $$OSCstring (ignored)")
		return True
		
	def recognizedMfgBasic(self, keyword):
		if keyword == "$$dimoption":
			return True
		return False
		
	def keywordMfgBasic(self, keyword):
		if keyword == "$$dimoption":
			if len(self.tokens) == 3:
				self.cues.setOptionForAddress(int(self.tokens[1]), int(self.tokens[2]))
		return True
		
	def parseFile(self, path):
		f = open(path, 'r')
		fs = f.read()
		f.close()
		self.success = USITTAsciiParser.processString(self,fs)
		self.cues.putCuesInOrder()
		return self.message