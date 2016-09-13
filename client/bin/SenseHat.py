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
import threading
from general_device import general_device

try:
	import sense_hat
	HAVE_DEVICE_DRIVER = True
except ImportError:
	HAVE_DEVICE_DRIVER = False


class device(general_device):

	THE_DEVICE = "SenseHat"

	def __init__(self, config, debug=False):
		super(device, self).__init__(self.THE_DEVICE, config, HAVE_DEVICE_DRIVER, debug)
		if not self.enabled:
			return
		self.sensor = sense_hat.SenseHat()
		tmp = self.sensor.get_pressure() # work around a first time use bug
		self.add_reading("temperature", "%.1fC", "C", self.sensor.get_temperature)
		self.add_reading("pressure", "%.1fPa", "Pa", self.sensor.get_pressure, scale=100.0)
		self.add_reading("humidity", "%.1f%%rH", "%rH", self.sensor.get_humidity)
		directions = {"up":sense_hat.DIRECTION_UP, "down":sense_hat.DIRECTION_DOWN, "left":sense_hat.DIRECTION_LEFT , "right":sense_hat.DIRECTION_RIGHT , "middle":sense_hat.DIRECTION_MIDDLE }
		self.joy_direction = directions.get(config[self.THE_DEVICE].get("show_message_on",None),None)
		if self.joy_direction:
			self.joystickthread = threading.Thread(target=self.__joystick)
			self.joystickthread.start()

	def __joystick(self):
		while self.keep_running:
			done = False
			for event in self.sensor.stick.get_events():
				if not done and event.direction == self.joy_direction and event.action == sense_hat.ACTION_RELEASED:
					self.sensor.show_message(self.summary())
					done = True
			time.sleep(0.5)

	def close(self):
		super(device, self).close()
		if self.enabled and self.joy_direction:
			self.joystickthread.join()


if __name__ == '__main__':

	if len(sys.argv) < 3:
		print("Specify <send time period> <total sends> [--debug]")
	else:
		debug = len(sys.argv) > 3 and sys.argv[3] == "--debug"
		config = { device.THE_DEVICE: { "average_over":3, "read_period":2, "show_message_on":"middle" } }
		with device(config, debug) as d:
			d.test(int(sys.argv[1]), int(sys.argv[2]))

