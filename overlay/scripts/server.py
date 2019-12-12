#!/usr/bin/env python3

__author__ = "Elias Ibis"
__copyright__ = "Copyright 2019, AutarcTech GmbH"
__license__ = "GPL"
__version__ = "2.0.2"
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
from bottle import run, post, request, response, get, route, static_file, HTTPResponse, error
from time import sleep
import random
import socket
import crcmod
import os


#######UDP Multicast Code

crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0x0000, xorOut=0x0000)                           # CRC Setup for Joulie-16

ANY = "0.0.0.0" 
MCAST_ADDR = "239.255.73.100"
MCAST_PORT = 1500
MCAST_TTL = 2
BMS_LIST = []

try:
	# Create a UDP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

	# Allow multiple sockets to use the same PORT number
	sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

	# Bind to the port that we know will receive multicast data
	sock.bind((ANY,MCAST_PORT))

	# Tell the kernel that we are a multicast socket
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MCAST_TTL)

	# Tell the kernel that we want to add ourselves to a multicast group
	# The address for the multicast group is the third param


	status = sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MCAST_ADDR) + socket.inet_aton(ANY))

	# setblocking(0) is equiv to settimeout(0.0) which means we poll the socket.
	# But this will raise an error if recv() or send() can't immediately find or send data. 
	sock.setblocking(1)
	sock.settimeout(1)
	count = 0
except:
	print("An error has okuu'd")
	sys.exit()

#######End UDP Multicast Code



#initialize queue for multithreading
q = []
q.append(queue.Queue(maxsize=4))

#Initializing I2C LCD on address defined by I2C_LCD_Driver module
try:
	mylcd = I2C_LCD_driver.lcd()
except:
	pass
try:
	mylcd.lcd_display_string("Battery Status:",1)
except:
	pass


#Thread that scavenges the serial port for new data and tries to put it into the queue
def scavenge_data_q(q):
	while True:
		try:
			data, addr = sock.recvfrom(1024)
			data = str(data).split(",")
			if data[2] == '100':
				if data[1] not in BMS_LIST:
					BMS_LIST.append(data[1])
				try:
					q[0].put(data, False)
				except:
					sleep(0.1)
					pass
		except KeyboardInterrupt:
			sys.exit()
		except:
			print("No data received. Is the BMS connected to the network and turned on?")
		sleep(0.1)


#Thread that updates the I2C LCD Screen every 0.5 seconds. Blocking queue get
def update_lcd():
	try:
		while True:
			data = q[0].get()
			Voltage = float(data[-8])
			SOC = float(data[-6])
			Current = float(data[-9])
			Power = Voltage * Current
			mylcd.lcd_display_string((str(round(SOC, 1))+"%").rjust(5),2)
			mylcd.lcd_display_string((str(round(Voltage,2))+"V").rjust(6), 2, 14)
			mylcd.lcd_display_string((str(round(Current,1))+"A").ljust(7),3)
			mylcd.lcd_display_string((str(round(Power,2))+"W").rjust(9),3 ,11)
			mylcd.lcd_display_string(ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr'].rjust(18),4, 2)
			mylcd.lcd_display_string("",4)
			mylcd.lcd_write_char(219)
			if Current > 2000:
				mylcd.lcd_write_char(127)
			elif Current < -2000:
				mylcd.lcd_write_char(126)
			else:
				mylcd.lcd_write_char(165)
			
			sleep(0.5)
	except KeyboardInterrupt:
		sys.exit()
	except:
		pass


#This function fetches all the data from the BMS and parses it into a JSON for usage with javascript. Nonblocking queue peek
def get_json():
	datadict = {'BMSCount':len(BMS_LIST)}
	try:
		data = q[0].get()
		Voltage = float(data[-8])
		SOC = float(data[-6])
		Current = float(data[-9])
		Power = Voltage * Current
		datadict.update({"BMS" + str(len(BMS_LIST)-1):{
		"SOC":{"Unit":"%","Value":SOC},
		"Voltage":{"Unit":"V","Value":Voltage},
		"Current":{"Unit":"A","Value":Current},
		"Power":{"Unit":"W","Value":Power}
		,"SW":{"QueueSize":q[0].qsize(), "RawData":data}}})
		json_out = json.dumps(datadict);
		return json_out;
	except:
		pass

t1 = Thread(target=scavenge_data_q, args=(q,))
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
	print(filename)
	if filename == "restart.html":
		print("Restart Trig'd")
		subprocess.Popen('sleep 1; systemctl restart server.service', shell=True)
	response = static_file(filename, root="Server")
	response.set_header('Content-Language', 'de')
	response.add_header("Cache-Control", "no-cache")
	return response;						#Send requested file from Server root directory
@route('/')
def index():
	response = static_file("index.html", root="Server")
	response.set_header('Content-Language', 'de')
	response.add_header("Cache-Control", "no-cache")
	return response;						#Send the index.html as default for accessing the server

@error(404) 
def error404(error):
	response = static_file("404.html", root="Server")
	return response;


run(host='0.0.0.0', port=80, debug=True)										#Start the Server and listen on all interfaces and port 8080
