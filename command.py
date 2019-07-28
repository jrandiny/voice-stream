def worker(command_queue, run_loop):
  while (run_loop.is_set()):
    command = input("> ")
    command_queue.put(command)
    command_queue.join()