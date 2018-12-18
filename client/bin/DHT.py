#! /usr/bin/env python

#	Copyright 2018 Paul Broadhead
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

from general_device import general_device

try:
	import Adafruit_DHT
	HAVE_DEVICE_DRIVER = True
except ImportError:
	HAVE_DEVICE_DRIVER = False


class device(general_device):

	THE_DEVICE = "DHT"

	def get_general(self):
		if self.read_count == 0:
			while True:
				humidity, temperature = Adafruit_DHT.read(self.sensor_type, self.sensor_pin)
				if humidity is not None and temperature is not None:
					break
				if self.debug:
					print("%s: waiting for data" %(self.THE_DEVICE))
				time.sleep(2)
			self.humidity = humidity
			self.temperature = temperature
		self.read_count += 1
		if self.read_count >= len(self.buffers):
			self.read_count = 0

	def get_temperature(self):
		self.get_general()
		return self.temperature

	def get_humidity(self):
		self.get_general()
		return self.humidity

	def __init__(self, config, debug=False):

		types = { '11': Adafruit_DHT.DHT11, '22': Adafruit_DHT.DHT22, '2302': Adafruit_DHT.AM2302 }
		if not config[self.THE_DEVICE]["type"] in types:
			return

		self.sensor_type = types[config[self.THE_DEVICE]["type"]]
		self.sensor_pin = config[self.THE_DEVICE]["pin"]

		super(device, self).__init__(self.THE_DEVICE, config, HAVE_DEVICE_DRIVER, debug)
		if not self.enabled:
			return

		self.read_count = 0
		self.add_reading("temperature", "Temperature %.1f C", "C", self.get_temperature, device_tag=config[self.THE_DEVICE]["type"])
		self.add_reading("humidity", "%.1f%%rH", "%rH", self.get_humidity, device_tag=config[self.THE_DEVICE]["type"])


if __name__ == '__main__':

	if len(sys.argv) < 3:
		print("Specify <send time period> <total sends> [--debug]")
	else:
		debug = len(sys.argv) > 3 and sys.argv[3] == "--debug"
		config = { device.THE_DEVICE: { "average_over":3, "read_period":10, "type":"22", "pin":22 } }
		with device(config, debug) as d:
			d.test(int(sys.argv[1]), int(sys.argv[2]))
