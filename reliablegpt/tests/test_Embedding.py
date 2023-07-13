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
openai.api_key = os.getenv("AZURE_OPENAI_KEY")

# Wrap both completion + embedding 

openai.ChatCompletion.create = reliableGPT(
  openai.ChatCompletion.create,
  user_email="krrish@berri.ai",
  backup_openai_key=os.getenv("OPENAI_API_KEY"), _test=True, verbose=True)

openai.Embedding.create = reliableGPT(
  openai.Embedding.create,
  user_email="krrish@berri.ai",
  backup_openai_key=os.getenv('OPENAI_API_KEY'),
  verbose=True)

# Make Azure completion fail 
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

response = simple_openai_call("What do you know?")
print(response)

# Test embedding 
# choose text to embed
text_string = "sample text"

embeddings = openai.Embedding.create(deployment_id="azure-embedding-model",
                                     input=text_string)
# print(embeddings)