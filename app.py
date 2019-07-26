from queue import Queue
import pyaudio
import socket
import threading
import sys

import command

command_queue = Queue()
input_thread = threading.Thread(target=command.worker, args=(command_queue, ))

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

audio_listening = False
audio_play = True
socket_mode = 0

while True:
  if (audio_listening):
    if (socket_mode == 1):
      data = stream.read(CHUNK)
      sock.sendto(data, (socket_ip, socket_port))
    elif (socket_mode == 2):
      try:
        data, addr = sock.recvfrom(CHUNK * 4)
        if (audio_play):
          stream.write(data, CHUNK)
      except socket.error:
        pass

  if (not command_queue.empty()):
    command = command_queue.get().split(" ")

    if (command[0] == "exit"):
      command_queue.task_done()
      break
    elif (command[0] == "serve"):
      audio_listening = True
      audio_play = False
      if(len(command)>=3):
        socket_ip = command[1]
        socket_port = int(command[2])
      print("Serving to",socket_ip,":",socket_port)
      socket_mode = 1
    elif (command[0] == "connect"):
      audio_listening = True
      audio_play = True
      socket_mode = 2
      if(len(command)>=3):
        socket_ip = command[1]
        socket_port = int(command[2])
      print("Connecting to",socket_ip,":",socket_port)  
      sock.bind((socket_ip,socket_port))
      sock.setblocking(False)
    elif (command[0] == "stop"):
      audio_listening = False
      socket_mode = 0
      sock.close()
    elif (command[0] == "info"):
      print("Audio listening") if (audio_listening) else print("Audio not listening")
      print("Audio muted") if (not audio_play) else print("Audio not muted")
      print(HELP_STATUS_TEXT[socket_mode])
    elif (command[0] == "mute"):
      audio_play = False
    elif (command[0] == "unmute"):
      audio_play = True
    else:
      print("Command")
      print("exit                - Exit app")
      print("serve <ip> <port>   - Start server (defaults to localhost 9000)")
      print("connect <ip> <port> - Connect to (defaults to localhost 9000)")
      print("stop                - Stop connection")
      print("mute                - Mute other party")
      print("listen              - Unmute other party")
      print("info                - Print current status")
    

    command_queue.task_done()

print("Exiting")

sock.close()

stream.stop_stream()
stream.close()

p.terminate()

input_thread.join()
