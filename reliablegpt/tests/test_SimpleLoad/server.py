from flask import Flask, request
import time
import openai
import sys
import traceback
import dotenv
import vecs
from dotenv import load_dotenv
load_dotenv()

sys.path.append('../..')  # Adds the parent directory to the system path
from CacheDecorator import reliableCache

import openai
from main import reliableGPT

import os 
openai.api_key = os.getenv('OPENAI_API_KEY')


DB_CONNECTION = os.getenv("DB_CONNECTION")
# create vector store client
vx = vecs.create_client(DB_CONNECTION)

vectorstore = vx.get_collection(name="reliable_gpt_testing")

cache = reliableCache(max_threads=20, query_arg="query", customer_instance_arg="instance_id", user_email="krrish@berri.ai")

def logging_fn(*args, **kwargs):
  pass

# openai.ChatCompletion.create = reliableGPT(
#   openai.ChatCompletion.create,
#   user_email=["ishaan@berri.ai"], verbose=True)


app = Flask(__name__)

@app.route("/test_func")
@cache.cache_wrapper
def test_fn():
  print("received request")
  try:
    # take query 
    question = request.args.get("query")
    # embed query 
    query_embedding = openai.Embedding.create(model="text-embedding-ada-002",
                                      input=question)['data'][0]['embedding']
    # get similar context from vectorstore 
    response = vectorstore.query(
        query_vector=query_embedding,      # required
        limit=5,                         # number of records to return
        include_value = True,
        include_metadata=True,
    )
    # get chatgpt response 
    input_prompt = f"""Given this context\n{response}\n Answer this question:{question}"""
    # return chatgpt
    result = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": input_prompt}])
    print(f"ENDPOINT RETURNED RESULT: {result}")
    return result
  except:
    traceback.print_exc()
    return "Error", 500


@app.route('/')
def index():
  return 'Hello from Flask!'


if __name__ == "__main__":
  from waitress import serve
  serve(app, host="0.0.0.0", port=4000, threads=200)
