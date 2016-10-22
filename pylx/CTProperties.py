#   CTProperties.py
#
#	by Claude Heintz
#	copyright 2014 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html


#################################################################
#
#	This file contains a very basic properties file parser
#	assumes a file with key=value pairs, one to a line and no frills
#	like quotes or escapes
#
#################################################################


class CTProperties:

	def __init__(self):
		self.properties = {}
		
		
	def parseString(self, string):
		lines = string.split("\n")
		for l in lines:
			pair = l.split("=")
			if len(pair) == 2:
				self.properties[pair[0]] = pair[1]
			
	def parseFile(self, filename):
		f = open(filename, 'r')
		contents = f.read()
		f.close()
		self.parseString(contents)
		
	def stringForKey(self, key, default=""):
		if key in self.properties:
			return str(self.properties[key])
		return default
		
	def intForKey(self, key, default=0):
		if key in self.properties:
			return int(self.properties[key])
		return default
		
		