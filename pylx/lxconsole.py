#!/usr/bin/python

#   lxconsole.py
#
#	by Claude Heintz
#	copyright 2014-15 by Claude Heintz Design
#
#   lxconsole.py is free software: you can redistribute it and/or modify
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
#   lxconsole.py is distributed in the hope that it will be useful,
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


#################################################################
#
#     This file contains the main interface for a simple lighting control application
#     The user interface is provided through Tkinter
#     if Tkinter is not installed, on linux use:      sudo apt-get install python-tk
#     refer to READ ME.txt for configursation information	
#
#################################################################


from Tkinter import *
import tkFileDialog
import tkMessageBox
from CTProperties import CTProperties
from LXChannelDisplay import LXChannelDisplay
from LXCues import LXCues
from LXCues import LXLiveCue
from LXCuesAsciiParser import LXCuesAsciiParser
from OSCListener import OSCListener
import time
import threading
import os

class App:

	def __init__(self, master):
		self.boss = master
		master.title('LXConsole')
		master.bind('<Return>', self.read_cmd)
		
		#read application options
		self.props = CTProperties()
		cpath = os.path.realpath(__file__)
		self.pylxdir = os.path.dirname(cpath)
		self.props.parseFile( self.pylxdir + "/lxconsole.properties")
		chans = self.props.intForKey("channels", 300)
		dims = self.props.intForKey("dimmers", 512)
	
		#create cues
		self.cues = LXCues(chans, dims)
		self.cues.delegate = self
		self.update_thread = None
		self.updating = False
		self.path = ""
		self.lastcomplete = None
		self.back = None
		self.oscin = None
		
		#setup output interface
		use_interface = self.props.stringForKey("interface", "")
		if use_interface == "widget":
			self.set_usb_out()
		else:
			self.set_artnet_out()
		self.oscport = int(self.props.stringForKey("oscport", "7688"))
		self.echo_osc_ip = self.props.stringForKey("echo_osc_ip", "none")
		self.echo_osc_port = int(self.props.stringForKey("echo_osc_port", "9000"))
		
		#create main tk frame
		f = Frame(master, height=500, width=580)
		f.pack()
		f.pack_propagate(0)
		
		#create left frame
		lf = Frame(f)
		
		# create channel display
		self.chandisp = LXChannelDisplay(lf,self.cues.channels, 10)

		# create command field
		self.e = Entry(lf)
		self.e.pack(fill=X, side=BOTTOM)
		self.e.bind("<Key>", self.key)
		
		lf.pack(side=LEFT)
		
		#create right frame
		rf = Frame(f, height=500, width=250)
		rf.pack(side=RIGHT)
		rf.pack_propagate(0)
		
		# create current cue label
		self.cqt = Label(rf, anchor=W, width=20, padx=5, pady=5)
		self.cqt.pack(fill=X, side=TOP)
		
		# create current cue up label
		self.cqup = Label(rf, anchor=W, width=20, padx=5, pady=5)
		self.cqup.pack(fill=X, side=TOP)
		
		# create current cue down label
		self.cqdn = Label(rf, anchor=W, width=20, padx=5, pady=5)
		self.cqdn.pack(fill=X, side=TOP)
		
		# create current cue follow label
		self.cqf = Label(rf, anchor=W, width=20, padx=5, pady=5)
		self.cqf.pack(fill=X, side=TOP)
		
		# create go button
		cf = Frame(rf)
		self.gb = Button(cf, text="Go", width=10, command=self.go_cmd)
		self.gb.pack(side=BOTTOM)
		self.sb = Button(cf, text="Stop", width=10, command=self.stop_cmd)
		self.sb.pack(side=BOTTOM)
		self.sb = Button(cf, text="Back", width=10, command=self.back_cmd)
		self.sb.pack(side=BOTTOM)
		cf.pack(side=LEFT)
		
		# create next cue label and pack the gf frame
		self.nx = Label(rf, width=5)
		self.nx.pack(side=LEFT)
		
		# create master fader
		pf = Frame(rf, width=20)
		pf.pack(side=RIGHT)
		self.mfader = Scale(rf, from_=100, to=0, showvalue=0)
		self.mfader.set(100)
		self.mfader.config(command=self.scroll_change)
		self.mfader.pack(side=RIGHT)
	
		# create a menu
		menubar=Menu(master)
		filemenu=Menu(menubar, tearoff=0)
		filemenu.add_command(label='Open',command=self.menuOpen)
		filemenu.add_command(label='Save',command=self.menuSave)
		filemenu.add_command(label='Exit', command=self.menuQuit)
		menubar.add_cascade(label='File', menu=filemenu)
		
		self.oscIN = BooleanVar()
		livemenu=Menu(menubar, tearoff=0)
		livemenu.add_checkbutton(label="OSC", onvalue=True, offvalue=False, variable=self.oscIN, command=self.menuOSC)
		livemenu.add_command(label='Set Output to USB', command=self.menu_set_usb_out)
		livemenu.add_command(label='Set Output to Art-Net', command=self.menu_set_artnet_out)
		menubar.add_cascade(label='Live', menu=livemenu)
		
		helpmenu=Menu(menubar, tearoff=0)
		helpmenu.add_command(label='About', command=self.menuAbout)
		helpmenu.add_command(label='Quick Help', command=self.menuQuickHelp)
		menubar.add_cascade(label='Help', menu=helpmenu)
		
		master.config(menu=menubar)
		
		self.e.focus_set()


#########################################
#
#	menu methods handle setting the output interface
#
#########################################

	def set_usb_out(self):
		if self.cues.livecue.output != None:
			self.cues.livecue.output.close()
		try:
			from DMXUSBPro import DMXUSBProInterface
			serial_port = self.props.stringForKey("widget", "")
			iface = DMXUSBProInterface(serial_port)
			self.cues.livecue.output = iface
			iface.startSending()
		except:
			tkMessageBox.showinfo("Error Connecting", sys.exc_info()[0])
			
	def set_artnet_out(self):
		from ArtNet import ArtNetInterface
		if self.cues.livecue.output != None:
			self.cues.livecue.output.close()
		ip = self.props.stringForKey("artip", "10.255.255.255")
		iface = ArtNetInterface(ip)
		self.cues.livecue.output = iface
		iface.startSending()
		
		
#########################################
#
#	menu methods handle the menu commands
#
#########################################
		
	def menuOpen(self):
		filename = tkFileDialog.askopenfilename(filetypes=[('ASCII files','*.asc')])
		if len(filename) > 0:
			p = LXCuesAsciiParser(self.cues.channels, self.cues.livecue.patch.addresses, self.cues.livecue.output)
			message = p.parseFile(filename)
			if p.success:
				self.cues = p.cues
				self.cues.next = None
				self.lastcomplete = None
				self.back = None
				self.path = filename
			tkMessageBox.showinfo(message='Open',detail=message,icon='info',title='Open')
			self.boss.title(os.path.basename(self.path))
			self.updateCurrent()
		
	def menuSave(self):
		if len(self.path) > 0:
			filename = tkFileDialog.asksaveasfilename(defaultextension="asc", initialfile=os.path.basename(self.path), initialdir=os.path.dirname(self.path))
		else:
			filename = tkFileDialog.asksaveasfilename(defaultextension="asc")
		if len(filename) > 0:
			f = open(filename, 'w')
			f.write(self.cues.asciiString())
			f.close()
		
	def menuQuit(self):
		if tkMessageBox.askokcancel("Quit", "Do you really wish to quit?"):
			if self.oscin != None:
				self.oscin.stopListening()
			sys.exit()
	
	def menu_set_usb_out(self):
		if tkMessageBox.askokcancel("USB", "Set USB DMX Pro as output interface?"):
			self.set_usb_out()
	
	def menu_set_artnet_out(self):
		if tkMessageBox.askokcancel("Art-Net", "Set Art-Net as output interface?"):
			self.set_artnet_out()


	def menuOSC(self):
		if self.oscin == None:
			self.oscin = OSCListener()
			self.oscin.startListening(self.oscport, self.cues)
		else:
			self.oscin.stopListening()
			self.oscin = None

	def menuAbout(self):
		tkMessageBox.showinfo(message='LXConsole|Python v 0.5',detail='build 1021\nCopyright 2015 Claude Heintz Design\nSee source files for license info.',icon='info',title='About LXConsole')

	def menuQuickHelp(self):
		f = open(self.pylxdir + '/quickhelp.txt', 'r')
		message = f.read()
		f.close()
		self.displayMessage(message, 'Quick Help')
		
#########################################
#
#	go and stop
#
#	go_cmd is initiated by the Go Button
#	stop_cmd is called by pressing the esc key
#
#########################################
	
	def go_cmd(self):
		self.cues.delegate = self
		self.cues.startFadingToCue(self.cues.next)
			
	
	def stop_cmd(self):
		self.cues.livecue.stopped = True
		if self.cues.livecue.fading:
			self.cues.livecue.followtime = -1
			self.cues.livecue.stopFading()
			
	def back_cmd(self):
		if self.back != None:
			self.cues.delegate = self
			self.cues.startFadingToCue(self.back)

#########################################
#
#	fade callbacks to the fade delegate are called by the fading thread
#
#########################################

	def fadeStarted(self):
		self.cqup.config(text="Fading: " + self.cues.livecue.titleString())
		self.cqdn.config(text="")
		self.cqf.config(text=self.cues.livecue.followTimeString())
		self.back = self.lastcomplete
	
	def fadeProgress(self):
		self.updateDisplayAsynch()
		
	def fadeComplete(self):
		if self.cues.livecue.stopped == False:
			self.lastcomplete = self.cues.current
		self.updateDisplay()
		self.updateCurrent()

#########################################
#
#	display updates
#	can happen on a separate thread to allow the fade thread
#	not to have to wait for the user interface
#
#########################################

	def updateAsynch(self):
		while (self.updating):
			self.updating = False
			self.updateDisplay()
			time.sleep(0.1)	#max update every 10th of a second
		self.update_thread = None
		
	def updateDisplayAsynch(self):
  		self.updating = True;
  		if self.update_thread is None:
  			self.update_thread = threading.Thread(target=self.updateAsynch)
  			self.update_thread.daemon = True
  			self.update_thread.start()
		
	def updateDisplay(self):
		self.cues.updateDisplay(self.chandisp)
		
	def updateOutput(self):
		self.cues.updateDisplay(self.chandisp)
		self.cues.livecue.writeToInterface()
		
	def updateCurrent(self):
		if self.cues.current != None:
			self.cqt.config(text=self.cues.current.titleString())
			self.cqup.config(text=self.cues.current.upTimeString())
			self.cqdn.config(text=self.cues.current.downTimeString())
			self.cqf.config(text=self.cues.current.followTimeString())
		else:
			self.cqt.config(text="")
			self.cqup.config(text="")
			self.cqdn.config(text="")
			self.cqf.config(text="")
		if self.cues.next != None:
			self.nx.config(text=str(self.cues.next.number))
		else:
			self.nx.config(text="")
			

#########################################
#
#	display message opens a window to display some text
#
#########################################
		
	def displayMessage(self, message, title="Message"):
		auxmaster = Tk()
		auxmaster.title(title)

		frame = Frame(auxmaster, height=530, width=530)
		frame.pack()
		frame.pack_propagate(0)
		
		scrollbar = Scrollbar(frame)
		scrollbar.pack(side=RIGHT, fill=Y)
		
		l = Text(frame, yscrollcommand=scrollbar.set)
		l.pack(side=LEFT, fill=BOTH)
		l.insert(INSERT,message)
		scrollbar.config(command=l.yview)
		
	def displayPatch(self):
		self.displayMessage(self.cues.livecue.patch.patchString(), "Patch")
		
	def displayCues(self):
		self.displayMessage(self.cues.descriptionString(), "Cues")
		
	def displayOSC(self):
		self.displayMessage(self.cues.oscString(), "OSC")
		
	def displayDimmerOptions(self):
		self.displayMessage(self.cues.livecue.patch.optionString(), "Dimmer Options")

#########################################
#
#	The channel display only shows a certain number of channels
#	at a time. 
#
#########################################

	def displayNextPage(self):
		self.chandisp.nextPage()
		self.updateDisplay()

	def displayPrevPage(self):
		self.chandisp.prevPage()
		self.updateDisplay()
		
#########################################
#
#	This is called by a change in the master fader
#
#########################################
        
	def scroll_change(self, event):
		self.cues.setMasterLevel(float(self.mfader.get()))
		self.updateOutput()
		
#########################################
#
#	This is called when a key is pressed in the command line
#
#########################################
        
	def key(self, event):
		self.external_key(event.char)
		return "break"		
		
 #########################################
#
#	This method takes a key press and interprets it based on context,
#	expanding it if it begins or ends a command
#   or substituting such as 'a' becoming '@'
#
#########################################

	def external_key(self, k):
		if len(k) == 0:
			return
		if k == "enter":
			self.read_cmd(None)
		elif ord(k) == 13:
			self.read_cmd(None)
		elif ord(k) == 127:
			self.e.delete(len(self.e.get())-1,END)
		elif ord(k) == 8:
			self.e.delete(len(self.e.get())-1,END)
		elif k == "clear":
			self.e.delete(0, END)
		elif k == "-":
			self.e.insert(END, ' ')
		elif k == "@":
			self.e.insert(END, '@')
		elif k == "a":
			self.e.insert(END, '@')
		elif k == "f":
			ce = self.e.get()
			if len(ce) > 0:
				if ce.endswith('@'):
					self.e.insert(END, '100')
				else:
					self.e.insert(END, '@100')
				self.read_cmd(None)
		elif k == "x":
			ce = self.e.get()
			if len(ce) > 0:
				if ce.endswith('@'):
					self.e.insert(END, '0')
				else:
					self.e.insert(END, '@0')
				self.read_cmd(None)
		elif k == "z":
			ce = self.e.get()
			if len(ce) > 0:
				if ce.endswith('@'):
					self.e.insert(END, '0')
				else:
					self.e.insert(END, '@0')
				self.read_cmd(None)
		elif k == "t":
			ce = self.e.get()
			if len(ce) == 0:
				self.e.insert(END, 'time ')
			else:
				if ce.startswith('time') or ce.startswith('cue') or ce.startswith('rec'):
					self.e.insert(END, ' ')
				else:
					self.e.insert(END, '>')
		elif k == "r":
			ce = self.e.get()
			if len(ce) == 0:
				self.e.insert(END, 'record ')
		elif k == "q":
			ce = self.e.get()
			if len(ce) == 0:
				self.e.insert(END, 'cue ')
		elif k == "k":
			ce = self.e.get()
			if len(ce) == 0:
				self.e.insert(END, 'delete cue ')
		elif k == "p":
			ce = self.e.get()
			if len(ce) == 0:
				self.e.insert(END, 'patch ')
		elif k == "P":
			ce = self.e.get()
			if len(ce) == 0:
				self.e.insert(END, 'dimmer_option ')
		elif k == "o":
			ce = self.e.get()
			if len(ce) == 0:
				self.e.insert(END, 'osc ')
		elif k == "]":
			ce = self.e.get()
			if len(ce) == 0:
				self.displayNextPage()
				self.e.delete(0, END)
		elif k == "[":
			ce = self.e.get()
			if len(ce) == 0:
				self.displayPrevPage()
				self.e.delete(0, END)
		else:
			self.e.insert(END, k)
			if k.isdigit():
				ce = self.e.get()
				ai = ce.find('@')
				if ai > 0 and ai == (len(ce)-3):
					self.read_cmd(None)
			
		if self.echo_osc_ip != "none":
			self.cues.oscinterface.sendOSCstring(self.echo_osc_ip,self.echo_osc_port, "/1/cmdline", self.e.get())
 
 #########################################
#
#	This is called to read the command line and process its contents
#
#########################################		
		
	def read_cmd(self, event):
		self.process_cmd(self.e.get())
		
		
 #########################################
#
#	This is the method that interprets commands entered in the command field
#	The command string is split into tokens separated by a space
#	the first token determines how the command is interpreted
#   except in the case where the command line contains '@'
#
#########################################

				
	def process_cmd(self, n):
		cp = n.split("@")
		if len(cp) == 2:
			self.process_at_cmd(cp[0], cp[1])
			self.e.delete(0,END)
			return

		cp = n.split(" ")
		self.e.delete(0,END)
		
		if n.startswith("rec"):
			self.process_rec_cmd(n, cp)
		elif n.startswith("tim"):
			self.process_time_cmd(cp)
		elif n.startswith("pat"):
			self.process_patch_cmd(cp)
		elif n.startswith("dim"):
			self.process_dimmer_cmd(cp)
		elif n.startswith("cue"):
			self.process_cue_cmd(n, cp)
		elif n.startswith("delete cue"):
			self.process_delete_cue_cmd(cp)
		elif n.startswith("osc"):
			self.process_osc_cmd(cp)
			

 #########################################
#
#	This is called when the command line contains "@"
#
#########################################
			
	def process_at_cmd(self, n, lp):
		cp = n.split(">")
		if len(cp) == 1:
			cp = n.split(",")
			if len(cp) == 1:
				self.cues.livecue.setNewLevel(cp[0], lp)
			else:
				for i in range(0, len(cp)):
					self.cues.livecue.setNewLevel(cp[i], lp)
		elif  len(cp) == 2:
			for i in range(int(cp[0]), int(cp[1])+1):
				self.cues.livecue.setNewLevel(i, lp)
		self.updateDisplay()
		
 #########################################
#
#	This is called when the command line starts with "rec"
#
#########################################
			
	def process_rec_cmd(self, n, cp):
		if  len(cp) >= 2:
			if len(cp[1]) > 0:
				recorded = self.cues.recordCueFromLive(float(cp[1]))
			else:
				recorded = self.cues.recordCueFromLive()
			if recorded == False:
				shouldreplace = tkMessageBox.askyesno("Cue Exists!", "Replace?")
				if shouldreplace == True:
					if  len(cp) == 2:
						recorded = self.cues.recordCueFromLive(float(cp[1]), 1)
					else:
						recorded = self.cues.recordCueFromLive(0,1)
			if recorded == True and len(cp) > 2:
				q = self.cues.cueForNumber(float(cp[1]))
				if q != None:
					self.cues.current = q
					nn = 'time ' + n[8+len(cp[1]):]
					self.process_cmd(nn)
		self.updateCurrent()

 #########################################
#
#	This is called when the command line starts with "tim"
#
#########################################
			
	def process_time_cmd(self, cp):
		if self.cues.current != None:
			if  len(cp) == 2 and len(cp[1]) > 0:
				self.cues.current.uptime = float(cp[1])
				self.cues.current.downtime = float(cp[1])
				self.updateCurrent()
			elif len(cp) == 3:
				self.cues.current.uptime = float(cp[1])
				self.cues.current.downtime = float(cp[2])
				self.updateCurrent()
			elif len(cp) == 4:
				self.cues.current.uptime = float(cp[1])
				self.cues.current.downtime = float(cp[2])
				self.cues.current.followtime = float(cp[3])
				self.updateCurrent()
			elif len(cp) == 5:
				self.cues.current.uptime = float(cp[1])
				self.cues.current.waituptime = float(cp[2])
				self.cues.current.downtime = float(cp[3])
				self.cues.current.waitdowntime = float(cp[4])
				self.updateCurrent()
			elif len(cp) == 6:
				self.cues.current.uptime = float(cp[1])
				self.cues.current.waituptime = float(cp[2])
				self.cues.current.downtime = float(cp[3])
				self.cues.current.waitdowntime = float(cp[4])
				self.cues.current.followtime = float(cp[5])
				self.updateCurrent()
				
 #########################################
#
#	This is called when the command line starts with "pat"
#
#########################################
			
	def process_patch_cmd(self, cp):
		if len(cp) == 3:
			self.cues.patchAddressToChannel( int(cp[1]), int(cp[2]) )
		elif len(cp) == 4:
			self.cues.patchAddressToChannel( int(cp[1]), int(cp[2]), float(cp[3]) )
		elif len(cp) == 5:
			self.cues.patchAddressToChannel( int(cp[1]), int(cp[2]), float(cp[3]), int(cp[4]) )
			#option 0=normal 1=non-dim 2=always on 3=no-master
		else:
			self.displayPatch()
		
 #########################################
#
#	This is called when the command line starts with "dim"
#
#########################################
			
	def process_dimmer_cmd(self, cp):
		if len(cp) == 3:
			self.cues.setOptionForAddress( int(cp[1]), int(cp[2]) )
		elif len(cp) == 4:
			self.cues.setOptionForAddress( int(cp[1]), int(cp[2]), int(cp[4]) )
		else:
			self.displayDimmerOptions()
			
#########################################
#
#	This is called when the command line starts with "cue"
#
#########################################
			
	def process_cue_cmd(self, n, cp):
		if len(cp) == 2:
			if len(cp[1]) > 0 and cp[1] != '?':
				q = self.cues.cueForNumber(float(cp[1]))
				if q != None:
					self.cues.current = q
					self.cues.next = q
					self.updateCurrent()
			else:
				self.displayCues()
		elif len(cp) > 2:
			q = self.cues.cueForNumber(float(cp[1]))
			if q != None:
				self.cues.current = q
				nn = 'time ' + n[5+len(cp[1]):]
				self.process_cmd(nn)
				
#########################################
#
#	This is called when the command line starts with "delete cue"
#
#########################################
			
	def process_delete_cue_cmd(self, cp):
		if len(cp) == 2:
			if len(cp[1]) > 0:
				q = self.cues.cueForNumber(float(cp[1]))
				if q != None:
					shoulddelete = tkMessageBox.askyesno("Delete Cue!", "Are you sure?")
					if shoulddelete == True:
						self.cues.removeCue(q)

#########################################
#
#	This is called when the command line starts with "osc"
#
#########################################
			
	def process_osc_cmd(self, cp):	
		if self.cues.current != None:
			if len(cp) == 2:
				if len(cp[1]) > 0 and cp[1] != '?':
					self.cues.current.oscstring = cp[1]
				elif cp[1] == '?':
					self.displayOSC()
				else:
					self.cues.current.oscstring = None
		elif cp[1] == '?':
			self.displayOSC()
	
#####################################################################################
#
#	This is the main program
#
#####################################################################################

def windowwillclose():
    app.menuQuit()

root = Tk()
root.protocol("WM_DELETE_WINDOW", windowwillclose)
app = App(root)
root.mainloop()
#root.destroy()
