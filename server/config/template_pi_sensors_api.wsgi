import sys

sys.path.insert(0, "###path-to-api###")

from pi_sensors_api import app as application

sys.stdout = sys.stderr
