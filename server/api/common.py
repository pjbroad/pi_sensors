#! /usr/bin/env python

#	Copyright 2016 Paul Broadhead
#	Contact: pjbroad@twinmoons.org.uk
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import pymongo
import json
import time

def get_config(config_file = os.path.join(os.path.dirname(__file__), "..", "config/mongodb_config.json")):
	if os.path.isfile(config_file):
		return json.load(open(config_file))
	else:
		return { "hostname": "localhost", "port": 27017, "username": None, "password": None, "db_name": None }

def format_error(message):
	return json.dumps({"status":False, "message":message}, separators=(',',':'), indent=4)

def format_success(data):
	return json.dumps({"status":True, "data":data}, separators=(',',':'), indent=4)

def get_dates(args):
	today = time.strftime("%Y%m%d", time.localtime())
	start_date_str = args.get("start_date",today)
	end_date_str = args.get("end_date",None)
	if not start_date_str.isdigit():
		return (None, None, "Invalid start_date")
	start_date = int(start_date_str)
	if end_date_str and not end_date_str.isdigit():
		return (None, None, "Invalid end_date")
	if end_date_str:
		end_date = int(end_date_str)
	else:
		end_date = start_date+1
	return (start_date, end_date, None)

class db:
	def __init__(self):
		versionstr = pymongo.version.split(".")
		self.version = float(versionstr[0] + "." + versionstr[1])
		self.config = get_config()
		self.client = pymongo.MongoClient(self.config["hostname"], self.config["port"])
		if "username" in self.config and "password" in self.config and self.config["username"] and self.config["password"]:
			self.client[self.config["db_name"]].authenticate(self.config["username"], self.config["password"])
		self.database = self.client[self.config["db_name"]]

if __name__ == '__main__':
	print(json.dumps(get_config(), separators=(',',':'), indent=4))
