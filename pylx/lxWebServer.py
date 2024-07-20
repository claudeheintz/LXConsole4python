#   lxWebServer.py
#
#   by Claude Heintz
#   copyright 2024 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html
#

from http.server import HTTPServer
from myRequestHandler import myRequestHandler
import threading

#################################################################
#
#   lxWebServer
#   myRequestHandler extends BaseHTTPRequestHandler to handle GET requests
#      specifically get request urls of the form 'http://address:port/?query'
#      when a recognized query is received, passes it to class's 'owner' object.
#   
#   URL address:port/?setAxV  (example 10.110.111.4:/?set10x35, 10@35%)
#      sets address A at percentage V
#      multiple AxV pairs can be added, separated by underscores
#      (example example 10.110.111.4:/?set10x35_20x45, 10@35% and 20@45%)
#
#########################################
class lxWebServer:

    def __init__(self, owner, host, port):
        self.owner = owner
        self.hostname = host
        self.serverport = port
        self.createWebServer(self.hostname, self.serverport)



#########################################
#
#   createWebServer makes web server object
#   uses myRequestHandler class calls back with requests
#
#########################################
    def createWebServer(self, hostname, serverport):
        self.web_server = HTTPServer((hostname, serverport), myRequestHandler)
        myRequestHandler.setOwner(self)

#########################################
#
#   runWebServer
#      serve_forever BLOCKS until KeyboardInterrupt throws an exception
#
#########################################
    def runWebServer(self):
        serve_thread = threading.Thread(target=self.do_run_web_server)
        serve_thread.daemon = True
        serve_thread.start()

    def do_run_web_server(self):
        print("Starting web server http://%s:%s" % (self.hostname, self.serverport))
        try:
            self.web_server.serve_forever()
        except KeyboardInterrupt:
            pass

#########################################
#
#   closeWebServer
#
#########################################
    def closeWebServer(self):
        self.web_server.shutdown()
        self.web_server.server_close()
        print("Web server stopped.")

#########################################
#
#   doGet (myRequestHandler owner method)
#      called in response to a GET request
#       rh request handler for sending response
#       p path to resource
#       q query
#
#########################################
    def doGet(self, rh, p, q):
        if ( p == "/" ):
            wfile = rh.respond(200)
            rh.writeHTMLHeader("pylx")
            if ( q != None ):
                self.do_query(wfile, q)
            self.owner.query_complete( wfile )
            rh.endHTMLBody()
        else:
            rh.respond(400)
#########################################
#
#   do_QUERY processes query portion of url from a get request
#      does nothing if query is not handled
#
#########################################
    def do_query(self, f, query):
        qpts = query.split("&")
        if (len(qpts) > 0):
            for q in qpts:
                qt = q.split("=")
                if ( len(qt) == 2):
                    if ( qt[0].lower() == "set"):
                        self.do_set_query(f, qt[1])
                    elif ( qt[0].lower() == "setl"):
                        self.do_setl_query(f, qt[1])
                    elif ( qt[0].lower() == "cmd"):
                        self.do_cmd_query(f, qt[1])

#########################################
#
#   do_setl_query->splits query on the right of 'setl='
#      into address and value sequence, AxV1_V2_V3...
#      sends owner a do_set message for each 
#
#########################################
    def do_setl_query(self, f, sv ):
        spts = sv.split("x")
        if ( len(spts) == 2 ):
            addr = int(spts[0])
            varr = spts[1].split("_")
            for v in varr:
                self.owner.do_set( f, addr, v)
                addr = addr + 1

    def do_cmd_query(self, f, cmd):
        from urllib.parse import unquote
        dcmd = unquote(cmd)
        self.owner.do_web_cmd(f, dcmd)

#########################################
#
#   do_set_query->splits query on the right of 'set='into address value pairs
#      sends owner a do_set message for each 
#
#########################################
    def do_set_query(self, f, sv ):
        spts = sv.split("_")
        for sp in spts:
            scv = sp.split("x")
            if ( len(scv) == 2 ):
                self.owner.do_set( f, scv[0], scv[1])
                self.owner.query_complete( f )
