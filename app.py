import pyaudio
from queue import Queue
import threading

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

input_thread.start()

audio_on = False

while True:
  if(audio_on):
    data = stream.read(CHUNK)
    stream.write(data, CHUNK)
    
  if (not command_queue.empty()):
    command = command_queue.get().split(" ")
    
    if (command[0] == "exit"):
      command_queue.task_done()
      break
    elif (command[0] == "serve"):
      audio_on = True
      pass
    elif (command[0] == "connect"):
      audio_on = True
      pass
    elif (command[0] == "stop"):
      audio_on = False
      pass

    command_queue.task_done()


print("Exiting")

stream.stop_stream()
stream.close()

p.terminate()

input_thread.join()
