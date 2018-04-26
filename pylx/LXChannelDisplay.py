#   LXChannelDisplay.py
#
#	by Claude Heintz
#	copyright 2014 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html

try:
	from Tkinter import *
except:
	from tkinter import *

#########################################
#
#	LXChannelLevelWidget holds a sub-frame containing two labels
#
#########################################

class LXChannelLevelWidget:

	def __init__(self, frame, channel, level=0):
		self.sframe = Frame(frame, height=45, width=30)
		self.sframe.pack_propagate(0)
		
		self.clabel = Label(self.sframe, text=channel)
		self.clabel.pack()
		self.llabel = Label(self.sframe, text=level)
		self.llabel.pack()
		
	def set_level(self, level):
		self.llabel.config(text=level)

	def set_channel(self, channel):
		self.clabel.config(text=channel)
		
#########################################
#
#	LXChannelDisplay holds a frame of a number of rows and columns
#	of LXChannelLevelWidgets.
#	The channels displayed by these widgets are organized into pages.
#
#########################################

class LXChannelDisplay:

	def __init__(self, frame, channels, rows=10, columns=10):
		self.cwidgets = []
		self.channels = channels
		self.rows = rows
		
		self.columns = columns
		self.page = 0
		i=0
		c=1
		ch = 0
		total = rows*columns
		while i<total:
			if c==1:
				sframe = Frame(frame)
			ch = i+1
			cl = LXChannelLevelWidget(sframe, ch)
			if ch > self.channels:
				cl.set_channel("")
			cl.sframe.pack(side=LEFT)
			self.cwidgets.append(cl)
			i += 1
			c += 1
			if c > columns:
				sframe.pack()
				c = 1
				
	def setLevel(self, channel, level):
		if channel > self.channels:
				return
		chansperpage = self.columns*self.rows
		pgstart = self.page*chansperpage
		if channel < pgstart:
				return
		if channel > pgstart + chansperpage:
				return
		self.cwidgets[channel-1-pgstart].set_level(level)
		
	def beginIndex(self):
		chansperpage = self.columns*self.rows
		return self.page*chansperpage

	def endIndex(self):
		chansperpage = self.columns*self.rows
		pgend = (self.page + 1) *chansperpage 
		if pgend  > self.channels:
			return self.channels	
		return pgend

	def setPage(self, page):
		self.page = page
		chansperpage = self.columns*self.rows
		pgstart = self.page*chansperpage
		if pgstart+1 > self.channels:
			pgstart = 0
			self.page = 0
		i = 0
		while i < chansperpage:
			cw = self.cwidgets[i]
			cc = i+pgstart+1
			if cc > self.channels:
				cw.set_channel("")
			else:
				cw.set_channel(cc)
			i += 1

	def nextPage(self):
			self.setPage(self.page+1)

	def prevPage(self):
			p = self.page - 1
			if p < 0:
					p = 0
			self.setPage(p)
