import openai
from reliablegpt import reliableGPT
import json
import ast

# make openAI reliable and safe
openai.ChatCompletion.create = reliableGPT(openai.ChatCompletion.create, user_email=="ishaan@berri.ai", fallback_strategy=['gpt-3.5-turbo', 'gpt-3.5-turbo','gpt-3.5-turbo'])
openai.api_key = "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"

import concurrent.futures

def test_multiple_calls():
    model = "gpt-4"
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"*400},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "Where was it played?"}
    ]
    temperature = 0.7

    error_count = 0
    failure_count = 0  # Track the number of failures

    def call_reliable_openai():
        nonlocal error_count, failure_count
        try:
            print("Making OpenAI Call")
            response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
            if response and "error" in response:
                error_count += 1
            if response == "Sorry, the OpenAI (GPT) failed":
                failure_count += 1
        except Exception as e:
            print("Exception occurred:", e)
            error_count += 1

    # Create a ThreadPoolExecutor with a maximum of 10 threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit the callable to the executor for each call
        future_calls = [executor.submit(call_reliable_openai) for _ in range(20)]

        # Wait for all the futures to complete
        concurrent.futures.wait(future_calls)

    print(f"Error Count: {error_count}")
    print(f"Fallback response count: {failure_count}")

    if error_count == 0:
        print("All calls executed successfully.")
    else:
        print("Some calls returned errors.")



def test_context_window():
    # Open the JSON file
    with open('context_window_test.json') as f:
        #print(f.read())
        kwargs = ast.literal_eval(f.read())

        #kwargs = json.load(f)
        print(type(kwargs))
        print("Making context window exceeded call")
        response = openai.ChatCompletion.create(**kwargs)

    # Access the data in the JSON file
    #print(kwargs)

test_multiple_calls()
test_context_window()