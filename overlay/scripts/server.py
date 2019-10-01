#!/usr/bin/env python3

__author__ = "Elias Ibis"
__copyright__ = "Copyright 2019, AutarcTech GmbH"
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Elias Ibis"
__email__ = "elias.ibis@autarctech.de"
__status__ = "Development"

#Loading all required modules
import I2C_LCD_driver
import subprocess
import json
import sys
from threading import Thread
import netifaces as ni
import queue
from bottle import run, post, request, response, get, route, static_file, HTTPResponse
from time import sleep
import serial
import random
import sys


#initialize queue for multithreading
q = queue.Queue(maxsize=4)

#Initializing I2C LCD on address defined by I2C_LCD_Driver module
try:
	mylcd = I2C_LCD_driver.lcd()
except:
	pass


#Trying to connect to BMS and erroring out if connection fails
for i in range(15):
	try:
		ser = serial.Serial('/dev/ttyACM0', timeout=1)
		sleep(0.25)
	except:
		print("Error trying to connect")

try:
	ser.is_open
except:
	print("Serial port could not be opened.")
	mylcd.lcd_display_string("Serial Error!",1)
	sys.exit(1)
try:
	mylcd.lcd_display_string("Battery Status:",1)
	mylcd.lcd_display_string(ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr'].rjust(20),4)
except:
	pass


#Thread that scavenges the serial port for new data and tries to put it into the queue
def scavenge_serial_q(q):
	while True:
		data = ser.readline()
		#
		data = str(data).split(";")
		try:
			q.put(data, False)
		except queue.Full:
			ser.reset_input_buffer()
			sleep(0.1)
			pass
		sleep(0.1)


#Thread that updates the I2C LCD Screen every 0.5 seconds. Blocking queue get
def update_lcd():
	try:
		while True:
			data = q.get()
			Voltage = int(data[36])
			SOC = int(data[35])/1000
			Current = int(data[33])
			Power = (Voltage/1000.0) * (Current/1000.0)
			mylcd.lcd_display_string((str(round(SOC, 1))+"%").rjust(5),2)
			mylcd.lcd_display_string((str(round(Voltage/1000.0,2))+"V").rjust(6), 2, 14)
			mylcd.lcd_display_string((str(round(Current/1000.0,1))+"A").ljust(7),3)
			mylcd.lcd_display_string((str(round(Power,2))+"W").rjust(9),3 ,11)
			mylcd.lcd_display_string("",4)
			mylcd.lcd_write_char(219)
			if Current > 2000:
				mylcd.lcd_write_char(127)
			elif Current < -2000:
				mylcd.lcd_write_char(126)
			else:
				mylcd.lcd_write_char(165)
			
			sleep(0.5)
	except:
		pass


#This function fetches all the data from the BMS and parses it into a JSON for usage with javascript
def get_json():
	try:
		data = q.queue[0]
		Voltage = int(data[36])
		SOC = int(data[35])/1000
		Current = int(data[33])
		Power = (Voltage/1000.0) * (Current/1000.0)
		json_out = json.dumps({"Data":{
		"SOC":{"Unit":"%","Value":SOC},
		"Voltage":{"Unit":"mV","Value":Voltage},
		"Current":{"Unit":"mA","Value":Current},
		"Power":{"Unit":"W","Value":Power}
		},"SW":{"QueueSize":q.qsize()}}, sort_keys=True)
		return json_out;
	except:
		pass

t1 = Thread(target=scavenge_serial_q, args=(q,))
t2 = Thread(target=update_lcd)
t1.start()
t2.start()

#Server definitions
@route('/data.json')
def process():
	response.content_type = 'application/json; charset=UTF8'
	response.add_header("Cache-Control", "no-cache")
	return get_json()						#Send JSON to connected clients

@route('/<filename>')
def server_static(filename):
	response = static_file(filename, root="Server")
	response.set_header('Content-Language', 'de')
	response.add_header("Cache-Control", "no-cache")
	return response;						#Send requested file from Server root directory
@route('/restart')
def restart():
	response.set_header('Content-Language', 'de')
	response.add_header("Cache-Control", "no-cache")
	subprocess.run(["systemctl", "restart", "server.service"])
	return HTTPResponse(status=200)			#Restart the service unit on command. Usefull for LCD Resetting
@route('/')
def index():
	response = static_file("index.html", root="Server")
	response.set_header('Content-Language', 'de')
	response.add_header("Cache-Control", "no-cache")
	return response;						#Send the index.html as default for accessing the server


run(host='0.0.0.0', port=80, debug=True)										#Start the Server and listen on all interfaces and port 8080
