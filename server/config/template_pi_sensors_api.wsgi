import sys
import logging

sys.path.insert(0, "###path-to-api###")

from pi_sensors_api import app as application

logging.basicConfig(stream=sys.stderr)
