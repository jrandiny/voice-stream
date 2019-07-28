import time
import socket
import json
from config import *
from util import gen_payload

discovered_list = {}

def listener(command_queue, run_loop, do_loop, name):
  while(run_loop.is_set()):
    if(do_loop.is_set()):
      listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      listener_socket.setblocking(False)
      listener_socket.bind(("", DISCOVERY_SOCK["PORT"]))
      while (do_loop.is_set()):
        try:
          data, addr = listener_socket.recvfrom(65515)
          json_data = json.loads(data)
          if (json_data["version"] == DISCOVERY_SOCK["VERSION"]
              and json_data["name"] != name):
            if(json_data["type"] == DISCOVERY_SOCK["TYPE"]):
              if (json_data["name"] not in discovered_list):
                print("discovered {} on {}:{}".format(json_data["name"],addr[0],json_data["port"]))
                discovered_list[json_data["name"]] = (addr[0], json_data["port"])
                print(discovered_list)
            elif(json_data["type"] == CONNECT_SOCK["TYPE"]):
              command_queue.put((addr[0],json_data["port"]))
        except socket.error:
          pass
        except json.decoder.JSONDecodeError:
          pass
        except KeyError:
          pass
      listener_socket.close()

def broadcast(run_loop, do_loop, name):
  while(run_loop.is_set()):
    if(do_loop.is_set()):
      broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      while (do_loop.is_set()):
        broadcast_socket.sendto(
            gen_payload(DISCOVERY_SOCK, name).encode(), ('<broadcast>', DISCOVERY_SOCK["PORT"]))
        time.sleep(2)
      broadcast_socket.close()
