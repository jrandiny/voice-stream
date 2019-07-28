from config import *
import time
import json

def gen_payload(payload, name):
  data = {}
  data["type"] = payload["TYPE"]
  data["version"] = payload["VERSION"]
  data["name"] = name
  data["time"] = int(time.time())
  data["port"] = COMM_PORT

  return json.dumps(data)