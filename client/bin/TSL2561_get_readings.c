//	Copyright 2016 Paul Broadhead
//	Contact: pjbroad@twinmoons.org.uk
//
//	This file is part of pi_sensors.
//
//	pi_sensors is free software: you can redistribute it and/or modify
//	it under the terms of the GNU General Public License as published by
//	the Free Software Foundation, either version 3 of the License, or
//	(at your option) any later version.
//
//	pi_sensors is distributed in the hope that it will be useful,
//	but WITHOUT ANY WARRANTY; without even the implied warranty of
//	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//	GNU General Public License for more details.
//
//	You should have received a copy of the GNU General Public License
//	along with pi_sensors.  If not, see <http://www.gnu.org/licenses/>.

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <TSL2561.h>

/*
Based on https://github.com/amolyp/TSL2561_Simple_Library/blob/master/TSL2561_test_single_sensor.c

Compile using for exmaple:
export TSL2561_PATH=$HOME/code/sensors_dependencies/TSL2561_Simple_Library/
gcc -o TSL2561_get_readings -I$TSL2561_PATH TSL2561_get_readings.c $TSL2561_PATH/TSL2561.c
*/

int main(int argc, char *argv[])
{
	int rc;
	uint16_t broadband, ir;
	uint32_t lux=0;

	int controller = -1;

	if (argc < 2)
	{
		printf("Usage : %s <i2c contoller 0 or 1>\n", argv[0]);
		return 1;
	}
	else
		controller = atoi(argv[1]);

	// prepare the sensor
	// (the first parameter is the raspberry pi i2c master controller attached to the TSL2561, the second is the i2c selection jumper)
	// The i2c selection address can be one of: TSL2561_ADDR_LOW, TSL2561_ADDR_FLOAT or TSL2561_ADDR_HIGH
	TSL2561 light1 = TSL2561_INIT(controller, TSL2561_ADDR_FLOAT);
	
	// initialize the sensor
	rc = TSL2561_OPEN(&light1);
	if(rc != 0) {
		fprintf(stderr, "Error initializing TSL2561 sensor (%s). Check your i2c bus (es. i2cdetect)\n", strerror(light1.lasterr));
		// you don't need to TSL2561_CLOSE() if TSL2561_OPEN() failed, but it's safe doing it.
		TSL2561_CLOSE(&light1);
		return 1;
	}
	
	// set the gain to 1X (it can be TSL2561_GAIN_1X or TSL2561_GAIN_16X)
	// use 16X gain to get more precision in dark ambients, or enable auto gain below
	rc = TSL2561_SETGAIN(&light1, TSL2561_GAIN_1X);
	
	// set the integration time 
	// (TSL2561_INTEGRATIONTIME_402MS or TSL2561_INTEGRATIONTIME_101MS or TSL2561_INTEGRATIONTIME_13MS)
	// TSL2561_INTEGRATIONTIME_402MS is slower but more precise, TSL2561_INTEGRATIONTIME_13MS is very fast but not so precise
	rc = TSL2561_SETINTEGRATIONTIME(&light1, TSL2561_INTEGRATIONTIME_402MS);
	
	// sense the luminosity from the sensor (lux is the luminosity taken in "lux" measure units)
	// the last parameter can be 1 to enable library auto gain, or 0 to disable it
	rc = TSL2561_SENSELIGHT(&light1, &broadband, &ir, &lux, 1);

	printf("{\"TSL2561\":{\"broadband\":%i,\"ir\":%i,\"lux\":%i}}\n", broadband, ir, lux);
	
	TSL2561_CLOSE(&light1);
	
	return 0;
}
