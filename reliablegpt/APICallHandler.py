import queue
from concurrent.futures import ThreadPoolExecutor
import threading
from termcolor import colored
import traceback


from reliablegpt.CustomQueue import CustomQueue


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
    self.error_occurred = False
    self.error_description = None
    self.start_worker()

  def start_worker(self):
    if not self.worker_running:
      self.worker_thread = threading.Thread(target=self.worker)
      self.worker_thread.start()
      self.worker_running = True

  def stop_worker(self):
    if self.worker_running:
      self.worker_running = False
    return

  def print_verbose(self, print_statement):
    if self.verbose:
      print(colored("APICallHandler: " + str(print_statement), "cyan"))

  def result_handler(self, result, task_id):
    self.results[task_id] = result

  def process_item(self, function, kwargs, task_id):
    # wrap this around reliableGPT
    try:
      self.print_verbose(f"processing function: {function}")
      result = function(**kwargs)
      self.result_handler(result, task_id)
      return result
    except Exception as e:
      self.print_verbose(f"Error in task {task_id}: {e}")
      self.error_occurred = True
      self.error_description = traceback.format_exc()

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
        thread.join

      # Check if any errors occurred
      if self.error_occurred:
        # Break out of the worker threads
        for thread in threads:
          thread.join()
        self.print_verbose("Errors occurred. Terminating worker threads.")

  # Define worker function that processes items from the queue
  def worker(self):
    timeout = 5
    try:
      self.error_occurred = False  # reset to False -> if one request is bad, don't stop any new request from coming in, in production. Just drop that batch. [TODO: drop just that single request].
      while True and self.error_occurred == False:
        try:
          items = self.q.get(timeout=timeout)  # Add timeout to the get method
        except queue.Empty:  # Add an exception handler for queue empty

          self.stop_worker()

          break
        except Exception as e:
          self.print_verbose(f"Hit an exception {traceback.format_exc()}")
        self.print_verbose(f"gets item from queue: {items}")
        if isinstance(items, list):
          self.run_async(items=items)
        else:
          function, argument, task_id = items
          self.process_item(function, argument, task_id)
        self.q.task_done()
    except:
      self.print_verbose(f"Hit an exception {traceback.format_exc()}")

  def add_sentinel(self, sentinel_value):
    self.q.put(sentinel_value)

  def add_task(self, process_func, input, task_id):
    if not self.worker_running:
      self.start_worker()
    self.q.put((process_func, input, task_id))

  def get_result(self, task_id):
    if task_id in self.results:
      return self.results[task_id]
    elif self.error_occurred:
      raise RuntimeError(
        f"An error occurred while processing one of the requests. Set verbose=True to debug this further. \n\n {self.error_description}"
      )
    else:
      return None

  def get_results(self):
    return self.results
