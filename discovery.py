import time
import socket
import json

DISCOVERY_PORT = 56789
DISCOVERY_TYPE = "vs-discover"
DISCOVERY_VERSION = 1


def listener(command_queue, run_loop, name):
  listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  listener_socket.setblocking(False)
  listener_socket.bind(("", DISCOVERY_PORT))
  while (run_loop.is_set()):
    try:
      data, addr = listener_socket.recvfrom(65515)
      json_data = json.loads(data)
      if (json_data["type"] == DISCOVERY_TYPE
          and json_data["version"] == DISCOVERY_VERSION
          and json_data["name"] != name):
        print("discover ", json_data["name"])
    except socket.error:
      pass
    except json.decoder.JSONDecodeError:
      pass


def broadcast(run_loop, name):
  broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  while (run_loop.is_set()):
    data = {}
    data["type"] = DISCOVERY_TYPE
    data["version"] = DISCOVERY_VERSION
    data["name"] = name
    data["time"] = int(time.time())
    broadcast_socket.sendto(
        json.dumps(data).encode(), ('<broadcast>', DISCOVERY_PORT))
    time.sleep(2)
