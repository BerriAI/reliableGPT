import queue
from concurrent.futures import ThreadPoolExecutor
import threading
from reliablegpt.custom_queue import CustomQueue

class APICallHandler():

  def __init__(self, max_token_capacity, max_request_capacity, verbose):
    super().__init__()
    self.verbose = verbose
    self.upperbound = 1000000
    self.q = CustomQueue(max_token_capacity=max_token_capacity,
                         max_request_capacity=max_request_capacity,
                         verbose=verbose)
    self.results = {
    }  #key-value pair, task_id is the key, and the response from openai is the value
    # Define a sentinel value for stopping the worker
    # Start the worker thread
    worker_thread = threading.Thread(target=self.worker)
    worker_thread.start()

  def print_verbose(self, *args):
    if self.verbose:
      print(*args)
    
  def set_upperbound(self, upperbound):
    self.upperbound = upperbound

  def result_handler(self, result, task_id):
    self.results[task_id] = result

  def process_item(self, function, argument, task_id):
    print(f"Processing taskID: {task_id}, for function {function} with input: {argument} ")
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
    count_items = 0
    while True:
      if count_items == self.upperbound:
        break
      items = self.q.get()
      self.print_verbose("gets item from queue: ", items)
      # if items is self.STOP_WORKER:
      #   break  # Exit the loop when the sentinel value is encountered
      self.print_verbose(type(items))
      self.print_verbose(f"items: {items}")
      if isinstance(items, list):
        count_items += len(items)
        self.run_async(items=items)
      else:
        function, argument, task_id = items
        count_items += 1
        result = function(argument)  # Call the function with its argument
        self.print_verbose("result from function arg")
        self.result_handler(
          result, task_id)  # Call the callback function with the result
      self.q.task_done()
      self.print_verbose(f"count_items: {count_items} \n\n self.upperbound: {self.upperbound} ")

  def add_sentinel(self, sentinel_value): 
    self.q.put(sentinel_value)

  def add_task(self, process_func, input, task_id):
    self.q.put((process_func, input, task_id))

  def get_result(self, task_id):
    if task_id in self.results:
      return self.results[task_id]
    else:
      return None

  def get_results(self):
    return self.results