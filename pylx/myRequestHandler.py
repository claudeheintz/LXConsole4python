#   myRequestHandler.py
#
#	by Claude Heintz
#	copyright 2024 by Claude Heintz Design
#
#  see license included with this distribution or
#  https://www.claudeheintzdesign.com/lx/opensource.html
#

from http.server import BaseHTTPRequestHandler

#################################################################
#
#   myRequestHandler extends BaseHTTPRequestHandler to handle GET requests
#      when a GET request is received, calls class variable owner's doGet method
#      owner's doGet should callback to myRequestHandler's respond method
#      if the respond method receives status code 200, OK,
#      it returns a stream for writing content
#
#########################################
class myRequestHandler(BaseHTTPRequestHandler):

#########################################
#   setOwner->owner object to process results of requests
#      owner is class variable
#      owner must respond to doGet(self, f(file stream), p(resource path), q(query))
#########################################
    @classmethod
    def setOwner(cls, owner):
        cls.owner = owner

#########################################
#
#   writeHTMLHeader
#
#########################################
    def writeHTMLHeader(self, t):
        self.wfile.write(bytes("<html><head><title>%s</title></head>"% t, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))

#########################################
#
#   endHTMLBody
#
#########################################
    def endHTMLBody(self):
        self.wfile.write(bytes("</body></html>", "utf-8"))

#########################################
#
#   respond sends status code
#       returns stream for writing content if status code == OK
#
#########################################
    def respond(self, code):
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        if ( code == 200 ):
            return self.wfile
        else:
            self.writeHTMLHeader("bad request")
            self.wfile.write(bytes("<h3>Bad Request</h3>", "utf-8"))
            self.endHTMLBody()
            return None

#########################################
#
#   override of do_GET
#      handles get requests
#      owner should callback to respond(code) from its doGet method
#      if code is 200, OK, respond returns a stream for writing content
#
#########################################
    def do_GET(self):
        p = self.path.split("?")
        if ( len(p) == 2 ):
            self.owner.doGet(self, p[0], p[1])
        else:
            self.owner.doGet(self, p[0], None)
