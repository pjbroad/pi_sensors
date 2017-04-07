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
import flask
import common
import sys


db = common.db()
readings_collection = db.database.readings
raw_weather_collection = db.database.raw_weather
app = flask.Flask(__name__)


@app.route("/<room>/<sensor>/latest")
def latest(room, sensor):
	yesterday = int(time.strftime("%Y%m%d", time.localtime(time.time()-24*60*60)))
	day_query = { "date": {"$gte":yesterday }, "type":sensor, "room":room }
	data = []
	for device in list(readings_collection.find(day_query).distinct("record.device")):
		day_query["record.device"] = device
		try:
			data.append({"device":device, "record":readings_collection.find_one({ "$query": day_query, "$orderby": { "epoch" : -1 } }, {"_id": False})})
		except Exception, e:
			return common.format_error("Failed to get latest [%s]" %(str(e)))
	return common.format_success(data)


@app.route("/<room>/<sensor>/maxminperday", methods=['GET'])
def maxminperday(room, sensor):
	start_date, end_date, message = common.get_dates(flask.request.args)
	if message:
		return common.format_error(message)
	day_query = { "date": {"$gte":start_date, "$lt":end_date }, "type":sensor, "room":room }
	data = []
	for device in list(readings_collection.find(day_query).distinct("record.device")):
		day_query["record.device"] = device
		try:
			if db.version < 3.0:
				data.append({"device":device, "dates":readings_collection.aggregate([{"$match":day_query},
					{"$group":{"_id":"$date", "min":{"$min":"$record.value"},"max":{"$max":"$record.value"}}}])["result"]})
			else:
				data.append({"device":device, "dates":list(readings_collection.aggregate([{"$match":day_query},
					{"$group":{"_id":"$date", "min":{"$min":"$record.value"},"max":{"$max":"$record.value"}}}]))})
		except Exception, e:
			return common.format_error("Failed to get maxminperday [%s]" %(str(e)))
	return common.format_success(data)


@app.route("/<room>/<sensor>/maxmin", methods=['GET'])
def maxmin(room, sensor):
	start_date, end_date, message = common.get_dates(flask.request.args)
	if message:
		return common.format_error(message)
	day_query = { "date": {"$gte":start_date, "$lt":end_date }, "type":sensor, "room":room }
	try:
		if db.version < 3.0:
			data = readings_collection.aggregate([{"$match":day_query},
				{"$group":{"_id":"$record.device", "min":{"$min":"$record.value"},"max":{"$max":"$record.value"}}}])["result"]
		else:
			data = list(readings_collection.aggregate([{"$match":day_query},
				{"$group":{"_id":"$record.device", "min":{"$min":"$record.value"},"max":{"$max":"$record.value"}}}]))
	except Exception, e:
		return common.format_error("Failed to get maxmin [%s]" %(str(e)))
	return common.format_success(data)


@app.route("/<room>/<sensor>/get_readings", methods=['GET'])
def get_readings(room, sensor):
	start_date, end_date, message = common.get_dates(flask.request.args)
	if message:
		return common.format_error(message)
	day_query = { "date": {"$gte":start_date, "$lt":end_date }, "type":sensor, "room":room }
	try:
		return common.format_success( list(readings_collection.find({ "$query": day_query, "$orderby": { "epoch" : -1 } }, {"_id": False})) )
	except Exception, e:
		return common.format_error("Failed to get readings [%s]" %(str(e)))


@app.route("/distinct/<the_info>")
def info(the_info):
	try:
		return common.format_success(list(readings_collection.distinct(the_info)))
	except Exception, e:
		return common.format_error("Failed to get distinct [%s] [%s]" %(the_info, str(e)))


@app.route("/<room>/distinct/<the_info>")
def room_info(room, the_info):
	# use format compatable with older pymongo
	try:
		return common.format_success(list(readings_collection.find({"room":room}).distinct(the_info)))
	except Exception, e:
		return common.format_error("Failed to get room info [%s]" %(str(e)))


@app.route('/add_reading', methods=['POST'])
def add_reading():
	data = flask.request.get_json(force=True, silent=True, cache=False)
	needed = [ "type", "record", "date", "room", "epoch" ]
	for key in needed:
		if not key in data:
			return common.format_error("Missing [%s] when adding record" %(key))
	try:
		readings_collection.insert(data)
	except Exception, e:
		return common.format_error("Failed to insert reading to dB [%s]" %(str(e)))
	return common.format_success(None)


@app.route('/add_raw_weather', methods=['POST'])
def add_raw_weather():
	data = flask.request.get_json(force=True, silent=True, cache=False)
	needed = [ "cnt", "list" ]
	for key in needed:
		if not key in data:
			return common.format_error("Missing [%s] when adding raw weather" %(key))
	if data['cnt'] < 1:
		return common.format_error("Count is zero when adding raw weather" %(key))
	for record in data['list']:
		try:
			raw_weather_collection.insert(record)
		except Exception, e:
			return common.format_error("Failed to insert raw weather to dB [%s]" %(str(e)))
	return common.format_success(None)


if __name__ == "__main__":
	the_debug = False
	the_host = '127.0.0.0'
	if len(sys.argv) > 2:
		if sys.argv[1] == "debug":
			the_debug = True
		if sys.argv[2] == "external":
			the_host = '0.0.0.0'
		app.run(debug=the_debug, host=the_host)
	else:
		app.run(debug=True, host='localhost')
