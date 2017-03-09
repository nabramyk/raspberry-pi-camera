#!/usr/bin/python
from http.server import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process, Queue, Value
from urllib import parse
from collections import deque
import subprocess, threading, time, ctypes, urllib, platform, sys, socket, math

try:
	import psutil
except ImportError:
	print('Package psutil not installed.')

stored_images = Queue()
HTTP_PORT = 8080
timelapse_running = Value(ctypes.c_bool, False)

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


def convert_bytes(b):
	sizes = ['Bytes', 'KB', 'MB', 'GB']
	i = math.floor(math.log10(b) / math.log10(1024))
	return round(b / math.pow(1024, i), 2) + ' ' + sizes[i]

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
			f = open('views/camera.html',"rb")
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
			
			# Uncomment this line for use on the raspberry pi
			output = subprocess.Popen(["/opt/vc/bin/vcgencmd","measure_temp"], stdout=subprocess.PIPE)
			temperature = output.communicate()[0].decode()
			temp = temperature[5:7] + '.' + temperature[8]
			
			data = 	{
					'camera_status':'not running',
					'cpu_temperature': temp,
					'cpu_percent':psutil.cpu_percent(),
					'platform_machine':platform.machine(),
					'platform_version':platform.version(),
					'platform_system':platform.system(),
					'storage_total':convert_bytes(psutil.disk_usage('/').total),
					'storage_used':psutil.disk_usage('/').used,
					'storage_free':psutil.disk_usage('/').free,
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
		temp2 = temp.query.split('&')
		params = []
		for p in temp2:
			t = p.split('=')
			for t2 in t:
				params.append(t2)
		
		global timelapse_running, stored_images
		
		if self.path=="/timelapse/start/":
			timelapse_running.value = True
			p = Process(target=camera_interval_grab, args=('5', stored_images, timelapse_running)).start()
				
		if self.path=="/timelapse/stop/":
			timelapse_running.value = False
	
		#if temp.path=="/take_image/":

	
		self.send_response(200)
		self.end_headers()
	
	def log_message(self, format, *args):
		return

if __name__ == '__main__':
	server = HTTPServer(('', HTTP_PORT), myHandler)
	print('RaspiCam server running')
		
	server.serve_forever()
