import openai
from termcolor import colored
import time
import functools
import copy

def make_LLM_request(new_kwargs):
    try:
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

def handle_openAI_error(args, kwargs, openAI_error, fallback_strategy, graceful_string):
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
        print(colored("ReliableGPT: invalid request error", "red"))
        # check if this is context window related, try with a 16k model
        if openAI_error.code == 'context_length_exceeded':
            fallback_strategy = ['gpt-3.5-turbo-16k'] + fallback_strategy
            result = fallback_request(args=args, kwargs=kwargs, fallback_strategy=fallback_strategy)
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
    def __init__(self, openai_create_function, fallback_strategy = ['gpt-3.5-turbo', 'text-davinci-003', 'gpt-4', 'text-davinci-002'], graceful_string="Sorry, the OpenAI API is currently down"):
        self.openai_create_function = openai_create_function
        self.graceful_string = graceful_string
        self.fallback_strategy = fallback_strategy

    def __call__(self, *args, **kwargs):
        try:
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
                    graceful_string = self.graceful_string
                )
                print(colored(f"ReliableGPT: Recoverd got a successfull response {result}", "green"))
                return result
            except:
                return self.fallback_strategy