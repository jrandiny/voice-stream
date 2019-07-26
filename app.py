from queue import Queue
import pyaudio
import socket
import threading
import sys

import command

command_queue = Queue()
input_thread = threading.Thread(target=command.worker,args=(command_queue,))

p = pyaudio.PyAudio()

CHUNK = 1024
WIDTH = 2
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5

print("Opening sound device")

stream = p.open(format=p.get_format_from_width(WIDTH),
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

socket_ip = "127.0.0.1"
socket_port = 9000

input_thread.start()

audio_on = False
socket_mode = 0

while True:
  if(audio_on):
    if (socket_mode == 1):
      data = stream.read(CHUNK)
      sock.sendto(data,(socket_ip, socket_port))
      pass
    elif (socket_mode == 2):
      data,addr = sock.recvfrom(CHUNK*4)
      stream.write(data, CHUNK)
      pass
    
  if (not command_queue.empty()):
    command = command_queue.get().split(" ")
    
    if (command[0] == "exit"):
      command_queue.task_done()
      break
    elif (command[0] == "serve"):
      audio_on = True
      socket_mode = 1
      pass
    elif (command[0] == "connect"):
      audio_on = True
      socket_mode = 2
      sock.bind((socket_ip, socket_port))
      pass
    elif (command[0] == "stop"):
      audio_on = False
      socket_mode = 0
      sock.close()
      pass

    command_queue.task_done()

print("Exiting")

sock.close()

stream.stop_stream()
stream.close()

p.terminate()

input_thread.join()
