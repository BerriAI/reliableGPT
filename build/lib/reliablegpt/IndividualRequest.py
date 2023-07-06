from termcolor import colored
import time
import requests
import copy
import posthog
import importlib
import openai
from openai import ChatCompletion
import traceback
import random
from uuid import uuid4
import subprocess
import importlib
from waitress import serve
from flask import Flask, request
import random
from uuid import uuid4
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
import chromadb
import traceback
import hashlib 
import psutil
import os 
from threading import active_count


class IndividualRequest:
  """A brief description of the class."""

  def __init__(self,
               model=None,
               fallback_strategy=[
                 'gpt-3.5-turbo', 'text-davinci-003', 'gpt-4',
                 'text-davinci-002'
               ],
               graceful_string="Sorry, the OpenAI API is currently down",
               user_email="",
               user_token="",
               send_notification=False,
               logging_fn=None,
               backup_openai_key="",
               caching=False,
               alerting=None,
               max_threads=None,
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
    self.print_verbose(f"INIT fallback strategy {self.fallback_strategy}")
    self.caching = caching
    self.max_threads = max_threads
    self.alerting = alerting
    if self.caching:
      self.print_verbose(
        f"Trying to import caching dependencies - caching set to {self.caching}"
      )
      self.chroma_client = chromadb.Client()
      self.cache = {
        "global":
        self.chroma_client.create_collection(name="global_collection")
      }  # initialize a global/catch-all cache

  def print_verbose(self, print_statement):
    if self.verbose:
      print(colored("Individual Request: " + print_statement, "blue"))

  ## Code that handles / wraps openai calls
  def __call__(self, *args, **kwargs):
    try:
      self.print_verbose(f"calling model function: {self.model_function}")
      self.print_verbose(f"these are the kwargs: {kwargs}")
      self.print_verbose(f"this is the openai api base: {openai.api_base}")
      try:
        # this should never block running the openai call
        # [TODO] make this into a threaded call to reduce impact on latency
        self.save_request(
          user_email=self.user_email,
          graceful_string=self.graceful_string,
          posthog_event='reliableGPT.request',
        )
      except:
        print("ReliableGPT error occured during saving request")
      if self.max_threads and self.caching:
        thread_utilization = active_count()/self.max_threads
        self.print_verbose(f"Thread utilization: {thread_utilization}")
        if thread_utilization > 0.8: # over 80% utilization of threads, start returning cached responses
          self.print_verbose(
            f"queue depth is higher than the threshold, start caching")
          result = self.try_cache_request(query=input_prompt)
          self.alerting.add_error(error_type="Thread Utilization > 85%", error_description="Your thread utilization is over 85%. We've started responding with cached results, to prevent requests from dropping. Please increase capacity (allocate more threads/servers) to prevent result quality from dropping.")
          if result == None:
            pass
          else:
            return result
      print("received request")
      result = self.model_function(*args, **kwargs)
      if "messages" in kwargs and self.caching:
        print(kwargs["messages"])
        input_prompt = "\n".join(message["content"]
                                 for message in kwargs["messages"])
        extracted_result = result['choices'][0]['message']['content']
        self.add_cache(
          input_prompt, extracted_result
        )  # [TODO] turn this into a threaded call, reduce latency.
      self.print_verbose(f"This is the result: {str(result)[:500]}")
      return result
    except Exception as e:
      self.print_verbose("catches the error")
      return self.handle_exception(args, kwargs, e)

  def add_cache(self, input_prompt, response):
    try:
      if self.caching:
        if request:
          if request.args and request.args.get("user_email"):
            hashed_value = hashlib.sha1(self.user_email.encode()).hexdigest()
            id = str(uuid4())
            if hashed_value in self.cache:
              self.cache[hashed_value].add(documents=[input_prompt],
                                           metadatas=[{
                                             "response": response
                                           }],
                                           ids=str(id))
            else:
              self.cache[hashed_value] = self.chroma_client.create_collection(
                name=f"{hashed_value}_collection")
              self.cache[hashed_value].add(documents=[input_prompt],
                                           metadatas=[{
                                             "response": response
                                           }],
                                           ids=str(id))
    except:
      pass

  def try_cache_request(self, query=None):
    if query:
      self.print_verbose("Inside the cache")
      if request:
        if request.args and request.args.get("user_email"):
          hashed_value = hashlib.sha1(
            request.args.get("user_email").encode()).hexdigest()
          self.print_verbose(f"hashed value: {hashed_value}")
          if hashed_value in self.cache:
            collection = self.cache[hashed_value]
            results = collection.query(query_texts=[self.query], n_results=1)
            return results["metadatas"][0][0]["response"]
    else:
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
        print(colored(f"ReliableGPT: Retrying Embedding request", "blue"))
        return embedding_model(**new_kwargs)

      model = str(new_kwargs['model'])
      print(
        colored(f"ReliableGPT: Checking request model {model} {new_kwargs}",
                "blue"))
      if "3.5" in model or "4" in model:  # call ChatCompletion
        print(
          colored(
            f"ReliableGPT: Retrying request with model CHAT {model} {new_kwargs}",
            "blue"))
        return chat_model(**new_kwargs)
      else:
        print(
          colored(f"ReliableGPT: Retrying request with model TEXT {model}",
                  "blue"))
        new_kwargs['prompt'] = " ".join(
          [message["content"] for message in new_kwargs['messages']])
        new_kwargs.pop('messages',
                       None)  # remove messages for completion models
        return completion_model(**new_kwargs)
    except Exception as e:
      print(colored(f"ReliableGPT: Got 2nd AGAIN Error {e}", "red"))
      raise ValueError(e)

  def api_key_handler(self, args, kwargs, fallback_strategy, user_email,
                      user_token):
    try:
      url = f"https://reliable-gpt-backend-9gus.zeet-berri.zeet.app/get_keys?user_email={user_email}&user_token={user_token}"
      response = requests.get(url)
      if response.status_code == 200:
        result = response.json()
        if result['status'] == 'failed':
          print(
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
        print(
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
        print(
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
        print(
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
      print(colored("ReliableGPT: Auth error", "red"))
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
      print(f"result: {result}")
      self.print_verbose(
        colored(f"ReliableGPT: Recovered got a successful response {result}",
                "green"))
      if result == self.graceful_string:
        # did a retry with model fallback, so now try caching.
        if "messages" in kwargs and self.caching:
          print(kwargs["messages"])
          input_prompt = "\n".join(message["content"]
                                   for message in kwargs["messages"])
          cached_response = self.try_cache_request(query=input_prompt)
          if cached_response == None:
            pass
          else:
            return cached_response
        print("returns graceful string")
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
      print("gets 2nd error: ", e2)
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
      return result
      raise e
    return result
