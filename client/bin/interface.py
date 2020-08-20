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

import os
import time
import requests
import json
import pi_config

class sender:

	def __init__(self, config):
		self.hostname = config["hostname"]
		self.url = config["url"]
		self.certfile = config.get("certfile",None)
		self.username = config.get("username",None)
		self.password = config.get("password",None)
		tmp_dir = os.path.expanduser(config["tmp_dir"])
		if not os.path.exists(tmp_dir):
			os.makedirs(tmp_dir)
		self.buffered_file = os.path.join(tmp_dir, "buffered_%s" %(self.hostname))
		self.retry_file = os.path.join(tmp_dir, "retry_%s" %(self.hostname))
		self.have_unsent = self._line_count() != 0

	def _log(self, message):
		print("%s: %s: sender class: %s" %(time.asctime(), self.hostname, message))

	def _line_count(self):
		if os.path.exists(self.buffered_file):
			return len(open(self.buffered_file, "r").readlines())
		else:
			return 0

	def add_reading(self, room, data):
		for check in ["type", "record" ]:
			if not check in data:
				self._log("missing field [%s]" %(check))
				return
		for check in ["value", "device" ]:
			if not check in data["record"]:
				self._log("missing field [%s] in record" %(check))
				return
		else:
			now = time.localtime()
			epoch = time.mktime(now)
			thedate = int(time.strftime("%Y%m%d", now))
			self._save("add_reading", { "date":thedate, "epoch":epoch, 'type':data["type"], "room":room, "record":data["record"]} )

	def add_raw_weather(self, data):
		if data:
			self._save("add_raw_weather", data)

	def _save(self, url_function, data ):
		with open(self.buffered_file, "a") as fid:
			fid.write("%s\n"%(json.dumps({"url":self.url+url_function, "data":data})))

	def send(self):
		if not os.path.exists(self.buffered_file):
			return
		with open(self.buffered_file, "r") as buffered, open(self.retry_file, "w") as failed:
			failed_already_urls = {}
			session = requests.Session()
			if self.username and self.password:
				session.auth = (self.username, self.password)
			for line in buffered.readlines():
				data = json.loads(line)
				url = data["url"]
				if url in failed_already_urls:
					# if already failed this url, do not try again this time else we could take too long
					failed.write("%s\n"%(json.dumps(data)))
					continue
				payload = data["data"]
				successful = False
				try:
					r = session.post(url, verify=self.certfile, data=json.dumps(payload), timeout=5)
				except requests.exceptions.ConnectionError, err:
					self._log("send failed to connect ....")
					self._log(err)
				except requests.exceptions.Timeout, err:
					self._log("send timed out ....")
					self._log(err)
				except Exception, err:
					self._log("send failed with unexpected error ....")
					self._log(err)
				else:
					if not r.status_code == 200:
						self._log("post error code %d" %(r.status_code))
					elif not r.json().get("status", False):
						self._log("invalid response [%s]" %r.json())
					else:
						successful = True
				if not successful:
					self._log("failed [%s] so will not try again this time" %(url))
					failed.write("%s\n"%(json.dumps(data)))
					failed_already_urls[url] = True
		os.remove(self.buffered_file)
		os.rename(self.retry_file, self.buffered_file)
		num_lines = self._line_count()
		if num_lines:
			self._log("have %d records to retry next time" %(num_lines))
			self.have_unsent = True
		else:
			if self.have_unsent:
				self._log("cleared previously unsent")
				self.have_unsent = False


if __name__ == '__main__':

	config = pi_config.get()
	print(json.dumps(config))
	servers = []
	for server_config in config["servers"]:
		servers.append(sender(server_config))

	for server in servers:
		server.add_reading("testing", {}, )
		server.add_reading("testing", {"type":"testtype"})
		server.add_reading("testing", {"record":{"value": 42}})
		server.add_reading("testing", {"type":"testtype", "record":{"value": 42}})
		server.add_reading("testing", {"type":"testtype", "record":{"value": 41, "device":"virtual"}})
		server.add_reading("testing", {"type":"testtype", "record":{"value": 42, "device":"virtual"}})
		server.add_reading("testing", {"type":"testtype", "record":{"value": 43, "device":"virtual"}})
		server.send()
