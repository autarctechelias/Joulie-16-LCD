import I2C_LCD_driver
from time import sleep
import serial
import random
import sys

mylcd = I2C_LCD_driver.lcd()
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
	sys.exit()


counter_write = 0
SOC = 0
Voltage = 52447
Current = 100
Power = Voltage * Current
try:
	f = open("energy.txt", "r")
	read = f.readline()
	if float(read) > 0:
		Energy = float(read)
	f.close()
except:
	Energy = 0
direction = 'pos'

mylcd.lcd_display_string("Battery SOC:",1)
try:
	while True:
		try:
			data = ser.readline()
			data = str(data).split(";")
			Voltage = int(data[36])
			SOC = int(data[35])/1000
			Current = int(data[33])
			Power = (Voltage/1000.0) * (Current/1000.0)
			if Power > 0:
				Energy += Power		# Energy in Ws
			kilowatthours = Energy / (3600000*4)
			mylcd.lcd_display_string((str(round(SOC, 1))+"%").rjust(5),2)
			
			mylcd.lcd_display_string((str(round(Voltage/1000.0,2))+"V").rjust(6), 2, 14)
			mylcd.lcd_display_string((str(round(Current/1000.0,1))+"A").ljust(7),3)
			mylcd.lcd_display_string((str(round(Power,2))+"W").rjust(9),3 ,11)
			mylcd.lcd_display_string("",4)
			mylcd.lcd_write_char(219)
			if Current > 4000:
				mylcd.lcd_write_char(127)
			elif Current < -4000:
				mylcd.lcd_write_char(126)
			else:
				mylcd.lcd_write_char(165)
			mylcd.lcd_display_string((str(round(kilowatthours,1))+"kWh").rjust(18),4,2)
			counter_write += 1
			if counter_write >= 100:
				f = open("energy.txt", "w+")
				f.write(str(Energy))
				f.close()
				counter_write = 0
			ser.reset_input_buffer()
			sleep(0.25)
		except (KeyboardInterrupt, SystemExit):
			break
		except:
			pass
except (KeyboardInterrupt, SystemExit):
		print("Exiting…")
		ser.close()
