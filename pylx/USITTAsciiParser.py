#   USITTAsciiParser
#
#	by Claude Heintz
#	copyright 2014 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html

##### This is an abstract class for parsing strings to extract
#     data formatted as specified in:
#
# 	  ASCII Text Representation for Lighting Console Data
#	  http://old.usitt.org/documents/nf/a03asciitextreps.pdf
######

class USITTAsciiParser:
	END_DATA = -1
	NO_PRIMARY = 0
	CUE_COLLECT = 1
	GROUP_COLLECT = 2
	SUB_COLLECT = 3
	MFG_COLLECT = 5
	
	def __init__(self):
		self.line = 0
		self.state = USITTAsciiParser.NO_PRIMARY
		self.startedLine = False
		self.tokens = []
		self.cstring = ""
		self.message = ""
		self.console = None
		self.manufacturer = None
		self.cue = None
		self.part = None
		self.group = None
		self.sub = None
		self.cuepage = None
		self.grouppage = None
		self.subpage = None
		self.console = None
		self.manufacturer = None
		
##### processString(string) parses the string passed to it character by character
#     it returns True unless there is an error in the string
#     for the most part, exceptions are noted and ignored
#     printing the .message after calling parseString will list any exceptions
#
#     As the string is read and data is extracted, there are a number of 
#     implementation specific methods that are called.  A subclass should override
#     these methods and do something with the data.  For instance, as individual channel
#     levels are extracted, doChannelForCue(self, cue, page, channel, level) is called.
#     An implementing subclass would override this method to set channel@level in cue.
#
##### look at the bottom of the file for all the methods that can be overridden
		
	def processString(self, s):
		valid = True
		for i in range(len(s)):
			self.processCharacter(s[i])
			if not valid or self.state == USITTAsciiParser.END_DATA:
				break
			
		if self.startedLine:
			self.addTokenWithCurrentString()
			self.processLine()
			
		if valid and self.state != USITTAsciiParser.END_DATA:
			self.addMessage("ER 0100 unexpected termination: ENDDATA missing")
			valid = self.finishUnfinished()
		else:
			self.addMessage("0000 processing complete")

		if valid:
			self.doFinalCleanup()
	
		return valid;

##### processCharacter takes a character and determines if it ends the current line.
#     If so, the entire line is processed.
#     Otherwise, the character is added to the current string unless
#     it is a delimiter, in which case, the current string is added to the tokens list
##### A '!' character puts processing in comment mode until the end of the line is reached
				
	def processCharacter(self, c):
		# check to see if the character is a line termination character
		if c == '\n' or c == '\r':
			if not ( len(self.cstring) == 0 and len(self.tokens) == 0 ):
				if not ( self.cstring == "!" or len(self.cstring) == 0 ):
					self.addTokenWithCurrentString()
			if self.processLine():
				self.endLine()
			else:
				return False
		elif not self.cstring == "!":
			if c == '\t' or ( ord(c) > 31 and ord(c) <127 ):
				if self.isDelimiter(c):
					if not ( self.cstring == "!" or len(self.cstring) == 0 ):
						self.addTokenWithCurrentString()
				else:
					if c == "!":
						self.cstring = c
					else:
						self.cstring += c
					if not self.startedLine:
						self.beginLine()
			else:
				self.addMessage("Invalid Character (ignored)")
			
		return True
		
##### addTokenWithCurrentString() self.tokens is a list of small strings that
#     that make up the current line.  each token is separated by one or more
#     of the delimiter characters defined in
#     ASCII Text Representation for Lighting Console Data 5.4, page 13
#####
		
	def addTokenWithCurrentString(self):
		self.tokens.append(self.cstring)
		self.cstring = ""
		
##### beginLine is called when the first non-delimiter character
#     of a line is encountered
#####
		
	def beginLine(self):
		self.startedLine = True
		self.line += 1

##### endLine resets the current string and tokens list
#
#####

	def endLine(self):
		self.cstring = ""
		self.tokens = []
		self.startedLine = False
		self.finishProcessingLine()

##### finishProcessingLine (for override if needed)

	def finishProcessingLine(self):
		test = True

##### finishUnfinished (for override if needed)
			
	def finishUnfinished(self):
		test = True

##### doFinalCleanup (for override if needed)
			
	def doFinalCleanup(self):
		test = True
	

##### processLine takes a complete line and calls the appropriate keyword function
#     processLine returns True as long as there is no error to stop processing
#####
		
	def processLine(self):
		if len(self.tokens) > 0:
			keyword = self.tokens[0]
			
			# check for manufacturer specific keywords
			if keyword.startswith("$"):
				if keyword.startswith("$$"):
					if self.recognizedMfgBasic(keyword):
						return self.keywordMfgBasic(keyword)
				else:
					return self.keywordMfgPrimary(keyword)
			
			#keywords are limited to 10 characters	
			if len(keyword) > 10:
				keyword = keyword[0:10]
				
			if keyword.lower() == "clear":
				return self.keywordClear()
				
			if keyword.lower() == "console":
				return self.keywordConsole()
				
			if keyword.lower() == "enddata":
				self.state = USITTAsciiParser.END_DATA
				return True
				
			if keyword.lower() == "ident":
				return self.keywordIdent()
				
			if keyword.lower() == "manufactur":
				return self.keywordManufacturer()
				
			if keyword.lower() == "patch":
				return self.keywordPatch()
				
			if keyword.lower() == "set":
				return self.keywordSet()
				
			if keyword.lower() == "cue":
				return self.keywordCue()
				
			if keyword.lower() == "group":
				return self.keywordGroup()
				
			if keyword.lower() == "sub":
				return self.keywordSub()
				
			if self.state > USITTAsciiParser.MFG_COLLECT -1:
				return self.keywordMfgSecondary(keyword)
				
			if self.state == USITTAsciiParser.CUE_COLLECT:
				return self.keywordCueSecondary(keyword)
				
			if self.state == USITTAsciiParser.GROUP_COLLECT:
				return self.keywordGroupSecondary(keyword)
				
			if self.state == USITTAsciiParser.SUB_COLLECT:
				return self.keywordSubSecondary(keyword)
			
		return True		#any other keyword is simply ignored	

	
##### addMessage is used to report exceptions that may change how the ASCII
#     data is interpreted, but not necessarily enough to stop processing.
#     After processString has been called the message can be read
#####
	
	def addMessage(self, message):
		self.message = self.message +"Line " + str(self.line) + ": " + message + "\n"
		
	def tokenStringForText(self, delimiter=" "):
		tc = len(self.tokens)
		if tc > 1:
			ti = 1;
			rs = self.tokens[ti];
			ti += 1
			while ti < tc:
				rs = rs + delimiter + self.tokens[ti];
				ti += 1
			return rs
		return None
		

##### process keyword functions
#     each of these functions is called in response to a specific keyword
#     keywords are found at the beginning of a line ie. self.tokens[0]
#     each keyword function should return True if there are no errors
#     These functions set the parse state and various other values.
#
#     To implement the functionality of these keywords, override the 
#     corresponding "do" function
#####

	def keywordClear(self):
		if len(self.tokens) == 2:
			return self.doClearItem(self.tokens[1], "")
		if len(self.tokens) == 3:
			return self.doClearItem(self.tokens[1], self.tokens[2])
		self.addMessage("bad CLEAR (ignored)")
		return True
		
	def keywordConsole(self):
		if len(self.tokens) == 2:
			self.console = self.tokens[1]
			return True
		self.addMessage("bad CONSOLE(ignored)")
		return True
		
	def keywordIdent(self):
		if len(self.tokens) == 2:
			if self.tokens[1] == "3:0":
				return True
			if self.tokens[1] == "3.0":
				return True
		return False
		
	def keywordManufacturer(self):
		if len(self.tokens) == 2:
			self.manufacturer = self.tokens[1]
			return True
		self.addMessage("bad MANUFACTUR (ignored)")
		return True
	
	def keywordPatch(self):
		tc = len(self.tokens)
		if tc > 4:
			rs = 5;
			valid = True
			while valid and tc >= rs:
				valid = self.doPatch(self.tokens[1], self.tokens[rs-3], self.tokens[rs-2], self.tokens[rs-1])
				rs += 3
			if valid:
			 return True
		self.addMessage("bad PATCH (ignored)")
		return True
		
	def keywordSet(self):
		if len(self.tokens) == 3:
			self.doSet(self.tokens[1], self.tokens[2])
			return True
		self.addMessage("bad SET (ignored)")
		return True
		
	def keywordCue(self):
		self.state = USITTAsciiParser.CUE_COLLECT
		self.part = None
		if len(self.tokens) == 2:
			self.cue = self.tokens[1]
			self.cuepage = ""
			return True
		if len(self.tokens) == 3:
			self.cue = self.tokens[1]
			self.cuepage = self.tokens[2]
			return True
			
		self.cue = None
		self.cuepage = None
		self.addMessage("bad CUE (ignored)")
		return True
		
	def keywordGroup(self):
		self.state = USITTAsciiParser.GROUP_COLLECT
		self.part = None
		if len(self.tokens) == 2:
			self.group = self.tokens[1]
			self.grouppage = ""
			return True
		if len(self.tokens) == 3:
			self.group = self.tokens[1]
			self.grouppage = self.tokens[2]
			return True
			
		self.group = None
		self.grouppage = None
		self.addMessage("bad GROUP (ignored)")
		return True
		
	def keywordSub(self):
		self.state = USITTAsciiParser.SUB_COLLECT
		self.part = None
		if len(self.tokens) == 2:
			self.sub = self.tokens[1]
			self.subpage = ""
			return True
		if len(self.tokens) == 3:
			self.sub = self.tokens[1]
			self.subpage = self.tokens[2]
			return True
			
		self.sub = None
		self.subpage = None
		self.addMessage("bad SUB (ignored)")
		return True

	def keywordMfgBasic(self, keyword):
		return True;
		
	def keywordMfgPrimary(self, keyword):
		self.state = USITTAsciiParser.MFG_COLLECT
		if self.recognizedMfgPrimary(keyword):
			return self.doMfgPrimary(keyword)
		return True;
		
	def keywordMfgSecondary(self, keyword):
		if self.recognizedMfgSecondary(keyword):
			return self.doMfgSecondary(keyword)
		return True;
		
##### secondary keywords are similar to primary keywords
#     when cue, group or sub primary keywords are encountered
#     the state is set so that secondary keywords modify
#     the current cue, group or sub
#####
		
	def keywordCueSecondary(self, keyword):
		if self.cue != None and self.cue != "" and len(self.tokens) > 1:
			
			if keyword.startswith("$$"):
				return self.keywordMfgForCue(keyword)
			
			if keyword.lower() == "chan":
				return self.keywordChannelForCue()
				
			if keyword.lower() == "down":
				return self.keywordDownForCue()
				
			if keyword.lower() == "followon":
				return self.keywordFollowonForCue()
			
			if keyword.lower() == "link":
				return self.keywordLinkForCue()
				
			if keyword.lower() == "part":
				return self.keywordPartForCue()
				
			if keyword.lower() == "text":
				return self.keywordTextForCue()
				
			if keyword.lower() == "up":
				return self.keywordUpForCue()
				
				
		self.addMessage("(ignored) unknown or out of place " + keyword )
		return True
		
	def keywordGroupSecondary(self, keyword):
		if self.group != None and self.group != "" and len(self.tokens) > 1:
			
			if keyword.startswith("$$"):
				return self.keywordMfgForGroup(keyword)
			
			if keyword.lower() == "chan":
				return self.keywordChannelForGroup()
			
			if keyword.lower() == "part":
				return self.keywordPartForGroup()
				
			if keyword.lower() == "text":
				return self.keywordTextForGroup()
			
		return True
		
	def keywordSubSecondary(self, keyword):
		if self.sub != None and self.sub != "" and len(self.tokens) > 1:
			
			if keyword.startswith("$$"):
				return self.keywordMfgForGroup(keyword)
			
			if keyword.lower() == "chan":
				return self.keywordChannelForSub()
				
			if keyword.lower() == "down":
				return self.keywordDownForSub()
				
			if keyword.lower() == "text":
				return self.keywordTextForSub()
				
			if keyword.lower() == "up":
				return self.keywordUpForCue()
			
		return True
		
##### handle each specific secondary keyword
#     these methods check that the number of tokens is correct for the keyword
#     and then pass them along to a specific "do" method.
#     All "do" methods are meant to be overridden by an implementing subclass
##### cue keywords

	def keywordChannelForCue(self):
		lt = len(self.tokens) 
		v = True
		rs = 3
		while v and rs <= lt:
			v = self.doChannelForCue(self.cue, self.cuepage, self.tokens[rs-2], self.tokens[rs-1])
			rs += 2
		if v:
			return True
		self.addMessage("bad CHAN (ignored)")
		return True
		
	def keywordDownForCue(self):
		if len(self.tokens) == 2:
			self.doDownForCue(self.cue, self.cuepage, self.tokens[1], "0")
			return True
		if len(self.tokens) == 3:
			self.doDownForCue(self.cue, self.cuepage, self.tokens[1], self.tokens[2])
			return True
		self.addMessage("bad DOWN (ignored)")
		return True
		
	def keywordFollowonForCue(self):
		if len(self.tokens) == 2:
			self.doFollowonForCue(self.cue, self.cuepage, self.tokens[1])
			return True
		self.addMessage("bad FOLLOWON (ignored)")	
		return True
		
	def keywordlinkForCue(self):
		if len(self.tokens) == 2:
			self.doLinkForCue(self.cue, self.cuepage, self.tokens[1])
			return True
		self.addMessage("bad LINK (ignored)")	
		return True
		
	def keywordPartForCue(self):
		if len(self.tokens) == 2:
			self.doPartForCue(self.cue, self.cuepage, self.tokens[1])
			return True
		self.addMessage("bad PART (ignored)")	
		return True
		
	def keywordTextForCue(self):
		if len(self.tokens) > 1:
			self.doTextForCue(self.cue, self.cuepage, self.tokenStringForText())
			return True
		self.addMessage("bad TEXT (ignored)")
		return True
		
	def keywordUpForCue(self):
		if len(self.tokens) == 2:
			self.doUpForCue(self.cue, self.cuepage, self.tokens[1], "0")
			return True
		if len(self.tokens) == 3:
			self.doUpForCue(self.cue, self.cuepage, self.tokens[1], self.tokens[2])
			return True
		self.addMessage("bad UP (ignored)")
		return True

##### group keywords
		
	def keywordChannelForGroup(self):
		lt = len(self.tokens) 
		v = True
		rs = 3
		while v and rs <= lt:
			v = self.doChannelForGroup(self.group, self.grouppage, self.tokens[rs-2], self.tokens[rs-1])
			rs += 2
		if v:
			return True
		self.addMessage("Warning:  bad CHAN (ignored)")
		return True
		
	def keywordPartForGroup(self):
		if len(self.tokens) == 2:
			self.doPartForGroup(self.group, self.grouppage, self.tokens[1])
			return True
		self.addMessage("bad PART (ignored)")	
		return True
	
	def keywordTextForGroup(self):
		if len(self.tokens) > 1:
			self.doTextForGroup(self.group, self.grouppage, self.tokenStringForText())
			return True
		self.addMessage("bad TEXT (ignored)")
		return True
		
##### sub keywords	
	
	def keywordChannelForSub(self):
		lt = len(self.tokens) 
		v = True
		rs = 3
		while v and rs <= lt:
			v = self.doChannelForSub(self.sub, self.subpage, self.tokens[rs-2], self.tokens[rs-1])
			rs += 2
		if v:
			return True
		self.addMessage("Warning:  bad CHAN (ignored)")
		return True
	
	def keywordDownForSub(self):
		if len(self.tokens) == 2:
			self.doDownForSub(self.sub, self.subpage, self.tokens[1], "0")
			return True
		if len(self.tokens) == 3:
			self.doDownForSub(self.sub, self.subpage, self.tokens[1], self.tokens[2])
			return True
		self.addMessage("bad UP (ignored)")
		return True
		
	def keywordTextForSub(self):
		if len(self.tokens) > 1:
			self.doTextForSub(self.sub, self.subpage, self.tokenStringForText())
			return True
		self.addMessage("bad TEXT (ignored)")
		return True
		
	def keywordUpForSub(self):
		if len(self.tokens) == 2:
			self.doUpForSub(self.sub, self.subpage, self.tokens[1], "0")
			return True
		if len(self.tokens) == 3:
			self.doUpForSub(self.sub, self.subpage, self.tokens[1], self.tokens[2])
			return True
		self.addMessage("bad UP (ignored)")
		return True

########################################################################
#
#  override these functions to actually implement whatever action is appropriate
#
######################################################################## 

##### primary actions

	def doClearItem(self, what, page):
		test = True
		
	def doSet(self, item, value):
		test = True
		
	def doPatch(self, page, channel, dimmer, level):
		return True

##### cue actions	
	
	def doChannelForCue(self, cue, page, channel, level):
		return True
	
	def doDownForCue(self, cue, page, down, waitdown):
		test = True
		
	def doFollowonForCue(self, cue, page, follow):
		test = True
	
	def doLinkForCue(self, cue, page, link):
		test = True
		
	def doPartForCue(self, cue, page, part):
		self.part = part
		test = True	
		
	def doTextForCue(self, cue, page, text):
		test = True
	
	def doUpForCue(self, cue, page, up, waitup):
		test = True


##### group actions
		
	def doChannelForGroup(self, group, page, channel, level):
		return True
		
	def doPartForGroup(self, group, page, part):
		self.part = part
		test = True	
		
	def doTextForGroup(self, group, page, text):
		test = True
		

##### sub actions
		
	def doChannelForSub(self, sub, page, channel, level):
		return True
		
	def doDownForSub(self, sub, page, down, waitdown):
		test = True
		
	def doTextForSub(self, sub, page, text):
		test = True
		
	def doUpForSub(self, sub, page, up, waitup):
		test = True
		
########################################################################	
#
#     override these functions to handle manufacturer keywords
#
########################################################################
	
	def recognizedMfgBasic(self, keyword):
		return False
		
	def recognizedMfgPrimary(self, keyword):
		return False
		
	def recognizedMfgSecondary(self, keyword):
		return False
		
	def doMfgPrimary(self, keyword):
		return True
		
	def doMfgPrimary(self, keyword):
		return True
		
	def keywordMfgForCue(self, keyword):
		return True
		
	def keywordMfgForGroup(self, keyword):
		return True
		
	def keywordMfgForSub(self, keyword):
		return True
		
##### utility method isDelimiter(c)
#     test to see if character is one of the standard delimiter characters
#     ASCII Text Representation for Lighting Console Data 5.4, page 13
#####
	
	def isDelimiter(self, c):
		if c == '\t':
			return True
		if c == ' ':
			return True
		if c == ',':
			return True
		if c == '/':
			return True
		if c == ';':
			return True
		if c == '<':
			return True
		if c == '=':
			return True
		if c == '>':
			return True
		if c == '@':
			return True
		return False
	
