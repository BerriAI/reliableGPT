import openai
from main import reliable_create

@reliable_create
def reliable_openai_call(model, messages, temperature):
   return openai.ChatCompletion.create(model=model,
                                            messages=messages,
                                            temperature=temperature)


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

    def call_reliable_openai():
        nonlocal error_count
        try:
            print("Making OpenAI Call")
            response = reliable_openai_call(model=model, messages=messages, temperature=temperature)
            if response and "error" in response:
                error_count += 1
        except Exception as e:
            print("Exception occurred:", e)
            error_count += 1

    # Create a ThreadPoolExecutor with a maximum of 10 threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit the callable to the executor for each call
        future_calls = [executor.submit(call_reliable_openai) for _ in range(200)]

        # Wait for all the futures to complete
        concurrent.futures.wait(future_calls)

    print(f"Error Count: {error_count}")

    if error_count == 0:
        print("All calls executed successfully.")
    else:
        print("Some calls returned errors.")

test_multiple_calls()


