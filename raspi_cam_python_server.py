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
pid = Value(ctypes.c_int, 0)

timelapse_running = False
timelapse_interval = 0
timelapse_time_unit = ''
timelapse_image_limit = 0
timelapse_start_time = ''
timelapse_end_time = ''

camera_counter = 1

image_directory = "../images/"
image_subdirectory = ""
output_session_name = ""
output_format = ""
output_filename = ""

NO_PREVIEW = "-n"

#Functionality for camera handling
def camera_grab(pid, cr, parameters, camera_counter):

	cr.value = True
	global timelapse_running, image_subdirectory, output_session_name, output_format
	p = urllib.parse.urlparse(parameters)
	temp = p.query.split('&')
	params = []
	for p in temp:
		t = p.split('=')
		for t2 in t:
			print(t2)
			if t2=='timelapse':
				timelapse_running = t[1]
				break
			elif t2=='interval':
				timelapse_interval = int(t[1])
				break
			elif t2=='time-unit':
				timelapse_time_unit = t[1]
				break
			elif t2=='limit':
				timelapse_image_limit = int(t[1])
				break
			elif t2=='start-time':
				timelapse_start_time = t[1]
				break
			elif t2=='end-time':
				timelapse_end_time = t[1]
				break
			elif t2=='session_title':
				output_session_name = parse_time_replacement_characters(t[1]) + '/'
				break
			elif t2=='-o':
				output_filename = t[1]
				break
			elif t2=="subfolder":
				image_subdirectory = t[1]
				break
			elif t2=='--encoding':
				params.append(t2)
				params.append(t[1])
				output_format = t[1]
				break
			elif t2=='raspivid':
				output_format = 'h264'
				params.append(t2)
				break
			elif t2=='raspistillyuv':
				print('YUV')
				output_format = 'YUV'
				params.append(t2)
				break
			elif t2=='':
				break
			else:
				params.append(t2)
	
	params.append('-o')
	
	if timelapse_running=="true":
		
		iterative_counter = 1
		
		#Convert the interval from seconds to the requested time unit
		if timelapse_time_unit=='minutes':
			timelapse_interval = timelapse_interval * 60
		elif timelapse_time_unit=='hours':
			timelapse_interval = timelapse_interval * 60 * 60
		while cr.value:
			
			if not os.path.exists(image_directory + output_session_name):
				os.mkdir(image_directory + output_session_name)
				
			temp = ""
			if image_subdirectory!="":
				temp = parse_time_replacement_characters(image_subdirectory) + "/"
				if not os.path.exists(image_directory + output_session_name + "/" + temp):
					os.mkdir(image_directory + output_session_name + "/" + temp)
			subprocess.call(params + [image_directory + output_session_name + temp + parse_time_replacement_characters(output_filename) + '.' + output_format])
						
			camera_counter += 1
			time.sleep(int(timelapse_interval))
	else:
		# Sends the parameters string to the os and calls the camera function
		# The next line is commented out for the purposes of testing the program
		# on a device that is not a raspberry pi
		output = subprocess.Popen(params + [image_directory + parse_time_replacement_characters(output_filename) + '.' + output_format])

	cr.value = False

#A small function for converting memory sizes to human readable strings
def convert_bytes(b):
	sizes = ['Bytes', 'KB', 'MB', 'GB']
	i = math.floor(math.log10(b) / math.log10(1024))
	return str(round(b / math.pow(1024, i), 2)) + ' ' + sizes[i]

def parse_time_replacement_characters(s):
	global camera_counter
	while(s.find('%C')!=-1):
		i = s.find('%C')
		s = s[:i] + str(camera_counter) + s[i+2:]
		camera_counter += 1
	return time.strftime(s)

#This is the local server
class myHandler(BaseHTTPRequestHandler):
	
	def do_GET(self):
		
		temp = urllib.parse.urlparse(self.path)
		print(temp)
		
		if self.path=="/":
			f = open('views/view.html',"rb")
			self.send_response(200)
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
		
		if self.path=="/libs/jquery/jquery-3.2.0.js":
			f = open('libs/jquery/jquery-3.2.0.js',"rb")
			self.send_response(200)
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
		
		#Implementing mechanic for handling file porting to a different
		#machine
		if self.path=="/pull/":
			self.send_response(200)
			self.end_headers()
			
		
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
	
		if self.path=="/views/tags/":
			f = open('views/tags.html',"rb")
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
		
		if self.path=="/viewfinder/":
			output = subprocess.Popen(['raspistill','--width','800','--height','600','-o','-'], stdout=subprocess.PIPE)
			self.send_response(200)
			self.end_headers()
			self.wfile.write(output.communicate()[0])
		
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
			p = Process(target=camera_grab, args=(pid, camera_running, self.path, camera_counter)).start()
	
		self.send_response(200)
		self.end_headers()
	
	def log_message(self, format, *args):
		return

if __name__ == '__main__':
	print("Checking for default images directory: " + image_directory)
	if not os.path.exists(image_directory):
		print("Directory " + image_directory + " does not exist, creating it now")
		os.mkdir(image_directory)
	server = HTTPServer(('', HTTP_PORT), myHandler)
	print('RaspiCam server running')
		
	server.serve_forever()
