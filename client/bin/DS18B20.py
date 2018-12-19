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
import glob
import threading

from general_device import general_device


class device(general_device):

	THE_DEVICE = "DS18B20"

	def _get_device_name(self):
		base_dir = '/sys/bus/w1/devices/'
		try:
			device_folder = glob.glob(base_dir + '28*')[0]
		except:
			return None
		device_file = device_folder + '/w1_slave'
		if os.path.isfile(device_file):
			return device_file
		else:
			return None

	def _get_temperature(self):
		device_file = self._get_device_name()
		lines = open(device_file, 'r').readlines()
		while not lines[0].strip().endswith("YES"):
			time.sleep(0.2)
			lines = open(device_file, 'r').readlines()
		tmp = lines[1].strip().split("=")
		if len(tmp) != 2:
			return None
		else:
			try:
				return int(tmp[1]) / 1000.0
			except:
				return None

	def __init__(self, config, debug=False):
		HAVE_DEVICE = self._get_device_name() != None
		super(device, self).__init__(self.THE_DEVICE, config, HAVE_DEVICE, debug)
		if not self.enabled:
			return
		self.add_reading("temperature", "%.1f", "C", self._get_temperature)


if __name__ == '__main__':

	if len(sys.argv) < 3:
		print("Specify <send time period> <total sends> [--debug]")
	else:
		debug = len(sys.argv) > 3 and sys.argv[3] == "--debug"
		config = { device.THE_DEVICE: { "average_over":3, "read_period":2 } }
		with device(config, debug) as d:
			d.test(int(sys.argv[1]), int(sys.argv[2]))
