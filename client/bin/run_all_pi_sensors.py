#! /usr/bin/env python

#	Copyright 2016 Paul Broadhead
#	Contact: pjbroad@twinmoons.org.uk
#
#	This file is part of pi_sensors.
#
#	pi_sensors is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	pi_sensors is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with pi_sensors.  If not, see <http://www.gnu.org/licenses/>.

import time
import sys
import os

import RCW0506
import DS18B20
import MCP9808
import TSL2561
import BMP180
import BME280
import SenseHat
import lcd_panel
import openweathermap
import pi_config
import interface

if __name__ == '__main__':

	if len(sys.argv) < 3:
		print("Specify <send time period> <total sends> [<room>]")
	else:

		config = pi_config.get()
		debug = config.get("debug", False)

		send_time_period = int(sys.argv[1])
		total_sends = int(sys.argv[2])
		if len(sys.argv) > 3:
			config["room"] = sys.argv[3]

		print("%s: Starting Pi Sensors for room [%s]" %(time.asctime(), config["room"]))

		servers = []
		for server_config in config["servers"]:
			servers.append(interface.sender(server_config))

		try:
			lcd = lcd_panel.device(config, debug)
			weather = openweathermap.device(config, debug)
			sensors = []
			sensors.append(MCP9808.device(config, debug))
			sensors.append(DS18B20.device(config, debug))
			sensors.append(TSL2561.device(config, debug))
			sensors.append(RCW0506.device(config, lcd, debug))
			sensors.append(BMP180.device(config, debug))
			sensors.append(BME280.device(config, debug))
			sensors.append(SenseHat.device(config, debug))
			enabled_sensors = ""
			for sensor in sensors + [lcd, weather]:
				if sensor.enabled:
					enabled_sensors += "(" + sensor.THE_DEVICE + ") "
			print("Enabled devices: [%s]" %(enabled_sensors.rstrip()))
			for server in servers:
				server.send()
			sys.stdout.flush()

			last_send_time = time.time()
			send_count = 0
			while send_count < total_sends:
				line = 1
				if lcd.is_on:
					for sensor in sensors:
						if sensor.enabled:
							lcd.text(line, sensor.summary().ljust(20))
							line += 1
				time.sleep(1)
				if time.time() - last_send_time > send_time_period:
					last_send_time = time.time()
					if weather.enabled:
						weather.update_raw()
					records = []
					for sensor in sensors:
						if sensor.enabled:
							for reading in sensor.get():
								records.append(reading)
					for server in servers:
						for record in records:
							if record:
								server.add_reading(config["room"], record)
						if weather.enabled:
							for location, record in weather.get_readings():
								server.add_reading(location, record)
							if weather.save_raw:
								server.add_raw_weather(weather.get_raw())
						server.send()
					sys.stdout.flush()
					send_count += 1

		except:
			print("%s: Exception caught, exiting" %(time.asctime()))
			raise

		finally:
			for sensor in sensors + [lcd, weather]:
				sensor.close()
