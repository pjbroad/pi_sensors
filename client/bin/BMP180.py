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

import sys


from general_device import general_device

try:
	import Adafruit_BMP.BMP085 as BMP085
	HAVE_DEVICE_DRIVER = True
except ImportError:
	HAVE_DEVICE_DRIVER = False


class device(general_device):

	THE_DEVICE = "BMP180"

	def __init__(self, config, debug=False):
		super(device, self).__init__(self.THE_DEVICE, config, HAVE_DEVICE_DRIVER, debug)
		if not self.enabled:
			return
		self.sensor = BMP085.BMP085()
		self.add_reading("temperature", "%.1f", "C", self.sensor.read_temperature)
		self.add_reading("pressure", "%.1f", "Pa", self.sensor.read_pressure)


if __name__ == '__main__':

	if len(sys.argv) < 3:
		print("Specify <send time period> <total sends> [--debug]")
	else:
		debug = len(sys.argv) > 3 and sys.argv[3] == "--debug"
		config = { device.THE_DEVICE: { "average_over":3, "read_period":2 } }
		with device(config, debug) as d:
			d.test(int(sys.argv[1]), int(sys.argv[2]))
