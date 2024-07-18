#   ArtNet.py
#
#   by Claude Heintz
#   copyright 2014-2024 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html
#
#   Art-Net(TM) Designed by and Copyright Artistic Licence Holdings Ltd.


import socket
import threading
import time
import ipaddress
from select import select
from CTNetUtil import CTNetUtil

##################################################################################
#                               DMXInterface
#
#           An abstract super class for DMX over network protocols
#
##################################################################################

class DMXInterface(object):
    
    def __init__(self):
        self.send_thread = None
        self.listen_thread = None
        self.lock = threading.Lock()
        self.last_send_time = 0.0
        self.ok = False

########################################
#
#   port   OVERRIDE THIS METHOD
#      port for sending and receiving UPD DMX packets
#
#########################################
    def port(self):
        return 0

#########################################
#
#   setDMXValue   OVERRIDE THIS METHOD
#      set a single slot in the DMX output stream
#
#########################################
    def setDMXValue(self, address, value):
        print ("SetDMXValue")

#########################################
#
#   setDMXValues   OVERRIDE THIS METHOD
#      set values for all DMX slots
#
#########################################
    def setDMXValues(self, values):
        print ("setDMXValues")
        self.sending = False

########################################
#
#   startSending
#      creates a thread that sends UDP DMX packets
#
#########################################
    def startSending(self):
        self.sending = True
        if self.send_thread is None:
            self.send_thread = threading.Thread(target=self.send)
            self.send_thread.daemon = True
            self.send_thread.start()

########################################
#
#   send
#      method to be attached to a thread (don't call directly)
#      periodically calls sendDMXNow,
#      you can call sendDMXNow directly to force an immediate update
#
#########################################
    def send(self):
        while self.sending:
            st = time.time() - self.last_send_time
            if  st >= 2:
                try:
                    self.sendDMXNow()
                except:
                    self.sending = False
            else:
                time.sleep(2-st)
        self.send_thread = None
        self.sending = False

#########################################
#
#   sendDMXNow   OVERRIDE THIS METHOD
#      sends a packet containing DMX data
#
#########################################
    def sendDMXNow(self):
        print ("sendDMXNow")

#########################################
#
#   stopSending
#      ends the sending thread by setting a flag
#
#########################################
    def stopSending(self):
        while self.send_thread != None:
            self.sending = False

#########################################
#
#   close
#      stops sending and listening
#
#########################################
    def close(self):
        self.stopSending()
        self.stopListening()
        self.udpsocket.close()

#########################################
#
#   startListening creates a thread that runs the listen() method
#
#########################################
    
    def startListening(self):
        self.listening = True
        if ( self.listen_thread is None ):
            self.listen_thread = threading.Thread(target=self.listen)
            self.listen_thread.daemon = True
            self.listen_thread.start()

#########################################
#
#   stopListening sets a flag which will cause the listen loop to end on the next pass
#   setting the delegate to None prevents messages from being sent after stopListening
#   is called.
#
#########################################
    def stopListening(self):
        self.delegate = None
        self.listening = False
        
#########################################
#
#   listen contains a loop that runs while the self.listening flag is True
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
                with self.lock:
                    self.data, self.recdaddr = self.udpsocket.recvfrom(256)
                self.packetReceived()
            else:
                time.sleep(0.1)
        self.listen_thread = None

#########################################
#
#   packetReceived   OVERRIDE THIS METHOD
#
#########################################
    
    def packetReceived(self):
        print ( self.data )

##################################################################################
#                               ArtNetInterface
#
#           Implements Art-Net output
#
##################################################################################

class ArtNetInterface(DMXInterface):

########################################
#
#   init requires broadcast ip address
#   and local interface's ip address
#
#########################################

    def __init__(self, iface_ip, target_ip = None, net=0, subnet=0, univ=0):
        super().__init__()
        self.seqcounter = 0
        self.prcounter = 0
        self.target_list = []
        self.localip = iface_ip
        self.unicast_ip = target_ip
        self.loopback = "127.0.0.1"
        self.last_poll_time = 0.0
        self.namebytes = bytes("LXWeb2DMX", 'utf-8')
        
        self.setArtnetNet(net)
        self.setArtnetSubnet(subnet)
        self.setArtnetUniverse(univ)
        
        self.setupSocket()
        self.setupSendBuffer()
        self.setupArtPollBuffer()
        self.setupArtPollReplyBuffer()
        
        self.startListening()

########################################
#
#   port   ARTNET_PORT = 0x1936
#
#########################################
    def port(self):
        return 0x1936

    def setArtnetNet(self, n):
        self.artnet_net = 0x7F & n

    def setArtnetSubnet(self, sn):
        self.artnet_subnet = 0x0F & sn

    def setArtnetUniverse(self, u):
        self.artnet_universe = 0x07 & u

########################################
#
#   setupSocket and options
#   bind to any interface and Art-Net port
#
#########################################
    def setupSocket(self):
         try:
            self.udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.udpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self.udpsocket.bind(("0.0.0.0",self.port()))
            
            self.udpsocket.setblocking(False)
            self.udpsocket.settimeout(1)
            self.ok = True
         except Exception as e:
            print ("Socket Error ", e)

########################################
#
#   setupSendBuffer
#   pre-fill header info for sending DMX packets
#   send_buffer also holds DMX data for output
#
#########################################
    def setupSendBuffer(self):
        self.send_buffer = bytearray(529)
        try:
            self.send_buffer[0:6] = "Art-Net"
        except:
            self.send_buffer[0:6] = bytes("Art-Net", 'utf-8')
            #python 3
        self.send_buffer[7] = 0
        self.send_buffer[8] = 0      #opcode l/h
        self.send_buffer[9] = 0x50
        self.send_buffer[10] = 0     #version h/l
        self.send_buffer[11] = 14
        self.send_buffer[12] = 0     #sequence
        self.send_buffer[13] = 0     #physical
        self.send_buffer[14] = self.artnet_net # 7bits
        self.send_buffer[15] = self.artnet_universe | (self.artnet_subnet << 4)  #subnet upper 4 bits - universe lower 4 bits
        self.send_buffer[16] = 2     #dmxcount h/l
        self.send_buffer[17] = 0
        for i in range(512):
            self.send_buffer[i+18] = 0

########################################
#
#   setupArtPollBuffer
#   pre-fill ArtPoll packet
#
#########################################
    def setupArtPollBuffer(self):
        self.artpoll_buffer = bytearray(14)
        try:
            self.artpoll_buffer[0:6] = "Art-Net"
        except:
            self.artpoll_buffer[0:6] = bytes("Art-Net", 'utf-8')
            #python 3
        self.artpoll_buffer[7] = 0
        self.artpoll_buffer[8] = 0      #opcode l/h
        self.artpoll_buffer[9] = 0x20
        self.artpoll_buffer[10] = 0     #version h/l
        self.artpoll_buffer[11] = 14
        self.artpoll_buffer[12] = 6     #talk to me
        self.artpoll_buffer[13] = 0

########################################
#
#   setupArtPollReplyBuffer
#   pre-fill ArtPollReply packet
#
#########################################
    def setupArtPollReplyBuffer(self):
        self.pollreply_buffer = bytearray(240)
        for i in range(240):
            self.pollreply_buffer[i] = 0
        try:
            self.pollreply_buffer[0:6] = "Art-Net"
        except:
            self.pollreply_buffer[0:6] = bytes("Art-Net", 'utf-8')
            #python 3
        self.pollreply_buffer[7] = 0
        self.pollreply_buffer[8] = 0      #opcode l/h
        self.pollreply_buffer[9] = 0x21
        iparr = self.localip.split(".")
        self.pollreply_buffer[10] = int(iparr[0])     # 10-13 IP Address 
        self.pollreply_buffer[11] = int(iparr[1])
        self.pollreply_buffer[12] = int(iparr[2])
        self.pollreply_buffer[13] = int(iparr[3])
        self.pollreply_buffer[14] = 0x36            #port 0x1936 l/h
        self.pollreply_buffer[15] = 0x19
        self.pollreply_buffer[16] = 0               #firmware h/l
        self.pollreply_buffer[17] = 0
        self.pollreply_buffer[18] = self.artnet_net              #net, subnet
        self.pollreply_buffer[19] = self.artnet_subnet
        self.pollreply_buffer[20] = 0x12            #Artistic License LXConsole Code
        self.pollreply_buffer[21] = 0x50
        self.pollreply_buffer[22] = 0               #ubea bios firmware version
        self.pollreply_buffer[23] = 0x10            # status
        self.pollreply_buffer[24] = 0x78            #Esta Mfg Code
        self.pollreply_buffer[25] = 0x6C
        self.pollreply_buffer[26:35] = self.namebytes  #short name
        self.pollreply_buffer[44:52] = self.namebytes  #long name
        self.updatePollReplyCounter()
        self.pollreply_buffer[173] = 1  #number of ports
        self.pollreply_buffer[174] = 0x40  #port 1 to network (|| 0x08 from network)
        self.pollreply_buffer[178] = 128   #port 1 good
        self.pollreply_buffer[186] = self.artnet_universe 
        self.pollreply_buffer[200] = 1  # controller

    def startSending(self):
        self.sendArtPoll()
        super().startSending()
########################################
#
#   send
#   override of send() to also periodically send Art-Net polls for device discovery
#
#########################################
    def send(self):
        while self.sending:
            st = time.time() - self.last_send_time
            if  st >= 2:
                try:
                    self.sendDMXNow()
                except:
                    self.sending = False
            else:
                pt = time.time() - self.last_poll_time
                if  pt >= 4:
                    self.removeExpiredTargets()
                    self.sendArtPoll()
                    self.last_poll_time = time.time()
                else:
                    time.sleep(2-st)
        self.send_thread = None
        self.sending = False

########################################
#
#   updateCounter
#   increment packet sequence counter
#
#########################################
    def updateCounter(self):
        self.seqcounter += 1
        if self.seqcounter > 255:
            self.seqcounter = 0
        self.send_buffer[12] = self.seqcounter

########################################
#
#   sendDMXNow
#   updates the counter and sends ArtDMX packet
#
#########################################
    def sendDMXNow(self):
        self.updateCounter()
        with self.lock:
            if ( self.unicast_ip == None ):
                for n in self.target_list:
                    self.udpsocket.sendto(self.send_buffer, (n.address, self.port()))
            else:
                self.udpsocket.sendto(self.send_buffer, ( self.unicast_ip, self.port()))
        self.last_send_time = time.time()

########################################
#
#   setDMXValue sets slot directly in DMX packet buffer
#
#########################################
    def setDMXValue(self, address, value):
        with self.lock:
            self.send_buffer[address+17] = value

########################################
#
#   setDMXValues sets slots directly in DMX packet buffer
#
#########################################
    def setDMXValues(self, values):
        with self.lock:
            for i in range (len(values)):
                self.send_buffer[18+i] = values[i]

########################################
#
#   test to see if received address matches loopback or stored local address
#
#########################################
    def recd_from_local(self):
        if ( self.recdaddr[0] != self.loopback ):
            if ( self.recdaddr[0] != self.localip ):
                return 0
        return 1

########################################
#
#   packetReceived called when listen() thread receives data received at Art-Net port
#
#########################################
    def packetReceived(self):
        if ( self.data[0:7] == bytes("Art-Net", 'utf-8')):
            opcode =  self.data[8] + 256 * self.data[9]
            if ( opcode == 0x5000 ):
                self.artDMXReceived()
            elif ( opcode == 0x2000 ):
                self.sendArtPollReply()
            elif ( opcode == 0x2100 ):
                self.artPollReplyReceived()
            else:
                print ( "unsupported opcode ", opcode )

########################################
#
#   sendArtPoll called periodically from send() method/thread
#
#########################################
    def sendArtPoll(self):
        with self.lock:
            self.udpsocket.sendto(self.artpoll_buffer, ("255.255.255.255", self.port()))
        self.last_poll_time = time.time()

########################################
#
#   update Poll Reply Counter
#
#########################################
    def updatePollReplyCounter(self): 
        self.prcounter += 1
        if self.prcounter > 9999:
            self.prcounter = 0
        for i in range(30):
            self.pollreply_buffer[i+108] = 0
        status = "#0001 [" + str(self.prcounter) + "] LXWeb2DMX OK " 
        self.pollreply_buffer[108:108+len(status)] = bytes(status, 'utf-8')  #long name

########################################
#
#   replyMatchesNetwork
#      returns 1 if poll reply matches one port's 
#      output from network universe to self.artnet_universe
#
#########################################
    def replyMatchesNetwork(self):
        if ( (self.data[174] & 0x80) != 0 ):    #node's port 1 can output from network
            if ( self.data[190] == self.artnet_universe ):
                return 1
        elif ( (self.data[175] & 0x80) != 0 ):
            if ( self.data[191] == self.artnet_universe ):
                return 1
        elif ( (self.data[176] & 0x80) != 0 ):
            if ( self.data[192] == self.artnet_universe ):
                return 1
        elif ( (self.data[177] & 0x80) != 0 ):
            if ( self.data[193] == self.artnet_universe ):
                return 1
        return 0

########################################
#
#   sendArtPollReply ->send reply to Art-Net poll
#   reply to broadcast address of ArtPoll sender
#
#########################################
    def sendArtPollReply(self):
        self.updatePollReplyCounter()
        netbroadcastip = CTNetUtil.findBroadcastAddress(self.recdaddr[0])
        with self.lock:
            self.udpsocket.sendto(self.pollreply_buffer, (netbroadcastip, self.port()))

########################################
#
#   artPollReplyReceived-> if poll matches out output, set target ip address for ArtDMX
#
#########################################
    def artPollReplyReceived(self):
        if ( self.data[26:35] != self.namebytes ):
            if ( self.data[18] == self.artnet_net ):  # matches net, subnet
                if ( self.data[19] == self.artnet_subnet ):
                    if ( self.replyMatchesNetwork() == 1 ):
                        self.foundNode(self.recdaddr[0])

########################################
#
#   artDMXReceived
#
#########################################
    def artDMXReceived(self):
        if ( self.recd_from_local() == 0 ):
            print (" Art DMX ", self.recdaddr[0])

########################################
#
#   foundNode
#      append to target list, remove broadcast ip 
#      if node previously found, update polltime
#
#########################################
    def foundNode( self, ipaddr ):
        x = self.targetWithAddress(ipaddr)
        if ( x == None ):
            self.target_list.append(ArtNetNode(ipaddr))
            print( "added node: ", ipaddr )
        else:
            x.pollReceived()

    def targetWithAddress(self, ipaddr):
        for n in self.target_list:
            if ( n.address == ipaddr ):
                return n
        return None

    def removeExpiredTargets(self):
        expired = []
        for n in self.target_list:
            if ( n.expired() == 1 ):
                expired.append(n)
        for n in expired:
            self.target_list.remove(n)
            print("removed node with address ", n.address)

##################################################################################
#                               ArtNetNode
#
#           encapsulates artnet node's ipaddress from ArtPoll and the time it last polled
#
##################################################################################
class ArtNetNode(object):

    def __init__(self, ipaddr):
        self.address = ipaddr
        self.polltime = time.time()
    
    def pollReceived(self):
        self.polltime = time.time()
        
    def expired(self):
        if ( time.time()-self.polltime > 12 ):
            return 1
        return 0