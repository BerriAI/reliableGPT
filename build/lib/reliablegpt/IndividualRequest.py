from termcolor import colored
import requests
import copy
import posthog
import openai
from openai import ChatCompletion
import traceback
from uuid import uuid4
from waitress import serve
from flask import Flask, request
from uuid import uuid4
import traceback
from threading import active_count
import random 
import time 
import asyncio 
import signal

## for testing
class CustomError(Exception):
    def __init__(self, error):
        self.error = error


class IndividualRequest:
  """A brief description of the class."""

  def __init__(self,
               model=None,
               fallback_strategy=[
                 'gpt-3.5-turbo', 'text-davinci-003', 'gpt-4',
                 'text-davinci-002'
               ],
               azure_fallback_strategy=None,
               graceful_string="Sorry, the OpenAI API is currently down",
               user_email="",
               user_token="",
               send_notification=False,
               logging_fn=None,
               backup_openai_key="",
               caching=False,
               alerting=None,
               max_threads=None,
               _test=False,
               verbose=False):
    # Initialize instance variables
    self.model = model
    self.model_function = model.get_model_function()
    self.verbose = verbose
    self.graceful_string = graceful_string
    self.fallback_strategy = fallback_strategy
    self.user_email = user_email
    self.user_token = user_token
    self.save_request = logging_fn
    self.backup_openai_key = backup_openai_key
    self._test = _test
    self.print_verbose(f"INIT fallback strategy {self.fallback_strategy}")
    self.caching = caching
    self.max_threads = max_threads
    self.print_verbose(f"INIT with threads {self.max_threads} {self.caching} {max_threads}")
    self.alerting = alerting
    self.azure_fallback_strategy = azure_fallback_strategy
    self.backup_model = None
    self.set_cooldown = False
    self.cooldown_start_time = time.time()

  def handle_unhandled_exception(self, e):
    self.print_verbose(colored("UNHANDLED EXCEPTION OCCURRED", "red"))
    if self.alerting:
      self.alerting.add_error(error_type="Unhandled Exception", error_description=traceback.format_exc())

  def print_verbose(self, print_statement):
    if self.verbose:
      print(colored("Individual Request: " + str(print_statement), "blue"))

  def start_cooldown(self):
    self.set_cooldown = True
    self.cooldown_start_time = time.time()

  def call_model(self, args, kwargs):
    try: 
      if self._test: # private function for testing package
        error = {"type": "RandomError"}
        raise CustomError(error)
      if self.set_cooldown:
        if time.time() - self.cooldown_start_time > 900: # endpoint is being cooled down for 15 minutes, default to fallbacks
          error = {"type": "ErrorCooldown"}
          raise(CustomError(error=error))
        else:
          self.set_cooldown = False
      result = self.model_function(*args, **kwargs)
      if result == None:
        self.print_verbose(f"None result!")
        return
        error = {"type": f"OpenAI Endpoint {self.model_function} returned None"}
        raise CustomError(error)
      if "messages" in kwargs:
        if "engine" in kwargs:
          self.curr_azure_model = kwargs["engine"]
        if self.caching:
          self.print_verbose(kwargs["messages"])
          input_prompt = "\n".join(message["content"]
                                  for message in kwargs["messages"])
          extracted_result = result['choices'][0]['message']['content']
          self.print_verbose(f'This is extracted result {extracted_result}')
          self.add_cache(
            input_prompt, extracted_result
          )  # [TODO] turn this into a threaded call, reduce latency.
        self.print_verbose(f"This is the result: {str(result)[:500]}")
      return result
    except Exception as e:
      self.print_verbose(f"Error: {traceback.format_exc()}")
      self.print_verbose("catches the error")
      self.start_cooldown()
      return self.handle_exception(args, kwargs, e)
    
  async def async_call_model(self, args, kwargs):
    try: 
      if self._test: # private function for testing package
        error = {"type": "RandomError in async function"}
        raise CustomError(error)
      if self.set_cooldown:
        if time.time() - self.cooldown_start_time > 900: # endpoint is being cooled down for 15 minutes
          error = {"type": "ErrorCooldown"}
          raise(CustomError(error=error))
        else:
          self.set_cooldown = False
      result = await self.model_function(*args, **kwargs)
      if "messages" in kwargs:
        if "engine" in kwargs:
          self.curr_azure_model = kwargs["engine"]
        if self.caching:
          self.print_verbose(kwargs["messages"])
          input_prompt = "\n".join(message["content"]
                                  for message in kwargs["messages"])
          extracted_result = result['choices'][0]['message']['content']
          self.print_verbose(f'This is extracted result {extracted_result}')
          self.add_cache(
            input_prompt, extracted_result
          )  # [TODO] turn this into a threaded call, reduce latency.
        self.print_verbose(f"This is the result: {str(result)[:500]}")
      return result
    except Exception as e:
      self.print_verbose("catches the error")
      self.start_cooldown()
      return self.handle_exception(args, kwargs, e)


  ## Code that handles / wraps openai calls
  def __call__(self, *args, **kwargs):
    try:
      self.print_verbose(f"calling model function: {self.model_function}")
      self.print_verbose(f"these are the kwargs: {kwargs}")
      self.print_verbose(f"this is the openai api base: {openai.api_base}")
      self.print_verbose(f"testing enabled: {self._test}")
      try:
        # this should never block running the openai call
        # [TODO] make this into a threaded call to reduce impact on latency
        self.save_request(
          user_email=self.user_email,
          graceful_string=self.graceful_string,
          posthog_event='reliableGPT.request',
        )
      except:
        self.print_verbose("ReliableGPT error occured during saving request")
      self.print_verbose(f"max threads: {self.max_threads}, caching: {self.caching}")
      if self.max_threads and self.caching:
        self.print_verbose(f'current util: {active_count()/self.max_threads}')
        thread_utilization = active_count()/self.max_threads
        self.print_verbose(f"Thread utilization: {thread_utilization}")
        if thread_utilization > 0.8: # over 80% utilization of threads, start returning cached responses
          if "messages" in kwargs and self.caching:
            self.print_verbose(kwargs["messages"])
            input_prompt = "\n".join(message["content"]
                                    for message in kwargs["messages"])
            self.print_verbose(
              f"queue depth is higher than the threshold, start caching")
            result = self.try_cache_request(query=input_prompt)
            if self.alerting:
              # save_exception
              self.alerting.add_error(error_type="Thread Utilization > 85%", error_description="Your thread utilization is over 85%. We've started responding with cached results, to prevent requests from dropping. Please increase capacity (allocate more threads/servers) to prevent result quality from dropping.")
            if result == None: # cache miss!
              pass
            else:
              self.print_verbose(f"returns cached result: {result}")
              self.save_request(
                user_email=self.user_email,
                posthog_event='reliableGPT.recovered_request_cache',
                graceful_string = self.graceful_string,
                result=result,
                posthog_metadata={
                  'error': 'High Thread Utilization',
                  'recovered_response': result,
                },
                errors=['High Thread Utilization'],
                function_name=str(self.model_function),
                kwargs=kwargs
              )
              return result
      
      # Run user request
      if asyncio.iscoroutinefunction(self.model_function):
        return self.async_call_model(args=args, kwargs=kwargs)
      else:
        return self.call_model(args=args, kwargs=kwargs)
    except Exception as e:
      self.print_verbose(f"Error in main call function: {traceback.format_exc()}")

  def add_cache(self, input_prompt, response):
    try:
      if self.caching:
        if request:
          if request.args and request.args.get("user_email"):
            customer_id = request.args.get("user_email")
            if request.args.get("instance_id"):
              instance_id = request.args.get("instance_id")
            else:
              instance_id = 0000 # default instance id if none passed in
            user_email = self.user_email
            url = "https://reliablegpt-logging-server-7nq8.zeet-berri.zeet.app/add_cache"
            querystring = {
              "customer_id": customer_id,
              "instance_id": instance_id, 
              "user_email": user_email, 
              "input_prompt": input_prompt,
              "response": response
            }
            response = requests.post(url, params=querystring)
    except:
      pass

  def try_cache_request(self, query=None):
    try:
      if query:
        self.print_verbose("Inside the cache")
        if request:
          if request.args and request.args.get("user_email"):
            customer_id = request.args.get("user_email")
            if request.args.get("instance_id"):
              instance_id = request.args.get("instance_id")
            else:
              instance_id = 0000 # default instance id if none passed in
            user_email = self.user_email
            url = "https://reliablegpt-logging-server-7nq8.zeet-berri.zeet.app/get_cache"
            querystring = {
                "customer_id": customer_id,
                "instance_id": instance_id, 
                "user_email": user_email, 
                "input_prompt": query,
            }
            response = requests.get(url, params=querystring)
            self.print_verbose(f"cached response: {response.json()}")
            extracted_result = response.json()["response"]
            results = {"choices":[{"message":{"content": extracted_result}}]}
            return results
    except:
      traceback.print_exc()
      pass
    self.print_verbose(f"cache miss!")
    return None

  def fallback_request(self, args, kwargs, fallback_strategy):
    try:
      self.print_verbose("In fallback request")
      result = None
      new_kwargs = copy.deepcopy(kwargs)  # Create a deep copy of kwargs
      if self.backup_openai_key and len(
          self.backup_openai_key
      ) > 0:  # user passed in a backup key for the raw openai endpoint
        # switch to the raw openai model instead of using azure.
        new_kwargs["openai2"] = openai.__dict__.copy(
        )  # preserve the azure endpoint details
        if "Embedding" in str(self.model_function):
          fallback_strategy = ["text-embedding-ada-002"]

      if self.azure_fallback_strategy: # try backup azure models
        for engine in self.azure_fallback_strategy:
          new_kwargs["engine"] = engine
          new_kwargs["azure_fallback"] = True
          self.print_verbose(f"new azure engine: {new_kwargs}")
          result = self.make_LLM_request(new_kwargs)
          if result != None:
            return result
        
      for model in fallback_strategy:
        new_kwargs['model'] = model  # Update the model
        result = self.make_LLM_request(new_kwargs)
        if result != None:
          return result
      return None
    except:
      self.print_verbose(traceback.format_exc())
      return None

  def make_LLM_request(self, new_kwargs):
    embedding_model = self.model.get_original_embeddings()
    chat_model = self.model.get_original_chat()
    completion_model = self.model.get_original_completion()
    try:
      self.print_verbose(f"{new_kwargs.keys()}")
      if "azure_fallback" in new_kwargs:
        new_kwargs_except_azure_fallback_flag = {
          k: v
          for k, v in new_kwargs.items() if k != "azure_fallback"
        }
        return chat_model(**new_kwargs_except_azure_fallback_flag)
      if "openai2" in new_kwargs:
        openai.api_type = "openai"
        openai.api_base = "https://api.openai.com/v1"
        openai.api_version = None
        openai.api_key = self.backup_openai_key
        new_kwargs_except_openai_attributes = {
          k: v
          for k, v in new_kwargs.items() if k != "openai2"
        }
        new_kwargs_except_engine = {
          k: v
          for k, v in new_kwargs_except_openai_attributes.items()
          if k != "engine"
        }
        completion = self.model_function(**new_kwargs_except_engine)
        openai.api_type = new_kwargs["openai2"]["api_type"]
        openai.api_base = new_kwargs["openai2"]["api_base"]
        openai.api_version = new_kwargs["openai2"]["api_version"]
        openai.api_key = new_kwargs["openai2"]["api_key"]
        return completion
      if "embedding" in str(self.model_function):
        # retry embedding with diff key
        self.print_verbose(colored(f"ReliableGPT: Retrying Embedding request", "blue"))
        return embedding_model(**new_kwargs)

      model = str(new_kwargs['model'])
      self.print_verbose(
        colored(f"ReliableGPT: Checking request model {model} {new_kwargs}",
                "blue"))
      if "3.5" in model or "4" in model:  # call ChatCompletion
        self.print_verbose(
          colored(
            f"ReliableGPT: Retrying request with model CHAT {model} {new_kwargs}",
            "blue"))
        return chat_model(**new_kwargs)
      else:
        self.print_verbose(
          colored(f"ReliableGPT: Retrying request with model TEXT {model}",
                  "blue"))
        new_kwargs['prompt'] = " ".join(
          [message["content"] for message in new_kwargs['messages']])
        new_kwargs.pop('messages',
                       None)  # remove messages for completion models
        return completion_model(**new_kwargs)
    except Exception as e:
      self.print_verbose(colored(f"ReliableGPT: Got 2nd AGAIN Error {e}", "red"))
      raise ValueError(e)

  def api_key_handler(self, args, kwargs, fallback_strategy, user_email,
                      user_token):
    try:
      url = f"https://reliable-gpt-backend-9gus.zeet-berri.zeet.app/get_keys?user_email={user_email}&user_token={user_token}"
      response = requests.get(url)
      if response.status_code == 200:
        result = response.json()
        if result['status'] == 'failed':
          self.print_verbose(
            colored(
              f"ReliableGPT: No keys found for user: {user_email}, token: {user_token}",
              "red"))
          return None

        fallback_keys = result['response'][
          'openai_api_keys']  # list of fallback keys
        if len(fallback_keys) == 0:
          return None
        for fallback_key in fallback_keys:
          openai.api_key = fallback_key
          result = self.make_LLM_request(kwargs)
          if result != None:
            return result
      else:
        self.print_verbose(
          colored(
            f"ReliableGPT: No keys found for user: {user_email}, token: {user_token}",
            "red"))
      return None
    except Exception as e:
      raise ValueError(e)

  def handle_openAI_error(self,
                          args,
                          kwargs,
                          openAI_error,
                          fallback_strategy,
                          graceful_string,
                          user_email="",
                          user_token=""):
    # Error Types from https://platform.openai.com/docs/guides/error-codes/python-library-error-types
    # 1. APIError - retry, retry with fallback
    # 2. Timeout - retry, retry with fallback
    # 3. RateLimitError - retry, retry with fallback
    # 4. APIConnectionError - Check your network settings, proxy configuration, SSL certificates, or firewall rules.
    # 5. InvalidRequestError - User input was bad: context_length_exceeded,
    # 6. AuthenticationError - API key not working, return default hardcoded message
    # 7. ServiceUnavailableError - retry, retry with fallback
    self.print_verbose(
      colored(f"Inside handle openai error for User Email: {user_email}",
              "red"))
    if openAI_error != None:
      openAI_error = openAI_error.error  # index into the error attribute of the class

    error_type = None  # defalt to being None
    if openAI_error != None and 'type' in openAI_error:
      error_type = openAI_error['type']
    if error_type == 'invalid_request_error' or error_type == 'InvalidRequestError':
      # check if this is context window related, try with a 16k model
      if openAI_error.code == 'context_length_exceeded':
        self.print_verbose(
          colored(
            "ReliableGPT: invalid request error - context_length_exceeded",
            "red"))
        fallback_strategy = ['gpt-3.5-turbo-16k'] + fallback_strategy
        result = self.fallback_request(args=args,
                                       kwargs=kwargs,
                                       fallback_strategy=fallback_strategy)
        if result == None:
          return graceful_string
        else:
          return result
      if openAI_error.code == "invalid_api_key":
        self.print_verbose(
          colored("ReliableGPT: invalid request error - invalid_api_key",
                  "red"))
        result = self.api_key_handler(args=args,
                                      kwargs=kwargs,
                                      fallback_strategy=fallback_strategy,
                                      user_email=user_email,
                                      user_token=user_token)
        if result == None:
          return graceful_string
        else:
          return result

    # todo: alert on user_email that there is now an auth error
    elif error_type == 'authentication_error' or error_type == 'AuthenticationError':
      self.print_verbose(colored("ReliableGPT: Auth error", "red"))
      return graceful_string

    # catch all
    result = self.fallback_request(args=args,
                                   kwargs=kwargs,
                                   fallback_strategy=fallback_strategy)
    if result == None:
      return graceful_string
    else:
      return result
    return graceful_string

  def handle_exception(self, args, kwargs, e):
    result = self.graceful_string  # default to graceful string
    try:
      # Attempt No. 1, exception is received from OpenAI
      self.print_verbose(colored(f"ReliableGPT: Got Exception {e}", 'red'))
      result = self.handle_openAI_error(
        args=args,
        kwargs=kwargs,
        openAI_error=e,
        fallback_strategy=self.fallback_strategy,
        graceful_string=self.graceful_string,
        user_email=self.user_email,
        user_token=self.user_token)
      self.print_verbose(
        colored(f"ReliableGPT: Recovered got a successful response {result}",
                "green"))
      if result == self.graceful_string:
        # did a retry with model fallback, so now try caching.
        if "messages" in kwargs and self.caching:
          self.print_verbose(kwargs["messages"])
          input_prompt = "\n".join(message["content"]
                                   for message in kwargs["messages"])
          cached_response = self.try_cache_request(query=input_prompt)
          if cached_response == None:
            pass
          else:
            self.save_request(
              user_email=self.user_email,
              posthog_event='reliableGPT.recovered_request_cache',
              graceful_string = self.graceful_string,
              result=cached_response,
              posthog_metadata={
                'error': 'High Thread Utilization',
                'recovered_response': cached_response,
              },
              errors=['High Thread Utilization'],
              function_name=str(self.model_function),
              kwargs=kwargs
            )
            return cached_response
        self.save_request(
          user_email=self.user_email,
          graceful_string=self.graceful_string,
          posthog_event='reliableGPT.recovered_request_exception',
          result=result,
          posthog_metadata={
            'error': str(e),
            'recovered_response': result
          },
          errors=[e],
          function_name=str(self.model_function),
          kwargs=kwargs)
      else:
        # No errors, successfull retry
        self.save_request(user_email=self.user_email,
                          graceful_string=self.graceful_string,
                          posthog_event="reliableGPT.recovered_request",
                          result=result,
                          posthog_metadata={
                            'error': str(e),
                            'recovered_response': result
                          },
                          errors=[e],
                          function_name=str(self.model_function),
                          kwargs=kwargs)
    except Exception as e2:
      # Exception 2, After trying to rescue
      traceback.print_exc()
      self.print_verbose("gets 2nd error: ", e2)
      self.save_request(
        user_email=self.user_email,
        graceful_string=self.graceful_string,
        posthog_event='reliableGPT.recovered_request_exception',
        result="",
        posthog_metadata={
          'original_error': str(e),
          'error2': str(e2),
          'recovered_response': self.graceful_string
        },
        errors=[e, e2],
        function_name=str(self.model_function),
        kwargs=kwargs)
      raise e
    return result
