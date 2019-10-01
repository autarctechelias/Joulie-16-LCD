import json
import random


def func():
	print(json.dumps({"Data":{
		"SOC":{"Unit":"%","Value":int(open('/sys/class/power_supply/BAT1/capacity', 'r').read())},
		"Voltage":{"Unit":"mV","Value":random.randint(55000,55500)},
		"Current":{"Unit":"mA","Value":random.randint(120000,125000)}
		}}, sort_keys=True))
func()
