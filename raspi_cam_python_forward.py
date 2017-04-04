#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process, Value
import ctypes, httplib, time, os

HTTP_PORT = 8000
CAMERA_PORT = 8080
CAMERA_IP = "192.168.1.13"

timelapse_running = Value(ctypes.c_bool, False)

class myHandler(BaseHTTPRequestHandler):
	
	def do_GET(self):
		
		if self.path=="/":
			f = open('views/view.html',"rb")
			self.send_response(200)
			self.end_headers()
			self.wfile.write(f.read())
			f.close()

if __name__ == '__main__':
	server = HTTPServer(('', HTTP_PORT), myHandler)
	print 'RaspiCam forward running'
		
	server.serve_forever()
