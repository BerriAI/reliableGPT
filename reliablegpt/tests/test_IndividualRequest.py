# have the router (which is reliableGPT) determine if an instantiation is calling the rate limit handler or the individual request wrapper directly
# save the original references of a model in model.py -> like a Model Card
import sys
import os
import dotenv
from dotenv import load_dotenv
load_dotenv()

sys.path.append('..')  # Adds the parent directory to the system path
import openai
from main import reliableGPT
import concurrent.futures

openai.ChatCompletion.create = reliableGPT(
  openai.ChatCompletion.create,
  user_email="krrish@berri.ai", verbose=True)

print(openai.ChatCompletion.create)

good_open_ai_api_key = os.getenv('OPENAI_API_KEY')

def test_single_call_bad_key():
  openai.api_key = "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"
  model = "gpt-4"
  messages = [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Who won the Chess championship 2022"
    },
  ]
  temperature = 0.7

  error_count = 0
  failure_count = 0  # Track the number of failures

  try:
    print("Making OpenAI Call")
    response = openai.ChatCompletion.create(model=model,
                                            messages=messages,
                                            temperature=temperature)
    print("Response: ", response)
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


#test_single_call_bad_key()


def test_embedding_bad_key():
  openai.Embedding.create = reliableGPT(
    openai.Embedding.create,
    user_email="krrish@berri.ai",
    user_token='_4FTminlzIHtyWZ5Jy9UkNOoN31TirdHaqOwi-lYHfI',
    send_notification=True)

  openai.api_key = "bad-key"

  def get_embedding(text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")
    print("text")
    return openai.Embedding.create(input=[text],
                                   model=model)["data"][0]["embedding"]

  result = get_embedding("GM")
  print(result)


#test_embedding_bad_key()


def test_embedding_bad_key_fail():
  openai.Embedding.create = reliableGPT(
    openai.Embedding.create,
    user_email="krrish@berri.ai",
    send_notification=True)

  openai.api_key = "bad-key"

  def get_embedding(text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")
    print("text")
    return openai.Embedding.create(input=[text],
                                   model=model)["data"][0]["embedding"]

  result = get_embedding("GM")
  print(result)

#test_embedding_bad_key_fail()


def test_bad_open_ai_call():
  model = "gpt-4-turbo"
  openai.api_key = good_open_ai_api_key
  messages = [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Who are you?"
    },
  ]
  result = openai.ChatCompletion.create(model=model, messages=messages)
  print(f"Result: from open ai result {result}")
  return result


test_bad_open_ai_call()


def test_bad_open_ai_call_with_q():
  openai.ChatCompletion.create = reliableGPT(
    openai.ChatCompletion.create,
    user_email="krrish@berri.ai",
    fallback_strategy=["text-davinci-003", "text-davinci-003"],
    queue_requests=True)
  model = "gpt-4-turbo"
  openai.api_key = good_open_ai_api_key
  messages = [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Who are you?"
    },
  ]
  result = openai.ChatCompletion.create(model=model, messages=messages)
  print(f"Result: from open ai result {result}")
  return result


# test_bad_open_ai_call_with_q()


def test_multiple_calls():
  model = "gpt-4"
  openai.api_key = good_open_ai_api_key
  messages = [{
    "role": "system",
    "content": "You are a helpful assistant."
  }, {
    "role": "user",
    "content": "Who won the world series in 2020?" * 400
  }, {
    "role":
    "assistant",
    "content":
    "The Los Angeles Dodgers won the World Series in 2020."
  }, {
    "role": "user",
    "content": "Where was it played?"
  }]
  temperature = 0.7

  error_count = 0
  failure_count = 0  # Track the number of failures

  def call_reliable_openai():
    nonlocal error_count, failure_count
    try:
      print("Making OpenAI Call")

      response = openai.ChatCompletion.create(model=model,
                                              messages=messages,
                                              temperature=temperature)
      print(response)
      if response and "error" in response:
        error_count += 1
      if response == "Sorry, the OpenAI API is currently down":
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

