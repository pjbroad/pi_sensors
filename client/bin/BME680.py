#! /usr/bin/env python

#	Copyright 2018 Paul Broadhead
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
from general_device import general_device

try:
	import bme680
	HAVE_DEVICE_DRIVER = True
except ImportError:
	HAVE_DEVICE_DRIVER = False


class device(general_device):

	THE_DEVICE = "BME680"

	def get_general(self):
		if self.read_count == 0:
			while not self.sensor.get_sensor_data() or not self.sensor.data.heat_stable:
				if self.debug:
					print("%s: waiting for data" %(self.THE_DEVICE))
				time.sleep(1)
		self.read_count += 1
		if self.read_count >= len(self.buffers):
			self.read_count = 0

	def get_temperature(self):
		self.get_general()
		return self.sensor.data.temperature

	def get_pressure(self):
		self.get_general()
		return self.sensor.data.pressure

	def get_humidity(self):
		self.get_general()
		return self.sensor.data.humidity

	# Air Quality Calculation heavily based on https://github.com/pimoroni/bme680/blob/master/examples/indoor-air-quality.py
	def calc_air_quality(self):
		self.get_general()
		if self.sensor.data.heat_stable:
			self.last_gas_resistance = self.sensor.data.gas_resistance
		elif self.debug:
			print("%s: gas resistance - heat not stable using last %.1f" %(self.THE_DEVICE, self.last_gas_resistance))
		hum_weighting = 0.25
		gas = float(self.last_gas_resistance)
		hum = float(self.sensor.data.humidity)
		gas_offset = self.gas_baseline - gas
		hum_offset = hum - self.hum_baseline
		if hum_offset > 0:
			hum_score = (100.0 - self.hum_baseline - hum_offset) / (100.0 - self.hum_baseline) * (hum_weighting * 100.0)
		else:
			hum_score = (self.hum_baseline + hum_offset) / self.hum_baseline * (hum_weighting * 100.0)
		if gas_offset > 0:
			gas_score = (gas / self.gas_baseline) * (100.0 - (hum_weighting * 100.0))
		else:
			gas_score = 100.0 - (hum_weighting * 100.0)
		air_quality_score = hum_score + gas_score
		return air_quality_score

	def get_gas_resistance(self):
		self.get_general()
		if self.sensor.data.heat_stable:
			self.last_gas_resistance = self.sensor.data.gas_resistance
		elif self.debug:
			print("%s: gas resistance - heat not stable using last %.1f" %(self.THE_DEVICE, self.last_gas_resistance))
		return self.last_gas_resistance

	def __init__(self, config, debug=False):
		super(device, self).__init__(self.THE_DEVICE, config, HAVE_DEVICE_DRIVER, debug)
		if not self.enabled:
			return

		self.read_count = 0
		self.last_gas_resistance = 0
		self.gas_baseline = config[self.THE_DEVICE]["gas_baseline"]
		self.hum_baseline = config[self.THE_DEVICE]["humidity_baseline"]

		self.sensor = bme680.BME680()

		oversample = { "OS_NONE":bme680.OS_NONE, "OS_1X":bme680.OS_1X, "OS_2X":bme680.OS_2X, "OS_4X":bme680.OS_4X, "OS_8X":bme680.OS_8X, "OS_16X":bme680.OS_16X }
		self.sensor.set_humidity_oversample(oversample[config[self.THE_DEVICE].get("humidity_oversample","OS_2X")])
		self.sensor.set_pressure_oversample(oversample[config[self.THE_DEVICE].get("pressure_oversample","OS_4X")])
		self.sensor.set_temperature_oversample(oversample[config[self.THE_DEVICE].get("temperature_oversample","OS_8X")])

		filters = { "FILTER_SIZE_0":bme680.FILTER_SIZE_0, "FILTER_SIZE_1":bme680.FILTER_SIZE_1,
			"FILTER_SIZE_3":bme680.FILTER_SIZE_3, "FILTER_SIZE_7":bme680.FILTER_SIZE_7,
			"FILTER_SIZE_15":bme680.FILTER_SIZE_15, "FILTER_SIZE_31":bme680.FILTER_SIZE_31,
			"FILTER_SIZE_63":bme680.FILTER_SIZE_63, "FILTER_SIZE_127":bme680.FILTER_SIZE_127 }
		self.sensor.set_filter(filters[config[self.THE_DEVICE].get("filter_size","FILTER_SIZE_3")])

		gas_measurement = { "DISABLE_GAS_MEAS":bme680.DISABLE_GAS_MEAS, "ENABLE_GAS_MEAS":bme680.ENABLE_GAS_MEAS }
		self.sensor.set_gas_status(gas_measurement[config[self.THE_DEVICE].get("gas_measurement","ENABLE_GAS_MEAS")])

		self.sensor.set_gas_heater_temperature(config[self.THE_DEVICE].get("heater_temperature",320))
		self.sensor.set_gas_heater_duration(config[self.THE_DEVICE].get("heater_duration",150))
		self.sensor.select_gas_heater_profile(config[self.THE_DEVICE].get("heater_profile",0))

		self.add_reading("temperature", "Temperature %.1f C", "C", self.get_temperature)
		self.add_reading("pressure", "%.1fPa", "Pa", self.get_pressure, scale=100.0)
		self.add_reading("humidity", "%.1f%%rH", "%rH", self.get_humidity)
		self.add_reading("gas-resistance", "%.1fOhms", "Ohms", self.get_gas_resistance)
		self.add_reading("air-quality", "%0.1f%%", "%", self.calc_air_quality)

if __name__ == '__main__':

	if len(sys.argv) < 3:
		print("Specify <send time period> <total sends> [--debug]")
	else:
		debug = len(sys.argv) > 3 and sys.argv[3] == "--debug"
		config = { device.THE_DEVICE: { "average_over":3, "read_period":5, "gas_baseline":500000.0, "humidity_baseline":40.0 } }
		with device(config, debug) as d:
			d.test(int(sys.argv[1]), int(sys.argv[2]))

