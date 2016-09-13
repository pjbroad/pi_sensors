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
import requests
import sys
import time

class device(object):

	THE_DEVICE = "OWM"

	def __init__(self, config, debug):
		self.raw_data = None
		if not self.THE_DEVICE in config:
			self.enabled = False
			if debug:
				print("%s disabled" %(self.THE_DEVICE))
			return
		self.enabled = True
		config = config[self.THE_DEVICE]
		ids = ""
		for i in config["ids"]:
			ids += str(i) + ","
		ids = ids.strip(",")
		self.url = config["url"] + "?id=" + ids + "&" + "APPID=" + config["APPID"]
		if "units" in config:
			self.temp_units = {"metric":"C", "imperial":"F"}.get(config["units"],"?")
			self.url += "&units=" + config["units"]
		else:
			self.temp_units = "K"
		self.save_raw = config.get("save_raw", False)
		self.raw_file = config.get("raw_file", None)

	def update_raw(self):
		if not self.enabled:
			return
		if self.raw_file:
			self._log("using file not live [%s]" %(self.raw_file))
			lines  = open(self.raw_file,"r").readlines()
			self.raw_data = json.loads(lines[-1])
			return
		successful = False
		try:
			r = requests.get(self.url)
		except requests.exceptions.ConnectionError:
			self._log("send failed to connect ....")
		except:
			self._log("unknown send failed ....")
		else:
			if not r.status_code == 200:
				self._log("send error code %d" %(r.status_code))
			elif r.json().get("cnt", 0) < 1:
				self._log("invalid response [%s]" %r.json())
			else:
				successful = True
			if successful:
				self.raw_data = r.json()
			else:
				self.raw_data = None

	def get_readings(self):
		if not self.enabled or not self.raw_data or not "list" in self.raw_data:
			return []
		records = []
		for entry in self.raw_data["list"]:
			location = entry["name"].lower()
			main = entry["main"]
			records.append((location, {"type":"temperature", "record":{"value":main["temp"], "units":self.temp_units, "values":{"max":main["temp_max"] , "mean":main["temp"], "min":main["temp_min"]}, "device":self.THE_DEVICE}}))
			records.append((location, {"type":"pressure", "record":{"value":main["pressure"]*100.0, "units":"Pa", "device":self.THE_DEVICE}}))
			records.append((location, {"type":"humidity", "record":{"value":main["humidity"], "units":"%rH", "device":self.THE_DEVICE}}))
		return records

	def get_raw(self):
		return self.raw_data

	def close(self):
		None

	def _log(self, message):
		print("%s: %s: %s" %(time.asctime(), self.THE_DEVICE, message))

	def __enter__(self):
		return self

	def __exit__(self, exct_type, exce_value, traceback):
		None

if __name__ == '__main__':

	if len(sys.argv) < 2:
		print("Specify <live | old record file (json)> [--debug]")
	else:

		debug = len(sys.argv) > 2 and sys.argv[2] == "--debug"
		if sys.argv[1] == "live":
			filename = None
		else:
			filename = sys.argv[1]

		config = { device.THE_DEVICE: {"url":"http://api.openweathermap.org/data/2.5/group",
				"raw_file":filename, "save_raw": False, "units":"metric",
				"ids":[2643743,5128581], "APPID":"your-API-key>" } }

		with device(config, debug) as d:
			d.update_raw()
			print(json.dumps(d.get_raw(), separators=(',',':')))
			print(json.dumps(d.get_readings(), separators=(',',':')))
