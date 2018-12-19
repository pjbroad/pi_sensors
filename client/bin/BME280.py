#! /usr/bin/env python

#	Copyright 2017 Paul Broadhead
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
	import Adafruit_BME280 as BME280
	HAVE_DEVICE_DRIVER = True
except ImportError:
	HAVE_DEVICE_DRIVER = False


class device(general_device):

	THE_DEVICE = "BME280"

	def __init__(self, config, debug=False):
		super(device, self).__init__(self.THE_DEVICE, config, HAVE_DEVICE_DRIVER, debug)
		if not self.enabled:
			return
		modes = { "BME280_OSAMPLE_1":BME280.BME280_OSAMPLE_1, "BME280_OSAMPLE_2":BME280.BME280_OSAMPLE_2,
		"BME280_OSAMPLE_4":BME280.BME280_OSAMPLE_4, "BME280_OSAMPLE_8":BME280.BME280_OSAMPLE_8,
		"BME280_OSAMPLE_16":BME280.BME280_OSAMPLE_16 }
		mode = config[device.THE_DEVICE]["mode"]
		if mode in modes:
			self.sensor = BME280.BME280(modes[mode])
			self.add_reading("temperature", "%.1f", "C", self.sensor.read_temperature)
			self.add_reading("humidity", "%.1f", "%rH", self.sensor.read_humidity)
			self.add_reading("pressure", "%.1f", "Pa", self.sensor.read_pressure, scale=1.0)
		else:
			print("%s: Invalid mode [%s]" %(self.THE_DEVICE, mode))
			self.enabled = False

if __name__ == '__main__':

	if len(sys.argv) < 3:
		print("Specify <send time period> <total sends> [--debug]")
	else:
		debug = len(sys.argv) > 3 and sys.argv[3] == "--debug"
		config = { device.THE_DEVICE: { "mode":"BME280_OSAMPLE_1", "average_over":3, "read_period":2 } }
		with device(config, debug) as d:
			d.test(int(sys.argv[1]), int(sys.argv[2]))

