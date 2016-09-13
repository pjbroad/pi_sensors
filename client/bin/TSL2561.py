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

import json
import os
import sys
import subprocess
from general_device import general_device


class reading:
	def __init__(self, controller, exec_path):
		self.controller = controller
		self.exec_path = exec_path
		self.readings = {}
		self.used_flags = {"lux":True, "broadband":True, "ir":True}

	def get_common(self, name):
		if self.used_flags[name]:
			self.get_readings()
		self.used_flags[name] = True
		return self.readings["TSL2561"][name]

	def get_lux(self):
		return self.get_common("lux")

	def get_bb(self):
		return self.get_common("broadband")

	def get_ir(self):
		return self.get_common("ir")

	def get_readings(self):
		process = subprocess.Popen([self.exec_path, str(self.controller)], stdout=subprocess.PIPE)
		(output, err) = process.communicate()
		exit_code = process.wait()
		if exit_code == 0:
			self.readings = json.loads(output)
			self.used_flags = {"lux":False, "broadband":False, "ir":False}
		else:
			raise Exception("Failed to getreading %s %s" %(device.THE_DEVICE, err))



class device(general_device):

	THE_DEVICE = "TSL2561"

	def __init__(self, config, debug=False):
		if device.THE_DEVICE in config and "exec_path" in config[device.THE_DEVICE]:
			exec_path = config[device.THE_DEVICE]["exec_path"]
			have_dep = os.path.isfile(exec_path) and os.access(exec_path, os.X_OK)
		else:
			have_dep = False
		super(device, self).__init__(self.THE_DEVICE, config, have_dep, debug)
		if not self.enabled:
			return
		controller = config[device.THE_DEVICE]["i2c Controller"]
		self.sensor = reading(controller, exec_path)
		self.add_reading("light", "Light %.0f Lx", "Lx", self.sensor.get_lux, device_tag=".lux")
		self.add_reading("light", None, None, self.sensor.get_ir, device_tag=".ir")
		self.add_reading("light", None, None, self.sensor.get_bb, device_tag=".bb")


if __name__ == '__main__':

	if len(sys.argv) < 3:
		print("Specify <send time period> <total sends> [--debug]")
	else:
		debug = len(sys.argv) > 3 and sys.argv[3] == "--debug"
		config = { device.THE_DEVICE: { "average_over":3, "read_period":2, "i2c Controller":1, "exec_path":"./TSL2561_get_readings" } }
		with device(config, debug) as d:
			d.test(int(sys.argv[1]), int(sys.argv[2]))
