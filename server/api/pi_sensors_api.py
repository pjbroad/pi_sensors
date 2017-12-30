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
config_collection = db.database.config
app = flask.Flask(__name__)


@app.route("/<room>/<sensor>/latest", methods=['GET'])
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


@app.route("/distinct/<the_info>", methods=['GET'])
def info(the_info):
	try:
		return common.format_success(list(readings_collection.distinct(the_info)))
	except Exception, e:
		return common.format_error("Failed to get distinct [%s] [%s]" %(the_info, str(e)))


@app.route("/<room>/distinct/<the_info>", methods=['GET'])
def room_info(room, the_info):
	# use format compatable with older pymongo
	try:
		return common.format_success({"room":room, the_info: list(readings_collection.find({"room":room}).distinct(the_info))})
	except Exception, e:
		return common.format_error("Failed to get room info [%s]" %(str(e)))


@app.route("/option/<option>", methods=['GET', 'POST', "DELETE"])
def room_option(option):
	if not option:
		return common.format_error("Need an option name")
	if flask.request.method == 'GET':
		try:
			rec = config_collection.find_one({ "type": "option", "name": option }, {"_id":0, "type":0} )
		except Exception, e:
			return common.format_error("Failed to get options <%s> [%s]" %(option, str(e)))
		return common.format_success(rec)
	elif flask.request.method == 'POST':
		record = {"type": "option", "name": option}
		data = flask.request.get_json(force=True, silent=True, cache=False)
		if data:
			record["value"] = data
		try:
			config_collection.update({"type": "option", "name": option}, record, upsert=True)
		except Exception, e:
			return common.format_error("Failed to update options <%s> [%s]" %(option, str(e)))
		return common.format_success(None)
	elif flask.request.method == 'DELETE':
		try:
			rec = config_collection.remove({ "type": "option", "name": option })
		except Exception, e:
			return common.format_error("Failed to delete options <%s> [%s]" %(option, str(e)))
		return common.format_success(None)
	else:
		return common.format_errors("Invalid method for options %s" %(flask.request.method))


@app.route("/room_list", methods=['GET', 'DELETE'])
def room_list():
	if flask.request.method == 'GET':
		try:
			rooms = list(config_collection.distinct("name", {"type": "room"}))
		except Exception, e:
			return common.format_error("Failed to get rooms list [%s]" %(str(e)))
		rooms.sort()
		return common.format_success(rooms)
	elif flask.request.method == 'DELETE':
		try:
			config_collection.remove({"type": "room"})
		except Exception, e:
			return common.format_error("Failed to delete rooms list [%s]" %(str(e)))
		return common.format_success(None)
	else:
		return common.format_errors("Invalid method room list %s" %(flask.request.method))


@app.route("/<room>/type_list", methods=['GET', 'POST'])
def type_list(room):
	if flask.request.method == 'GET':
		try:
			rec = config_collection.find_one({"$query": { "type": "room", "name": room }})
		except Exception, e:
			return common.format_error("Failed to read room types <%s> [%s]" %(room, str(e)))
		if rec:
			types = rec.get("types",[])
			types.sort(reverse=True)
			return common.format_success(types)
		else:
			return common.format_success([])
	elif flask.request.method == 'POST':
		data = flask.request.get_json(force=True, silent=True, cache=False)
		if type(data) is dict and "types" in data and len(data["types"]) > 0:
			try:
				config_collection.remove({ "type": "room", "name": room })
			except Exception, e:
				return common.format_error("Failed to remove existing room type list <%s> [%s]" %(room, str(e)))
			try:
				config_collection.insert({"type": "room", "name": room, "types": data["types"]})
			except Exception, e:
				return common.format_error("Failed to insert room type list <%s> [%s]" %(room, str(e)))
			return common.format_success(None)
		else:
			return common.format_error("Invalid data for room types list <%s>" %(room))
	else:
		return common.format_errors("Invalid method for room types list <%s> %s" %(room, flask.request.method))


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

	# if manually generated room list, return now
	try:
		rec = config_collection.find_one({ "type": "option", "name": "manual" } )
	except Exception, e:
		return common.format_error("Failed to get manu option [%s]" %(str(e)))
	if rec and rec.get("name", None) == "manual" and rec.get("value", False):
		return common.format_success(None)

	# if room not in rooms collection, add it with the type
	try:
		rec = config_collection.find_one({"$query": { "type": "room", "name": data["room"] }})
	except Exception, e:
		return common.format_error("Failed to read room collection [%s]" %(str(e)))
	if not rec:
		try:
			config_collection.insert({"type": "room", "name": data["room"], "types": [data["type"]]})
		except Exception, e:
			return common.format_error("Failed to insert room to collection [%s]" %(str(e)))
	# if room already exists, add type if not already there
	else:
		if not data["type"] in rec["types"]:
			rec["types"].append(data["type"])
			try:
				config_collection.update({ "_id": rec["_id"] }, {"$set": { "types": rec["types"]} })
			except Exception, e:
				return common.format_error("Failed to update room collection [%s]" %(str(e)))

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
