# have the router determine if an instantiation is calling the rate limit handler or the individual request wrapper directly
# save the original references of a model in model.py -> like a Model Card
import sys
sys.path.append('..')

from dotenv import load_dotenv
load_dotenv()

import openai
from reliablegpt import reliableGPT
import os
import time

good_open_ai_api_key = os.getenv('OPENAI_API_KEY')

openai.ChatCompletion.create = reliableGPT(
  openai.ChatCompletion.create,
  user_email="krrish@berri.ai",
  user_token="_4FTminlzIHtyWZ5Jy9UkNOoN31TirdHaqOwi-lYHfI",
  queue_requests=True,
  fallback_strategy=["gpt-3.5-turbo"])

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


print(test_single_call_bad_key())


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


test_embedding_bad_key()

list_questions = [
  "What is the difference between a list and a tuple in Python?",
  "How do you iterate over a dictionary in Python?",
  "What is the purpose of the 'self' parameter in a class method?",
  "What are lambda functions in Python?",
  "How do you remove duplicates from a list in Python?",
  "What is the difference between append() and extend() methods in Python lists?",
  "How do you read a file in Python?", "How do you write to a file in Python?",
  "What is the difference between a shallow copy and a deep copy in Python?",
  "How do you convert a string to lowercase in Python?"
]


def simple_openai_call(prompt):
  print(f"in simple openai call with question:  {prompt}")
  model = "gpt-4-turbo"
  messages = [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": prompt
    },
  ]
  result = openai.ChatCompletion.create(model=model, messages=messages)
  print(f"Result: from open ai for {prompt}, result {result}")
  return result


simple_openai_call("Hi im ishaan")


def test_regular_q():
  openai.api_key = good_open_ai_api_key
  results = {}
  start_time = time.time()
  for question in list_questions[:5]:
    print("Making request")
    print(question)
    # async
    result = simple_openai_call(question)
    print("response")
    print(result)
    results[question] = result
  print("\n\nDone executing\n]n")
  print(results)
  print(len(results))
  end_time = time.time()
  print("Total time:", end_time - start_time)


test_regular_q()
