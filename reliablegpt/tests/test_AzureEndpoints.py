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

## Test Azure / OpenAI Fallback 
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2023-05-15"

openai.ChatCompletion.create = reliableGPT(
  openai.ChatCompletion.create,
  user_email="krrish@berri.ai",
  azure_fallback_strategy=["chatgpt-v-2"], _test=True, verbose=True)

def simple_openai_call(prompt):
  print(f"in simple openai call with question:  {prompt}")
  engine="chatgpt-test"
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
  result = openai.ChatCompletion.create(engine=engine, messages=messages)
  print(f"Result: from open ai for {prompt}, result {result}")
  return result

list_questions = [
  "what do you know?", 
  "who is jacky robinson?",
  "what do you know?",
  "what do you know?",
  "what do you know?",
]


#bad key
# openai.api_key = "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"

# for question in list_questions:
#   response = simple_openai_call(question)
#   print(response)

#good key
openai.api_key = os.getenv("AZURE_OPENAI_KEY")

for question in list_questions:
  response = simple_openai_call(question)
  print(response)