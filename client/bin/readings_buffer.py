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

class readings_buffer:

	def __init__(self, thetype, format_string, units, value_function, scale, average_over, read_period, device_tag="", debug=False):
		self.thetype = thetype
		self.format_string = format_string
		self.units = units
		self.value_function = value_function
		self.scale = scale
		self.average_over = average_over
		self.read_period = read_period
		self.device_tag = device_tag
		self.debug = debug
		self.readings = []

	def is_empty(self):
		return len(self.readings) == 0

	def add(self):
		self.readings.append(self.value_function() * self.scale)
		if self.debug:
			print(len(self.readings), ' '.join(format(f, ".2f") for f in self.readings[-self.average_over:]))

	def get_mean(self):
		v = self.readings[-self.average_over:]
		return round((sum(v)/float(len(v))),1)

	def get_max(self):
		return round(max(self.readings),1)
	
	def get_min(self):
		return round(min(self.readings),1)

	def get_values(self):
		return {"max":self.get_max(), "mean":self.get_mean(), "min":self.get_min()}
	
	def get_units(self):
		return self.units

	def get_format_string(self):
		return self.format_string

	def get_type(self):
		return self.thetype

	def get_tag(self):
		return self.device_tag

	def truncate(self):
		self.readings = self.readings[-self.average_over:]

if __name__ == '__main__':

	buf = readings_buffer("tester", "X", None, 1, 2, 2, True)
 
