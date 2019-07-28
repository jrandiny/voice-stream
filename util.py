from config import *
import time
import json

def gen_payload(payload_type):
  data = {}
  data["type"] = payload_type
  data["version"] = SIGNALING_VERSION,
  data["name"] = SIGNALING_NAME
  data["time"] = int(time.time())
  data["port"] = COMM_PORT

  return json.dumps(data)