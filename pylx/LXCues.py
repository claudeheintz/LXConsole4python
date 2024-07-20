#   LXCues.py
#
#   by Claude Heintz
#   copyright 2014 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html

from ArtNet import ArtNetInterface
from OSC import OSCInterface
from LXPatch import LXPatch
from LXChannelDisplay import LXChannelDisplay
import threading
import time
from operator import attrgetter

#################################################################
#
#     The LXCues class represents a list of cues.
#     Cues in the list are kept sorted by number.
#     LXCues also keeps track of a current cue 
#
#     LXCues has an LXLiveCue representing a fade-able output state
#     The livecue has an output interface and
#     a patch for translating channels to dimmers
#     livecue interface is set separately from __init__
#
#################################################################
            
class LXCues:

    def __init__(self, channels, dimmers):
        self.cues = []                          # list of cues
        self.channels = channels                    # number of channels in all cues
        self.current = None                     # the current cue
        self.next = None                        # the next cue
        self.delegate = None                        # delegate
        self.livecue = LXLiveCue(channels, dimmers) # LXLiveCue can fade between cues

        self.oscinterface = OSCInterface()
        
#####
#     cueForNumber returns a cue matching the number
#     
#####
        
    def cueForNumber(self, number):
        for cue in self.cues:
            if cue.number == float(number):
                return cue
        return None

#####
#     createCueForNumber returns a cue matching the number
#     or, if none exists, it will make one.
#     ( Note that createCueForNumber does not sort the cues after
#     making a new cue. )    
#####
        
    def createCueForNumber(self, number):
        q = self.cueForNumber(number)
        if q == None:
            q = LXCue(self.channels)
            q.number = float(number)
            self.cues.append(q)
        return q
        
#####
#     removeCue deletes the cue
#     
#####
        
    def removeCue(self, cue):
        self.cues.remove(cue)
        
#####
#     putCuesInOrder sorts the cues by number
#     
#####
    
    def putCuesInOrder(self):
        self.cues.sort(key=attrgetter('number'))

#####
#     nextCueNumber returns a number for the next cue following the end of the list
#     
#####
    
    def nextCueNumber(self):
        l = len(self.cues)
        if l > 0:
            return self.cues[l-1].number + 1.0
        return 1
        
#####
#     recordCue saves the state represented by "cue"
#     If there is no number specified, the state is copied into the current cue
#     or, a new cues is added to the end of the list
#     If a number is specified, the state is copied into that cue if it exists
#     or a cue with that number is added  
#     returns True if record was done
#     returns false if cue exists and overwrite == 0 
#####
    
    def recordCue(self, cue, number=0, overwrite=0):
        newcue = None
        if number == 0:
            if self.current != None:
                # current cue exists
                if overwrite == 1:
                    # replace
                    self.current.copyLevelsFromCue(cue)
                elif overwrite == 2:
                    # add instead
                    newcue = LXCue(self.channels, cue)
                    newcue.number = self.nextCueNumber()
                else:
                    return False
            else:
                newcue = LXCue(self.channels, cue)
                newcue.number = self.nextCueNumber()
        else:
            excue = self.cueForNumber(number)
            if excue == None:
                newcue = LXCue(self.channels, cue)
                newcue.number = number
            elif overwrite == 1:
                excue.copyLevelsFromCue(cue)
                self.current = excue
            elif overwrite == 2:
                # add instead
                newcue = LXCue(self.channels, cue)
                newcue.number = self.nextCueNumber()
            else:
                return False
        if newcue != None:
            self.cues.append(newcue)
            self.cues.sort(key=attrgetter('number'))
            self.current = newcue
        return True

#####
#     recordCueFromLive calls recordCue, passing livecue as the state to be saved
#     
#####
            
    def recordCueFromLive(self, number=0, overwrite=0):
        return self.recordCue(self.livecue, number, overwrite)
        
#####
#     asciiString returns a string representing the patch and cues
#     in the format specified by:
#     ASCII Text Representation for Lighting Console Data
#     http://old.usitt.org/documents/nf/a03asciitextreps.pdf  
#####
            
    def asciiString(self):
        s = "Ident 3:0\n"
        s += self.livecue.patch.patchString()
        s += self.livecue.patch.optionString()
        for cue in self.cues:
            s += cue.asciiString()
        s += "enddata\n"
        return s

#####
#     descriptionString returns a string representing
#     a list of the cues and their times      
#      
#####       
        
    def descriptionString(self):
        s =""
        for cue in self.cues:
            s += cue.descriptionString(",")
            s+= "\n"
        return s
        
#####
#     oscString returns a string representing
#     a list of the cues and their osc strings    
#      
#####       
        
    def oscString(self):
        s =""
        for cue in self.cues:
            os = cue.oscString();
            if os != None:
                s += os
                s+= "\n"
        return s
    
#####
#     nextCueAfterCue returns the next cue following "cue" in the cue list
#     
#####
        
    def nextCueAfterCue(self, cue):
        if cue != None:
            if cue in self.cues:
                i = self.cues.index(cue) + 1
                if i < len(self.cues):
                    return self.cues[i]
        if len(self.cues) > 0:
            return self.cues[0]
        return None

#####
#     startFadingToCue will use the live cue to start a fade to "cue"
#     or, if no cue is specified, it will start a fade to the next cue
#     after the current cue in the list    
#####
        
    def startFadingToCue(self, cue=None):
        if cue == None:
            cue = self.next
        if cue == None:
            cue = self.nextCueAfterCue(self.current)
            if cue == None:
                if len(self.cues) > 0:
                    cue = self.cues[0]
        if cue != None:
            self.livecue.startFadeToCue(cue, self)
            if cue.oscstring != None:
                self.oscinterface.sendOSCFromString(cue.oscstring);
            self.current = cue
            self.next = self.nextCueAfterCue(self.current)

#####
#     startFadeToCueNumber will use the live cue to start a fade to the cue
#     matching "number" in the cue list
#     or, if no number is specified, it will start a fade to the next cue
#     after the current cue in the list    
#####
            
    def startFadeToCueNumber(self, number=0):
        if number == 0:
            self.startFadingToCue()
        else:
            cue = self.cueForNumber(number)
            if cue != None:
                self.startFadingToCue(cue)
                
#####
#     fadeStarted() is called by the live cue at the start of fading
#     after the fade thread has been created
#####               
                
    def fadeStarted(self):
        if self.delegate != None:
            self.delegate.fadeStarted()
                
#####
#     fadeProgress() is called by the live cue during a fade
#     
#####
                
    def fadeProgress(self):
        if self.delegate != None:
            self.delegate.fadeProgress()

#####
#     fadeComplete() is called by the live cue when the fade is finished
#     
#####
                
    def fadeComplete(self):
        if self.livecue.stopped == True:
                self.next = self.current
        if self.livecue.followtime >= 0:
            self.startFadingToCue()
        else:
            self.livecue.delegate = None
            if self.delegate != None:
                self.delegate.fadeComplete()

#####
#     startLiveOutput starts the live cue's output interface sending DMX
#     
#####
                
    def startLiveOutput(self):
        if self.livecue.output:
            self.livecue.output.startSending()

#####
#     stopLiveOutput stops the live cue's output interface from sending DMX
#     
#####
        
    def stopLiveOutput(self):
        self.livecue.output.stopSending()
        
#####
#     setMasterLevel
#     
#####
        
    def setMasterLevel(self, level=100.0):
        self.livecue.master = level/100.0
        
#####
#     patchAddressToChannel calls the live cue's patchAddressToChannel method
#     
#####
        
    def patchAddressToChannel(self, address, channel, level=100, option=0):
        self.livecue.patchAddressToChannel(address, channel, level, option)
        
#####
#     setOptionForAddress calls the live cue's setOptionForAddress method
#     
#####
        
    def setOptionForAddress(self, address, option, level=-1):
        self.livecue.setOptionForAddress(address, option, level)
        
#####
#     clearPatch calls the live cue's clearPatch method
#     
#####
        
    def clearPatch(self):
        self.livecue.clearPatch()

#####
#     updateDisplay
#     
#####
        
    def updateDisplay(self, display):
        for i in range(display.beginIndex(), display.endIndex()):
            display.setLevel(i+1, int(self.livecue.livestate[i]*self.livecue.master))

#####
#     receivedOSC
#     
#####
            
    def receivedOSC(self, addressPattern, args):
        parts = addressPattern.split('/')
        if len(parts) == 4:
            if parts[2] == "dmx":
                if len(args) >= 1:
                    dim = int(parts[1])*512 + int(parts[3]) + 1
                    self.livecue.setDimmerLevel(dim, args[0]*100)
                    self.delegate.updateDisplay()
                return
            if parts[1] == "cue":
                if parts[3] == "start":
                    q = self.cueForNumber(parts[2])
                    if q != None:
                        self.startFadingToCue(q)
        elif len(parts) == 3:
            if parts[1] == "cmd.lxconsole":
                if (self.delegate != None) and (args[0] > 0 ):
                    if parts[2] == "GO":
                        self.delegate.go_cmd()
                        return
                    if parts[2] == "STOP":
                        self.delegate.stop_cmd()
                        return
                    if parts[2] == "BACK":
                        self.delegate.back_cmd()
                        return
                    self.delegate.external_cmd(parts[2], args[0])
                    return;
            if parts[1] == "key.lxconsole":
                if (self.delegate != None) and (args[0] > 0 ):
                    self.delegate.external_key(parts[2])
                    
        

#################################################################
#
#     The LXCue class represents an output state.
#     It keeps the state in a list of floating point values
#     LXCue also contains times for fading into the output state
#
#################################################################

class LXCue:
    
    def __init__(self, channels, cue=None):
        self.number = 0                 # cue number determines order of playback
        self.uptime = 5                 # time for fade of increasing levels
        self.downtime = 5               # time for fade of decreasing levels
        self.waituptime = 0             # wait time for increasing levels
        self.waitdowntime = 0           # wait time for decreasing levels
        self.followtime = -1            # time for followon (-1 is no follow)
        self.oscstring = None;
        
        if  cue == None:
            self.livestate = []         # list of floating point levels
            for i in range(channels):
                self.livestate.append(0.0)
        else:
            self.copyLevelsFromCue(cue)

#####
#     copyLevelsFromCue copies the levels from another cue's livestate
#####
                
    def copyLevelsFromCue(self, cue):
        self.livestate = []
        for i in range(len(cue.livestate)):
            self.livestate.append(cue.livestate[i])

#####
#     setNewLevel sets a level of a channel in the livestate
#     (the channel number is converted into a list index by subtracting 1)
#####
            
    def setNewLevel(self, channel, level):
        self.livestate[int(channel)-1] = float(level)
        
    def getLevel(self, channel):
    	return self.livestate[int(channel)-1]
        
#####
#     setDimmerLevel sets a level of a channel in the livestate
#     (the channel number is converted into a list index by subtracting 1)
#####
            
    def setDimmerLevel(self, dimmer, level):
        channel = self.patch.channelForDimmer(dimmer)
        if channel > 0:
            self.setNewLevel(channel,level)
        
#####
#     titleString returns a cue number text
#####
            
    def titleString(self):
        return "Cue " + str(self.number)
        
        
#####
#     upTimeString returns up time text
#####
            
    def upTimeString(self):
        if self.waituptime > 0:
            return "Up: " + str(self.uptime) + " wait: " + str(self.waituptime)
        return "Up: " + str(self.uptime)

#####
#     downTimeString returns down time text
#####
            
    def downTimeString(self):
        if self.waitdowntime > 0:
            return "Down: " + str(self.downtime) + " wait: " + str(self.waitdowntime)
        return "Down: " + str(self.downtime)        

#####
#     followTimeString returns follow time text
#####
            
    def followTimeString(self):
        if self.followtime > 0:
            return "Follow: " + str(self.followtime)
        return ""
        
#####
#     descriptionString returns a string 
#####
            
    def descriptionString(self, sep):
        s = "Cue " + str(self.number) + sep
        if self.waituptime > 0:
            s = s + "Up " + str(self.uptime) + " " + str(self.waituptime) + sep
        else:
            s = s + "Up " + str(self.uptime) + sep
        if self.waitdowntime > 0:
            s = s + "Down " + str(self.downtime) + " " + str(self.waitdowntime)
        else:
            s = s + "Down " + str(self.downtime)
        if self.followtime >= 0:
            s = s + sep + "Followon " + str(self.followtime)
        return s
        
#####
#     asciiToString returns a string representing the cue
#     in the format specified by:
#     ASCII Text Representation for Lighting Console Data
#     http://old.usitt.org/documents/nf/a03asciitextreps.pdf  
#####
            
    def asciiString(self):
        s = self.descriptionString("\n") + "\n"
        s = s + self.levelsString()
        if self.oscstring != None:
            s = s + "$$OSCstring " + self.oscstring + "\n"
        return s
        
#####
#     levelsString returns a string with just the cue's level data in ascii format
#     
#####
            
    def levelsString(self):
        tc = 0
        s = ""
        for i in range(len(self.livestate)):
            if self.livestate[i] > 0:
                if tc == 0:
                    s = s + "Chan " + str(i+1) +"@"+str(int(self.livestate[i]))
                    tc = 1;
                else:
                    s = s + " " + str(i+1) +"@"+str(int(self.livestate[i]))
                    tc += 1
                    if tc > 6:
                        s += "\n"
                        tc = 0
        if tc > 0:
            s += "\n"
        return s
        
#####
#     oscString returns a the OSCstring or None
#####
            
    def oscString(self):
        if self.oscstring != None:
            return "Cue " + str(self.number) + " " + self.oscstring
        return None 

#################################################################
#
#     the LXLiveCue class is an LXCue that can fade from one state to another
#
#################################################################   
            
class LXLiveCue (LXCue):
    
    def __init__(self, channels, addresses):
        LXCue.__init__(self, channels)
        self.initialstate = []      # list of floating point levels at start of fade
        self.deltastate = []        # list of difference in level for fade
        for i in range(channels):
            self.deltastate.append(0.0)
            self.initialstate.append(0.0)
        
        self.output = None          # should be set to instance of ArtNetInterface
        self.fading = False         # flag which causes fade loop to repeat until done
        self.fade_thread = None     # thread for running fade() loop
        self.delegate = None        # object to inform when fade is complete
        self.master = 1.0           # master level for output
        self.stopped = False
        
        self.patch = LXPatch(channels, addresses)
        self.output = None

        
#####           
#     the normalizeValue utility insures output buffer will only be set to 0-255
#####
            
    def normalizeValue(self, value):
        if value < 0:
            return 0
        if value > 255:
            return 255
        return int(value)

#####       
#     writeToInterface() copies values from floating point list
#     to buffer and sends them to the output interface
#     here is where the patch translates channels to addresses
#####
    
    def writeToInterface(self):
        if self.output:
            try:
                buffer = self.patch.byteArrayFromFloatList(self.livestate, self.master)
                self.output.setDMXValues(buffer)    # dmx 0-255 levels written to self.output
                self.output.sendDMXNow()
            except:
                print ("Could not write to DMX output")

#####       
#     prepareFade() sets the initialstate and deltastate lists
#     this means that calculating the livestate during the fade 
#     is simply initial + delta * fade_progress
#     when progress is 0.0, live is initialstate
#     when progress is 1.0, live is newstate
#####
        
    def prepareFade(self, cue, delegate=None):
        self.delegate = delegate
        self.number = cue.number
        self.uptime = cue.uptime
        self.downtime = cue.downtime
        self.waituptime = cue.waituptime
        self.waitdowntime = cue.waitdowntime
        self.followtime = cue.followtime
        for i in range(len(self.livestate)-1):
            self.deltastate[i] = cue.livestate[i] - self.livestate[i]
            self.initialstate[i] = self.livestate[i]

#####           
#     fade() should be called on a separate thread after prepareFade()
#     
#     Each pass through the fade loop, a new live state is calculated.
#     The progress of the fade (0.0 to 1.0) is determined by
#     dividing the elapsed time by the fade time
#     separate progress is calculated for channels that are increasing (uptime)
#     and channels that are decreasing (downtime)
#     then the new live state is calculated as initial + delta * fade_progress
#     this is also multiplied by the master level (0.0-1.0) before
#     the new live state is written to the interface
#     the loop continues while the elapsed time is less than both the up and down times
#####
            
    def fade(self):
        starttime = time.time();
        etime = 0;
        while self.fading:
            etime = time.time()-starttime
            if etime - self.waituptime > 0:
                if self.uptime > 0:
                    upprogress = (etime - self.waituptime)/self.uptime
                    if upprogress > 1.0:
                        upprogress = 1.0
                else:
                    upprogress = 1.0
            else:
                upprogress = 0.0
            if etime - self.waitdowntime > 0:
                if self.downtime > 0:
                    downprogress = (etime - self.waitdowntime)/self.downtime
                    if downprogress > 1.0:
                        downprogress = 1.0
                else:
                    downprogress = 1.0
            else:
                downprogress = 0.0
                
            for i in range(len(self.livestate)-1):
                if self.deltastate[i] > 0:
                    self.livestate[i] = (self.initialstate[i] + upprogress * self.deltastate[i])
                else:
                    self.livestate[i] = (self.initialstate[i] + downprogress * self.deltastate[i])
            self.writeToInterface()
            if self.delegate != None:
                self.delegate.fadeProgress()
            
            self.fading = ((etime - self.waituptime) < self.uptime) or ((etime - self.waitdowntime) < self.downtime)
            if self.followtime >= 0:
                self.fading = self.fading and  ( etime < self.followtime )
            if self.fading:
                time.sleep(0.025)   #max 40 times per sec for DMX
                
        self.fade_thread = None
        if self.delegate != None:
            self.delegate.fadeComplete()        # may start another fade if followtime

#####       
#     startFading() creates a new thread which will loop until the fade is finished
#     Or, until self.fading is set to false
#####
        
    def startFading(self):
        self.fading = True;
        if self.fade_thread is None:
            self.fade_thread = threading.Thread(target=self.fade)
            self.fade_thread.daemon = True
            self.fade_thread.start()
        if self.delegate != None:
            self.delegate.fadeStarted()

#####   
#     stopFading() sets the fading flag to false and waits for the 
#     fade loop to exit and the current fade thread to end
#####
    
    def stopFading(self):
        while self.fade_thread != None:
            self.fading = False
            
######      
#     startFadeToCue() stops the current fade (if necessary)
#     it prepares for the fade using the cue's livestate and
#     cue times and then starts the fade
#####
            
    def startFadeToCue(self, cue, delegate=None):
        if self.fading:
            self.delegate = None
            self.stopFading()
        self.prepareFade(cue, delegate)
        self.stopped = False
        self.startFading()

#####   
#     setMaster(level) converts a percentage 0-100 into the master 0.0-1.0 for
#     faster multiplication in the fade loop
#####
        
    def setMaster(self, level):
        self.master = level / 100.0

#####       
#     setNewLevel() changes the level of a channel in the livestate
#     or, if fading, it modifies the fade so that the channel remains at the new level
#####
            
    def setNewLevel(self, channel, level):
        if not self.fading:
            self.livestate[int(channel)-1] = float(level)
            self.writeToInterface()
        else:
            self.deltastate[int(channel)-1] = 0                 # stop changing
            self.initialstate[int(channel)-1] = float(level)    # set new state on the
                                                                # next pass through loop
            
#####
#     patchAddressToChannel calls the patch's patchAddressToChannel method
#     
#####
            
    def patchAddressToChannel(self, address, channel, level=100, option=0):
        self.patch.patchAddressToChannel(address, channel, level/100.0, option)
        
#####
#     setOptionForAddress calls the patch's setOptionForAddress method
#     
#####
        
    def setOptionForAddress(self, address, option, level=-1):
        self.patch.setOptionForAddress(address, option, level)

#####
#     clearPatch calls the patch's unpatchAll method
#     
#####
        
    def clearPatch(self):
        self.patch.unpatchAll()