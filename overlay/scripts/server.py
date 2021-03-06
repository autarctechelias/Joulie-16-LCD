#!/usr/bin/env python3

__author__ = "Elias Ibis"
__copyright__ = "Copyright 2019, AutarcTech GmbH"
__license__ = "GPL"
__version__ = "2.3.5"
__maintainer__ = "Elias Ibis"
__email__ = "elias.ibis@autarctech.de"
__status__ = "Development"

#Loading all required modules
import I2C_LCD_driver
import subprocess
import json
import sys
from threading import Thread
import collections
from bottle import run, post, request, response, get, route, static_file, HTTPResponse, error
from time import sleep
import random
import socket
import crcmod
import time
import os

def map(x, in_min, in_max, out_min, out_max):
    return max(min(out_max, int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)), out_min)



try:
	with open('/boot/currentscale.txt') as f:
		current_scaling_factor = float(f.readline())
except:
	current_scaling_factor = 1
	pass
customchars = [
	[0x0E,0x1F,0x11,0x11,0x11,0x13,0x17,0x1F],
	[0x0E,0x1F,0x11,0x11,0x13,0x17,0x1F,0x1F],
	[0x0E,0x1F,0x11,0x13,0x17,0x1F,0x1F,0x1F],
	[0x0E,0x1F,0x13,0x17,0x1F,0x1F,0x1F,0x1F],
	[0x0E,0x1F,0x1F,0x1F,0x1F,0x1F,0x1F,0x1F],
	[0x04,0x0E,0x1F,0x04,0x04,0x04,0x04,0x04],
	[0x04,0x04,0x04,0x04,0x04,0x1F,0x0E,0x04]
]


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
#q.append(collections.deque(maxlen=2)

#Initializing I2C LCD on address defined by I2C_LCD_Driver module
try:
	mylcd = I2C_LCD_driver.lcd()
except:
	pass
try:
	mylcd.lcd_load_custom_chars(customchars)
	mylcd.lcd_display_string(__version__,1)
except:
	pass


#Thread that listens to the network for new data and tries to put it into the queue
def scavenge_data_q(q):
	LOG_COUNT = 0
	LOG_INTERVAL = 60
	while True:
		try:
			data, addr = sock.recvfrom(1024)
			datal = str(data).split(",")
			if datal[2] == '100':
				if LOG_COUNT >= LOG_INTERVAL:
					#now = time.strftime("%d.%m.%Y-%H:%M:%S", time.localtime(time.time()))                       # Get current system time
					f = open("Logs/BMS"+str(datal[1])+".csv", "a+")                                                    # Open/create Logfile for each BMS
					#f.write(str(now)+','+str(data)+'\r\n')                                                           # Write complete message to logfile
					f.write(str(data)+'\r\n')
					f.close()
					LOG_COUNT = 0
				else:
					LOG_COUNT +=1
				if datal[1] not in BMS_LIST:
					BMS_LIST.append(datal[1])
					q.append(collections.deque(maxlen=2))
				try:
					q[BMS_LIST.index(datal[1])].append(datal)
				except:
					sleep(0.1)
					pass
		except KeyboardInterrupt:
			sys.exit()
		except:
			print("No data received. Is the BMS connected to the network and turned on?")
		sleep(0.1)


#Thread that updates the I2C LCD Screen every second. Deque peek
def update_lcd():
	try:
		sleep(1)
		mylcd.lcd_display_string("Battery Status:",1)
		while True:
			for i in range(len(BMS_LIST)):
				for n in range(10):
					data = q[i][0]
					Voltage = float(data[-8])
					SOC = float(data[-6])
					Current = float(data[-9]) * current_scaling_factor
					Power = Voltage * Current
					mylcd.lcd_display_string((str(round(SOC, 1))+"%").rjust(5),2)
					mylcd.lcd_display_string((str(round(Voltage,2))+"V").rjust(6), 2, 14)
					mylcd.lcd_display_string((str(round(Current,1))+"A").ljust(7),3)
					mylcd.lcd_display_string((str(round(Power,2))+"W").rjust(9),3 ,11)
					#mylcd.lcd_display_string(ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr'].rjust(18),4, 2)
					mylcd.lcd_display_string(("ID: " + str(BMS_LIST[i])).rjust(18),4, 2)
					mylcd.lcd_display_string("",4)
					mylcd.lcd_write_char(map(int(SOC),20,80,0,4))
					if Current > 2:
						mylcd.lcd_write_char(5)
					elif Current < -2:
						mylcd.lcd_write_char(6)
					else:
						mylcd.lcd_write_char(165)
					
					sleep(1)
	except KeyboardInterrupt:
		sys.exit()
	except:
		pass


#This function is parsing the raw BMS data into a JSON for usage with javascript. Deque peek
def get_json():
	datadict = {'BMSCount':len(BMS_LIST)}
	for i in range(len(BMS_LIST)):
		data = q[i][0]
		Voltage = float(data[-8])
		SOC = float(data[-6])
		Current = float(data[-9]) * current_scaling_factor
		Power = Voltage * Current
		datadict.update({"BMS" + str(i):{
		"SOC":{"Unit":"%","Value":SOC},
		"Voltage":{"Unit":"V","Value":Voltage},
		"Current":{"Unit":"A","Value":Current},
		"Power":{"Unit":"W","Value":Power}
		,"SW":{"RawData":data}}})
		json_out = json.dumps(datadict);
	return json_out;
	#except:
		#pass

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
@route('/log')
def server_static():
	print()
	response = static_file("BMS"+BMS_LIST[0]+".csv", root="Logs")
	response.set_header('Content-Language', 'de')
	response.add_header("Cache-Control", "no-cache")
	return response;						#Send requested file from Server root directory
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
@route('/de/<filename>')
def server_static(filename):
	print(filename)
	if filename == "restart.html":
		print("Restart Trig'd")
		subprocess.Popen('sleep 1; systemctl restart server.service', shell=True)
	response = static_file(filename, root="Server/de/")
	response.set_header('Content-Language', 'de')
	response.add_header("Cache-Control", "no-cache")
	return response;						#Send requested file from Server root directory

@route('/')
def index():
	response = static_file("index.html", root="Server")
	response.set_header('Content-Language', 'de')
	response.add_header("Cache-Control", "no-cache")
	return response;						#Send the index.html as default for accessing the server

#@error(404) 
#def error404(error):
#	response = static_file("404.html", root="Server")
#	return response;


run(host='0.0.0.0', port=80, debug=True)										#Start the Server and listen on all interfaces and port 80
