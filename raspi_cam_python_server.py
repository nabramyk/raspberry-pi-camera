#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process, Queue, Value
from urlparse import urlparse, parse_qs
from collections import deque
import subprocess, threading, time, ctypes

stored_images = Queue()
HTTP_PORT = 8080
timelapse_running = Value(ctypes.c_bool, False)
STILL_CAPTURE = "raspistill"
VIDEO_CAPTURE = "raspivid"
UV_STILL_CAPTURE = "raspistillyuv"
NO_PREVIEW = "-n"

def camera_interval_grab(interval, stored_images, timelapse_running):

	while timelapse_running.value:
		output = subprocess.Popen(["raspistill","-n","-q","40","-w","800","-h","640","-e","jpg","-o","-"], stdout=subprocess.PIPE)
		#i = Image()
		#i.data = output.communicate()[0]
		#i.timestamp = time.ctime()
		temp = output.communicate()[0]
		stored_images.put(temp)
		time.sleep(float(interval))

#This is the local server

class myHandler(BaseHTTPRequestHandler):
	
	def do_GET(self):

		temp = urlparse(self.path)
		print temp.query
		
		if self.path=="/":
			f = open('views/photography.html')
			self.send_response(200)
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
		
		if self.path=="/temperature/":
			self.send_response(200)
			self.end_headers()
			output = subprocess.Popen(["/opt/vc/bin/vcgencmd","measure_temp"], stdout=subprocess.PIPE)
			self.wfile.write(output.communicate()[0])

		if self.path=="/image/":
			self.send_response(200)
			self.end_headers()
			output = subprocess.Popen(["raspistill","-n","-q","40","-w","800","-h","640","-e","jpg","-o","-"], stdout=subprocess.PIPE)
			self.wfile.write(output.communicate()[0])
		
		if self.path=="/timelapse/download/":
			self.send_response(200)
			self.end_headers()
			global stored_images
			if not stored_images.empty():
				self.wfile.write(stored_images.get())
				
		if self.path=="/monitor/":
			self.send_response(200)
			self.end_headers()
			output = subprocess.Popen(["raspivid","-w","320","-h","240","-fps","10","-o","temp"])
	
	def do_POST(self):
		
		temp = urlparse(self.path)
		print temp.query
		
		global timelapse_running, stored_images
		
		if self.path=="/timelapse/start/":
			self.send_response(200)
			self.end_headers()
			timelapse_running.value = True
			p = Process(target=camera_interval_grab, args=('5', stored_images, timelapse_running)).start()
				
		if self.path=="/timelapse/stop/":
			self.send_response(200)
			self.end_headers()
			timelapse_running.value = False
	
		if temp.path=="/take_image/":
			self.send_response(200)
			self.end_headers()
	
		self.send_response(200)
		self.end_headers()
	
	def log_message(self, format, *args):
		return

if __name__ == '__main__':
	server = HTTPServer(('', HTTP_PORT), myHandler)
	print 'RaspiCam server running'
		
	server.serve_forever()
