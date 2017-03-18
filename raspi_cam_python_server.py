#!/usr/bin/python
from http.server import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process, Queue, Value
from urllib import parse
from collections import deque
import subprocess, threading, time, ctypes, urllib, platform, sys, socket, math, os

try:
	import psutil
except ImportError:
	print('Package psutil not installed.')

HTTP_PORT = 8080

camera_running = Value(ctypes.c_bool, False)
timelapse_running = False
timelapse_interval = 0
timelapse_time_unit = ''

image_directory = "images/"
output_format = ""

NO_PREVIEW = "-n"

#Functionality for camera handling
def camera_grab(cr, parameters):

	cr.value = True
	global timelapse_running
	p = urllib.parse.urlparse(parameters)
	temp = p.query.split('&')
	params = []
	for p in temp:
		t = p.split('=')
		for t2 in t:
			if t2=='timelapse':
				timelapse_running = t[1]
				break
			elif t2=='interval':
				timelapse_interval = int(t[1])
				break
			elif t2=='time-unit':
				timelapse_time_unit = t[1]
				break
			elif t2=='-o':
				params.append(image_directory + t[1])
				break
			elif t2=='--encoding':
				output_format = t[1]
				break
			elif t2=='':
				break
			else:
				params.append(t2)
		
	if timelapse_running=="true":
		#Convert the interval from seconds to the requested time unit
		if timelapse_time_unit=='minutes':
			timelapse_interval = timelapse_interval * 60
		elif timelapse_time_unit=='hours':
			timelapse_interval = timelapse_interval * 60 * 60
		while cr.value:
			#output = subprocess.Popen(parameters, stdout=subprocess.PIPE)
			#i = Image()
			#i.data = output.communicate()[0]
			#i.timestamp = time.ctime()
			#temp = output.communicate()[0]
			time.sleep(int(timelapse_interval))
			print("timelapse");
	else:
		# Sends the parameters string to the os and calls the camera function
		# The next line is commented out for the purposes of testing the program
		# on a device that is not a raspberry pi
		# output = subprocess.Popen(params, stdout=subprocess.PIPE)
		print('else')

	cr.value = False

#A small function for converting memory sizes to human readable strings
def convert_bytes(b):
	sizes = ['Bytes', 'KB', 'MB', 'GB']
	i = math.floor(math.log10(b) / math.log10(1024))
	return str(round(b / math.pow(1024, i), 2)) + ' ' + sizes[i]


#This is the local server
class myHandler(BaseHTTPRequestHandler):
	
	def do_GET(self):
		
		temp = urllib.parse.urlparse(self.path)
		
		if self.path=="/":
			f = open('views/view.html',"rb")
			self.send_response(200)
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
		
		if self.path=="/views/monitor/":
			f = open('views/monitor.html',"rb")
			self.send_response(200)
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
		
		if self.path=="/views/camera/":
			f = ""
			if not camera_running.value:
				f = open('views/camera.html',"rb")
			else:
				f = open('views/running_camera.html',"rb")
			self.send_response(200)
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
	
		if self.path=="/views/system_info/":
			f = open('views/system_info.html',"rb")
			self.send_response(200)
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
				
		if self.path=="/views/running_camera/":		
			f = open('views/running_camera.html',"rb")
			self.send_response(200)
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
		
		if self.path=="/monitor/":
			self.send_response(200)
			self.send_header("Content-type","xml")
			self.end_headers()
			xmlTemplate = """<root>
								<camera_status>%(camera_status)s</camera_status>
								<cpu_temperature>%(cpu_temperature)s</cpu_temperature>
								<cpu_percent>%(cpu_percent)s</cpu_percent>
								<platform_machine>%(platform_machine)s</platform_machine>
								<platform_version>%(platform_version)s</platform_version>
								<platform_system>%(platform_system)s</platform_system>
								<storage_total>%(storage_total)s</storage_total>
								<storage_used>%(storage_used)s</storage_used>
								<storage_free>%(storage_free)s</storage_free>
								<storage_percent>%(storage_percent)s</storage_percent>
							</root>"""
			
			# Grabs the temperature of the raspberry pi's cpu
			# Uncomment this line for use on the raspberry pi
			# output = subprocess.Popen(["/opt/vc/bin/vcgencmd","measure_temp"], stdout=subprocess.PIPE)
			# temperature = output.communicate()[0].decode()
			# temp = temperature[5:7] + '.' + temperature[8]
			temp = 'blank'
			
			data = 	{
					'camera_status':camera_running.value,
					'cpu_temperature':temp,
					'cpu_percent':psutil.cpu_percent(),
					'platform_machine':platform.machine(),
					'platform_version':platform.version(),
					'platform_system':platform.system(),
					'storage_total':convert_bytes(psutil.disk_usage('/').total),
					'storage_used':convert_bytes(psutil.disk_usage('/').used),
					'storage_free':convert_bytes(psutil.disk_usage('/').free),
					'storage_percent':psutil.disk_usage('/').percent,
					}
			t = bytes(xmlTemplate%data, 'utf-8')
			self.wfile.write(t)
	
		if self.path=="/views/style.css":
			f = open('views/style.css',"rb")
			self.send_response(200)
			self.end_headers()
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
	
	def do_POST(self):
		temp = urllib.parse.urlparse(self.path)

		if temp.path=="/stop_sequence/":
			print("stopping")
			camera_running.value=False;
		elif temp.path=="/start_sequence/":
			print("starting")
			p = Process(target=camera_grab, args=(camera_running, self.path)).start()
	
		self.send_response(200)
		self.end_headers()
	
	def log_message(self, format, *args):
		return

if __name__ == '__main__':
	server = HTTPServer(('', HTTP_PORT), myHandler)
	print('RaspiCam server running')
		
	server.serve_forever()
