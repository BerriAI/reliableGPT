# # Prod Imports
from reliablegpt.IndividualRequest import IndividualRequest
from reliablegpt.Model import Model
from reliablegpt.Alerting import Alerting
import requests
import asyncio 

# Dev Imports
# from IndividualRequest import IndividualRequest
# from Model import Model
# from Alerting import Alerting

from posthog import Posthog
from flask import Flask, request

posthog = Posthog(
  project_api_key='phc_yZ30KsPzRXd3nYaET3VFDmquFKtMZwMTuFKVOei6viB',
  host='https://app.posthog.com')

alerting = Alerting()

def save_exception(type, user_email, result="", original_error="", error2="", function_name="", kwargs={}):
  try:
    #print("in save exception on reliableGPT")
    # url = 'http://0.0.0.0:5000/save_exception'
    url = 'https://reliablegpt-logging-server-7nq8.zeet-berri.zeet.app/save_exception'

    data = {
            'type': type,
            'user_email': user_email,
            'result': result,
            'original_error': original_error,
            'error2': error2,
            'function_name': function_name,
            'kwargs': kwargs
        }
    #print(f"in save exception on reliableGPT, sending req {data}")
    response = requests.post(url, json=data)
  except Exception as e:
      pass
  
  return response



# Parent Logging function
def save_request(user_email,
                 graceful_string,
                 posthog_event="",
                 result="",
                 posthog_metadata={},
                 errors=[], function_name="", kwargs={}):
  pass
  # try:
  #   if posthog_event != "":
  #     posthog.capture(user_email, posthog_event,
  #                     posthog_metadata)  # save posthog event
      
  #     # Log handled and unahndled exceptions in R-GPT servers
  #     if posthog_event == 'reliableGPT.recovered_request':
  #       original_error = ""
  #       if 'error' in posthog_metadata:
  #         original_error = posthog_metadata['error']
  #       save_exception(type = 'handled', user_email=user_email, result=result, original_error=original_error, function_name=function_name, kwargs=kwargs)

  #     # Log handled and unahndled exceptions in R-GPT servers
  #     if posthog_event == 'reliableGPT.recovered_request_cache':
  #       original_error = ""
  #       if 'error' in posthog_metadata:
  #         original_error = posthog_metadata['error']
  #       save_exception(type = 'handled cache', user_email=user_email, result=result, original_error=original_error, function_name=function_name, kwargs=kwargs)

  #     # Log unhandled exceptions in R-GPT servers
  #     if posthog_event == 'reliableGPT.recovered_request_exception':
  #       original_error = ""
  #       error2 = ""
  #       if 'error' in posthog_metadata:
  #         original_error = posthog_metadata['error']
  #       if 'error2' in posthog_metadata:
  #         error2 = posthog_metadata['error2']
  #       save_exception(type = 'unhandled', user_email=user_email, result=result, original_error=original_error, error2=error2, function_name=function_name, kwargs=kwargs)
      
  #   if result == graceful_string or len(
  #       errors) == 2:  # returns a graceful string or got a 2nd exception
  #     # send an email and alert
  #     for error in errors:
  #       alerting.add_error(error)
  #     # send_emails_task(self.user_email, posthog_metadata, self.send_notification)
  # except:
  #   pass
    # return  # safe function, should not impact error handling if logging fails


def reliableGPT(openai_create_function,
           fallback_strategy=[
             'gpt-3.5-turbo', 'text-davinci-003', 'gpt-4', 'text-davinci-002'
           ],
           azure_fallback_strategy=None,
           graceful_string="Sorry, the OpenAI API is currently down",
           user_email="",
           user_token="",
           send_notification=True,
           caching=False,
           max_threads=None,
           backup_openai_key=None,
           _test=False,
           verbose=False):
  """Determine if an instantiation is calling the rate limit handler or the individual request wrapper directly and return the correct object"""

  primary_email = ""  # which api key management is mapped to
  ## Add email for alerting
  if isinstance(user_email, str):
    if user_email == "":
      raise ValueError("ReliableGPT Error: Please pass in a user email")
    else:
      alerting.add_emails(user_email)
      primary_email = user_email
  elif isinstance(user_email, list):
    primary_email = user_email[0]
    for email in user_email:
      alerting.add_emails(email)

  model = Model(openai_create_function)
  ## Route to the right object
  return IndividualRequest(model,
                            fallback_strategy=fallback_strategy,
                            azure_fallback_strategy=azure_fallback_strategy,
                            graceful_string=graceful_string,
                            user_email=primary_email,
                            user_token=user_token,
                            logging_fn=save_request,
                            send_notification=send_notification,
                            backup_openai_key=backup_openai_key, 
                            caching=caching,
                            max_threads=max_threads,
                            alerting=alerting,
                            _test=_test,
                            verbose=verbose)