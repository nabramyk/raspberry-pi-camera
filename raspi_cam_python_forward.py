#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process, Value
import ctypes, httplib, time, os

HTTP_PORT = 8000
CAMERA_PORT = 8080
CAMERA_IP = "192.168.1.13"

timelapse_running = Value(ctypes.c_bool, False)

def interval_of_image_pulls(timelapse_running):
	
	while timelapse_running.value:
		path = os.getcwd() + "/images/" + time.strftime('%Y.%m.%d') + "/"
		if not os.path.exists(path):
			os.makedirs(path)
		conn = httplib.HTTPConnection(CAMERA_IP, CAMERA_PORT)
		conn.request("GET", "/timelapse/download/")
		image_data = conn.getresponse().read()
		if not len(image_data)==0:
			f = open(path + time.strftime('%H:%M:%S') + '.jpg', 'a+')
			f.write(image_data)
			f.close()
		time.sleep(1)

class myHandler(BaseHTTPRequestHandler):
	
	def do_GET(self):
		
		global timelapse_running
		
		if self.path=="/snapshot/":
			self.send_response(200)
			self.end_headers()
			conn = httplib.HTTPConnection(CAMERA_IP, CAMERA_PORT)
			conn.request("GET", "/image/")
			self.wfile.write(conn.getresponse().read())
			conn.close()
		
		if self.path=="/timelapse/start/":
			timelapse_running.value = True
			self.send_response(200)
			self.end_headers()
			conn = httplib.HTTPConnection(CAMERA_IP, CAMERA_PORT)
			conn.request("POST", "/timelapse/start/")
			conn.getresponse()
			conn.close()
			p = Process(target=interval_of_image_pulls,args=(timelapse_running,)).start()
			
		if self.path=="/timelapse/stop/":
			timelapse_running.value = False
			self.send_response(200)
			self.end_headers()
		
		if self.path=="/temperature/":
			self.send_response(200)
			self.end_headers()
			conn = httplib.HTTPConnection(CAMERA_IP, CAMERA_PORT)
			conn.request("GET", "/temperature/")
			print conn.getresponse().read()
			conn.close()
			return

if __name__ == '__main__':
	server = HTTPServer(('', HTTP_PORT), myHandler)
	print 'RaspiCam forward running'
		
	server.serve_forever()
