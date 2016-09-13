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

try:
	from gpiozero import MotionSensor
	FAILED_DEVICE_DRIVER = False
except ImportError:
	class MotionSensor:
		None
	FAILED_DEVICE_DRIVER = True

def on_motion(pir):
	pir.detections += 1
	if pir.state_change_obj:
		pir.state_change_obj.change_state(True)

def on_no_motion(pir):
	if pir.state_change_obj:
		pir.state_change_obj.change_state(False)


class Counting_Motion(MotionSensor):

	def __init__(self, gpio_pin, state_change_obj):
		super(Counting_Motion, self).__init__(gpio_pin)
		self.state_change_obj = state_change_obj
		self._reset()
		if self.detections > 0:
			if self.state_change_obj:
				self.state_change_obj.change_state(True)

	def close(self):
		super(Counting_Motion, self).close()

	def _reset(self):
		if self.motion_detected:
			self.detections = 1
		else:
			self.detections = 0


class device:

	THE_DEVICE = "RCW0506"

	def __init__(self, config, state_change_obj, debug=False):
		self.debug = debug
		if (not device.THE_DEVICE in config) or FAILED_DEVICE_DRIVER:
			if self.debug:
				print("%s disabled" %(device.THE_DEVICE))
			self.enabled = False
			return
		self.enabled = True
		self.pir = None
		self.gpio_pin = config[device.THE_DEVICE]["GPIO"]
		self.state_change_obj = state_change_obj
		self.mutex = threading.Lock()
		self.active = 0
		self.inactive = 0
		self.pir = Counting_Motion(self.gpio_pin, self.state_change_obj)
		self.pir.when_motion = on_motion
		self.pir.when_no_motion = on_no_motion
		self.keep_running = True
		self.runthread = threading.Thread(target=self.__run)
		self.runthread.start()

	def __enter__(self):
		return self

	def __exit__(self, exct_type, exce_value, traceback):
		self.close()

	def _reset(self):
		with self.mutex:
			self.active = 0
			self.inactive = 0
			self.pir._reset()

	def __run(self):
		while self.keep_running:
			with self.mutex:
				if self.pir.motion_detected:
					self.active += 1
				else:
					self.inactive += 1
				if self.debug:
					print("Active=%d Inactive=%d" %(self.active, self.inactive))
			time.sleep(1)

	def close(self):
		if not self.enabled:
			return
		self.keep_running = False
		self.runthread.join()
		self.pir.close()

	def current(self):
		if not self.enabled:
			return (False, None)
		with self.mutex:
			if self.active + self.inactive == 0:
				activity = 0
			else:
				activity = round(100 * float(self.active) / float(self.active + self.inactive), 1)
			data = {"detections":self.pir.detections, "activity":activity }
		return (self.pir.motion_detected, data)

	def summary(self):
		if not self.enabled:
			return "No movement sensor"
		have_motion, motion_data = self.current()
		if have_motion:
			thetext = "Active, %.1f%%" %(motion_data["activity"])
		else:
			thetext = "Inactive, %.1f%%" %(motion_data["activity"])
		return thetext

	def get(self):
		if not self.enabled:
			return []
		have_motion, motion_data = self.current()
		self._reset()
		return [ {"type":"movement", "record":{ "value":motion_data["activity"], "units":"%", "device":device.THE_DEVICE + ".activity" }},
				{"type":"movement", "record":{ "value":motion_data["detections"], "device":device.THE_DEVICE + ".detections" }} ]


if __name__ == '__main__':

	if len(sys.argv) < 3:
		print("Specify <send time period> <total sends> [--debug]")

	else:

		send_time_period = int(sys.argv[1])
		total_sends = int(sys.argv[2])
		debug = len(sys.argv) > 3 and sys.argv[3] == "--debug"
		config = { device.THE_DEVICE: { "GPIO":17 } }

		m = device(config, None)
		m.close()

		with device(config, None, debug) as m:
			for i in range(total_sends):
				for j in range(send_time_period):
					print(m.current(), m.summary())
					time.sleep(1)
				print("record", m.get())
		print("exit")
