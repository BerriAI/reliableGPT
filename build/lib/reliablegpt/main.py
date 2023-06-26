## Imports for reliableGPT
import openai
from termcolor import colored
import time
import functools
import copy
import requests
from posthog import Posthog
from klotty import Klotty
from tqdm import tqdm

## Import for Batch requests
import uuid
from reliablegpt.api_handler import APICallHandler
import time
import threading

client = Klotty(api_key="re_X1PBTBvD_5mJfFM98AuF2278fNAGfXVNV") # email client

posthog = Posthog(
  project_api_key='phc_yZ30KsPzRXd3nYaET3VFDmquFKtMZwMTuFKVOei6viB',
  host='https://app.posthog.com')

def send_emails_task(user_email, notification_data, send_notification=False):
    if send_notification:
        body = f"""
        Unhandled Error Data
        {notification_data}
        """
        client.send_email(to=user_email,
                        sender="krrish@berri.ai",
                        subject="reliableGPT: Unhandled Error",
                        html=body)

def make_LLM_request(new_kwargs, self):
    try:
        if "embedding" in str(self.openai_create_function):
            # retry embedding with diff key
            print(colored(f"ReliableGPT: Retrying Embedding request", "blue"))
            return openai.Embedding.create(**new_kwargs)
        model = new_kwargs['model']
        if "3.5" or "4" in model: # call ChatCompletion
            print(colored(f"ReliableGPT: Retrying request with model CHAT {model}", "blue"))
            return openai.ChatCompletion.create(**new_kwargs)
        else:
            print(colored(f"ReliableGPT: Retrying request with model TEXT {model}", "blue"))
            new_kwargs['prompt'] = " ".join([message["content"] for message in new_kwargs['messages']])
            new_kwargs.pop('messages', None) # remove messages for completion models 
            return openai.Completion.create(**new_kwargs)
    except Exception as e:
        print(colored(f"ReliableGPT: Got 2nd AGAIN Error {e}", "red"))
        raise ValueError(e)

def fallback_request(args, kwargs, fallback_strategy, self):
    result = None
    for model in fallback_strategy:
        new_kwargs = copy.deepcopy(kwargs)  # Create a deep copy of kwargs
        new_kwargs['model'] = model  # Update the model
        result = make_LLM_request(new_kwargs, self=self)
        if result != None:
            return result    
    return None

def api_key_handler(args, kwargs, fallback_strategy, user_email, user_token, self=""):
    try:
        url = f"https://reliable-gpt-backend-9gus.zeet-berri.zeet.app/get_keys?user_email={user_email}&user_token={user_token}"
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            if result['status'] == 'failed':
                print(colored(f"ReliableGPT: No keys found for user: {user_email}, token: {user_token}", "red"))
                return None

            fallback_keys = result['response']['openai_api_keys'] # list of fallback keys
            if len(fallback_keys) == 0:
                return None
            for fallback_key in fallback_keys:
                openai.api_key = fallback_key
                result = make_LLM_request(kwargs, self=self)
                if result != None:
                    return result
        else:
            print(colored(f"ReliableGPT: No keys found for user: {user_email}, token: {user_token}", "red"))
        return None
    except Exception as e:
        raise ValueError(e)


def handle_openAI_error(args, kwargs, openAI_error, fallback_strategy, graceful_string, user_email="", user_token="", self=""):
    # Error Types from https://platform.openai.com/docs/guides/error-codes/python-library-error-types
    # 1. APIError - retry, retry with fallback
    # 2. Timeout - retry, retry with fallback
    # 3. RateLimitError - retry, retry with fallback
    # 4. APIConnectionError - Check your network settings, proxy configuration, SSL certificates, or firewall rules.
    # 5. InvalidRequestError - User input was bad: context_length_exceeded, 
    # 6. AuthenticationError - API key not working, return default hardcoded message
    # 7. ServiceUnavailableError - retry, retry with fallback
    if openAI_error != None:
        openAI_error = openAI_error.error # index into the error attribute of the class
    
    error_type = None # defalt to being None
    if openAI_error != None and 'type' in openAI_error:
        error_type = openAI_error['type']
    if error_type == 'invalid_request_error' or error_type == 'InvalidRequestError':
        # check if this is context window related, try with a 16k model
        if openAI_error.code == 'context_length_exceeded':
            print(colored("ReliableGPT: invalid request error - context_length_exceeded", "red"))
            fallback_strategy = ['gpt-3.5-turbo-16k'] + fallback_strategy
            result = fallback_request(args=args, kwargs=kwargs, fallback_strategy=fallback_strategy, self=self)
            if result == None:
                return graceful_string
            else:
                return result
        if openAI_error.code == "invalid_api_key":
            print(colored("ReliableGPT: invalid request error - invalid_api_key", "red"))
            result = api_key_handler(args=args, kwargs=kwargs, fallback_strategy=fallback_strategy, user_email=user_email, user_token=user_token, self=self)
            if result == None:
                return graceful_string
            else:
                return result

    # todo: alert on user_email that there is now an auth error 
    elif error_type == 'authentication_error' or error_type == 'AuthenticationError':
        print(colored("ReliableGPT: Auth error", "red"))
        return graceful_string

    # catch all 
    result = fallback_request(args=args, kwargs=kwargs, fallback_strategy=fallback_strategy, self=self)
    if result == None:
        return graceful_string
    else:
        return result
    return graceful_string

## Additional Features
## Log OpenAI request, results and exceptions
def capture_relevant_info(self, args, kwargs, result=None, error=None):
    if 'reliableGPT_metadata' in kwargs:
        print(f"In capture relevant info")

        url = "http://0.0.0.0:5000/log_request"  # Replace with the actual URL of the endpoint

        data = {
            "metadata": kwargs['reliableGPT_metadata'],
            "user_email": self.user_email,
            "openai_create_function": str(self.openai_create_function),
            "kwargs": kwargs,
            "args": args,
            "response": result,
            "error": error
        }
        # print(f"In capture relevant info {data}")
        response = requests.post(url, json=data)
        # Check the response status
        if response.status_code == 200:
            print("POST request successful")
        else:
            print("POST request failed")
        return

# Parent Logging function
def save_request(self, args, kwargs, posthog_event="", result="", posthog_metadata={}, errors=[]):
    try:
        #metadata  = kwargs['metadata']
        capture_relevant_info(self, args, kwargs, result, errors) # log event before and after for reliableGPT users
        if posthog_event != "":
            posthog.capture(self.user_email, posthog_event, posthog_metadata) # save posthog event 

        if result == self.graceful_string or len(errors) == 2: # returns a graceful string or got a 2nd exception
            # send an email and alert
            send_emails_task(self.user_email, posthog_metadata, self.send_notification)
    except:
        return # safe function, should not impact error handling if logging fails

class batchRequests:
    def __init__(self,
               process_func,
               max_token_capacity,
               max_request_capacity,
               set_timeout=10,
               verbose=False):
        super().__init__()
        self.api_handler = APICallHandler(max_token_capacity,
                                        max_request_capacity,
                                        verbose=verbose)
        self.process_func = process_func
        self.set_timeout = set_timeout
        self.verbose = verbose

    def print_verbose(self, *args):
        if self.verbose:
            print(*args)

    def get_result(self, text):
        task_id = uuid.uuid4().int
        self.print_verbose("task_id: ", task_id)

        self.api_handler.add_task(process_func=self.process_func,
                                input=text,
                                task_id=task_id)

        start_time = time.time()

        while time.time() - start_time < self.set_timeout:
            result = self.api_handler.get_result(task_id)
        if result:
            return result

        return None

    def get_results(self):
        return self.api_handler.get_results()

    def get_result_threaded(self, test_question, results):
        self.print_verbose(f"Enters reliableGPT with question: {test_question}")
        start_time = time.time()
        result = self.get_result(test_question)
        results.append(result)
        end_time = time.time()
        self.print_verbose(f"Gets result from reliableGPT: {result}",
                        end_time - start_time)


    def execute(self, questions=[]):
        for question in questions: 
            task_id = uuid.uuid4().int
            self.print_verbose("task_id: ", task_id)
            self.api_handler.add_task(process_func=self.process_func,
                                        input=question, task_id=task_id)
            self.api_handler.set_upperbound(len(questions))
        start_time = time.time() 
        while time.time() - start_time < self.set_timeout:
            results = self.api_handler.get_results()
            if len(results) >= len(questions):
                return results
        return self.api_handler.get_results()



class reliableGPT:
    def __init__(
            self, 
            openai_create_function, 
            fallback_strategy = ['gpt-3.5-turbo', 'text-davinci-003', 'gpt-4', 'text-davinci-002'], 
            graceful_string="Sorry, the OpenAI API is currently down", 
            user_email="", 
            user_token="",
            send_notification=False,
            open_ai_limits={}
            ):
        self.openai_create_function = openai_create_function
        self.graceful_string = graceful_string
        self.fallback_strategy = fallback_strategy
        self.user_email = user_email
        self.user_token = user_token
        self.send_notification = send_notification
        self.open_ai_limits = open_ai_limits

        if self.user_email == "":
            raise ValueError("ReliableGPT Error: Please pass in a user email")


    def handle_exception(self, args, kwargs, e):
        result = self.graceful_string # default to graceful string
        try:
            # Attempt No. 1, exception is received from OpenAI 
            print(colored(f"ReliableGPT: Error Response from {self.openai_create_function}", 'red'))
            print(colored(f"ReliableGPT: Got Exception {e}", 'red'))
            result = handle_openAI_error(
                args = args,
                kwargs = kwargs,
                openAI_error = e,
                fallback_strategy = self.fallback_strategy,
                graceful_string = self.graceful_string,
                user_email = self.user_email,
                user_token=self.user_token,
                self=self
            )
            print(colored(f"ReliableGPT: Recovered got a successful response {result}", "green"))
            if result == self.graceful_string:
                # did a retry but still returned graceful string
                save_request(
                    self, 
                    args, 
                    kwargs,
                    posthog_event = 'reliableGPT.recovered_request_exception', 
                    result = result, 
                    posthog_metadata = {'error':str(e), 'recovered_response': result}, 
                    errors = [e]
                )
            else:
                # No errors, successfull retry
                save_request(
                    self,
                    args, 
                    kwargs, 
                    posthog_event = "reliableGPT.recovered_request", 
                    result=result, 
                    posthog_metadata={'error':str(e), 'recovered_response': result},
                    errors = [e]
                )
        except Exception as e2:
            # Exception 2, After trying to rescue
            save_request(
                self, 
                args, 
                kwargs, 
                posthog_event = 'reliableGPT.recovered_request_exception',
                result = "",
                posthog_metadata = {'original_error':str(e), 'error2':str(e2), 'recovered_response': self.graceful_string},
                errors = [e, e2]
            )
            return result
        return result

    ## Code that handles / wraps openai calls
    def __call__(self, *args, **kwargs):
        try:
            save_request(self, args, kwargs, "reliableGPT.request", result="")
            result = self.openai_create_function(*args, **kwargs)
            save_request(self, args, kwargs, "", result=result)
            return result
        except Exception as e:
            return self.handle_exception(args, kwargs, e)




### OpenAI Key Management - Optional code if you want to use reliableGPT for Key Mgmt ###
def add_keys(user_email="", keys=[]):
    url = f"https://reliable-gpt-backend-9gus.zeet-berri.zeet.app/add_keys"
    if user_email == "":
        return "reliableGPT: Please add an Email to add your keys"
    if len(keys) == 0:
        return "reliableGPT: Please add keys to add"
    payload = {"user_email": user_email}
    for idx, key in enumerate(keys):
        key_name = "key_" + str(idx+1)
        payload[key_name] = key
    response = requests.get(url, params=payload)
    return response.json()

def delete_keys(user_email, user_token):
    url = f"https://reliable-gpt-backend-9gus.zeet-berri.zeet.app/delete_keys"
    if user_email == "":
        return "reliableGPT: Please add an Email to delete your keys"
    if user_email == "":
        return "reliableGPT: Please add an account_token to delete your keys"
    payload = {"user_email": user_email, "user_token": user_token}
    response = requests.get(url, params=payload)
    return response.json()

