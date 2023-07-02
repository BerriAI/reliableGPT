from termcolor import colored
import uuid
import time
import traceback


## Dev Imports 
# from IndividualRequest import IndividualRequest
# from APICallHandler import APICallHandler

## Prod Imports
from reliablegpt.IndividualRequest import IndividualRequest
from reliablegpt.APICallHandler import APICallHandler


class RateLimitHandler:
  """A brief description of the class."""

  def __init__(
      self,
      model=None,
      fallback_strategy=[
        'gpt-3.5-turbo', 'text-davinci-003', 'gpt-4', 'text-davinci-002'
      ],
      graceful_string="Sorry, the OpenAI API is currently down",
      user_email="",
      user_token="",
      send_notification=False,
      max_token_capacity=40000,  #using default openai gpt-4 token capacity
      max_request_capacity=200,  #using default openai gpt-4 request capacity
      logging_fn=None,
      verbose=False):
    # Initialize instance variables
    super().__init__()
    self.model = model
    self.process_func = model.get_model_function()
    self.verbose = verbose
    self.user_email = user_email
    self.logging_fn = logging_fn
    self.graceful_string = graceful_string
    self.api_handler = APICallHandler(max_token_capacity,
                                      max_request_capacity,
                                      verbose=verbose)
    self.individual_request_handler = IndividualRequest(
      model,
      fallback_strategy=fallback_strategy,
      graceful_string=graceful_string,
      user_email=user_email,
      user_token=user_token,
      logging_fn=self.logging_fn,
      send_notification=False)

  def __call__(self, *args, **kwargs):
    try:
      result = self.get_request(kwargs)
      return result
    except:
      self.print_verbose(f"Hits an error: {traceback.format_exc()}")

  def print_verbose(self, print_statement):
    if self.verbose:
      print(colored("RateLimitHandler Request: " + print_statement, "yellow"))

  def get_batch_result_helper(self, text):
    task_id = uuid.uuid4().int
    self.print_verbose("task_id: ", task_id)
    self.print_verbose(
      f"function description: {self.individual_request_handler}")
    self.api_handler.add_task(process_func=self.individual_request_handler,
                              input=text,
                              task_id=task_id)

    start_time = time.time()

    while time.time() - start_time < self.set_timeout:
      result = self.api_handler.get_result(task_id)
    if result:
      return result

    return None

  def get_request(self, kwargs, set_timeout=1200):
    try:
      task_id = uuid.uuid4().int
      self.print_verbose(f"task_id: {task_id}")
      self.print_verbose(
        f"function description: {self.individual_request_handler}")
      self.api_handler.add_task(process_func=self.individual_request_handler,
                                input=kwargs,
                                task_id=task_id)

      start_time = time.time()
      while time.time() - start_time < set_timeout:
        results = self.api_handler.get_result(task_id=task_id)
        if results:
          return results

      result = self.graceful_string
      self.logging_fn(user_email=self.user_email,
                      graceful_string=self.graceful_string,
                      posthog_event='reliableGPT.recovered_request_exception',
                      result=result,
                      posthog_metadata={
                        'error': "Request timed out",
                        'recovered_response': result
                      },
                      errors=["Request timed out"])
      return result
    except:
      result = self.graceful_string
      self.logging_fn(user_email=self.user_email,
                      graceful_string=self.graceful_string,
                      posthog_event='reliableGPT.recovered_request_exception',
                      result=result,
                      posthog_metadata={
                        'error': traceback.format_exc(),
                        'recovered_response': result
                      },
                      errors=[traceback.format_exc()])
      return result

  def get_results(self):
    return self.api_handler.get_results()

  def get_result_threaded(self, test_question, results, set_timeout):
    self.print_verbose(f"Enters reliableGPT with question: {test_question}")
    start_time = time.time()
    result = self.get_batch_result_helper(test_question, set_timeout)
    results.append(result)
    end_time = time.time()
    self.print_verbose(f"Gets result from reliableGPT: {result}",
                       end_time - start_time)

  def batch_process(self, questions=[], set_timeout=1200):
    for question in questions:
      task_id = uuid.uuid4().int
      self.print_verbose("task_id: ", task_id)
      self.api_handler.add_task(process_func=self.process_func,
                                input=question,
                                task_id=task_id)
    start_time = time.time()
    while time.time() - start_time < set_timeout:
      results = self.api_handler.get_results()
      if len(results) >= len(questions):
        return results
    return self.api_handler.get_results()
