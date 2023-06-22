import openai
from main import reliableGPT
import main

# make openAI reliable and safe
#openai.ChatCompletion.create = reliableGPT(openai.ChatCompletion.create, user_email="krrish@berri.ai", user_token="rjPyk_xegdh-dpLBpDJzZacS0fVj3kR_zpNCnl5f4e0")
openai.ChatCompletion.create = reliableGPT(openai.ChatCompletion.create, user_email= "krrish@berri.ai", user_token = 'QA5T6lYfzB-8u3gFlC0hxtBZ-TbkJRF_FwrCB8GKTLM')


# fallback_priority = {user_emails}

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

#test_multiple_calls()


def test_single_call_bad_key():
    openai.api_key = "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"
    model = "gpt-4"
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the Chess championship 2022"*100},
    ]
    temperature = 0.7

    error_count = 0
    failure_count = 0  # Track the number of failures

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

    print(f"Error Count: {error_count}")
    print(f"Fallback response count: {failure_count}")

    if error_count == 0:
        print("All calls executed successfully.")
    else:
        print("Some calls returned errors.")

# test_single_call_bad_key()

def krrish_test_key():
    openai.api_key = "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" 
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello world"}])
    print(completion)
# krrish_test_key()
# def test_add_keys():
#     result = main.add_keys(account_email="ishaan1@berri.ai", keys=["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", "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"])
#     print(result)

# def test_delete_keys():
#     result = main.delete_keys(account_email="ishaan@berri.ai", account_token="OwfY1OFqy8fxR0zsJQPW_tcMPo8N7_vP8x3YW-dU9R8")
#     print(result)


# test_add_keys()
# test_delete_keys()


def test_embedding_bad_key():
    from main import reliableGPT
    openai.Embedding.create = reliableGPT(openai.Embedding.create, user_email= "krrish@berri.ai", user_token = 'QA5T6lYfzB-8u3gFlC0hxtBZ-TbkJRF_FwrCB8GKTLM')

    openai.api_key = "bad-key"
    def get_embedding(text, model="text-embedding-ada-002"):
        text = text.replace("\n", " ")
        print("text")
        return openai.Embedding.create(input=[text],
                                        model=model)["data"][0]["embedding"]
    result = get_embedding("GM")
    #print(f"This is the embedding response {result}")

test_embedding_bad_key()
