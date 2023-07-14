from typing import Any
import threading
from threading import active_count
import requests
import traceback
from flask import Flask, request

class reliableCache: 
    def __init__(self, query_arg=None, customer_instance_arg=None, user_email=None, max_threads=100) -> None:
        self.max_threads = max_threads
        self.verbose = True
        self.query_arg = query_arg
        self.customer_instance_arg = customer_instance_arg
        self.user_email = user_email
        self.cache_wrapper_threads = {}
        self.hot_cache = {}
        pass

    def print_verbose(self, print_statement):
        if self.verbose:
            print("Cached Request: " + str(print_statement))

    def add_cache(self, user_email, instance_id, input_prompt, response):
        try:
            url = "https://reliablegpt-logging-server-7nq8.zeet-berri.zeet.app/add_cache"
            querystring = {
                "customer_id": "temp@xyz.com",
                "instance_id": instance_id, 
                "user_email": user_email, 
                "input_prompt": input_prompt,
                "response": response
            }
            response = requests.post(url, params=querystring)      
        except:
            pass

    def try_cache_request(self, user_email, instance_id, query=None):
        try:
            if (user_email, instance_id, query) in self.hot_cache:
                result = self.hot_cache[(user_email, instance_id, query)]
                return result
            else:
                url = "https://reliablegpt-logging-server-7nq8.zeet-berri.zeet.app/get_cache"
                querystring = {
                    "customer_id": "temp@xyz.com",
                    "instance_id": instance_id, 
                    "user_email": user_email, 
                    "input_prompt": query,
                }
                response = requests.get(url, params=querystring)
                extracted_result = response.json()["response"]
                self.hot_cache[(user_email, instance_id, query)] = extracted_result
                return extracted_result
        except:
            pass
        self.print_verbose(f"cache miss!")
        return None

    def cache_wrapper(self, func):
        def wrapper(*args, **kwargs):
            query = request.args.get(self.query_arg) # the customer question
            instance_id = request.args.get(self.customer_instance_arg) # the unique instance to put that customer query/response in
            curr_thread_id = threading.get_ident()
            self.cache_wrapper_threads[curr_thread_id] = True   # mark thread as active
            try:
                # monitor for high thread utilization 
                self.print_verbose(f"max threads: {self.max_threads}")
                thread_utilization = self.get_wrapper_thread_utilization()
                self.print_verbose(f"thread utilization: {thread_utilization}")
                if thread_utilization > 0.8: # over 80% utilization of threads, start returning cached responses
                    result = self.try_cache_request(user_email=self.user_email, instance_id=instance_id, query=query)
                    if result != None:
                        self.cache_wrapper_threads[curr_thread_id] = False  # mark thread as inactive
                        return result
                result = func(*args, **kwargs)
                # add response to cache 
                # Create a separate thread to run the code
                thread = threading.Thread(target=self.add_cache, args=(self.user_email, instance_id, query, result))
                thread.start()
                pass 
            except:
                traceback.print_exc()
                pass
            finally:
                self.cache_wrapper_threads[curr_thread_id] = False  # mark thread as inactive
            return result
        return wrapper
    
    def get_wrapper_thread_utilization(self):
        self.print_verbose(f"cache wrapper thread values: {self.cache_wrapper_threads.values()}")
        active_cache_threads = 0
        for value in self.cache_wrapper_threads.values():
            if value == True:
                active_cache_threads += 1
        # active_cache_threads = sum(self.cache_wrapper_threads.values())
        self.print_verbose(f"active_cache_threads: {active_cache_threads}")
        return active_cache_threads / self.max_threads