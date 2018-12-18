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
import json

def get(config_file = os.path.join(os.path.dirname(__file__), "..", "config/pi_config.json")):
	if os.path.isfile(config_file):
		return json.load(open(config_file))
	else:
		return	{
					"debug": False,
					"room":"testroom",
					"servers" : [
						{"tmp_dir":"~/spool_pi_sensors", "hostname":"server1", "url":"https://server1/pi_sensors_api/", "certfile":"../config/server1.cert"},
						{"tmp_dir":"~/spool_pi_sensors", "hostname":"server2", "url":"https://server2/pi_sensors_api/", "certfile":"../config/server2.cert"} ],
					"LCD": { "address":"0x3f", "timeout_seconds":30, "num_lines":4 },
					"OWM": { "save_raw": False, "raw_file":None, "units":"metric",
								"ids":[2643743, 5128581], "APPID":None,
								"url":"http://api.openweathermap.org/data/2.5/group" },
					"RCW0506": { "GPIO":4 },
					"TSL2561": { "i2c Controller":1, "average_over":3, "read_period":10, "exec_path":"./TSL2561_get_readings" },
					"BMP180": { "average_over":3, "read_period":10 },
					"MCP9808": { "average_over":3, "read_period":10 },
					"SenseHat": { "average_over":3, "read_period":10, "show_message_on":"middle" },
					"DS18B20": { "average_over":3, "read_period":10 },
					"BME280": { "mode":"BME280_OSAMPLE_1", "average_over":3, "read_period":10 },
					"BME680": { "average_over":3, "read_period":10, "gas_baseline":500000.0, "humidity_baseline":40.0 },
					"DHT": { "average_over":3, "read_period":10, "type":"22", "pin":22 }
				}

if __name__ == '__main__':
	print(json.dumps(get(), separators=(',',':'), indent=4))
