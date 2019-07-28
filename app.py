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

def start_discovery_broadcast():
  discovery_broadcast_running.set()

def stop_discovery_broadcast():
  discovery_broadcast_running.clear()

command_queue = Queue()
connect_queue = Queue()

is_running = threading.Event()
discovery_listener_running = threading.Event()
discovery_broadcast_running = threading.Event()

is_running.set()
discovery_listener_running.set()
discovery_broadcast_running.clear()

input_thread = threading.Thread(target=command.worker, args=(command_queue, is_running ))
listener_thread  = threading.Thread(target=discovery.listener, args=(connect_queue, is_running, discovery_listener_running, socket.gethostname()))
broadcast_thread = threading.Thread(target=discovery.broadcast, args=(is_running, discovery_broadcast_running, socket.gethostname()))

p = pyaudio.PyAudio()

chosen_device_index = 0
if(p.get_device_count()>=1):
  for x in range(0,p.get_device_count()):
    info = p.get_device_info_by_index(x)
    if info["name"] == "pulse":
      chosen_device_index = info["index"]

CHUNK = 1024
WIDTH = 2
CHANNELS = 2
RATE = 44100

HELP_STATUS_TEXT = [
    "Not connected", "Connected as server", "Connected as client"
]

print("Opening sound device")

stream = p.open(format=p.get_format_from_width(WIDTH),
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                input_device_index=chosen_device_index,
                frames_per_buffer=CHUNK)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

socket_ip = "127.0.0.1"
socket_port = 9000

input_thread.start()
listener_thread.start()
broadcast_thread.start()

audio_listening = False
audio_play = True
socket_mode = 0

connection_list = []

while True:
  if (audio_listening):
    if (socket_mode == 1):
      data = stream.read(CHUNK)
      for addr in connection_list:
        sock.sendto(data, addr)
    elif (socket_mode == 2):
      try:
        data, addr = sock.recvfrom(CHUNK * 4)
        if (audio_play):
          stream.write(data, CHUNK)
      except socket.error:
        pass

  if (not connect_queue.empty()):
    addr = connect_queue.get()
    print(addr)
    connection_list.append(addr)
    connect_queue.task_done()

  if (not command_queue.empty()):
    command = command_queue.get().split(" ")

    if (command[0] == "exit"):
      command_queue.task_done()
      break
    elif (command[0] == "serve"):
      audio_listening = True
      audio_play = False
      socket_mode = 1
      start_discovery_broadcast()
    elif (command[0] == "connect"):
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
      
      audio_listening = True
      audio_play = True
      socket_mode = 2
      print("Connecting to {}:{}".format(socket_ip, socket_port))  
      connect_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      connect_socket.sendto(gen_payload(CONNECT_SOCK,socket.gethostname()).encode(),(socket_ip, CONNECT_SOCK["PORT"]))
      connect_socket.close()
      sock.bind(("",COMM_PORT))
      sock.setblocking(False)
    elif (command[0] == "stop"):
      audio_listening = False
      socket_mode = 0
      sock.close()
      stop_discovery_broadcast()
      connection_list = []
    elif (command[0] == "info"):
      print("Audio listening") if (audio_listening) else print("Audio not listening")
      print("Audio muted") if (not audio_play) else print("Audio not muted")
      print(HELP_STATUS_TEXT[socket_mode])
    elif (command[0] == "mute"):
      audio_play = False
    elif (command[0] == "unmute"):
      audio_play = True
    elif (command[0] == "debug"):
      socaaa = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      socaaa.sendto("hahaha".encode(),("192.168.43.102",9000))
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

is_running.clear()
discovery_listener_running.clear()

sock.close()

stream.stop_stream()
stream.close()

p.terminate()

stop_discovery_broadcast()
input_thread.join()
listener_thread.join()