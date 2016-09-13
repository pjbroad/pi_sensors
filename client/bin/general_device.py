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
from readings_buffer import readings_buffer

class general_device(object):

	def __init__(self, thedevice, config, have_deps, debug=False):
		self.device = thedevice
		self.debug = debug
		if (not self.device in config) or (not have_deps):
			if self.debug:
				print("%s disabled" %(self.device))
			self.enabled = False
			return
		self.enabled = True
		self.average_over = config[self.device]["average_over"]
		self.read_period = config[self.device]["read_period"]
		self.buffers = []
		self.mutex = threading.Lock()
		self.keep_running = True
		self.runthread = threading.Thread(target=self.__run)
		self.runthread.start()

	def __enter__(self):
		return self

	def __exit__(self, exct_type, exce_value, traceback):
		self.close()

	def __run(self):
		while self.keep_running:
			with self.mutex:
				for i in range(len(self.buffers)):
					self.buffers[i].add()
			for i in range(self.read_period):
				if not self.keep_running:
					break
				time.sleep(1)

	def add_reading(self, sensor, format_string, units, value_function, scale=1.0, device_tag=""):
		self.buffers.append(readings_buffer(sensor, format_string, units, value_function, scale, self.average_over, self.read_period, device_tag, self.debug))

	def close(self):
		if self.enabled:
			self.keep_running = False
			self.runthread.join()

	def current(self):
		if not self.enabled:
			return None
		for buf in self.buffers:
			if buf.is_empty():
				return None
		values = []
		with self.mutex:
			for buf in self.buffers:
				values.append(buf.get_mean())
		return values

	def summary(self):
		if not self.enabled:
			return "%s disabled" %(self.device)
		values = self.current()
		if not values:
			return "%s ?" %(self.device)
		else:
			thetext = ""
			for i in range(len(values)):
				if self.buffers[i].get_format_string():
					thetext += self.buffers[i].get_format_string() %(values[i]) + " "
			return thetext.rstrip()

	def get(self):
		if not self.enabled:
			return []
		for buf in self.buffers:
			if buf.is_empty():
				return []
		records = []
		with self.mutex:
			for buf in self.buffers:
				data = {"record":{}}
				data["type"] = buf.get_type()
				data["record"]["value"] = buf.get_mean()
				if buf.get_units():
					data["record"]["units"] = buf.get_units()
				data["record"]["values"] = buf.get_values()
				data["record"]["device"] = self.device + buf.get_tag()
				records.append(data)
				buf.truncate()
		return records

	def test(self, send_time_period, total_sends):
		print("Testing %s" %(self.device))
		for i in range(total_sends):
			for j in range(send_time_period):
				print(self.current(), self.summary())
				time.sleep(1)
			print("record", self.get())
		print("exit")

if __name__ == '__main__':

	with general_device("Test General Device", {}, True, True) as dg:
		pass
