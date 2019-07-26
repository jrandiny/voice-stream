def worker(command_queue):
  while (True):
    command_queue.join()
    command = input("> ")
    command_queue.put(command)
    if(command == 'exit'):
      break
