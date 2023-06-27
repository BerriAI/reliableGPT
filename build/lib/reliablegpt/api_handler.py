import queue
from concurrent.futures import ThreadPoolExecutor
import threading
from reliablegpt.custom_queue import CustomQueue


class APICallHandler():

  def __init__(self, max_token_capacity, max_request_capacity, verbose):
    super().__init__()
    self.verbose = verbose
    self.q = CustomQueue(max_token_capacity=max_token_capacity,
                         max_request_capacity=max_request_capacity,
                         verbose=verbose)
    self.results = {
    }  #key-value pair, task_id is the key, and the response from openai is the value
    # Define a sentinel value for stopping the worker
    # Start the worker thread
    worker_thread = threading.Thread(target=self.worker)
    self.worker_thread = None
    self.worker_running = False
    self.start_worker()
    # worker_thread.start()
  
  def start_worker(self):
    if not self.worker_running:
      self.worker_thread = threading.Thread(target=self.worker)
      self.worker_thread.start()
      self.worker_running = True
  
  def stop_worker(self):
    if self.worker_running:
      self.worker_running = False

  def print_verbose(self, *args):
    if self.verbose:
      print(*args)

  def result_handler(self, result, task_id):
    self.results[task_id] = result

  def process_item(self, function, argument, task_id):
    result = function(argument)
    self.result_handler(result, task_id)
    return result

  def run_async(self, items):
    self.print_verbose(items)
    if isinstance(items, list):
      threads = []
      for item in items:
        self.print_verbose(item)
        function, argument, task_id = item
        thread = threading.Thread(target=self.process_item,
                                  args=(function, argument, task_id))
        thread.start()
        threads.append(thread)

      # Wait for all threads to finish
      for thread in threads:
        thread.join()

  # Define worker function that processes items from the queue
  def worker(self):
    timeout = 5
    while True:
      try:
        items = self.q.get(timeout=timeout)  # Add timeout to the get method
      except queue.Empty:                      # Add an exception handler for queue empty
        self.print_verbose("Queue timeout: No new items")
        self.stop_worker()
        break
      # items = self.q.get()
      self.print_verbose("gets item from queue: ", items)
      # if items is self.STOP_WORKER:
      #   break  # Exit the loop when the sentinel value is encountered
      self.print_verbose(type(items))
      self.print_verbose(f"items: {items}")
      if isinstance(items, list):
        self.run_async(items=items)
      else:
        function, argument, task_id = items
        result = function(argument)  # Call the function with its argument
        self.print_verbose("result from function arg")
        self.result_handler(
          result, task_id)  # Call the callback function with the result
      self.q.task_done()

  def add_sentinel(self, sentinel_value): 
    self.q.put(sentinel_value)

  def add_task(self, process_func, input, task_id):
    if not self.worker_running:
        self.start_worker()
    self.q.put((process_func, input, task_id))

  def get_result(self, task_id):
    if task_id in self.results:
      return self.results[task_id]
    else:
      return None

  def get_results(self):
    return self.results
