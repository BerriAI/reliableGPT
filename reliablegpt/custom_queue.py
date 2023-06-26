import time
from queue import Queue
import threading
import tiktoken


class CustomQueue(Queue):

  def __init__(self, max_token_capacity, max_request_capacity, verbose, *args,
               **kwargs):
    super().__init__(*args, **kwargs)
    self.verbose = verbose
    self.available_token_capacity = max_token_capacity
    self.available_request_capacity = max_request_capacity
    self.max_request_capacity = max_request_capacity
    self.max_token_capacity = max_token_capacity
    self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    self.curr_time_block = int(time.time() // 60)
    self.lock = threading.Lock()

  def print_verbose(self, *args):
    if self.verbose:
      print(*args)

  def get(self, block=True, timeout=None):
    with self.lock:
      if self.is_empty():
        self.print_verbose("inside is empty")
        return super().get(block=block, timeout=timeout)
      # return the list of valid queries
      curr_time = time.time()
      # Convert it to minutes
      curr_time_minutes = int(curr_time // 60)
      self.print_verbose("curr_time_minutes: ", curr_time_minutes)
      self.print_verbose("self.curr_time_block: ", self.curr_time_block)
      #check how many requests have already been processed for that minute
      if self.curr_time_block == curr_time_minutes:
        self.print_verbose("in current time block")
        available_token_capacity = self.available_token_capacity
        available_request_capacity = self.available_request_capacity
        filtered_capacity = 0
        for args in list(self.queue)[:int(
            available_request_capacity
        )]:  # we can make a max number of requests per minute, check how much is left and iterate through the upperbound
          function, argument, task_id = args
          token_size = self.get_num_tokens(
            argument
          )  # assume you're getting the input prompt and the max output
          tmp_token_capacity = available_token_capacity - token_size
          if tmp_token_capacity >= 0:
            available_token_capacity = tmp_token_capacity
            filtered_capacity += 1
          else:
            break
        self.print_verbose("here's the filtered capacity: ", filtered_capacity)
        self.print_verbose("here's the previous available token capacity: ",
                           available_token_capacity)
        self.available_token_capacity = available_token_capacity
        self.available_request_capacity -= filtered_capacity
      else:
        available_token_capacity = self.max_token_capacity
        available_request_capacity = self.max_request_capacity
        filtered_capacity = 0
        #self.print_verbose(self.queue[:available_request_capacity])
        #self.print_verbose(type(self.queue[:available_request_capacity]))
        for args in list(self.queue)[:int(
            available_request_capacity
        )]:  # iterate through all available capacity until all chunks are done
          function, argument, task_id = args
          token_size = self.get_num_tokens(argument)
          self.print_verbose("token_size: ", token_size)
          tmp_token_capacity = available_token_capacity - token_size
          self.print_verbose("tmp_token_capacity: ", tmp_token_capacity)
          if tmp_token_capacity >= 0:
            available_token_capacity = tmp_token_capacity
            filtered_capacity += 1
          else:
            break
        self.print_verbose("here's the filtered capacity: ", filtered_capacity)
        self.print_verbose("here's the previous available token capacity: ",
                           available_token_capacity)
        self.available_token_capacity = available_token_capacity
        self.curr_time_block = curr_time_minutes
        self.available_request_capacity -= filtered_capacity
      # Create a new list with the required elements, using slicing
      new_list = list(self.queue)[:filtered_capacity]

      # Update the original list by removing the first `filtered_capacity` elements
      for _ in range(filtered_capacity):
        self.queue.popleft()
      self.print_verbose(
        "returning new list. Here's the remaining capacity for this minute: ",
        self.available_token_capacity)
      # Return the new list
      return new_list

  def get_num_tokens(self, chunk):
    return len(self.encoding.encode(chunk))

  def is_empty(self):
    return self.qsize() == 0
