# # Prod Imports
from reliablegpt.IndividualRequest import IndividualRequest
from reliablegpt.RateLimitHandler import RateLimitHandler
from reliablegpt.Model import Model
from reliablegpt.Alerting import Alerting

# # Dev Imports
# from IndividualRequest import IndividualRequest
# from RateLimitHandler import RateLimitHandler
# from Model import Model
# from Alerting import Alerting

from posthog import Posthog

posthog = Posthog(
  project_api_key='phc_yZ30KsPzRXd3nYaET3VFDmquFKtMZwMTuFKVOei6viB',
  host='https://app.posthog.com')

alerting = Alerting()

# Parent Logging function
def save_request(user_email,
                 graceful_string,
                 posthog_event="",
                 result="",
                 posthog_metadata={},
                 errors=[]):
  try:
    #metadata  = kwargs['metadata']
    if posthog_event != "":
      posthog.capture(user_email, posthog_event,
                      posthog_metadata)  # save posthog event
    if result == graceful_string or len(
        errors) == 2:  # returns a graceful string or got a 2nd exception
      # send an email and alert
      for error in errors:
        alerting.add_error(error)
      # send_emails_task(self.user_email, posthog_metadata, self.send_notification)
  except:
    return  # safe function, should not impact error handling if logging fails


def reliableGPT(openai_create_function,
           fallback_strategy=[
             'gpt-3.5-turbo', 'text-davinci-003', 'gpt-4', 'text-davinci-002'
           ],
           graceful_string="Sorry, the OpenAI API is currently down",
           user_email="",
           user_token="",
           send_notification=True,
           model_limits_dir={},
           backup_openai_key=None,
           queue_requests=False, 
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
  if queue_requests == False:
    return IndividualRequest(model,
                             fallback_strategy=fallback_strategy,
                             graceful_string=graceful_string,
                             user_email=primary_email,
                             user_token=user_token,
                             logging_fn=save_request,
                             send_notification=send_notification,
                             backup_openai_key=backup_openai_key, 
                             verbose=verbose)
  elif queue_requests == True:
    max_token_capacity = 40000
    max_request_capacity = 200
    ## [TODO]: Allow handling multiple model types (gpt-3.5-turbo AND gpt-4)
    if model_limits_dir and isinstance(model_limits_dir, dict):
      keys = model_limits_dir.keys()
      max_token_capacity = model_limits_dir[keys[0]]["max_token_capacity"]
      max_request_capacity = model_limits_dir["max_request_capacity"]

    return RateLimitHandler(model,
                            fallback_strategy=fallback_strategy,
                            graceful_string=graceful_string,
                            user_email=primary_email,
                            user_token=user_token,
                            send_notification=send_notification,
                            max_request_capacity=max_request_capacity,
                            max_token_capacity=max_token_capacity,
                            logging_fn=save_request)
