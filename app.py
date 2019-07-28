from queue import Queue
import pyaudio
import socket
import threading
import sys
import time

from config import *
from util import gen_payload
import command
import discovery

# Setup thread
command_queue = Queue()
connect_queue = Queue()

is_running = threading.Event()
discovery_listener_running = threading.Event()
discovery_broadcast_running = threading.Event()

is_running.set()
discovery_listener_running.set()
discovery_broadcast_running.clear()

input_thread = threading.Thread(target=command.worker, args=(command_queue, is_running ))
listener_thread  = threading.Thread(target=discovery.listener, args=(connect_queue, is_running, discovery_listener_running))
broadcast_thread = threading.Thread(target=discovery.broadcast, args=(is_running, discovery_broadcast_running))

# Setup audio
p = pyaudio.PyAudio()

chosen_device_index = 0
if(p.get_device_count()>=1):
  for x in range(0,p.get_device_count()):
    info = p.get_device_info_by_index(x)
    if info["name"] == "pulse":
      chosen_device_index = info["index"]

stream = p.open(format=p.get_format_from_width(WIDTH),
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                input_device_index=chosen_device_index,
                frames_per_buffer=CHUNK)

# Setup network
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("",COMM_PORT))
sock.setblocking(False)

input_thread.start()
listener_thread.start()
broadcast_thread.start()

# Setup state
sending_audio = False
receiving_audio = False
play_audio = True

connection_list = []

while True:
  # Audio sending
  if(sending_audio):
    data = stream.read(CHUNK)
    for addr in connection_list:
      sock.sendto(data, addr)

  # Audio receiving
  if(receiving_audio):
    try:
      data, addr = sock.recvfrom(CHUNK * 4)
      if (play_audio):
        stream.write(data, CHUNK)
    except socket.error:
      pass

  # Connect request processor
  if (not connect_queue.empty()):
    addr = connect_queue.get()
    if(addr not in connection_list):
      connection_list.append(addr)
    connect_queue.task_done()

  # Command processor
  if (not command_queue.empty()):
    command = command_queue.get().split(" ")

    # Quit app
    if (command[0] == "exit"):
      break
    # Start server
    elif (command[0] == "serve"):
      play_audio = False
      sending_audio = True
      receiving_audio = True
      discovery_broadcast_running.set()
    # Connect to server
    elif (command[0] == "connect"):
      # Check for configuration
      socket_ip = "127.0.0.1"
      socket_port = 56789
      if(len(command)>=3):
        socket_ip = command[1]
        socket_port = int(command[2])
      else:
        print("Discovered server:")
        for name,addr in discovery.discovered_list.items():
          print("{} on {}:{}".format(name,addr[0],addr[1]))

        hostname = ""

        while (hostname not in discovery.discovered_list):
          hostname = input("Hostname : ")

        socket_ip = discovery.discovered_list[hostname][0]
        socket_port = discovery.discovered_list[hostname][1]

      # Setup
      play_audio = True
      sending_audio = True
      receiving_audio = True
      # Connect to remote
      print("Connecting to {}:{}".format(socket_ip, socket_port))  
      connect_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      connect_socket.sendto(gen_payload(SIGNALING_CONNECT).encode(),(socket_ip, SIGNALING_PORT))
      connect_socket.close()
      if((socket_ip, socket_port) not in connection_list):
        connection_list.append((socket_ip, socket_port))
    # Stop sending and receiving
    elif (command[0] == "stop"):
      sending_audio = False
      receiving_audio = False
      discovery_broadcast_running.clear()
      connection_list = []
    # Connection and audio info
    elif (command[0] == "info"):
      print("Connected - in") if (receiving_audio) else print("Disconnected - in")
      print("Connected - out") if (sending_audio) else print("Disconnected - out")
      print("Audio muted") if (not play_audio) else print("Audio not muted")
    # Audio setting
    elif (command[0] == "mute"):
      play_audio = False
    elif (command[0] == "unmute"):
      play_audio = True
    # Help
    else:
      print("Command")
      print("exit                - Exit app")
      print("serve               - Start server")
      print("connect             - Interactive connect (recommended)")
      print("connect <ip> <port> - Connect to specific ip port")
      print("stop                - Stop connection")
      print("mute                - Mute other party")
      print("listen              - Unmute other party")
      print("info                - Print current status")
    
    command_queue.task_done()

print("Exiting")

# Signaling thread
is_running.clear()
discovery_listener_running.clear()
discovery_broadcast_running.clear()

command_queue.task_done()

# Closing socket
sock.close()

# Closing audio
stream.stop_stream()
stream.close()

p.terminate()

# Wait for thread
broadcast_thread.join()
input_thread.join()
listener_thread.join()