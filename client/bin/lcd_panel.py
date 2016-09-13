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
import threading
import sys
import os

try:
	import lcddriver
	simulate_mode = False
except ImportError:
	simulate_mode = True

class device:

	THE_DEVICE = "LCD"

	def __init__(self, config, debug=False):
		self.debug = debug or simulate_mode
		self.is_on = False
		if not device.THE_DEVICE in config:
			self.enabled = False
			return
		self.enabled = True
		if not simulate_mode:
			self.driver = lcddriver.lcd(int(config[device.THE_DEVICE]["address"],16))
		if self.debug:
			print("LCD panel initialised")
		self.off_delay = config[device.THE_DEVICE]["timeout_seconds"]
		self.num_lines = config[device.THE_DEVICE]["num_lines"]
		self.last_active = time.time()
		self.is_active = False
		self.terminate = False
		self.text_lines = self.num_lines * [""]
		self._on()
		self.runthread = threading.Thread(target=self._run)
		self.runthread.start()

	def __enter__(self):
		return self

	def __exit__(self, exct_type, exce_value, traceback):
		self.close()

	def change_state(self, state):
		if not self.enabled:
			return
		self.last_active = time.time()
		self.is_active = state
		if (state):
			self._on()

	def text(self, line, thetext):
		if not self.enabled:
			return
		if line < self.num_lines:
			self.text_lines[line] = thetext

	def _run(self, timing_out=False):
		while not self.terminate:
			if self.is_on:
				self.text(0, time.strftime("%d %b %Y %H:%M:%S", time.localtime()))
				if self.debug:
					print("LCD text:")
				for line in range(0,len(self.text_lines)):
					if not self.text_lines[line]:
						continue
					if self.debug:
						print("  %d: [%s]" %(line, self.text_lines[line]))
					if not simulate_mode:
						self.driver.lcd_display_string(self.text_lines[line],line+1)
			if not self.is_active and ((time.time() - self.last_active) > self.off_delay):
				self._off()
			time.sleep(1)

	def close(self):
		if not self.enabled:
			return
		self.terminate = True
		self.runthread.join()
		self._off()

	def _on(self):
		if self.debug:
			print("LCD backlight on")
		if not simulate_mode:
			self.driver.lcd_backlight(True)
		self.is_on = True

	def _off(self):
		if not self.is_on:
			return
		self.is_on = False
		if self.debug:
			print("LCD off")
		if not simulate_mode:
			self.driver.lcd_clear()
			self.driver.lcd_backlight(False)

if __name__ == '__main__':

	if len(sys.argv) < 3:
		print("Specify <update period> <total loops> [--debug]")

	else:
		config = { device.THE_DEVICE:{ "timeout_seconds":10, "num_lines":4, "address":"0x3f" } }
		update_period = int(sys.argv[1])
		total_loops = int(sys.argv[2])
		debug = len(sys.argv) > 3 and sys.argv[3] == "--debug"

		lcd = device(config)
		lcd.close()

		with device(config, debug) as m:
			for i in range(total_loops):
				m.text(1, "Line 1 %d" %(i))
				m.text(2, "Line 2 %d" %(i))
				m.text(3, "Line 3 %d" %(i))
				print("Sleeping")
				time.sleep(update_period)
		print("exit")
