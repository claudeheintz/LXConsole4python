#   CTNetUtil.py
#
#   by Claude Heintz
#   copyright 2024 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html
#



import socket
import ipaddress


##################################################################################
#                               CTNetUtil
#
#           Utility class for network support
#
##################################################################################

class CTNetUtil(object):

#########################################
#
#   get_ip_address
#   creates an internet family socket and reads address returned by getsockname()
#   returns localhost if this fails
#
#######################################
    def get_ip_address():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # doesn't even have to be reachable, but throws an error if port 0
            s.connect(('10.254.254.254',80))
            addr = s.getsockname()[0]
        except Exception as e:
            print ( "get_ip_address error: ", e )
            addr = '127.0.0.1'
        finally:
            s.close()
        return addr

#########################################
#
#   getClassOfIPAddress
#   takes integer from first octet of ipv4 address
#   returns class a=1, class b=2, class c=3 or other class=0
#
#######################################
    def getClassOfIPAddress(a):
        if  (( a > 0 ) and  ( a < 127 )):
            return 1
        if  (( a > 127 ) and  ( a < 192 )):
            return 2
        if  (( a > 191 ) and  ( a < 224 )):
            return 3
        return 0

#########################################
#
#   findBroadcastAddress
#   returns third command line argument
#   OR, value from properties file
#       if "auto" returns broadcast address based on
#       the network portion of available interface address (belonging to internet family)
#       as determined by that address's class
#
#######################################

    def findBroadcastAddress(ipaddress):
        octets = ipaddress.split(".")
        ipclass = CTNetUtil.getClassOfIPAddress(int(octets[0]))
        if ( ipclass == 1 ):
            return octets[0] + ".255.255.255"
        if ( ipclass == 2 ):
            return octets[0] + "." + octets[1] + ".255.255"
        if ( ipclass == 3 ):
            return octets[0] + "." + octets[1] + "." + octets[2] + ".255"
            #default to broadcast to all networks
        return "255.255.255.255"