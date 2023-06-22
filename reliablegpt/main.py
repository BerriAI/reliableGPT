import openai
from termcolor import colored
import time
import functools
import copy
import requests
from posthog import Posthog

posthog = Posthog(
  project_api_key='phc_yZ30KsPzRXd3nYaET3VFDmquFKtMZwMTuFKVOei6viB',
  host='https://app.posthog.com')

def make_LLM_request(new_kwargs, self):
    try:
        if "embedding" in str(self.openai_create_function):
            # retry embedding with diff key
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
        return None
    return None

def fallback_request(args, kwargs, fallback_strategy):
    result = None
    for model in fallback_strategy:
        new_kwargs = copy.deepcopy(kwargs)  # Create a deep copy of kwargs
        new_kwargs['model'] = model  # Update the model
        result = make_LLM_request(new_kwargs)
        if result != None:
            return result    
    return None

def api_key_handler(args, kwargs, fallback_strategy, user_email, user_token, self=""):
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


def handle_openAI_error(args, kwargs, openAI_error, fallback_strategy, graceful_string, user_email="", user_token="", self=""):
    # Error Types from https://platform.openai.com/docs/guides/error-codes/python-library-error-types
    # 1. APIError - retry, retry with fallback
    # 2. Timeout - retry, retry with fallback
    # 3. RateLimitError - retry, retry with fallback
    # 4. APIConnectionError - Check your network settings, proxy configuration, SSL certificates, or firewall rules.
    # 5. InvalidRequestError - User input was bad: context_length_exceeded, 
    # 6. AuthenticationError - API key not working, return default hardcoded message
    # 7. ServiceUnavailableError - retry, retry with fallback
    error_type = openAI_error['type']
    if error_type == 'invalid_request_error' or error_type == 'InvalidRequestError':
        # check if this is context window related, try with a 16k model
        if openAI_error.code == 'context_length_exceeded':
            print(colored("ReliableGPT: invalid request error - context_length_exceeded", "red"))
            fallback_strategy = ['gpt-3.5-turbo-16k'] + fallback_strategy
            result = fallback_request(args=args, kwargs=kwargs, fallback_strategy=fallback_strategy)
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
    result = fallback_request(args=args, kwargs=kwargs, fallback_strategy=fallback_strategy)
    if result == None:
        return graceful_string
    else:
        return result
    return graceful_string

class reliableGPT:
    def __init__(self, openai_create_function, fallback_strategy = ['gpt-3.5-turbo', 'text-davinci-003', 'gpt-4', 'text-davinci-002'], graceful_string="Sorry, the OpenAI API is currently down", user_email="", user_token=""):
        self.openai_create_function = openai_create_function
        self.graceful_string = graceful_string
        self.fallback_strategy = fallback_strategy
        self.user_email = user_email
        self.user_token = user_token
        if self.user_email == "":
            raise ValueError("ReliableGPT Error: Please pass in a user email")

    def __call__(self, *args, **kwargs):
        try:
            posthog.capture(self.user_email, 'reliableGPT.request')
            result = self.openai_create_function(*args, **kwargs)
            return result
        except Exception as e:
            try:
                print(colored(f"ReliableGPT: Error Response from openai.ChatCompletion.create()", 'red'))
                print(colored(f"ReliableGPT: Got Exception {e}", 'red'))
                result = handle_openAI_error(
                    args = args,
                    kwargs = kwargs,
                    openAI_error = e.error,
                    fallback_strategy = self.fallback_strategy,
                    graceful_string = self.graceful_string,
                    user_email = self.user_email,
                    user_token=self.user_token,
                    self=self
                )
                posthog.capture(self.user_email, 'reliableGPT.recovered_request', {'error':e.error, 'recovered_response': result})
                print(colored(f"ReliableGPT: Recovered got a successful response {result}", "green"))
                return result
            except:
                posthog.capture(self.user_email, 'reliableGPT.recovered_request_exception', {'error':e.error, 'recovered_response': self.graceful_string})
                return self.graceful_string


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


